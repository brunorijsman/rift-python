__all__ = ['ttypes', 'constants']

from . import ttypes

for _klass in dir(ttypes):
    try:
        delattr(getattr(ttypes, _klass),"__setattr__")
    except (KeyError, AttributeError):
        pass
