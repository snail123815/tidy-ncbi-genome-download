import subprocess

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
