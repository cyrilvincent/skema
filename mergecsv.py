import config
import os
import time
import argparse


if __name__ == '__main__':
    print("Merge CSVs")
    print("==========")
    print(f"V{config.version}")
    print()
    parser = argparse.ArgumentParser(description="Merge CSVs")
    parser.add_argument("dir", help="Directory")
    parser.add_argument("-e", "--ext", help="extension, eg csv (default)")
    parser.add_argument("-p", "--prefix", help="file prefix, eg adresses")
    args = parser.parse_args()
    time0 = time.perf_counter()
    nb = 0
    ext = "csv" if args.ext is None else args.ext
    pre = "" if args.prefix is None else args.prefix
    print(f"Open {pre}merged.csv")
    with open(f"{args.dir}/{pre}merged.csv", "w") as f:
        print(f"Scan {args.dir}/{pre}*.{ext}")
        for item in os.listdir(args.dir):
            if item.endswith(f".{ext}") and item.startswith(pre) and "merged" not in item:
                nb += 1
                print(f"Parse {item} ({nb} files) in {int(time.perf_counter() - time0)}s")
                with open(f"{args.dir}/{item}") as g:
                    l = g.readlines()
                    if nb == 1:
                        f.write(l[0])
                    if len(l) > 1:
                        for row in l[1:]:
                            f.write(row)
    print(f"Saved {pre}merged.csv from {nb} files in {int(time.perf_counter() - time0)}s")
