import os
import pandas as pd
from datetime import datetime
from collections import defaultdict
import psycopg2
from sqlalchemy import create_engine
from decimal import Decimal

class SteelDatabaseManager:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}')

    def save_dataframes(self, product_df, production_df, inventory_df, consumption_df):
        try:
            product_df.to_sql("product", self.engine, if_exists="append", index=False, method='multi')
            production_df.to_sql("production", self.engine, if_exists="append", index=False, method='multi')
            inventory_df.to_sql("inventory", self.engine, if_exists="append", index=False, method='multi')
            consumption_df.to_sql("consumption", self.engine, if_exists="append", index=False, method='multi')
            
            # Do NOT call self.conn.commit(), it's not needed here
            print("Data saved to PostgreSQL.")
        except Exception as e:
            print(f"Error saving data to PostgreSQL: {e}")
    
    def add_to_database(self, importer_i_df, product_i_df, transaction_df):
        try:
            # Step 1: Add new importers (check for duplicates by 'mst')
            try:
                existing_importers_df = pd.read_sql("SELECT DISTINCT mst FROM importer_i", self.engine)
                existing_mst = set(existing_importers_df['mst'])
                new_importers_df = importer_i_df[~importer_i_df['mst'].isin(existing_mst)]
            except Exception as e:
                print(f"Error reading existing importers: {e}")


            if not new_importers_df.empty:
                new_importers_df.to_sql("importer_i", self.engine, if_exists="append", index=False, method='multi')
                print(f"Added {len(new_importers_df)} new importers.")
            else:
                print("No new importers to add.")

            # Step 2: Insert products and retrieve their IDs
            
            try: 
                product_i_df.to_sql("product_i", self.engine, if_exists="append", index=False, method='multi')
            except Exception as e:
                print(f'Error at product_i: {e}')
            

            # Retrieve the latest product data to match and get `id`s
            existing_products_df = pd.read_sql("SELECT id, hs_code, country, address FROM product_i", self.engine)

            # Merge to find corresponding product_id for transaction_df
            merged = pd.merge(
                transaction_df,
                existing_products_df,
                how='left',
                on=['hs_code', 'country', 'address']
            )

            if merged['id'].isnull().any():
                missing = merged[merged['id'].isnull()]
                print("Warning: Some transactions refer to unknown products and will be skipped.")
                print(missing[['hs_code', 'country', 'address']])
                merged = merged.dropna(subset=['id'])

            merged = merged.rename(columns={'id': 'product_id'})
            try: 
                final_transaction_df = merged[['mst', 'quantity', 'unit_price', 'exchange_rate', 'amount', 'date', 'product_id', 'exporter']]
            except Exception as e:
                print(f'transaction df: {transaction_df.columns}')
                print(f'Error at final_transaction_df: {e}')


            # Step 3: Insert cleaned transaction data
            final_transaction_df.to_sql("transaction", self.engine, if_exists="append", index=False, method='multi')

            print("Data saved to PostgreSQL.")
            
        except Exception as e:
            print(f"Error saving data to PostgreSQL")


    def close(self):
        self.conn.close()

    def check_product_exists(self, product_type, company_name):
        try:
            cursor = self.conn.cursor()
            query = """SELECT EXISTS (
                SELECT 1 FROM Product WHERE ProductType = %s AND CompanyName = %s
            );"""
            cursor.execute(query, (product_type, company_name))
            exists = cursor.fetchone()[0]
            return bool(exists)
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def search_product_ID(self, product_type, company_name):
        try:
            product_type = product_type.strip().lower()
            company_name = company_name.strip().lower()

            query = """SELECT ID FROM Product 
                       WHERE LOWER(TRIM(ProductType)) = %s AND LOWER(TRIM(CompanyName)) = %s 
                       LIMIT 1"""
            cursor = self.conn.cursor()
            cursor.execute(query, (product_type, company_name))
            result = cursor.fetchone()
            return result[0] if result else None

        except Exception as e:
            print(f"Database error while searching product ID: {e}")
            return None

    def get_data(self, main_table, id, start_date, end_date):
        cur = self.conn.cursor()
        id_placeholders = ','.join(['%s'] * len(id))

        if main_table == "Domestic":
            query = f""" 
                SELECT Date, SUM(t.Amount), p.CompanyName, p.ProductType
                FROM Consumption t
                LEFT JOIN Product p ON t.ProductID = p.ID
                WHERE t.ProductID IN ({id_placeholders})
                  AND t.Date BETWEEN %s AND %s
                  AND t.Region IN ('Northern', 'Central', 'Southern')
                GROUP BY t.Date, p.CompanyName, p.ProductType
                ORDER BY t.Date
            """
        elif main_table == "Export":
            query = f""" 
                SELECT Date, t.Amount, p.CompanyName, p.ProductType
                FROM Consumption t
                LEFT JOIN Product p ON t.ProductID = p.ID
                WHERE t.ProductID IN ({id_placeholders})
                  AND t.Date BETWEEN %s AND %s
                  AND t.Region = 'Region'
                GROUP BY t.Date, p.CompanyName, p.ProductType
                ORDER BY t.Date
            """
        else:
            query = f"""
                SELECT Date, Amount, p.CompanyName, p.ProductType
                FROM {main_table} main
                JOIN Product p ON p.ID = main.ProductID
                WHERE p.ID IN ({id_placeholders})
                  AND main.Date BETWEEN %s AND %s
            """

        params = id + [start_date, end_date]
        cur.execute(query, params)
        companies_info = cur.fetchall()
        return self.to_chartjs_format(companies_info)

    def to_chartjs_format(self, rows):
        date_set = set()
        company_data = defaultdict(dict)

        for date, amount, company, product in rows:
            value = f"{company} - {product}"
            date_set.add(date)
            company_data[value][date] = amount

        sorted_dates = sorted(date_set, key=lambda d: datetime.strptime(d, "%Y-%m"))

        datasets = []
        for idx, (company, data_dict) in enumerate(company_data.items()):
            data = [data_dict.get(date, 0) for date in sorted_dates]
            datasets.append({
                'label': company,
                'data': data,
                'yAxisID': f'y{idx + 1}'
            })

        return {
            'labels': sorted_dates,
            'datasets': datasets
        }

    def pie_market_share(self, product_type: str, date: str):
        cursor = self.conn.cursor()
        query = """
        SELECT 
            p.companyname,
            SUM(c.amount) as total_amount
        FROM consumption c
        JOIN product p ON c.productid = p.id
        WHERE p.producttype = %s AND c.date = %s
        GROUP BY p.companyname
        ORDER BY total_amount DESC
        """
        cursor.execute(query, (product_type, date))
        rows = cursor.fetchall()

        labels = [company for company, _ in rows]
        data = [float(total) if isinstance(total, Decimal) else total for _, total in rows]


        return {
            "labels": labels,
            "data": data
        }
