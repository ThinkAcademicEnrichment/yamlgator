from ..constants import *
from ..tree import *
from .ValueTransformer import *

from . import DEBUG

class IfTransformerException(Exception):
    pass


# TODO: using self.context needs tests
class IfTransformer(ValueTransformer):
    name = 'transform_ifs'
    match_regex = rf"{re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.IF}"
    extract_regex = rf'{re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.IF_EXP}'

    def __init__(self, odict_or_tree=None, context_tree=None, **kwargs):
        odict_or_tree = OrderedDict() if odict_or_tree is None else odict_or_tree
        # super(IfTransformer, self).__init__(odict_or_tree)
        super().__init__(odict_or_tree)
        self.context = context_tree

    def reduce_logical_exp(self, logical_sub_exps):
        _reduced_logical_exps = []
        for _logical_sub_exp in logical_sub_exps:
            _logical_connective = None
            _not_if = False
            if _logical_sub_exp.strip()[0] == REGEXES.OR_SEP:
                _logical_connective = REGEXES.OR_SEP
                _logical_sub_exp = _logical_sub_exp.strip()[1:]
            elif _logical_sub_exp.strip()[0] == REGEXES.AND_SEP:
                _logical_connective = REGEXES.AND_SEP
                _logical_sub_exp = _logical_sub_exp.strip()[1:]
            else:
                _logical_sub_exp = _logical_sub_exp.strip()
            _logical_terms = _logical_sub_exp.split('=')
            if len(_logical_terms) == 2:
                assert _logical_terms[0][-1] == '!'
                _not_if = True
                _left_key = _logical_terms[0][:-1].strip()
                _right_key = _logical_terms[1].strip()
            elif len(_logical_terms) == 3:
                assert _logical_terms[1] == ''
                _left_key = _logical_terms[0].strip()
                _right_key = _logical_terms[2].strip()
            else:
                # I think we have a boolean-key
                if DEBUG.IfTransformer:
                    _msg = f'testing {_logical_sub_exp} as a boolean-key'
                    ic(_msg)

                _negate_test = False
                if '!' in _logical_sub_exp:
                    _logical_sub_exp = _logical_sub_exp[_logical_sub_exp.index('!') + 1:].strip()
                    _negate_test = True
                if DEBUG.IfTransformer:
                    ic(_negate_test)
                # a key does not exist yet
                try:
                    if self.context is not None:
                        _test_result = self.context.get(_logical_sub_exp.strip())
                    else:
                        _test_result = self.get(_logical_sub_exp.strip())

                except KeyError:
                    if DEBUG.IfTransformer:
                        _msg = f'get({_logical_sub_exp.strip()} not found!)'
                    return None
                if DEBUG.IfTransformer:
                    ic(_test_result)

                if isinstance(_test_result, str):
                    if not re.match(REGEXES.BOOL_VALUE, _test_result):
                        raise IfTransformerException(f"{_test_result} is not a recognized boolean string")
                    if _test_result in TRUE_VALUES:
                        _test_result = True if not _negate_test else False
                    elif _test_result in FALSE_VALUES:
                        _test_result = False if not _negate_test else True
                # elif isinstance(_test_result, Tree):
                #     # TODO: this definition of True needs to be formalized for other transformers, like IfKey
                #     if any(map(lambda x: x.startswith('))?'), _test_result.keys())):
                #         return None
                #     else:
                #         # a boolean key with a tree value (that is not an if key node) is True (?)
                #         _test_result = True if not _negate_test else False
                elif not isinstance(_test_result, bool):
                    return None

                _reduced_logical_exps.append((_test_result,_logical_connective))
                continue

            _slice = None
            _local_context_keychain = None
            _m = re.match(rf"^({REGEXES.KEYCHAIN}{REGEXES.KEY})\[({REGEXES.DATA_INDEX})\]$",_left_key)
            if _m:
                _left_key,_data_index = _m.groups()
                if re.match(REGEXES.SLICE,_data_index):
                    _slice = _data_index
                else:
                    _local_context_keychain = _data_index

            if DEBUG.IfTransformer:
                ic(_logical_terms)
                ic(_left_key)
                ic(_slice)
                ic(_local_context_keychain)
                ic(_right_key)
                ic(_not_if)
                ic(_logical_connective)

            _if = not _not_if
            if _left_key[0] == _left_key[-1] == "'":
                # strip the quotes on strings
                _left_value = _left_key[1:-1]
            else:
                # it's a key (unless it doesn't exist; error is caught by _transform())
                if self.context is not None:
                    _left_value = self.context.get(_left_key)
                else:
                    _left_value = self.get(_left_key)
            if _slice:
                assert isinstance(_left_value,str) or isinstance(_left_value,list)
                _left_value = eval(f'_left_value[{_slice}]')
            elif _local_context_keychain:
                assert isinstance(_left_value,Tree)
                _left_value = _left_value.get(_local_context_keychain)

            if _right_key[0] == _right_key[-1] == "'":
                _right_value = _right_key[1:-1]
            else:
                # it's a key (unless it doesn't exist; error is caught by _transform())
                if self.context is not None:
                    _right_value = self.context.get(_right_key)
                else:
                    _right_value = self.get(_right_key)

            if DEBUG.IfTransformer:
                ic(_left_value)
                ic(_right_value)

            if type(_left_value) != type(_right_value):
                if DEBUG.IfTransformer:
                    _msg = 'Cannot compare values'
                    ic(_msg)
                return None

            _reduced_logical_exps.append((
                _left_value == _right_value if _if else _left_value != _right_value,_logical_connective))

        if DEBUG.IfTransformer:
            ic(_reduced_logical_exps)

        assert _reduced_logical_exps[0][-1] is None
        # the rest should have a connective
        assert all([_rle[-1] is not None for _rle in _reduced_logical_exps[1:]])

        _current_logical_state = None
        for _reduced_logical_exp in _reduced_logical_exps:
            _equality_truth, _logical_connnective = _reduced_logical_exp
            if _current_logical_state is None:
                _current_logical_state = _equality_truth
            elif _logical_connnective == REGEXES.OR_SEP:
                _current_logical_state = _current_logical_state or _equality_truth
            elif _logical_connnective == REGEXES.AND_SEP:
                _current_logical_state = _current_logical_state and _equality_truth
            else:
                raise IfTransformerException(f'unknown logical connective: {_logical_connnective}')

            if DEBUG.IfTransformer:
                ic(_current_logical_state)

        return _current_logical_state

    def _transform(self, parameters, keychain):
        _logical_exp,_key_if_true,_key_if_false = parameters
        _logical_exp = _logical_exp.strip()
        _key_if_true = _key_if_true.strip()
        _key_if_false = _key_if_false.strip() if _key_if_false is not None else _key_if_false
        _logical_sub_exps = re.findall(REGEXES.LOGICAL_EXP,_logical_exp)
        if DEBUG.IfTransformer:
            ic()
            ic(_logical_exp)
            ic(_key_if_true)
            ic(_key_if_false)
            ic(_logical_sub_exps)
        # TODO: review this error handling
        try:
            _test_result = self.reduce_logical_exp(_logical_sub_exps)
        except KeyError:
            if DEBUG.IfTransformer:
                _msg = f'self.reduce_logical_exp({_logical_sub_exps}) raised KeyError'
                ic(_msg)
            # we're missing a key in the tree
            return None

        if DEBUG.IfTransformer:
            ic(_test_result)

        if _test_result is None:
            return None

        if _test_result is True:
            if DEBUG.IfTransformer:
                ic(_key_if_true)
            try:
                _return_value = self.get(_key_if_true)
            except KeyError:
                if _key_if_true[0] == _key_if_true[-1] == "'":
                    _return_value = _key_if_true[1:-1]
                else:
                    _return_value =  _key_if_true
        else:
            if DEBUG.IfTransformer:
                ic(_key_if_false)
            try:
                _return_value = self.get(_key_if_false) if _key_if_false is not None else ''
            except KeyError:
                if _key_if_false[0] == _key_if_false[-1] == "'":
                    _return_value =  _key_if_false[1:-1]
                else:
                    _return_value =  _key_if_false

        if DEBUG.IfTransformer:
            ic(_return_value)

        return _return_value


