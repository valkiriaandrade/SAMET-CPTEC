"""Minimum temperature anomaly map for southern Brazil.

Shortcut for ``samet-cptec --variable tmin --region south``; run with ``--help`` for all options.
"""

import sys

from samet_cptec.cli import main

if __name__ == "__main__":
    main(["--variable", "tmin", "--region", "south", *sys.argv[1:]])
