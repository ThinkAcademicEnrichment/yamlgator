from __future__ import annotations
from ..tree import Tree


class AbstractValidator(Tree):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
