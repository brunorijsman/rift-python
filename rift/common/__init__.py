#very, very magic code to cleanup the immutable schema to allow old code to modify rift packets

__all__ = ['ttypes', 'constants']

from . import ttypes

for _klass in dir(ttypes):
    try:
        delattr(getattr(ttypes, _klass),"__setattr__")
    except (KeyError, AttributeError):
        pass

