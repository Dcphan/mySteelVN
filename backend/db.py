import os
import pandas as pd
from datetime import datetime
from collections import defaultdict
import psycopg2
from sqlalchemy import create_engine, text
from decimal import Decimal
from backend.ETL_pipeline import hs_code
import numpy as np

COLUMN_TABLE_MAP = {
    "exporter": "transaction",
    "date": "transaction",
    "mst": "transaction",
    "commodity": "product_i",
    "hs_code": "product_i",
    "country": "product_i",
    "company": "importer_i",
    "address": "importer_i"
}

TABLE_JOIN_SQL = {
    "transaction": "",
    "product_i": """
        JOIN transaction t ON p.id = t.product_id
    """,
    "importer_i": """
        JOIN transaction t ON i.mst = t.mst
    """
}

TABLE_ALIAS_MAP = {"transaction": "t", "product_i": "p", "importer_i": "i"}

class SteelDatabaseManager:
    def __init__(self, dbname, user, password, host=192.168.10.96, port=5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}')

# File Sản Lượng

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
            print(f"Error saving data to PostgreSQL: {str(e)}")


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
    


# File Xuất Nhập Khẩu
    def xnk_get_total_data(self, category, date, item:list):

        placeholders = ', '.join(['%s'] * len(item))

        query = f"""
            SELECT * FROM (
                SELECT 
                    p.{category}, 
                    ROUND(SUM(tr.amount)::numeric, 2) AS amount, 
                    ROUND(SUM(tr.quantity)::numeric, 0) AS quantity
                FROM transaction tr
                JOIN product_i p ON tr.product_id = p.id
                WHERE tr.date = %s AND p.{category} IN ({placeholders})
                GROUP BY p.{category}

                UNION ALL

                SELECT 
                    'TOTAL' AS {category}, 
                    ROUND(SUM(tr.amount)::numeric, 2) AS amount, 
                    ROUND(SUM(tr.quantity)::numeric, 0) AS quantity
                FROM transaction tr
                JOIN product_i p ON tr.product_id = p.id
                WHERE tr.date = %s AND p.{category} IN ({placeholders})
            ) AS combined
            ORDER BY CASE WHEN {category} = 'TOTAL' THEN 0 ELSE 1 END;
        """

        # Construct parameter list: [date, *item, date, *item]
        params = tuple([date] + item + [date] + item)

        df = pd.read_sql(query, self.engine, params=params)
        return df.to_dict(orient="records")
    
    def get_distinct_commodities(self, column):
        try:
            query = text(f"SELECT DISTINCT {column} FROM product_i;")
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"Error fetching distinct commodities: {e}")
            return []
        
    def xnk_get_info(self, filter_field, filter_value, rows_fields: list, rows_values, date):
        # Resolve which tables each column comes from
        fixed_table = COLUMN_TABLE_MAP[filter_field]
        variable_table_1 = COLUMN_TABLE_MAP[rows_fields[0]]
        variable_table_2 = COLUMN_TABLE_MAP[rows_fields[1]]




        # Resolve aliases for both fields
        fixed_alias = TABLE_ALIAS_MAP[fixed_table]
        variable_alias_1 = TABLE_ALIAS_MAP[variable_table_1]
        variable_alias_2 = TABLE_ALIAS_MAP[variable_table_2]


        # Prepare parameter placeholders
        placeholders = ','.join(['%s'] * len(rows_values))
        params = [filter_value] + rows_values + [date] + [filter_value] + rows_values + [date]

        # SQL SELECT fields
        select_fields = f"{variable_alias_1}.{rows_fields[0]}, {variable_alias_2}.{rows_fields[1]}, SUM(t.quantity) AS total_quantity"
        total_select_fields = f"{variable_alias_1}.{rows_fields[0]}, 'TOTAL' AS {rows_fields[1]}, SUM(t.quantity) AS total_quantity"

        # Final SQL query
        query = f"""
            SELECT *
            FROM (
                SELECT 
                    {select_fields}
                FROM transaction t
                JOIN product_i p ON p.id = t.product_id
                JOIN importer_i i ON i.mst = t.mst
                WHERE {fixed_alias}.{filter_field} = %s
                AND {variable_alias_1}.{rows_fields[0]} IN ({placeholders})
                AND t.date = %s
                GROUP BY {variable_alias_1}.{rows_fields[0]}, {variable_alias_2}.{rows_fields[1]}

                UNION ALL

                SELECT 
                    {total_select_fields}
                FROM transaction t
                JOIN product_i p ON p.id = t.product_id
                JOIN importer_i i ON i.mst = t.mst
                WHERE {fixed_alias}.{filter_field} = %s
                AND {variable_alias_1}.{rows_fields[0]} IN ({placeholders})
                AND t.date = %s
                GROUP BY {variable_alias_1}.{rows_fields[0]}
            ) AS combined
            ORDER BY 
                {rows_fields[0]},
                CASE WHEN {rows_fields[1]} = 'TOTAL' THEN 1 ELSE 0 END,
                {rows_fields[1]};
        """

        print(query)
        print(params)

        df = pd.read_sql(query, self.engine, params=tuple(params))

        # Clean NaN/inf to avoid JSON errors
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(how='any', inplace=True)

        return df.to_dict(orient="records")

   
   # delete later:
    
    def xnk_get_distinct_filter(self, filter, date):
        table = COLUMN_TABLE_MAP.get(filter)
        if table is None:
            raise ValueError(f"Invalid filter: {filter}")

        alias = TABLE_ALIAS_MAP[table]
        join_clause = TABLE_JOIN_SQL.get(table, "")

        try:
            # Base SQL
            sql = f"""
                SELECT DISTINCT {alias}.{filter}
                FROM {table} {alias}
                {join_clause}
            """

            params = {}

            # Add date filter only if date is not None
            if date:
                sql += " WHERE t.date = :date"
                params["date"] = date

            sql += f" ORDER BY {alias}.{filter};"

            query = text(sql)

            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"Error fetching distinct {filter}: {e}")
            return []

    

    def get_XNK_data(self, date: list):
        placeholders = ', '.join(['%s'] * len(date))
        
        query = f"""
        SELECT 
            t.mst, 
            t.quantity, 
            t.unit_price, 
            t.exchange_rate, 
            t.amount, 
            t.date,  
            t.exporter, 
            i.company AS importer,
            i.address,
            p.commodity,
            p.hs_code,
            p.country
        FROM transaction t
        JOIN product_i p ON p.id = t.product_id
        JOIN importer_i i ON i.mst = t.mst
        where t.date in ({placeholders});
        """

        param = tuple(date)

        df = pd.read_sql(query, self.engine, params=param)
        return df
