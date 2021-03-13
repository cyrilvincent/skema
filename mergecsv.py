import config
import os
import time
import argparse

class MergeCSV:
    """
    Fusionne des CSV
    """

    def merge(self, path, ext, prefix, noheader):
        """
        Fusion
        :param path: le répertoire à fusionner
        :param ext: l'extension des fichiers
        :param prefix: le préfixe des fichiers
        :param noheader: présence d'un header
        :return le nombre de fichier fusionné
        """
        nb = 0
        with open(f"{path}/{prefix}merged.csv", "w", encoding="utf8") as f:
            print(f"Scan {path}/{prefix}*.{ext}")
            for item in os.listdir(path):
                if item.endswith(f".{ext}") and item.startswith(prefix) and "merged" not in item:
                    nb += 1
                    print(f"Parse {item} ({nb} files) in {int(time.perf_counter() - time0)}s")
                    with open(f"{args.dir}/{item}", encoding="utf8") as g:
                        l = g.readlines()
                        if (nb == 1 or noheader) and len(l) > 0:
                            f.write(l[0])
                        if len(l) > 1:
                            for row in l[1:]:
                                f.write(row)
        return nb


if __name__ == '__main__':
    print("Merge CSVs")
    print("==========")
    print(f"V{config.version}")
    print()
    parser = argparse.ArgumentParser(description="Merge CSVs")
    parser.add_argument("dir", help="Directory")
    parser.add_argument("-e", "--ext", help="extension, eg csv (default)")
    parser.add_argument("-p", "--prefix", help="file prefix, eg adresses")
    parser.add_argument("-h", "--noheader", help="No header", action="store_true")
    args = parser.parse_args()
    time0 = time.perf_counter()
    ext = "csv" if args.ext is None else args.ext
    pre = "" if args.prefix is None else args.prefix
    print(f"Open {pre}merged.csv")
    m = MergeCSV()
    nb = m.merge(args.dir, ext, pre, args.noheader)
    print(f"Saved {pre}merged.csv from {nb} files in {int(time.perf_counter() - time0)}s")
