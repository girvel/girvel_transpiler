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


def build(args):
    build_dir = args.directory / '.build'
    build_dir.mkdir(exist_ok=True)
    os.system(f'rm -r {build_dir}/*')

    entrypoint = args.directory / "main.grv"

    sys.stderr.write(f"\t{colored('Transpiling', 'green', attrs=['bold'])} {args.directory.name}\n")

    for path in args.directory.glob('**/*.grv'):
        source = path.read_text()

        try:
            transpiled_code = transpile(source)
        except UnexpectedCharacters as ex:
            sys.stderr.write(f"\t{colored('Syntax error', 'red', attrs=['bold'])} {path}:{ex.line}:{ex.column}\n")
            sys.stderr.write(f"\n{ex}\n")
            exit(1)

        (build_dir / path.relative_to(args.directory).with_suffix('.c')).write_text(transpiled_code)

    sys.stderr.write(f"\t{colored('Running', 'green', attrs=['bold'])} {path.parent.name}\n")
    sys.stderr.write("\n")

    os.system(f'gcc -std=c11 {build_dir / "main.c"}')

parser_run = subparsers.add_parser("build", help="Build an executable file starting from main.grv in given directory")
parser_run.add_argument("directory", default=".", nargs="?", type=Path, help="directory to build")
parser_run.set_defaults(func=build)


def run(args):
    build(args)
    os.system('./a.out')

parser_run = subparsers.add_parser("run", help="Run main.grv in given directory")
parser_run.add_argument("directory", default=".", nargs="?", type=Path, help="directory to run")
parser_run.set_defaults(func=run)
