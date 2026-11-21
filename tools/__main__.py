import sys
from pathlib import Path

from tools.cli import main

# Always work on the project folder, wherever the command is run from.
raise SystemExit(main(sys.argv[1:], root=Path(__file__).resolve().parent.parent))
