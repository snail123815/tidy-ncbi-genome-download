# Before combining two databases, use this script to check the file names.
# This script should check:
# - Replication of file names, including those only differ in letter cases.
# - File name safety, make sure there is no illegal characters, using the function safeName

import os
import argparse
import re
from typing import overload, Literal
from tidy import safeName


def checkIllegal(names: list[str]) -> list[tuple[str, None|str]]:
    corrNames: list[tuple[str, None|str]] = []
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
    corrNames.sort(key=lambda x: x[0].lower())
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


def checkDup(
    corrPathNames_in: dict[str, list[tuple[str, None|str]]],
    keep='first'
) -> dict[str, list[tuple[str, None|str]]]:

    corrPathNames_out: dict[str, list[tuple[str, None|str]]] = {}
    uniqueNames: set[str] = set() # track all unique names
    noneUnique: set[str] = set() # track none unique names
    allNames: set[str] = set() # track all names, with suffix added to the none unique ones
    count = 0 # track total files
    noneUniquePrefix = '_name_rep'
    hasAssignedChecker = re.compile(noneUniquePrefix+r'\d+$')

    for p, corrNames_in in corrPathNames_in.items():
        corrPathNames_out[p] = []
        count += len(corrNames_in)

        for fn0, fn1 in corrNames_in: 
            fn = (fn0 if fn1 is None else fn1)
            name, ext = splitExt(fn)
            uniqueNames.add(name.lower())

            lenAll = len(allNames)
            allNames.add(name.lower())
            isUnique = (lenAll != len(allNames))
            if not isUnique: noneUnique.add(name.lower())
            noneUniqueIndex = 0
            while lenAll == len(allNames):
                noneUniqueIndex += 1
                hasAssigned = hasAssignedChecker.search(name)
                if hasAssigned:
                    name = name[:hasAssigned.start()]
                name += noneUniquePrefix + str(noneUniqueIndex)
                allNames.add(name.lower())

            if isUnique and fn1 is None:
                corrName = None
            elif isUnique:
                corrName = fn1
            else:
                corrName = name+ext

            if keep == 'all' or isUnique:
                corrPathNames_out[p].append((fn0, corrName))
            else: # keep == 'first' and not isUnique
                pass
                #print(f'File {os.path.join(p, fn0)} will be excluded.')
        corrPathNames_out[p].sort(key=lambda x:x[0].lower())

    sortedNoneUnique = sorted(list(noneUnique))
    dups: dict[str, list[tuple[str, str, str|None]]] = {}
    for p, corrNames_in in corrPathNames_in.items():
        for nn in sortedNoneUnique:
            for n0, n1 in corrNames_in:
                nx = splitExt(n0)[0].lower()
                ny = splitExt(n1)[0]
                ny = (ny if ny is None else ny.lower())
                if nn in [nx, ny]:
                    isIncluded = False
                    for n0_o, n1_o in corrPathNames_out[p]:
                        if n0 == n0_o:
                            isIncluded = True
                            n1 = (n0 if n1_o is None else n1_o)
                            break
                    if not isIncluded: n1 = None
                    if nn not in dups:
                        dups[nn] = [(p, n0, n1)]
                    else: dups[nn].append((p, n0, n1))

    for dup, itemlist in dups.items():
        print(f'Found duplicated name {dup}:')
        for p, n0, n1 in itemlist:
            print('\t'+os.path.join(p, n0))
            if n1 is None:
                print('\t\t!!Will be EXCLUDED!!')
            else:
                if n1 == n0:
                    print('\t\t--> (no change) '+n1)
                else:
                    print('\t\t--> '+n1)

    if len(noneUnique) == 0:
        print('No possible duplication found in dir(s):')
        print('\t'+'\n'.join(corrPathNames_in.keys()))
    else:
        print(f'Found {len(dups)} none unique name(s), {len(uniqueNames)} unique one(s).')
    print(f'Total checked files: {count}\n')

    return corrPathNames_out

    
def checkCombine(
    paths: list[str],
    keep: Literal['first','all']='first'
) -> dict[str, list[tuple[str, None|str]]]:
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
    return checkDup(namesEachPath, keep=keep)