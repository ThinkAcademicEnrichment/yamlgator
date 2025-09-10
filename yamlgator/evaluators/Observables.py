from ..constants import *
from .AbstractObservable import *

from . import DEBUG

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

