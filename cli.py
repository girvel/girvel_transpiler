from argparse import ArgumentParser
from pathlib import Path

import os
from pathlib import Path
from termcolor import colored

from lark import UnexpectedCharacters

from transpiler import transpile


parser = ArgumentParser(
    prog="girvel",
    description="Toolchain for Girvel programming language",
)
parser.set_defaults(func=lambda args: parser.print_help())

subparsers = parser.add_subparsers()



def run(args):
    path = Path("demo/main.grv")
    source = path.read_text()

    try:
        transpiled_code = transpile(source)
    except UnexpectedCharacters as ex:
        print(f"{colored('SYNTAX ERROR', 'red', attrs=['bold'])} {path}:{ex.line}:{ex.column}")
        print(ex)
        exit(1)

    Path('demo/.build').mkdir(exist_ok=True)
    Path('demo/.build/main.c').write_text(transpiled_code)
    os.system('gcc demo/.build/main.c')
    os.system('./a.out')

parser_run = subparsers.add_parser("run", help="Run main.grv in given directory")
parser_run.add_argument("directory", default=".", nargs="?", type=Path, help="directory to run")
parser_run.set_defaults(func=run)
