from tests import *
class MockYAMLator(YAMLator):
    def machine_arch(self):
        return 'x86-64bit'
    def machine_subarch(self):
        return 'amd64-zen'
    def ncpus(self):
        return 16
    def machine_python_exe(self):
        return 'python3.9'

class TestXtoo(unittest.TestCase):
    types_dir = pathlib.Path(__file__).absolute().parent.joinpath('types')
    projects_dir = pathlib.Path(__file__).absolute().parent.joinpath('projects')

    @debug_on(Exception)
    def test_init(self):
        _type_yaml = self.types_dir.joinpath('init.yaml')
        _project_yaml = self.projects_dir.joinpath('init.yaml')


        with _type_yaml.open('r') as f:
            _type_tree = MockYAMLator.load(f)
        with _project_yaml.open('r') as f:
            _project_tree = YAMLator.load(f)

        _type_tree.transform()
        self.assertEqual(_type_tree.odict,_project_tree.odict)

    @debug_on(Exception)
    def test_host(self):
        _type_yaml = self.types_dir.joinpath('host.yaml')
        _project_yaml = self.projects_dir.joinpath('host.yaml')

        _context_yaml = self.projects_dir.joinpath('init.yaml')

        with _type_yaml.open('r') as f:
            _type_tree = MockYAMLator.load(f)
        with _project_yaml.open('r') as f:
            _project_tree = YAMLator.load(f)
        with _context_yaml.open('r') as f:
            _context_tree = YAMLator.load(f)

        # this mimics a type of 'inheritence' between the trees
        _type_tree.transform(methods=['transform_ats','transform_values'],context_tree=_context_tree)
        _type_tree.transform()
        # override ))!short-uuid() from base.yaml
        _type_tree.get('project-id','8349')
        def _compare_values(node,keychain):
            self.assertEqual(node,_project_tree.get([keychain,'']))
        _type_tree.visit(value_process=_compare_values)

        _type_tree_flat = _type_tree.flatten()
        _project_tree_flat = _project_tree.flatten()
        self.assertEqual(_type_tree_flat, _project_tree_flat)

        self.assertEqual(_type_tree.get('config').odict,_project_tree.get('config').odict)
        self.assertEqual(_type_tree.get('recipe').odict,_project_tree.get('recipe').odict)

if __name__ == '__main__':
    unittest.main()