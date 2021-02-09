import os
import config
import cyrilload
import re
import shutil
import datetime

def get_dept_from_cp(cp):
    dept = cp[:2]
    if int(dept) > 96 and int(dept) < 98:
        dept = cp[:3]
    elif dept == "20":
        dept = "2A" if int(cp) < 20200 else "2B"
    return dept

if __name__ == '__main__':
    print("Pickles2CSV")
    print("===========")
    print(f"V{config.version}")
    print()
    print(f"Create data/ameli-all.csv")
    with open(f"data/ameli-all.csv", "w", encoding="utf8") as f:
        idset = set()
        f.write("id,name,fname,tel,convention,dept,specialite,vitale,adresse,cp,honoraire\n")
        for item in os.listdir("data"):
            if item.endswith("pickle"):
                print(f"Load data/{item}")
                db = cyrilload.load(f"data/{item}")
                for id in db.keys():
                    if id not in idset:
                        e = db[id]
                        cp = ""
                        dept = None
                        e.dept = str(e.dept)
                        if e.address is not None:
                            match = re.search(r'(\d{5})\s\w', e.address)
                            cp = match[1]
                            dept = get_dept_from_cp(cp)
                        if dept != "98" and dept != "99" and dept != "00":
                            if dept is not None and (e.dept == "" or e.dept is None or e.dept != dept):
                                print(f"Dept {e.dept}=>{dept}")
                                e.dept = dept
                            idset.add(id)
                            f.write(f"{id},")
                            f.write(f"{e.name if e.name is not None else ''},")
                            f.write(f"{e.fname if e.fname is not None else ''},")
                            f.write(f"{e.phone if e.phone is not None else ''},")
                            f.write(f"{e.convention if e.convention is not None else ''},")
                            f.write(f"{e.dept if e.dept is not None else ''},")
                            f.write(f"{e.speciality if e.speciality is not None else ''},")
                            f.write(f"{1 if e.vitale else 0},")
                            f.write(f"{e.address if e.address is not None else ''},")
                            f.write(f"{cp},")
                            # To remove because parser bug for dept<50
                            if e.honoraire is not None and e.honoraire.startswith("<a alt="):
                                e.honoraire = "Conventionné"
                            f.write(f"{e.honoraire if e.honoraire is not None else ''}\n")

    dt = datetime.datetime.now()
    print(f"Saved {len(idset)} rows in data/ameli-{dt.strftime('%y%m%d')}-{len(idset)}.csv")
    shutil.copy2("data/ameli-all.csv", f"data/ameli-{dt.strftime('%y%m%d')}-{len(idset)}.csv")
