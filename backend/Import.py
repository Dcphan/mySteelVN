import pandas as pd
import os
import re
from datetime import datetime
import uuid
from backend.db import SteelDatabaseManager


class SteelDataProcessor:
    def __init__(self, file_path, skiprows=7):
        self.file_path = file_path
        self.skiprows = skiprows
        self.df = None
        self.date = self.extract_date_from_filename()
        self.db_manager = SteelDatabaseManager(dbname="neondb", user="neondb_owner", password="npg_3vSCDycG9jUQ")

        # Output DataFrames
        self.product_df = pd.DataFrame(columns=['id', 'producttype', 'companyname'])
        self.production_df = pd.DataFrame(columns=['productid', 'date', 'amount'])
        self.inventory_df = pd.DataFrame(columns=['productid', 'date', 'amount'])
        self.consumption_df = pd.DataFrame(columns=['productid', 'date', 'amount', 'region'])

        # Product ID Counter
        self.product_id_counter = 1

    def load_data(self):
        try:
            self.df = pd.read_excel(self.file_path, skiprows=self.skiprows)
            print("File loaded successfully.")
        except Exception as e:
            print(f"Failed to load Excel file: {e}")
            self.df = None

    def reformat(self):
        if self.df is None:
            print("No DataFrame loaded to reformat.")
            return None

        try:
            non_nan_header = self.df.columns[self.df.iloc[0].notna()]
            non_nan_value = self.df[non_nan_header].iloc[0].values

            new_column_names = {
                old_col: new_name for old_col, new_name in zip(non_nan_header, non_nan_value)
            }

            self.df.rename(columns=new_column_names, inplace=True)
            self.df.drop(self.df.index[0], inplace=True)

            for col in ['Ticker', 'Total']:
                if col in self.df.columns:
                    self.df.drop(columns=[col], inplace=True)

            if 'Production' in self.df.columns:
                self.df.dropna(subset=['Production'], inplace=True)
            else:
                print("Cột 'Production' không tồn tại trong DataFrame.")

            self.df.reset_index(drop=True, inplace=True)
            print("DataFrame reformatted successfully.")
            return self.df

        except Exception as e:
            print(f"Error during reformatting: {e}")
            return self.df

    def extract_date_from_filename(self):
        match = re.search(r'(\d{4}-\d{1,2})', self.file_path)
        if match:
            year_month = match.group(1)
            date_obj = datetime.strptime(year_month, "%Y-%m")
            standardized = date_obj.strftime("%Y-%m")
            return standardized
        return None

    def process_all_rows(self):
        if self.df is None:
            print("Data not loaded.")
            return

        for i in range(3, len(self.df)):  # Bỏ qua 3 hàng đầu
            self._process_single_row(i)

    def _process_single_row(self, index):
        try:
            if index < 2:
                return

            def normalize(name):
                return str(name).strip().lower()

            name = normalize(self.df['Company Name'][index])
            target_products = ["hot steel coil", "cool steel coil","steel black pipe", "steel coated pipe","steel gal", "steel painted", "steel other"]

            if name in target_products:
                # Walk back to find the most recent company name
                i = index - 1
                company_name = None

                while i >= 0:
                    candidate = normalize(self.df['Company Name'][i])
                    if candidate not in target_products and candidate != "total":
                        company_name = self.df['Company Name'][i]
                        break
                    i -= 1

                if company_name is None:
                    return  # Couldn't find a valid company

                company_name_clean = normalize(company_name)
                product = [name, company_name_clean]

                # Try to find existing ID
                if not self.db_manager.check_product_exists(product[0], product[1]):
                    pro_id = self.db_manager.search_product_ID(product[0], product[1])

                    if not pro_id:
                        # Not found, generate new ID and insert
                        pro_id = str(uuid.uuid4())
                        self.product_df.loc[len(self.product_df)] = [pro_id, name, company_name]
                else:
                    pro_id = self.db_manager.search_product_ID(product[0], product[1])
                    if not pro_id:
                        print(f"Warning: Product exists but no ID found for ({product[0]}, {product[1]})")
                        return

                # Add production & inventory values
                prod_value = self.df['Production'].fillna(0)[index]
                inv_value = self.df['Inventory'].fillna(0)[index]
                self.add_data_to_table(pro_id, index, prod_value, inv_value)

        except Exception as e:
            print(f"Error processing row {index}: {e}")

    def add_data_to_table(self, pro_id, index, prod_value, inv_value, ):
        self.production_df.loc[len(self.production_df)] = [pro_id, self.date, prod_value]
        self.inventory_df.loc[len(self.inventory_df)] = [pro_id, self.date, inv_value]

        for region in ['Northern', 'Central', 'Southern', 'Export']:
            consumption_value = self.df[region].fillna(0)[index]
            self.consumption_df.loc[len(self.consumption_df)] = [pro_id, self.date, consumption_value, region]

    def get_dataframe(self):
        return self.product_df, self.production_df, self.inventory_df, self.consumption_df

    def import_function(self):
        self.load_data()
        self.reformat()
        self.process_all_rows()
        self.db_manager.save_dataframes(self.product_df, self.production_df, self.inventory_df, self.consumption_df)
        self.db_manager.close()
