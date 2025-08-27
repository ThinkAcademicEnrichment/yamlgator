from .tree import Tree
from copy import copy
from collections import OrderedDict
class UnOrderedTreeException(Exception):
    pass

class UTree(Tree):
    def __init__(self, odict_or_dict_or_tree=None):
        if odict_or_dict_or_tree is None:
            self.odict = dict()
        elif isinstance(odict_or_dict_or_tree, dict):
            self.odict = odict_or_dict_or_tree
        elif issubclass(odict_or_dict_or_tree.__class__, UTree):
            self.odict = odict_or_dict_or_tree.odict
        else:
            raise UnOrderedTreeException('Cannot create tree')

    def visit(self,pre_process=lambda x, y:None, post_process=lambda x, y:None, value_process=lambda x, y:None,reverse=False):
        if reverse:
            raise UnOrderedTreeException('Reverse visiting not supported !')

        self._visit(self.odict, pre_process, post_process, value_process, None)

    def _visit(self, node, pre_process=lambda x, y:None, post_process=lambda x, y:None, value_process=lambda x, y:None,keychain=None):
        keychain = [] if keychain is None else keychain

        if isinstance(node,dict) or isinstance(node,OrderedDict):
            pre_process(node,copy(keychain))
            for _child_key in node.keys():
                keychain.append(_child_key)
                self._visit(node.get(_child_key), pre_process, post_process, value_process, copy(keychain))
                keychain.pop()
            post_process(node,copy(keychain))

        else:
            value_process(node,keychain)

    def copy(self):
        '''return a copy of the tree'''
        return UTree(deepcopy(self.odict))


