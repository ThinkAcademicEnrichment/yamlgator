from ..constants import *
from ..evaluators.AbstractEvaluator import *

from . import DEBUG

class TransformerException(Exception):
    pass

class Transformer(AbstractEvaluator):

    def __init__(self, odict_or_tree=None):
        odict_or_tree = OrderedDict() if not odict_or_tree else odict_or_tree
        # super(Transformer, self).__init__(odict_or_tree)
        super().__init__(odict_or_tree)
    def _match(self, line):
        '''used recursively in self._tokenize to split a line into tokens by matching'''
        # return a re.match object or None to skip
        # if m = re.match then  len(m.groups()) == 3: head,match,tail
        raise NotImplemented

    def _extract(self, token):
        '''used in self.value_evaluate() to extract regex groups from a token which are passed to self._transform() as parameters'''
        # return a re.match object or None to skip
        raise NotImplemented

    def _transform(self, parameters, keychain):
        # use the supplied parameters to produce a str or bytes value
        # include the keychain for context awareness
        raise NotImplemented

    def _do_not_evaluate(self, value, keychain):
        # skip this nodes for a specific reason
        return False

    def _tokenize(self, expression, pieces=None):
        '''
        tokenize an expression recursively, splitting it by presence of the first match of re_matcher expression
        turn a line into a list of tokens
        '''
        if DEBUG.Transformer:
            ic()
            ic(self.match_regex)
            ic(expression)
            # ic(pieces)
        # don't parse blank lines; but include them in the output
        if expression == '':
            return ''

        pieces = pieces if pieces is not None else []

        _match = self._match(expression)
        if _match:
            if DEBUG.Transformer:
                ic(_match.groups())

            _front, _match, _back = _match.groups()
            if _match == '':
                pieces.append(expression)
            if _front != '':
                pieces.append(_front)

            pieces.append(_match)
            if _back != '':
                self._tokenize(_back, pieces)
        else:
            pieces.append(expression)

        if DEBUG.Transformer:
            ic(pieces)

        return list(pieces)
