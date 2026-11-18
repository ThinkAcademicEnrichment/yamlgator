from yamlgator.transformers import KeyTransformer
from yamlgator.transformers import ValueTransformer
from ..constants import *
from ..tree import *
from .ValueTransformer import *
from .KeyTransformer import *


from . import DEBUG

# dict concat
from functools import reduce
import operator

class ForTransformerException(Exception):
    pass


# TODO: using self.context needs tests
class ForKeyTransformer(KeyTransformer):
    name = 'transform_fors'
    match_regex = rf"{re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.FOR_KEY}"
    extract_regex = rf'{re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.FOR_KEY_EXP}'

    def __init__(self, odict_or_tree=None, context_tree=None, **kwargs):
        odict_or_tree = OrderedDict() if odict_or_tree is None else odict_or_tree
        super().__init__(odict_or_tree)
        self.context = context_tree
        if DEBUG.ForTransformer:
            ic()
            ic(odict_or_tree)
            ic(context_tree)

    def _match(self, line):
        _m = re.match(rf"^(.*?)({self.match_regex})(.*?)$", str(line))
        if _m:
            if DEBUG.ForTransformer:
                ic()
                ic(str(line))
                ic(_m.groups())
        return _m

    def _extract(self, token):
        _m = re.match(self.extract_regex,str(token))
        if DEBUG.ForTransformer:
            if _m:
                ic()
                ic(token)
                ic(_m.groups())
        return _m

    def _transform(self,parameters,keychain):
        if DEBUG.ForTransformer:
            ic()
            ic(parameters)
            ic(keychain)
        _exp,_trailing_slash = parameters 
        _loop_var,_list_var = tuple(map(lambda x:x.strip(),_exp.split('in')))
        _loop_vals = self.get([_list_var,''])
        if not isinstance(_loop_vals,list): _loop_vals = [] 
        return _loop_var,_loop_vals,_trailing_slash

    def _pre_evaluate(self, node, keychain):
        if DEBUG.ForTransformer:
            ic()
            ic(node)
            ic(keychain)

        if self._do_not_evaluate(node, keychain):
            return

        for _node_key in copy(list(node.keys())):
            _tmp_key = _node_key

            _tokenized_key = self._tokenize(_tmp_key)
            if DEBUG.ForTransformer:
                ic(_tokenized_key)

            _transformed_lines = []
            _transformed_key = []

            for _token in _tokenized_key:
                _transformed_token = _token
                _match = self._extract(_token)
                if _match is not None:
                    _loop_var, _loop_values,_trailing_slash = self._transform(_match.groups(), keychain)
                else:
                    continue
                if _loop_values:
                    self._unroll_node_key(node,_node_key,_loop_var,_loop_values,_trailing_slash)

    def _unroll_node_key(self, node, node_key, _loop_var, _loop_vals,_trailing_slash):

        if DEBUG.ForTransformer:
            ic()
            ic(node)
            ic(node_key)
            ic(_loop_var)
            ic(_loop_vals)
            ic(_trailing_slash)

        _node_copy = deepcopy(node)
        _key_index = list(_node_copy.keys()).index(node_key)

        for _key in list(_node_copy.keys())[:_key_index]:
            if DEBUG.ForTransformer:
                _msg = f'rotating {_key}'
                ic(_msg)
            _value = node.pop(_key)
            node[_key] = _value

        _for_body_tree = Tree(node.pop(node_key))
        
        if DEBUG.ForTransformer:
            _msg = 'Popping loop body'
            ic(_msg)
            ic(_for_body_tree.print())

        _unrolls = []
        for _loop_val in _loop_vals:
            _unrolls.append(_for_body_tree.copy())

            ValueTransformer(
                _unrolls[-1],
                context_tree=Tree(
                    OrderedDict({
                        _loop_var:_loop_val
                    }
                    ))).evaluate()

            KeyTransformer(
                _unrolls[-1],
                context_tree=Tree(
                    OrderedDict({
                        _loop_var:_loop_val
                    }
                    ))).evaluate()

            
            if DEBUG.ForTransformer:
                _msg = f'unrolling {node_key} with {_loop_val}'
                ic(_msg)
                ic(_unrolls[-1].print())
                ic(node)
            

        if not _trailing_slash:
            _roll = reduce(operator.or_,[_unroll.odict for _unroll in _unrolls])
            for _key,_val in _roll.items():
                node[_key] = _val
        else:
            if isinstance(list(_unrolls[0].odict.values())[0],list):
                # list aggregation
                [_unrolls[0].aget(*list(_unroll.odict.items())[0]) for _unroll in _unrolls[1:]]
                for _key,_val in _unrolls[0].odict.items():
                    node[_key] = _val
            elif isinstance(list(_unrolls[0].odict.values())[0],str):
                # str concatenation
                _aggregate_str = reduce(operator.concat,[list(_unroll.odict.values())[0] for _unroll in _unrolls])
                _key = list(_unrolls[0].odict.keys())[0]
                node[_key] = _aggregate_str

        for _key in list(_node_copy.keys())[_key_index + 1:]:
            if DEBUG.ForTransformer:
                _msg = f'rotating {_key}'
                ic(_msg)
            _value = node.pop(_key)
            node[_key] = _value

class ForTransformerUtility(ForKeyTransformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
