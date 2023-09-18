import os
from pathlib import Path

from transpiler import transpile

if __name__ == '__main__':
    Path('demo/.build').mkdir(exist_ok=True)
    Path('demo/.build/main.c').write_text(transpile(Path("demo/main.grv").read_text()))
    os.system('gcc demo/.build/main.c')
    os.system('./a.out')