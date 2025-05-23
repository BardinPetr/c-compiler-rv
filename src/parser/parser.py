from os.path import dirname, realpath, join

from lark import Lark, Tree

parser = Lark(open(join(dirname(realpath(__file__)), "grammar.lark")))


def do_parse(text: str) -> Tree:
    return parser.parse(text)
