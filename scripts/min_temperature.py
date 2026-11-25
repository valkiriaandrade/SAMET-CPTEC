"""Minimum temperature anomaly map.

Shortcut for ``samet-cptec --variable tmin``; run with ``--help`` for all options.
"""

import sys

from samet_cptec.cli import main

if __name__ == "__main__":
    main(["--variable", "tmin", *sys.argv[1:]])
