"""
Validate examples used in the README.md
"""
from tests import *

class TestExamples(unittest.TestCase):
    tests_dir = pathlib.Path(__file__).absolute().parent.joinpath('test-docs')

    @debug_on(Exception)
    def test_examples(self):
        _tests_yaml = self.tests_dir.joinpath('readme-examples.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}\n{'-'*len(_test_name)}")
            print()
            _test_tree = _tests_tree.get(_test_name)
            _input_tree = _test_tree.get('input/').copy()
            print(_input_tree)
            _output_tree = _test_tree.get('output/').copy()
            YAMLator(_input_tree).transform()
            print(_input_tree)
            try:
                self.assertEqual(_input_tree.odict,_output_tree.odict)
            except Exception as e:
               print()
               print(_output_tree)
               raise e


    def test_bangs(self):
        class BangYAMLator(YAMLator):
            def short_uuid(self):
                import uuid
                return str(uuid.uuid1())[:4]

            def uuid(self):
                import uuid
                return str(uuid.uuid1())

            def token_hex(self, n):
                import secrets
                return str(secrets.token_hex(n))

            def date(self, date_fmt_str):
                import datetime
                return datetime.datetime.now().strftime(date_fmt_str)

            def replace(self, s, char1, char2):
                return str(s).replace(char1, char2)

        _tests_yaml = self.tests_dir.joinpath('bang-examples.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"\n{_test_name}\n{'-'*len(_test_name)}")
            print()
            _test_tree = _tests_tree.get(_test_name)
            _input_tree = _test_tree.get('input/').copy()
            print(_input_tree)
            BangYAMLator(_input_tree).transform()
            print(_input_tree)

    def test_issues(self):
        '''validate issues'''

        _tests_yaml = self.tests_dir.joinpath('validation-examples.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            _test_tree = _tests_tree.get(['',_test_name])
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':
                _input_tree = _test_tree.get('input/').copy()
                _all_issues = _input_tree.validate()
                _issue_names = [result.issue_type.name for result in _all_issues]
                for _issue_name in _issue_names:
                    self.assertIn(_issue_name, _test_tree.get('validation-issues/'))
                for _issue in _all_issues:
                    print(f"\t{_issue}")
            else:
                print(f'skipping validation of issues:{_test_name}')

    @debug_on(Exception)
    def test_type_conversion(self):
        import pathlib
        from yarl import URL
        from yamlgator import YAMLator

        class MyConfig(YAMLator):
            WORK_DIR = None
            IS_PRODUCTION = None
            API_URL = None

        _config_yaml = self.tests_dir.joinpath('type-conversion-example.yaml')

        with _config_yaml.open('r') as f:
            _configlator = MyConfig.load(f)

        _configlator.transform()
        _configlator.set_config_attrs()

        # Verify the types
        print()
        print(f"WORK_DIR: {_configlator.WORK_DIR} (type: {type(_configlator.WORK_DIR)})")
        print(f"IS_PRODUCTION: {_configlator.IS_PRODUCTION} (type: {type(_configlator.IS_PRODUCTION)})")
        print(f"API_URL: {_configlator.API_URL} (type: {type(_configlator.API_URL)})")

        self.assertIsInstance(_configlator.WORK_DIR, pathlib.Path)
        self.assertIsInstance(_configlator.IS_PRODUCTION, bool)
        self.assertIsInstance(_configlator.API_URL, URL)
        self.assertTrue(_configlator.IS_PRODUCTION is True)


if __name__ == '__main__':
    unittest.main()


