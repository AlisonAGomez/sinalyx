"""LEGADO: compatibilidade de import; implementação em src.models.heuristics."""

import sys
from src.models import heuristics as _implementation

sys.modules[__name__] = _implementation
