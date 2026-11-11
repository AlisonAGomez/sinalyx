"""Compatibilidade LEGADO/HISTÓRICO para scripts.historical.pipelines.train."""

if __name__ == "__main__":
    from scripts.historical.pipelines.train import main

    main()
else:
    import sys
    from scripts.historical.pipelines import train as _implementacao

    sys.modules[__name__] = _implementacao
