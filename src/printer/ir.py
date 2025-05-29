""" Intermediate representation code objects """

from dataclasses import dataclass
from enum import StrEnum, auto
from typing import *

from hir import HFunLayout, HVar

"""
Data
"""


class IRType(StrEnum):
    VOID = auto()
    INT = auto()
    CHAR = auto()
    STRING = auto()


@dataclass(kw_only=True)
class IRValue:
    type: IRType = IRType.INT


@dataclass
class IRIntValue(IRValue):
    value: int

    def __post_init__(self):
        self.type = IRType.INT


@dataclass
class IRCharValue(IRValue):
    value: str

    def __post_init__(self):
        self.type = IRType.INT
        assert len(self.value) == 1


@dataclass
class IRStringValue(IRValue):
    value: str

    def __post_init__(self):
        self.type = IRType.STRING


"""
    Commands
"""


@dataclass(kw_only=True)
class IRStatement:
    label: Optional[str] = None


@dataclass
class IRStStoreValue(IRStatement):
    dest: str
    value: IRValue


class IRBOp(StrEnum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    REM = auto()
    CLT = auto()
    CGT = auto()
    CEQ = auto()
    CNE = auto()
    BIT_AND = auto()
    BIT_OR = auto()
    BIT_LSH = auto()
    BIT_RSH = auto()
    LOG_AND = auto()
    LOG_OR = auto()


@dataclass
class IRStBinOp(IRStatement):
    operation: IRBOp
    dest: str
    arg1: str
    arg2: str


class IRUOp(StrEnum):
    MINUS = auto()
    BIT_NEG = auto()
    LOG_NEG = auto()


@dataclass
class IRStUnOp(IRStatement):
    operation: IRUOp
    dest: str
    arg: str


@dataclass
class IRStJump(IRStatement):
    target: str


class IRCJumpType(StrEnum):
    JZ = auto()
    JNZ = auto()


@dataclass
class IRStCJump(IRStatement):
    check_type: IRCJumpType
    checked_var: str
    jump_to: str


@dataclass
class IRStCall(IRStatement):
    fun_name: str
    arg_vars: List[str]
    assign_var: Optional[str] = None


@dataclass
class IRStReturn(IRStatement):
    var: str


"""
    Structure
"""


@dataclass
class IRFunParam:
    name: str
    type: IRType


@dataclass
class IRFun:
    name: str
    ret_typ: IRType
    params: List[IRFunParam]
    body: Optional[List[IRStatement]] = None
    layout: Optional[HFunLayout] = None

    def __post_init__(self):
        self.exit_label = f"__exit_{self.name}"
        self.is_impl = self.body is not None


@dataclass
class IRGlobal:
    name: str
    type: IRType
    val: Optional[IRValue] = None


@dataclass
class IRProg:
    functions: List[IRFun]
    globals: List[IRGlobal]


"""
    Pseudo
"""


# псевдо-инструкция для перемещения данных
# между физическими локациями переменных уровня IR
@dataclass
class HIRMove(IRStatement):
    src: HVar
    dst: HVar
