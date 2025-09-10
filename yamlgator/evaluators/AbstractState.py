from ..tree import *

class AbstractState(Tree):
    def __init__(self,  pre_observables=(), value_observables=(), post_observables=(),initial_state=None):
        super().__init__(initial_state)
        self.pre_observables = pre_observables
        self.post_observables = post_observables
        self.value_observables = value_observables
        self.all_observables = pre_observables + post_observables + value_observables

    def pre_update(self,node,keychain):
        raise NotImplemented

    def value_update(self,value,keychain):
        raise NotImplemented

    def post_update(self,node,keychain):
        raise NotImplemented