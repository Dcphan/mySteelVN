import pycountry
import re
import unicodedata
import numpy as np

class DetectCountry():
    def __init__(self, other_country_name, city_list, road_street_name):
        self.other_country_name = other_country_name
        self.city_list = city_list
        self.road_street_name = road_street_name


    def combine_address(self, part1, part2, part3, part4):
    # Create a list of all parts
        parts = [part1, part2, part3, part4]
        
        # Replace None or NaN with a space, and ensure all parts are strings
        cleaned_parts = [str(p).strip() if p not in [None, np.nan] else " " for p in parts]
        
        # Concatenate non-empty parts with commas
        full_address = ", ".join([p for p in cleaned_parts if p and p.strip()])
        
        return full_address

        

    def clean_text(self, text):
        if not isinstance(text, str):
            return ""
        text = unicodedata.normalize('NFD', text)
        text = re.sub(r'[\u0300-\u036f]', '', text)  # Bỏ dấu
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)         # Bỏ dấu câu
        text = re.sub(r'\s+', ' ', text).strip()     # Chuẩn hóa khoảng trắng
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
        for keyword, country in self.other_country_name.items():
            if keyword in cleaned_text:
                return country
        return None

    def match_country_by_city(self, cleaned_text):
        for keyword, country in self.city_list.items():
            if keyword in cleaned_text:
                return country
        return None
    
    def match_country_by_road(self, cleaned_text):
        for keyword, country in self.road_street_name.items():
            if keyword in cleaned_text:
                return country
        return None
    
    # Tổng hợp
    def detect_country_full(self, address: list):
        if len(address) > 1:
            address = self.combine_address(address[0], address[1], address[2], address[3])
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
    
