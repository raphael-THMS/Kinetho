from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    if "--point-annotator" in sys.argv[1:]:
        from point_annotator import run

        arguments = sys.argv[1:]
        switch_index = arguments.index("--point-annotator")
        initial_folder = None
        if switch_index + 1 < len(arguments):
            initial_folder = Path(arguments[switch_index + 1]).expanduser()
        run(initial_folder)
        return

    from studio import main as run_studio

    run_studio()


if __name__ == "__main__":
    main()