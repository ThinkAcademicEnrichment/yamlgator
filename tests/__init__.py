from yamlgator.tree import *
from yamlgator.transformers import *
from yamlgator.YAMLator import *
from yamlgator.evaluators.StateEvaluator import *
from yamlgator.evaluators.Observables import *
from yamlgator.evaluators.States import *

from collections import OrderedDict
from copy import deepcopy
from importlib import import_module

import sys
import pdb
import random
import pathlib
import tempfile
import unittest
import functools
import traceback

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
