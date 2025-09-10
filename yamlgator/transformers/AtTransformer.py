from ..constants import *
from .ValueTransformer import *

from . import DEBUG

class AtTransformerException(Exception):
    pass


class AtTransformer(ValueTransformer):
    name = 'transform_ats'
    match_regex = \
        f"{re.escape(KEY_OR_KEYCHAIN_OP)}{re.escape(KEYCHAIN_LEFT_BOUND)}?" + \
        f"{REGEXES.AT}{re.escape(KEYCHAIN_RIGHT_BOUND)}?"
    extract_regex = \
        f"{re.escape(KEY_OR_KEYCHAIN_OP)}({re.escape(KEYCHAIN_LEFT_BOUND)}?)" + \
        f"({REGEXES.AT_EXP})({re.escape(KEYCHAIN_RIGHT_BOUND)}?)"

    def __init__(self, odict_or_tree=None, **kwargs):
        odict_or_tree = OrderedDict() if odict_or_tree is None else odict_or_tree
        super(AtTransformer, self).__init__(odict_or_tree)
        if DEBUG.AtTransformer:
            ic()

    def _match(self, line):
        _m = re.match(f"(.*?)({self.match_regex})(.*)",str(line))
        if _m:
            if DEBUG.AtTransformer:
                ic()
                ic(line)
                ic(_m.groups())
        return _m

    def _extract(self, token):
        _m = re.match(f"{self.extract_regex}",str(token))
        if _m:
            if DEBUG.AtTransformer:
                ic()
                ic(token)
                ic(_m.groups())
        return _m

    def _transform(self, parameters, keychain):
        if  DEBUG.AtTransformer:
            ic(parameters)
            ic(keychain)

        _l_brace, _special_keychain_param, _sign, _index, _r_brace = parameters

        _transformed_token = None

        if DEBUG.AtTransformer:
            ic(_l_brace)
            ic(_special_keychain_param)
            ic(_sign)
            ic(_index)
            ic(_r_brace)

        # TODO: Note that if we are making a keychain based on @
        # and there is a variable in the keychain, we need to 'reverse escape' the
        # path: key1/))key2//key3 , not key1/))key2/key3 ; we don't want ))key2/key3 to parse as a keychain !
        if any(map(is_variable_token,keychain)):
            _old_keychain = copy(keychain)
            keychain = []
            for _key in _old_keychain:
                if is_variable_token(_key):
                    keychain.append(_key + '/')
                else:
                    keychain.append(_key)

        if _index:
            _index = int(_index)
            if _sign:
                _transformed_token = '/'.join(keychain[:-_index])
            else:
                _transformed_token = '/'.join(keychain[:_index])
        else:
            _transformed_token = '/'.join(keychain)

        if _l_brace == '' and _r_brace == '':
            _transformed_token = _transformed_token.split('/')[-1]

        if DEBUG.AtTransformer:
            ic(_transformed_token)

        return _transformed_token

class AtTransformerUtility(AtTransformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
