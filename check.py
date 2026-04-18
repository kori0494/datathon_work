import pandas as pd


master = pd.read_csv("data/master_dataset.csv")

print(master.columns)

for column in master.columns:
    print(f"Column name: {column}")
    print(f"Blank cells: {master[column].isnull().sum()}")
    print(f"NaN cells: {master[column].isna().sum()}")