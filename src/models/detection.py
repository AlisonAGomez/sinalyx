"""LEGADO: compatibilidade de import; implementação em src.models.isolation_forest."""

import sys
from src.models import isolation_forest as _implementation

sys.modules[__name__] = _implementation
