"""Compatibilidade LEGADO/HISTÓRICO para scripts.historical.pipelines.prepare."""

if __name__ == "__main__":
    from scripts.historical.pipelines.prepare import main

    main()
else:
    import sys
    from scripts.historical.pipelines import prepare as _implementacao

    sys.modules[__name__] = _implementacao
