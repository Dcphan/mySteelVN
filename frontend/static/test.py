from db import SteelDatabaseManager
from Import import SteelDataProcessor

# Sau này fix lại File_Path
file_path = "D:\MySteel\Data Sản lượng\HRC CRC\FiinProX_SteelCoilStatistic_2018-1_20250322.xlsx"

import_file = SteelDataProcessor(file_path)

import_file.import_function()

