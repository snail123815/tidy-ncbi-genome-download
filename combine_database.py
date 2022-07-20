from combine import combineDatabases
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('p', nargs="+", help="pathes of databases (folders) you want to combine")
parser.add_argument('-t', type=str, help='target dir to store combined files')
parser.add_argument('--keep', type=str, help='If duplicated file names found, keep "first" or "all"')

args = parser.parse_args()

combineDatabases(args.p, args.t, keep=args.keep)