from tests import *

_od = OrderedDict
_test_odict_0 = OrderedDict(
        a='A',
        b=OrderedDict(
            c='BC',
            d=OrderedDict(
                e='BDE',
                f='BDF',
            ),
            g='BG',
            h=OrderedDict(
                i='BHI',
                j='BHJ',
            ),
        ),
    )


class TestTree(unittest.TestCase):
    tests_dir = pathlib.Path(__file__).absolute().parent

    def _tree_factory(self,odict=None):
        odict = OrderedDict() if odict is None else odict
        return Tree(deepcopy(odict))

    def test_tree_init_and_eq(self):
        _test_odict = OrderedDict(
            a='A',
            b=OrderedDict(
                a='BA',
                b='BB'
            )
        )

        _t = self._tree_factory(_test_odict)
        self.assertIsInstance(_t,Tree)

        _t_copy = _t.copy()
        self.assertIsInstance(_t_copy,Tree)

        self.assertEqual(_t,_t_copy)
        self.assertTrue(_t == _t_copy)

        _t = self._tree_factory(_test_odict)
        self.assertEqual(_t,Tree(str(_t)))

    @debug_on(ZeroDivisionError)
    def test_load(self):
        _yaml_path = self.tests_dir.joinpath('load.yaml')
        with _yaml_path.open('r') as f:
            _test = self._tree_factory(Tree._load(f))

        _result = Tree(
            OrderedDict(
                a_key='A_VALUE',
                b_key='B_VALUE',
                c_key=OrderedDict(
                    d_key='C_D_VALUE',
                    e_key='C_E_VALUE',
                    f_key=OrderedDict(
                        g_key='C_F_G_VALUE'
                    )
                ),
                h_value='H_VALUE'
            )
        )

        self.assertEqual(_test,_result)

    def test_all(self):
        pass

    @debug_on(Exception)
    def test_get(self):

        _test_odict_1 = OrderedDict(
            a='A',
            b=OrderedDict(
                c='BC',
                d=OrderedDict(
                    e='BDE',
                    f='BDF'
                )
            )
        )


        # test pure get() with no value argument
        _t1 = self._tree_factory(_test_odict_1)

        self.assertEqual(_t1,_t1.get([])) # the unamed 'root' node of the tree
        self.assertEqual(_t1,_t1.get('')) # the unamed 'root' node of the tree

        self.assertEqual('A',_t1.get('a'))
        self.assertEqual('A',_t1.get('a/'))

        self.assertEqual(OrderedDict(b=_test_odict_1['b']),_t1.get('b').odict)
        self.assertEqual(self._tree_factory(OrderedDict(b=_test_odict_1['b'])),_t1.get('b'))

        self.assertEqual(_test_odict_1['b'],_t1.get('b/').odict)
        self.assertEqual(self._tree_factory(_test_odict_1['b']),_t1.get('b/'))

        self.assertEqual(OrderedDict(d=_test_odict_1['b']['d']),_t1.get('b/d').odict)
        self.assertEqual(self._tree_factory(OrderedDict(d=_test_odict_1['b']['d'])),_t1.get('b/d'))

        self.assertEqual(_test_odict_1['b']['d'],_t1.get('b/d/').odict)
        self.assertEqual(self._tree_factory(_test_odict_1['b']['d']),_t1.get('b/d/'))

        self.assertEqual('BDE',_t1.get('b/d/e'))
        self.assertEqual('BDE',_t1.get('b/d/e/'))

        self.assertEqual('BDF',_t1.get('b/d/f'))
        self.assertEqual('BDF',_t1.get('b/d/f/'))

        self.assertEqual('BC',_t1.get('b/c'))
        self.assertEqual('BC',_t1.get('b/c/'))

        # relative roots now work!
        # self.assertRaises(KeyError,_t1.get,'c/a')
        # self.assertRaises(KeyError,_t1.get,'c/a/')


        # now test get()s that update the tree

        #update a string
        _t1 = self._tree_factory(_test_odict_1)
        self.assertEqual('AA',_t1.get('a','AA'))
        self.assertEqual('AA',_t1.get('a'))
        self.assertEqual('AA',_t1.get('a/'))

        # insert a tree, updating a string value
        _insert_odict = OrderedDict(
            b='B',
            c='C'
        )

        _t1 = self._tree_factory(_test_odict_1)
        _tInsert = self._tree_factory(_insert_odict)


        _t1 = Tree()
        _t1.get('/a','A')
        _t1.get('/a/b','AB')
        self.assertEqual(_t1.odict,OrderedDict(a=OrderedDict(b='AB')))


    def _keychain_orders(self,tree,reverse=False):
        _data = {}

        _keychains  = []
        def _process(node,keychain):
            _keychains.append('/'.join(keychain))

        if not reverse:
            tree.visit(pre_process=_process)
            _data.update({'pre':_keychains})

            _keychains = []
            tree.visit(post_process=_process)
            _data.update({'post':_keychains})

            _keychains = []
            tree.visit(value_process=_process)
            _data.update({'value':_keychains})
        else:
            tree.visit(pre_process=_process,reverse=True)
            _data.update({'pre':_keychains})

            _keychains = []
            tree.visit(post_process=_process,reverse=True)
            _data.update({'post':_keychains})

            _keychains = []
            tree.visit(value_process=_process,reverse=True)
            _data.update({'value':_keychains})
        return _data

    def test_visit_1(self):
        _test_odict = OrderedDict(
            a='A',
            b='B',
            c='C',
        )

        _keychain_orders = self._keychain_orders(self._tree_factory(_test_odict))
        self.assertEqual({'pre': [''], 'post': [''], 'value': ['a', 'b', 'c']},_keychain_orders)
        _reverse_keychain_orders = self._keychain_orders(self._tree_factory(_test_odict),reverse=True)
        self.assertEqual({'pre': [''], 'post': [''], 'value': ['c', 'b', 'a']},_reverse_keychain_orders)

    @debug_on(ZeroDivisionError)
    def test_visit_2(self):
        _test_odict = OrderedDict(
            a=OrderedDict(
                a='AA',
                b='BA',
                c=OrderedDict(
                    a='ACA',
                    b='ACB',
                ),
                d=OrderedDict(
                    a='ADA',
                    b='ADB',
                )
            ),
            b=OrderedDict(
                a='BA'
            ),
        )

        _keychain_orders = self._keychain_orders(self._tree_factory(_test_odict))
        self.assertEqual(
            {'pre': ['', 'a', 'a/c', 'a/d', 'b'], 'post': ['a/c', 'a/d', 'a', 'b', ''], 'value': ['a/a', 'a/b', 'a/c/a', 'a/c/b', 'a/d/a', 'a/d/b', 'b/a']},
            _keychain_orders)

        _reverse_keychain_orders = self._keychain_orders(self._tree_factory(_test_odict),reverse=True)
        self.assertEqual(
            {'pre': ['', 'b', 'a', 'a/d', 'a/c'], 'post': ['b', 'a/d', 'a/c', 'a', ''], 'value': ['b/a', 'a/d/b', 'a/d/a', 'a/c/b', 'a/c/a', 'a/b', 'a/a']},
            _reverse_keychain_orders
        )

    def test_visit_3(self):
        _test_odict = OrderedDict(
            a=OrderedDict(
                a='AA'
            ),
            b=OrderedDict(
                a='BA'
            ),
        )

        _keychain_orders = self._keychain_orders(self._tree_factory(_test_odict))
        self.assertEqual(
            {'pre': ['', 'a', 'b'], 'post': ['a', 'b', ''], 'value': ['a/a', 'b/a']},
            _keychain_orders
        )

        _reverse_keychain_orders = self._keychain_orders(self._tree_factory(_test_odict),reverse=True)
        self.assertEqual(
            {'pre': ['', 'b', 'a'], 'post': ['b', 'a', ''], 'value': ['b/a', 'a/a']},
            _reverse_keychain_orders
        )

    def test_keys(self):
        _test_odict = OrderedDict(
            a='A',
            b=OrderedDict(
                c='C',
                d=OrderedDict(
                    e='E',
                    f='F'
                )
            )
        )

        _t = self._tree_factory(_test_odict)

        self.assertEqual(list(_t.get('b').keys()),['b'])
        self.assertEqual(list(_t.get('b/').keys()),['c','d'])
        self.assertEqual(list(_t.get('b/d').keys()),['d'])
        self.assertEqual(list(_t.get('b/d/').keys()),['e','f'])

        self.assertEqual(list(_t.keys()),['a','b'])
        self.assertEqual(list(_t.keys('b')),['c','d'])
        self.assertEqual(list(_t.keys('b/')),['c','d'])
        self.assertEqual(list(_t.keys('b/d/')),['e','f'])
        self.assertEqual(list(_t.keys('b/d')),['e','f'])

    @debug_on(Exception)
    def test_pop(self):

        _test_odict = OrderedDict(
            a='A',
            b=OrderedDict(
                c='C',
                d=OrderedDict(
                    e='E',
                    f='F'
                )
            )
        )

        _t2 = self._tree_factory(_test_odict)
        self.assertEqual('A',_t2.pop('a'))
        self.assertEqual(OrderedDict(
            b=OrderedDict(
                c='C',
                d=OrderedDict(
                    e='E',
                    f='F'
                )
            )
        ),_t2.get('').odict)

        _t2 = self._tree_factory(_test_odict)
        self.assertEqual('A',_t2.pop('a/'))
        self.assertEqual(OrderedDict(
            # a='',
            b=OrderedDict(
                c='C',
                d=OrderedDict(
                    e='E',
                    f='F'
                )
            )
        ),_t2.get('').odict)

        _t2 = self._tree_factory(_test_odict)
        self.assertEqual(_test_odict.get('b'),_t2.pop('b/').odict)

        _t2 = self._tree_factory(_test_odict)
        self.assertEqual(OrderedDict(b=_test_odict.get('b')),_t2.pop('b').odict)
        _t2 = self._tree_factory(_test_odict)
        self.assertEqual(OrderedDict(d=_test_odict.get('b').get('d')),_t2.pop('b/d').odict)
        _t2 = self._tree_factory(_test_odict)
        self.assertEqual(_test_odict.get('b').get('d'),_t2.pop('b/d/').odict)
        _t2 = self._tree_factory(_test_odict)
        self.assertEqual(_test_odict.get('b').get('d').get('e'),_t2.pop('b/d/e'))
        _t2 = self._tree_factory(_test_odict)
        self.assertEqual(_test_odict.get('b').get('d').get('e'),_t2.pop('b/d/e/'))

        # pop by a single unique key
        _t3 = self._tree_factory(_test_odict)
        self.assertEqual(_t3.pop('d').odict,OrderedDict(d=OrderedDict(e='E',f='F')))
        self.assertEqual(_t3.odict,OrderedDict(a='A',b=OrderedDict(c='C')))

        _test_keyvars_odict = OrderedDict({
            'a':'A',
            'b':'B',
            '))(key-a)-is-a-key':OrderedDict({
                'c':'C',
                'd':OrderedDict({
                    'e':'E',
                    'f':'F'
                }),
            }),
        })

        _t5 = self._tree_factory(_test_keyvars_odict)
        self.assertEqual(
            OrderedDict({'))(key-a)-is-a-key':_test_keyvars_odict.get('))(key-a)-is-a-key')}),
            _t5.pop('))(key-a)-is-a-key').odict)

        _test_dfs_odict = OrderedDict(
            a='A',
            b='B',
            c=OrderedDict(
                b='CB',
                d='CD'
            )
        )

        _t6 = self._tree_factory(_test_dfs_odict)
        _val = _t6.pop('b')
        self.assertEqual(_val,'CB')
        self.assertEqual(_t6.odict,OrderedDict(
            a='A',
            b='B',
            c=OrderedDict(
                d='CD'
            )
        ))

        _test_config_odict = OrderedDict(
            config=OrderedDict(
                is_updated_cleaned=OrderedDict(
                    prompt='Emerge @world on your host (highly recommended)?',
                    default='y',
                    confirm_yes=OrderedDict(
                        emerge_world='',
                    ),
                    confirm_no='',
                ),
            ),
        )

        _t7 = self._tree_factory(_test_config_odict)

        _subtree = _t7.get('is_updated_cleaned/')
        self.assertEqual(_test_config_odict.get('config').get('is_updated_cleaned'),_subtree.odict)
        _confirm_yes = _subtree.pop('confirm_yes')


