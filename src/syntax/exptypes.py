from enum import StrEnum, auto


class UOp(StrEnum):
    UOP_NEG = auto()
    UOP_INV = auto()
    UOP_SUB = auto()
    UOP_DEC = auto()
    UOP_INC = auto()
    def __repr__(self):
        return f"U<{self.value}>"

class BOp(StrEnum):
    MAT_PLUS = auto()
    MAT_MINUS = auto()
    MAT_STAR = auto()
    MAT_DIV = auto()
    MAT_MOD = auto()
    LOG_XOR = auto()
    LOG_AND = auto()
    LOG_OR = auto()
    LOG_LAND = auto()
    LOG_LOR = auto()
    LOG_RIGHT = auto()
    LOG_LEFT = auto()
    CMP_LE = auto()
    CMP_LT = auto()
    CMP_GE = auto()
    CMP_GT = auto()
    CMP_EQ = auto()
    CMP_NE = auto()
    def __repr__(self):
        return f"B<{self.value}>"


BOP_MATCH = {
    "<=": BOp.CMP_LE,
    "<": BOp.CMP_LT,
    ">=": BOp.CMP_GE,
    ">": BOp.CMP_GT,
    "==": BOp.CMP_EQ,
    "!=": BOp.CMP_NE,
    "^": BOp.LOG_XOR,
    "&": BOp.LOG_AND,
    "|": BOp.LOG_OR,
    "&&": BOp.LOG_LAND,
    "||": BOp.LOG_LOR,
    ">>": BOp.LOG_RIGHT,
    "<<": BOp.LOG_LEFT,
    "+": BOp.MAT_PLUS,
    "-": BOp.MAT_MINUS,
    "*": BOp.MAT_STAR,
    "/": BOp.MAT_DIV,
    "%": BOp.MAT_MOD,
}

UOP_MATCH = {
    "--": UOp.UOP_DEC,
    "++": UOp.UOP_INC,
    "!": UOp.UOP_NEG,
    "~": UOp.UOP_INV,
    "-": UOp.UOP_SUB,
}
