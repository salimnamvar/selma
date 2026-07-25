"""Sample Python file for testing."""

import os
from pathlib import Path


def hello_world():
    """Print hello world."""
    print("Hello, World!")


def add(a, b):
    """Add two numbers."""
    return a + b


class Calculator:
    """A simple calculator class."""

    def __init__(self, value=0):
        """Initialize calculator."""
        self.value = value

    def add(self, x):
        """Add x to value."""
        self.value += x
        return self

    def subtract(self, x):
        """Subtract x from value."""
        self.value -= x
        return self


def complex_func(a, b, *args, keyword="default", **kwargs):
    """A complex function with various parameter types."""


def __dunder_method__():
    """A dunder method."""
