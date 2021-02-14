import unidecode
import re
import csv
import cyrilload
import difflib
import config
import entities
import time
import argparse
import special

time0 = time.perf_counter()

nb = 0
nbnocp = 0
nbbp = 0
nbcedex = 0
nbnonum = 0

print("Load data/ameli/ameli-all.csv")
with open("data/ameli/ameli-all.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        nb += 1
        adresse = row["adresse"].replace("<br/>", " ").upper()
        regex = r"\d{5}"
        match = re.search(regex, adresse)
        if match is None:
            nbnocp += 1
        if " BP" in adresse:
            nbbp += 1
        if "CEDEX" in adresse:
            nbcedex += 1
        regex = r"\d+.+\d{5}"
        match = re.search(regex, adresse)
        if match is None:
            nbnonum += 1
print(f"Nb adresses: {nb}")
print(f"Nb No CP: {nbnocp} ({nbnocp * 100 / nb:.1f}%)")
print(f"Nb Cedex: {nbcedex} ({nbcedex * 100 / nb:.1f}%)")
print(f"Nb BP: {nbbp} ({nbbp * 100 / nb:.1f}%)")
print(f"Nb Bad CP min: {nbbp + nbnocp+ nbcedex} ({(nbbp + nbnocp+ nbcedex) * 100 / nb:.1f}%)")
print(f"No Num: {nbnonum} ({nbnonum * 100 / nb:.1f}%)")