# class TestRelativeRoot(unittest.TestCase):
#     def _tree_factory(self,odict=None):
#         odict = OrderedDict() if odict is None else odict
#         return Tree(deepcopy(odict))

    @debug_on(Exception)
    def test_get_relative_root(self):

        _test_odict = OrderedDict(
            a='A',
            b=OrderedDict(
                c='C',
                d=OrderedDict(
                    e='E',
                    f='F'
                )
            )
        )

        _t = self._tree_factory(_test_odict)
        self.assertEqual(_t.get('c'),'C')
        self.assertEqual(_t.get('a'),'A')
        self.assertEqual(_t.get('b'),self._tree_factory(OrderedDict(b=OrderedDict(c='C',d=OrderedDict(e='E',f='F')))))
        self.assertEqual(_t.get('b/c'),'C')
        self.assertEqual(_t.get('b/d'),self._tree_factory(OrderedDict(d=OrderedDict(e='E',f='F'))))

        self.assertEqual(_t.get('d'),self._tree_factory(OrderedDict(d=OrderedDict(e='E',f='F'))))
        self.assertEqual(_t.get('d/'),self._tree_factory(OrderedDict(e='E',f='F')))
        self.assertEqual(_t.get('d/e/'),'E')
        self.assertEqual(_t.get('d/e'),'E')

    @debug_on(AssertionError)
    def test_get_value_relative_root(self):

        _test_odict = OrderedDict(
            a='A',
            b=OrderedDict(
                c='C',
                d=OrderedDict(
                    e='E',
                    f='F'
                )
            )
        )

        _t = self._tree_factory(_test_odict)
        #
        _t.get('d/e','EE')
        self.assertEqual(_t.get('d'),self._tree_factory(OrderedDict(d=OrderedDict(e='EE',f='F'))))
        self.assertEqual(_t.get('d/e/'),'EE')
        self.assertEqual(_t.get('e'),'EE')
        _t.get('d/f','FF')
        self.assertEqual(_t.get('d'),self._tree_factory(OrderedDict(d=OrderedDict(e='EE',f='FF'))))
        self.assertEqual(_t.get('d/f/'),'FF')
        self.assertEqual(_t.get('f'),'FF')

        self.assertEqual(_t.get('d/'),self._tree_factory(OrderedDict(e='EE',f='FF')))

    @debug_on(Exception)
    def test_random_things(self):
        _test_odict_1 = OrderedDict(
            a='A',
            b=OrderedDict(
                c='BC',
                d=OrderedDict(
                    e='BDE',
                    f='BDF'
                )
            )
        )

        _insert_odict = OrderedDict(
            g='G',
            h='H'
        )

        _t1 = self._tree_factory(_test_odict_1)
        _tInsert = self._tree_factory(_insert_odict)


        # TODO: Document this get behaviour!!! t.get('a',value) != t.get('a/',value)
        _tGet = _t1.get('a',_tInsert)
        self.assertEqual(_tGet,self._tree_factory(OrderedDict(a=_insert_odict)))
        _tGet = _t1.get('a/',_tInsert)
        self.assertEqual(_tGet,_tInsert)

        _t1 = self._tree_factory(_test_odict_1)
        _tInsert = self._tree_factory(_insert_odict)

        # raise AssertionError

        _tGet = _t1.get('d',_tInsert)
        _result_subodict = OrderedDict(e='BDE',f='BDF',g='G',h='H')
        self.assertEqual(_tGet,self._tree_factory(OrderedDict(d=_result_subodict)))
        _tGet = _t1.get('d/',_tInsert)
        self.assertEqual(_tGet,self._tree_factory(_result_subodict))

        # self.assertEqual(_tmerged.get('a/'),_tInsert)
        # self.assertEqual(_tmerged.get('a'),self._tree_factory(OrderedDict(a=_insert_odict)))
        # self.assertEqual(_tInsert,_t1.get('c/a/'))
        # broken or wrong by dfs rules
        self.assertEqual(self._tree_factory(OrderedDict(a=_insert_odict)),_t1.get('a',_tInsert))
        self.assertEqual(self._tree_factory(OrderedDict(a=_insert_odict)),_t1.get('a'))
        self.assertEqual(self._tree_factory(_insert_odict),_t1.get('a/'))

        # update a string two levels in
        _t1 = self._tree_factory(_test_odict_1)
        self.assertEqual('G',_t1.get('c/a','G'))
        self.assertEqual('G',_t1.get('c/a'))
        self.assertEqual('G',_t1.get('c/a/'))

        # update a string with a tree two levels in two different way:
        _t1 = self._tree_factory(_test_odict_1)
        _tInsert = self._tree_factory(_insert_odict)


        # update at c/a with a subtree
        _t1 = self._tree_factory(_test_odict_1)
        self.assertEqual(self._tree_factory(OrderedDict(a=_insert_odict)),_t1.get('c/a',_tInsert))

        # broken
        #self.assertEqual(self._tree_factory(OrderedDict(a=_insert_odict)),_t1.get('c/a'))
        #self.assertEqual(_t2,_t1.get('c/a/'))

        # create a new subtree at the root level
        _t1 = self._tree_factory(_test_odict_1)
        self.assertEqual('H',_t1.get('c/b/a','H'))

        # broken
        #self.assertEqual('H',_t1.get('c/b/a'))
        #self.assertEqual('H',_t1.get('c/b/a/'))

        _updated_test_odict = deepcopy(_test_odict_1)
        _updated_test_odict['c'] = OrderedDict(b=OrderedDict(a='H'))

        # broken
        # self.assertEqual(self._tree_factory(_updated_test_odict),_t1)

        # append a key to an existing subtree
        _t1 = self._tree_factory(_test_odict_1)

        self.assertEqual('BE',_t1.get('b/e','BE'))

        _updated_test_odict = deepcopy(_test_odict_1)
        _updated_test_odict['b']['e'] = 'BE'

        self.assertEqual(self._tree_factory(_updated_test_odict),_t1)

        # now add another to same tree

        # locate a key via depth first search
        _t1 = self._tree_factory(_test_odict_1)
        # add a ducplicate key at a deeper level
        self.assertEqual('BDC',_t1.get('c','BDC'))
        self.assertEqual('BDC',_t1.get('c'))
        self.assertEqual('BDC',_t1.get('c/'))

        _test_odict_2 = OrderedDict(
            a='A',
            b=OrderedDict(
                c='BC',
                d=OrderedDict(
                    e='BDE',
                    f='BDF',
                    a='BDA',
                )
            )
        )

        _tInsert = self._tree_factory(_test_odict_2)
        self.assertEqual('BDA',_tInsert.get('a'))
        self.assertNotEqual('BDA',_tInsert.get('/a'))
        self.assertEqual('A',_tInsert.get('/a'))

