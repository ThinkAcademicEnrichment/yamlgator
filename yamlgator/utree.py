from .constants import *
from .tree import *

class UnOrderedTreeException(Exception):
    pass

class UTree(Tree):
    def __init__(self, odict_or_dict_or_tree=None):
        super().__init__()
        if odict_or_dict_or_tree is None:
            self.odict = dict()
        elif isinstance(odict_or_dict_or_tree, dict):
            self.odict = odict_or_dict_or_tree
        elif issubclass(odict_or_dict_or_tree.__class__, UTree):
            self.odict = odict_or_dict_or_tree.odict
        else:
            raise UnOrderedTreeException('Cannot create tree')

    def visit(self,pre_process=lambda x, y:None, post_process=lambda x, y:None, value_process=lambda x, y:None,reverse=False,entry_keychain=None):
        """Reverse visting is not supported for UTree objects."""
        if reverse:
            raise UnOrderedTreeException('Reverse visiting is not supported !')
        if entry_keychain:
            raise UnOrderedTreeException('Tree entry keychains are not supported !')

        self._visit(self.odict, pre_process, post_process, value_process, None)

    visit.__doc__ += '\n' + Tree.visit.__doc__

    def _visit(self, node, pre_process=lambda x, y:None, post_process=lambda x, y:None, value_process=lambda x, y:None,keychain=None,entry_keychain=None,process=None):
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


