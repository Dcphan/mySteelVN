import pandas as pd
import re
from pathlib import Path
from backend.ETL_pipeline import parser, regex_pattern, country_detection, country_dictionary, hs_and_currency, hs_code, unit, unit_conversion
from backend.ETL_pipeline.unit_conversion import unit_conversion as unit_conversion_dict, unit_name_to_code


class imported_pipeline():
    def __init__(self, file_path: str, import_file: object, address: list, country_detect: object,
                 hs_and_currency_converter: object, convert_unit: object):
        self.file_path = file_path
        self.address_cols = address
        self.import_file = import_file
        self.country_detect = country_detect
        self.hs_and_currency_converter = hs_and_currency_converter
        self.convert_unit = convert_unit

    def extract_month_year_from_path(self, file_path: str) -> str:
        file_name = Path(file_path).name
        match = re.search(r'T?(\d{1,2})[-_.]?T?(\d{4})', file_name)
        if match:
            return f"{int(match.group(2))}-{int(match.group(1)):02d}"
        return "unknown"

    def produce_check_xlsx(self):
        required_cols = [
            'DATE', 'TAX CODE', 'IMPORTER', 'ADDRESS', 'EXPORTER',
            'HS CODE', 'CURRENCY', 'UNIT PRICE', 'UNIT', 'QUANTITY', 'EXCHANGE RATE'
        ]
        for col in required_cols:
            if col not in self.import_file.columns:
                raise ValueError(f"❌ Missing required column: '{col}'")

        has_amount = 'AMOUNT' in self.import_file.columns
        cols_to_load = required_cols.copy()
        if has_amount:
            cols_to_load.append('AMOUNT')

        excel = self.import_file[cols_to_load].copy()
        excel[['TAX CODE', 'HS CODE']] = excel[['TAX CODE', 'HS CODE']].astype(str)

        # Extract date from file path
        
        formatted_date = self.extract_month_year_from_path(self.file_path)
        excel['DATE'] = [formatted_date] * len(excel)
        print(formatted_date)


        # Exchange rate conversion
        excel["EXCHANGE RATE"] = self.import_file["EXCHANGE RATE"].apply(
            lambda x: self.hs_and_currency_converter.ti_gia_conversion(x)
        )

        def get_final_unit_code(unit, unit_conversion_dict, name_map):
            unit = str(unit).strip()
            if unit in unit_conversion_dict:
                return unit
            return name_map.get(unit, None)

        excel['UNIT_CODE'] = excel['UNIT'].apply(
            lambda u: get_final_unit_code(u, unit_conversion_dict, unit_name_to_code)
        )

        excel['UNIT PRICE'] = excel.apply(
            lambda x: self.hs_and_currency_converter.unit_conversion(
                unit_price=x['UNIT PRICE'],
                forex_rate=x['EXCHANGE RATE'],
                unit=x['UNIT_CODE']
            ), axis=1
        )

        # Address processing
        if len(self.address_cols) == 4:
            excel['COMBINED ADDRESS'] = self.import_file.apply(
        lambda row: self.country_detect.combine_address(*[row[col] for col in self.address_cols]),
        axis=1
            )
        elif len(self.address_cols) == 1:
            excel['COMBINED ADDRESS'] = self.import_file[self.address_cols[0]]
        else:
            raise ValueError("❌ Unsupported address format. Expected either ['DIA CHI'] or ['DIA CHI 1', ..., 'DIA CHI 4']")

        # HS code → Commodity
        def safe_hs_lookup(x):
            try:
                return hs_code.hs_code_dict.get(int(float(x)))
            except (ValueError, TypeError):
                return None

        excel["COMMODITY"] = excel["HS CODE"].apply(safe_hs_lookup)

        # Country detection
        excel['EXPORTED COUNTRY'] = excel['COMBINED ADDRESS'].apply(
            lambda x: self.country_detect.detect_country_full(x)
        )

        # Convert quantity to tons
        excel['QUANTITY'] = excel.apply(
            lambda row: self.convert_unit.convert_to_tan(row["QUANTITY"], row["UNIT_CODE"]),
            axis=1
        )

        if not has_amount:
            excel['AMOUNT'] = excel['UNIT PRICE'] * excel['QUANTITY']

        excel = excel.dropna(subset=['IMPORTER'])

        # Final tables
        importer_i_df = excel[['TAX CODE', 'IMPORTER', 'ADDRESS']].rename(
            columns={'TAX CODE': 'mst', 'IMPORTER': 'company', 'ADDRESS': 'address'}
        ).drop_duplicates(subset='mst')

        product_i_df = excel[['HS CODE', 'EXPORTED COUNTRY', 'COMBINED ADDRESS', 'COMMODITY']].rename(
            columns={'HS CODE': 'hs_code', 'EXPORTED COUNTRY': 'country',
                     'COMBINED ADDRESS': 'address', 'COMMODITY': 'commodity'}
        ).drop_duplicates()

        transaction_df = excel[['TAX CODE', 'QUANTITY', 'UNIT PRICE', 'EXCHANGE RATE',
                                'AMOUNT', 'DATE', 'EXPORTER', 'HS CODE', 'EXPORTED COUNTRY', 'COMBINED ADDRESS']].rename(
            columns={'TAX CODE': 'mst', 'QUANTITY': 'quantity', 'UNIT PRICE': 'unit_price',
                     'EXCHANGE RATE': 'exchange_rate', 'AMOUNT': 'amount', 'DATE': 'date',
                     'EXPORTER': 'exporter', 'HS CODE': 'hs_code', 'EXPORTED COUNTRY': 'country',
                     'COMBINED ADDRESS': 'address'}
        )

        return importer_i_df, product_i_df, transaction_df
