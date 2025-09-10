from tests import *

class TestYAMLator(unittest.TestCase):
    tests_dir = pathlib.Path(__file__).absolute().parent

    def yamlator_factory(self,odict=None,root_dir=None):
        odict = OrderedDict() if odict is None else odict
        return YAMLator(deepcopy(odict),root_dir)

    @debug_on(Exception)
    def test_get_as_object(self):
        _test_odict = OrderedDict({
            'is-a':'True',
            'use-b':'False',
            'is-c':'y',
            'use-d':'n',
            'my-path': '/var/tmp/xtoo'
        })

        _yltr = YAMLator(_test_odict)

        self.assertTrue(_yltr.get_as_object('is-a'))
        self.assertIsInstance(_yltr.get_as_object('is-a'),bool)
        self.assertFalse(_yltr.get_as_object('use-b'))
        self.assertIsInstance(_yltr.get_as_object('use-b'),bool)

        self.assertTrue(_yltr.get_as_object('is-c'))
        self.assertIsInstance(_yltr.get_as_object('is-c'), bool)
        self.assertFalse(_yltr.get_as_object('use-d'))
        self.assertIsInstance(_yltr.get_as_object('use-d'), bool)

        self.assertIsInstance(_yltr.get_as_object('my-path'),pathlib.Path)

    @debug_on(Exception)
    def test_objects(self):
        _tests_yaml = self.tests_dir.joinpath('objects.yaml')
        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            _test_tree = _tests_tree.get(['', _test_name])
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':

                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _test_tree.get('output/').copy()

                _input_tree.set_config_attrs(set_all=True)

                def _object_value_check(node, keychain):
                    assert isinstance(node, list)
                    _attr_name = keychain[-1].upper().replace('-','_')
                    _object_value = getattr(_input_tree,_attr_name)
                    _object_type, _str_rep = node
                    try:
                        _package, _class = _object_type.split('.')
                        _mod = import_module(_package)
                        self.assertIsInstance(_object_value, getattr(_mod, _class))
                    except ValueError:
                        if _object_type == 'bool':
                            _object_type = bool
                        elif _object_type == 'str':
                            _object_type = str
                        self.assertIsInstance(_object_value, _object_type)

                    self.assertEqual(str(_object_value), _str_rep)

                _output_tree.visit(value_process=_object_value_check)

    @debug_on(Exception)
    def test_merge_yaml(self):
        _test_odict = OrderedDict(
            a='A',
            b=OrderedDict(
                c='C',
                d='D'
            )
        )

        _to_merge_odict = OrderedDict(
            e='E',
            f='F'
        )
        _tmp_dir = self.tests_dir.joinpath('tmp')
        _tmp_dir.mkdir(exist_ok=True)
        _ymltr = self.yamlator_factory(_test_odict,_tmp_dir)

        _tmp_yaml = pathlib.Path(tempfile.mkstemp(dir=_tmp_dir,suffix='.yaml')[1])
        with _tmp_yaml.open('w') as _f:
            Tree(_to_merge_odict).dump(_f)

        _ymltr_copy = _ymltr.copy()
        _ymltr_copy.merge(f'{_tmp_yaml}#/', '/b/')

        self.assertEqual(
            _ymltr_copy.odict,
            OrderedDict(
                 a='A',
                 b=OrderedDict(
                     e='E',
                     f='F'
                 )
            ))

        _ymltr_copy = _ymltr.copy()
        _ymltr_copy.merge(f'{_tmp_yaml}#/', 'b')

        self.assertEqual(
            _ymltr_copy.odict,
            OrderedDict(
                 a='A',
                 b=OrderedDict(
                     c='C',
                     d='D',
                     e='E',
                     f='F'
                 )
            ))

    @debug_on(Exception)
    def test_config_merge_yaml(self):
        _config_odict = OrderedDict(
            config=OrderedDict(
                build_server_url=OrderedDict(
                    default='https://build.funtoo.org',
                ),
                meta_repo_dir=OrderedDict(
                    default='/var/git/meta-repo',
                ),
            )
        )

        _tmp_dir = self.tests_dir.joinpath('tmp')
        _tmp_dir.mkdir(exist_ok=True)
        _ymltr = self.yamlator_factory(OrderedDict(),_tmp_dir)

        _tmp_yaml = pathlib.Path(tempfile.mkstemp(dir=_tmp_dir,suffix='.yaml')[1])
        with _tmp_yaml.open('w') as _f:
            Tree(_config_odict).dump(_f)

    @debug_on(Exception)
    def test_transform(self):
        _tests_yaml = self.tests_dir.joinpath('transform.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)
        for _test_name in _tests_tree.keys():
            _test_tree = _tests_tree.get(_test_name)
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _input_tree.copy()
                _output_tree.overlay(_test_tree.get('output/').copy())
                _input_tree.transform()
                self.assertEqual(_input_tree, _output_tree)

    @debug_on(Exception)
    def test_hierarchical_ifs(self):
        _tests_yaml = self.tests_dir.joinpath('hierarchical-ifs.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = Tree(Tree._load(f))

        for _test_name in _tests_tree.keys():
            _test_tree = _tests_tree.get(_test_name)
            _skip = _test_tree.uget('skip','n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _test_tree.get('output/').copy()
                YAMLator(_input_tree,root_dir=self.tests_dir).transform()
                self.assertEqual(_input_tree, _output_tree)

if __name__ == '__main__':
    unittest.main()
