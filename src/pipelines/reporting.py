"""Compatibilidade LEGADO/HISTÓRICO para scripts.historical.pipelines.reporting."""

if __name__ != "__main__":
    import sys
    from scripts.historical.pipelines import reporting as _implementacao

    sys.modules[__name__] = _implementacao
