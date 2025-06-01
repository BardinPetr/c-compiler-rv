from collections.abc import generator
from contextlib import contextmanager

from backend.base.base_transformer import BaseTransformer, TCtx, CtxTransformer
from backend.ir.ir import *
from backend.ir.ir import IRType
from frontend.astdef import *
from frontend.astdef import _Literal, _Expression, ExRdVar
from utils import flatten, random_string


def gvar():
    return "__" + random_string()


@contextmanager
def var() -> str:
    yield gvar()


@contextmanager
def vars(n: int) -> str:
    yield [gvar() for _ in range(n)]


def is_generated(x: str):
    return x.startswith("__")


@dataclass
class LoopCtx(TCtx):
    loop_pre_label: str
    loop_post_label: str
    loop_body_label: str
    loop_chk_label: str


class AST2IR(BaseTransformer, CtxTransformer):
    """ AST -> IR """

    def __init__(self):
        super().__init__()
        self.ex_translator = AST2IRExpr()

    """
        Structural
    """

    def Prog(self, p: Prog):
        return IRProg(
            self(i for i in p.functions.values()),
            self(p.globals)
        )

    def DeclStaticVar(self, x: DeclStaticVar) -> IRGlobal:
        return IRGlobal(
            x.sig.name,
            self(x.sig.type),
            self(x.init)
        )

    def DataType(self, x: DataType) -> Type[IRType]:
        return IRType[x.name]

    def DeclFun(self, x: DeclFun) -> IRFun:
        return IRFun(
            x.sig.name,
            self(x.sig.ret_type),
            params=self(x.sig.args),
            body=flatten(self(x.body)) if x.body is not None else None
        )

    def _Literal(self, x: _Literal) -> IRValue:
        match x:
            case LitInt(x):
                return IRIntValue(x)
            case LitChar(x):
                return IRCharValue(x)
            case LitString(x):
                return IRStringValue(x)

    def VarSig(self, x: VarSig) -> IRFunParam:
        return IRFunParam(x.name, self(x.type))

    """
        Statements
    """

    def StAsn(self, x: StAsn) -> Generator[IRStatement]:
        """ root of expression translation """
        cmds, dst = self.ex_translator.start(x.expr)
        yield from cmds
        yield IRStUnOp(IRUOp.COPY, x.dst, dst)

    def StVarDecl(self, x: StVarDecl) -> Generator[IRStatement]:
        if x.init is not None:
            yield from self(StAsn(x.sig.name, x.init))

    def StReturn(self, x: StReturn) -> Generator[IRStatement]:
        if x is None:
            yield IRStReturn()
            return
        with var() as v:
            yield from self(StAsn(v, x.value))
            yield IRStReturn(v)

    def StContinue(self, _) -> Generator[IRStatement]:
        if (lctx := self.cpeek(LoopCtx)) is None:
            return self.err("no loop ctx for 'continue' statement")
        yield IRStJump(lctx.loop_chk_label)

    def StBreak(self, _) -> Generator[IRStatement]:
        if (lctx := self.cpeek(LoopCtx)) is None:
            return self.err("no loop ctx for 'continue' statement")
        yield IRStJump(lctx.loop_post_label)

    def StWhile(self, x: StWhile) -> Generator[IRStatement]:
        with vars(5) as (pre_label, post_label, body_label, chk_label, chk_var):
            self.cpush(LoopCtx(pre_label, post_label, body_label, chk_label))

            yield IRStatement(label=pre_label)
            yield IRStatement(label=chk_label)

            yield from self(StAsn(chk_var, x.check_expr))
            yield IRStCJump(IRCJumpType.JZ, chk_var, post_label)

            yield IRStatement(label=body_label)
            yield from self(x.body)
            yield IRStJump(chk_label)

            yield IRStatement(label=post_label)

            self.cpop(LoopCtx)

    def StIf(self, x: StIf) -> Generator[IRStatement]:
        with vars(3) as (chk_var, false_label, post_label):
            yield from self(StAsn(chk_var, x.check_expr))
            yield IRStCJump(IRCJumpType.JZ, chk_var, false_label)

            yield from self(x.br_true)
            yield IRStJump(post_label)

            yield IRStatement(label=false_label)
            if x.br_false is not None:
                yield from self(x.br_false)
            yield IRStatement(label=post_label)

    def fallback(self, x):
        if isinstance(x, _Expression):
            yield from list(self(StAsn("__", x)))[:-1]

