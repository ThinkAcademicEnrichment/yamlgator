from tests import *
import io
import random


class TestTransformer(unittest.TestCase):
    tests_dir = pathlib.Path(__file__).absolute().parent.joinpath('test-docs')

    @debug_on(Exception)
    def test_basic(self):
        '''apply a sequence of transformations '''

        _tests_yaml = self.tests_dir.joinpath('basic-tests.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            # print(f"\n Transforming {_test_name}")
            _test_tree = _tests_tree.get(['',_test_name])
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':
                _transformer_class_names = _test_tree.get('transformer/')
                if not isinstance(_transformer_class_names,list):
                    _transformer_class_names = [_transformer_class_names]

                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _test_tree.get('input/').copy()
                _output_tree.overlay(_test_tree.get('output/'))

                for _transformer_class_name in _transformer_class_names:
                    _transformer_class = globals().get(_transformer_class_name)
                    if _transformer_class in (YAMLTransformer,PlainTextTransformer,ImportTransformer):
                        _transformer_class(_input_tree,root_dir=self.tests_dir).evaluate()
                    elif _transformer_class in (BangTransformer,ValueTransformer, AtTransformer, IfTransformer):
                        _transformer_class(_input_tree).evaluate()
                self.assertEqual(_input_tree, _output_tree)
            else:
                print(f'skipping {_test_name}')

            # self._is_confluent_with(_test_tree.get('input/').copy(), _output_tree,list(map(lambda x:getattr(globals().get(x),'name'),_transformer_class_names)))

    #  so deeply confusing
    # @debug_on(Exception)
    # def test_restrictions(self):
    #     _tests_yaml = self.tests_dir.joinpath('restriction-tests.yaml')
    #
    #     with _tests_yaml.open('r') as f:
    #         _tests_tree = Tree(Tree._load(f))
    #
    #     for _test_name in _tests_tree.keys():
    #         ic(_test_name)
    #         _test_tree = _tests_tree.get(['', _test_name, ''])
    #         _all_output_tree = _test_tree.get('/output/').copy()
    #         for _restriction in _all_output_tree.keys():
    #             ic(_restriction)
    #             _input_tree = _test_tree.get('/input/').copy()
    #             _output_tree_overlay = _all_output_tree.get(['', _restriction, '']).copy()
    #             ic(_output_tree_overlay.print())
    #
    #             _output_tree = _input_tree.copy()
    #
    #             _output_tree.overlay(_output_tree_overlay)
    #
    #             SubstitutionValueTransformer(_input_tree, _restriction).evaluate()
    #             self.assertEqual(_input_tree.odict, _output_tree.odict)

    @debug_on(Exception)
    def test_key_subs(self):
        _tests_yaml = self.tests_dir.joinpath('key-subs.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            _test_tree = _tests_tree.get(_test_name)
            _input_tree = _test_tree.get('input/').copy()
            _output_tree = _test_tree.get('output/').copy()
            KeyTransformer(_input_tree).evaluate()
            self.assertEqual(_input_tree.odict,_output_tree.odict)

            self._is_confluent(_test_tree.get('input/').copy(), _output_tree)

    @debug_on(Exception)
    def test_list_subs(self):
        _tests_yaml = self.tests_dir.joinpath('list-subs.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            _test_tree = _tests_tree.get(_test_name)

            _input_tree = _test_tree.get('input/').copy()
            _output_tree = _test_tree.get('input/').copy()
            _output_tree.overlay(_test_tree.get('output/'))

            ValueTransformer(_input_tree).evaluate()
            self.assertEqual(_input_tree.odict,_output_tree.odict)

            self._is_confluent(_test_tree.get('input/').copy(), _output_tree)

    @debug_on(Exception)
    def test_if_keys(self):
        _tests_yaml = self.tests_dir.joinpath('if-keys.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            _test_tree = _tests_tree.get(_test_name)
            _skip = _test_tree.uget('skip','n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                # we are changing tree structure here
                _output_tree = _test_tree.get('output/').copy()
                IfKeyTransformer(_input_tree).evaluate()
                ValueTransformer(_input_tree).evaluate()
                self.assertEqual(_input_tree.odict,_output_tree.odict)
                # if _test_name == 'test-5': 1/0

                try:
                    self._is_confluent(_test_tree.get('input/').copy(), _test_tree.get('output/').copy())
                except Exception as e:
                    print(f"\n Full Confluence fails")
                    1/0
                self._is_confluent_with(_test_tree.get('input/').copy(), _test_tree.get('output/').copy(),[IfKeyTransformer.name,ValueTransformer.name])

    @debug_on(Exception)
    def test_if_vars(self):
        _tests_yaml = self.tests_dir.joinpath('if-vars.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            _test_tree = _tests_tree.get(_test_name)
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _input_tree.copy()
                _output_tree.overlay(_test_tree.get('output/').copy())
                IfTransformer(_input_tree).evaluate()
                ValueTransformer(_input_tree).evaluate()
                self.assertEqual(_input_tree.odict, _output_tree.odict)
                # self.assertEqual(_input_tree, _output_tree)

            self._is_confluent(_test_tree.get('input/').copy(), _output_tree)


    @debug_on(Exception)
    def test_context(self):
        _tests_yaml = self.tests_dir.joinpath('context.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)
        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            _test_tree = _tests_tree.get(_test_name)
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _input_tree.copy()
                _output_tree.overlay(_test_tree.get('output/').copy())
                ValueTransformer(_input_tree).evaluate()
                self.assertEqual(_input_tree, _output_tree)

            self._is_confluent(_test_tree.get('input/').copy(), _output_tree)

    @debug_on(Exception)
    def test_import(self):
        _tests_yaml = self.tests_dir.joinpath('imports.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)
        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            _test_tree = _tests_tree.get(_test_name)
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _test_tree.get('output/').copy()
                ImportTransformer(_input_tree).evaluate()
                self.assertEqual(_input_tree, _output_tree)

            self._is_confluent(_test_tree.get('input/').copy(), _output_tree)

    @debug_on(Exception)
    def test_plaintext(self):
        _tests_yaml = self.tests_dir.joinpath('plaintext.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)
        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            _test_tree = _tests_tree.get(_test_name)
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _test_tree.get('output/').copy()
                PlainTextTransformer(_input_tree).evaluate()

                self.assertEqual(_input_tree, _output_tree)

        self._is_confluent(_test_tree.get('input/').copy(), _output_tree)

    def _is_confluent_with(self,initial_yt,expected_tree,transforms=None):
        from itertools import permutations
        if transforms is None:
            transforms = list(DEFAULT_UTILITIES.keys())
        _test_results = {}
        for _permuted_transforms in permutations(transforms):
            _yt = initial_yt.copy()
            _yt.transform(methods=_permuted_transforms)
            _test_results.update({_permuted_transforms : _yt == expected_tree})
        # self.assertTrue(any(_test_results.values()))
        if not any(_test_results.values()):
            print('CONFLUENCE FAILURE!!!!')
        print("\nConfluence Test Results:")
        for _permuted_transforms, _result in _test_results.items():
            print(f"\n\t{_permuted_transforms} : {_result}")
        return _test_results

    def _is_confluent(self,initial_yt,expected_tree):
        """
        Tests that YAMLator.transform() is confluent, i.e., the final result
        is independent of the order of transformer utilities.
        """

        # 2. Establish the canonical result with default order
        canonical_yt = initial_yt.copy()
        canonical_yt.transform()
        self.assertEqual(canonical_yt, expected_tree)

        # 3. Test with a reversed order of transformers
        reversed_yt = initial_yt.copy()
        default_methods = list(DEFAULT_UTILITIES.keys())
        default_methods.reverse()
        reversed_yt.transform(methods=default_methods)
        self.assertEqual(reversed_yt, expected_tree)

        # 4. Test with a shuffled order of transformers
        shuffled_yt = initial_yt.copy()
        shuffled_methods = list(DEFAULT_UTILITIES.keys())
        random.shuffle(shuffled_methods)
        shuffled_yt.transform(methods=shuffled_methods)
        self.assertEqual(shuffled_yt, expected_tree)


    # @debug_on(Exception)
    # def test_confluence(self):
    #     _test_yaml = self.tests_dir.joinpath('confluence.yaml')
    #     with _test_yaml.open('r') as f:
    #         _tests_tree = YAMLator.load(f)
    #     for _test_name in _tests_tree.keys():
    #         print(f"\n{_test_name}")
    #         _test_tree = _tests_tree.get(_test_name)
    #         _skip = _test_tree.uget('skip', 'n')
    #         if not _skip == 'y':
    #             _input_tree = _test_tree.get('input/').copy()
    #             _output_tree = _test_tree.get('input/').copy()
    #             _output_tree.overlay(_test_tree.get('output/'))
    #
    #             self._is_confluent_with(_input_tree,_output_tree,transforms=_test_tree.get('transformer/'))
    #         else:
    #             print(f"\n{_test_name} skipped")

    # ----- Non confluent transforms

    @debug_on(Exception)
    def test_at_if_vars(self):
        _tests_yaml = self.tests_dir.joinpath('if-at-vars.yaml')
        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}")
            _test_tree = _tests_tree.get(_test_name)
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                _output_tree = _input_tree.copy()
                _output_tree.overlay(_test_tree.get('output/').copy())
                _yt = YAMLator(_input_tree)
                AtTransformer(_input_tree).evaluate()
                IfTransformer(_input_tree).evaluate()
                ValueTransformer(_input_tree).evaluate()
                self.assertEqual(_input_tree.odict, _output_tree.odict)

                self._is_confluent_with(_test_tree.get('input/').copy(), _output_tree,transforms=['transform_ats','transform_ifs','transform_values'])

if __name__ == '__main__':
    unittest.main()
