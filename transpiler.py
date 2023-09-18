from pathlib import Path
from typing import Iterator

from lark import Lark
from lark.visitors import Interpreter, v_args

parser = Lark((Path(__file__).parent / "girvel.lark").read_text())

def _indent(code):
    if isinstance(code, Iterator):
        code = '\n' + '\n'.join(code)

    return code.replace("\n", "\n    ")

ignore = v_args(True)(lambda self, value: value if isinstance(value, str) else self.visit(value))

class GirvelInterpreter(Interpreter):
    start = ignore
    footer = ""

    def module(self, tree):
        return "".join(self.visit_children(tree)) + self.footer

    module_element = ignore

    @v_args(True)
    def include(self, target):
        if target.endswith('.grv"'):
            target = target[:-5] + '.c"'
        return f"#include {target}\n"

    def generic_include(self, tree):
        *assignments, target = self.visit_children(tree)
        if target.endswith('.grv"'):
            target = target[:-5] + '.c"'

        return (
            "\n" +
            ''.join(f"#define {typevar} {typeval}\n" for typevar, typeval in assignments) +
            f"#include {target}\n" +
            ''.join(f"#undef {typevar}" for typevar, _ in assignments) +
            "\n"
        )

    def generic_include_assignment(self, tree):
        return self.visit_children(tree)

    @v_args(True)
    def generic(self, target):
        self.footer = "\n#endif" + self.footer
        return f"#ifdef {target}\n"

    @v_args(True)
    def function_definition(self, signature, expression):
        *code, ret = self.visit_children(expression)

        if len(code) == 0:
            block_content = _indent("\nreturn {};".format(ret))
        else:
            block_content = _indent("\n{};\n\nreturn {};".format(
                ";\n".join(code), ret
            ))

        return ("\n{} {{{}\n}}\n".format(
            self.visit(signature),
            block_content
        ))

    @v_args(True)
    def signature(self, return_type, name, arguments):
        return f"{self.visit(return_type)} {self.visit(name)}{self.visit(arguments)}"

    @v_args(True)
    def function_name(self, *elements):
        return "_".join(elements)

    def arguments(self, tree):
        return f"({', '.join(self.visit_children(tree))})"

    @v_args(True)
    def struct_definition(self, name, *variable_definitions):
        if len(name.children) == 1:
            typename, = name.children
            def_prefix = ""
        else:
            prefix, generics = name.children
            to_concat = [prefix] + generics.children
            def_prefix = "#define CONCAT({}) {}\n".format(
                ', '.join("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i] for i in range(len(to_concat))),
                "##_##".join("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i] for i in range(len(to_concat))),
            ) + "#define _({}) CONCAT({})\n".format(
                ', '.join("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i] for i in range(len(to_concat))),
                ", ".join("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i] for i in range(len(to_concat))),
            )
            typename = "_({})".format(", ".join(to_concat))

        return def_prefix + (
            f"\ntypedef struct {{"
            + _indent(f"{self.visit(d)};" for d in variable_definitions) +
            f"\n}} {typename};\n"
        )

    def type_name(self, tree):
        return '_'.join(self.visit_children(tree))

    def generic_postfix(self, tree):
        return '_'.join(self.visit_children(tree))

    def block(self, tree):
        if len(tree.children) <= 1:
            expression, = self.visit_children(tree)
            return f"({expression})"

        return "({{{};\n}})".format(
            _indent('\n' + ';\n'.join(self.visit_children(tree)))
        )

    def statement_block(self, tree):
        statements = self.visit_children(tree)
        return (
            "{"
            + _indent(f"{s};" for s in statements) +
            "\n}"
        )

    statement = ignore

    def expression(self, tree):
        expression, = self.visit_children(tree)
        return expression

    def variable_definition(self, tree):
        return " ".join(self.visit_children(tree))

    def variable_assignment(self, tree):
        return " ".join(self.visit_children(tree))

    def variable_declaration(self, tree):
        type_, lvalue, rvalue = self.visit_children(tree)
        return f"{type_} {lvalue} = {rvalue}"

    @v_args(True)
    def return_(self, expression):
        return f"return {self.visit(expression)}"

    def break_(self, tree):
        return "break"

    def continue_(self, tree):
        return "continue"

    def identifier(self, tree):
        elements = self.visit_children(tree)
        return ".".join(elements)

    identifier_piece = ignore

    def if_(self, tree):
        condition, if_block, else_block = self.visit_children(tree)
        return f"{condition} ? {if_block} : {else_block}"

    def statement_if(self, tree):
        condition, if_block, *else_block = self.visit_children(tree)
        return f"if ({condition}) {if_block}" + ("" if len(else_block) == 0 else f"\nelse {else_block[0]}")

    def statement_loop(self, tree):
        body, = self.visit_children(tree)
        return f"while (1) {body}"

    operation = ignore

    def infix_operation(self, tree):
        return " ".join(self.visit_children(tree))

    def prefix_operation(self, tree):
        return " ".join(self.visit_children(tree))

    def call(self, tree):
        function, *arguments = self.visit_children(tree)
        return f"{function}({', '.join(arguments)})"

    def constructor(self, tree):
        struct, *elements = self.visit_children(tree)
        return (
            "({"
            + _indent(f"\n{struct} _ = {{{', '.join(elements)}}};\n_;") +
            "\n})"
        )

setattr(GirvelInterpreter, "if", GirvelInterpreter.if_)
del GirvelInterpreter.if_

setattr(GirvelInterpreter, "return", GirvelInterpreter.return_)
del GirvelInterpreter.return_

setattr(GirvelInterpreter, "break", GirvelInterpreter.break_)
del GirvelInterpreter.break_

setattr(GirvelInterpreter, "continue", GirvelInterpreter.continue_)
del GirvelInterpreter.continue_


def transpile(source: str) -> str:
    return GirvelInterpreter().visit(parser.parse(source))
