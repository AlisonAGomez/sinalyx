"""Compatibilidade LEGADO/HISTÓRICO para scripts.historical.pipelines.validate."""

if __name__ == "__main__":
    from scripts.historical.pipelines.validate import main

    main()
else:
    import sys
    from scripts.historical.pipelines import validate as _implementacao

    sys.modules[__name__] = _implementacao
