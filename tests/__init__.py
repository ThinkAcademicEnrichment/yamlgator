from yamlgator.tree import Tree,TreeException
from yamlgator.transformers import *
from yamlgator.YAMLator import YAMLator,DEFAULT_UTILITIES
# from yamlgator.transformers.ValueTransformer import ValueTransformerUtility

from collections import OrderedDict
from copy import deepcopy
import pathlib
import sys
import pdb
import functools
import traceback
import pathlib
import unittest
import tempfile
from importlib import import_module

try:
    from icecream import ic
    ic.configureOutput(includeContext=False)
except ImportError:  # Graceful fallback if IceCream isn't installed.
    ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa


TESTS_DIR = pathlib.Path(__file__).absolute().parent


def debug_on(*exceptions):
    if not exceptions:
        exceptions = (AssertionError, )
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except exceptions:
                info = sys.exc_info()
                traceback.print_exception(*info)
                pdb.post_mortem(info[2])
        return wrapper
    return decorator

# from tests.tree import TestTree
# from tests.transformers import TestTransformer

if __name__ == '__main__':
    _tl = unittest.TestLoader()
    _tl.discover('.')
    unittest.main()
