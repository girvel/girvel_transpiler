from pathlib import Path
from typing import Iterator

from lark import Lark
from lark.visitors import Interpreter, v_args

from utils import capital_letters

parser = Lark((Path(__file__).parent / "girvel.lark").read_text())

def _indent(code):
    if isinstance(code, Iterator):
        code = '\n' + '\n'.join(code)

    return code.replace("\n", "\n    ")

def _generate_concat_macro(args_n):
    args_array = [capital_letters[i] for i in range(args_n)]

    return "#define _GIRVEL_CONCAT{n}({args}) {expr}\n".format(
        n=args_n, args=', '.join(args_array), expr="##_##".join(args_array),
    ) + "#define GIRVEL_CONCAT{n}({args}) _GIRVEL_CONCAT{n}({args})\n".format(
        n=args_n, args=', '.join(args_array)
    )

ignore = v_args(True)(lambda self, value: value if isinstance(value, str) else self.visit(value))

class GirvelInterpreter(Interpreter):
    start = ignore
    concats = set()
    footer = ""
    in_struct = False

    def _concat(self, elements):
        if len(elements) == 1:
            return elements[0]

        self.concats.add(len(elements))
        return "GIRVEL_CONCAT{}({})".format(len(elements), ", ".join(elements))

    def module(self, tree):
        contents = self.visit_children(tree)

        return "".join([
            "".join(map(_generate_concat_macro, self.concats)),
            "\n\n" if len(self.concats) > 0 else "",
            "".join(contents),
            self.footer,
        ])

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

        return "".join([
            "\n",
            ''.join(f"#define {typevar} {typeval}\n" for typevar, typeval in assignments),
            f"#include {target}\n",
            ''.join(f"#undef {typevar}" for typevar, _ in assignments),
            "\n",
        ])

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
    def signature(self, name, return_type, arguments):
        return f"{self.visit(return_type)} {self.visit(name)}{self.visit(arguments)}"

    def function_name(self, tree):
        return self._concat(self.visit_children(tree))

    def arguments(self, tree):
        return f"({', '.join(self.visit_children(tree))})"

    def struct_definition(self, tree):
        was_in_struct = self.in_struct
        self.in_struct = True
        name, *variable_definitions = self.visit_children(tree)
        self.in_struct = was_in_struct

        return (
            f"\ntypedef struct {{"
            + _indent(f"{d};" for d in variable_definitions) +
            f"\n}} {name};\n"
        )

    def type_name(self, tree):
        return self._concat(self.visit_children(tree))

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
        elements = self.visit_children(tree)

        if len(elements) == 2:
            return ("" if self.in_struct else "const ") + " ".join(elements)

        return " ".join(elements[1:])

    def variable_assignment(self, tree):
        return " ".join(self.visit_children(tree))

    def variable_declaration(self, tree):
        lvalue, rvalue = self.visit_children(tree)
        return f"{lvalue} = {rvalue}"

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
