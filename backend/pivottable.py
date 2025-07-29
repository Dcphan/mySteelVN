import pandas as pd
import os
from backend.db import SteelDatabaseManager
import time
import json
from collections import defaultdict

db_manager = SteelDatabaseManager(dbname="steel_database", user="mysteelvn", password="cjLVuBdaSd5vtst")

class pivotTable:
    def __init__(self):
        self.df = None

    def set_df(self, date: list):
        self.df = db_manager.get_XNK_data(date=date)

    def get_df(self):
        return self.df
    
    def create_pivot(self, row, column=None, value=None):
        if self.df is None:
            raise ValueError("Data not loaded. Call set_df(date) first.")
        
        pivot = self.df.pivot_table(index=row, columns=column, values=value, aggfunc='sum', fill_value=0)
        return pivot
    
    def create_pivot_json(self, row, column=None, value=None):
        if self.df is None:
            raise ValueError("Data not loaded. Call set_df(date) first.")
        
        # Create pivot table
        pivot = self.df.pivot_table(index=row, columns=column, values=value, aggfunc='sum', fill_value=0)

        # Flatten MultiIndex columns
        if isinstance(pivot.columns, pd.MultiIndex):
            pivot.columns = ['_'.join(map(str, col)).strip() for col in pivot.columns]
        else:
            pivot.columns = [str(col) for col in pivot.columns]

        pivot.reset_index(inplace=True)

        # Optional: rename quantity columns if there's only one

        
        return pivot.to_dict(orient='records')  
    
    def add_pivot_total(self, data: list[dict]) -> list[dict]:
        pivot_total = defaultdict(lambda: defaultdict(float))
        final_output = []
        key = list(data[1].keys())
        print(type(key))

        for row in data:
            
            
            firstKey = row.get(key[0])
            final_output.append(row)

            # Sum up only numeric fields with "amount" or "quantity"
            for key, value in row.items():
                if key.startswith("amount") or key.startswith("quantity"):
                    pivot_total[firstKey][key] += value

        # Append total row for each country
        for firstKey, totals in pivot_total.items():
            total_row = {key[0]: firstKey, key[1]: "TOTAL"}
            total_row.update(totals)
            final_output.append(total_row)

        return final_output




