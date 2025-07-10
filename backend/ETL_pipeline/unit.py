class UnitConverter:
    def __init__(self, unit_conversion):
        self.unit_conversion = unit_conversion

    def convert_to_tan(self, value, unit):
        if unit in self.unit_conversion:
            tan_value = value * self.unit_conversion[unit]
            return tan_value
        else:
            return None