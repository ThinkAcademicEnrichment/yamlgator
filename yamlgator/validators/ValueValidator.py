from __future__ import annotations

from ..constants import *
from ..tree import *
from .AbstractValidator import  *
from .issues import *

class _DEBUG:
    ValueValidator = True


class ValueValidator(AbstractValidator):
    """
    Validates a tree for issues related to variable substitution, such as
    circular dependencies, and undefined or unused variables, before the
    main transformation process is run.
    """
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

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