import json

dict = {
    0: {
        "id": 0,
        "label": "Equipment root",
        "parentId": -1,
        "order": 0,
    }
}
s = "ABCDE"
parent = 0
key = 0
for i in range(5):
    key += 1
    dict[key] = {
        "id": key,
        "label": f"Equipment secondary {s[i]}",
        "shortLabel": s[i],
        "parentId": parent,
        "order": i,
        "leaf": False,
    }
    jparent = key
    for j in range(5):
        key += 1
        dict[key] = {
            "id": key,
            "label": f"Equipment {s[i]}-{s[j]}",
            "shortLabel": f"{s[i]}-{s[j]}",
            "parentId": jparent,
            "order": j,
            "leaf": False,
        }
        kparent = key
        for k in range(5):
            key += 1
            dict[key] = {
                "id": key,
                "label": f"Equipment {s[i]}-{s[j]}-{s[k]}",
                "shortLabel": f"{s[i]}-{s[j]}-{s[k]}",
                "parentId": kparent,
                "order": k,
                "leaf": False,
            }
            lparent = key
            for l in range(5):
                key += 1
                dict[key] = {
                    "id": key,
                    "label": f"Equipment {s[i]}-{s[j]}-{s[k]}-{s[l]}",
                    "shortLabel": f"{s[i]}-{s[j]}-{s[k]}-{s[l]}",
                    "parentId": lparent,
                    "order": l,
                    "leaf": False,
                }
                mparent = key
                for m in range(5):
                    key += 1
                    dict[key] = {
                        "id": key,
                        "label": f"Equipment {s[i]}-{s[j]}-{s[k]}-{s[l]}-{s[m]}",
                        "shortLabel": f"{s[i]}-{s[j]}-{s[k]}-{s[l]}-{s[m]}",
                        "parentId": mparent,
                        "order": m,
                        "leaf": True,
                    }

# print(dict)
json = json.dumps(dict, indent=True)
print(json)
with open("db.json", "w") as f:
    f.write(json)
