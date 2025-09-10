from ..constants import *
from .PathValueTransformer import *
from ..tree import *

from . import DEBUG

class YAMLTransformerException(Exception):
    pass


class YAMLTransformer(PathValueTransformer):
    name = 'transform_yaml'
    ext = 'yaml'

    def __init__(self, odict_or_yamlator_or_tree, context_tree=None, allow_tree_subs=False, root_dir=None):

        if hasattr(odict_or_yamlator_or_tree, 'root_dir') and root_dir is None:
            self.root_dir = odict_or_yamlator_or_tree.root_dir
        else:
            root_dir = pathlib.Path('.') if root_dir is None else root_dir
            self.root_dir = pathlib.Path(root_dir).absolute()

        super(YAMLTransformer, self).__init__(odict_or_yamlator_or_tree)

    def select(self, stream, keychain):

        if any(map(is_variable_token,keychain.split('/'))):
            if DEBUG.YAMLTransformer:
                _msg = f'found unsubbed vars'
                ic(_msg)
                ic(keychain)
            return None

        _stream_path = pathlib.Path(stream.name)
        if DEBUG.YAMLTransformer:
            ic()
            ic(keychain)
            ic(_stream_path)
        if _stream_path.absolute():
            _new_root_dir = _stream_path.parent
            _yt = YAMLTransformer(Tree.load(stream),root_dir=_new_root_dir)
        else:
            _new_root_dir = _stream_path.parent.relative_to(self.root_dir)
            _yt = YAMLTransformer(Tree.load(stream),self.root_dir.joinpath(_new_root_dir))

        if DEBUG.YAMLTransformer:
            ic(_new_root_dir)

        # TODO: this needs documenting; it's tricky
        # NOTICE: keeps loading trees until we run out of selector references
        # YAMLTransformer calls itself recursively

        _yt.evaluate()

        try:
            # if DEBUG.YAMLTransformer:
            #     _value = _yt.get(keychain)
                # ic(_value.print()) if isinstance(_value,Tree) else ic(_value)
            return _yt.get(keychain)
        except KeyError:
            # keychain may contain un-subbed variables
            if DEBUG.YAMLTransformer:
                _msg = f'Failed to select {keychain}'
                ic(_msg)
            return


class YAMLTransformerUtility(YAMLTransformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)