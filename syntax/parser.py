import sys
from dataclasses import dataclass

from lark import Transformer, v_args
from lark.ast_utils import Ast, create_transformer, WithMeta
from lark.tree import Meta


@dataclass
class SemanticBase(Ast, WithMeta):
    meta: Meta

@dataclass
class IntegerLiteral(SemanticBase):
    symbol: str

@dataclass
class FloatLiteral(SemanticBase):
    symbol: str

@dataclass
class StringLiteral(SemanticBase):
    symbol: str

@dataclass
class CharacterLiteral(SemanticBase):
    symbol: str

Literal = IntegerLiteral | FloatLiteral | StringLiteral | CharacterLiteral

class _GirvelParser(Transformer):
    pass

girvel_parser = create_transformer(sys.modules[__name__], _GirvelParser())
