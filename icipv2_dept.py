import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sqlalchemy
import sqlentities
import csv
import config
import art

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Sql Dept")
    print("========")
    print(f"V{config.version}")
    print(config.copyright)
    print()

    context = sqlentities.Context()
    context.create()

    depts = list(range(1, 20)) + list(range(21, 96)) + [201, 202]

    for d in depts:
        dept = sqlentities.Dept()
        dept.id = d
        dept.num = str(d)
        if len(dept.num) < 2:
            dept.num = "0" + dept.num
        elif d == 201:
            dept.num = "2A"
        elif d == 202:
            dept.num = "2B"
        print(f"Creating {dept}")
        context.session.add(dept)
        context.session.commit()




