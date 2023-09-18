from pathlib import Path

from lark import Lark, Transformer


parser = Lark(Path("girvel.lark").read_text())

class GirvelTransformer(Transformer):
    def start(self, children):
        return children[0]

    def function_definition(self, children):
        signature, block = children
        return f"{signature} {{\n    return {block};\n}}\n\n"

    def signature(self, children):
        return_type, name, arguments = children
        return f"{return_type} {name}{arguments}"

    def arguments(self, children):
        return f"({', '.join(children)})"

    def block(self, children):
        return f"({{ {''.join(children)}; }})"

    def expression(self, children):
        return children[0]

    def if_(self, children):
        condition, if_block, else_block = children
        return f"(({condition}) ? ({if_block}) : ({else_block}))"

    def variable_definition(self, children):
        return " ".join(children)

    def operation(self, children):
        return " ".join(children)

setattr(GirvelTransformer, "if", GirvelTransformer.if_)
del GirvelTransformer.if_

if __name__ == '__main__':
    print(GirvelTransformer().transform(parser.parse(Path("main.grv").read_text())))