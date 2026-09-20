"""Entrada compatível por nome; consulte --help para configurar os arquivos."""

import sys

from samet_cptec.cli import main

if __name__ == "__main__":
    main(["--variable", "tmax"] + sys.argv[1:])
