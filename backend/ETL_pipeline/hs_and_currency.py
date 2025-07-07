import pandas as pd

class HSandMoneyExchange():
  def __init__(self, usd_rate, hs_dict):
    self.usd_rate = usd_rate
    self.hs_dict = hs_dict

  def unit_price_in_usd(self, rate):
    return round(rate/self.usd_rate,2)

  def exchange_to_usd(self, money, rate):
    if pd.isna(rate):
      rate = 1
    return round((money*rate)/self.usd_rate,2) 
  
  def hs_code(self, code):
    if pd.isna(code):
      return
    commodity = self.hs_dict[code]
    return commodity