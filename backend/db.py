import os
import pandas as pd
from datetime import datetime
from collections import defaultdict
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
from decimal import Decimal
from backend.ETL_pipeline import hs_code
import numpy as np
import time
import math 

IMPORTER_COLUMN_TABLE_MAP = {
    "exporter": "transaction",
    "date": "transaction",
    "mst": "transaction",
    "commodity": "product_i",
    "hs_code": "product_i",
    "country": "product_i",
    "company": "importer_i",
    "address": "importer_i"
}
EXPORTER_COLUMN_TABLE_MAP = {
    "importer": "transaction_e",
    "date": "transaction_e",
    "mst": "transaction_e",
    "commodity": "product_e",
    "hs_code": "product_e",
    "country": "product_e",
    "company": "exporter_e",
    "address": "exporter_e"
}


TABLE_JOIN_SQL = {
    "transaction": "",
    "transaction_e": "",
    "product_e": """
        JOIN transaction t ON p.id = t.product_id
    """,
    "product_i": """
        JOIN transaction t ON p.id = t.product_id
    """,
    "importer_i": """
        JOIN transaction t ON i.mst = t.mst
    """,
    "exporter_e": """
        JOIN transaction t ON e.mst = t.mst
    """
}

TABLE_ALIAS_MAP = {"transaction": "t", "transaction_e": "t", "product_e": "p", "product_i": "p", "importer_i": "i", "exporter_e": "e"}

