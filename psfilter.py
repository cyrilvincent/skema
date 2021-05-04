import pandas
import art
import config
import argparse
import re
import sys
import repositories


def test1(dataframe):
    res = dataframe[dataframe[0] == "F"]
    return res


def test2(dataframe, name):
    res = dataframe[(dataframe[0] == "H") & (dataframe[1] == name)]
    return res

def opthtalmo_secteur1(dataframe):
    res = dataframe[(dataframe[10] == 56) & (dataframe[13] == "c1")]
    return res


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("PS Filter")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    parser = argparse.ArgumentParser(description="PS filter")
    parser.add_argument("path", help="Path")
    parser.add_argument("fn", help="Function call")
    parser.add_argument("-s", "--save", action="store_true", help="Save result")
    args = parser.parse_args()
    regex = r"(\d{2})-(\d{2})"
    match = re.search(regex, args.path)
    if match is None:
        print("Bad file format, must have YY-MM")
        sys.exit(1)
    year = int(match[1])
    month = int(match[2])
    repo = repositories.PSRepository()
    dataframe = repo.get_dataframe(args.path)
    res = eval(args.fn)  # data/ps/ps-tarifs-21-03-adresses.csv test2(dataframe,'VINCENT')
    res = res.assign(year=year).assign(month=month)
    print(res)
    if args.save:
        file = args.path.replace(".csv", f"-{args.fn}.csv")
        file = file.replace("<", "lt;").replace(">", "gt;").replace(":", "").replace("*", "").replace("|", "OR")
        repo.save_csv_from_dataframe(res, file)
        print(f"Saved {file}")
