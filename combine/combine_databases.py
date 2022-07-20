import os
import shutil
from typing import Literal
from combine import checkCombine

def combineDatabases(paths, target, keep: Literal['first','all']='first'):
    corrPathNames = checkCombine(paths, keep=keep)
    os.makedirs(target)
    for p, corrNames in corrPathNames.items():
        for fn0, fn1 in corrNames:
            src = os.path.join(p, fn0)
            dst = os.path.join(target, (fn0 if fn1 is None else fn1))
            shutil.copyfile(src, dst)