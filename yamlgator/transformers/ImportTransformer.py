from ..constants import *
from ..tree import *
from .KeyTransformer import *
from .YAMLTransformer import *
from .ValueTransformer import *

from . import DEBUG

class ImportTransformer(KeyTransformer):
    name = 'transform_imports'
    match_regex = rf"{re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.IMPORT}"
    extract_regex = rf"({re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.IMPORT_EXP})"

    def __init__(self, odict_or_yamlator_or_tree=None, context_tree=None, allow_tree_subs=False, root_dir=None):
        if hasattr(odict_or_yamlator_or_tree, 'root_dir') and root_dir is None:
            self.root_dir = odict_or_yamlator_or_tree.root_dir
        else:
            root_dir = pathlib.Path('.') if root_dir is None else root_dir
            self.root_dir = pathlib.Path(root_dir).absolute()

        super(ImportTransformer,self).__init__(odict_or_yamlator_or_tree, context_tree)

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

        for _k,_v in _transformed_key.items():
            node[_k] = _v
        # node[_transformed_key] = _value

        for _key in list(_node_copy.keys())[_key_index + 1:]:
            if DEBUG.KeyTransformer:
                _msg = f'moving {_key}'
                ic(_msg)
            _value = node.pop(_key)
            node[_key] = _value

    def _transform(self, parameters, keychain):
        _node_key, = parameters
        if _node_key[-1] == '/':
            _node_key = _node_key[:-1]

        _selector_value = self.get(keychain + list(parameters) + [''])
        if DEBUG.ImportTransformer:
            ic(keychain)
            ic(parameters)
            ic(_selector_value if not isinstance(_selector_value,Tree) else _selector_value.print())

        if not isinstance(_selector_value,Tree):
            _input_tree = Tree(OrderedDict({_node_key:_selector_value}))
            ValueTransformer(_input_tree,context_tree=self,allow_tree_subs=False).evaluate()

            YAMLTransformer(_input_tree,root_dir=self.root_dir).evaluate()

            _transformed_value = _input_tree.get(_node_key + '/')
            # TODO: this is broken; why cannot we pass a keychain string??
            # _transformed_value = _input_tree.get([_node_key,''])
            _path,_selector = _selector_value.split('#')
            _new_root_dir = self.root_dir.joinpath(pathlib.Path(_path).parent)
            ImportTransformer(_transformed_value,root_dir=_new_root_dir).evaluate()
        else:
            _transformed_value = _selector_value
            ImportTransformer(_transformed_value,root_dir=self.root_dir).evaluate()

        if isinstance(_transformed_value,Tree):
            if DEBUG.ImportTransformer:
                ic(_transformed_value.print())

            _transformed_value = _transformed_value.odict

        return _transformed_value

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

            _transformed_token = None
            for _token in _tokenized_key:
                _transformed_token = _token
                _match = self._extract(_token)
                if _match is not None:
                    _transformed_token = self._transform(_match.groups(), keychain)

                if _transformed_token is None:
                    _transformed_token = _token
                elif isinstance(_transformed_token, list):
                    raise Exception(f'Are you really trying to turn a list into a key?')
                if DEBUG.KeyTransformer:
                    ic(_transformed_token)


            if isinstance(_transformed_token,OrderedDict):
                self._replace_node_key(node,_node_key,_transformed_token)


class ImportTransformerUtility(ImportTransformer):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)