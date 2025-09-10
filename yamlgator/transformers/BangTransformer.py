from ..tree import *
from ..constants import *
from .ValueTransformer import ValueTransformer

from . import DEBUG

class BangTransformerException(Exception):
    pass


class BangTransformer(ValueTransformer):
    match_regex = rf"{re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.BANG}"
    extract_regex = rf"{re.escape(KEY_OR_KEYCHAIN_OP)}{REGEXES.BANG_EXP}"

    name = 'transform_bangs'
    def __init__(self, odict_or_tree=None, **kwargs):
        odict_or_tree = OrderedDict() if odict_or_tree is None else odict_or_tree
        super(BangTransformer, self).__init__(odict_or_tree)
        # if DEBUG.BangTransformer:
        #     ic()

        if isinstance(odict_or_tree, Tree):
            self.driver_source = odict_or_tree
        else:
            self.driver_source = None

    def _transform(self, parameters, keychain):
        _method_call, = parameters
        if DEBUG.BangTransformer:
            ic(_method_call)

        class _MethodParser(ast.NodeVisitor):
            def visit_Call(self,node):
                self.method_name = astor.to_source(node.func).strip()
                self.arguments = list(map(lambda x:astor.to_source(x).strip(),node.args))
                self.keywords = list(map(lambda x:x.arg.strip(),node.keywords))
                self.keyword_values = list(map(lambda x:astor.to_source(x.value).strip(),node.keywords))

        _mp = _MethodParser()
        _mp.visit(ast.parse(_method_call))

        if DEBUG.BangTransformer:
            ic(_mp.method_name)
            ic(_mp.arguments)
            ic(_mp.keywords)
            ic(_mp.keyword_values)

        # this might be useful someday...
        # getattr(self,_mp.method_name).__call__(*_mp.arguments,**dict(zip(_mp.keywords,_mp.keyword_values)))

        _computed_value = None
        if self.driver_source:
            try:
                _computed_value = eval(f'self.driver_source.{_method_call}')
                if DEBUG.BangTransformer:
                    # _msg = f'computed {_method_call} as {_computed_value}'
                    _msg = f'method call success'
                    ic(_msg)
                    ic(self.driver_source)
            except AttributeError:
                if DEBUG.BangTransformer:
                    _msg = f"{_method_call} not found (or the method threw AttributeError)!"
                    ic(_msg)
                    ic(self.driver_source)
                    ic(dir(self.driver_source))
                # Eventually, it will be found!
                # raise AttributeError
                _computed_value = None
            except Exception as e:
                if DEBUG.BangTransformer:
                    _msg = f"{_method_call} failed with {e}!"
                    ic(_msg)
                    ic(self.driver_source)
                _computed_value = None


        else:
            raise BangTransformerException(f"no driver source configured for {_method_call}")

        return _computed_value

class BangTransformerUtility(BangTransformer):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)