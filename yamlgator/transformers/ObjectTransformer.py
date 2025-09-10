"""
Deprecated, tree values are always string reps of objects, upper case vars are set with object values
"""

from ..evaluators import AbstractEvaluator
from ..transformers import Transformer, TransformerException, AtTransformer
from ..constants import *

class ObjectValueEvaluatorException(Exception):
    pass

class ObjectValueEvaluator(AbstractEvaluator):

    def _all_tokens(self,value_str):
        return
    @classmethod
    def _object_map(cls, key, values):
        # TODO we need a standard to decode obj types from key names
        _new_values = []
        for _value in values:
            # note: special variables don't tokenize like regular variables!!
            _tokens = Transformer()._tokenize(_value) + AtTransformer()._tokenize(_value)
            if any(list(map(lambda x:is_variable_token(x),_tokens))):
                _new_values.append(_value)
                continue
            if '-dir' in key or '-path' in key:
                _value = pathlib.Path(_value).expanduser()
                if '-dir' in key:
                    # directory creation
                    if not _value.exists():
                        try:
                            _value.mkdir(parents=True, exist_ok=True)
                        except PermissionError:
                            raise ObjectValueEvaluatorException
                            # print(f"permision denied to create {_value}")
                else:
                    # path creation
                    if not _value.exists():
                        try:
                            _value.touch(exist_ok=True)
                        except PermissionError:
                            print(f"permission denied to create {_value}. This could be fatal.")
            elif '-url' in key:
                # TODO test url
                _value = urlpath.URL(_value)
            # elif 'use-' in key or 'is-' in key or 'has-' in key:
            elif key.startswith('use-') or key.startswith('is-') or key.startswith('has-'):
                if isinstance(_value,str):
                    if not re.match(REGEXES.BOOL_REGEX,_value):
                        raise TransformerException(f"{_value} is not a recognized boolean string")
                    if _value in TRUE_VALUES:
                        _value = True
                    elif _value in FALSE_VALUES:
                        _value = False
                    else:
                        raise TransformerException("Regex failure")
                elif isinstance(_value,bool):
                    pass
                else:
                    raise TransformerException(f"Wrong value type: {type(_value)} for key: {key}")
            _new_values.append(_value)
        return _new_values

    def _value_evaluate(self, value, keychain):
        _key = keychain[-1]
        _value = value
        if not isinstance(_value, list):
                _tmp_values = [str(_value)]
        else:
            _tmp_values = list(map(str,_value))

        _new_values = self._object_map(_key,_tmp_values)

        if isinstance(value,list):
            value = _new_values
        else:
            value = _new_values.pop()
        self.get(keychain, value)
