""" Hardware-oriented IR extensions """

from dataclasses import dataclass, field
from typing import Dict, List

from printer.reg import Reg


@dataclass
class HVar:
    def __str__(self):
        return self.__repr__()


@dataclass
class HStackVar(HVar):
    pos: int = 0
    size: int = 8
    name: str = ""

    def __repr__(self):
        return f"HStkVar@{self.pos}"

@dataclass
class HStackRegCopy(HStackVar):
    pos: int = 0
    reg: Reg = None
    name: str = ""

    def __repr__(self):
        return f"HStkVar@{self.pos}(copy of {self.reg.code if self.reg else '?'})"


@dataclass
class HRegVar(HVar):
    reg: Reg
    name: str = ""

    def __repr__(self):
        return f"HRegVar({self.reg.code if self.reg else '?'})"


@dataclass
class HMemVar(HVar):
    label: str

    def __repr__(self):
        return f"HMemVar({self.label})"


@dataclass
class HFunLayout:
    mem_slots: Dict[str, HVar] = field(default_factory=dict)
    stack: List[HStackVar] = field(default_factory=list)
