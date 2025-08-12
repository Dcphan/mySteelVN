from backend.config.project_config import XUAT_KHAU_CONFIG
from backend.database.base_manager import BaseDBManager
import psycopg2
import math
import numpy as np

from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
import pandas as pd

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
    "transaction_e": "",
    "product_e": """
        JOIN transaction_e t ON p.id = t.product_id
    """,
    "exporter_e": """
        JOIN transaction_e t ON e.mst = t.mst
    """
}
TABLE_ALIAS_MAP = {"transaction_e": "t", "product_e": "p", "exporter_e": "e"}


class XuatKhauDatabase(BaseDBManager):
    def __init__(self):
        super().__init__(XUAT_KHAU_CONFIG) 


    def add_exporter_to_database(self, exporter_e_df, product_e_df, transaction_e_df):
        def log_step(step_desc, func):
            try:
                func()
            except Exception as e:
                print(f"❌ {step_desc} failed: {e}")
                raise

        try:
            self._create_engine()

            # --- Constants ---
            importer_columns = ["mst", "company", "address"]
            product_columns = [
                'hs_code', 'country', 'address', 'commodity',
                'place_of_r', 'place_of_l', 'product_description'
            ]

            # --- Step 1: Insert importers ---
            log_step("Insert into importer_i", lambda: self._insert_on_conflict_do_nothing(exporter_e_df, "exporter_e", importer_columns))

            # --- Step 2: Insert products ---
            missing_cols = set(product_columns) - set(product_e_df.columns)
            if missing_cols:
                print(f"❌ Missing required columns in product_i_df: {missing_cols}")
                return
            log_step("Insert into product_i", lambda: self._insert_on_conflict_do_nothing(product_e_df, "product_e", product_columns))
             # --- Step 3: Convert 'date' to DATE format ---
            if 'date' in transaction_e_df.columns:
                try:
                    transaction_e_df['date'] = pd.to_datetime(transaction_e_df['date'], format='%Y-%m').dt.date
                except Exception as e:
                    print(f"❌ Failed to parse 'date' column: {e}")
                    return
            
            # --- Step 3: Create staging table ---
            def create_staging():
                with self.engine.begin() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS _transaction_e_stage"))
                    conn.execute(text("""
                        CREATE TEMP TABLE _transaction_e_stage (
                            mst TEXT, quantity NUMERIC, unit_price REAL, exchange_rate REAL,
                            amount REAL, date DATE, importer TEXT, unit TEXT, currency TEXT,
                            origin_unit_price REAL, origin_amount REAL, origin_quantity REAL,
                            hs_code TEXT, country TEXT, address TEXT,
                            place_of_r TEXT, place_of_l TEXT, product_description TEXT
                        )
                    """))
            log_step("Create transaction staging table", create_staging)

            # --- Step 4: Insert into staging table ---
            log_step("Insert into transaction_e", lambda: self._bulk_insert_dataframe("_transaction_e_stage", transaction_e_df))

            # --- Step 5: Insert joined records into transaction table ---
            def insert_transaction():
                with self.engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO transaction_e (
                            mst, quantity, unit_price, exchange_rate, amount, date,
                            product_id, importer, unit, currency,
                            origin_unit_price, origin_amount, origin_quantity
                        )
                        SELECT 
                            t.mst, t.quantity, t.unit_price, t.exchange_rate, t.amount, t.date,
                            p.id, t.importer, t.unit, t.currency,
                            t.origin_unit_price, t.origin_amount, t.origin_quantity
                        FROM _transaction_e_stage t
                        JOIN product_e p ON
                            t.hs_code = p.hs_code AND
                            t.country = p.country AND
                            t.address = p.address AND
                            t.place_of_r = p.place_of_r AND
                            t.place_of_l = p.place_of_l AND
                            t.product_description = p.product_description
                    """))
            log_step("Insert into final transaction table", insert_transaction)

            print("✅ All data inserted successfully.")

        except Exception as e:
            print(f"❌ Unexpected error during import process: {e}")

        finally:
            self.dispose()

    def get_XNK_data(self, date, limit, offset):
        try:
            self._create_engine()
            with self.engine.connect() as conn:
                query = """
                    SELECT 
                        t.id as id,
                        t.mst as tax_code,
                        t.quantity as quantity,
                        t.unit_price as unit_price,
                        t.exchange_rate as exchange_rate,
                        t.amount as amount,
                        t.date as date,
                        t.importer as importer,
                        e.company AS exporter,
                        e.address AS exporter_address,
                        p.commodity as commodity,
                        p.hs_code as hs_code,
                        p.address as importer_address,
                        p.country as country,
                        p.place_of_r as place_of_r,
                        p.place_of_l as place_of_l,
                        p.product_description as product_description
                    FROM transaction_e t
                    JOIN product_e p ON p.id = t.product_id
                    JOIN exporter_e e ON e.mst = t.mst
                    WHERE t.date = :date
                    LIMIT :limit OFFSET :offset
                """
                result = conn.execute(text(query), {
                    "date": date,
                    "limit": limit,
                    "offset": offset
                })

                columns = result.keys()
                rows = result.fetchall()

            # Convert result to list of dicts with None/NaN/Inf safe handling
            data = [
                {
                    col: (
                        "unknown" if val is None or
                        (isinstance(val, float) and (math.isnan(val) or math.isinf(val)))
                        else val
                    )
                    for col, val in zip(columns, row)
                }
                for row in rows
            ]

            return data

        except Exception as e:
            print(f"❌ Failed to fetch import data: {e}")
            return []

# NEED FIX      
    def edit_value_in_DB(self, id: int, quantity: float, amount: float):
        query = """
            UPDATE transaction_e
            SET quantity = :quantity, amount = :amount 
            WHERE id = :id
        """
        try:
            self._create_engine()
            with self.engine.begin() as conn:
                conn.execute(
                    text(query),
                    {"id": id, "quantity": quantity, "amount": amount}
                )
            return {"success": True, "message": f"✅ Updated record with ID {id}"}
        except Exception as e:
            return {"success": False, "message": f"❌ Update failed: {e}"}

# NEED FIX
    def delete_by_id(self, id: int):
        query = "DELETE FROM transaction_e WHERE id = :id"
        try:
            with self.engine.begin() as conn:
                result = conn.execute(text(query), {"id": id})
            return {
                "success": True,
                "message": f"✅ Deleted {result.rowcount} record(s) from 'transaction_e'"
            }
        except Exception as e:
            return {"success": False, "message": f"❌ Delete failed: {e}"}


# PIVOTTABLE
    def xnk_get_total_data(self, row_field, date, items, value_fields):
        COLUMN_TABLE_MAP = EXPORTER_COLUMN_TABLE_MAP
        join_query = (
            "JOIN product_e p ON p.id = t.product_id "
            "JOIN exporter_e e ON e.mst = t.mst"
        )
        
        alias = TABLE_ALIAS_MAP[COLUMN_TABLE_MAP[row_field]]
        value_select_clause = self.build_value_select_clause(value_fields)

        condition = ""
        params = [date]
        if items:
            placeholders = ','.join(['%s'] * len(items))
            condition = f"AND {alias}.{row_field} IN ({placeholders})"
            params += items
        params *= 2  # Because date/items used twice in UNION

        base_query = f"""
                SELECT * FROM (
                    SELECT {alias}.{row_field}, {value_select_clause[0]}
                    FROM transaction_e t
                    {join_query}
                    WHERE t.date = %s {condition} AND {value_select_clause[1]}
                    GROUP BY {alias}.{row_field} 

                    UNION ALL

                    SELECT 'TOTAL' AS {row_field}, {value_select_clause[0]}
                    FROM transaction_e t
                    {join_query}
                    WHERE t.date = %s {condition} AND {value_select_clause[1]}
                ) AS combined
                ORDER BY CASE WHEN {row_field} = 'TOTAL' THEN 1 ELSE 0 END;
            """

        try:
            
            with self.get_cursor() as cur:  # <-- use your context manager here
                cur.execute(base_query, params)
                colnames = [desc[0] for desc in cur.description]
                rows = [dict(zip(colnames, r)) for r in cur.fetchall()]
            return rows
        except Exception as e:
            print(f"Error fetching total data: {e}")
            return []
        
    def get_distinct_commodities(self, column):
        
        table = "product_e"
        query = f"SELECT DISTINCT {column} FROM {table};"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"Error fetching distinct commodities: {e}")
            return []
        
    def xnk_get_info(self, type_of_file, filter_field, filter_value,
                    rows_fields: list, rows_values, values_fields: list, date):
        
        # 1. Resolve column→table mappings
        if type_of_file == "exporter":
            COLUMN_TABLE_MAP = EXPORTER_COLUMN_TABLE_MAP
            join_query = "JOIN product_e p ON p.id = t.product_id JOIN exporter_e e ON e.mst = t.mst"
        
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
            FROM transaction_e t
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

        try:
            self._create_engine()
            # 9. Execute and clean results
            df = pd.read_sql(query, self.engine, params=final_params)

            # Replace NaN and infs for JSON safety
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df = df.where(pd.notnull(df), None)  # Replace NaN with None (for JSON)

            return df.to_dict(orient="records")
        
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
        finally:
            self.dispose()
    
    def xnk_get_distinct_filter(self, type_of_file, filter, filter_header,  filter_value, date):
        

        if type_of_file == "exporter":
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
            self._create_engine()
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
                
            if filter_value:
                sql += f" AND {alias}.{filter_header} = :filter_value"
                params["filter_value"] = filter_value

            sql += f" ORDER BY {alias}.{filter};"

            

            query = text(sql)
            print("sql:"+ sql)
            print("params:"+ str(params))

            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"Error fetching distinct {filter}: {e}")
            return []

        finally:
            self.dispose()