class IfTransformerUtility(IfTransformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evaluate()

class IfKeyTransformer(IfTransformer):
    name = 'transform_if_keys'
    extract_regex = rf'{re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.IF_KEY_EXP}'

    def __init__(self, odict_or_tree=None, context_tree=None, **kwargs):
        # super(IfKeyTransformer,self).__init__(odict_or_tree)
        super().__init__(odict_or_tree)
        self.context = context_tree
        # if DEBUG.IfKeyTransformer:
        #     ic()

    def _replace_node_key(self, node, node_key, new_node_key, new_key_value):

        if DEBUG.IfKeyTransformer:
            ic(node_key)
            ic(new_node_key)
            ic(new_key_value)

        # short circuit; is this still necessary?
        # Yes, for replacing an if-key with a str value !!!
        #  NO! you would need to set node = new_key_value, which does not work
        # if new_node_key is None and not isinstance(new_key_value,OrderedDict):
        #     node[node_key] = new_key_value
        #     return new_key_value

        _node_copy = deepcopy(node)
        _key_index = list(_node_copy.keys()).index(node_key)

        for _key in list(_node_copy.keys())[:_key_index]:
            if DEBUG.IfKeyTransformer:
                _msg = f'moving {_key}'
                ic(_msg)
            _value = node.pop(_key)
            node[_key] = _value

        if DEBUG.IfKeyTransformer:
            _msg = f'replacing {node_key} with {new_key_value}'
            ic(_msg)

        _ = node.pop(node_key)
        if not isinstance(new_key_value,OrderedDict):
            node[new_node_key] = new_key_value
        else:
            for _key in new_key_value.keys():
                node[_key] = new_key_value.get(_key)

        for _key in list(_node_copy.keys())[_key_index + 1:]:
            if DEBUG.IfKeyTransformer:
                _msg = f'moving {_key}'
                ic(_msg)
            _value = node.pop(_key)
            node[_key] = _value

    def _value_evaluate(self, value, keychain):
        pass

    def _pre_evaluate(self,node,keychain):

        if any(map(lambda x: x.startswith('))?'), node.keys())):
            if DEBUG.IfKeyTransformer:
                ic()
                ic(self.__class__)
                ic(keychain)
                ic(node.keys())
        else:
            return None

        # TODO: forward slashes and string string values are problematic
        for _node_key in copy(list(node.keys())):
            if not _node_key.startswith('))?'):
                continue

            if DEBUG.IfKeyTransformer:
                ic(_node_key)

            _transformed_lines = []
            _transformed_key = []
            _if = True

            _token = _node_key

            _transformed_token = _token
            _parameters = self._extract(_token)

            _logical_exp,_forward_slash = _parameters.groups()
            _logical_sub_exps = re.findall(REGEXES.LOGICAL_KEY_EXP, _logical_exp)

            _node_copy = deepcopy(node)
            _key_index = list(_node_copy.keys()).index(_node_key)
            _branches = node.get(_node_key)
            if isinstance(_branches,OrderedDict):
                assert len(list(_branches.keys())) < 3
                if not _forward_slash:
                    _true_branch = OrderedDict({list(_branches.keys())[0]: list(_branches.values())[0]})
                else:
                    _true_branch = list(_branches.values())[0]
                if len(list(_branches.keys())) == 2:
                    if not _forward_slash:
                        _false_branch = OrderedDict({list(_branches.keys())[1]:list(_branches.values())[1]})
                    else:
                        _false_branch = list(_branches.values())[1]
                else:
                    _false_branch = None
            else:
                _true_branch = _branches
                _false_branch = None

            if DEBUG.IfKeyTransformer:
                ic(_branches)
                ic(_key_index)
                ic(_forward_slash)
                ic(_true_branch)
                ic(_false_branch)
                ic(_logical_exp)
                ic(_logical_sub_exps)
                # if self.context:
                #     ic(self.context.print())
                # else:
                #     ic(self.context)

            # TODO: review this error handling
            try:
                _test_result = self.reduce_logical_exp(_logical_sub_exps)
            except Exception as e:
                if DEBUG.IfKeyTransformer:
                    _msg = f'{_logical_sub_exps} failed. Returning None'
                    ic(_msg)
                    ic(e)
                return None

            if DEBUG.IfKeyTransformer:
                ic(_test_result)

            if _test_result is None:
                return None

            if _test_result:

                if DEBUG.IfKeyTransformer:
                    _msg = f'{_logical_exp} is TRUE'
                    ic(_msg)

                # are we key order preserving here? NO! fix it...
                if _if:
                    if not _forward_slash:
                        self._replace_node_key(node,_node_key,list(_branches.keys())[0],_true_branch)
                    else:
                        self._replace_node_key(node, _node_key, None, _true_branch)

                elif not _if:
                    if _false_branch:
                        if not _forward_slash:
                            self._replace_node_key(node, _node_key,list(_branches.keys())[1], _false_branch)
                        else:
                            self._replace_node_key(node, _node_key, None, _false_branch)

                    else:
                        _ = node.pop(_node_key)

            else:

                if DEBUG.IfKeyTransformer:
                    _msg = f'{_logical_exp} is FALSE'
                    ic(_msg)

                if not _if:
                    if not _forward_slash:
                        self._replace_node_key(node, _node_key,list(_branches.keys())[0], _true_branch)
                    else:
                        self._replace_node_key(node, _node_key, None, _true_branch)
                elif _if:
                    if _false_branch:
                        if not _forward_slash:
                            self._replace_node_key(node, _node_key,list(_branches.keys())[1], _false_branch)
                        else:
                            self._replace_node_key(node, _node_key, None, _false_branch)
                    else:
                        _ = node.pop(_node_key)


class IfKeyTransformerUtility(IfKeyTransformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
