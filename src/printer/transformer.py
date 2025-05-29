import dataclasses

from printer.emitter import Emitter, BaseTransformer
from printer.hir import *
from printer.hir import HRegVar
from printer.ir import *
from printer.opt import RV64IR2HIRTransformer
from printer.rv64 import DEC_RV64_IRCJumpType, RV64Reg, RV64_IRBOp_decoder
from tests.qemu import run_qemu
from utils import string_escape


@dataclass
class Context:
    globals: Dict[str, HMemVar] = dataclasses.field(default_factory=dict)
    functions: Dict[str, IRFun] = dataclasses.field(default_factory=dict)
    current_function: Optional[IRFun] = None

    @property
    def global_names(self) -> List[str]:
        return [*self.globals.keys(), ]

class RV64IR2ASMTransformer(BaseTransformer, Emitter):
    TYPE_DECODER_FOR_DECL = {
        IRType.INT: "quad",
        IRType.CHAR: "byte",
        IRType.STRING: "string",
    }
    TYPE_DECODER_SIZE_BYTE = {
        IRType.INT: 8,
        IRType.CHAR: 1,
        IRType.STRING: 8,
    }

    def __init__(self):
        super().__init__()
        self.ctx = Context()
        self.regmap = RV64Reg

    @property
    def fun(self) -> Optional[IRFun]:
        return self.ctx.current_function

    def slot(self, name) -> Optional[HVar]:
        """
        find variable by name (fun ctx then global ctx)
        """
        if (slot := self.fun.layout.mem_slots.get(name, None)) is not None:
            return slot
        if (slot := self.ctx.globals.get(name, None)) is not None:
            return slot

    def rvar(self, name):
        """
        find variable in allocation table by name.
        check that it is assigned to register.
        return register name
        """
        slot = self.slot(name)
        if slot is None:
            self.throw("var", name, "not found")
        if not isinstance(slot, HRegVar):
            self.throw(f"var '{name}' was not physically assigned to register (needed reg var, got {slot})")
        return slot.reg.code

    """
    Definitions
    """

    def IRGlobal(self, glob: IRGlobal):
        name = glob.name
        if name in self.ctx.global_names:
            self.throw("name", name, "already exists")

        typ = self.TYPE_DECODER_FOR_DECL[glob.type]
        match glob:
            case IRGlobal(_, IRType.INT, IRIntValue(x) | x):
                val = x if x is not None else 0
                self.emit_label(name)
                self.emit(f".{typ}", val)

            case IRGlobal(_, IRType.CHAR, IRCharValue(x) | x):
                val = ord(x[0]) if x is not None else 0
                self.emit_label(name)
                self.emit(f".{typ}", val)

            case IRGlobal(_, IRType.STRING, IRStringValue(x)):
                val = '"' + string_escape(x) + '"'
                ptr = "__" + name
                self.emit_label(ptr)
                self.emit(f".{typ}", val)
                self.emit_label(name)
                self.emit(".dword", ptr)

            case _:
                self.throw("invalid global", name)
                return

        self.ctx.globals[name] = HMemVar(name)

    def IRFun(self, x: IRFun):
        if not x.is_impl: return
        m_layout = x.layout

        # PROLOGUE
        self.emit_label(x.name)
        # allocate locals on stack
        stack_size = sum(i.size for i in m_layout.stack)
        self.emit("addi", "sp", "sp", -stack_size)
        # save regs
        for slot in m_layout.stack:
            if isinstance(slot, HStackRegCopy):
                self.emit("sd", slot.reg.code, f"{slot.pos}(sp)")
        # save args
        for param_reg, param in zip(self.regmap.params(), x.params):
            param_slot = m_layout.mem_slots[param.name]
            if isinstance(param_slot, HStackVar):
                self.emit("sd", param_reg.code, f"{param_slot.pos}(sp)")

        # BODY
        self.ctx.current_function = x
        self(x.body)
        self.ctx.current_function = None

        # EPILOGUE
        self.emit_label(x.exit_label)  # to return from function just jump here
        # restore saved
        for slot in m_layout.stack[::-1]:
            if isinstance(slot, HStackRegCopy):
                self.emit("ld", slot.reg.code, f"{slot.pos}(sp)")
        # deallocate locals
        self.emit("addi", "sp", "sp", stack_size)
        # return back
        self.emit("jr", "ra")

    def IRProg(self, x: IRProg):
        self.emit(".align", 2)

        ###
        self.emit_section("data")
        self(x.globals)

        ###
        self.emit_section("bss")
        self.emit(".align", 4)

        self.emit_label("stack_bottom")
        self.emit(".space", 4096)
        self.emit_label("stack_top")

        ###
        self.emit_section("text")
        self.emit(".global", "_start")

        self.emit_label("_start")
        # assert single-core operation
        self.emit("csrr", "t0", "mhartid")
        self.emit("bnez", "t0", "halt")
        self.emit("la", "sp", "stack_top")
        self.emit("j", "main")

        self.ctx.functions = {i.name : i for i in x.functions}
        self(x.functions)

        self.emit_label("halt")
        self.emit("j", "halt")

    """
    Memory moves for abstract memory locations (HVar)
    """

    def HIRMove(self, x: HIRMove):
        match x:
            case HIRMove(HRegVar(src_reg), HRegVar(dst_reg)):
                self.emit("addi", dst_reg.code, src_reg.code, 0)
            case HIRMove(HRegVar(src_reg), HStackVar(dst_stk_pos, _)):
                self.emit("sd", src_reg.code, f"{dst_stk_pos}(sp)")
            case HIRMove(HStackVar(src_stk_pos, _), HRegVar(dst_reg)):
                self.emit("ld", dst_reg.code, f"{src_stk_pos}(sp)")
            case HIRMove(HRegVar(src_reg), HMemVar(dst_mem_lbl)):
                self.emit("la", "t0", dst_mem_lbl)
                self.emit("sd", src_reg.code, "0(t0)")
            case HIRMove(HMemVar(src_mem_lbl), HRegVar(dst_reg)):
                self.emit("la", "t0", src_mem_lbl)
                self.emit("ld", dst_reg.code, "0(t0)")
            case _:
                self.throw("invalid HIRMove combination", x.src, x.dst)

    """
    Statements
    """

    def IRStatement(self, x: IRStatement):
        # before each statement, emit label if exists
        if x.label is not None:
            self.emit_label(x.label)

    def IRStReturn(self, x: IRStReturn):
        original_ret_var = self.fun.layout.mem_slots.get(x.var, None)
        if original_ret_var is None:
            self.throw("not existing var", x.var)
        # меняем псевдо-возврат IR на запись возвращаемого значения из "переменной" в A0 и переход к эпилогу
        self([
            HIRMove(src=original_ret_var, dst=HRegVar(self.regmap.ret()[0])),
            IRStJump(target=self.fun.exit_label)
        ])

    def IRStCall(self, x: IRStCall):
        fun = self.ctx.functions.get(x.fun_name, None)
        if fun is None:
            self.throw("not existing function", x.fun_name)
        if len(fun.params) != len(x.arg_vars):
            self.throw("args invalid for function", x.fun_name)
        self([
            HIRMove(src=self.slot(src_var), dst=HRegVar(param_reg))
            for param_reg, src_var in zip(self.regmap.params(), x.arg_vars)
        ]) # пишем из переменных в регистры по calling conv
        self.emit("call", x.fun_name)
        if x.assign_var is not None:
            self([HIRMove(src=HRegVar(RV64Reg.ret()[0]), dst=self.slot(x.assign_var))])

    def IRStJump(self, x: IRStJump):
        self.emit("j", x.target)

    def IRStCJump(self, x: IRStCJump):
        self.emit(
            DEC_RV64_IRCJumpType[x.check_type],
            self.rvar(x.checked_var),
            x.label
        )

    def emit_reg_op(self, op, *args):
        self.emit(op, *[self.rvar(i) for i in args])

    def IRStBinOp(self, x: IRStBinOp):
        match x.operation:
            case IRBOp.CLT:
                self.emit_reg_op("slt", x.dest, x.arg1, x.arg2)
            case IRBOp.CGT:
                self.emit_reg_op("slt", x.dest, x.arg2, x.arg1)
            case IRBOp.CEQ:
                self.emit("sub", "t0", self.rvar(x.arg1), self.rvar(x.arg2))
                self.emit("seqz", self.rvar(x.dest), "t0")
            case IRBOp.CNE:
                self.emit("sub", "t0", self.rvar(x.arg1), self.rvar(x.arg2))
                self.emit("snez", self.rvar(x.dest), "t0")
            case IRBOp.LOG_AND:
                self.emit("and", "t0", self.rvar(x.arg1), self.rvar(x.arg2))
                self.emit("andi", self.rvar(x.dest), "t0", "1")
            case IRBOp.LOG_OR:
                self.emit("or", "t0", self.rvar(x.arg1), self.rvar(x.arg2))
                self.emit("andi", self.rvar(x.dest), "t0", "1")
            case _:
                default_cmd = RV64_IRBOp_decoder.get(x.operation, None)
                if default_cmd is None:
                    self.throw(f"cannot decode ir {x} to asm")
                self.emit_reg_op(default_cmd, x.dest, x.arg1, x.arg2)

    def IRStUnOp(self, x: IRStUnOp):
        match x.operation:
            case IRUOp.MINUS:
                self.emit_reg_op("neg", x.dest, x.arg)
            case IRUOp.BIT_NEG:
                self.emit_reg_op("not", x.dest, x.arg)
            case IRUOp.LOG_NEG:
                self.emit("not", "t0", self.rvar(x.arg))
                self.emit("andi", self.rvar(x.dest), "t0", "1")
            case _:
                self.throw(f"cannot decode ir {x} to asm")

    def IRStStoreValue(self, x: IRStStoreValue):
        match x.value:
            case IRIntValue(ival):
                self.emit("li", "t0", ival)
            case IRCharValue(csval):
                self.emit("li", "t0", ord(csval[0]))
            case IRStringValue(label):
                self(HIRMove(src=HMemVar(label), dst=self.slot(x.dest)))
                return
        self(HIRMove(
            src=HRegVar(reg=self.regmap.T0),
            dst=self.slot(x.dest)
        ))


