class AbstractObservable:
    # we might want to turn off certain observables from aggregating
    aggregate = True

    def __init__(self,**kwargs):
        [ setattr(self,k,v) for k,v in kwargs.items() ]

    def observe(self,node,keychain):
        _keychain_parameters = self._test_keychain(node,keychain)
        if _keychain_parameters:
            return self._create_observation(node,*_keychain_parameters)
        return None

    def read(self,state_or_evaluator):
       pass

    def _test_keychain(self,node,keychain):
        return []

    def _create_state_keychain(self,*parameters):
        return

    def _create_observation(self,node,*parameters):
        return self._create_state_keychain(*parameters),None

