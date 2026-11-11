"""LEGADO: compatibilidade de import; implementação em src.services.pfsense_incremental_service."""

import sys
from src.services import pfsense_incremental_service as _implementation

sys.modules[__name__] = _implementation
