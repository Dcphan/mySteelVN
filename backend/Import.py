import pandas as pd
import os
import re
from datetime import datetime
import uuid
from backend.database.san_luong_db import SanLuongDatabase

TRANSLATION_MAP = {
    # Products
    "thép cán nóng": "hot steel coil",
    "thép cán nguội": "cool steel coil",
    "thép ống đen": "steel black pipe",
    "thép ống mạ": "steel coated pipe",
    "tôn mạ kẽm": "steel gal",
    "tôn mạ màu": "steel painted",
    "tôn mạ khác": "steel other",

    # Regions
    "tổng": "Total",
    "miền bắc": "Northern",
    "miền trung": "Central",
    "miền nam": "Southern",
    "xuất khẩu": "Export",
    "tồn kho": "Inventory",
    "sản xuất": "Production",
    "tiêu thụ": "Consumption",
    "tên công ty": "Company Name"
}

COMPANY_TRANSLATION_MAP = {
    # Steel Coil
    "Hòa Phát": "Hoa Phat Group",
    "Đại Thiên Lộc": "Dai Thien Loc",
    "Tôn Đông Á": "Ton Dong A",
    "Thép tấm lá Thống Nhất": "Thong Nhat Flat Steel",
    "China Steel & Nippon Steel Việt Nam": "China Steel & Nippon Steel",
    "Tôn Hoa Sen": "Hssc",
    "Thép Tấm Lá Phú Mỹ - Vnsteel": "Pfs Co.,Ltd",
    
    # Pipe
    "đại thiên lộc": "Dai Thien Loc",
    "tôn đông á": "Ton Dong A",
    "hòa phát": "Hoa Phat Group",
    "tập đoàn hoa sen": "Hoa Sen Group",
    "thép nam kim": "Nam Kim Steel",
    "mạ kẽm công nghiệp vingal-vnsteel": "Vingal Industries",
    "tvp steel": "Tvp Steel",
    "doanh nghiệp khác": "Other Company",
    "sản xuất thép việt đức": "Vietnam Germany Steel",
    "sản xuất và thương mại minh ngọc": "Mn Co., Ltd",
    "chinh dai industrial co., ltd": "Chinh Dai Industrial Co., Ltd",
    "thép seah việt nam": "SEAH Vietnam",
    "ống thép 190": "190 Steel Pipes",
    "s - steel co., ltd": "S - Steel Co., Ltd",
    "công ty cổ phần maruichi sun steel": "MARUICHI SUN STEEL JOINT STOCK COMPANY",
    "vinapipe": "Vinapipe",

    # Sheet
    "Tôn Phương Nam": "Southern Steel Sheet",
    "Gia Công Và Dịch Vụ Thép Sài Gòn": "Sgc",
    "Perstima Việt Nam": "Perstima Vietnam"


}

ALL_PRODUCTS = [
    "hot steel coil", "cool steel coil", "steel black pipe", 
    "steel coated pipe", "steel gal", "steel painted", "steel other",
    "steel bar", "steel shape", "steel wire rod"
]

ALL_REGIONS = ["Northern", "Central", "Southern", "Export"]
ALL_METRICS = ["Production", "Consumption", "Inventory"]


class SteelDataProcessor:
    def __init__(self, file_path, skiprows=7):
        self.file_path = file_path
        self.skiprows = skiprows
        self.df = None
        self.date = self.extract_date_from_filename()
        self.db_manager = SanLuongDatabase()

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
    
    def _translate_dataframe(self):
        df = self.df.applymap(lambda x: str(x).strip().lower() if pd.notnull(x) else x)

        df = df.replace(TRANSLATION_MAP)

        if "Company Name" in df.columns:
            df["Company Name"] = df["Company Name"].replace(COMPANY_TRANSLATION_MAP)

        df.rename(columns=lambda x: TRANSLATION_MAP.get(x, x), inplace=True)

        self.df = df

    def _fill_missing_rows(self):
        return self.df.fillna(0)



    def process_all_rows(self):
        if self.df is None:
            print("Data not loaded.")
            return

        for i in range(3, len(self.df)):  # Bỏ qua 3 hàng đầu
            self._process_single_row(i)
        
        print("All rows processed.")

    def _process_single_row(self, index):
        try:
            if index < 2:
                return

            def normalize(name):
                return str(name).strip().lower()

            name = normalize(self.df['Company Name'][index])
            target_products = ["hot steel coil", "cool steel coil","steel black pipe", "steel coated pipe","steel gal", "steel painted", "steel other", "steel bar", "steel shape", "steel wire rod"]

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
        self._fill_missing_rows()

        self.process_all_rows()

        self.db_manager.save_dataframes(
            self.product_df, 
            self.production_df, 
            self.inventory_df, 
            self.consumption_df
        )
