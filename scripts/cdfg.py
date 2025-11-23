from __future__ import absolute_import, print_function
import sys
import os
from optparse import OptionParser

import pyverilog
from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import *

# --------------------------- Utilities ---------------------------

def get_lineno(node):
    """Return line number as string if available, else '0'."""
    coord = getattr(node, "coord", None)
    if coord is not None and hasattr(coord, "lineno") and coord.lineno is not None:
        return str(coord.lineno)
    return "0"

def sens_to_str(sens_list):
    """Pretty string for sensitivity list."""
    if not sens_list:
        return "@(*)"
    if isinstance(sens_list, SensList):
        parts = []
        for s in sens_list.list or []:
            if isinstance(s, Sens):
                sig = str(s.sig) if s.sig is not None else "*"
                parts.append(f"{s.type} {sig}" if s.type in ("posedge","negedge") else sig)
        return "@(" + ", ".join(parts) + ")"
    return "@(?)"

# Convert expressions to readable Verilog-like strings
def expr_to_str(node):
    if node is None:
        return ""

    # Identifiers
    if isinstance(node, Identifier):
        return str(node)

    # Constants
    if isinstance(node, IntConst):    return node.value
    if isinstance(node, FloatConst):  return node.value
    if isinstance(node, StringConst): return '"' + node.value + '"'

    # UnsizedConst (older versions may not have it)
    if hasattr(pyverilog.vparser.ast, "UnsizedConst"):
        if isinstance(node, pyverilog.vparser.ast.UnsizedConst):
            return node.value

    # Indexing/partselect/concat/repeat
    if isinstance(node, Pointer):     return f"{expr_to_str(node.var)}[{expr_to_str(node.ptr)}]"
    if isinstance(node, Partselect):  return f"{expr_to_str(node.var)}[{expr_to_str(node.msb)}:{expr_to_str(node.lsb)}]"
    if isinstance(node, Concat):      return "{" + ", ".join(expr_to_str(x) for x in (node.list or [])) + "}"
    if isinstance(node, Repeat):      return "{" + expr_to_str(node.times) + "{" + expr_to_str(node.value) + "}" + "}"

    # Unary ops
    if isinstance(node, Ulnot): return "!" + expr_to_str(node.right)
    if isinstance(node, Unot):  return "~" + expr_to_str(node.right)
    if isinstance(node, Uminus):return "-" + expr_to_str(node.right)
    if isinstance(node, Uplus): return "+" + expr_to_str(node.right)
    if isinstance(node, Uand):  return "&" + expr_to_str(node.right)
    if isinstance(node, Uor):   return "|" + expr_to_str(node.right)
    if isinstance(node, Uxor):  return "^" + expr_to_str(node.right)
    if isinstance(node, Uxnor): return "~^" + expr_to_str(node.right)
    if isinstance(node, Unand): return "~&" + expr_to_str(node.right)
    if isinstance(node, Unor):  return "~|" + expr_to_str(node.right)

    # Binary helpers
    def bin(node, op):
        left  = expr_to_str(getattr(node, "left", None))
        right = expr_to_str(getattr(node, "right", None))
        return f"({left} {op} {right})"

    # Binary ops
    if isinstance(node, Plus):         return bin(node, "+")
    if isinstance(node, Minus):        return bin(node, "-")
    if isinstance(node, Times):        return bin(node, "*")
    if isinstance(node, Divide):       return bin(node, "/")
    if isinstance(node, Mod):          return bin(node, "%")
    if isinstance(node, Power):        return bin(node, "**")
    if isinstance(node, Sll):          return bin(node, "<<")
    if isinstance(node, Srl):          return bin(node, ">>")
    if isinstance(node, Sla):          return bin(node, "<<<")
    if isinstance(node, Sra):          return bin(node, ">>>")
    if isinstance(node, LessThan):     return bin(node, "<")
    if isinstance(node, GreaterThan):  return bin(node, ">")
    if isinstance(node, LessEq):       return bin(node, "<=")
    if isinstance(node, GreaterEq):    return bin(node, ">=")
    if isinstance(node, Eq):           return bin(node, "==")
    if isinstance(node, NotEq):        return bin(node, "!=")
    if isinstance(node, Eql):          return bin(node, "===")
    if isinstance(node, NotEql):       return bin(node, "!==")
    if isinstance(node, And):          return bin(node, "&")
    if isinstance(node, Or):           return bin(node, "|")
    if isinstance(node, Xor):          return bin(node, "^")
    if isinstance(node, Xnor):         return bin(node, "~^")
    if isinstance(node, Land):         return bin(node, "&&")
    if isinstance(node, Lor):          return bin(node, "||")

    # Conditional (?:)
    if isinstance(node, Cond):
        c  = expr_to_str(node.cond)
        t  = expr_to_str(node.true_value)
        f  = expr_to_str(node.false_value)
        return f"({c}) ? {t} : {f}"

    # Function calls
    if isinstance(node, FunctionCall):
        args = ", ".join(expr_to_str(a) for a in (node.args or []))
        return f"{expr_to_str(node.name)}({args})"

    return str(node)