# class TestTreeFind(unittest.TestCase):
#     tests_dir = pathlib.Path(__file__).absolute().parent
#
#     def _tree_factory(self,odict=None):
#         odict = OrderedDict() if odict is None else odict
#         return Tree(deepcopy(odict))

    @debug_on(Exception)
    def test_dfs(self):
        _test_odict_1 = OrderedDict(
            a='A',
            b=OrderedDict(
                c='BC',
                d=OrderedDict(
                    e='BDE',
                    f='BDF',
                ),
                g='BG',
                h=OrderedDict(
                    i='BHI',
                    j='BHJ',
                ),
            ),
        )
        _keys_to_test = ['a','b','c','d','e','f']
        _keychains_odict = OrderedDict(
            a='/a',
            b='/b',
            c='/b/c',
            d='/b/d',
            e='/b/d/e',
            f='/b/d/f',
            g='/b/g',
            h='/b/h',
            i='/b/h/i',
            j='/b/h/j'
        )


        _results_odict = OrderedDict(
            a='A',
            b = OrderedDict(
                c='BC',
                d=OrderedDict(
                    e='BDE',
                    f='BDF',
                ),
                g='BG',
                h=OrderedDict(
                    i='BHI',
                    j='BHJ',
                ),
            ),
            c='BC',
            d=OrderedDict(
                e='BDE',
                f='BDF',
            ),
            e='BDE',
            f='BDF',
            g='BG',
            h = OrderedDict(
                i='BHI',
                j='BHJ',
            ),
            i='BHI',
            j='BHJ'
        )

        for _key, _keychain in _keychains_odict.items():
            _t1 = self._tree_factory(_test_odict_1)
            __keychain, __value = _t1.dfs(_key)
            self.assertEqual(__keychain, _keychain.split('/'))
            self.assertEqual(__value,_results_odict.get(_key))

        self.assertRaises(KeyError,_t1.dfs,'x')

    @debug_on(Exception)
    def test_dfs_wins(self):
        _test_odict = OrderedDict(
            a=OrderedDict(
                b='AB'
            ),
            b='B'
        )

        _t1 = self._tree_factory(_test_odict)
        _keychain,_value = _t1.dfs('b')
        self.assertEqual(_keychain,['','a','b'])
        self.assertEqual(_value,'AB')

        _test_odict_2 = OrderedDict(
            a=OrderedDict(
                b='AB'
            ),
            b='B',
            c=OrderedDict(
                d=OrderedDict(
                    b='CDB'
                )
            )
        )

        _t1 = self._tree_factory(_test_odict_2)
        _keychain,_value = _t1.dfs('b')
        self.assertEqual(_keychain,['','c','d','b'])
        self.assertEqual(_value,'CDB')


