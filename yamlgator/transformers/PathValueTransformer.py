from ..constants import *
from .ValueTransformer import *

from . import DEBUG

class PathValueTransformerException(Exception):
    pass


class PathValueTransformer(ValueTransformer):
    root_dir = None
    ext = None
    # the ? after # is critical. But why?
    match_regex = rf'(?:{REGEXES.POSIX_RELATIVE}|{REGEXES.POSIX_ABSOLUTE})#?{REGEXES.KEYCHAIN}?(?:{REGEXES.KEY})?/?'
    extract_regex = r'^([^#]*?)#(.*)$'

    def __init__(self, odict_or_tree):
        # if not hasattr(odict_or_tree, 'root_dir'):
        #     raise PathValueTransformerException
        # self.root_dir = odict_or_tree.root_dir
        super(PathValueTransformer,self).__init__(odict_or_tree)


    def select(self, stream, selector):
        '''intpret a selctor string to select bytes from stream'''
        raise NotImplemented

    def _do_not_evaluate(self,value,keychain):
        # don't try to pathtransform on multi=line strings
        if isinstance(value,str) and len(value.split('\n')) > 1:
            return True

    def _match(self, line):
        # TODO: Note this
        # we have to avoid matching the internal structure of a URI somehow...
        _m = re.match(rf'([^:]*?)({self.match_regex})(.*)',str(line))
        if _m:
            if DEBUG.PathValueTransformer:
                ic()
                ic(line)
                ic(_m.groups())
        return _m

    def _extract(self, token):
        if DEBUG.PathValueTransformer:
            ic()
            ic(token)
        _m = re.match(self.extract_regex,str(token))
        if _m:
            if DEBUG.PathValueTransformer:
                ic()
                ic(token)
                ic(_m.groups())
        # else:
            # if DEBUG.PathValueTransformer:
            #     _msg = f'No path selector match for {token}!'
            #     ic(_msg)
        return _m

    def _transform(self, parameters, keychain):
        _path_str,_selector = parameters
        _path = pathlib.Path(_path_str)
        _ext = _path.name.split('.')[-1]
        if _ext == _path.name:
            _ext = None

        if DEBUG.PathValueTransformer:
            ic(_path)
            ic(_selector)
            ic(self.ext)

        if _ext != self.ext:
            if DEBUG.PathValueTransformer:
                _msg = f'wrong ext {_ext}, not {self.ext}'
                ic(_msg)
            return

        # only transform paths with the right extension!!!
        # if self.ext and _path.name.split('.')[-1] != self.ext:
        #     if DEBUG.PathValueTransformer:
        #         _msg = f'wrong extension {_path.name.split(".")[-1]} not {self.ext}'
        #         ic(_msg)
        #     return None
        # elif self.ext is None and _path.name.split('.')[-1] != _path.name :
        #     if DEBUG.PathValueTransformer:
        #         _msg = f'Found a plain text file to read'
        #         ic(_msg)


        # we handle absolute paths in yaml selectors
        if pathlib.Path(_path_str).is_absolute():
            _value_path = _path
        else:
            # there's always a root_dir set in the superclass
            _value_path = self.root_dir.joinpath(_path)

        try:
            with _value_path.open('r') as f:
                _new_value = self.select(f, _selector)
        except FileNotFoundError as e:
            if DEBUG.PathValueTransformer:
                ic(e)
            _new_value = None
        except KeyError as e:
            if DEBUG.PathValueTransformer:
                ic(e)
            _new_value = None
        return _new_value
