import os
import psycopg2
import pandas as pd
from datetime import datetime
from collections import defaultdict
from xlsxwriter import Workbook


class Export:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

    def read_df(self, category):
        if category == "Export":
            query = f"""
                SELECT
                    t.date AS month,
                    p.companyname,
                    p.producttype,
                    t.amount
                FROM consumption t
                LEFT JOIN product p ON t.productid = p.id
                WHERE t.region = 'Export'
                GROUP BY month, p.companyname, p.producttype, t.amount
                ORDER BY month
            """
        elif category == "Domestic":
            query = f"""
                SELECT
                    t.date AS month,
                    p.companyname,
                    p.producttype,
                    SUM(t.amount) AS amount
                FROM consumption t
                LEFT JOIN product p ON t.productid = p.id
                WHERE t.region IN ('Northern', 'Central', 'Southern')
                GROUP BY t.date, p.companyname, p.producttype
                ORDER BY t.date
            """                            
        else:
            query = f"""
                SELECT 
                    t.date AS month,
                    p.companyname,
                    p.producttype,
                    t.amount
                FROM {category.lower()} t
                LEFT JOIN product p ON t.productid = p.id
                GROUP BY month, p.companyname, p.producttype, t.amount
                ORDER BY month
            """
        df_read = pd.read_sql_query(query, self.conn)
        return df_read

    def change_to_pivot(self, df):
        pivot = df.pivot_table(
            index=['companyname', 'producttype'],
            columns='month',
            values='amount',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        pivot.columns.name = None  # remove pivot index name
        pivot = pivot.sort_index(axis=1)  # sort columns if needed

        new_order = ['producttype', 'companyname'] + [col for col in pivot.columns if col not in ('companyname', 'producttype')]
        pivot = pivot[new_order]

        return pivot

    def convert_to_excel(self, excel_file_path: str) -> bool:
        output_dir = os.path.dirname(excel_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            inventory_df = self.read_df('Inventory')
            production_df = self.read_df('Production')
            export_df = self.read_df('Export')
            domestic_df = self.read_df('Domestic')

            inventory_pivot = self.change_to_pivot(inventory_df)
            production_pivot = self.change_to_pivot(production_df)
            export_pivot = self.change_to_pivot(export_df)
            domestic_pivot = self.change_to_pivot(domestic_df)

            with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
                inventory_pivot.to_excel(writer, sheet_name='Inventory', index=False)
                production_pivot.to_excel(writer, sheet_name='Production', index=False)
                export_pivot.to_excel(writer, sheet_name='Export', index=False)
                domestic_pivot.to_excel(writer, sheet_name='Domestic', index=False)
            return True
        except Exception as e:
            print(f"Error converting data to Excel: {e}")
            return False

    def get_all_pivot_data(self):
        data = {}
        df_inventory = self.read_df('Inventory')
        df_production = self.read_df('Production')
        df_export = self.read_df('Export')
        df_domestic = self.read_df('Domestic')

        data['Inventory'] = self.change_to_pivot(df_inventory).to_dict(orient='records')
        data['Production'] = self.change_to_pivot(df_production).to_dict(orient='records')
        data['Export'] = self.change_to_pivot(df_export).to_dict(orient='records')
        data['Domestic'] = self.change_to_pivot(df_domestic).to_dict(orient='records')
        return data

