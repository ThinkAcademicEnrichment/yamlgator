from .tree import Tree
from .transformers import *
from .objdb import *
from .constants import *


DEFAULT_UTILITIES= {
    'transform_imports':ImportTransformerUtility,
    'transform_values':ValueTransformerUtility,
    'transform_ats':AtTransformerUtility,
    'transform_bangs':BangTransformerUtility,
    'transform_yaml':YAMLTransformerUtility,
    'transform_keys':KeyTransformerUtility,
    'transform_if_keys':IfKeyTransformerUtility,
    'transform_ifs':IfTransformerUtility,
    'transform_plaintext':PlainTextTransformerUtility,
}


class _DEBUG:
    YAMLator = False
    CONFIG_ATTRS = False


class YAMLatorException(Exception):
    pass


class YAMLatorObjectDB(ObjectDB):
    regexes = None

    def __init__(self):
        super(YAMLatorObjectDB,self).__init__()

        self.regexes = {}


    def add_object(self, key_type, key_type_regex, constructor, *args, **kwargs):
        self._register(key_type, constructor, *args, **kwargs)
        self.regexes[key_type] = key_type_regex

    def get_object(self,key,value):
        try:
            return getattr(self,self.key_type(key))(value)
        except TypeError:
            return value

    def get_as_object(self,key):
        _value = self.get(key)
        try:
            return getattr(self,self.key_type(key))(_value)
        except TypeError:
            _msg = f"could not make a {self.key_types(key)} object from {_value}"
            raise YAMLatorException(f"could not make an ")

    def key_types(self):
        return list(self.regexes.keys())

    def key_type(self,key):
        _key_type = None
        for __key_type, _regex in self.regexes.items():
            _m = re.match(_regex, key)
            if _m:
                if _key_type is not None and _key_type != __key_type:
                    raise YAMLatorException('we matched two keys types for one key!')
                _key_type = __key_type
        return _key_type

    def register(self,object_class,attribute_name,*args,**kwargs):
        self._register(attribute_name,object_class,self,*args,**kwargs)