def do_asm(ir: IRProg):
    opt = RV64IR2HIRTransformer(RV64Reg)
    ir = opt(ir)

    trf = RV64IR2ASMTransformer()
    trf(ir)

    return trf.get()


res = do_asm(
    IRProg(
        functions=[
            IRFun("puts", IRType.VOID, [IRFunParam("s", IRType.STRING)]),
            IRFun("putc", IRType.VOID, [IRFunParam("c", IRType.CHAR)]),
            IRFun("demo", IRType.INT, [IRFunParam("par", IRType.INT)], [
                IRStStoreValue("d", IRIntValue(48)),
                # IRStBinOp(IRBOp.ADD, "d", "d", "par"),
                IRStReturn("d")
            ]),
            IRFun(
                "main",
                IRType.INT,
                [IRFunParam("par_i", IRType.INT), IRFunParam("par_j", IRType.CHAR), IRFunParam("par_s", IRType.STRING)],
                [
                    IRStCall("puts", ["gvar_str"], label="l1"),

                    IRStStoreValue("d", IRCharValue("%")),
                    IRStCall("putc", ["d"]),

                    IRStStoreValue("d", IRStringValue("\n\n\n-----HELLOW!\n\n -> ")),
                    IRStCall("puts", ["d"]),

                    # IRStJump("l1"),

                    IRStStoreValue("a", IRIntValue(2)),
                    IRStCall("demo", ["a"], assign_var="a"),
                    IRStStoreValue("b", IRIntValue(2)),
                    IRStStoreValue("c", IRIntValue(4)),
                    IRStBinOp(IRBOp.ADD, "d", "a", "c"),
                    IRStCall("putc", ["d"]),
                    IRStBinOp(IRBOp.SUB, "d", "d", "b"),
                    IRStCall("putc", ["d"]),

                    # IRStCall("test", ["a", "par_i", "c"]),
                    IRStReturn("par_j")
                ]
            )
        ],
        globals=[
            # IRGlobal("gvar_nd_int", IRType.INT),
            IRGlobal("gvar_int", IRType.INT, IRIntValue(48)),
            # IRGlobal("gvar_nd_char", IRType.CHAR),
            # IRGlobal("gvar_char", IRType.CHAR, IRCharValue('\n')),
            IRGlobal("gvar_str", IRType.STRING, IRStringValue("hellow\torld\n\t\t!!!!")),
        ]
    )
)
print(res)
print(run_qemu(res))