#class TestTreeGet(unittest.TestCase):
#    tests_dir = pathlib.Path(__file__).absolute().parent
#
#    def _tree_factory(self,odict=None):
#        odict = OrderedDict() if odict is None else odict
#        return Tree(deepcopy(odict))
    @debug_on(Exception)
    def test_root_get(self):
        t = self._tree_factory()
        t.get('/a','A')
        self.assertEqual(t.odict,_od(a=_test_odict_0['a']))
    @debug_on(Exception)
    def test_root_override(self):

        t = self._tree_factory()
        _val = t.get('/c/a','CA')
        self.assertEqual(_val,'CA')
        _val = t.get('/c/b/a','CBA')
        self.assertEqual(_val,'CBA')
        _result_odict = OrderedDict(
            c=OrderedDict(
                a='CA',
                b=OrderedDict(
                    a='CBA'
                )
            )
        )
        self.assertEqual(t.odict,_result_odict)
        self.assertEqual(t.get('a'),'CBA')
        self.assertEqual(t.get('/c/a'),'CA')

        t2 = self._tree_factory()
        t2.get('/a/b','AB')
        # t2.get('a/c','AC')
        t2.get('/a/d','AD')
        t2.get('/a/x',t)

        _result_odict_2 = OrderedDict(
            a=OrderedDict(
                b='AB',
                # c='AC',
                d='AD',
                x=t.odict,
            )
        )

        self.assertEqual(t2.odict,_result_odict_2)
