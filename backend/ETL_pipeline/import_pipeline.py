from ETL_pipeline import parser, regex_pattern, country_detection, country_dictionary, hs_and_currency, hs_code, unit, unit_conversion
import pandas as pd


class imported_pipeline():
    def __init__(self, import_file: object , address: list,  country_detect: object, hs_and_currency_converter: object, convert_unit: object):
        self.address_cols = address
        self.import_file = import_file
        self.country_detect = country_detect
        self.hs_and_currency_converter = hs_and_currency_converter
        self.convert_unit = convert_unit
    
    def produce_check_xlsx(self):
        excel = self.import_file[['DATE', 'TAX CODE', 'IMPORTER', 'ADDRESS', 'EXPORTER', 'HS CODE', 'CURRENCY', 'AMOUNT', 'UNIT PRICE', 'UNIT']] # Name in Excel Have To Match
        excel[['TAX CODE', 'HS CODE']] = excel[['TAX CODE', 'HS CODE']].astype(str)

        excel["EXCHANGE RATE"] = self.import_file["EXCHANGE RATE"].apply(lambda x: self.hs_and_currency_converter.ti_gia_conversion(x))

        excel['UNIT PRICE'] = excel.apply(lambda x: self.hs_and_currency_converter.unit_conversion(unit_price = x['UNIT PRICE'], forex_rate = x['EXCHANGE RATE'], unit = x['UNIT']), axis=1)

        excel['COMBINED ADDRESS'] = self.import_file.apply(
            lambda row: self.country_detect.combine_address(
                row['DIA CHI 1'],
                row['DIA CHI 2'],
                row['DIA CHI 3'],
                row['DIA CHI 4']
            ),
            axis=1
        )

        excel["COMMODITY"] = excel["HS CODE"].apply(lambda x: hs_code.hs_code_dict.get(x, None))

        excel['EXPORTED COUNTRY'] = self.import_file.apply(
            lambda row: self.country_detect.detect_country_full([row[col] for col in self.address_cols]),
            axis=1
        )

        excel['QUANTITY'] = self.import_file.apply(lambda row: self.convert_unit.convert_to_tan(row["QUANTITY"], row["UNIT"]), axis=1)
        

        importer_i_df = excel[['TAX CODE', 'IMPORTER', 'ADDRESS']]
        importer_i_df = importer_i_df.rename(columns={'TAX CODE': 'mst', 'IMPORTER': 'company', 'ADDRESS': 'address'})
        
        importer_i_df = importer_i_df.drop_duplicates(subset = 'mst')

        product_i_df = excel[['HS CODE', 'EXPORTED COUNTRY', 'COMBINED ADDRESS']]
        product_i_df = product_i_df.rename(columns={'HS CODE': 'hs_code', 'EXPORTED COUNTRY': 'country', 'COMBINED ADDRESS': 'address'})
        product_i_df = product_i_df.drop_duplicates()

        transaction_df = excel[['TAX CODE','QUANTITY', 'UNIT PRICE', 'EXCHANGE RATE', 'AMOUNT', 'DATE', 'EXPORTER', 'HS CODE', 'EXPORTED COUNTRY', 'COMBINED ADDRESS']]
        transaction_df = transaction_df.rename(columns={'TAX CODE': 'mst', 'QUANTITY': 'quantity', 'UNIT PRICE': 'unit_price', 'EXCHANGE RATE': 'exchange_rate', 'AMOUNT': 'amount', 'DATE': 'date', 'EXPORTER': 'exporter', 'HS CODE': 'hs_code', 'EXPORTED COUNTRY': 'country', 'COMBINED ADDRESS': 'address'})

        return importer_i_df, product_i_df, transaction_df
    