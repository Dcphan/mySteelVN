import os
import psycopg2
import pandas as pd
from datetime import datetime
from collections import defaultdict

class TableDatabase:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

    def close(self):
        self.conn.close()

    def table_data(self, products, month):
        cur = self.conn.cursor()
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

        try:
            param = products + [month]
            cur.execute(query, param)
            rows = cur.fetchall()
            return self.transform_to_dict(rows)
        except Exception as e:
            print(f"[ERROR] Failed to fetch table data: {e}")
            self.conn.rollback()
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

    def get_product_and_company(self):
        cursor = self.conn.cursor()
        try:
            query = 'SELECT CompanyName, ProductType, ID FROM Product'
            cursor.execute(query)
            rows = cursor.fetchall()

            result = {}
            for company, product, pid in rows:
                entry = {"product": product, "id": pid}
                result.setdefault(company, []).append(entry)
            return result
        except Exception as e:
            print(f"Error in get_product_and_company: {e}")
            self.conn.rollback()  # 👈 This fixes the broken transaction
            return {}


    def get_product(self):
        cursor = self.conn.cursor()
        query = "SELECT DISTINCT ProductType FROM Product"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [item[0] for item in rows]

    def get_month_summary(self, category, id: list, start, end):
        cursor = self.conn.cursor()
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
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return self.format_for_table(rows)
        except Exception as e:
            print(f"[ERROR] Failed to execute summary query: {e}")
            self.conn.rollback()
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
