"""Compatibilidade LEGADO/HISTÓRICO para scripts.historical.pipelines.stream_processor."""

if __name__ == "__main__":
    from scripts.historical.pipelines.stream_processor import main

    main()
else:
    import sys
    from scripts.historical.pipelines import stream_processor as _implementacao

    sys.modules[__name__] = _implementacao
