from ..constants import *
from .PathValueTransformer import *

from . import DEBUG

class PlainTextTransformerException(Exception):
    pass


class PlainTextTransformer(PathValueTransformer):
    name = 'transform_plaintext'
    ext = None

    def __init__(self, odict_or_yamlator_or_tree, context_tree=None, allow_tree_subs=False,root_dir=None):

        if hasattr(odict_or_yamlator_or_tree, 'root_dir') and root_dir is None:
            self.root_dir = odict_or_yamlator_or_tree.root_dir
        else:
            root_dir = pathlib.Path('.') if root_dir is None else root_dir
            self.root_dir = pathlib.Path(root_dir).absolute()

        super(PlainTextTransformer,self).__init__(odict_or_yamlator_or_tree)

        if DEBUG.PlainTextTransformer:
            ic(self.__class__)
            ic(self.ext)
            ic(self.root_dir)
            # ic(self.print())


    def select(self, stream, keychain):
        if DEBUG.PlainTextTransformer:
            ic()
            ic(keychain)

        # let's avoid a syscall that's going to fail
        if any(map(is_variable_token,keychain.split('/'))):
            if DEBUG.PlainTextTransformer:
                _msg = f'found unsubbed vars'
                ic(_msg)
                ic(keychain)
            return None

        _stream_path = pathlib.Path(stream.name)

        _plain_text = stream.read()

        if DEBUG.PlainTextTransformer:
            ic(_stream_path)
            ic(_plain_text)

        return _plain_text

    # # for testing
    # def _match(self, line):
    #     ic(line)
    #     # TODO: Note this
    #     # we have to avoid matching the internal structure of a URI somehow...
    #     _m = re.match(rf'([^:]*?)({self.match_regex})(.*)',str(line))
    #     if _m:
    #         ic()
    #         ic(line)
    #         ic(_m.groups())
    #     return _m
    #
    # def _extract(self, token):
    #     ic()
    #     ic(token)
    #     _m = re.match(r'^([^#]*?)#(.*)$',str(token))
    #     if _m:
    #         ic()
    #         ic(token)
    #         ic(_m.groups())
    #     # else:
    #         # if DEBUG.PathValueTransformer:
    #         #     _msg = f'No path selector match for {token}!'
    #         #     ic(_msg)
    #     return _m

    # def _transform(self, parameters, keychain):
    #     ic()
    #     _path_str,_selector = parameters
    #     _path = pathlib.Path(_path_str)
    #     ic(_path)
    #     ic(_selector)
    #
    #     # only transform paths with the right extension!!!
    #     if self.ext and _path.name.split('.')[-1] != self.ext:
    #         _msg = f'wrong extension {_path.name.split(".")[-1]} not {self.ext}'
    #         ic(_msg)
    #         return
    #     else:
    #         _msg = f'Found a plain text file to read'
    #         ic(_msg)
    #
    #
    #     # we handle absolute paths in yaml selectors
    #     if pathlib.Path(_path_str).is_absolute():
    #         _value_path = _path
    #     else:
    #         if DEBUG.PlainTextTransformer:
    #             ic(self.root_dir)
    #         _value_path = self.root_dir.joinpath(_path)
    #
    #     try:
    #         with _value_path.open('r') as f:
    #             _new_value = self.select(f, _selector)
    #     except FileNotFoundError as e:
    #         ic(e)
    #         _new_value = None
    #     except KeyError as e:
    #         ic(e)
    #         _new_value = None
    #     if DEBUG.PlainTextTransformer:
    #         ic(_new_value)
    #
    #     return _new_value
    #
    #


class PlainTextTransformerUtility(PlainTextTransformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)