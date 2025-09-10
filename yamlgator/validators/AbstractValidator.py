from __future__ import annotations
from ..tree import Tree

from ..constants import KEYCHAIN_LEFT_BOUND, KEYCHAIN_RIGHT_BOUND
from ..transformers import ValueTransformer

class AbstractValidator(Tree):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
    def invert(self):
        """Creates an inverted index of the configuration tree.

        Much like a textbook index, this method scans the tree for all variable
        tokens (e.g., `${VAR}` or `))VAR`) and generates a new tree that maps
        each variable to a list of all the locations (keychains) where it is
        used. This is highly useful for dependency analysis and debugging
        complex configurations.

        Returns:
            AbstractValidator: A new `AbstractValidator` instance representing the inverted index.
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
            >>> yt = YAMLator(yaml_content) # Assuming YAMLator inherits from AbstractValidator
            >>> inverted_tree = yt.invert()
            >>> print(inverted_tree.pretty())
            ))host-ip:
            - server/host
            - database/url
            ))db-user:
            - database/url
            ))db-name:
            - database/url
        """
        _var_tree = self.__class__() # Use cls() for generic instantiation
        def _val(value, keychain):
            if not isinstance(value, str) and not isinstance(value, list):
                return
            if keychain and keychain[-1].startswith('_'):
                return
            if not isinstance(value, list):
                value = [value]
            for _value in value:
                _tokens = ValueTransformer()._tokenize(_value)
                for _token in _tokens:
                    _token,_keychain = self._remove_data_index(_token)
                    # _keychain == None means _token looks like a variable but is not a value type variable
                    if not _keychain: continue
                    # we cannot use .get() here because it will parse )){a/b} like a keychain string!
                    _tree_values = _var_tree.odict.get(_token, [])
                    _tree_values.append('/'.join(keychain))
                    _var_tree.odict[_token] = _tree_values

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
            AbstractValidator: A new `AbstractValidator` instance representing the dependency graph.
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
            >>> yt = YAMLator(yaml_content) # Assuming YAMLator inherits from AbstractValidator
            >>> dependency_graph = yt.reduce()
            >>> print(dependency_graph.pretty())
            db-url:
            - '))db-host'
            - '))db-port'
            app-port:
            - '))db-port'
            <BLANKLINE>
        """
        _reduced_tree = self.__class__() # Use cls() for generic instantiation
        def _val(value, keychain):
            if not isinstance(value, str) and not isinstance(value, list):
                return
            if keychain and keychain[-1].startswith('_'):
                return
            if not isinstance(value, list):
                value = [value]

            _variables_in_value = []
            for _value in value:
                _tokens = ValueTransformer()._tokenize(_value)
                for _token in _tokens:
                    # this is bad: we want to parse ))a//b ( ))a/, /b )
                    if _token[-1] == '/':
                        _token = _token[:-1]
                    _token,_keychain = self._remove_data_index(_token)
                    # _keychain == None means _token looks like a variable but is not a value type variable
                    if not _keychain:
                        continue
                    if not _keychain == keychain[-1]:
                        _variables_in_value.append(_token)

            if _variables_in_value:
                _reduced_tree.get(keychain, _variables_in_value)

        self.visit(value_process=_val)

        return _reduced_tree

    def _remove_data_index(self,token):
        _token = token
        _keychain = None
        # there are variables like )){@[-1]/c} that look like variables but do not tokenize
        _m = ValueTransformer()._extract(token)
        if _m:
            _keychain, _data_index = _m.groups()
            if '/' in _keychain:
                _token =  KEYCHAIN_LEFT_BOUND + _keychain + KEYCHAIN_RIGHT_BOUND
                _keychain = _keychain.split('/')[-1]
            else:
                _token = _keychain
            _token = '))' + _token
        return _token,_keychain
