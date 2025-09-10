from ..constants import *
from .KeyChainTransformer import *

from . import DEBUG


class KeyTransformerException(Exception):
    pass


class KeyTransformer(KeyChainTransformer):
    name = 'transform_keys'
    def __init__(self, odict_or_tree=None, context_tree=None, allow_tree_subs=False):
        super(KeyTransformer,self).__init__(odict_or_tree, context_tree, False)

    def _replace_node_key(self, node, node_key, _transformed_key):

        if DEBUG.KeyTransformer:
            ic(node_key)
            ic(_transformed_key)
        _node_copy = deepcopy(node)
        _key_index = list(_node_copy.keys()).index(node_key)

        for _key in list(_node_copy.keys())[:_key_index]:
            if DEBUG.KeyTransformer:
                _msg = f'moving {_key}'
                ic(_msg)
            _value = node.pop(_key)
            node[_key] = _value

        if DEBUG.KeyTransformer:
            _msg = f'replacing {node_key} with {_transformed_key}'
            ic(_msg)

        _value = node.pop(node_key)
        if DEBUG.KeyTransformer:
            ic(_value)

        node[_transformed_key] = _value

        for _key in list(_node_copy.keys())[_key_index + 1:]:
            if DEBUG.KeyTransformer:
                _msg = f'moving {_key}'
                ic(_msg)
            _value = node.pop(_key)
            node[_key] = _value

    def _pre_evaluate(self, node, keychain):
        if DEBUG.KeyTransformer:
            ic()
            ic(keychain)
            ic(node.keys())

        for _node_key in copy(list(node.keys())):
            _tmp_key = _node_key

            _tokenized_key = self._tokenize(_tmp_key)
            if DEBUG.KeyTransformer:
                ic(_tokenized_key)

            _transformed_lines = []
            _transformed_key = []

            for _token in _tokenized_key:
                _transformed_token = _token
                _match = self._extract(_token)
                if _match is not None:
                    _transformed_token = self._transform(_match.groups(), keychain)

                if _transformed_token is None:
                    _transformed_token = _token
                elif isinstance(_transformed_token, list):
                    raise KeyTransformerException(f'Are you really trying to turn a list into a key?')
                    # _transformed_token = self._yaml_list_transformer(_transformed_token)
                if DEBUG.KeyTransformer:
                    ic(_transformed_token)

                # make sure we append strings
                _transformed_key.append(str(_transformed_token))

            _transformed_key = ''.join(_transformed_key)

            if _transformed_key != _node_key:
                self._replace_node_key(node,_node_key,_transformed_key)


class KeyTransformerUtility(KeyTransformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)