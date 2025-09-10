from .constants import *

class _DEBUG:
    VISIT = False
    POP = False
    GET = False
    FIND = False
    FLATTEN = False
    STRINGIFY = False
    OVERLAY = False
    DFS = False
    INDENT = None
    RESET = False
    ENTRY = False


class TreeVisitRestartException(Exception):
    pass


class TreeVisitStopException(Exception):
    pass


class TreeException(Exception):
    pass



class TreeCreationException(TreeException):
    pass


class Tree:
    def __eq__(self, other):
        if self.odict == other.odict:
            return True
        return False

    def __add__(self, other):
        self.overlay(other)
        return self

    def __str__(self):
        #this has to be dump(); other functions depend upon this string rep
        # not the same as self.print() !
        return self.dump()

    def __init__(self,odict_or_tree=None,**kwargs):
        if odict_or_tree is None:
            self.odict = OrderedDict()
            # TODO: what is the point of this?
            #-------------------------------
            if kwargs:
                for _k,_v in kwargs.items():
                    self.get(_k,_v)
            #-------------------------------

        elif isinstance(odict_or_tree,OrderedDict):
            self.odict = odict_or_tree
        elif issubclass(odict_or_tree.__class__,Tree):
            self.odict = odict_or_tree.odict
        elif isinstance(odict_or_tree,str):
            self.odict = self.load(io.StringIO(odict_or_tree)).odict
        elif isinstance(odict_or_tree,dict):
            self.odict = OrderedDict(odict_or_tree)
        else:
            raise TreeCreationException('Cannot create tree')
        if _DEBUG.GET:
            _DEBUG.INDENT = -1

    def is_empty(self):
        if not self.odict:
            return True

    def copy(self):
        """Copies the Tree object.

        Returns:
             Tree: A deepcopy of the Tree object.
        """
        return self.__class__(deepcopy(self.odict))

    def reset(self, *keys_to_preserve):
        """Clears all contents of the tree, with an option to preserve branches.

        The tree is modified in-place.

        Args:
            *keys_to_preserve (str): A variable number of keychain strings.
                If no arguments are provided, the entire tree is emptied.
                If one or more keychains are provided, only those branches
                will remain in the tree.

        Returns:
            None

        Examples:
            >>> tree = Tree({'a': 1, 'b': {'c': 2}})
            >>> tree.reset()
            >>> tree.is_empty()
            True

            >>> tree = Tree({'a': 1, 'b': {'c': 2}, 'd': 3})
            >>> tree.reset('b/')
            >>> print(tree.dump())
            b:
              c: 2
        """
        _old_tree = self.copy()

        if _DEBUG.RESET:
            ic()
            ic(keys_to_preserve)
            ic(_old_tree.print())

        # preserve refs!
        _keys = list(self.odict.keys())
        _keys.reverse()
        for _key in _keys:
            # clean out the current odict but preserve its reference
            self.odict.pop(_key)
            if _DEBUG.RESET:
                print(self.odict)

        for _key_to_preserve in keys_to_preserve:
            try:
                _dfs_keychain,_dfs_value = _old_tree.dfs(_key_to_preserve)
                if isinstance(_dfs_value,Tree) and _dfs_keychain[-1] != '':
                    _dfs_keychain.append('')
                if _DEBUG.RESET:
                    ic(_dfs_keychain)
                    ic(_dfs_value)
                self.get(_dfs_keychain,_old_tree.get(_dfs_keychain))
            except KeyError:
                if _DEBUG.RESET:
                    _msg = f'{_key_to_preserve} not found in state'
                    ic(_msg)
                pass

        if _DEBUG.RESET:
            ic(self.print())

    def visit(self,pre_process=lambda x, y:None, post_process=lambda x, y:None, value_process=lambda x, y:None,reverse=False,entry_keychain=None):
        """Traverses the tree using a visitor pattern.

        This method walks through the entire tree, executing callbacks at
        different stages of the traversal. It provides three distinct callback
        hooks:

        - `pre_process`: Called on a branch node before its children are visited
            (pre-order traversal).
        - `post_process`: Called on a branch node after its children have been
            visited (post-order traversal).
        - `value_process`: Called on a leaf node.

        Args:
            pre_process (callable, optional): A function that accepts a branch
                node (OrderedDict) and its keychain (list[str]). It is
                executed before visiting the node's children. Defaults to a
                no-op.
            post_process (callable, optional): A function with the same
                signature as `pre_process`, but executed after visiting the
                node's children. Defaults to a no-op.
            value_process (callable, optional): A function that accepts a leaf
                value (any type) and its keychain (list[str]). Defaults to a
                no-op.
            reverse (bool, optional): If True, the children of each node are
                visited in reverse order. Defaults to False.
            entry_keychain (typing.Union[str, list[str]], optional): A specific
                keychain (string or list) that defines a starting point for
                processing. The traversal still begins at the root, but the
                callbacks will only be activated for the target node and its
                descendants. Defaults to None.

        Raises:
            TreeVisitRestartException: A callback can raise this exception to
                interrupt and restart the entire visit, optionally providing a
                new entry keychain to begin the new traversal from.
            TreeVisitStopException: A callback can raise this exception to
                gracefully and immediately terminate the entire traversal.

        Examples:
            >>> tree = Tree({'a': {'b': 1}, 'c': 2})
            >>>
            >>> def pre(node, keychain):
            ...     indent = '  ' * len(keychain)
            ...     if keychain:
            ...         print(f"{indent}{keychain[-1]}:")
            ...
            >>> def post(node, keychain):
            ...     pass  # Not needed for this example
            ...
            >>> def value(val, keychain):
            ...     indent = '  ' * (len(keychain) -1)
            ...     print(f"{indent}  {keychain[-1]}: {val}")
            ...
            >>> tree.visit(pre_process=pre, value_process=value)
            a:
              b: 1
            c: 2
        """
        try:
            if not reverse:
                self._visit(self.odict,pre_process,post_process,value_process,None,entry_keychain=entry_keychain)
            else:
                self._reverse_visit(self.odict,pre_process,post_process,value_process,None)
        except TreeVisitRestartException as e:
            if _DEBUG.VISIT or _DEBUG.ENTRY:
                ic(e)
                ic(self.odict)
            if e.args[0] is not None:
                _keychain_or_keychain_str = e.args[0]
                _entry_keychain = copy(_keychain_or_keychain_str) if isinstance(_keychain_or_keychain_str,list) else _keychain_or_keychain_str.split('/')
                if _DEBUG.ENTRY:
                    ic(_entry_keychain)
                self.visit(pre_process, post_process, value_process, reverse,entry_keychain=_entry_keychain)
            else:
                self.visit(pre_process, post_process, value_process, reverse)
        except TreeVisitStopException as e:
            if _DEBUG.VISIT:
                ic(e)
            return

    def _visit(self, node, pre_process=lambda x, y:None, post_process=lambda x, y:None, value_process=lambda x, y:None,keychain=None,entry_keychain=None,process=False):
        keychain = [] if keychain is None else keychain
        entry_keychain = [] if entry_keychain is None else entry_keychain
        if not entry_keychain:
            process = True
        elif not process and keychain[:len(entry_keychain)] == entry_keychain:
            process = True
            if _DEBUG.ENTRY:
                _msg = f"{keychain[:len(entry_keychain)]} == {entry_keychain} "
                ic(_msg)
                ic(process)

        if isinstance(node,OrderedDict):
            if process:
                pre_process(node,copy(keychain))
            for _child_key in node.keys():
                keychain.append(_child_key)
                self._visit(node.get(_child_key), pre_process, post_process, value_process, copy(keychain),entry_keychain,process)
                keychain.pop()
            if process:
                post_process(node,copy(keychain))
        else:
            if process:
                value_process(node,keychain)

    def _reverse_visit(self, node,pre_process=lambda x, y:None, post_process=lambda x, y:None, value_process=lambda x, y:None,keychain=None):
        keychain = [] if keychain is None else keychain
        if isinstance(node,OrderedDict):
            pre_process(node,copy(keychain))
            _node_keys = copy(list(node.keys()))
            _node_keys.reverse()
            for _child_key in _node_keys:
                keychain.append(_child_key)
                self._reverse_visit(node.get(_child_key), pre_process, post_process, value_process, copy(keychain))
                keychain.pop()
            post_process(node,copy(keychain))
        else:
            value_process(node,keychain)

    def keys(self, keychain_or_keychain_str=None):
        """Returns the keys of a node, behaving like dict.keys().

        Args:
            keychain_or_keychain_str (typing.Union[str, list[str]], optional):
                A keychain string or list of strings specifying the target node.
                If omitted, returns the keys of the root node. Defaults to None.

        Returns:
            dict_keys: A view object containing the keys of the specified node.

        Raises:
            KeyError: If the keychain is invalid or points to a leaf node.

        Examples:
            >>> tree = Tree({'a': {'b': 'B_VAL'}, 'c': 'C_VAL'})
            >>> list(tree.keys())
            ['a', 'c']
            >>> list(tree.keys('a/'))
            ['b']
        """
        if keychain_or_keychain_str:
            _keychain = copy(keychain_or_keychain_str) if isinstance(keychain_or_keychain_str,list) else keychain_or_keychain_str.split('/')
            # never do this
            # if not _keychain[-1] == '':
            if _keychain[-1] != '':
                _keychain += ['']
        try:
            return self.odict.keys() if keychain_or_keychain_str is None else self.get(_keychain).keys()
        except AttributeError:
            raise KeyError

    def dfs(self, keychain_or_keychain_str, keychain_or_keychain_str_context=None):
        """Performs a depth-first search (DFS) to locate a node in the tree.

        The search is performed for the first key in the provided keychain. If
        multiple nodes with the same key exist, the search prioritizes and
        returns the one that is nested deepest within the tree structure.

        Args:
            keychain_or_keychain_str (typing.Union[str, list[str]]): The keychain
                to search for.
            keychain_or_keychain_str_context (typing.Union[str, list[str]], optional):
                An optional keychain that defines a starting branch for the search.
                If provided, the search is restricted to descendants of this node.
                Defaults to None.

        Returns:
            tuple[list[str], typing.Any]: A tuple containing the full, absolute
            keychain (as a list of strings) of the found node and the value at
            that node.

        Raises:
            KeyError: If the keychain cannot be found in the tree.
        """
        _keychain = copy(keychain_or_keychain_str) if isinstance(keychain_or_keychain_str,list) \
                                                                else keychain_or_keychain_str.split('/')

        # if DEBUG.DFS:
        #     ic(keychain_or_keychain_str)
        #     ic(keychain_or_keychain_str_context)

        keychain_or_keychain_str_context = [] \
            if keychain_or_keychain_str_context is None else keychain_or_keychain_str_context

        # if DEBUG.DFS:
        #     ic(keychain_or_keychain_str)
        #     ic(keychain_or_keychain_str_context)

        _keychain_context = copy(keychain_or_keychain_str_context) \
            if isinstance(keychain_or_keychain_str_context,list) else keychain_or_keychain_str_context.split('/')

        if _DEBUG.DFS:
            ic(_keychain)
            ic(_keychain_context)

        if not _keychain or (len(_keychain) == 1 and _keychain[0] == ''):
            # if _keychain[0] == '' :
            if _DEBUG.DFS:
                _msg = f'returning /,{self.get(_keychain_context)}'
                ic(_msg)
            return '/',self.get(_keychain_context)

        if _keychain[0] == '':
            _keychain = _keychain[1:]

        key = _keychain[0]

        _all_results = []

        def _dfs(node,keychain):
            if _DEBUG.DFS:
                ic()
                ic(keychain)

            if not keychain[:len(_keychain_context)] == _keychain_context:
                # we are not a child of the given keychain context
                if _DEBUG.DFS:
                    _msg = f'returning None. {keychain} is not a child of {_keychain_context}'
                    ic(_msg)
                return

            _node_keys = copy(list(node.keys()))
            _node_keys.reverse()
            for _node_key in _node_keys:
                if _DEBUG.DFS:
                    ic(key)
                    ic(_node_key)
                if _node_key == key:
                    if _DEBUG.DFS:
                        _msg = f'found {key}'
                        ic(_msg)
                    # all results are absolute!
                    _all_results.append(([''] + keychain+[_node_key],node[_node_key]))

        self.visit(post_process=_dfs)

        if not _all_results:
            if _DEBUG.DFS:
                ic()
                ic(KeyError)
            raise KeyError

        # if DEBUG.DFS:
        #     ic(_all_results)

        _all_results.sort(key=lambda x:len(x[0]),reverse=True)

        if _DEBUG.DFS:
            ic(_all_results)

        if len(_keychain) > 1:
            # we are looking for a particular keychain
            for _result in _all_results:
                try:
                    # test for existence of keychain in search result
                    _value = Tree(_result[1]).get(_keychain[1:])
                    if _DEBUG.DFS:
                        _msg = f'returning {_result[0] + _keychain[1:]},{_value}'
                        ic(_msg)
                    return _result[0] + _keychain[1:],_value
                except KeyError:
                    pass
                if _DEBUG.DFS:
                    ic()
                    ic(KeyError)

                raise KeyError
        else:
            if _DEBUG.DFS:
                _msg = f'returning {_all_results[0]}'
                ic(_msg)
            return _all_results[0]

    def uget(self, keychain_or_keychain_str, value=None):
        """Gets a value from the tree, returning a default if the key does not exist.

        This method acts as a "get with default." It attempts to retrieve the
        value at the specified keychain. If the keychain does not exist, it
        sets the provided `value` at that keychain and then returns it.

        Args:
            keychain_or_keychain_str (typing.Union[str, typing.List[str]]): The
                keychain (path) to retrieve.
            value (typing.Any, optional): The default value to set and return if
                the keychain does not exist. Defaults to None.

        Returns:
            typing.Any: The value at the keychain if it exists, otherwise the
            provided default `value`.
        """
        try:
            #  get the value if it exists, forget the passed in value
            _value = self.get(keychain_or_keychain_str)
        except KeyError:
            #  create a key and set the value
            _value = self.get(keychain_or_keychain_str,value)
        return _value

    def aget(self,keychain_or_keychain_str, value):
        """Appends a value to a list at a specified keychain.

        If the keychain does not exist, a new list is created with `value` as
        its first element. If a value at the keychain exists but is not a
        list, it is converted into a list, and the new `value` is appended.
        If `value` itself is a list, its items are added to the list at the
        keychain.

        Args:
            keychain_or_keychain_str (typing.Union[str, typing.List[str]]): The
                keychain (path) where the value will be appended.
            value (typing.Any): The value or list of values to append.

        Returns:
            list: The modified list at the specified keychain.
        """
        if not keychain_or_keychain_str:
            # does not work at root level
            return
        if not isinstance(value,list):
            value = [value]

        # always trim the root on aget, but we call self.get on not trimmed root
        _keychain = copy(keychain_or_keychain_str) if isinstance(keychain_or_keychain_str, list) \
            else keychain_or_keychain_str.split('/')
        if not _keychain[-1] == '':
            _keychain.append('')
        else:
            keychain_or_keychain_str = keychain_or_keychain_str[:-1]

        try:
            _value = self.get(_keychain)
            if not isinstance(_value,list):
                _value = [_value]
            _value += value
        except KeyError:
            _value = value

        # call get() on the root of the keychain
        self.get(keychain_or_keychain_str,_value)
        # but return the value
        return _value

    def daget(self,keychain_or_keychain_str, value=None):
        """Updates a dictionary at a specified keychain.

        This method performs a dictionary update at the given keychain. If the
        keychain does not exist, a new dictionary is created. If a value
        exists at the keychain, it must be a dictionary, or a `TreeException`
        will be raised.

        Args:
            keychain_or_keychain_str (typing.Union[str, typing.List[str]]): The
                keychain (path) of the dictionary to update.
            value (dict): A dictionary of key-value pairs to update the target
                dictionary with.

        Returns:
            Tree: A `Tree` object representing the updated dictionary.

        Raises:
            TreeException: If the keychain is empty or if the existing value at
                the keychain is not a dictionary.
        """
        if not keychain_or_keychain_str:
            # does not work at root level
            raise TreeException('bad keychain!')
            # return
        assert isinstance(value,dict)
        try:
            _value = self.get(keychain_or_keychain_str)
            if not isinstance(_value, dict):
                # _value = [_value]
                raise TreeException('bad value!')
            _value.update(value)
        except KeyError:
            _value = value  # like a regular get() wth the key just created

        return self.get(keychain_or_keychain_str, _value)

    def get(self, keychain_or_keychain_str, value=None):
        """Gets or sets a value in the tree, with path-aware logic.

        This method serves a dual purpose:
        1.  **Getter (value is None):** Retrieves a node or subtree from the
            tree based on the provided keychain.
        2.  **Upsert Setter (value is not None):** Inserts or updates a value
            at the specified keychain. If the path does not exist, it will be
            created.

        Path Resolution:
        -   **Absolute Paths:** If `keychain_or_keychain_str` starts with a `/`,
            the path is resolved from the root of the tree.
        -   **Relative Paths:** If the path does not start with a `/`, the
            method performs a depth-first search (DFS) to find the first
            node matching the initial key, and then resolves the rest of the
            path from there.

        Trailing Slash Convention (for getters):
        -   **With trailing slash (e.g., 'a/b/'):** Returns the actual node
            at the given path. If the node is a branch, it returns a `Tree`
            object representing the subtree. If it's a leaf, it returns the
            leaf's value.
        -   **Without trailing slash (e.g., 'a/b'):** Returns a `Tree` object
            containing the target node as a value, with the last segment of
            the key as its key. For `x.get('a/b')`, the result is
            `Tree(OrderedDict(b=<value at keychain a/b in Tree x>))`.

        Args:
            keychain_or_keychain_str (typing.Union[str, typing.List[str]]): The keychain
                (path) to the target node. Can be a '/'-separated string or a
                list of strings.
            value (typing.Any, optional): The value to set at the keychain. If None,
                the method acts as a getter. Defaults to None.

        Returns:
            typing.Union['Tree', typing.Any]: When getting, returns a `Tree` object or a
            scalar value depending on the path and the trailing slash
            convention. When setting, it returns the value that was set.

        Raises:
            KeyError: If `value` is `None` and the specified keychain cannot be
                found in the tree.
            TreeException: If an attempt is made to set a scalar value at the
                root of the tree.

        Examples:
            >>> tree = Tree()
            >>> tree.get('/a/b', 'value1')
            >>> print(tree.get('/a/b/'))
            value1
            >>> print(tree.get('/a/b'))
            b:
              value1

            >>> tree.get('/a/c', {'d': 'value2'})
            >>> print(tree.dump())
            a:
              b: value1
              c:
                d: value2
        """
        # it should be passed in as a list to avoid splitting
        _keychain = copy(keychain_or_keychain_str) if isinstance(keychain_or_keychain_str,list) \
                                                                else keychain_or_keychain_str.split('/')
        _absolute_keychain = False
        if _keychain and _keychain[0] == '':
            _absolute_keychain = True
            _keychain = _keychain[1:]
        elif not _keychain:
            _absolute_keychain = True

        if _DEBUG.GET:
            ic()
            ic(keychain_or_keychain_str)
            ic(_absolute_keychain)
            ic(_keychain)
            ic(value)

        _trim_root = False
        # _keychain = [] if _keychain is None else _keychain

        if len(_keychain) > 1 and _keychain[-1] == '':
            # so if _keychain was None or [] we are
            _trim_root = True
            _keychain.pop()
        elif _keychain == ['']:
            _keychain.pop()

        if not _keychain and not isinstance(value,Tree) and value is not None:
            raise TreeException("Cannot set scalars at the root")

        _single_key = False

        if len(_keychain) == 1:
            _single_key = True

        _original_keychain = copy(_keychain)

        _keychain.reverse()

        if _DEBUG.GET:
            ic(_trim_root)
            ic(_original_keychain)
            ic(_keychain)
            if isinstance(value,Tree):
                ic(value.odict)
            else:
                ic(value)

        if _absolute_keychain:
            _ROOT_KEY = 'ROOT'

            _key = _ROOT_KEY
            _current_node_parent = self.odict
            _parents_key = _key # _key_parent[_key] == _key_parent ??? the root node?
            _current_node = _current_node_parent
        else:
            _ROOT_KEY = _keychain[0]
            _key = _ROOT_KEY
            _current_node_parent = None
            _parents_key = _key
            _current_node = _current_node_parent

        if not _keychain:
            if not _absolute_keychain:
                print('please use / to designate the root node')
                _absolute_keychain = True
            # we are manipulating the root node
            if value is not None:
                # it must be a Tree; not allowed to set scalars at root
                if _DEBUG.GET:
                    _msg = f'maninpulating the root node'
                    ic(_msg)
                    ic(_key)
                    ic(_parents_key)

                    ic(value.odict)

                _current_node.update({_k:_v for _k,_v in value.odict.items()})

                _current_node = value.odict


        else:
            if _absolute_keychain:
                while _keychain:
                    _key = _keychain.pop()
                    if _DEBUG.GET:
                        ic(_key)
                        ic(_keychain)
                        ic(_parents_key)
                        # ic(_current_node_parent)
                        # ic(_current_node)
                    try:
                        # _current_node.keys() will throw AttributeError if it is not an OrderedDict
                        if _key in _current_node.keys():
                            if _DEBUG.GET:
                                _msg = f'{_key} in _current_node keys'
                                ic(_msg)
                            # try to get the next element of the keychain
                            _current_node_parent = _current_node
                            _current_node = _current_node[_key]
                            _parents_key = _key
                        else:
                            if _DEBUG.GET:
                                _msg = f'{_key} not in _current_node keys'
                                ic(_msg)
                            raise KeyError
                    except (KeyError,AttributeError) as e:
                        if _DEBUG.GET:
                            ic(e)
                        if isinstance(e,AttributeError) and value:
                            if _DEBUG.GET:
                                _msg = f'setting _current_node_parent[{_parents_key}] = OrderedDict()'
                                ic(_msg)
                                _msg = f'setting _current_node = _current_node_parent[{_parents_key}]'
                                ic(_msg)

                            _current_node_parent[_parents_key] = OrderedDict()
                            _current_node = _current_node_parent[_parents_key]

                            _keychain.append(_key)
                            if _DEBUG.GET:
                                _msg = f'repeating key {_key}'
                                ic(_msg)

                            continue

                        elif isinstance(e,KeyError):
                            if _DEBUG.GET:
                                _msg = f'{_key} not found'
                                ic(_msg)

                            if value is not None:
                                if _DEBUG.GET:
                                    # _msg = f'Setting _current_node[{_key}] to None'
                                    _msg = f'Setting _current_node[{_key}] to OrderedDict()'
                                    ic(_msg)
                                    _msg = f'Setting _current_node_parent to _current_node'
                                    ic(_msg)
                                    _msg = f'Setting _current_node to _current_node[{_key}]'
                                    ic(_msg)

                                _current_node[_key] = OrderedDict()
                                _current_node_parent = _current_node
                                _current_node = _current_node[_key]
                                _parents_key = _key

                            elif value is None:
                                if _DEBUG.GET:
                                    _msg = f' raising KeyError'
                                    ic(_msg)
                                raise KeyError
                        else:
                            # raise e
                            # if we try to apply a key to a string value, it's really a KeyError, not AttributeError
                            raise KeyError

            else:
                _key  = _keychain.pop()

                try:
                    if _DEBUG.GET:
                        _msg = f'dfs looking for {_key}'
                        ic(_msg)
                    _dfs_keychain,_dfs_value = self.dfs(_key)

                    _relative_keychain = copy(_keychain)
                    _relative_keychain.reverse()
                    if _DEBUG.GET:
                        _msg = f'dfs found {_key} at:'
                        ic(_dfs_keychain)
                        # ic(_dfs_value)
                        ic(_relative_keychain)
                    #
                    if _trim_root:
                        _relative_keychain += ['']

                    if _DEBUG.GET:
                        _msg = f'RECURSING'
                        ic(_msg)

                    return self.get(_dfs_keychain+_relative_keychain,value)

                except KeyError:
                    # we could not find a relative root;
                    # assuming it is meant to be at root can be useful
                    if _DEBUG.GET:
                        _msg = f"Assuming {keychain_or_keychain_str} should have been absolute"
                        ic(_msg)
                    return self.get([''] + _original_keychain,value)

        if _DEBUG.GET:
            ic(_parents_key)
            # ic(_current_node_parent)
            # ic(_current_node)

        if value is not None and not isinstance(value,Tree):
            # if isinstance(_current_node,OrderedDict):
            if _DEBUG.GET:
                _msg = f'Setting _parent_current_node[{_key}] to {value}'
                ic(_msg)
                _msg = f'Setting _current_node = _parent_current_node[{_key}]'
                ic(_msg)
            _current_node_parent[_key] = value
            _current_node = _current_node_parent[_key]
            # else:
            #     if DEBUG.GET:
            #         _msg = f'Setting _parent_current_node[{_key}] to {value}'
            #         ic(_msg)
            #         _msg = f'Setting _current_node = _parent_current_node[{_key}]'
            #         ic(_msg)
            #     _current_node_parent[_key] = value
            #     _current_node = _current_node_parent[_key]
        elif value is not None and isinstance(value,Tree):
            if isinstance(_current_node,OrderedDict):
                if _DEBUG.GET:
                    _msg = f'updating _current_node with {list(value.keys())} from  value'
                    ic(_msg)
                _current_node.update({_k:_v for _k,_v in value.odict.items()})
            else:
                if _DEBUG.GET:
                    _msg = f'setting _current_node to OrderedDict()'
                    ic(_msg)
                    _msg = f'updating _current_node with {list(value.keys())} from value'
                    ic(_msg)
                    _msg = f'setting _current_node_parent[_key] = _current_node'
                _current_node = OrderedDict()
                _current_node.update({_k:_v for _k,_v in value.odict.items()})
                _current_node_parent[_key] = _current_node

        if not isinstance(_current_node,OrderedDict):
            if isinstance(_current_node,list) and not _trim_root:
                _ret = Tree(OrderedDict({_key: _current_node}))
            else:
                _ret = _current_node
        else:
            if not _trim_root:
                _ret = Tree(OrderedDict({_key:_current_node}) if _key != _ROOT_KEY else Tree(_current_node))
            else:
                _ret = Tree(_current_node)

        return _ret

    def pop(self, keychain_or_keychain_str, delete_key=True, keychain_context=None):
        """Removes and returns a node and its descendants from the tree.

        This method locates a node by its keychain and removes it. For relative
        paths (those not starting with '/'), it performs a depth-first search (DFS)
        to find the target node.

        Args:
            keychain_or_keychain_str (typing.Union[str, list[str]]): The path to the
                node to be removed. Can be a '/'-separated string or a list of
                strings.
            delete_key (bool, optional): Determines the removal behavior.
                - If `True` (default), the target key and all its children are
                  completely removed from the tree.
                - If `False`, the children are removed, but the key itself is
                  preserved with an empty string value.
            keychain_context (typing.Union[str, list[str], None], optional): An
                optional starting path that provides context for a relative
                `keychain` search. Defaults to None.

        Returns:
            typing.Union['Tree', typing.Any, None]: The removed value. This can be a
            scalar or a `Tree` object representing the removed branch. If the
            specified key is not found, the method does nothing and returns `None`.
        """

        _keychain = copy(keychain_or_keychain_str) if isinstance(keychain_or_keychain_str,list) \
                                                    else keychain_or_keychain_str.split('/')

        if _DEBUG.POP:
            ic()
            ic(self)
            ic(self.odict)
            ic(_keychain)
            ic(delete_key)
            ic(keychain_context)

        _trim_root = False
        if _keychain[-1] == '':
            _trim_root = True
            _keychain.pop()

        try:
            _absolute_keychain,_= self.dfs(_keychain,keychain_context)
            if _DEBUG.POP:
                ic(_absolute_keychain)
        except KeyError:
            #???? silently fail???
            return

        _value = self.get(keychain_or_keychain_str)
        if _DEBUG.POP:
            ic(_value)

        _new_tree = Tree()
        if not delete_key:
            _new_tree.get(keychain_or_keychain_str,'')


        for __keychain,__value in self.flatten():
            if _DEBUG.POP:
                ic(__keychain)

            if __keychain == _absolute_keychain:
                # ic(__keychain)
                # ic(_absolute_keychain)
                if not delete_key:
                    if _DEBUG.POP:
                        _msg = f'leaving keychain {keychain_or_keychain_str}'
                        ic(_msg)
                    _new_tree.get(keychain_or_keychain_str,'')
                else:
                    if _DEBUG.POP:
                        _msg = f'deleting keychain {keychain_or_keychain_str}'
                        ic(_msg)
                continue

            elif __keychain[:len(_absolute_keychain)] == _absolute_keychain:
                if not delete_key:
                    if _DEBUG.POP:
                        _msg = f'leaving keychain {keychain_or_keychain_str}'
                        ic(_msg)
                    _new_tree.get(keychain_or_keychain_str,'')
                continue
            else:
                _new_tree.get(__keychain,__value)

        # remove odict contents without breaking refs
        self.reset()
        self.overlay(_new_tree)

        if _DEBUG.POP:
            ic(self)
            ic(self.odict)
            if isinstance(_value,Tree):
                ic(_value.odict)
            else:
                ic(_value)
        return _value

    def flatten(self, relative: bool = False) -> list[tuple[list[str], typing.Any]]:
        """Creates a flat representation of the tree as a list of keychain-value pairs.

        Args:
            relative (bool, optional): Determines the path format for the keychains.
                - If `False` (default), keychains are absolute paths starting with an
                  empty string to represent the root (e.g., ['', 'a', 'b']).
                - If `True`, keychains are relative paths and do not start with an
                  empty string (e.g., ['a', 'b']). Defaults to False.

        Returns:
            list[tuple[list[str], typing.Any]]: A list of tuples, where each tuple
            contains a keychain (as a list of strings) and its corresponding value.

        Examples:
            >>> tree = Tree({'a': {'b': 'B_VAL'}, 'c': 'C_VAL'})
            >>> tree.flatten()
            [(['', 'a', 'b'], 'B_VAL'), (['', 'c'], 'C_VAL')]
            >>> tree.flatten(relative=True)
            [(['a', 'b'], 'B_VAL'), (['c'], 'C_VAL')]
        """
        if _DEBUG.FLATTEN:
            ic()
        _data = []
        def _val(node,keychain):
            if not relative:
                _data.append(([''] + keychain,node))
            else:
                _data.append((keychain,node))

        self.visit(value_process=_val)
        return _data

    def oget(self,keychain_or_keychain_str,value):
        """So we can use overlay like get in TreeState"""
        if isinstance(value,Tree):
            return self.overlay(value,keychain_or_keychain_str)
        return self.get(keychain_or_keychain_str,value)

    def overlay(self, tree: 'Tree', keychain_or_keychain_str: typing.Union[str, list[str]] = []) -> 'Tree':
        """Merges the contents of another Tree into the current one.

        This method overlays the key-value pairs from the source `tree` onto the
        current tree in-place. If a key already exists in the current tree, its
        value will be overwritten with the value from the source tree.

        Args:
            tree (Tree): The source `Tree` object to overlay.
            keychain_or_keychain_str (typing.Union[str, list[str]], optional): A base
                keychain to apply the overlay. If provided, the source tree will be
                merged at this location. If omitted, the merge happens at the root.
                Defaults to [].

        Returns:
            Tree: The modified `Tree` instance (`self`), allowing for method chaining.

        Examples:
            >>> base_tree = Tree({'a': 1, 'b': {'c': 2}})
            >>> overlay_tree = Tree({'b': {'d': 3}, 'e': 4})
            >>> base_tree.overlay(overlay_tree)
            >>> print(base_tree.dump())
            a: 1
            b:
              d: 3
            e: 4

            >>> target_tree = Tree({'app': {'config': {'version': '1.0'}}})
            >>> new_settings = Tree({'debug': True, 'version': '1.1'})
            >>> target_tree.overlay(new_settings, 'app/config')
            >>> print(target_tree.dump())
            app:
              config:
                debug: true
                version: '1.1'
        """
        _keychain = copy(keychain_or_keychain_str) if isinstance(keychain_or_keychain_str,list) \
                                                    else keychain_or_keychain_str.split('/')

        _relative = False
        if keychain_or_keychain_str:
            _relative = True

        for __keychain,__value in tree.flatten(_relative):
            if _DEBUG.OVERLAY:
                _msg = f"setting {'/'.join(_keychain + __keychain)} to {__value}"
                ic(_msg)
                ic(type(__value))

            self.get(_keychain + __keychain,__value)
        return self

    def print(self):
        """Construct a printable string representation of the tree.

        Returns:
            String: A printable indented string representing the tree
        """

        TAB='  '
        _n = 0
        _output = []
        def _pre(node,keychain):
            if not keychain: return
            nonlocal _n,TAB,_output
            _output.append(_n*TAB+keychain[-1]+':')
            _n += 1

        def _post(node,keychain):
            if not keychain: return
            nonlocal _n,TAB
            _n -= 1

        def _value(value, keychain):
            nonlocal _n,TAB
            _output.append(_n*TAB+keychain[-1]+':')

            if value is None: return
            if keychain[-1][0] == '_':
                # a hidden value
                _output.append((_n+1)*TAB+'...')
                return
            if isinstance(value, list):
                # no multiline values in lists
                for _value in value:
                    _output.append((_n+1)*TAB+str(_value))
            else:
                # possible multiline string print
                _output.append((_n+1)*TAB+str(value).replace('\n', '\n' + (_n + 1) * TAB))

        self.visit(_pre, _post, _value)
        return '\n'.join(_output)

    def stringify(self):
        """Ensure the leaf values in the tree are strings.

        Returns:
            String: A Tree object with all leaf values guaranteed to be stings.
        """
        if _DEBUG.STRINGIFY:
            ic()
        _data_tree = Tree()
        def _stringify(value,keychain):
            if _DEBUG.STRINGIFY:
                ic(keychain)
                ic(value)
            if isinstance(value,list):
                _data_tree.get([''] + keychain, list(map(str, value.decode() if isinstance(value,bytes) else value)))
            else:
                _data_tree.get([''] + keychain, str(value.decode() if isinstance(value,bytes) else value))

        self.visit(value_process=_stringify)
        return _data_tree

    def dump(self,stream=None,Dumper=yaml.Dumper,**kwds):
        """Serializes the Tree object into a YAML formatted string.

        This method preserves the order of keys from the original tree in the
        YAML output. It also ensures that all values within the tree are
        converted to their string representation before being serialized.

        Args:
            stream (typing.IO, optional): A file-like object (e.g., a file
                handle opened in write mode). If provided, the YAML output
                will be written to this stream. Defaults to None.
            Dumper (yaml.Dumper): The yaml.Dumper class to be used for the
                serialization process.
            **kwds: Additional keyword arguments that will be passed directly
                to the underlying yaml.dump function.

        Returns:
            str or None: If `stream` is None (the default), the method
            returns the YAML output as a string. If `stream` is provided,
            the method writes to the stream and returns None.
        """
        _data_tree = self.stringify()

        class OrderedDumper(Dumper):
            pass

        def _dict_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                data.items())

        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        return yaml.dump(_data_tree.odict, stream, OrderedDumper, **kwds)

    @classmethod
    def _load(cls, stream):
        class OrderedLoader(yaml.BaseLoader):
            pass
        def construct_mapping(loader, node):
            return OrderedDict(loader.construct_pairs(node))

        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_mapping)
        return yaml.load(stream,OrderedLoader)

    @classmethod
    def load(cls,stream):
        """Constructs a new Tree instance from a YAML source.

        This factory @classmethod parses a YAML source, preserving the order of
        keys from the input.

        Args:
            stream (typing.Union[typing.IO, str]): The source of the YAML data.
                This can be a file-like object (e.g., from an open file) or a
                string containing YAML markup.

        Returns:
            Tree: A new Tree instance populated with the data from the stream.
        """
        return cls(Tree._load(stream))
