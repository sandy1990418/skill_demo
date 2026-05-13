"""
Call setup() at the top of any skill script that needs to import from another skill.

Usage:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from skills._path import setup; setup(__file__)

    # Now you can import from any skill's scripts:
    from skills.pptx.scripts.office import pack
"""

import sys
from pathlib import Path


def setup(caller_file: str) -> Path:
    """Add the project root to sys.path so cross-skill imports work."""
    root = Path(caller_file).resolve().parents[3]  # skills/<skill>/scripts/<file>
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root
