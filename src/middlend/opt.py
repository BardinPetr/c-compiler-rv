from backend.ir.hir import *
from backend.ir.ir import *
from backend.hw.rv64 import RV64Reg
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
        """
        назначить переменным ir регистры или стек или зарезервированную память.
        добавить псевдо-команды для перехода от одного к другому типов памяти.
        """
        if not fun.is_impl: return fun
        fun.layout = HFunLayout()
        slots = fun.layout.mem_slots

        for i in self.ctx.globals:
            if i.name in slots:
                raise Exception(f"redeclared var {i}")
            slots[i.name] = HMemVar(i.name)

        for i, p in enumerate(fun.params):
            slots[p.name] = HStackVar(name=p.name)

        all_locals = detect_locals(fun)
        local_regs_to_assign = self.regmap.locals()

        # в качестве простейшей оптимизации отображаем в регистры наиболее часто используемые переменные
        # увы, времени на что-то более адекватное (например отслеживать времена жизни переменных) времени у нас не хватило
        locals_to_assign = sorted(all_locals.items(), key=lambda x: -sum(x[1]))
        for name, (use_r, _) in locals_to_assign:
            if name in slots:  # могут попасться имена которые уже кудато сосланы
                continue
            if len(local_regs_to_assign) > 0 and \
                    use_r > 0:  # игнорируем те переменные, что не читаются
                reg = local_regs_to_assign.pop(0)
                # назначаем регистр
                slots[name] = HRegVar(reg, name=name)
            else:
                # когда кончились регистры, оставшиеся переменные загоняем на стек
                slots[name] = HStackVar(name=name)

        # print("-" * 10, fun.name)
        # print(slots)

        return fun

    def fun_add_var_moves(self, fun: IRFun) -> IRFun:
        """
        вставить адаптеры когда надо чтобы переменная оказалась в регистре (и наоборот),
        а ее внезапно аллоцировали не в регистр, а в память (стек)
        """
        if not fun.is_impl: return fun
        res = []
        for i in fun.body:
            allowed_regs = self.regmap.one_time()
            in_repl, out_repl = {}, {}
            in_mov, out_mov = [], []
            for typ, arr in [('in', i.v_inputs), ('out', i.v_outputs)]:
                for v_name in arr:
                    v_orig = fun.layout.mem_slots[v_name]
                    if not isinstance(v_orig, HRegVar):
                        v_tmp_name = random_string(4)
                        v_tmp_reg = allowed_regs.pop()
                        v_tmp = HRegVar(v_tmp_reg, name=v_name)

                        fun.layout.mem_slots[v_tmp_name] = v_tmp
                        if typ == 'in':
                            in_repl[v_name] = v_tmp_name
                            in_mov.append((v_orig, v_tmp))
                        else:
                            out_repl[v_name] = v_tmp_name
                            out_mov.append((v_tmp, v_orig))

            for src, dst in in_mov:
                res.append(HIRMove(src, dst))

            res.append(statement_substitute_vars(i, in_repl, out_repl))

            for src, dst in out_mov:
                res.append(HIRMove(src, dst))

        fun.body = res
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
                v.value.value = label  # replace actual string with label
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
        fun = self.fun_add_var_moves(fun)
        return fun


def detect_locals(fun: IRFun) -> Dict[str, Tuple[int, int]]:
    """
    найти используемые переменные, заодно оценить частоту использования
    :return (r, w)
    """
    if not fun.is_impl: return {}

    result = {}
    for i in fun.body:
        if isinstance(i, IRStatement):
            for v in i.v_inputs:
                if v not in result: result[v] = [0, 0]
                result[v][0] += 1
            for v in i.v_outputs:
                if v not in result: result[v] = [0, 0]
                result[v][1] += 1
    return result


def statement_substitute_vars(x: IRStatement, irepl: Dict[str, str], orepl: Dict[str, str]) -> IRStatement:
    match x:
        case IRStStoreValue(dest, _):
            x.dest = orepl.get(dest, dest)
        case IRStBinOp(_, dest, arg1, arg2):
            x.dest = orepl.get(dest, dest)
            x.arg1 = irepl.get(arg1, arg1)
            x.arg2 = irepl.get(arg2, arg2)
        case IRStUnOp(_, dest, arg):
            x.dest = orepl.get(dest, dest)
            x.arg = irepl.get(arg, arg)
        case IRStCJump(_, checked_var, _):
            x.checked_var = irepl.get(checked_var, checked_var)
        case IRStReturn(var) if var is not None:
            x.var = irepl.get(var, var)
        case IRStCall(_, arg_vars, assign_var):
            x.arg_vars = [irepl.get(i, i) for i in arg_vars]
            x.assign_var = orepl.get(assign_var, assign_var)
    return x
