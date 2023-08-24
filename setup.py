import os
from setuptools import setup, find_packages

scripts = [
	"bin/jupyterm",
]

setup(
	name="jupyterm",
	version=0.1,
	description="TUI Jupyter notebook viewer",
	author="Sidney Mau",
	packages=find_packages(),
	scripts=scripts,
)
