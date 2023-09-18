import sys
from argparse import ArgumentParser

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


def run(args):  # TODO fix path
    path = Path("demo/main.grv")
    source = path.read_text()

    sys.stderr.write(f"\t{colored('Transpiling', 'green', attrs=['bold'])} {path.parent.name}\n")
    try:
        transpiled_code = transpile(source)
    except UnexpectedCharacters as ex:
        sys.stderr.write(f"\t{colored('Syntax error', 'red', attrs=['bold'])} {path}:{ex.line}:{ex.column}\n")
        sys.stderr.write(f"\n{ex}\n")
        exit(1)

    Path('demo/.build').mkdir(exist_ok=True)
    Path('demo/.build/main.c').write_text(transpiled_code)

    sys.stderr.write(f"\t{colored('Running', 'green', attrs=['bold'])} {path.parent.name}\n")
    sys.stderr.write("\n")
    os.system('gcc -std=c11 demo/.build/main.c')
    os.system('./a.out')

parser_run = subparsers.add_parser("run", help="Run main.grv in given directory")
parser_run.add_argument("directory", default=".", nargs="?", type=Path, help="directory to run")
parser_run.set_defaults(func=run)
