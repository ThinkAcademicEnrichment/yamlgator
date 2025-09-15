from ..constants import *
from ..tree import *
from ..YAMLator import YAMLator
from .States import *
from .Observables import *


from . import DEBUG

class StateEvaluator(YAMLator):
    """ _post_evaluate,_pre_evaluate and _value_evaluate all have access to the state
        which is updated upon entering and exiting a node of nodes, or a node containing a value.
    """

    def __init__(self, tree, state,**kwargs):
        # if a subclass of this calls copy() it needs to call the constructor with root_dir=self.root_dir
        super().__init__(tree,**kwargs)
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
