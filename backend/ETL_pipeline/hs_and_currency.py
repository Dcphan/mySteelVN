import pandas as pd

class HSandMoneyExchange():
  def __init__(self, usd_rate, hs_dict, unit_dict):
    self.usd_rate = usd_rate
    self.hs_dict = hs_dict
    self.unit_dict = unit_dict

  def ti_gia_conversion(self, rate):
    if pd.isna(rate):
        rate = 1
    return rate/(self.usd_rate)

  def unit_conversion(self, unit_price, forex_rate, unit):
    if unit not in self.unit_dict:
        return None
    if forex_rate is None:
        forex_rate = 1
    
    usd_price = unit_price * forex_rate
    usd_price_per_ton = usd_price / self.unit_dict[unit]
    return usd_price_per_ton

  def hs_code(self, code):
    if pd.isna(code):
      return
    commodity = self.hs_dict.get(code) # Use .get() to avoid KeyError
    return commodity