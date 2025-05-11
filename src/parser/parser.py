from os.path import dirname, realpath, join

from lark import Lark

parser = Lark(open(join(dirname(realpath(__file__)), "grammar.lark")))


def parse(text):
    tree = parser.parse(text)
    return tree
