"""LEGADO: use src.pipelines.process_pfsense_incremental; CLI antiga preservada."""

import sys
from src.pipelines import process_pfsense_incremental as _implementation

if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
