import pandas as pd

df = pd.read_csv("data/raw/aqi.csv")

print("\nColumns:\n")
print(df.columns.tolist())

print("\nFirst 5 rows:\n")
print(df.head())