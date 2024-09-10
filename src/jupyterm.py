import argparse
import io
import itertools
import functools
import os

import base64
from PIL import Image
import nbformat

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Footer, Header, Static, TextArea


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="Jupyter notebook file to view [.ipynb]")
    # parser.add_argument("--color", action="store_const", const=True, help="highlight syntax")
    return parser.parse_args()


class Notebook:
    def __init__(self, path, version=4):
        self.path = path
        self.version = version
        self.notebook = self._read()
        self.cells = self._parse_cells()

    def _read(self):
        return nbformat.read(self.path, as_version=self.version)

    def _parse_cells(self):
        for cell in self.notebook.get("cells"):
            yield cell


def _display_handler(content):
    image_raw = base64.b64decode(content)
    image_bytes = io.BytesIO(image_raw)
    with Image.open(image_bytes) as image:
        image.show()


class DisplayButton(Button):
    pass

    def on_mount(self) -> None:
        self.styles.border = ("solid", "white")
        self.styles.padding = 0
        self.styles.margin = 0
        self.styles.width = "auto"
        self.styles.height = "auto"


class CodeCell(Static):
    def on_mount(self) -> None:
        self.styles.border = ("solid", "white")


class OutputCell(Static):
    pass
    # def on_mount(self) -> None:
    #     # self.styles.background = "darkred"
    #     # self.styles.border = ("hkey", "white")


class NotebookApp(App):
    # BINDINGS = [
    #     ("d", "toggle_dark", "Toggle dark mode"),
    # ]

    def on_mount(self) -> None:
        self.title = "Jupyterm"
        self.sub_title = f"{self.file}"

    def compose(self) -> ComposeResult:
        args = get_args()
        if not args.file.lower().endswith(".ipynb"):
            raise ValueError(f"{args.file} is not a jupyter notebook file.")
        if not os.path.exists(args.file):
            raise ValueError(f"{args.file} does not exist.")

        self.file = args.file
        nb = Notebook(self.file)
        cells = nb.cells

        self.counter = itertools.count()
        self.display_data = {}

        yield Header()
        with Container():
            with VerticalScroll():
                for i, cell in enumerate(cells):
                    execution_count = cell.get("execution_count")
                    match cell.cell_type:
                        case "code":
                            yield CodeCell(cell.source)
                            if cell.outputs:
                                for output in cell.outputs:
                                    if "text" in output.keys():
                                        yield OutputCell(output.get("text"))
                                    if output.get("output_type") == "display_data":
                                        for content_type, content in output.get("data", {}).items():
                                            if content_type.startswith("image/"):
                                                count = next(self.counter)
                                                button_id = f"d{count}"
                                                self.display_data[button_id] = content
                                                yield DisplayButton(
                                                    "Display data [press <enter> to display]",
                                                    id=button_id,
                                                )
                                    else:
                                        yield OutputCell(f"[{output.get('output_type')}]")
                        case "markdown":
                            yield Static(cell.source, expand=True)
                        case _:
                            pass
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        content = self.display_data[button_id]
        _display_handler(content)

    # def action_toggle_dark(self) -> None:
    #     """An action to toggle dark mode."""
    #     self.dark = not self.dark


def main():
    app = NotebookApp()
    app.run()
