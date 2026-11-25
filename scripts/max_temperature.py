"""Maximum temperature anomaly map.

Shortcut for ``samet-cptec --variable tmax``; run with ``--help`` for all options.
"""

import sys

from samet_cptec.cli import main

if __name__ == "__main__":
    main(["--variable", "tmax", *sys.argv[1:]])
