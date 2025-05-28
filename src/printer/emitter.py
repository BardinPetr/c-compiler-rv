from typing import Iterable

from utils import str_class_hierarchy


class Emitter:

    def __init__(self):
        self.data = []

    def emit(self, cmd, *args):
        self.data.append(f"{cmd} {', '.join(str(i) for i in args)}")

    def emit_label(self, text):
        self.data.append(f"{text}:")

    def emit_section(self, name):
        self.emit(".section", f".{name}")

    def get(self) -> str:
        return '\n'.join(self.data) + "\n"

class BaseTransformer:
    def __call__(self, node):
        if isinstance(node, Iterable):
            for i in node:
                self(i)
        else:
            for node_name in str_class_hierarchy(node):
                if hasattr(self, node_name):
                    getattr(self, node_name)(node)
                    break
            else:
                print(f"no transformer for node: \n{node}\n")

    def throw(self, *x):
        raise Exception("invalid transform: " + ' '.join(str(i) for i in x))
