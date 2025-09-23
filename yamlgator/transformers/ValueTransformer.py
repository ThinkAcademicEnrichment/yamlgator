import ast

from ..constants import *
from ..tree import *
from .KeyChainTransformer import *

from . import DEBUG

class _DEBUG:
    IGNORE_IFKEYS = False

if DEBUG.ValueTransformer:
    _DEBUG.IGNORE_IFKEYS = True

class ValueTransformerException(Exception):
    pass

class ValueTransformer(KeyChainTransformer):
    name = 'transform_values'
    def _do_not_evaluate(self, value, keychain):
        if keychain and keychain[-1].startswith('_'):
            if DEBUG.ValueTransformer:
                _msg = f'NOT EVALUATING {keychain}'
                ic(_msg)
            return True
        elif keychain and any(list(map(lambda key:key.startswith('))?'),keychain))):
            if _DEBUG.IGNORE_IFKEYS:
                _msg = f'NOT EVALUATING {keychain}'
                ic(_msg)
            return True
        return False

    def _value_evaluate(self, value, keychain):
        '''generically transform in-place a multiline value using self._transform()'''
        # if DEBUG.ValueTransformer:
        #     ic()
            # ic(keychain)

        if self._do_not_evaluate(value, keychain):
            return

        if not isinstance(value, list):
            _tmp_values = [str(value)]
        else:
            _tmp_values = list(map(str, value))

        # if DEBUG.ValueTransformer:
        #     ic(_tmp_values)

        # the list of transformed values
        _transformed_values = []

        _transformed_lines = []
        # are the results of _transform() Tree values?
        _are_tree_values = False
        _are_list_values = False

        for _i, _tmp_value in enumerate(_tmp_values):
            _tokenized_lines = list(map(lambda x: self._tokenize(x), _tmp_value.split('\n')))

            # if DEBUG.ValueTransformer:
            #     ic(_tmp_value)
            #     ic(_tokenized_lines)

            _transformed_lines = []
            for _tokenized_line in _tokenized_lines:
                _transformed_line = []
                for _token in _tokenized_line:

                    # if DEBUG.ValueTransformer:
                    #     ic(_token)

                    _transformed_token = _token
                    # ------------------------------
                    _extract = self._extract(_token)
                    # ------------------------------
                    if DEBUG.ValueTransformer:
                        ic(_extract.groups()) if _extract else None
                    # MUST reset this!
                    _are_tree_values = False
                    _are_list_values = False
                    if _extract is not None:
                        _transformed_token = self._transform(_extract.groups(), keychain)

                        if DEBUG.ValueTransformer:
                            ic(_transformed_token)

                    if _transformed_token is None:
                        _transformed_token = _token
                    elif isinstance(_transformed_token, Tree):
                        # we need to recreate Tree objects from str reps when we self.get() below on transformed values
                        # this works but is awkward
                        _are_tree_values = True
                    elif isinstance(_transformed_token, list):
                        _are_list_values = True
                        # _transformed_token = ' '.join(map(str, _transformed_token))
                    elif isinstance(_transformed_token, str) and re.match(
                            # TODO: this needs refinement
                            # DO NOT SUB IN ANY UNRESOLVED SELECTORS
                            # unevaluated yaml path selector strings NEVER get subbed as values
                            # f"(.*?)({PathValueTransformer.posix_abolute_regex}|{PathValueTransformer.posix_relative_regex}#.*)(.*)",
                            # f".*?({REGEXES.POSIX_RELATIVE}|{REGEXES.POSIX_ABSOLUTE})#.*",
                            rf"^[^#](.*?#.*)",
                            _transformed_token):
                        if DEBUG.ValueTransformer:
                            _msg = 'throwing away transformed token'
                            ic(_msg)
                            ic(_transformed_token)
                        _transformed_token = _token
                    # make sure we append strings
                    _transformed_line.append(str(_transformed_token))
                _transformed_lines.append(''.join(_transformed_line))
            for _line in _transformed_lines:
                _transformed_values.append(_line)

        # if DEBUG.ValueTransformer:
        #     ic(_transformed_values)

        if _are_tree_values:
            # now insert Tree objects and return
            if DEBUG.ValueTransformer:
                ic(_are_tree_values)
                ic(_transformed_values)

            try:
                # note how this handles lists of trees elegantly
                # TODO: but it overwrites existing trees and does not overlay them!
                _t = Tree()
                _trees = list(map(lambda x: _t.load(io.StringIO(x)), _transformed_values))
                if DEBUG.ValueTransformer:
                    ic(_trees)
                    ic(keychain)
                # list(map(lambda x: self.get([''] + keychain, x), _trees))
                list(map(lambda x: self.overlay(x,[''] + keychain), _trees))
                return
            except TreeCreationException as e:
                if DEBUG.ValueTransformer:
                    _msg = 'failed to _transform() tree'
                    ic(_msg)
                return
            except Exception as e:
                if DEBUG.ValueTransformer:
                    ic(e)
        elif _are_list_values:
            _lists = list(map(ast.literal_eval,_transformed_values))
            if len(_lists) > 1:
                raise ValueTransformerException("Nested lists cannot be substituted")
            value = _lists[0]
        else:
            if isinstance(value, list):
                value = _transformed_values
            else:
                value = '\n'.join(_transformed_values)

        self.get([''] + keychain, value)
