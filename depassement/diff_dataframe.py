import argparse
import pandas as pd

parser = argparse.ArgumentParser(description="Diff Dataframe")
parser.add_argument("file1", help="File 1")
parser.add_argument("file2", help="File 2")
parser.add_argument("-r", "--round", help="Round", type=int, default=1)
args = parser.parse_args()
print(f"Loading {args.file1}")
df1 = pd.read_csv(args.file1)
print(f"Loading {args.file2}")
df2 = pd.read_csv(args.file2)
nb_col1 = len(df1.columns)
nb_col2 = len(df2.columns)
print(f"Nb columns: {nb_col1} vs {nb_col2} => {'OK' if nb_col1 == nb_col2 else 'ERROR'}")
nb_row1 = len(df1)
nb_row2 = len(df2)
print(f"Nb rows: {nb_row1} vs {nb_row2} => {'OK' if nb_row1 == nb_row2 else 'ERROR'}")
df1 = df1.fillna(9999).round(args.round)
df2 = df2.fillna(9999).round(args.round)
diff = df1 - df2
print("Generate diff.html")
diff.to_html("diff.html")

# ../data/depassement/Rendus_PartIII/dépassements_anest.csv ../data/depassement/out/out_Anest.csv