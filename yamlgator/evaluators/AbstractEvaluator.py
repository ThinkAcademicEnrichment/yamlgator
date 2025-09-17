from ..tree import *

# this has no role yet
class AbstractEvaluator(Tree):


    def evaluate(self,*args):
        self.visit(self._pre_evaluate, self._post_evaluate, self._value_evaluate)

    def _pre_evaluate(self, node, keychain):
        pass

    def _post_evaluate(self, node, keychain):
        pass

    def _value_evaluate(self, value, keychain):
        pass
