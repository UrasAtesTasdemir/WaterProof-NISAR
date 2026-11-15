"""Merged EN / TR string tables. Each module defines EN and TR with the same keys."""
from importlib import import_module

MODULES = ('common', 'workflow', 'compass', 'evidence', 'visibility', 'pages', 'case_views', 'dashboard', 'explore', 'start', 'demo', 'placebo', 'flood', 'release')
EN, TR, COLUMNS_TR, MAP_PAIRS_TR = {}, {}, {}, []
for _name in MODULES:
    _module = import_module(f'src.locales.{_name}')
    for _target, _source in ((EN, _module.EN), (TR, _module.TR)):
        _duplicate = set(_target) & set(_source)
        if _duplicate:
            raise ValueError(f'Duplicate translation keys in {_name}: {sorted(_duplicate)[:5]}')
        _target.update(_source)
    COLUMNS_TR.update(getattr(_module, 'COLUMNS_TR', {}))
    MAP_PAIRS_TR.extend(getattr(_module, 'MAP_PAIRS_TR', []))
