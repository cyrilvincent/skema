import os

path = "data/ps"
path = "data/UFC"
# path = "data/SanteSpecialite"
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
            s = f'python ps_tarif_parser.py "{path}/{f}"'
            print(s)
            code = os.system(s)
            if code != 0:
                quit(code)
            print()
        else:
            print(f"Exclude {f}")
