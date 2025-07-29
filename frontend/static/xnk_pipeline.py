import pandas as pd
import os
from db import SteelDatabaseManager
from ETL_pipeline import parser, regex_pattern, country_detection, country_dictionary, hs_and_currency, hs_code, unit, unit_conversion, import_pipeline, export_pipeline

class XNK_pipeline:
    def __init__(self, file_path: str,
                 dbname: str = "steel_database",
                 user: str = "mysteelvn",
                 password: str = "cjLVuBdaSd5vtst"):
        self.file_path = file_path
        self.db_manager = SteelDatabaseManager(dbname=dbname, user=user, password=password)
        self.address_cols = []
        self.import_file = None
        self.average_usd_rate = None
        self.pipeline = None

    def load_file(self):
        self.import_file = pd.read_excel(self.file_path)
        print(self.import_file.columns)

        # Detect which address format is used
        if all(col in self.import_file.columns for col in ['DIA CHI 1', 'DIA CHI 2', 'DIA CHI 3', 'DIA CHI 4']):
            self.address_cols = ['DIA CHI 1', 'DIA CHI 2', 'DIA CHI 3', 'DIA CHI 4']
        elif 'DIA CHI' in self.import_file.columns:
            self.address_cols = ['DIA CHI']
        else:
            raise ValueError("❌ Excel file does not contain recognizable address columns.")

        print(f"✅ Detected address columns: {self.address_cols}")

    def calculate_usd_rate(self):
        usd_rates = self.import_file[self.import_file['CURRENCY'] == 'USD']['EXCHANGE RATE']
        self.average_usd_rate = usd_rates.mean()

    def build_pipeline(self, type_of_file):
        country_detect = country_detection.DetectCountry(
            country_dictionary.other_country_name,
            country_dictionary.city_list,
            country_dictionary.road_street_name
        )

        hs_and_currency_converter = hs_and_currency.HSandMoneyExchange(
            self.average_usd_rate,
            hs_dict=hs_code.hs_code_dict,
            unit_dict=unit_conversion.unit_conversion
        )

        convert_unit = unit.UnitConverter(unit_conversion.unit_conversion)
        if type_of_file == "importer":
            self.pipeline = import_pipeline.imported_pipeline(
                self.file_path,
                self.import_file,
                self.address_cols,
                country_detect,
                hs_and_currency_converter,
                convert_unit
            )
        elif type_of_file == "exporter":
            self.pipeline = export_pipeline.export_pipeline(
                self.file_path,
                self.import_file,
                self.address_cols,
                country_detect,
                hs_and_currency_converter,
                convert_unit
            )



    def run_pipeline(self):
        return self.pipeline.produce_check_xlsx()


    def import_function(self, type_of_file):
        self.load_file()
        
        self.calculate_usd_rate()
        self.build_pipeline(type_of_file)
        importer_i_df, product_id_df, transaction_df = self.run_pipeline()
        if type_of_file == "importer":
            self.db_manager.add_importer_to_database(importer_i_df, product_id_df, transaction_df)
        else:
            self.db_manager.add_exporter_to_database(importer_i_df, product_id_df, transaction_df)
        

