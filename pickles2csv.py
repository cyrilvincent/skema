import os
import config
import cyrilload

print("Pickles2CSV")
print("===========")
print(f"V{config.version}")
print()
print(f"Create data/ameli-all.csv")
with open(f"data/ameli-all.csv", "w", encoding="ISO-8859-1") as f:
    idset = set()
    f.write("id,name,fname,tel,convention,dept,specialite,vitale,adresse,honoraire\n")
    for item in os.listdir("data"):
        if item.endswith("pickle"):
            print(f"Load data/{item}")
            db = cyrilload.load(f"data/{item}")
            for id in db.keys():
                if id not in idset:
                    idset.add(id)
                    f.write(f"{id},")
                    e = db[id]
                    f.write(f"{e.name if e.name is not None else ''},")
                    f.write(f"{e.fname if e.fname is not None else ''},")
                    f.write(f"{e.phone if e.phone is not None else ''},")
                    f.write(f"{e.convention if e.convention is not None else ''},")
                    f.write(f"{e.dept if e.dept is not None else ''},")
                    f.write(f"{e.speciality if e.speciality is not None else ''},")
                    f.write(f"{1 if e.vitale else 0},")
                    f.write(f"{e.address if e.address is not None else ''},")
                    f.write(f"{e.honoraire if e.honoraire is not None else ''}\n")
print(f"Saved {len(idset)} rows in data/ameli-all.csv")