def lvalue_to_str(lv):
    """Pretty string for an Lvalue node (left side of assignments)."""
    if isinstance(lv, Lvalue):
        return expr_to_str(lv.var)
    return expr_to_str(lv)

def extract_identifiers(node, ids=None):
    """Collect all Identifier names used within an expression subtree."""
    if ids is None:
        ids = []
    if node is None:
        return ids
    if isinstance(node, Identifier):
        ids.append(str(node))
        return ids
    for c in node.children():
        extract_identifiers(c, ids)
    return ids

# --------------------------- CFG Builder ---------------------------

def cfg_build_for_module(module):
    lines = []
    header = f"Module {module.name}"
    lines.append(header)

    for item in (module.items or []):
        if isinstance(item, Assign):
            lhs = lvalue_to_str(item.left)
            rhs_node = item.right.var if isinstance(item.right, Rvalue) else item.right
            rhs = expr_to_str(rhs_node)
            lines.append(f"  - assign {lhs} = {rhs}")

        elif isinstance(item, Always):
            sens = sens_to_str(item.sens_list)
            lines.append(f"  - always {sens}")
            cfg_walk_statement(item.statement, lines, indent=4)

        elif isinstance(item, Initial):
            lines.append(f"  - initial")
            cfg_walk_statement(item.statement, lines, indent=4)

    return lines

