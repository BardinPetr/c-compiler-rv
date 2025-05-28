from enum import auto, Enum, IntEnum
from typing import List


class RegisterType(IntEnum):
    SCRATCH = auto()
    ARGUMENT = auto()
    RETURN = auto()

    CALLEE_SAVED = auto()
    CALLER_SAVED = auto()

class Reg(Enum):
    def __init__(self, code, types):
        self.code = code
        self.types = types

    @classmethod
    def get(cls, name):
        try:
            return cls[name.strip().upper()]
        except KeyError:
            return None

    @classmethod
    def by(cls, typ: RegisterType) -> List['Reg']:
        return [i for i in cls if typ in i.types]

    @classmethod
    def params(cls) -> List['Reg']:
        return cls.by(RegisterType.ARGUMENT)

    @classmethod
    def ret(cls) -> List['Reg']:
        return cls.by(RegisterType.RETURN)

    @classmethod
    def scratch(cls) -> List['Reg']:
        return cls.by(RegisterType.SCRATCH)

    @classmethod
    def caller_saved(cls) -> List['Reg']:
        return cls.by(RegisterType.CALLER_SAVED)

    @classmethod
    def callee_saved(cls) -> List['Reg']:
        return cls.by(RegisterType.CALLEE_SAVED)
