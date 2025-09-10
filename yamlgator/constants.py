import io
import re
import ast
import yarl
import yaml
import astor
import pathlib
import typing

from copy import copy,deepcopy
from collections import OrderedDict
from functools import partial,reduce
from dataclasses import dataclass
from enum import Enum


try:
    from icecream import ic
    ic.configureOutput(includeContext=True)
except ImportError:  # Graceful fallback if IceCream isn't installed.
    ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa

KEYCHAIN_SEP = r'/'
KEY_OR_KEYCHAIN_OP = r'))'
KEYCHAIN_LEFT_BOUND = r'{'
KEYCHAIN_RIGHT_BOUND = r'}'

TRUE_VALUES = \
    ("y","Y","yes","Yes","YES",)\
    + ("true","True","TRUE",)\
    + ("on","On","ON",)

FALSE_VALUES = \
    ("n","N","no","No","NO",)\
    + ("false","False","FALSE",)\
    + ("off","Off","OFF")


class REGEXES:
    BOOL_VALUE = r'|'.join(TRUE_VALUES) + r'|' + r'|'.join(FALSE_VALUES)

    KEY = r'[a-zA-Z0-9_][a-zA-Z0-9_\.-]*'
    KEYCHAIN = rf'/?(?:{KEY}/)*'

    BOOL_TYPE_KEY = rf'(?:use|is)-{KEY}'
    PATH_TYPE_KEY = rf'{KEY}-(?:path|dir)$'
    URL_TYPE_KEY = rf'{KEY}-url$'

    LIST_INDEX = r'\d+'
    SLICE = r'\:?\-?\d+\:?'
    DATA_INDEX = rf'{KEYCHAIN}{KEY}/?|{SLICE}'
    POSIX_RELATIVE = r'\./(?:[^\0/]+/?)*[^#]'
    POSIX_ABSOLUTE = r'/(?:[^\0/]+/?)*[^#]'

    AT = r'@(?:\[\-?\d+\])?'
    AT_EXP = r'@(?:\[(\-?)(\d+)\])?'

    # FRAGILE! Does not allow multiple bang expressions on one line
    BANG = r'(?:\!.*\))'
    BANG_EXP =r'\!([^)]*?\)$)'

    IMPORT = r'(?:\+.*\)(?:\s|$))'
    IMPORT_EXP = r'\+.*(?:\s|$)'
    # -----------------------------------

    IF = rf'\?{re.escape(KEYCHAIN_LEFT_BOUND)}[^}}]+{re.escape(KEYCHAIN_RIGHT_BOUND)}'

    OR_SEP = r'|'
    AND_SEP = r'&'
    CASE_SEP = r':'

    LOGICAL_KEY_EXP = \
        rf'[{OR_SEP}{AND_SEP}]?\s*!?\s*[^=!{AND_SEP}{OR_SEP}]+\s*(?:[!=]=\s*!?\s*[^=!{AND_SEP}{OR_SEP}]+)?'

    IF_KEY_EXP = \
        rf'\?{re.escape(KEYCHAIN_LEFT_BOUND)}((?:\s*{LOGICAL_KEY_EXP}|\s*[{OR_SEP}{AND_SEP}]?\s*!?\s*{BOOL_TYPE_KEY})+)\s*{re.escape(KEYCHAIN_RIGHT_BOUND)}(/?)'

    LOGICAL_EXP = \
        rf'[{OR_SEP}{AND_SEP}]?\s*!?\s*[^=!{AND_SEP}{OR_SEP}{CASE_SEP}]+(?:\[{DATA_INDEX}\])?\s*(?:[!=]=\s*!?\s*[^=!{AND_SEP}{OR_SEP}{CASE_SEP}]+)?'

    IF_EXP = \
        rf'\?{re.escape(KEYCHAIN_LEFT_BOUND)}((?:\s*{LOGICAL_EXP}|\s*[{OR_SEP}{AND_SEP}]?\s*!?\s*{BOOL_TYPE_KEY})+)\s*{CASE_SEP}' + \
        rf'([^{AND_SEP}{OR_SEP}{CASE_SEP}]+)\s*(?:{CASE_SEP}([^{AND_SEP}{OR_SEP}{CASE_SEP}]+))?\s*{re.escape(KEYCHAIN_RIGHT_BOUND)}'


def bool_factory(x):
    if not re.match(REGEXES.BOOL_VALUE, x):
        raise f"{x} is not a recognized boolean string"
    if x in TRUE_VALUES:
        x = True
    elif x in FALSE_VALUES:
        x = False
    return x


DEFAULT_KEY_TYPES = dict(
    path = (REGEXES.PATH_TYPE_KEY, (pathlib.Path,)),
    url = (REGEXES.URL_TYPE_KEY,(yarl.URL,)),
    bool = (REGEXES.BOOL_TYPE_KEY,(bool_factory,))
)


def is_variable_token(token):
    if str(token)[:len(KEY_OR_KEYCHAIN_OP)] == KEY_OR_KEYCHAIN_OP:
        return True
    return False
