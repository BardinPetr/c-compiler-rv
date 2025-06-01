from backend.ir.ir import IRCJumpType, IRBOp
from backend.hw.reg import *


class RV64Reg(Reg):
    ZERO = ("zero", [])
    RA = ("ra", [RegisterType.CALLEE_SAVED])
    SP = ("sp", [])
    GP = ("gp", [])
    TP = ("tp", [])
    FP = ("fp", [RegisterType.CALLEE_SAVED])

    T0 = ("t0", [RegisterType.CALLER_SAVED]) # RegisterType.SCRATCH
    T1 = ("t1", [RegisterType.CALLER_SAVED]) # RegisterType.SCRATCH
    T2 = ("t2", [RegisterType.SCRATCH, RegisterType.CALLER_SAVED])
    T3 = ("t3", [RegisterType.SCRATCH, RegisterType.CALLER_SAVED])
    T4 = ("t4", [RegisterType.SCRATCH, RegisterType.CALLER_SAVED])
    T5 = ("t5", [RegisterType.SCRATCH, RegisterType.CALLER_SAVED])
    T6 = ("t6", [RegisterType.SCRATCH, RegisterType.CALLER_SAVED])

    A0 = ("a0", [RegisterType.ARGUMENT, RegisterType.CALLER_SAVED, RegisterType.RETURN])
    A1 = ("a1", [RegisterType.ARGUMENT, RegisterType.CALLER_SAVED, RegisterType.RETURN])
    A2 = ("a2", [RegisterType.ARGUMENT, RegisterType.CALLER_SAVED])
    A3 = ("a3", [RegisterType.ARGUMENT, RegisterType.CALLER_SAVED])
    A4 = ("a4", [RegisterType.ARGUMENT, RegisterType.CALLER_SAVED])
    A5 = ("a5", [RegisterType.ARGUMENT, RegisterType.CALLER_SAVED])
    A6 = ("a6", [RegisterType.ARGUMENT, RegisterType.CALLER_SAVED])
    A7 = ("a7", [RegisterType.ARGUMENT, RegisterType.CALLER_SAVED])

    # S0 = ("s0", [RegisterType.CALLEE_SAVED]) -> FP
    S1 = ("s1", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S2 = ("s2", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S3 = ("s3", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S4 = ("s4", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S5 = ("s5", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S6 = ("s6", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S7 = ("s7", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S8 = ("s8", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S9 = ("s9", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S10 = ("s10", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])
    S11 = ("s11", [RegisterType.LOCAL, RegisterType.CALLEE_SAVED])


DEC_RV64_IRCJumpType = {
    IRCJumpType.JZ: "beqz",
    IRCJumpType.JNZ: "bnez"
}

RV64_IRBOp_decoder = {
    IRBOp.ADD: "add",
    IRBOp.SUB: "sub",
    IRBOp.MUL: "mul",
    IRBOp.DIV: "div",
    IRBOp.REM: "rem",
    IRBOp.BIT_AND: "and",
    IRBOp.BIT_OR: "or",
    IRBOp.BIT_LSH: "sll",
    IRBOp.BIT_RSH: "srl",
    IRBOp.LOG_AND: "",
    IRBOp.LOG_OR: ""
}
