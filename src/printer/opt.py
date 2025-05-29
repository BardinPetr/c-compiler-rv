from printer.ir import *
from printer.hir import *
from printer.rv64 import RV64Reg
from utils import random_string


class RV64IR2HIRTransformer:
    def __init__(self, regmap: Type[Reg]):
        self.regmap = regmap
        self.ctx: Optional[IRProg] = None

    def __call__(self, code: IRProg):
        self.ctx = code
        self.ctx.functions = [self.process_function(i) for i in self.ctx.functions]
        return self.ctx

    def fun_allocate_vars(self, fun: IRFun) -> IRFun:
        if not fun.is_impl: return fun
        """
        назначить переменным ir регистры или стек или зарезервированную память.
        добавить псевдо-команды для перехода от одного к другому типов памяти.
        """
        fun.layout = HFunLayout()
        slots = fun.layout.mem_slots

        for i in self.ctx.globals:
            if i.name in slots:
                raise Exception(f"redeclared var {i}")
            slots[i.name] = HMemVar(i.name)

        for i, p in enumerate(fun.params):
            slots[p.name] = HStackVar(name=p.name)

        free_regs = self.regmap.scratch()[:]

        slots['a'] = HRegVar(RV64Reg.T1)
        slots['b'] = HRegVar(RV64Reg.T2)
        slots['c'] = HRegVar(RV64Reg.T3)
        slots['d'] = HRegVar(RV64Reg.T4)
        # slots['d'] = HStackVar()

        # TODO allocate vars

        # TODO insert HIRMoves

        return fun

    def fun_extract_strings(self, fun: IRFun) -> IRFun:
        if not fun.is_impl: return fun
        for i in range(len(fun.body)):
            v = fun.body[i]
            if isinstance(v, IRStStoreValue) and isinstance(v.value, IRStringValue):
                label = random_string(16)
                self.ctx.globals.append(
                    IRGlobal(label, IRType.STRING, IRStringValue(v.value.value))
                )
                v.value.value = label # replace actual string with label
        return fun

    def fun_prepare_stack(self, fun: IRFun) -> IRFun:
        if not fun.is_impl: return fun
        used_regs = {i.reg for i in fun.layout.mem_slots.values() if isinstance(i, HRegVar)}

        stack_slot_size = 8
        stack_pos = 0
        for reg in self.regmap.callee_saved():
            if reg not in {RV64Reg.RA, RV64Reg.FP} and reg not in used_regs:
                continue
            fun.layout.stack.append(HStackRegCopy(stack_pos, stack_slot_size, reg.name, reg))
            stack_pos += stack_slot_size

        for key in fun.layout.mem_slots:
            v = fun.layout.mem_slots[key]
            if isinstance(v, HStackVar):
                v.pos = stack_pos
                fun.layout.stack.append(v)
                stack_pos += stack_slot_size

        return fun

    def process_function(self, fun: IRFun) -> IRFun:
        fun = self.fun_extract_strings(fun)
        fun = self.fun_allocate_vars(fun)
        fun = self.fun_prepare_stack(fun)
        return fun
