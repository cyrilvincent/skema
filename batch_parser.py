import os

path = "data/ps"
# path = "data/UFC"
# path = "data/etalab"
exe = "ps_parser.py"
# exe = "ps_tarif_parser.py"
# exe = "etalab_parser.py"

print("Batch Parser")
print()

l = os.listdir(path)
l.sort()
for f in l:
    if f.endswith(".csv"):
        try:
            yy = int(f[-9:-7])
            mm = int(f[-6:-4])
        except:
            print(f"Exclude {f}: bad date")
            continue
        ds = yy * 100 + mm
        if ds >= 0:
            s = f'python {exe} "{path}/{f}"'
            print(s)
            code = os.system(s)
            if code != 0:
                print(f"Error {code}, stopping")
                quit(code)
            print()
        else:
            print(f"Exclude {f}")

