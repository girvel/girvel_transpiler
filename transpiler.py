from pathlib import Path

from lark import Lark
from lark.visitors import Interpreter, v_args

parser = Lark(Path("girvel.lark").read_text())

def _indent(code):
    return code.replace("\n", "\n    ")

class GirvelInterpreter(Interpreter):
    @v_args(True)
    def start(self, module):
        return self.visit(module)

    def module(self, tree):
        return "".join(self.visit_children(tree))

    @v_args(True)
    def include(self, target):
        return f"#include {target}\n"

    @v_args(True)
    def function_definition(self, signature, block):
        return (
            f"\n{self.visit(signature)} {{" +
            _indent(f"\nreturn {self.visit(block)};") +
            f"\n}}\n"
        )

    @v_args(True)
    def signature(self, return_type, name, arguments):
        return f"{return_type} {name}{self.visit(arguments)}"

    def arguments(self, tree):
        return f"({', '.join(self.visit_children(tree))})"

    def block(self, tree):
        if len(tree.children) <= 1:
            expression, = self.visit_children(tree)
            return f"({expression})"

        return "({{{};\n}})".format(
            _indent('\n' + ';\n'.join(self.visit_children(tree)))
        )

    def expression(self, tree):
        expression, = self.visit_children(tree)
        return expression

    def if_(self, tree):
        condition, if_block, else_block = self.visit_children(tree)
        return f"{condition} ? {if_block} : {else_block}"

    def variable_definition(self, tree):
        return " ".join(self.visit_children(tree))

    def operation(self, tree):
        return " ".join(self.visit_children(tree))

    def call(self, tree):
        function, *arguments = self.visit_children(tree)
        return f"{function}({', '.join(arguments)})"

setattr(GirvelInterpreter, "if", GirvelInterpreter.if_)
del GirvelInterpreter.if_


def transpile(source):
    return GirvelInterpreter().visit(parser.parse(source))
