import argparse
import pandas as pd
import os
from tqdm import tqdm

from tools import removeDup, getNumCtgs

def processArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('tsv', help="Path to the .tsv file generated by `-m` switch")
    parser.add_argument('dir', help="Path to the directory generated by `-o` parameter")
    parser.add_argument('--excludeList', help="Exclusion list file, one item per line",
                        default="")
    parser.add_argument('--maxCtg', type=int,
                        help="Maximum number of contigs that a genome will be kept.",
                        default=None)

    args = parser.parse_args()
    return args

def main():
    args = processArgs()
    downloadTsv = args.tsv
    downloadDir = args.dir
    excludeList = args.excludeList
    dirName = os.path.split(downloadDir)[1]

    try:
        with open(excludeList, 'r') as el:
            exclusions = [e.strip() for e in el.readlines()]
    except FileNotFoundError:
        print(f'File {excludeList} does not find.')
        exclusions = []

    infoDf = pd.read_csv(downloadTsv, sep='\t', header=0, index_col=0)

    # Data table to dict, check file existance
    strains = {}
    for acc, row in infoDf.iterrows():
        org = row.organism_name.strip()
        strain = str(row.infraspecific_name).replace( 'strain=', '').strip()
        # remove type strain: "type strain (a = b = c)"
        if "type strain (" in strain:
            strain = strain.replace('type strain (', '')[:-1]
        # some strain name are duplicated in orgnism name
        names = f'{org} {strain}'.split(' ')
        org = " ".join(names[:2])
        try:
            strain = removeDup(" ".join(names[2:]))
        except RecursionError:
            print(" ".join(names))
        name = f'{org} {strain}'

        filePath = os.path.join(downloadDir,
            row.local_filename.split(dirName)[1][1:])

        assert os.path.isfile(filePath)
        data = row.to_dict()
        data['local_filename'] = filePath
        try:
            strains[name][acc] = data
        except KeyError:
            strains[name] = {}
            strains[name][acc] = data

    # Classify data and store
    validAssemblies = {} # store target genome info [(acc, {data..}), (acc, {data...}), ...]
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
    

    # Filter base on genome quality
    if not args.maxCtg is None:
        print(f'Checking contig number of {len(validAssemblies)} sequences.')
        print(f'"Complete Genome" and "chromosome" level assembly will be skipped.')
        allKeys = list(validAssemblies.keys())
        for name in tqdm(allKeys):
            acc, assemblyData = validAssemblies[name]
            assemblyLevel = assemblyData['assembly_level']
            if assemblyLevel in ['Complete Genome', 'Chromosome']:
                continue
            n = getNumCtgs(assemblyData['local_filename'])
            if n > args.maxCtg:
                tooManyContigs.append((name, validAssemblies.pop(name)[0]))


if __name__ == "__main__":
    main()