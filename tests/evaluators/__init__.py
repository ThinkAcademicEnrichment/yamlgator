from tests import *

class TestEvaluator(unittest.TestCase):
    tests_dir = pathlib.Path(__file__).absolute().parent

    @debug_on(Exception)
    def test_StateEvaluator(self):
        from yamlgator.constants import REGEXES

        class VolumeObs(RegexObservable):
            keychain_regex = rf'^({REGEXES.KEYCHAIN}volumes/)({REGEXES.KEY})$'

            def _create_state_keychain(self,*parameters):
                _keychain_root,_key = parameters
                return _keychain_root

            def _create_observation(self,node,*parameters):
                _,_vol_name, = parameters

                _path = node.get('path')
                _bind = node.get('bind')
                _mode = node.get('mode','ro')

                _state_keychain = self._create_state_keychain(*parameters)

                _vol_dict = dict({
                    _path:dict(
                        bind=_bind,
                        mode=_mode
                    )
                })

                return _state_keychain,_vol_dict

        # note this is a value/scalar observable
        class PathObs(RegexObservable):
            keychain_regex = rf'({REGEXES.KEYCHAIN})({REGEXES.PATH_TYPE_KEY})'

            def _create_state_keychain(self,*parameters):
                _keychain_root,_key = parameters
                return ''.join([_keychain_root,'paths'])

            def _create_observation(self,node,*parameters):
                _state_keychain = self._create_state_keychain(*parameters)
                return _state_keychain, node

        _t = Tree(OrderedDict(
            config=OrderedDict({
                'a-path':str(self.tests_dir),
                'b':'B',


            }),
            recipe=OrderedDict(
                volumes=OrderedDict({
                    'vol-a':OrderedDict(
                        path=str(self.tests_dir.joinpath('tmp/test-a.txt')),
                        bind='/xtoo/test-a.txt',
                        mode='ro'
                    ),
                    'vol-b':OrderedDict(
                        path=str(self.tests_dir.joinpath('tmp/test-b.txt')),
                        bind='/xtoo/test-b.txt',
                        mode='rw'
                    )}
                )
            )
        ))

        _se = StateEvaluator(_t, AggregateState([VolumeObs()],[PathObs()],[]))
        _se.evaluate()
        _result = Tree(OrderedDict(
            config=OrderedDict(
                paths=[str(self.tests_dir)]
            ),
            recipe=OrderedDict(
                volumes=[
                    {str(self.tests_dir.joinpath('tmp/test-a.txt')):dict(bind='/xtoo/test-a.txt',mode='ro')},
                    {str(self.tests_dir.joinpath('tmp/test-b.txt')):dict(bind='/xtoo/test-b.txt',mode='rw')},
                ]
            )
        ))

        self.assertEqual(_result,_se.state)

        # _se = StateEvaluator(_t, AggregateState(
        #     [VolumeObs()], [PathObs()], []))
        # _se.evaluate()
        # # you cannot remove a value observation with a post_observable
        # _result = Tree(OrderedDict(
        #     config=OrderedDict(
        #         paths=[self.tests_dir]
        #     ),
        # ))
        # self.assertEqual(_result,_se.state)

    @debug_on(Exception)
    def test_PathValueObjectObservable(self):
        _t1 = Tree(OrderedDict({
                'a-path': str(self.tests_dir)
            }))

        _t2 = Tree(OrderedDict(
            config=OrderedDict(OrderedDict({
                'a-deeper-value':OrderedDict({
                    'a-path':str(self.tests_dir)
                })
            })
        )))

        _t3 = Tree(OrderedDict(
            config=OrderedDict(OrderedDict({
                'a-deeper-value':OrderedDict({
                    'a-deeper-deeper-value':OrderedDict({
                        'a-path':str(self.tests_dir)
                    })
                })
            })
        )))

        class PathValueObservable(RegexObservable):
            keychain_regex = rf'({REGEXES.KEYCHAIN})?({REGEXES.PATH_TYPE_KEY})'

            def _create_state_keychain(self,*parameters):
                _root,_key = parameters
                return ''.join([_root,_key])

            def _create_observation(self,node,*parameters):
                return self._create_state_keychain(*parameters),pathlib.Path(node)

        _se = StateEvaluator(_t1,TreeState([],[PathValueObservable()],[]))
        _se.evaluate()
        _result = Tree(OrderedDict({
            'a-path':self.tests_dir
        }))
        self.assertEqual(_se.state,_result)

        _se = StateEvaluator(_t2,TreeState([],[PathValueObservable()],[]))
        _se.evaluate()
        _result = Tree(OrderedDict(
            config=OrderedDict(OrderedDict({
                'a-deeper-value': OrderedDict({
                    'a-path': self.tests_dir
                })
            })
        )))
        self.assertEqual(_se.state,_result)

        _se = StateEvaluator(_t3,TreeState([],[PathValueObservable()],[]))
        _se.evaluate()
        _result  = Tree(OrderedDict(
            config=OrderedDict(OrderedDict({
                'a-deeper-value':OrderedDict({
                    'a-deeper-deeper-value':OrderedDict({
                        'a-path':self.tests_dir
                    })
                })
            })
        )))
        self.assertEqual(_se.state,_result)


if __name__ == '__main__':
    unittest.main()
