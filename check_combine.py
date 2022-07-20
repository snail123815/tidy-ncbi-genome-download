from combine import checkCombine
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('p', nargs="+", help="pathes of databases (folders) you want to combine")

args = parser.parse_args()

checkCombine(args.p)