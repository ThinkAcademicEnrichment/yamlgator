from ..constants import *
from .AbstractState import  *

from . import DEBUG

class AggregateState(AbstractState):
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


class DAggregateState(AbstractState):
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


class TreeState(AbstractState):
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
    def post_update(self,node,keychain):
        if DEBUG.TreeState:
            ic()
            ic(keychain)
        for _observation in self.post_observables:
            _result = _observation.observe(node, keychain)
            if _result:
                _state_keychain, _value = _result
                if DEBUG.TreeState:
                    ic(_state_keychain)
                    ic(_value)
                try:
                    _values = self.get(_state_keychain)
                    if DEBUG.TreeState:
                        ic(_values)
                except KeyError:
                    # _state_keychain has already been popped ?
                    if DEBUG.TreeState:
                        _msg = f'{_state_keychain} not found; ignoring'
                        ic(_msg)
                    # return
                    continue
                self.pop(_state_keychain)

            if DEBUG.TreeState:
                ic(_observation.__class__)
                ic(_result)
