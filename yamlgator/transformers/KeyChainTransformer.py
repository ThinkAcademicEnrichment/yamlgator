from ..constants import *
from ..tree import *
from .Transformer import *

from . import DEBUG

class KeyChainTransformer(Transformer):
    match_regex = \
        f"{re.escape(KEY_OR_KEYCHAIN_OP)}{re.escape(KEYCHAIN_LEFT_BOUND)}?" + \
        f"{REGEXES.KEYCHAIN}{REGEXES.KEY}/?{re.escape(KEYCHAIN_RIGHT_BOUND)}?" + \
        f"(?:{re.escape('[')}[^]]*{re.escape(']')})?"

    extract_regex = \
        f"{re.escape(KEY_OR_KEYCHAIN_OP)}{re.escape(KEYCHAIN_LEFT_BOUND)}?" + \
        f"({REGEXES.KEYCHAIN}{REGEXES.KEY}/?){re.escape(KEYCHAIN_RIGHT_BOUND)}?" + \
        f"(?:{re.escape('[')}({REGEXES.DATA_INDEX}){re.escape(']')})?"

    def __init__(self, odict_or_tree=None, context_tree=None, allow_tree_subs=True):
        # super(KeyChainTransformer,self).__init__(odict_or_tree)
        super().__init__(odict_or_tree)
        self.context = context_tree
        self.allow_tree_subs = allow_tree_subs

    def _match(self, line):
        _m = re.match(rf"^(.*?)({self.match_regex})(.*)$", str(line))

        if _m:
            if DEBUG.KeyChainTransformer:
                ic(str(line))
                ic(_m.groups())
        return _m

    def _extract(self, token):
        _m = re.match(self.extract_regex,str(token))
        if _m:
            if DEBUG.KeyChainTransformer:
                ic(token)
                ic(_m.groups())

        return _m

    def _transform(self, parameters, keychain):
        if DEBUG.KeyChainTransformer:
            ic(parameters)

        _keychain_param, _data_index = parameters

        _local_context = self if not self.context else self.context

        _slice = None
        _local_context_keychain = None

        if _data_index:
            # slices take precedence so try to match first!
            _m = re.match(REGEXES.SLICE, _data_index)
            if _m:
                # we found a slice
                _slice = _data_index
                if DEBUG.KeyChainTransformer:
                    ic(_slice)

            else:
                # we found a local context
                _local_context_keychain = _data_index
                try:
                    if self.context:
                        _local_context = self.context.get(_local_context_keychain)
                    else:
                        _local_context = self.get(_local_context_keychain)

                    assert isinstance(_local_context,Tree)

                    if DEBUG.KeyChainTransformer:
                        ic(_local_context.print())
                except KeyError:
                    if DEBUG.KeyChainTransformer:
                        _msg = f'cannot find local context key {_local_context_keychain} in global context'
                        ic(_msg)
                    return None

            _substitution_value = None

        try:
            _substitution_value = _local_context.get(_keychain_param)
            # _substitution_value = _local_context.get(_local_context_keychain)
        except KeyError:
            if DEBUG.KeyChainTransformer:
                _msg = f'cannot find key {_keychain_param}'
                ic(_msg)
            return None

        if DEBUG.KeyChainTransformer:
            ic(_substitution_value)

        if isinstance(_substitution_value, OrderedDict):
            _substitution_value = str(Tree(_substitution_value))
            if DEBUG.KeyChainTransformer:
                _msg = 'found an ordereddict substitution'
                ic(_msg)

        # elif isinstance(_substitution_value, list):

        elif isinstance(_substitution_value, Tree):
            if DEBUG.KeyChainTransformer:
                _msg = 'found a tree substitution'
                ic(_msg)
            if not self.allow_tree_subs:
                _substitution_value = None

        if _slice is not None:
            if DEBUG.KeyChainTransformer:
                _msg = f'found a slice '
                ic(_msg)
            _substitution_value = eval(f"_substitution_value[{_slice}]")

        if DEBUG.KeyChainTransformer:
            ic(_substitution_value)

        return _substitution_value
