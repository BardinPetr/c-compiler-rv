from collections.abc import generator
from typing import *

from utils import str_class_hierarchy, flatten


class BaseVisitor:
    """
    For each node gets class hierarchy and calls in sequence functions
    named same as classnames from 'object' to most specific class
    """

    def __call__(self, node):
        if node is None:
            self.throw("None cannot be visited")
        elif isinstance(node, Iterable):
            for i in node:
                self(i)
        else:
            fired = False
            for node_name in str_class_hierarchy(node)[::-1]:
                if hasattr(self, node_name):
                    getattr(self, node_name)(node)
                    fired = True
            if not fired:
                print(f"no transformer for node: \n{node}\n")

    def throw(self, *x):
        raise Exception("invalid transform: " + ' '.join(str(i) for i in x))


class BaseTransformer:
    def __call__(self, node):
        if node is None:
            return node

        if isinstance(node, List | Tuple | generator):
            return [self(i) for i in node]

        fired = False
        for node_name in str_class_hierarchy(node)[::-1]:
            if hasattr(self, node_name):
                node = getattr(self, node_name)(node)
                fired = True
        if not fired:
            # print("no transform for", type(node))
            if hasattr(self, "fallback"):
                node = getattr(self, "fallback")(node)

        return node

    def fself(self, x) -> List:
        return flatten(self(x))

    def err(self, *x):
        raise Exception("invalid transform: " + ' '.join(str(i) for i in x))


class TCtx:
    pass


class CtxTransformer:
    def __init__(self):
        self.ctx: Dict[Type[TCtx], List[TCtx]] = {}

    def cpush(self, c: TCtx):
        typ = type(c)
        if typ not in self.ctx:
            self.ctx[typ] = []
        self.ctx[typ].append(c)

    def cpop(self, typ: Type[TCtx]):
        if typ not in self.ctx:
            raise Exception("no ctx for type", typ)
        self.ctx[typ].pop()

    def cpeek[T](self, typ: Type[T]) -> Optional[T]:
        if typ not in self.ctx or len(self.ctx[typ]) == 0:
            return None
        return self.ctx[typ][-1]