def cfg_walk_statement(stmt, lines, indent=0):
    sp = " " * indent
    if stmt is None:
        return

    if isinstance(stmt, Block):
        for s in (stmt.statements or []):
            cfg_walk_statement(s, lines, indent=indent)

    elif isinstance(stmt, ParallelBlock):
        lines.append(f"{sp}- parallel begin")
        for s in (stmt.statements or []):
            cfg_walk_statement(s, lines, indent=indent+2)
        lines.append(f"{sp}- parallel end")

    elif isinstance(stmt, SingleStatement):
        cfg_walk_statement(stmt.statement, lines, indent=indent)

    elif isinstance(stmt, (BlockingSubstitution, NonblockingSubstitution)):
        lhs = lvalue_to_str(stmt.left)
        rhs_node = stmt.right.var if isinstance(stmt.right, Rvalue) else stmt.right
        rhs = expr_to_str(rhs_node)
        op  = "<=" if isinstance(stmt, NonblockingSubstitution) else "="
        lines.append(f"{sp}- {lhs} {op} {rhs}")

    elif isinstance(stmt, IfStatement):
        cond = expr_to_str(stmt.cond)
        lines.append(f"{sp}- if ({cond})")
        cfg_walk_statement(stmt.true_statement, lines, indent=indent+2)
        if stmt.false_statement is not None:
            lines.append(f"{sp}- else")
            cfg_walk_statement(stmt.false_statement, lines, indent=indent+2)

    elif isinstance(stmt, CaseStatement):
        tag = "case"
        if isinstance(stmt, CasexStatement): tag = "casex"
        if isinstance(stmt, CasezStatement): tag = "casez"
        if isinstance(stmt, UniqueCaseStatement): tag = "unique case"
        comp = expr_to_str(stmt.comp)
        lines.append(f"{sp}- {tag} ({comp})")
        for c in (stmt.caselist or []):
            conds = [expr_to_str(v) for v in (c.cond or [])] if c.cond else ["default"]
            cond_label = ", ".join(conds)
            lines.append(f"{sp}  * {cond_label}:")
            cfg_walk_statement(c.statement, lines, indent=indent+4)

    elif isinstance(stmt, ForStatement):
        pre  = expr_to_str(stmt.pre)
        cond = expr_to_str(stmt.cond)
        post = expr_to_str(stmt.post)
        lines.append(f"{sp}- for ({pre}; {cond}; {post})")
        cfg_walk_statement(stmt.statement, lines, indent=indent+2)

    elif isinstance(stmt, WhileStatement):
        cond = expr_to_str(stmt.cond)
        lines.append(f"{sp}- while ({cond})")
        cfg_walk_statement(stmt.statement, lines, indent=indent+2)

    elif isinstance(stmt, EventStatement):
        lines.append(f"{sp}- event {sens_to_str(stmt.senslist)}")

    elif isinstance(stmt, WaitStatement):
        cond = expr_to_str(stmt.cond)
        lines.append(f"{sp}- wait ({cond})")
        cfg_walk_statement(stmt.statement, lines, indent=indent+2)

    elif isinstance(stmt, DelayStatement):
        d  = expr_to_str(stmt.delay)
        lines.append(f"{sp}- delay #{d}")

    elif isinstance(stmt, TaskCall):
        name = expr_to_str(stmt.name)
        args = ", ".join(expr_to_str(a) for a in (stmt.args or []))
        lines.append(f"{sp}- {name}({args})")

    elif isinstance(stmt, FunctionCall):
        args = ", ".join(expr_to_str(a) for a in (stmt.args or []))
        lines.append(f"{sp}- call {expr_to_str(stmt.name)}({args})")

    else:
        lines.append(f"{sp}- {stmt.__class__.__name__}")

# --------------------------- DFG Builder ---------------------------

def dfg_build_for_module(module):
    edges = []
    def add_edges_from_assignment(lhs_lvalue, rhs_expr, line_str):
        dst = lvalue_to_str(lhs_lvalue)
        srcs = extract_identifiers(rhs_expr)
        for s in srcs:
            edges.append((s, dst, line_str))

    for item in (module.items or []):
        if isinstance(item, Assign):
            rhs_node = item.right.var if isinstance(item.right, Rvalue) else item.right
            add_edges_from_assignment(item.left, rhs_node, get_lineno(item))
        elif isinstance(item, Always):
            dfg_walk_statement(item.statement, add_edges_from_assignment)
        elif isinstance(item, Initial):
            dfg_walk_statement(item.statement, add_edges_from_assignment)

    deps_by_dst = {}
    for s, d, _ln in edges:
        deps_by_dst.setdefault(d, set()).add(s)
    deps_by_dst = {k: sorted(list(v)) for k, v in deps_by_dst.items()}
    return edges, deps_by_dst

def dfg_walk_statement(stmt, add_edges_fn):
    if stmt is None:
        return

    if isinstance(stmt, Block):
        for s in (stmt.statements or []):
            dfg_walk_statement(s, add_edges_fn)

    elif isinstance(stmt, ParallelBlock):
        for s in (stmt.statements or []):
            dfg_walk_statement(s, add_edges_fn)

    elif isinstance(stmt, SingleStatement):
        dfg_walk_statement(stmt.statement, add_edges_fn)

    elif isinstance(stmt, (BlockingSubstitution, NonblockingSubstitution)):
        rhs_node = stmt.right.var if isinstance(stmt.right, Rvalue) else stmt.right
        add_edges_fn(stmt.left, rhs_node, get_lineno(stmt))

    elif isinstance(stmt, IfStatement):
        dfg_walk_statement(stmt.true_statement, add_edges_fn)
        if stmt.false_statement is not None:
            dfg_walk_statement(stmt.false_statement, add_edges_fn)

    elif isinstance(stmt, CaseStatement):
        for c in (stmt.caselist or []):
            dfg_walk_statement(c.statement, add_edges_fn)

    elif isinstance(stmt, ForStatement):
        dfg_walk_statement(stmt.statement, add_edges_fn)

    elif isinstance(stmt, WhileStatement):
        dfg_walk_statement(stmt.statement, add_edges_fn)

    elif isinstance(stmt, WaitStatement):
        dfg_walk_statement(stmt.statement, add_edges_fn)

