from ..constants import *
from ..tree import Tree
from ..YAMLator import YAMLator, YAMLatorException, YAMLatorObjectDB
from . import DEBUG


class AbstractObservable:
    # we might want to turn off certain observables from aggregating....?
    aggregate = True

    def __init__(self,**kwargs):
        [ setattr(self,k,v) for k,v in kwargs.items() ]

    def observe(self,node,keychain):
        _keychain_parameters = self._test_keychain(node,keychain)
        if _keychain_parameters:
            return self._create_observation(node,*_keychain_parameters)
        return

    def read(self,state_or_evaluator):
       pass

    def _test_keychain(self,node,keychain):
        return []

    def _create_state_keychain(self,*parameters):
        return

    def _create_observation(self,node,*parameters):
        return self._create_state_keychain(*parameters),None


class KeyPresenceObservable(AbstractObservable):
    keys = None

    def _test_keychain(self,node,keychain):
        if any(map(lambda x:x in keychain,self.keys)):
            return keychain
        return


class KeyAbsenceObservable(AbstractObservable):
    keys = None

    def _test_keychain(self, node,keychain):
        if all(map(lambda x: not x in keychain, self.keys)):
            return keychain
        return


class KeyLookAheadObservable(AbstractObservable):
    keys = None

    def _test_keychain(self,node,keychain):
        if DEBUG.Observable:
            ic(self.__class__)
            ic(keychain)

        _matched_keychain = None
        _matched_node_key = None
        for _node_key in node.keys():

            if _node_key in self.keys:

                assert _matched_node_key is None
                _matched_node_key = _node_key

        if _matched_node_key:
            _matched_keychain = keychain + [_matched_node_key]

        if DEBUG.Observable:
            ic(_matched_node_key)
            ic(_matched_keychain)
        return _matched_keychain


class RegexObservable(AbstractObservable):
    keychain_regex = None

    def _test_keychain(self, node, keychain):
        if DEBUG.Observable:
            ic(self.__class__)
            ic(keychain)
        _m = re.match(self.keychain_regex, '/'.join(keychain))
        if not _m:
            return
        _parameters = _m.groups()
        return _parameters


class RegexLookAheadObservable(AbstractObservable):
    keychain_regex = None

    def _test_keychain(self,node, keychain):
        _parameters = None
        _matched_keychain = None
        _matched_node_key = None
        for _node_key in node.keys():
            _m = re.match(self.keychain_regex,'/'.join(keychain + [_node_key]))
            if _m:
                _parameters = _m.groups()

        return _parameters

# this aggregates state values for a state keychain in lists; we may not always want that
class AggregateState(Tree):
    def __init__(self,  pre_observables=(), value_observables=(), post_observables=(),initial_state=None):
        super().__init__(initial_state)
        self.pre_observables = pre_observables
        self.post_observables = post_observables
        self.value_observables = value_observables
        self.all_observables = pre_observables + post_observables + value_observables

    def pre_update(self,node,keychain):
        if DEBUG.AggregateState:
            ic()
            ic(keychain)
        for _observation in self.pre_observables:
            _result = _observation.observe(node,keychain)
            if _result:
                if _observation.aggregate:
                    self.aget(*_result)
                else:
                    # TODO: observables can skip aggregating with this flag
                    self.get(*_result)

            if DEBUG.AggregateState:
                ic(_observation.__class__)
                ic(_result)

    def value_update(self,value,keychain):
        if DEBUG.AggregateState:
            ic()
            ic(keychain)
        for _observation in self.value_observables:
            _result = _observation.observe(value, keychain)
            if _result:
                if _observation.aggregate:
                    self.aget(*_result)
                else:
                    self.get(*_result)

            if DEBUG.AggregateState:
                ic(_observation.__class__)
                ic(_result)

    # this never pops any state created by value_update
    def post_update(self,node,keychain):
        if DEBUG.AggregateState:
            ic()
            ic(keychain)
        for _observation in self.post_observables:
            _result = _observation.observe(node, keychain)
            if _result:
                _state_keychain, _value = _result
                if DEBUG.AggregateState:
                    ic(_state_keychain)
                    ic(_value)
                try:
                    _values = self.get(_state_keychain)
                    if DEBUG.AggregateState:
                        ic(_values)
                except KeyError:
                    # _state_keychain has already been popped ?
                    if DEBUG.AggregateState:
                        _msg = f'{_state_keychain} not found; ignoring'
                        ic(_msg)
                    # return
                    continue
                if isinstance(_values,list) and _values and _observation.aggregate:
                    if not isinstance(_value,list):
                        _value = [_value]
                    try:
                        for __value in _value:
                            _popped_value = _values.pop(_values.index(__value))
                            assert _popped_value in _value
                            _new_value = self.get(_state_keychain,_values)
                            if DEBUG.AggregateState:
                                ic(_new_value)
                    except ValueError as e:
                        if DEBUG.AggregateState:
                            ic()
                            ic(self.__class__)
                            ic(e)
                        continue
                else:
                    self.pop(_state_keychain)

            if DEBUG.AggregateState:
                ic(_observation.__class__)
                ic(_result)


