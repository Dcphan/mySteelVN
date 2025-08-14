from backend.config.project_config import SAN_LUONG_CONFIG
from backend.database.base_manager import BaseDBManager
import psycopg2
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import pandas as pd
import os




class SanLuongDatabase(BaseDBManager):
    def __init__(self):
        super().__init__(SAN_LUONG_CONFIG)

    def save_dataframes(self, product_df, production_df, inventory_df, consumption_df): # FIX SAVE DATAFRAME
        try:
            self._create_engine()
            product_df.to_sql("product", self.engine, if_exists="append", index=False, method='multi')
            production_df.to_sql("production", self.engine, if_exists="append", index=False, method='multi')
            inventory_df.to_sql("inventory", self.engine, if_exists="append", index=False, method='multi')
            consumption_df.to_sql("consumption", self.engine, if_exists="append", index=False, method='multi')
            
            print("Data saved to PostgreSQL.")
        except Exception as e:
            print(f"Error saving data to PostgreSQL: {e}")
        finally:
            self.dispose()

    
    def check_product_exists(self, product_type: str, company_name: str) -> bool:
        try:
            with self.get_cursor() as cursor:
                query = """
                    SELECT EXISTS (
                        SELECT 1 FROM Product 
                        WHERE ProductType = %s AND CompanyName = %s
                    );
                """
                cursor.execute(query, (product_type, company_name))
                result = cursor.fetchone()
                exists = result[0] if result else False
                return bool(exists)
        except Exception as e:
            print(f"❌ Error in SanLuongDatabase.check_product_exists(): {e}")
            return False
        
    def search_product_ID(self, product_type: str, company_name: str):
        try: 
            with self.get_cursor() as cursor:
                product_type = product_type.strip().lower()
                company_name = company_name.strip().lower()

                query = """SELECT ID FROM Product 
                       WHERE LOWER(TRIM(ProductType)) = %s AND LOWER(TRIM(CompanyName)) = %s 
                       LIMIT 1"""
                
                cursor.execute(query, (product_type, company_name))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Database error while searching product ID: {e}")

    def get_data(self, main_table, ids, start_date, end_date):
        with self.get_cursor() as cur:
            placeholders = ','.join(['%s'] * len(ids))
            params = ids + [start_date, end_date]

            if main_table == "Domestic":
                query = f""" 
                    SELECT t.Date, SUM(t.Amount), p.CompanyName, p.ProductType
                    FROM Consumption t
                    LEFT JOIN Product p ON t.ProductID = p.ID
                    WHERE t.ProductID IN ({placeholders})
                      AND t.Date BETWEEN %s AND %s
                      AND t.Region IN ('Northern', 'Central', 'Southern')
                    GROUP BY t.Date, p.CompanyName, p.ProductType
                    ORDER BY t.Date
                """
            elif main_table == "Export":
                query = f""" 
                    SELECT t.Date, t.Amount, p.CompanyName, p.ProductType
                    FROM Consumption t
                    LEFT JOIN Product p ON t.ProductID = p.ID
                    WHERE t.ProductID IN ({placeholders})
                      AND t.Date BETWEEN %s AND %s
                      AND t.Region = 'Region'
                    GROUP BY t.Date, p.CompanyName, p.ProductType
                    ORDER BY t.Date
                """
            else:
                query = f"""
                    SELECT main.Date, main.Amount, p.CompanyName, p.ProductType
                    FROM {main_table} main
                    JOIN Product p ON p.ID = main.ProductID
                    WHERE p.ID IN ({placeholders})
                      AND main.Date BETWEEN %s AND %s
                """

            cur.execute(query, params)
            result = cur.fetchall()
            return self.to_chartjs_format(result)

    def to_chartjs_format(self, rows):
        date_set = set()
        company_data = defaultdict(dict)

        for date, amount, company, product in rows:
            key = f"{company} - {product}"
            date_set.add(date)
            company_data[key][date] = amount

        sorted_dates = sorted(date_set, key=lambda d: datetime.strptime(d, "%Y-%m"))
        datasets = []

        for idx, (company_product, date_values) in enumerate(company_data.items()):
            data = [date_values.get(date, 0) for date in sorted_dates]
            datasets.append({
                "label": company_product,
                "data": data,
                "yAxisID": f"y{idx + 1}"
            })

        return {
            "labels": sorted_dates,
            "datasets": datasets
        }

    def pie_market_share(self, top_n, product_type: list[str], date: str):
        # Create comma-separated placeholders for each product_type
        placeholders = ','.join(['%s'] * len(product_type))

        with self.get_cursor() as cur:
            query = f"""
                SELECT
                    CASE 
                        WHEN rank_no <= %s THEN companyname
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
                    WHERE p.producttype IN ({placeholders}) AND c.date = %s
                    GROUP BY p.companyname
                ) ranked
                GROUP BY company_group
                ORDER BY total_amount DESC;
            """
            # top_n + all product types + date
            cur.execute(query, (top_n, *product_type, date))
            rows = cur.fetchall()

            labels = [company for company, _ in rows]
            data = [float(total) if isinstance(total, Decimal) else total for _, total in rows]

            return {
                "labels": labels,
                "data": data
            }

            
    def build_value_select_clause(self, value_fields):
        mapping = {
            "amount": "ROUND(SUM(t.amount)::numeric, 2) AS amount",
            "quantity": "ROUND(SUM(t.quantity)::numeric, 0) AS quantity",
        }
        return ", ".join([mapping[f] for f in value_fields if f in mapping])

    def table_data(self, products, month):
        try:
            with self.get_cursor() as cursor:
                product_placeholders = ','.join(['%s'] * len(products))
                query = f"""
                    SELECT *
                    FROM (
                        SELECT 'production' AS source, p.companyname AS company, p.producttype AS product, NULL AS region, pr.amount AS amount, pr.date AS date
                        FROM production pr
                        JOIN product p ON pr.productid = p.id

                        UNION ALL

                        SELECT 'inventory', p.companyname, p.producttype, NULL, i.amount, i.date
                        FROM inventory i
                        JOIN product p ON i.productid = p.id

                        UNION ALL

                        SELECT 'consumption', p.companyname, p.producttype, c.region, c.amount, c.date
                        FROM consumption c
                        JOIN product p ON c.productid = p.id
                    ) AS unified
                    WHERE unified.product IN ({product_placeholders}) AND unified.date = %s
                """
                param = products + [month]
                cursor.execute(query, param)
                rows = cursor.fetchall()
                return self.transform_to_dict(rows)

        except Exception as e:
            print(f"[ERROR] Failed to fetch table data: {e}")
            return []

    def transform_to_dict(self, raw_data):
        result_dict = defaultdict(lambda: {
            'Production': 0,
            'Inventory': 0,
            'Northern': 0,
            'Central': 0,
            'Southern': 0,
            'Export': 0
        })

        for row in raw_data:
            source, company, product, region, amount, date = row
            key = (company, product, date)

            if source == 'Production':
                result_dict[key]['Production'] = amount
            elif source == 'Inventory':
                result_dict[key]['Inventory'] = amount
            elif source == 'Consumption' and region in ['Northern', 'Central', 'Southern', 'Export']:
                result_dict[key][region] = amount

        result_list = []
        for (company, product, date), values in result_dict.items():
            entry = {
                'Company': company,
                'Product': product,
                'Date': date,
                'Production': values['Production'],
                'Inventory': values['Inventory'],
                'Northern': values['Northern'],
                'Central': values['Central'],
                'Southern': values['Southern'],
                'Export': values['Export']
            }
            result_list.append(entry)

        return result_list
    
    def get_month_summary(self, category, id: list, start, end):
        id_placeholders = ','.join(['%s'] * len(id))
        params = id + [start, end]

        if category == "Export":
            query = f"""
                SELECT
                    t.date AS month,
                    p.companyname,
                    p.producttype,
                    t.amount
                FROM consumption t
                LEFT JOIN product p ON t.productid = p.id
                WHERE t.productid IN ({id_placeholders})
                AND t.date BETWEEN %s AND %s
                AND t.region = 'Export'
                GROUP BY t.date, p.companyname, p.producttype, t.amount
                ORDER BY t.date
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
                WHERE t.productid IN ({id_placeholders})
                AND t.date BETWEEN %s AND %s
                AND t.region IN ('Northern', 'Central', 'Southern')
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
                FROM {category} t
                LEFT JOIN product p ON t.productid = p.id
                WHERE t.productid IN ({id_placeholders})
                AND t.date BETWEEN %s AND %s
                GROUP BY t.date, p.companyname, p.producttype, t.amount
                ORDER BY t.date
            """

        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return self.format_for_table(rows)
        except Exception as e:
            print(f"[ERROR] Failed to execute summary query: {e}")
            return []

    def get_product_and_company(self):
        try:
            with self.get_cursor() as cursor:
                query = 'SELECT CompanyName, ProductType, ID FROM Product'
                cursor.execute(query)
                rows = cursor.fetchall()

                result = {}
                for company, product, pid in rows:
                    entry = {"company": company, "id": pid}
                    result.setdefault(product, []).append(entry)
                return result
        except Exception as e:
            print(f"[ERROR] in get_product_and_company: {e}")
            return {}

    def get_product(self):
        try:
            with self.get_cursor() as cursor:
                query = "SELECT DISTINCT ProductType FROM Product"
                cursor.execute(query)
                rows = cursor.fetchall()
                return [item[0] for item in rows]
        except Exception as e:
            print(f"[ERROR] in get_product: {e}")
            return []

    def format_for_table(self, rows):
        combined_keys = set()
        table = defaultdict(dict)

        for month, company, product, total in rows:
            key = f"{company} - {product}"
            table[month][key] = total
            combined_keys.add(key)

        columns = sorted(combined_keys)
        result = []

        for month in sorted(table.keys()):
            row = {"Month": month}
            for key in columns:
                row[key] = table[month].get(key, 0.0)
            result.append(row)

        return {"columns": columns, "rows": result}
    
    def read_df(self, category):
        self.reconnect_if_closed()
        try:
            if category == "Export":
                query = """
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
                query = """
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
                table = category.lower()
                query = f"""
                    SELECT 
                        t.date AS month,
                        p.companyname,
                        p.producttype,
                        t.amount
                    FROM {table} t
                    LEFT JOIN product p ON t.productid = p.id
                    GROUP BY month, p.companyname, p.producttype, t.amount
                    ORDER BY month
                """

            df_read = pd.read_sql_query(query, self.conn)
            return df_read

        except Exception as e:
            print(f"Error in read_df({category}): {e}")
            return pd.DataFrame()

    def change_to_pivot(self, df):
        try:
            pivot = df.pivot_table(
                index=['companyname', 'producttype'],
                columns='month',
                values='amount',
                aggfunc='sum',
                fill_value=0
            ).reset_index()

            pivot.columns.name = None
            pivot = pivot.sort_index(axis=1)

            new_order = ['producttype', 'companyname'] + [
                col for col in pivot.columns if col not in ('companyname', 'producttype')
            ]
            pivot = pivot[new_order]

            return pivot
        except Exception as e:
            print(f"Error in change_to_pivot: {e}")
            return pd.DataFrame()

    def convert_to_excel(self, excel_file_path: str) -> bool:
        output_dir = os.path.dirname(excel_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            inventory_pivot = self.change_to_pivot(self.read_df('Inventory'))
            production_pivot = self.change_to_pivot(self.read_df('Production'))
            export_pivot = self.change_to_pivot(self.read_df('Export'))
            domestic_pivot = self.change_to_pivot(self.read_df('Domestic'))

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
        try:
            return {
                'Inventory': self.change_to_pivot(self.read_df('Inventory')).to_dict(orient='records'),
                'Production': self.change_to_pivot(self.read_df('Production')).to_dict(orient='records'),
                'Export': self.change_to_pivot(self.read_df('Export')).to_dict(orient='records'),
                'Domestic': self.change_to_pivot(self.read_df('Domestic')).to_dict(orient='records'),
            }
        except Exception as e:
            print(f"Error in get_all_pivot_data: {e}")
            return {}
