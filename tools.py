import subprocess
import os
from tqdm import tqdm
import pandas as pd
import shutil

def removeEqu(names):
    newNames = [removeDup(n) for n in names]
    names = newNames.copy()
    changed = False
    for i, n in enumerate(names):
        for j, r in enumerate(newNames):
            if n in r and n != r:
                newNames[j] = r.replace(n, '').strip()
                changed = True
    if changed:
        newNames = [n for n in newNames if n!=""]
        return removeEqu(newNames)
    else:
        return names

def removeDup(name):
    changed = False
    if "=" in name:
        name = " ".join(removeEqu([n.strip() for n in name.split("=")]))
        changed = True
    if name == "":
        return ""
    midi = int((len(name) - 1)/2)
    if name[midi] == " " and name[:midi] == name[midi+1:]:
        name = name[:midi]
        changed = True
    if changed:
        return removeDup(name)
    else:
        return name

def getNumCtgs(file):
    ext = file.split(".")[-2]
    faFmts = ['fna', 'fa', 'faa']
    gbFmts = ['gbff', 'gb', 'gbk', 'gpff']
    if ext in faFmts:
        return int(
            subprocess.check_output(
                f"gzip -cd {file} | grep \">\" | wc -l",
                shell=True
            ).decode().strip()
        )
    elif ext in gbFmts:
        return int(
            subprocess.check_output(
                f"gzip -cd {file} | grep \"LOCUS       \" | wc -l",
                shell=True
            ).decode().strip()
        )
    else:
        raise Exception(f'File format not known: {file}, should be one of {faFmts + gbFmts}')

def getInfoFrom(args):
    dirName = os.path.split(args.dir)[1]
    infoDf = pd.read_csv(args.tsv, sep='\t', header=0, index_col=0)

    # Data table to dict, check file existance
    strains = {}
    for acc, row in infoDf.iterrows():
        org = row.organism_name.strip()
        strain = str(row.infraspecific_name).replace( 'strain=', '').strip()
        # remove type strain: "type strain (a = b = c)" "type strain: a"
        if "type strain" in strain:
            strain = strain.replace('type strain', '').\
                replace(':', '').replace('(', '').replace(')', '').strip()
        # some strain name are duplicated in orgnism name
        names = f'{org} {strain}'.split(' ')
        org = " ".join(names[:2])
        strain = removeDup(" ".join(names[2:]))
        name = f'{org} {strain}'

        filePath = os.path.join(args.dir,
            row.local_filename.split(dirName)[1][1:])

        assert os.path.isfile(filePath), filePath
        data = row.to_dict()
        data['local_filename'] = filePath
        try:
            strains[name][acc] = data
        except KeyError:
            strains[name] = {}
            strains[name][acc] = data
    return strains

def getExclusion(excludeList):
    try:
        with open(excludeList, 'r') as el:
            exclusions = [e.strip() for e in el.readlines()]
    except FileNotFoundError:
        print(f'File {excludeList} does not find.')
        exclusions = []
    return exclusions

def filterTooManyCtgs(assemblies, maxCtg, tooManyContigs):
    if not maxCtg is None:
        # Filter base on genome quality
        print(f'\nChecking contig number of {len(assemblies)} sequences.')
        print(f'"Complete Genome" and "chromosome" level assembly will be skipped.')
        allKeys = list(assemblies.keys())
        for name in tqdm(allKeys):
            _, assemblyData = assemblies[name]
            assemblyLevel = assemblyData['assembly_level']
            if assemblyLevel in ['Complete Genome', 'Chromosome']:
                continue
            n = getNumCtgs(assemblyData['local_filename'])
            if n > maxCtg:
                tooManyContigs.append((name, assemblies.pop(name)[0]))
    return assemblies, tooManyContigs