class AST2IRExpr(BaseTransformer, CtxTransformer):

    def __init__(self):
        super().__init__()
        self.top_var: Optional[str] = None

    def LitInt(self, x: LitInt) -> IRValue:
        return IRIntValue(x.value)

    def LitChar(self, x: LitChar) -> IRValue:
        return IRCharValue(x.value)

    def LitString(self, x: LitString) -> IRValue:
        return IRStringValue(x.value)

    def ExLit(self, x: ExLit):
        with var() as tgt:
            yield IRStStoreValue(tgt, value=self(x.value))
            self.top_var = tgt

    def ExRdVar(self, x: ExRdVar):
        self.top_var = x.name

    def ExCall(self, x: ExCall):
        args = []
        for in_ex in x.args:
            self.top_var = None
            yield from self.unwrap_call(in_ex)
            args.append(self.top_var)

        self.top_var = gvar()
        yield IRStCall(
            fun_name=x.name,
            arg_vars=args,
            assign_var=self.top_var
        )

    def ExUnary(self, x: ExUnary):
        self.top_var = None
        yield from self.unwrap_call(x.value)
        arg = self.top_var

        op = self.UOp(x.cmd)
        if op is not None:
            yield IRStUnOp(op, arg, arg)
            return

        match x.cmd:
            case UOp.UOP_DEC:
                yield IRStStoreValue("1", IRIntValue(1))
                yield IRStBinOp(IRBOp.SUB, arg, arg, "1")
                return
            case UOp.UOP_INC:
                yield IRStStoreValue("1", IRIntValue(1))
                yield IRStBinOp(IRBOp.ADD, arg, arg, "1")
                return

    def ExBinary(self, x: ExBinary):
        match x.cmd:
            case BOp.CMP_LE:
                yield from self(ExBinary(x.exp1, BOp.CMP_LT, ExBinary(x.exp2, BOp.MAT_PLUS, ExLit(LitInt(1)))))
                return
            case BOp.CMP_GE:
                yield from self(ExBinary(x.exp1, BOp.CMP_GT, ExBinary(x.exp2, BOp.MAT_MINUS, ExLit(LitInt(1)))))
                return

        op = self.BOp(x.cmd)
        self.top_var = None
        yield from self.unwrap_call(x.exp1)
        arg1 = self.top_var
        self.top_var = None
        yield from self.unwrap_call(x.exp2)
        arg2 = self.top_var
        dst = arg1 if is_generated(arg1) else gvar()
        yield IRStBinOp(op, dst, arg1, arg2)
        self.top_var = dst

    def UOp(self, x: UOp) -> Optional[IRUOp]:
        return {
            UOp.UOP_NEG: IRUOp.LOG_NEG,
            UOp.UOP_INV: IRUOp.BIT_NEG,
            UOp.UOP_SUB: IRUOp.MINUS
        }.get(x, None)

    def BOp(self, x: BOp) -> IRBOp:
        return {
            BOp.MAT_PLUS: IRBOp.ADD,
            BOp.MAT_MINUS: IRBOp.SUB,
            BOp.MAT_STAR: IRBOp.MUL,
            BOp.MAT_DIV: IRBOp.DIV,
            BOp.MAT_MOD: IRBOp.REM,
            BOp.LOG_AND: IRBOp.BIT_AND,
            BOp.LOG_OR: IRBOp.BIT_OR,
            BOp.LOG_LAND: IRBOp.LOG_AND,
            BOp.LOG_LOR: IRBOp.LOG_OR,
            BOp.LOG_RIGHT: IRBOp.BIT_RSH,
            BOp.LOG_LEFT: IRBOp.BIT_LSH,
            BOp.CMP_LT: IRBOp.CLT,
            BOp.CMP_GT: IRBOp.CGT,
            BOp.CMP_EQ: IRBOp.CEQ,
            BOp.CMP_NE: IRBOp.CNE
        }.get(x, None)

    def unwrap_call(self, x):
        """ with no yields generator would look line None instead """
        res = self(x)
        return list(res) if isinstance(res, generator) else []

    def start(self, x: _Expression):
        self.top_var = None
        res = self.unwrap_call(x)
        return res, self.top_var


def do_ir(prog: Prog) -> IRProg:
    t = AST2IR()
    return t(prog)