class YAMLator(YAMLatorObjectDB,Tree):
    """A powerful, high-level configuration processing engine.

    YAMLator provides a robust framework for managing and processing complex
    YAML-based configurations. It inherits from the `Tree` class, giving it a
    hierarchical, dictionary-like data structure that is easy to navigate.

    Its two primary features are:
    1.  A transformation engine that iteratively resolves macros, variables,
        imports, and conditionals. This process continues until the
        configuration is fully expanded and reaches a stable state (see the
        `transform` method).
    2.  A dynamic type system that automatically casts string values into rich
        Python objects (e.g., `pathlib.Path`, `bool`, `urlpath.URL`) based on
        regular expression patterns matched against their corresponding keys.

    The primary use case is to load a templated YAML file and transform it
    into a fully resolved, type-safe, and easily accessible configuration
    object.

    Attributes:
        root_dir (pathlib.Path): The absolute path that serves as the base
            for resolving relative file paths during transformations, such as
            for `!import` directives.
        (UPPERCASE_ATTRIBUTES): After processing (e.g., by calling
            `set_config_attrs`), the instance is populated with additional
            uppercase attributes. These attributes correspond to keys in the
            YAML data and provide direct, type-casted access to the final
            configuration values.
    """

    @classmethod
    def load(cls, stream):
        """A class method factory for creating a new YAMLator instance from a stream.

        This method overrides the parent `Tree.load` method. Its primary purpose
        is to automatically determine the `root_dir` for the new instance, which
        is crucial for resolving relative file paths in directives like `!import`.

        The `root_dir` is determined based on the stream type:
        - If the stream is a file, `root_dir` is set to the file's directory.
        - If the stream is an `io.StringIO` instance, it uses a default path
          based on the current working directory.

        Args:
            stream (file-like object or io.StringIO): The source of the YAML
                data. This can be a file-like object (from an open file) or
                an `io.StringIO` instance for in-memory YAML content.

        Returns:
            YAMLator: A new `YAMLator` instance, initialized with the parsed
                data and the determined `root_dir`.
        """
        if isinstance(stream,io.StringIO):
            _root_dir = str(pathlib.Path('.').parent)
        else:
            _root_dir = str(pathlib.Path(stream.name).parent)
        return YAMLator(cls._load(stream),_root_dir)

    def __init__(self, odict_or_yamlator_or_tree=None, root_dir=None):
        """Initializes a new YAMLator instance.

        Args:
            odict_or_yamlator_or_tree (OrderedDict | YAMLator | Tree | str | None, optional):
                Provides the initial data for the object. It can be one of
                several types:
                - OrderedDict: To initialize from a pre-existing dictionary.
                - YAMLator or Tree: To initialize from another instance,
                  effectively creating a copy.
                - str: To initialize by parsing a string of YAML content.
                - None: To create an empty YAMLator instance.
                Defaults to None.
            root_dir (pathlib.Path or str, optional): The base directory used
                to resolve relative file paths found within the YAML content
                (e.g., for `!import` directives). If not provided, it will be
                inferred from the input data source (if it has a `root_dir`
                attribute) or will default to the current working directory.
                Defaults to None.
        """
        # this order is critical
        YAMLatorObjectDB.__init__(self)
        Tree.__init__(self, odict_or_yamlator_or_tree)
        if hasattr(odict_or_yamlator_or_tree, 'root_dir') and root_dir is None:
            self.root_dir = odict_or_yamlator_or_tree.root_dir
        else:
            root_dir = pathlib.Path('.') if root_dir is None else root_dir
            self.root_dir = pathlib.Path(root_dir).absolute()

        # ensure custom objdb has the default types
        for _key_type, _data in DEFAULT_KEY_TYPES.items():
            _key_regex, _object_constructor_data = _data
            self.add_object(_key_type, _key_regex, *_object_constructor_data)

        # register the default utilities
        for _attribute_name,_transformer_class in DEFAULT_UTILITIES.items():
            self.register(_transformer_class,_attribute_name)


    def transform(self,methods=None,context_tree=None,allow_tree_subs=False):
        """The main processing engine for the YAMLator object.

        This method repeatedly applies a suite of transformation utilities to the
        data. The process continues in a loop until the data reaches a "stable
        state" or "fixed point," meaning a full pass of all transformers causes
        no further changes.

        This iterative approach is necessary to correctly resolve interdependent
        operations, such as importing a file and then substituting variables
        that were defined within it.

        Args:
            methods (list[str], optional): A sequence of strings, where each
                string is the name of a transformer method to run. If None,
                all default transformers are used. Defaults to None.
            context_tree (Tree | YAMLator, optional): An optional Tree or
                YAMLator object that provides an external context for lookups
                (e.g., for resolving variables not defined in the current
                tree). Defaults to None.
            allow_tree_subs (bool, optional): A boolean flag passed to the
                transformers to enable or disable a specific substitution
                feature. Defaults to False.

        Returns:
            None: The method modifies the YAMLator instance in-place.
        """
        # apply all default utilities until no more change in self.odict
        methods = methods if methods is not None else tuple(DEFAULT_UTILITIES.keys())
        _methods = []
        for _method in methods:
            _methods.append(getattr(self, _method))
        _old_odict = self.copy().odict
        [_method(context_tree=context_tree,allow_tree_subs=allow_tree_subs) for _method in _methods]
        while self.odict != _old_odict:
            _old_odict = self.copy().odict
            [_method(context_tree=context_tree,allow_tree_subs=allow_tree_subs) for _method in _methods]

    def get(self,keychain_or_keychain_str,value=None):
        """
        Wraps Tree.get() to return a YAMLator instance.

        This method follows the exact same semantics as the parent method,
        but ensures the return type is a YAMLator object for chainable
        operations.
        """
        # AND transfer registered utilities and objdb
        _tmp_value = super(YAMLator,self).get(keychain_or_keychain_str,value)
        if isinstance(_tmp_value,Tree):
            _yt = YAMLator(
                _tmp_value,
                root_dir=self.root_dir)
            _yt.set_config_attrs()
            return _yt
        else:
            return _tmp_value
    # Append the parent's detailed docstring after the class is defined
    get.__doc__ += '\n' + Tree.get.__doc__

    def copy(self):
        """Copies the YAMLator object.

        Returns:
             YAMLator: A deepcopy of the YAMLator object.
        """
        _yt = YAMLator(deepcopy(self.odict),root_dir=self.root_dir)
        _yt.set_config_attrs()
        return _yt

    def merge(self, yaml_path_selector, keychain_str=None, relative=False):
        """Merges data from an external YAML file into the current instance.

        This method imports data from a specified YAML file and merges it into
        the current YAMLator tree in-place. It allows for selecting a specific
        portion of the external file to merge.

        Args:
            yaml_path_selector (str): A string specifying the source file and an
                optional data selector, formatted as "path/to/file.yaml#selector".
                If the '#selector' part is omitted, the entire content of the
                file is merged.
            keychain_str (str, optional): A keychain string specifying the target
                location for the merge within the current tree. If the string
                ends with a '/', any existing data at that location will be
                deleted before the new data is merged. Defaults to None, which
                merges at the root.
            relative (bool): This parameter is present but currently has no effect.

        Side Effects:
            The instance's `root_dir` attribute is updated to the directory of the
            file that was merged.

        Returns:
            None

        Examples:
            Assuming `external.yaml` contains:
            ```yaml
            section_a:
              key1: value1
            section_b:
              key2: value2
            ```

            And the current YAMLator instance `yt` contains `{'existing_data': ...}`.
            To merge `section_a` from `external.yaml` into `existing_data/`,
            replacing its contents:
            >>> yt.merge('external.yaml#section_a', 'existing_data/')
        """
        # stringify as the argument might be a pathlib.Path
        yaml_path_selector = str(yaml_path_selector)
        if not '#' in yaml_path_selector:
            # assume we want to load the whole yaml file
            yaml_path_selector += '#'

        _yaml_path,_selector = yaml_path_selector.split('#')
        if _DEBUG.YAMLator:
            ic(_yaml_path)
            ic(_selector)

        if keychain_str is None:
            _keychain = []
        else:
            _keychain = keychain_str.split('/')
        if _keychain and _keychain[-1] == '':
            _keychain.pop()
            self.pop(_keychain)

        _yaml_path = pathlib.Path(_yaml_path)
        _root_dir = _yaml_path.parent

        _yt = YAMLTransformer(
            YAMLator(
                OrderedDict(
                    _merge_data=f'./{_yaml_path.name}#{_selector}'
                ),
                root_dir=_root_dir
            )
        )

        # notice: no transforms are done on the file to be merged
        # but YAMLTransformer is recursively called
        _yt.evaluate()
        self.overlay(_yt.get('/_merge_data/'),_keychain)
        # merging changes the root_dir...is that ok?
        self.root_dir = _root_dir

    def set_config_attrs(self,set_all=False):
        """Populates the instance with attributes from the configuration data.

        This method provides convenient, attribute-style access to configuration
        data by populating the instance with uppercase attributes that correspond
        to keys in the YAML tree. Attribute values are automatically converted
        to their appropriate Python types based on the object database's rules.

        The method traverses the tree depth-first. If the same key name
        (e.g., 'HOST') appears at multiple levels of nesting, the value from
        the deepest path will be the one that is set as the attribute.

        Args:
            set_all (bool, optional): Acts as a schema validator.
                - If False (the default), the method will only set attributes
                  that have been pre-defined on the class.
                - If True, the method will create and set an attribute for
                  every key found in the YAML data, regardless of whether it
                  was pre-defined.

        Returns:
            None: The method modifies the instance in-place.
        """
        _is_already_set = dict()

        def _depth_first(_node,_keychain):
            if _DEBUG.YAMLator:
                ic(_keychain)
            _node_keys = copy(list(_node.keys()))
            _node_keys.reverse()
            for _node_key in _node_keys:
                _attr_name = _node_key.replace('-', '_').upper()
                if _DEBUG.YAMLator:
                    ic(_attr_name)
                # strip the leading underscore
                if _attr_name.startswith('_'):
                    _attr_name = _attr_name[1:]

                if hasattr(self,_attr_name) or set_all:
                    if _is_already_set.get(_attr_name,False):
                        if _DEBUG.CONFIG_ATTRS:
                            _msg = f'{_attr_name} already set'
                            ic(_msg)
                        continue
                    try:
                        if isinstance(getattr(type(self), _attr_name), property):
                            # ignore any uppercase attribute that is a property
                            continue
                    except AttributeError:
                        pass

                    # -----------------------------------------------------------
                    # this can cause recursion, because we override get() to call super().get()
                    # only ever set the deepest value of a given key; get() is dfs
                    # _value = self.get(_node_key)
                    # -----------------------------------------------------------
                    _value = _node.get(_node_key)

                    if _DEBUG.CONFIG_ATTRS:
                        ic(_node_key)
                        ic(_value)

                    if isinstance(_value, str) and is_variable_token(_value):
                        # ignore unsubbed variables
                        continue

                    if isinstance(_value,OrderedDict):
                        _value = Tree(_value)

                    # # TODO: this definition of True needs to be formalized for other transformers, like IfKey
                    # if self.objdb.key_type(_node_key) == 'bool' and isinstance(_value,Tree):
                    #     if any(map(lambda x: x.startswith('))?'), _node.keys())):
                    #         return None
                    #     else:
                    #         # a boolean key with a tree value (that is not an if key node) is True (?)
                    #         return True

                    if isinstance(_value,list):
                        _object_value = list(map(lambda x:self.get_object(_node_key,x),_value))
                    else:
                        _object_value = self.get_object(_node_key, _value)

                    if _DEBUG.CONFIG_ATTRS:
                        ic(_object_value)
                    setattr(self, _attr_name, _object_value)
                    _is_already_set[_attr_name] = True

        # we set objects on demand with a special object getter
        self.visit(post_process=_depth_first)

    def get_config_attrs(self):
        """Retrieves a summary of the instance's configuration attributes.

        This method is an introspection tool that scans the YAMLator instance
        for all public, uppercase attributes, which are typically set by a
        prior call to `set_config_attrs`.

        Returns:
            dict: A dictionary where keys are the uppercase attribute names
                (e.g., 'SERVER_HOST') and values are the string
                representations of the corresponding attribute values.

        Examples:
            >>> yaml_content = "SERVER_HOST: 'localhost'\\nSERVER_PORT: 8080"
            >>> yt = YAMLator(yaml_content)
            >>> yt.set_config_attrs(set_all=True)
            >>> yt.get_config_attrs()
            {'SERVER_HOST': 'localhost', 'SERVER_PORT': '8080'}

        """
        _data = {}
        for _config_datum in list(filter(lambda x:x == x.upper() and not x.startswith('_'),self.__dir__())):
            _data.update({_config_datum:str(getattr(self,_config_datum))})
        return _data

    def check_subs(self):
        _unsubbed = Tree()

        def _assert_not_unsubbed(value,keychain):
            if not isinstance(value,list):
                _values = [value]
            else:
                _values = value
            for _value in _values:
                ic(_value)
                if type(_value) is str:
                    _tokens = ValueTransformer()._tokenize(_value)
                    if any(list(map(lambda x:is_variable_token(x),_tokens))):
                        _unsubbed.get(keychain,value)

        self.visit(value_process=_assert_not_unsubbed)
        return _unsubbed

    def invert(self):
        """Creates an inverted index of the configuration tree.

        Much like a textbook index, this method scans the tree for all variable
        tokens (e.g., `${VAR}` or `))VAR`) and generates a new tree that maps
        each variable to a list of all the locations (keychains) where it is
        used. This is highly useful for dependency analysis and debugging
        complex configurations.

        Returns:
            YAMLator: A new `YAMLator` instance representing the inverted index.
                The keys of this new tree are the variable names found in the
                original tree, and the values are lists of keychain strings
                indicating every location where each variable was used.

        Examples:
            >>> yaml_content = '''
            ... server:
            ...   host: ))host-ip
            ... database:
            ...   url: 'postgres://))db-user@))host-ip/))db-name'
            ... '''
            >>> yt = YAMLator(yaml_content)
            >>> inverted_tree = yt.invert()
            >>> print(inverted_tree)
            ))host-ip:
            - server/host
            - database/url
            ))db-user:
            - database/url
            ))db-name:
            - database/url
        """
        _var_tree = YAMLator()

        def _val(value,keychain):
            if not isinstance(value,str) and not isinstance(value,list):
                return
            if keychain[-1].startswith('_'):
                return
            if not isinstance(value,list):
                value = [value]
            for _value in value:
                _tokens = ValueTransformer()._tokenize(_value)
                for _token in _tokens:
                    if is_variable_token(_token):
                        if _token[2] == '{' and _token[-1] == '}':
                            _token = KEY_OR_KEYCHAIN_OP +  _token[3:-1]
                        try:
                            _tree_values = _var_tree.get(_token)
                        except KeyError:
                            _tree_values = _var_tree.get(_token,[])
                        _tree_values.append('/'.join(keychain))

        self.visit(value_process=_val)
        return _var_tree

    def reduce(self):
        """Builds a dependency graph of the configuration.

        This method acts as a tool for creating a dependency graph, much like a
        "Bill of Materials" for your configuration. For each keychain, it
        determines which variables its value depends on.

        Its primary use case is to enable the detection of circular dependencies
        before running the full, potentially expensive, transformation process.
        Self-referential dependencies (where a key's value refers to itself)
        are ignored.

        Returns:
            YAMLator: A new `YAMLator` instance representing the dependency graph.
                It preserves the keychains from the original tree, but replaces
                their values with a list of the variable tokens they depend on.
                Keychains with no dependencies are omitted from the result.

        Examples:
            >>> yaml_content = '''
            ... db-host: 'db.internal'
            ... db-port: 5432
            ... db-url: 'postgres://user@))db-host:))db-port'
            ... app-port: ))db-port
            ... '''
            >>> yt = YAMLator(yaml_content)
            >>> dependency_graph = yt.reduce()
            >>> print(dependency_graph)
            db-url:
            - '))db-host'
            - '))db-port'
            app-port:
            - '))db-port'
        """
        _reduced_tree = YAMLator()

        def _val(value,keychain):
            if not isinstance(value,str) and not isinstance(value,list):
                return
            if keychain[-1].startswith('_'):
                return
            if not isinstance(value,list):
                value = [value]

            _variables_in_value = []
            for _value in value:
                _tokens = ValueTransformer()._tokenize(_value)
                for _token in _tokens:
                    if is_variable_token(_token):
                        if _token[2] == '{' and _token[-1] == '}':
                            _token = KEY_OR_KEYCHAIN_OP +  _token[3:-1]
                        # not save self reference values
                        if not _token[len(KEY_OR_KEYCHAIN_OP):] == keychain[-1]:
                            _variables_in_value.append(_token)

            if _variables_in_value:
                _reduced_tree.get(keychain,_variables_in_value)

        self.visit(value_process=_val)

        return _reduced_tree
