import config
import csv
import argparse

class SplitPS:

    def __init__(self):
        self.depts = list(range(1, 20)) + list(range(21, 96)) + [201, 202]
        self.db = {}
        for d in self.depts:
            self.db[d] = []

    def dept_from_cp(self, cp):
        dept = int(str(cp)[:2])
        if cp < 10000:
            dept = int(str(cp)[:1])
        elif 20200 > cp >= 20000:
            dept = 201
        elif 21000 > cp >= 20200:
            dept = 202
        return dept

    def load(self, path):
        print(f"Parse {path}")
        with open(path) as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                cp = int(row[7])
                dept = self.dept_from_cp(cp)
                if dept in self.depts:
                    self.db[dept].append(row)

    def save(self, path):
        for d in self.db.keys():
            dept = str(d)
            if d < 10:
                dept = "0" + dept
            elif d == 201:
                dept = "2A"
            elif d == 202:
                dept = "2B"
            file = path.replace(".csv", f"-{dept}.csv")
            print(f"Save {file}")
            with open(file, "w") as f:
                for row in self.db[d]:
                    f.write(";".join(row))
                    f.write("\n")


if __name__ == '__main__':
    print("SplitPS")
    print("=======")
    print(f"V{config.version}")
    parser = argparse.ArgumentParser(description="Split PS")
    parser.add_argument("path", help="Path")
    args = parser.parse_args()
    s = SplitPS()
    s.load(args.path)
    s.save(args.path)