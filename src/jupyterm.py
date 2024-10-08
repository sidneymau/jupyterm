#!/usr/bin/env python
import argparse
import io
import functools

import base64
from PIL import Image
import nbformat
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.widgets import Frame, Label, TextArea, Button
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.python import PythonLexer
from pygments.lexers.markup import MarkdownLexer


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="Jupyter notebook file to view [.ipynb]")
    parser.add_argument("--color", action="store_const", const=True, help="highlight syntax")
    return parser.parse_args()


class Cell:
    def __init__(self, cell):
        self.cell = cell
        self.cell_type = cell.get("cell_type")
        self.source = cell.get("source")
        self.outputs = cell.get("outputs")


class Notebook:
    def __init__(self, path, version=4):
        self.path = path
        self.version = version
        self.notebook = self._read()
        self.cells = self._parse_cells()

    def _read(self):
        return nbformat.read(self.path, as_version=self.version)

    def _parse_cells(self):
        cells = map(Cell, self.notebook.get("cells"))
        return cells


def _display_handler(output):
    """
    Some of the logic in this function comes from
    https://github.com/damienmarlier51/Junix/tree/master
    """
    for content_type, content in output.get("data", {}).items():
        if content_type.startswith("image/"):
            image_raw = base64.b64decode(content)
            image_bytes = io.BytesIO(image_raw)
            with Image.open(image_bytes) as image:
                image.show()
        else:
            # TODO log this but otherwise don't complain too much
            # raise ValueError(f"output of type {content_type} cannot be displayed")
            continue
    return


def main():
    args = get_args()
    if not args.file.lower().endswith(".ipynb"):
        raise ValueError(f"{args.file} is not a jupyter notebook file.")

    nb = Notebook(args.file)

    cells = []
    for i, cell in enumerate(nb.cells):
        match cell.cell_type:
            case "code":
                cells.append(
                    Frame(
                        TextArea(
                            text=cell.source,
                            read_only=True,
                            line_numbers=True,
                            lexer=PygmentsLexer(PythonLexer) if args.color else None,
                        ),
                        title=f"{i + 1}",
                    )
                )
                if cell.outputs:
                    for output in cell.outputs:
                        if "text" in output.keys():
                            cells.append(
                                TextArea(
                                    text=output.get("text"),
                                    read_only=True,
                                    line_numbers=False,
                                )
                            )
                        if output.get("output_type") == "display_data":
                            display_handler = functools.partial(
                                _display_handler, output=output
                            )
                            cells.append(
                                Button(
                                    text="Display data [press <enter> to display]",
                                    handler=display_handler,
                                )
                            )
            case "markdown":
                cells.append(
                    Frame(
                        TextArea(
                            text=cell.source,
                            read_only=True,
                            line_numbers=False,
                            lexer=PygmentsLexer(MarkdownLexer) if args.color else None,
                        ),
                        title=f"{i + 1}",
                    )
                )
            case _:
                pass

    root_container = HSplit(
        [
            Label(args.file, style="underline"),
            ScrollablePane(HSplit(cells)),
        ]
    )

    layout = Layout(container=root_container)

    kb = KeyBindings()

    @kb.add("q")
    def exit_(event):
        event.app.exit()

    kb.add("pageup")(focus_previous)
    kb.add("pagedown")(focus_next)

    app = Application(
        layout=layout,
        key_bindings=kb,
        enable_page_navigation_bindings=True,
        full_screen=True,
    )
    app.run()

