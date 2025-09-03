from __future__ import annotations

from ..constants import KEY_OR_KEYCHAIN_OP, ic, KEYCHAIN_LEFT_BOUND, KEYCHAIN_RIGHT_BOUND
from .AbstractValidator import AbstractValidator
from ..transformers import ValueTransformer
from .issues import ValidationIssue, ValidationResult
from ..tree import Tree,TreeVisitRestartException


class _DEBUG:
    ValueValidator = True


class ValueValidator(AbstractValidator):
    """
    Validates a tree for issues related to variable substitution, such as
    circular dependencies, and undefined or unused variables, before the
    main transformation process is run.
    """

    def validate(self, context_tree: AbstractValidator = None) -> list[ValidationResult]:
        """Runs all value-related validation checks.

        Args:
            context_tree (AbstractValidator, optional): An external context tree
                for resolving variables. Defaults to None.

        Returns:
            list[ValidationResult]: A list of all validation issues found.
        """
        issues = []
        issues.extend(self._find_circular_dependencies())
        issues.extend(self._find_undefined_variables(context_tree))
        return issues

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

    def _find_circular_dependencies(self) -> list[ValidationResult]:
        """Detects cyclical dependencies in the variable graph.

        Returns:
            list[ValidationResult]: A list of validation results for any cycles found.
        """
        _reduced_tree = self.reduce()
        _visited = []
        _issues = []

        def _find_cycles(node, keychain):
            keychain_str = ''
            # Parse the variable token to get the keychain string to test
            for var_token in node:
                if var_token.startswith(KEY_OR_KEYCHAIN_OP):
                    if '{' in var_token and '}' in var_token:
                        # Handles cases like ')){a/b/c}'
                        start_index = len(KEY_OR_KEYCHAIN_OP) + 1
                        keychain_str = var_token[start_index:-1]
                    else:
                        # Handles cases like '))a-key'
                        start_index = len(KEY_OR_KEYCHAIN_OP)
                        keychain_str = var_token[start_index:]

                    if keychain_str in _visited:
                        _issues.append(ValidationResult(
                            issue_type=ValidationIssue.CIRCULAR_DEPENDENCY,
                            message=ValidationIssue.CIRCULAR_DEPENDENCY.value.format(path=' -> '.join(_visited))
                        ))
                        while _visited:
                            _visited.pop()
                        continue

                    _visited.append(keychain_str)
                    entry_keychain = keychain_str.split('/')
                    raise TreeVisitRestartException(entry_keychain)

        _reduced_tree.visit(value_process=_find_cycles)

        return _issues

    def _find_undefined_variables(self, context_tree: AbstractValidator = None) -> list[ValidationResult]:
        """Finds variables whose referenced keychains cannot be resolved in the tree.

        This method works by parsing each used variable token (e.g., ')){my/key}')
        to extract its keychain ('my/key'). It then attempts to resolve that
        keychain using `self.get()`. If the keychain cannot be resolved in either
        the current tree or the optional context_tree, it is marked as undefined.

        Args:
            context_tree (AbstractValidator, optional): An external tree to use
                as a secondary source for variable definitions. Defaults to None.

        Returns:
            list[ValidationResult]: A list of issues for any undefined variables.
        """
        issues = []
        used_vars_map = self.invert()

        for var_token in used_vars_map.keys():
            # Parse the variable token to get the keychain string to test
            keychain_str = ''
            if '{' in var_token and '}' in var_token:
                # Handles cases like ')){a/b/c}'
                start_index = len(KEY_OR_KEYCHAIN_OP) + 1
                keychain_str = var_token[start_index:-1]
            else:
                # Handles cases like '))a-key'
                start_index = len(KEY_OR_KEYCHAIN_OP)
                keychain_str = var_token[start_index:]

            # An empty keychain (e.g., from '))/' or ')){/}') refers to the
            # root, which always exists, so we can skip checking it.
            if not keychain_str or keychain_str == '/':
                continue

            # Check if the keychain is defined in self or the context_tree
            is_defined = False
            try:
                # Check the current tree first
                self.get(keychain_str)
                is_defined = True
            except KeyError:
                # If not in the current tree, check the context_tree if it exists
                if context_tree:
                    try:
                        context_tree.get(keychain_str)
                        is_defined = True
                    except KeyError:
                        # Not defined in the context_tree either
                        pass

            # If the keychain was not resolved in any context, it's undefined
            if not is_defined:
                issues.append(ValidationResult(
                    issue_type=ValidationIssue.UNDEFINED_VARIABLE,
                    message=ValidationIssue.UNDEFINED_VARIABLE.value.format(variable=var_token)
                ))

        return issues