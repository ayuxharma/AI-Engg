import pandas as pd
import json
import os

# read the csv file
df = pd.read_csv('data/sales.csv')
print("CSV Data:")
print(df)
print(f"\n Shape: {df.shape[0]} rows and {df.shape[1]} columns")

# calculate total for each row
df['Total'] = df['quantity'] * df['price']
print("\nData with Total:")
print(df)

# create output directory
os.makedirs('output', exist_ok=True)

# save as different formats

# json
df.to_json('output/sales_data.json', orient='records', indent=True)

# excel
df.to_excel('output/sales_data.xlsx', index=False)

# update the csv file with the new Total column
df.to_csv('output/sales_with_totals.csv', index=False)

print("\n Files saved:")
print(" - output/sales_data.json")
print(" - output/sales_data.xlsx")
print(" - output/sales_with_totals.csv")