# TODO: this is not quite right
class DAggregateState(AggregateState):
    def pre_update(self,node,keychain):
        for _observation in self.pre_observables:
            _result = _observation.observe(node,keychain)
            if _result:
                self.daget(*_result)
                if DEBUG.DAggregateState:
                    ic()
                    ic(keychain)
                    ic(self.print())

    def value_update(self,value,keychain):
        for _observation in self.value_observables:
            _result = _observation.observe(value, keychain)
            if _result:
                self.daget(*_result)
                if DEBUG.DAggregateState:
                    ic()
                    ic(keychain)
                    ic(self.print())

    def post_update(self,node,keychain):
        for _observation in self.post_observables:
            _result = _observation.observe(node, keychain)
            if _result:
                _state_keychain, _value = _result
                try:
                    _values = self.get(_state_keychain)
                except KeyError:
                    return
                if isinstance(_values,dict) and _values:
                    _new_values = [_values.pop(_k) for _k in _value.keys()]
                    self.get(_state_keychain,_new_values)
                else:
                    self.pop(_state_keychain)
                if DEBUG.AggregateState:
                    ic()
                    ic(keychain)
                    ic(_state_keychain)


class TreeState(AggregateState):
    def pre_update(self,node,keychain):
        for _observation in self.pre_observables:
            _result = _observation.observe(node,keychain)
            if _result:
                # we need to use an overlay type get here, I think
                self.oget(*_result)
                if DEBUG.TreeState:
                    ic()
                    ic(keychain)
                    ic(_result[0])
                    ic(self.keys())
                    # ic(self.print())

    def value_update(self,value,keychain):
        for _observation in self.value_observables:
            _result = _observation.observe(value, keychain)
            if _result:
                self.oget(*_result)
                if DEBUG.TreeState:
                    ic()
                    ic(keychain)
                    ic(_result[0])
                    ic(self.keys())
                    # ic(self.print())


# class StateEvaluator(YAMLator):
#     """ _post_evaluate,_pre_evaluate and _value_evaluate all have access to the state
#         which is updated upon entering and exiting a node of nodes, or a node containing a value.
#     """
#     def __init__(self, tree, state,root_dir=None,objdb=None):
#         super().__init__(tree,root_dir,objdb)
#         self.state = state

class StateEvaluator(YAMLator):
    """ _post_evaluate,_pre_evaluate and _value_evaluate all have access to the state
        which is updated upon entering and exiting a node of nodes, or a node containing a value.
    """
    # class StateEvaluator(YAMLator):

    def __init__(self, tree, state):
        super().__init__(tree)
        self.state = state

    def read_state(self,observable):
        try:
            return list(filter(lambda x: isinstance(x, observable),
                               self.state.pre_observables + self.state.value_observables)).pop().read(self.state)
        except IndexError:
            return None

    def aggregate_state(self,observable):
        # we call laggretate() and daggregate() on self, an evaluator, not self.state like in read_state
        try:
            return list(filter(lambda x: isinstance(x, observable),
                               self.state.pre_observables + self.state.value_observables)).pop().read(self)
        except IndexError:
            return None

    def _pre_evaluate(self):
        pass

    def _post_evaluate(self):
        pass

    def _value_evaluate(self):
        pass

    def reset_state(self,*keychains_to_preserve):
        self.state.reset(*keychains_to_preserve)

    def evaluate(self,reverse=False):
        def _pre(node, keychain):
            if DEBUG.StateEvaluator:
                ic()
            self.state.pre_update(node,keychain)
            self._pre_evaluate()

        def _val(value,keychain):
            if DEBUG.StateEvaluator:
                ic()
            self.state.value_update(value,keychain)
            self._value_evaluate()

        def _post(node, keychain):
            self._post_evaluate()
            self.state.post_update(node, keychain)

        self.visit(_pre, _post, _val, reverse=reverse)
        return self



    def laggregate(self,property_name):
        '''aggregate all properties into a single list'''
        class _PropertyAggregator(RegexObservable):
            def __init__(self, property):
                self.keychain_regex = rf'^{REGEXES.KEYCHAIN}({property})$'
                super().__init__()
                self.property = property

            def _create_observation(self, node, *parameters):
                assert parameters[0] == self.property
                return self.property, node

        return StateEvaluator(
            self.state,
            AggregateState(
                value_observables=(_PropertyAggregator(property_name),),
                initial_state=Tree(
                    OrderedDict({
                        property_name: []
                    })
                ),
            )
        ).evaluate().state.get(property_name)

    def daggregate(self,property_name):
        '''aggregate all property dictionaries into a single dict'''
        class _PropertyDaggregator(RegexObservable):
            def __init__(self, property):
                self.keychain_regex = rf'^{REGEXES.KEYCHAIN}({property})$'
                super().__init__()
                self.property= property

            def _create_observation(self, node, *parameters):
                # if DEBUG.StateEvaluator:
                #     ic()
                #     ic(parameters)
                #     ic(node)
                assert parameters[0] == self.property
                if isinstance(node,list):
                    return self.property, reduce(lambda x, y: {**y, **x}, filter(lambda x: x is not None, node))
                else:
                    return self.property,node

        return StateEvaluator(
            self.state,
            DAggregateState(
                value_observables=(_PropertyDaggregator(property_name),),
                initial_state=Tree(
                    OrderedDict({
                        property_name: {}
                    })
                )
            )
        ).evaluate().state.get(property_name)
