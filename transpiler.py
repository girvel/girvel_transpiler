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

    def module(self, tree):
        return "".join(self.visit_children(tree))

    module_element = ignore

    @v_args(True)
    def include(self, target):
        return f"#include {target}\n"

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
        return f"{return_type} {self.visit(name)}{self.visit(arguments)}"

    @v_args(True)
    def function_name(self, *elements):
        return "_".join(elements)

    def arguments(self, tree):
        return f"({', '.join(self.visit_children(tree))})"

    @v_args(True)
    def struct_definition(self, name, *variable_definitions):
        return (
            f"\ntypedef struct {{"
            + _indent(f"{self.visit(d)};" for d in variable_definitions) +
            f"\n}} {name};\n"
        )

    def block(self, tree):
        if len(tree.children) <= 1:
            expression, = self.visit_children(tree)
            return f"({expression})"

        return "({{{};\n}})".format(
            _indent('\n' + ';\n'.join(self.visit_children(tree)))
        )

    statement = ignore

    def expression(self, tree):
        expression, = self.visit_children(tree)
        return expression

    def variable_definition(self, tree):
        return " ".join(self.visit_children(tree))

    def variable_assignment(self, tree):
        lvalue, rvalue = self.visit_children(tree)
        return f"{lvalue} = {rvalue}"

    def identifier(self, tree):
        elements = self.visit_children(tree)
        return ".".join(elements)

    identifier_piece = ignore

    def if_(self, tree):
        condition, if_block, else_block = self.visit_children(tree)
        return f"{condition} ? {if_block} : {else_block}"

    def operation(self, tree):
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


def transpile(source):
    return GirvelInterpreter().visit(parser.parse(source))
