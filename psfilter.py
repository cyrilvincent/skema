import pandas
import art
import config
import argparse
import re
import sys


def test1(dataframe):
    res = dataframe[dataframe[0] == "F"]
    return res


def test2(dataframe):
    res = dataframe[(dataframe[0] == "H") & (dataframe[1] == "VINCENT")]
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
    parser.add_argument("fn", help="Function name")
    args = parser.parse_args()
    regex = r"(\d{2})-(\d{2})"
    match = re.search(regex, args.path)
    if match is None:
        print("Bad file format, must have YY-MM")
        sys.exit(1)
    year = int(match[1])
    month = int(match[2])
    dataframe = pandas.read_csv(args.path, delimiter=";", header=None)
    s = f"{args.fn}(dataframe)"
    res = eval(s)
    res = res.assign(year=year)
    res = res.assign(month=month)
    print(res)
    file = args.path.replace(".csv", f"-{args.fn}.csv")
    res.to_csv(file, header=None, index=False)
    print(f"Saved {file}")
