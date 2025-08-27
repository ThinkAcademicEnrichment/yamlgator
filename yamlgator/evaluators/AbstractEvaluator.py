from ..tree import Tree

class AbstractEvaluator(Tree):
    def __init__(self, odict_or_tree):
        super(AbstractEvaluator,self).__init__(odict_or_tree)

    def evaluate(self,*args):
        self.visit(self._pre_evaluate, self._post_evaluate, self._value_evaluate)

    def _pre_evaluate(self, node, keychain):
        pass

    def _post_evaluate(self, node, keychain):
        pass

    def _value_evaluate(self, value, keychain):
        pass


class AbstractReverseEvaluator(Tree):
    def evaluate(self):
        self.visit(self._pre_evaluate, self._post_evaluate, self._value_evaluate,reverse=True)


class AbstractContextEvaluator(Tree):
    def _do_not_evaluate(self,keychain):
        pass

    def _update_state(self,observation):
        pass

    def _create_observation(self,node,keychain):
        pass

    def evaluate(self):
        def _pre(node,keychain):
            if self._do_not_evaluate(keychain):
                return

            self._update_state(self._create_observation(node, keychain))

            # THESE ARE OVER-RIDDEN!!!
            self._pre_evaluate(node, keychain)

        def _post(node,keychain):
            if self._do_not_evaluate(keychain):
                return

            # THESE ARE OVER-RIDDEN!!!
            self._post_evaluate(node, keychain)

            self._pop_state()

        def _value(value,keychain):
            if self._do_not_evaluate(keychain):
                return
            self._value_evaluate(value, keychain)

        self.visit(_pre, _post, _value)

        return self

