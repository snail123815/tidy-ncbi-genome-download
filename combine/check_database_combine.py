# Before combining two databases, use this script to check the file names.
# This script should check:
# - Replication of file names, including those only differ in letter cases.
# - File name safety, make sure there is no illegal characters: :,();[]'" /{}+*\t\n

import os
import argparse
from typing import Any, overload
from collections import Counter

from tidy import safeName


def checkIllegal(names: list[str]) -> list[tuple[str, None|str]]:
    corrNames = []
    containsIllegalNames = False
    for name in names:
        sname: None|str = safeName(name)
        if sname == name:
            sname = None
        corrNames.append((name, sname))
    illegalNames = [ns for ns in corrNames if not ns[1] is None]
    if len(illegalNames) > 0:
        containsIllegalNames = True
        for ns in illegalNames:
            print(f'File with illegal character: "{ns[0]}",\n' +
                  f'\tshould be corrected to "{ns[1]}"')
    if not containsIllegalNames:
        print('No illegal characters found.')
    else:
        print()
    return corrNames

@overload
def splitExt(n: str) -> tuple[str, str]:
    ...
@overload
def splitExt(n: None) -> tuple[None, None]:
    ...
def splitExt(n):
    if n is None: return None, None
    name, ext = os.path.splitext(n)
    if ext in ['.gz', '.xz']:
        name, subExt = os.path.splitext(name)
        ext = subExt+ext
    return name, ext


def checkDup(dictOfCorrNames: dict[str, list[tuple[str, None|str]]]) -> None:
    uniqueNames: set[str] = set()
    noneUnique: set[str] = set()
    count = 0
    for _, corrNames in dictOfCorrNames.items():
        count += len(corrNames)
        for n0, n1 in corrNames: 
            n: str = (n0 if n1 is None else n1).lower()
            name, _ = splitExt(n)
            if name in uniqueNames:
                noneUnique.add(name)
            else:
                uniqueNames.add(name)
        
    sortedNoneUnique = sorted(list(noneUnique))
    dups: dict[str, list[tuple[str, str, str|None]]] = {}
    for p, corrNames in dictOfCorrNames.items():
        for nn in sortedNoneUnique:
            for n0, n1 in corrNames:
                nx, _ = splitExt(n0)
                ny, _ = splitExt(n1)
                if nn in [nx.lower(), (None if ny is None else ny.lower())]:
                    if nn not in dups:
                        dups[nn] = [(p, n0, n1)]
                    else: dups[nn].append((p, n0, n1))
    
    for dup, itemlist in dups.items():
        print(f'Found duplicated name {dup}:')
        for p, n0, n1 in itemlist:
            print('\t'+os.path.join(p, n0))
            if not n1 is None:
                print('\t\t'+os.path.join(p, n1))
    
    if len(noneUnique) == 0:
        print('No possible duplication found in dir(s):')
        print('\t'+'\n'.join(dictOfCorrNames.keys()))
    else:
        print(f'Found {len(noneUnique)} none unique name(s), {len(uniqueNames)} unique one(s).')
    print(f'Total checked files: {count}\n')

    
def checkCombine(paths: list[str]) -> None:
    namesEachPath = {}
    print()
    for p in paths:
        print(f'Checking dir {p} individually.')
        # check illegal names in each path
        corrNames = checkIllegal(os.listdir(p))
        namesEachPath[p] = corrNames
        # check duplication in single path
        checkDup({p:corrNames})
    # check duplication if combined
    print('Checking dirs as combined:')
    checkDup(namesEachPath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('p', nargs="+", help="pathes of databases (folders) you want to combine")

    args = parser.parse_args()

    checkCombine(args.p)

