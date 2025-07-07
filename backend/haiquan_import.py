import pycountry
import pandas as pd
import re
import unicodedata

other_country_name = {
    "viet nam": "Vietnam",
    "vn": "Vietnam",
    "vie tnam": "Vietnam",
    "vietnam": "Vietnam",
    "hongkong": "Hong Kong",
    "hk": "Hong Kong",
    "h k": "Hong Kong",
    "h k ": "Hong Kong",
    "r o c": "Taiwan",
    "korea": "South Korea",
    "taiwan": "Taiwan",
    "macau": "Macau",
    "usa": "United States",
    "u s a": "United States",
    "u s ": "United States",
    "p r c": "China",
    "prc": "China",
    "trung quoc": "China",
    "espana": "Spain",
    "united arab emirate" : "United Arab Emirates",
    "uae" : "United Arab Emirates",
    "british virgin": "British Virgin Islands",
    "russia": "Russia",
    "lao pdr": "Laos",
    "italia": "Italy"
}

city_list = {
    "hanoi": "Vietnam",
    "bien hoa": "Vietnam",
    "binh phuoc": "Vietnam",
    "ha noi": "Vietnam",
    "phu tho": "Vietnam",
    "ho chi minh": "Vietnam",
    "can tho": "Vietnam",
    "hcm": "Vietnam",
    "quang nam": "Vietnam",
    "quang ninh": "Vietnam",
    "dong nai": "Vietnam",
    "hai phong": "Vietnam",
    "vinh long": "Vietnam",
    "haiphong": "Vietnam",
    "hue": "Vietnam",
    "nghe an": "Vietnam",
    "binh duong": "Vietnam",
    "tien giang": "Vietnam",
    "bac giang": "Vietnam",
    "hoa binh": "Vietnam",
    "bac ninh": "Vietnam",
    "quang ngai": "Vietnam",
    "bacninh": "Vietnam",
    "da nang": "Vietnam",
    "danang": "Vietnam",
    "hung yen": "Vietnam",
    "thai nguyen": "Vietnam",
    "tay ninh": "Vietnam",
    "vinh phuc": "Vietnam",
    "hai duong": "Vietnam",
    "phu yen": "Vietnam",
    "nam dinh": "Vietnam",
    "ha nam": "Vietnam",
    "long an": "Vietnam",
    "ben tre": "Vietnam",
    "vung tau": "Vietnam",
    "thai binh": "Vietnam",
    "shanghai": "China",
    "guangxi": "China",
    "henan": "China",
    "jiangmen": "China",
    "jiangshu": "China",
    "jiangsu": "China",
    "jiang su": "China",
    "shijiazhuang": "China",
    "shandong": "China",
    "liaoning": "China",
    "zhejiang": "China",
    "shenzhen": "China",
    "zhongshan": "China",
    "zengcheng": "China",
    "tangshan": "China",
    "changzhou": "China",
    "dongguan": "China",
    "songling": "China",
    "hunan": "China",
    "jiangshu": "China",
    "zhuhai": "China",
    "beijing": "China",
    "nanning": "China",
    "tianjin": "China",
    "chongqing": "China",
    "jiangxi": "China",
    "shangdong": "China",
    "yuhuan": "China",
    "taichung": "China",
    "baiyun": "China",
    "wuxi": "China",
    "wujin": "China",
    "jiangshu": "China",
    "tongsheng": "China",
    "guang dong": "China",
    "guangdong": "China",
    "quzhou": "China",
    "suzhou": "China",
    "kunshan": "China",
    "hangzhou": "China",
    "guangming": "China",
    "foshan": "China",
    "kowloon": "Hong Kong",
    "kwai chung": "Hong Kong",
    "tokyo": "Japan",
    "kyoto": "Japan",
    "osaka": "Japan",
    "aichi": "Japan",
    "okayama": "Japan",
    "las pinas": "Philippines",
    "torrance": "United States",
    "fareham hampshire": "UK",
    "maharashtra": "India",
    "mumbai": "India",
    "bangkok": "Thailand",
    "samutprakarn": "Thailand",
    "kabupaten bekasi": "Indonesia",
    "taipei": "Taiwan",
    "seoul": "Korea",
    "houston": "United States",
}

road_street_name = {
    "tan thuan": "Vietnam",
    "des voeux road": "Hong Kong",
    "industrial building 26 38 kwai cheong road nt": "Hong Kong",
    "huashan st": "China",
    "lockhart road": "China",
    "liaocheng economic": "China",
    "tung choi street street kl": "Hong Kong",
    "thuan an": "Vietnam"
}


class convert_to_Excel():
    def __init__(self, file):
        self.df = pd.read_excel(file)

    def clean_text(self, text):
        if not isinstance(text, str):
            return ""
        text = unicodedata.normalize('NFD', text)
        text = re.sub(r'[\u0300-\u036f]', '', text)  
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)         
        text = re.sub(r'\s+', ' ', text).strip()     
        return text

    # Bước 2: Tìm quốc gia từ pycountry
    def match_country_from_pycountry(self, cleaned_text):
        for country in pycountry.countries:
            candidates = [
                country.name.lower(),
                getattr(country, 'official_name', '').lower(),
            ]
            for cand in candidates:
                if cand and cand in cleaned_text:
                    return country.name
        return None

    def match_country_manual(self, cleaned_text):
        for keyword, country in other_country_name.items():
            if keyword in cleaned_text:
                return country
        return None

    def match_country_by_city(self, cleaned_text):
        for keyword, country in city_list.items():
            if keyword in cleaned_text:
                return country
        return None
    def match_country_by_road(cleaned_text):
        for keyword, country in road_street_name.items():
            if keyword in cleaned_text:
                return country
        return None
# Tổng hợp
    def detect_country_full(self, address):
        cleaned = self.clean_text(address)

        country = self.match_country_from_pycountry(cleaned)
        if country:
            return country

        country = self.match_country_manual(cleaned)
        if country:
            return country

        country = self.match_country_by_city(cleaned)
        if country:
            return country

        country = self.match_country_by_road(cleaned)
        if country:
            return country
        return None
    

file_path = r"D:\MySteel\Data Hải quan\T1-2025\72-NK-T1.2025.xlsx"
data = convert_to_Excel(file_path)
print(data.df.isna().sum())

    


