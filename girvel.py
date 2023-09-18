import os
from pathlib import Path
from termcolor import colored

from lark import UnexpectedCharacters

from transpiler import transpile


if __name__ == '__main__':
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