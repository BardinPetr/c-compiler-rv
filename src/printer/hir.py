""" Hardware-oriented IR extensions """

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Dict, List, Optional

from printer.reg import Reg


@dataclass
class HVar:
    pass

@dataclass
class HStackVar(HVar):
    pos: int = 0
    size: int = 8
    name: str = ""

@dataclass
class HStackRegCopy(HStackVar):
    pos: int = 0
    reg: Reg = None
    name: str = ""

@dataclass
class HRegVar(HVar):
    reg: Reg
    name: str = ""

@dataclass
class HMemVar(HVar):
    label: str


@dataclass
class HFunLayout:
    mem_slots: Dict[str, HVar] = field(default_factory=dict)
    stack: List[HStackVar] = field(default_factory=list)
