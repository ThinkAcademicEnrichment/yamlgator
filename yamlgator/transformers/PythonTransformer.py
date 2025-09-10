from ..constants import *
from ..tree import *
from .PathValueTransformer import *


class PythonTransformerException(Exception):
    pass


class PythonTransformer(PathValueTransformer):
    ext = 'py'

    def __init__(self, odict_or_tree):
        if DEBUG.PythonTransformer: ic()
        super(PythonTransformer,self).__init__(odict_or_tree)

    def _loader(self,stream):
        # see https://github.com/berkerpeksag/astor/blob/master/astor/file_util.py
        fstr = stream.read()
        fstr = fstr.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        if not fstr.endswith(b'\n'):
            fstr += b'\n'
        return ast.parse(fstr, filename=stream.name)

    def _translate_keychain(self, _py_keychain):
        '''keychains in python are strings of the form x__y__z -> ))(x/y/z) e.g.'''
        if '__' in _py_keychain:
            # keychain type
            return f"{KEY_OR_KEYCHAIN_OP}{KEYCHAIN_LEFT_BOUND}{_py_keychain.replace('__', KEYCHAIN_SEP)}{KEYCHAIN_RIGHT_BOUND}"
        else:
            # key type
            return f"{KEY_OR_KEYCHAIN_OP}{_py_keychain}"

    def select(self, stream, _py_func_name):
        # holds the lines of a multiline Tree value
        _exec_node_lines = []

        class FuncVisitor(ast.NodeVisitor):
            def _bind_arguments(_self, arguments, line):
                for _argument in map(lambda x: astor.to_source(x).strip(), arguments):
                    # translate the python keychain syntax into substitution syntax
                    _new_argument = self._translate_keychain(_argument)
                    ############################################
                    # TODO: - and _ are ambiguous in key names for legacy reasons! Dumb!
                    ############################################
                    # print(f"!! altering referred key name from {_new_argument} to {_new_argument.replace('_','-')}")
                    _new_argument = _new_argument.replace('_','-')
                    # this is really dumb. There must be a better way
                    line = line.replace(f'{_argument}', f"'{_new_argument}'")
                return line

            def visit_Import(_self, node):
                _exec_node_lines.append(astor.to_source(node))

            def visit_ImportFrom(_self, node):
                _exec_node_lines.append(astor.to_source(node))

            def visit_FunctionDef(_self, node):
                # alter the body of the functions to use SubstitutionTransformer syntax
                if node.name == _py_func_name:
                    [_exec_node_lines.append(_self._bind_arguments(node.args.args, x)) for x in
                                                             list(map(astor.to_source, node.body))]


        FuncVisitor().visit(self._loader(stream))

        return Tree(OrderedDict(python=''.join(_exec_node_lines)))