#class TestTreeStringify(unittest.TestCase):
#
#    tests_dir = pathlib.Path(__file__).absolute().parent
#
#    def _tree_factory(self,odict=None):
#        odict = OrderedDict() if odict is None else odict
#        return Tree(deepcopy(odict))


    @debug_on(Exception)
    def test_stringify(self):
        t = self._tree_factory(_test_odict_0)
        _tData = t.stringify()
        self.assertEqual(_tData,Tree(_test_odict_0))

#class TestTreeSystematic(unittest.TestCase):
#
#    tests_dir = pathlib.Path(__file__).absolute().parent
#
#    def _tree_factory(self,odict=None):
#        odict = OrderedDict() if odict is None else odict
#        return Tree(deepcopy(odict))

    @debug_on(Exception)
    def test_overlay(self):

        _base_tree = Tree()
        _test_odict_1 = OrderedDict(
            a='A'
        )
        _overlay_tree = self._tree_factory(_test_odict_1)
        _base_tree.overlay(_overlay_tree)
        # self.assertEqual(_overlay_tree.odict,_test_odict_1)
        self.assertEqual(_base_tree.odict,_test_odict_1)

        _base_tree = Tree(OrderedDict(
            a=OrderedDict(b='B')
        ))
        _overlay_tree = Tree(OrderedDict(
            a=OrderedDict(c='C')
        ))

        _base_tree.overlay(_overlay_tree)
        self.assertEqual(_base_tree,Tree(OrderedDict(
            a=OrderedDict(b='B',c='C')
        )))

        _test_odict_2 = OrderedDict(
            a='A',
            d=OrderedDict(b=['B1','B2']),
            c='C'
        )
        _test_odict_3 = OrderedDict(
            d=OrderedDict(b=['B3','B4'])
        )
        _base_tree = self._tree_factory(_test_odict_2)
        _overlay_tree = self._tree_factory(_test_odict_3)

        _base_tree.overlay(_overlay_tree)
        self.assertEqual(_base_tree,Tree(OrderedDict(a='A',d=OrderedDict(b=['B3','B4']),c='C')))

        _base_tree = self._tree_factory(
            OrderedDict(
                a=OrderedDict(
                    b=OrderedDict(
                        c='C',
                        d='D'
                    )
                )
            )
        )

        _overlay_tree = self._tree_factory(
            OrderedDict(
                a=OrderedDict(
                    b=OrderedDict(
                        e='E',
                        f='F'
                    )
                )
            )
        )

        _result_tree = self._tree_factory(
            OrderedDict(
                a=OrderedDict(
                    b=OrderedDict(
                        c='C',
                        d='D',
                        e='E',
                        f='F'
                    )
                )
            )
        )

        _base_tree.overlay(_overlay_tree)
        self.assertEqual(_base_tree,_result_tree)

        _base_tree = self._tree_factory(
            OrderedDict(
                X=OrderedDict(
                    a=OrderedDict(
                        b=OrderedDict(
                            c='C',
                            d='D'
                        )
                    )
                )
            )
        )

        _overlay_tree = self._tree_factory(
            OrderedDict(
                X=OrderedDict(
                    a=OrderedDict(
                        b=OrderedDict(
                            e='E',
                            f='F'
                        )
                    )
                )
            )
        )

        _result_tree = self._tree_factory(
            OrderedDict(
                X=OrderedDict(
                    a=OrderedDict(
                        b=OrderedDict(
                            c='C',
                            d='D',
                            e='E',
                            f='F'
                        )
                    )
                )
            )
        )

        _base_tree.overlay(_overlay_tree)
        self.assertEqual(_base_tree, _result_tree)

        _base_tree = self._tree_factory(
            OrderedDict(
                X=OrderedDict(
                    a=OrderedDict(
                        b=OrderedDict(
                            c='C',
                            d='D'
                        )
                    )
                )
            )
        )

        _overlay_tree = self._tree_factory(
            OrderedDict(
                b=OrderedDict(
                    e='E',
                    f='F'
                )
            )
        )

        _result_tree = self._tree_factory(
            OrderedDict(
                X=OrderedDict(
                    a=OrderedDict(
                        b=OrderedDict(
                            c='C',
                            d='D',
                            e='E',
                            f='F'
                        )
                    )
                )
            )
        )

        _base_tree.overlay(_overlay_tree,['X','a'])
        self.assertEqual(_base_tree, _result_tree)

        _base_tree = self._tree_factory(OrderedDict())

        _overlay_tree_1 = self._tree_factory(
            OrderedDict(
                X=OrderedDict(
                    a=OrderedDict(
                        b=OrderedDict(
                            c='C',
                            d='D'
                        )
                    )
                )
            )
        )

        _overlay_tree_2 = self._tree_factory(
            OrderedDict(
                X=OrderedDict(
                    a=OrderedDict(
                        b=OrderedDict(
                            e='E',
                            f='F'
                        )
                    )
                )
            )
        )

        _result_tree = self._tree_factory(
            OrderedDict(
                X=OrderedDict(
                    a=OrderedDict(
                        b=OrderedDict(
                            c='C',
                            d='D',
                            e='E',
                            f='F'
                        )
                    )
                )
            )
        )

        _base_tree.overlay(_overlay_tree_1)
        _base_tree.overlay(_overlay_tree_2)

        self.assertEqual(_base_tree,_result_tree)

        _base_tree = self._tree_factory(OrderedDict())
        _base_tree.oget([],_overlay_tree_1)
        _base_tree.oget([],_overlay_tree_2)

        self.assertEqual(_base_tree,_result_tree)

    @debug_on(Exception)
    def test_is_empty(self):
        _tree = Tree()
        self.assertTrue(_tree.is_empty())

        _tree.get('a','A')
        self.assertFalse(_tree.is_empty())

    @debug_on(Exception)
    def test_reset(self):
        # Test resetting an already empty tree
        tree = self._tree_factory()
        tree.reset()
        self.assertTrue(tree.is_empty())

        # Test resetting a populated tree
        tree = self._tree_factory(_test_odict_0)
        tree.reset()
        self.assertTrue(tree.is_empty())

        # Test resetting with a preserved key
        tree = self._tree_factory(_test_odict_0)
        tree.reset('b/d')
        expected_odict = OrderedDict(
            b=OrderedDict(
                d=OrderedDict(
                    e='BDE',
                    f='BDF'
                )
            )
        )
        self.assertEqual(tree.odict, expected_odict)

        _test_odict_reset = OrderedDict(
            a=OrderedDict(
                b='AB',
                c='AC'
            ),
            b=OrderedDict(
                d=OrderedDict(
                    c='BDC'
                )
            )
        )
        _result_odict = OrderedDict(
            b=OrderedDict(
                d=OrderedDict(
                    c='BDC'
                )
            )
        )
        tree = self._tree_factory(_test_odict_reset)
        tree.reset('c')
        self.assertEqual(tree.odict, _result_odict)

    def test_uget(self):
        tree = self._tree_factory(_test_odict_0)

        # Test getting an existing value
        self.assertEqual(tree.uget('b/c'), 'BC')

        # Test setting a new value
        self.assertEqual(tree.uget('x/y', 'XY'), 'XY')
        self.assertEqual(tree.get('x/y/'), 'XY')

    @debug_on(Exception)
    def test_aget(self):
        tree = self._tree_factory()

        # Test appending to a non-existent key
        self.assertEqual(tree.aget('a', 'val1'), ['val1'])
        self.assertEqual(tree.get('a/'), ['val1'])

        # Test appending to a key that holds a list
        self.assertEqual(tree.aget('a', 'val2'), ['val1', 'val2'])
        self.assertEqual(tree.get('a/'), ['val1', 'val2'])

        # Test appending a list to a key that holds a list
        self.assertEqual(tree.aget('a', ['val3', 'val4']), ['val1', 'val2', 'val3', 'val4'])
        self.assertEqual(tree.get('a/'), ['val1', 'val2', 'val3', 'val4'])

        # Test appending to a scalar value
        tree.get('b', 'scalar')
        self.assertEqual(tree.aget('b', 'new_val'), ['scalar', 'new_val'])
        self.assertEqual(tree.get('b/'), ['scalar', 'new_val'])

    def test_daget(self):
        tree = self._tree_factory()

        # Test dict-appending to a non-existent key
        tree.daget('a', {'key1': 'val1'})
        self.assertEqual(tree.get('a/'), dict(key1='val1'))

        # Test adding a new key-value pair
        tree.daget('a', {'key2': 'val2'})
        self.assertEqual(tree.get('a/'), dict(key1='val1', key2='val2'))

        # Test updating an existing key
        tree.daget('a', {'key1': 'new_val1'})
        self.assertEqual(tree.get('a/'), dict(key1='new_val1', key2='val2'))

        # Test exception on non-dict target
        tree.get('b', 'not_a_dict')
        with self.assertRaises(TreeException):
            tree.daget('b', {'key3': 'val3'})

    def test_get_exceptions(self):
        tree = self._tree_factory()
        with self.assertRaises(KeyError):
            tree.get('non/existent/key')

        with self.assertRaises(TreeException):
            tree.get('/', 'a_scalar_value')

        with self.assertRaises(TreeException):
            tree.get([], 'a_scalar_value')

    def test_flatten(self):
        sample_data = OrderedDict([
            ('a', OrderedDict([
                ('b', 'B_VAL')
            ])),
            ('c', ['C1', 'C2'])
        ])
        tree = self._tree_factory(sample_data)

        # Test with absolute keychains (default)
        absolute_flattened = tree.flatten()
        expected_absolute = [
            (['', 'a', 'b'], 'B_VAL'),
            (['', 'c'], ['C1', 'C2'])
        ]
        self.assertEqual(absolute_flattened, expected_absolute)

        # Test with relative keychains
        relative_flattened = tree.flatten(relative=True)
        expected_relative = [
            (['a', 'b'], 'B_VAL'),
            (['c'], ['C1', 'C2'])
        ]
        self.assertEqual(relative_flattened, expected_relative)


if __name__ == '__main__':
    unittest.main()
