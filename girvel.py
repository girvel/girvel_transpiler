from pathlib import Path

from lark import Lark


parser = Lark(Path("girvel.lark").read_text())

if __name__ == '__main__':
    print(parser.parse(Path("demo.grv").read_text()).pretty())