class SteelDatabaseManager:
    def __init__(self, dbname, user, password, host='ep-fragrant-block-a1p5gndb-pooler.ap-southeast-1.aws.neon.tech', port=5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require'
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
    
    def add_importer_to_database(self, importer_i_df, product_i_df, transaction_df):
        
        try:
            
            print("Starting add_to_database...")
            total_start = time.time()

            # Step 1: Add new importers
            step_start = time.time()
            try:
                existing_importers_df = pd.read_sql(text("SELECT DISTINCT mst FROM importer_i"), self.engine)
                existing_mst = set(existing_importers_df['mst'])
                new_importers_df = importer_i_df[~importer_i_df['mst'].isin(existing_mst)]
            except Exception as e:
                print(f"[{time.time() - step_start:.2f}s] Error reading existing importers: {e}")
                new_importers_df = pd.DataFrame()

            if not new_importers_df.empty:
                print(f"Inserting {len(new_importers_df)} new importers...")
                new_importers_df.to_sql("importer_i", self.engine, if_exists="append", index=False, method='multi')
                print(f"[{time.time() - step_start:.2f}s] Added new importers.")
            else:
                print(f"[{time.time() - step_start:.2f}s] No new importers to add.")

            # Step 2: Deduplicate and insert product data
            step_start = time.time()
            try:
                print("Checking for duplicate products...")
                
                required_columns = ['hs_code', 'country', 'address', 'place_of_r', 'place_of_l', 'product_description']
                missing_cols = [col for col in required_columns if col not in product_i_df.columns]

                if missing_cols:
                    print(f"❌ Missing columns in product_i_df: {missing_cols}")
                    return
                
                existing_products_df = pd.read_sql(
                    text("SELECT hs_code, country, address, place_of_r, place_of_l, product_description FROM product_i"),
                    self.engine
                )

                product_i_df = product_i_df.fillna('unknown')
                existing_products_df = existing_products_df.fillna('unknown')

                existing_keys = set(zip(
                    existing_products_df['hs_code'],
                    existing_products_df['country'],
                    existing_products_df['address'],
                    existing_products_df['place_of_r'],
                    existing_products_df['place_of_l'],
                    existing_products_df['product_description']
                ))

                product_i_df['__key'] = list(zip(
                    product_i_df['hs_code'],
                    product_i_df['country'],
                    product_i_df['address'],
                    product_i_df['place_of_r'],
                    product_i_df['place_of_l'],
                    product_i_df['product_description']
                ))

                new_products_df = product_i_df[~product_i_df['__key'].isin(existing_keys)].drop(columns=['__key'])

                if not new_products_df.empty:
                    print(f"Inserting {len(new_products_df)} new products...")
                    new_products_df.to_sql("product_i", self.engine, if_exists="append", index=False, method='multi')
                    print(f"[{time.time() - step_start:.2f}s] Products inserted.")
                else:
                    print(f"[{time.time() - step_start:.2f}s] No new products to add.")
            except Exception as e:
                print(f"[{time.time() - step_start:.2f}s] Error checking/inserting product_i: {e}")


            # Step 3: Retrieve product IDs
            existing_products_df = pd.read_sql(
                text("SELECT id, hs_code, country, address, place_of_r, place_of_l, product_description FROM product_i"),
                self.engine
            )

            merged = pd.merge(
                transaction_df,
                existing_products_df,
                how='left',
                on=['hs_code', 'country', 'address', 'place_of_r', 'place_of_l', 'product_description']
            )

            if merged['id'].isnull().any():
                missing = merged[merged['id'].isnull()]
                print(f"[{time.time() - step_start:.2f}s] Warning: Some transactions refer to unknown products.")
                print(missing[['hs_code', 'country', 'address', 'place_of_r', 'place_of_l', 'product_description']])
                merged = merged.dropna(subset=['id'])

            merged = merged.rename(columns={'id': 'product_id'})

            try:
                final_transaction_df = merged[[ 
                    'mst', 'quantity', 'unit_price', 'exchange_rate', 
                    'amount', 'date', 'product_id', 'exporter', 'unit', 'currency', 'origin_unit_price','origin_amount', 'origin_quantity' 
                ]]
                print(f"[{time.time() - step_start:.2f}s] Merged transaction rows: {len(final_transaction_df)}")
            except Exception as e:
                print(f'transaction_df: {transaction_df.columns}')
                print(f"[{time.time() - step_start:.2f}s] Error at final_transaction_df: {e}")
                return

            # Step 4: Insert transactions
            
            self._bulk_insert_dataframe("transaction", final_transaction_df)

        except Exception as e:
            print(f"❌ Error saving data to PostgreSQL: {str(e)}")

    def add_exporter_to_database(self, exporter_e_df, product_e_df, transaction_df):
        
        try:
            
            print("Starting add_to_database...")

            # Step 1: Add new importers
            step_start = time.time()
            try:
                existing_exporters_df = pd.read_sql(text("SELECT DISTINCT mst FROM exporter_e"), self.engine)
                existing_mst = set(existing_exporters_df['mst'])
                new_exporters_df = exporter_e_df[~exporter_e_df['mst'].isin(existing_mst)]
            except Exception as e:
                print(f"[{time.time() - step_start:.2f}s] Error reading existing exporters: {e}")
                new_exporters_df = pd.DataFrame()

            if not new_exporters_df.empty:
                print(f"Inserting {len(new_exporters_df)} new exporters...")
                new_exporters_df.to_sql("exporter_e", self.engine, if_exists="append", index=False, method='multi')
                print(f"[{time.time() - step_start:.2f}s] Added new importers.")
            else:
                print(f"[{time.time() - step_start:.2f}s] No new importers to add.")

            # Step 2: Deduplicate and insert product data
            step_start = time.time()
            try:
                print("Checking for duplicate products...")
                
                required_columns = ['hs_code', 'country', 'address', 'place_of_r', 'place_of_l', 'product_description']
                missing_cols = [col for col in required_columns if col not in product_e_df.columns]

                if missing_cols:
                    print(f"❌ Missing columns in product_e_df: {missing_cols}")
                    return
                
                existing_products_df = pd.read_sql(
                    text("SELECT hs_code, country, address, place_of_r, place_of_l, product_description FROM product_e"),
                    self.engine
                )

                product_e_df = product_e_df.fillna('unknown')
                existing_products_df = existing_products_df.fillna('unknown')

                existing_keys = set(zip(
                    existing_products_df['hs_code'],
                    existing_products_df['country'],
                    existing_products_df['address'],
                    existing_products_df['place_of_r'],
                    existing_products_df['place_of_l'],
                    existing_products_df['product_description']
                ))

                product_e_df['__key'] = list(zip(
                    product_e_df['hs_code'],
                    product_e_df['country'],
                    product_e_df['address'],
                    product_e_df['place_of_r'],
                    product_e_df['place_of_l'],
                    product_e_df['product_description']
                ))

                new_products_df = product_e_df[~product_e_df['__key'].isin(existing_keys)].drop(columns=['__key'])

                if not new_products_df.empty:
                    print(f"Inserting {len(new_products_df)} new products...")
                    new_products_df.to_sql("product_e", self.engine, if_exists="append", index=False, method='multi')
                    print(f"[{time.time() - step_start:.2f}s] Products inserted.")
                else:
                    print(f"[{time.time() - step_start:.2f}s] No new products to add.")
            except Exception as e:
                print(f"[{time.time() - step_start:.2f}s] Error checking/inserting product_e: {e}")


            # Step 3: Retrieve product IDs
            existing_products_df = pd.read_sql(
                text("SELECT id, hs_code, country, address, place_of_r, place_of_l, product_description FROM product_e"),
                self.engine
            )

            merged = pd.merge(
                transaction_df,
                existing_products_df,
                how='left',
                on=['hs_code', 'country', 'address', 'place_of_r', 'place_of_l', 'product_description']
            )

            if merged['id'].isnull().any():
                missing = merged[merged['id'].isnull()]
                print(f"[{time.time() - step_start:.2f}s] Warning: Some transactions refer to unknown products.")
                print(missing[['hs_code', 'country', 'address', 'place_of_r', 'place_of_l', 'product_description']])
                merged = merged.dropna(subset=['id'])

            merged = merged.rename(columns={'id': 'product_id'})

            try:
                final_transaction_df = merged[[ 
                    'mst', 'quantity', 'unit_price', 'exchange_rate', 
                    'amount', 'date', 'product_id', 'importer', 'unit', 'currency', 'origin_unit_price','origin_amount', 'origin_quantity' 
                ]]
                print(f"[{time.time() - step_start:.2f}s] Merged transaction rows: {len(final_transaction_df)}")
            except Exception as e:
                print(f'transaction_df: {transaction_df.columns}')
                print(f"[{time.time() - step_start:.2f}s] Error at final_transaction_df: {e}")
                return

            # Step 4: Insert transactions
            
            self._bulk_insert_dataframe("transaction_e", final_transaction_df)

        except Exception as e:
            print(f"❌ Error saving data to PostgreSQL: {str(e)}")


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

    def pie_market_share(self, top_n, product_type: str, date: str):
        cursor = self.conn.cursor()
        query = f"""
        SELECT
            CASE 
                WHEN rank_no <= {top_n} THEN companyname
                ELSE 'others'
            END AS company_group,
            SUM(total_amount) AS total_amount
            FROM (
            SELECT
                p.companyname,
                SUM(c.amount) AS total_amount,
                RANK() OVER (ORDER BY SUM(c.amount) DESC) AS rank_no
            FROM consumption c
            JOIN product p ON c.productid = p.id
            WHERE p.producttype = %s AND c.date = %s
            GROUP BY p.companyname
            ) ranked
            GROUP BY company_group
            ORDER BY total_amount DESC;

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
    def _bulk_insert_dataframe(self, table_name: str, df: pd.DataFrame):
        """Efficiently insert a DataFrame into PostgreSQL using psycopg2's execute_values."""
        if df.empty:
            print(f"No data to insert into {table_name}.")
            return

        conn = self.engine.raw_connection()
        cursor = conn.cursor()

        columns = list(df.columns)
        values = df.to_records(index=False).tolist()
        insert_query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES %s
        """
        try:
            execute_values(cursor, insert_query, values)
            conn.commit()
            print(f"{len(df)} rows inserted into {table_name}.")
        except Exception as e:
            conn.rollback()
            print(f"Error inserting into {table_name}: {e}")
        finally:
            cursor.close()
            conn.close()

    def build_value_select_clause(self, value_fields):
        mapping = {
            "amount": "ROUND(SUM(t.amount)::numeric, 2) AS amount",
            "quantity": "ROUND(SUM(t.quantity)::numeric, 0) AS quantity",
        }
        return ", ".join([mapping[f] for f in value_fields if f in mapping])

    def xnk_get_total_data(self, type_of_file, row_field, date, items, value_fields):
        
        if type_of_file == "importer":
            COLUMN_TABLE_MAP = IMPORTER_COLUMN_TABLE_MAP
            join_query = "JOIN product_i p on p.id = t.product_id JOIN importer_i i on i.mst = t.mst"
        elif type_of_file == "exporter":
            join_query = "JOIN product_e p on p.id = t.product_id JOIN exporter_e e on e.mst = t.mst"
            COLUMN_TABLE_MAP = EXPORTER_COLUMN_TABLE_MAP
        else:
            raise ValueError(f"Invalid type_of_file: {type_of_file}")
        
        alias = TABLE_ALIAS_MAP[COLUMN_TABLE_MAP[row_field]]
        value_select_clause = self.build_value_select_clause(value_fields)
        condition = ""
        params = tuple(([date] + items if items else [date]) * 2)
        if items is not None:
            placeholders = ','.join(['%s'] * len(items))
            condition = f"AND {alias}.{row_field} IN ({placeholders})"

        BASE_QUERY = f"""
            SELECT * FROM (
                SELECT {alias}.{row_field},
                    {value_select_clause}
                    FROM transaction t
                    {join_query}
                    WHERE t.date = %s {condition}
                    GROUP BY {alias}.{row_field}

                UNION ALL

                SELECT
                    'TOTAL' as {row_field},
                    {value_select_clause}
                    FROM transaction t
                    {join_query}
                    WHERE t.date = %s {condition}
                    )
                AS combined
            ORDER BY CASE WHEN {row_field} = 'TOTAL' THEN 1 ELSE 0 END; 
        """
        
        df = pd.read_sql(BASE_QUERY, self.engine, params=params)
        df.replace([np.inf, -np.inf, np.nan], 0, inplace=True)
        return df.to_dict(orient="records")
    
    def get_distinct_commodities(self, type_of_file, column):
        if type_of_file == "importer":
            table = "product_i"
        elif type_of_file == "exporter":
            table = "product_e"

        try:
            query = text(f"SELECT DISTINCT {column} FROM {table};")
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"Error fetching distinct commodities: {e}")
            return []
        
    def xnk_get_info(self, type_of_file, filter_field, filter_value,
                    rows_fields: list, rows_values, values_fields: list, date):
        
        # 1. Resolve column→table mappings
        if type_of_file == "importer":
            COLUMN_TABLE_MAP = IMPORTER_COLUMN_TABLE_MAP
            join_query = "JOIN product_i p ON p.id = t.product_id JOIN importer_i i ON i.mst = t.mst"
        elif type_of_file == "exporter":
            COLUMN_TABLE_MAP = EXPORTER_COLUMN_TABLE_MAP
            join_query = "JOIN product_e p ON p.id = t.product_id JOIN exporter_e e ON e.mst = t.mst"
        else:
            raise ValueError(f"Invalid type_of_file: {type_of_file}")
        
        # Validate row fields
        if len(rows_fields) < 2:
            raise ValueError("rows_fields must contain at least two elements.")

        variable_table_1 = COLUMN_TABLE_MAP[rows_fields[0]]
        variable_table_2 = COLUMN_TABLE_MAP[rows_fields[1]]

        variable_alias_1 = TABLE_ALIAS_MAP[variable_table_1]
        variable_alias_2 = TABLE_ALIAS_MAP[variable_table_2]

        # 2. Filter condition (if any)
        has_filter = filter_field not in [None, "", "null"] and filter_value not in (None, "", "null")
        filter_condition = ""
        if has_filter:
            fixed_table = COLUMN_TABLE_MAP[filter_field]
            fixed_alias = TABLE_ALIAS_MAP[fixed_table]
            filter_condition = f"{fixed_alias}.{filter_field} = %s AND "

        # 3. IN condition (if rows_values provided)
        in_condition = ""
        value_params = []
        if values_fields and rows_values:
            placeholders = ','.join(['%s'] * len(rows_values))
            in_condition = f"{variable_alias_1}.{rows_fields[0]} IN ({placeholders}) AND "
            value_params = rows_values

        # 4. SUM fields and NULL exclusion
        sum_fields = ", ".join([f"SUM(t.{f}) AS {f}" for f in values_fields]) if values_fields else ""
        exclude_null_condition = ""
        if values_fields:
            exclude_null_condition = " AND " + " AND ".join([f"t.{f} <> 'NaN'" for f in values_fields])

        # 5. SELECT clause
        select_fields = f"{variable_alias_1}.{rows_fields[0]}, {variable_alias_2}.{rows_fields[1]}"
        if sum_fields:
            select_fields += f", {sum_fields}"

        total_select_fields = f"{variable_alias_1}.{rows_fields[0]}, 'TOTAL' AS {rows_fields[1]}"
        if sum_fields:
            total_select_fields += f", {sum_fields}"

        # 6. Main base query
        base_query = f"""
            SELECT {{select_fields}}
            FROM transaction t
            {join_query}
            WHERE {filter_condition}{in_condition}t.date = %s{exclude_null_condition}
            GROUP BY {{group_by}}
        """

        # 7. Final queries
        detailed_query = base_query.format(
            select_fields=select_fields,
            group_by=f"{variable_alias_1}.{rows_fields[0]}, {variable_alias_2}.{rows_fields[1]}"
        )
        total_query = base_query.format(
            select_fields=total_select_fields,
            group_by=f"{variable_alias_1}.{rows_fields[0]}"
        )

        query = f"""
            SELECT *
            FROM (
                {detailed_query}
                UNION ALL
                {total_query}
            ) AS combined
            ORDER BY 
                {rows_fields[0]},
                CASE WHEN {rows_fields[1]} = 'TOTAL' THEN 1 ELSE 0 END,
                {rows_fields[1]};
        """

        # 8. Final parameters
        params = []
        if has_filter:
            params.append(filter_value)
        params += value_params
        params.append(date)

        final_params = tuple(params*2)  # Only needed once — not params*2

        print("Query:", query)
        print("Params:", final_params)

        # 9. Execute and clean results
        df = pd.read_sql(query, self.engine, params=final_params)

        # Replace NaN and infs for JSON safety
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.where(pd.notnull(df), None)  # Replace NaN with None (for JSON)

        return df.to_dict(orient="records")


    
    def xnk_get_distinct_filter(self, type_of_file, filter, date):
        if type_of_file == "importer":
            COLUMN_TABLE_MAP = IMPORTER_COLUMN_TABLE_MAP
        elif type_of_file == "exporter":
            COLUMN_TABLE_MAP = EXPORTER_COLUMN_TABLE_MAP
        else:
            raise ValueError(f"Invalid type_of_file: {type_of_file}")


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

    def get_XNK_data(self, date: str, limit, offset):
        
        query = """
        SELECT 
            t.id as id,
            t.mst as tax_code,
            t.quantity as quantity,
            t.unit_price as unit_price,
            t.exchange_rate as exchange_rate,
            t.amount as amount,
            t.date as date,
            t.exporter as exporter,
            i.company AS importer,
            i.address AS importer_address,
            p.commodity as commodity,
            p.hs_code as hs_code,
            p.address as exporter_address,
            p.country as country
        FROM transaction t
        JOIN product_i p ON p.id = t.product_id
        JOIN importer_i i ON i.mst = t.mst
        WHERE t.date = :date
        LIMIT :limit OFFSET :offset
    """

        # 2. SQL Execution
        
        with self.engine.connect() as conn:
            result = conn.execute(
                text(query), {"date": date, "limit": limit, "offset": offset}
            )
            columns = result.keys()
            rows = result.fetchall()

            # 3. Fetch Results

    
        
        data = []
        for row in rows:
            record = {
                col: (
                    "unknown"
                    if val is None
                    or (isinstance(val, float) and (math.isinf(val) or math.isnan(val)))
                    else val
                )
                for col, val in zip(columns, row)
            }
            data.append(record)

        return data
    
    def edit_value_in_DB(self, id, quantity, amount):
        query = """
            UPDATE transaction 
            SET quantity = :quantity, amount = :amount 
            WHERE id = :id
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text(query),
                    {"id": id, "quantity": quantity, "amount": amount}
                )
            return {"success": True, "message": "Record updated successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        
        
    def delete_by_id(self, id: int):
        query = """
            DELETE FROM transaction 
            WHERE id = :id
        """
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(query), {"id": id})
            return {"success": True, "message": f"Deleted {result.rowcount} record(s)"}
        except Exception as e:
            return {"success": False, "message": str(e)}
