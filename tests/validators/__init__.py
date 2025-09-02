from tests import *
import io
import random


class TestValidator(unittest.TestCase):
    tests_dir = pathlib.Path(__file__).absolute().parent.joinpath('test-docs')

    @debug_on(Exception)
    def test_basic(self):
        '''validate basic tests '''

        _tests_yaml = self.tests_dir.joinpath('basic-tests.yaml')

        with _tests_yaml.open('r') as f:
            _tests_tree = YAMLator.load(f)

        for _test_name in _tests_tree.keys():
            print(f"Validating {_test_name} data")
            _test_tree = _tests_tree.get(['',_test_name])
            _skip = _test_tree.uget('skip', 'n')
            if not _skip == 'y':

                _input_tree = _test_tree.get('input/').copy()
                _all_issues = _input_tree.validate()
                for _issue in _all_issues:
                    print(f"\t{_issue}")

            else:
                print(f'skipping {_test_name}')

if __name__ == '__main__':
    unittest.main()
