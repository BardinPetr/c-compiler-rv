from printer.ir import *
from printer.hir import *
from printer.rv64 import RV64Reg


class RVIRTransformer:
    def __init__(self, regmap: Type[Reg]):
        self.regmap = regmap

    def __call__(self, code: IRProg):
        code.functions = [self.process_function(code, i) for i in code.functions]
        return code

    def fun_allocate_vars(self, code: IRProg, fun: IRFun) -> IRFun:
        """
        назначить переменным ir регистры или стек или зарезервированную память.
        добавить псевдо-команды для перехода от одного к другому типов памяти.
        """
        fun.layout = HFunLayout()
        slots = fun.layout.mem_slots

        for i in code.globals:
            if i.name in slots:
                raise Exception(f"redeclared var {i}")
            slots[i.name] = HMemVar(i.name, i.name)

        param_regs = self.regmap.params()
        for i, p in enumerate(fun.params):
            slots[p.name] = HRegVar(p.name, param_regs[i])

        free_regs = self.regmap.scratch()[:]

        # TODO allocate vars

        # TODO insert HIRMoves

        # TODO move inline strings to globals and replace text with label

        return fun

    def fun_prepare_stack(self, fun: IRFun) -> IRFun:
        stack_slots = [i for i in fun.layout.mem_slots.values() if isinstance(i, HStackVar)]
        reg_slots = [i for i in fun.layout.mem_slots.values() if isinstance(i, HRegVar)]
        used_regs = {i.reg for i in reg_slots}

        stack_slot_size = 8
        stack_pos = 0
        for reg in self.regmap.callee_saved():
            if reg not in {RV64Reg.RA, RV64Reg.FP} and reg not in used_regs:
                continue
            fun.layout.stack.append(HStackRegCopy(reg.name, stack_pos, stack_slot_size, reg))
            stack_pos += stack_slot_size

        for i in stack_slots:
            fun.layout.stack.append(HStackVar(i.name, stack_pos, stack_slot_size))
            stack_pos += stack_slot_size

        return fun

    def process_function(self, code: IRProg, fun: IRFun) -> IRFun:
        fun = self.fun_allocate_vars(code, fun)
        fun = self.fun_prepare_stack(fun)
        return fun