def filterDownloads(strains, exclusions, maxCtg):
    validAssemblies = {} # store target genome info [(strain, {data..}), (strain, {data...}), ...]
    excludedAccs = [] # store excluded (by input) accessions: [("strain", "acc"), ("strain", "acc")...]
    skippedAccs  = [] # store accessions that are not the best for one strain name
    tooManyContigs = [] # store genomes that have too many contigs (if --maxCtg is set)
    for s in strains:
        inEx = False
        for ex in exclusions:
            if ex in s:
                inEx = True
                excludedAccs.extend([(s, acc) for acc in strains[s]])
                break
        if inEx: continue
        """Assembly level - the highest level of assembly for any object in the assembly:
        Complete genome - all chromosomes are gapless and have no runs of 10 or more ambiguous bases (Ns), there are no unplaced or unlocalized scaffolds, and all the expected chromosomes are present (i.e. the assembly is not noted as having partial genome representation). Plasmids and organelles may or may not be included in the assembly but if present then the sequences are gapless.
        Chromosome - there is sequence for one or more chromosomes. This could be a completely sequenced chromosome without gaps or a chromosome containing scaffolds or contigs with gaps between them. There may also be unplaced or unlocalized scaffolds.
        Scaffold - some sequence contigs have been connected across gaps to create scaffolds, but the scaffolds are all unplaced or unlocalized
        Contig - nothing is assembled beyond the level of sequence contigs"""

        if len(strains[s])>1:
            complete   = [(acc,strains[s][acc]) for acc in strains[s] if \
                strains[s][acc]['assembly_level'] == 'Complete Genome']
            chromosome = [(acc,strains[s][acc]) for acc in strains[s] if \
                strains[s][acc]['assembly_level'] == 'Chromosome']
            scaffold   = [(acc,strains[s][acc]) for acc in strains[s] if \
                strains[s][acc]['assembly_level'] == 'Scaffold']
            contig     = [(acc,strains[s][acc]) for acc in strains[s] if \
                strains[s][acc]['assembly_level'] == 'Contig']

            assert len(complete + chromosome + scaffold + contig) == len(strains[s])

            complete.sort(  key=lambda d: d[1]['seq_rel_date'], reverse=True)
            chromosome.sort(key=lambda d: d[1]['seq_rel_date'], reverse=True)
            scaffold.sort(  key=lambda d: d[1]['seq_rel_date'], reverse=True)
            contig.sort(    key=lambda d: d[1]['seq_rel_date'], reverse=True)

            sortedAssemblies = (complete + chromosome + scaffold + contig)
            topAssembly = sortedAssemblies[0]
            validAssemblies[s] = topAssembly
            skippedAccs.extend([(s, ass[0]) for ass in sortedAssemblies[1:]])
        else:
            validAssemblies[s] = strains[s].popitem()

    validAssemblies, tooManyContigs = filterTooManyCtgs(validAssemblies, maxCtg, tooManyContigs)

    return validAssemblies, excludedAccs, skippedAccs, tooManyContigs

def generateTargetDir(args):
    if args.targetDir is None:
        targetDir = os.path.realpath(args.dir) + "-ready"
    else: targetDir = os.path.realpath(args.targetDir)
    return targetDir


def gatherAssemblies(args):
    validAssemblies, excludedAccs, skippedAccs, tooManyContigs = \
        filterDownloads(getInfoFrom(args), getExclusion(args.excludeList), args.maxCtg)
    targetDir = generateTargetDir(args)
    print(f'\nCopying file to "{targetDir}"')
    for name in tqdm(validAssemblies):
        fp = validAssemblies[name][1]['local_filename']
        os.makedirs(targetDir, exist_ok=True)
        t = os.path.join(targetDir, os.path.split(fp)[1])
        shutil.copy(fp, t)

    includeListFile = os.path.realpath(targetDir) + '-included.tsv'
    with open(includeListFile, 'w') as ef:
        ef.write('List of accessions in source dir:\n')
        ef.write(os.path.realpath(args.dir)+'\n')
        ef.write('Included in:\n')
        ef.write(targetDir+'\n')
        for strain, strainData in validAssemblies.items():
            ef.write('\n'+strain+'\t'+strainData[0])

    excludeListFile = os.path.realpath(targetDir) + '-excluded.tsv'
    with open(excludeListFile, 'w') as ef:
        ef.write('List of accessions in source dir:\n')
        ef.write(os.path.realpath(args.dir)+'\n')
        ef.write('but excluded in:\n')
        ef.write(targetDir+'\n')
        for text, excludedList in [
                ('Excluded by --excludeList', excludedAccs),
                ('Excluded because not the best for the strain', skippedAccs),
                ('Excluded because the assembly has too many contigs', tooManyContigs),
        ]:
            ef.write('\n'+text+'\n')
            for strain, acc in excludedList:
                ef.write(f'{strain}\t{acc}\n')

    return os.listdir(targetDir), includeListFile, excludeListFile