# --------------------------- Driver ---------------------------

def create_cdfg(filename, include=None, define=None):
    if not os.path.exists(filename):
        raise IOError(f"file not found: {filename}")

    ast, directives = parse([filename],
                            preprocess_include=include or [],
                            preprocess_define=define or [])

    description = ast.description
    if description is None or not hasattr(description, "definitions"):
        return "No modules found.", ""

    modules = [d for d in description.definitions if isinstance(d, ModuleDef)]
    if not modules:
        return "No modules found.", ""

    cfg = ""
    dfg = ""

    for m in modules:
        cfg_lines = cfg_build_for_module(m)
        cfg += f"########################################################################\n"
        cfg += f"CONTROL FLOW (CFG) for module {m.name}\n"
        cfg += f"########################################################################\n"
        cfg += "\n".join(cfg_lines) + "\n"

        edges, deps_by_dst = dfg_build_for_module(m)
        dfg += f"########################################################################\n"
        dfg += f"DATA FLOW (DFG) for module {m.name}\n"
        dfg += f"########################################################################\n"
        if deps_by_dst:
            dfg += "Dependencies per signal:\n"
            for dst, srcs in sorted(deps_by_dst.items()):
                sources = ", ".join(srcs) if srcs else "(none)"
                dfg += f"  - {dst} depends on: {sources}\n"
        else:
            dfg += "(no data dependencies found)\n"
        if edges:
            dfg += "\nEdges (src -> dst):\n"
            for s, d, ln in edges:
                dfg += f"  {s} -> {d}\n"
        dfg += "\n"
    
    # print(cfg, dfg)
    return cfg, dfg

def main():
    INFO = "Verilog code parser (CFG/DFG textual)"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python cdfg_textual.py file ..."

    def show_version_and_exit():
        print(INFO)
        print(VERSION)
        print(USAGE)
        sys.exit(0)

    optparser = OptionParser()
    optparser.add_option("-v", "--version", action="store_true", dest="showversion",
                         default=False, help="Show the version")
    optparser.add_option("-I", "--include", dest="include", action="append",
                         default=[], help="Include path")
    optparser.add_option("-D", dest="define", action="append",
                         default=[], help="Macro Definition")
    (options, args) = optparser.parse_args()

    if options.showversion or len(args) == 0:
        show_version_and_exit()

    for f in args:
        if not os.path.exists(f):
            raise IOError("file not found: " + f)

    ast, directives = parse(args,
                            preprocess_include=options.include,
                            preprocess_define=options.define)

    description = ast.description
    if description is None or not hasattr(description, "definitions"):
        print("No modules found.")
        return

    modules = [d for d in description.definitions if isinstance(d, ModuleDef)]
    if not modules:
        print("No modules found.")
        return

    cfg = ""
    dfg = ""

    for m in modules:
        cfg_lines = cfg_build_for_module(m)
        cfg += f"########################################################################\n"
        cfg += f"CONTROL FLOW (CFG) for module {m.name}\n"
        cfg += f"########################################################################\n"
        cfg += "\n".join(cfg_lines) + "\n"

        edges, deps_by_dst = dfg_build_for_module(m)
        dfg += f"########################################################################\n"
        dfg += f"DATA FLOW (DFG) for module {m.name}\n"
        dfg += f"########################################################################\n"
        if deps_by_dst:
            dfg += "Dependencies per signal:\n"
            for dst, srcs in sorted(deps_by_dst.items()):
                sources = ", ".join(srcs) if srcs else "(none)"
                dfg += f"  - {dst} depends on: {sources}\n"
        else:
            dfg += "(no data dependencies found)\n"
        if edges:
            dfg += "\nEdges (src -> dst):\n"
            for s, d, ln in edges:
                dfg += f"  {s} -> {d}\n"
        dfg += "\n"

    # print(cfg, dfg)

if __name__ == "__main__":
    main()
