import re
import math

class SteelParser:
    DENSITY = 7.85  # kg/m³ for steel
    UNIT_TO_M = {'mm': 0.1, 'cm': 1, 'm': 100, 'inch': 2.54, 'in': 2.54}

    def __init__(self, patterns, mass_patterns=None, patterns_non_unit = None, fallback_patterns = None,cylinder_patterns=None, special_circle_pattern=None):
        self.patterns = patterns
        self.mass_patterns = mass_patterns or []
        self.patterns_non_unit = patterns_non_unit or []
        self.fallback_patterns = fallback_patterns or []
        self.cylinder_patterns = cylinder_patterns or []
        self.special_circle_pattern = special_circle_pattern or []

    def normalize_number(self, value):
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                # Remove trailing dot before converting to float
                return float(value.rstrip(".").replace(",", "."))
            except ValueError:
                return None
        return None

    def extract_dimensions(self, s):
      # Normalize signs and formatting
      s = re.sub(r'[*×X]', 'x', s)
      s = re.sub(r'\(\s*\+?[\d.]+\s*/\s*\+?[\d.]+\s*\)', '', s)  # remove (+0.1/+0.3)
      s = re.sub(r'\(\+?/-?.*?\)', '', s)  # remove (+/-...) tolerances
      s = s.replace(",", ".")
      s = s.strip().lower()

      pattern_kho = re.search(r'khổ\s*([\d.]+)\s*(mm|cm|m)?\s*x\s*([\d.]+)\s*(mm|cm|m)?.*dày\s*([\d.]+)\s*(mm|cm|m)?', s)
      if pattern_kho:
          width_val = self.normalize_number(pattern_kho.group(1))
          width_unit = pattern_kho.group(2) or 'mm'
          length_val = self.normalize_number(pattern_kho.group(3))
          length_unit = pattern_kho.group(4) or width_unit
          thickness_val = self.normalize_number(pattern_kho.group(5))
          thickness_unit = pattern_kho.group(6) or 'mm'

          if any(v is None for v in [width_val, length_val, thickness_val]):
              return []

          width = width_val * self.UNIT_TO_M.get(width_unit, 0.001)
          length = length_val * self.UNIT_TO_M.get(length_unit, 0.001)
          thickness = thickness_val * self.UNIT_TO_M.get(thickness_unit, 0.001)

          return [round(length,4), round(width,4), round(thickness,4)]

      pattern_kt = re.search(
        r'kt\s*([\d.]+)\s*x\s*([\d.]+)\s*(mm|cm|m)?[,;\s]*dày\s*([\d.]+)\s*(mm|cm|m)?',
        s, re.IGNORECASE)

      if pattern_kt:
          width_val = self.normalize_number(pattern_kt.group(1))
          length_val = self.normalize_number(pattern_kt.group(2))
          width_unit = pattern_kt.group(3) or 'm'      # mặc định nếu không có đơn vị là mét
          thickness_val = self.normalize_number(pattern_kt.group(4))
          thickness_unit = pattern_kt.group(5) or 'mm' # mặc định dày là mm nếu không có đơn vị

          if any(v is None for v in [width_val, length_val, thickness_val]):
              return []

          width = width_val * self.UNIT_TO_M.get(width_unit, 1)
          length = length_val * self.UNIT_TO_M.get(width_unit, 1)
          thickness = thickness_val * self.UNIT_TO_M.get(thickness_unit, 0.001)

          return [round(length, 4), round(width, 4), round(thickness, 4)]




      # ✅ Case: thickness-first shorthand e.g. 3.0t*159.3*1745
      t_pattern = re.match(r'([\d.]+)\s*t\s*[x×*]\s*([\d.]+)\s*[x×*]\s*([\d.]+)', s)
      if t_pattern:
          thickness = self.normalize_number(t_pattern.group(1))
          width = self.normalize_number(t_pattern.group(2))
          length = self.normalize_number(t_pattern.group(3))

          if any(v is None for v in [width, length, thickness]):
              return []

          thickness *= self.UNIT_TO_M['mm']
          width *= self.UNIT_TO_M['mm']
          length *= self.UNIT_TO_M['mm']
          return [round(length, 4), round(width, 4), round(thickness, 4)]

       # ✅ Sửa lại phần dài..., rộng..., dày... cho linh hoạt thứ tự và dấu phân cách
      pattern_dims = r'(dài|rộng|dày)\s*([\d.]+)\s*(mm|cm|m)'
      matches = re.findall(pattern_dims, s, re.IGNORECASE)
      if matches:
          dims = {'dài': None, 'rộng': None, 'dày': None}
          units = {'dài': None, 'rộng': None, 'dày': None}
          for dim, val, unit in matches:
              dim = dim.lower()
              dims[dim] = self.normalize_number(val)
              units[dim] = unit.lower()

          # Kiểm tra đủ 3 chiều
          if all(v is not None for v in dims.values()):
              # Chuyển đơn vị về mét (hoặc mm tùy bạn)
              length = dims['dài'] * self.UNIT_TO_M.get(units['dài'], 0.001)
              width = dims['rộng'] * self.UNIT_TO_M.get(units['rộng'], 0.001)
              thickness = dims['dày'] * self.UNIT_TO_M.get(units['dày'], 0.001)
              return [round(length, 4), round(width, 4), round(thickness, 4)]


      # 🔥 Special case: "dày 2mm, kích thước: 800mm*1200mm"
      thickness_match = re.search(r'dày\s*([\d.]+)\s*(mm|cm|m)?', s)
      dimension_match = re.search(r'kích thước[:\s]*([\d.]+)\s*(mm|cm|m)?\s*[x×*]\s*([\d.]+)\s*(mm|cm|m)?', s)
      if thickness_match and dimension_match:
          thickness_val = self.normalize_number(thickness_match.group(1))
          thickness_unit = thickness_match.group(2) or 'mm'

          dim1_val = self.normalize_number(dimension_match.group(1))
          dim1_unit = dimension_match.group(2) or thickness_unit

          dim2_val = self.normalize_number(dimension_match.group(3))
          dim2_unit = dimension_match.group(4) or thickness_unit

          if any(v is None for v in [thickness_val, dim1_val, dim2_val]):
              return []

          return [
              round(thickness_val * self.UNIT_TO_M.get(thickness_unit, 0.001), 4),
              round(dim1_val * self.UNIT_TO_M.get(dim1_unit, 0.001), 4),
              round(dim2_val * self.UNIT_TO_M.get(dim2_unit, 0.001), 4)
          ]

      # Case: (0.6mm) + x 1250 x 2500
      paren_match = re.search(r'\(([\d.]+)\s*(mm|cm|m)?\)', s)
      if paren_match:
          num = self.normalize_number(paren_match.group(1))
          if num is None:
              return []
          unit = paren_match.group(2) or 'mm'
          if unit not in self.UNIT_TO_M:
              unit = 'mm'
          first_value = round(num * self.UNIT_TO_M[unit], 4)

          # Remove parenthesis content and find dimensions after x
          rest = re.sub(r'\([^)]+\)', '', s)
          rest_dims = re.findall(r'x\s*([\d.]+)', rest)
          if len(rest_dims) >= 2:
              second = self.normalize_number(rest_dims[0])
              third = self.normalize_number(rest_dims[1])
              if any(v is None for v in [second, third]):
                  return []
              second = round(second * self.UNIT_TO_M[unit], 4)
              third = round(third * self.UNIT_TO_M[unit], 4)
              return [first_value, second, third]

      # Case: Shared unit at end
      shared_unit_match = re.search(r'([\d.]+\s*x\s*[\d.]+\s*x\s*[\d.]+)\s*x?\s*([a-z]+)', s)
      if shared_unit_match:
          nums = re.split(r'\s*x\s*', shared_unit_match.group(1))
          unit = shared_unit_match.group(2)
          if unit not in self.UNIT_TO_M:
              unit = 'mm'
          result = []
          for n in nums:
              normalized_n = self.normalize_number(n)
              if normalized_n is None:
                  return []
              result.append(round(normalized_n * self.UNIT_TO_M[unit], 4))
          return result

      # Default: 3 numbers with optional units, fallback to mm
      # Modified to handle trailing decimal points
      matches = re.findall(r'([\d.]+)\s*(mm|cm|m)?', s)
      filtered = [(num.rstrip('.'), unit or 'mm') for num, unit in matches if num.strip()]


      if len(filtered) == 3:
          result = []
          for num, unit in filtered:
              if unit not in self.UNIT_TO_M:
                  unit = 'mm'
              try:
                  # Remove trailing dot if present before converting to float
                  num = num.rstrip('.')
                  result.append(round(float(num) * self.UNIT_TO_M[unit], 4))
              except ValueError:
                  return [] # Return empty list if conversion still fails
          return result

      return []



    def extract_volume_string(self, text):
        text = text.lower()
        for pattern in self.mass_patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group()

        for pattern in self.patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group()

        for pattern in self.patterns_non_unit:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group()

        for pattern in self.cylinder_patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group()

        for pattern in self.special_circle_pattern:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group()

        for pattern in self.fallback_patterns:
            if re.fullmatch(pattern, text, flags=re.IGNORECASE):
                return 0.5 / 1000  # Default volume in m³


        return None

    def extract_mass_to_ton(self, s):
      if not isinstance(s, str):
          return None

      s = s.lower().replace(",", ".").strip()

      # Match formats like '75 kg', '75kg/tấm', '75kg / piece'
      match = re.search(r'([\d.]+)\s*kg', s)
      if match:
          kg = float(match.group(1))
          tons = round(kg / 1000, 4)  # Convert kg to tons
          return tons

      return None

    def extract_cylinder_dimensions(self, s):
        # Normalize formatting
        s = re.sub(r'[*×X]', 'x', s)
        s = s.replace(",", ".")
        s = s.strip().lower()

        # Case 5: d32mm, chiều dài 317.5mm
        match = re.search(r'd\s*([\d.]+)\s*(mm|cm|m)[.\s]*chiều\s*dài\s*([\d.]+)\s*(mm|cm|m)', s)
        if match:
            try:
                diameter = self.normalize_number(match.group(1))
                d_unit = match.group(2)
                length = self.normalize_number(match.group(3))
                l_unit = match.group(4)

                if any(v is None for v in [diameter, length]):
                    return []

                d_m = diameter * self.UNIT_TO_M.get(d_unit, 0.001)
                l_m = length * self.UNIT_TO_M.get(l_unit, 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []


        # Pattern 1: 92 x 121 mm
        pattern_1 = re.search(r'([\d.]+)\s*x\s*([\d.]+)\s*(mm|cm|m)\b', s)
        if pattern_1:
            try:
                diameter = self.normalize_number(pattern_1.group(1))
                length = self.normalize_number(pattern_1.group(2))
                unit = pattern_1.group(3) or 'mm'

                if any(v is None for v in [diameter, length]):
                    return []

                d_m = diameter * self.UNIT_TO_M.get(unit, 0.001)
                l_m = length * self.UNIT_TO_M.get(unit, 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []

        # Pattern 2: phi 70 dài 739mm
        pattern_2 = re.search(r'phi\s*([\d.]+)\s*(mm|cm|m)?[,;\s]*d[àa]i\s*([\d.]+)\s*(mm|cm|m)?', s)
        if pattern_2:
            try:
                diameter = self.normalize_number(pattern_2.group(1))
                d_unit = pattern_2.group(2) or 'mm'
                length = self.normalize_number(pattern_2.group(3))
                l_unit = pattern_2.group(4) or d_unit

                if any(v is None for v in [diameter, length]):
                    return []

                d_m = diameter * self.UNIT_TO_M.get(d_unit, 0.001)
                l_m = length * self.UNIT_TO_M.get(l_unit, 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []

        # Pattern 3: d42mm, chiều dài 380.5mm
        pattern_3 = re.search(r'd\s*=?\s*([\d.]+)\s*(mm|cm|m)?[,;\s]*(?:chi[ềe]u\s*)?d[àa]i\s*([\d.]+)\s*(mm|cm|m)?', s)
        if pattern_3:
            try:
                diameter = self.normalize_number(pattern_3.group(1))
                d_unit = pattern_3.group(2) or 'mm'
                length = self.normalize_number(pattern_3.group(3))
                l_unit = pattern_3.group(4) or d_unit

                if any(v is None for v in [diameter, length]):
                    return []

                d_m = diameter * self.UNIT_TO_M.get(d_unit, 0.001)
                l_m = length * self.UNIT_TO_M.get(l_unit, 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []


        # ✅ Case 4: (0.8 x 1060)mm — shared unit after parentheses
        pattern_4 = re.search(r'\(\s*([\d.]+)\s*x\s*([\d.]+)\s*\)\s*(mm|cm|m)', s)
        if pattern_4:
            try:
                diameter = self.normalize_number(pattern_4.group(1))
                length = self.normalize_number(pattern_4.group(2))
                unit = pattern_4.group(3)
                if any(v is None for v in [diameter, length]):
                    return []
                d_m = diameter * self.UNIT_TO_M.get(unit, 0.001)
                l_m = length * self.UNIT_TO_M.get(unit, 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []


        pattern5 = re.search(r'dài\s*([\d.]+)\s*(mm|cm|m)[.,;\s]*phi\s*([\d.]+)\s*(mm|cm|m)', s)
        if pattern5:
          try:
            length = self.normalize_number(pattern5.group(1))
            length_unit = pattern5.group(2)
            diameter = self.normalize_number(pattern5.group(3))
            diameter_unit = pattern5.group(4)

            if any(v is None for v in [diameter, length]):
                return []

            l_m = length * self.UNIT_TO_M.get(length_unit.lower(), 0.001)
            d_m = diameter * self.UNIT_TO_M.get(diameter_unit.lower(), 0.001)

            return [round(l_m, 4), round(d_m, 4)]
          except ValueError:
            return []


        pattern_6 = re.search(r'phi\s*([\d.]+)\s*(mm|cm|m)?[.,*\s]*dài\s*([\d.]+)\s*(mm|cm|m)?', s)
        if pattern_6:
            try:
                diameter = self.normalize_number(pattern_6.group(1))
                d_unit = pattern_6.group(2) or 'mm'  # default to mm if missing
                length = self.normalize_number(pattern_6.group(3))
                l_unit = pattern_6.group(4) or 'mm'  # default to mm if missing

                if any(v is None for v in [diameter, length]):
                    return []

                d_m = diameter * self.UNIT_TO_M.get(d_unit.lower(), 0.001)
                l_m = length * self.UNIT_TO_M.get(l_unit.lower(), 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []

        pattern_7 = re.search(r'([\d.]+)\s*(mm|cm|m)?\s*[xX]\s*([\d.]+)\s*(mm|cm|m)?', s)
        if pattern_7:
            try:
                diameter = self.normalize_number(pattern_7.group(1))
                d_unit = pattern_7.group(2) or 'mm'  # default to mm if missing
                length = self.normalize_number(pattern_7.group(3))
                l_unit = pattern_7.group(4) or 'mm'  # default to mm if missing

                if any(v is None for v in [diameter, length]):
                    return []

                d_m = diameter * self.UNIT_TO_M.get(d_unit.lower(), 0.001)
                l_m = length * self.UNIT_TO_M.get(l_unit.lower(), 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []

        pattern_8 = re.search(r'phi\s*([\d.]+)\s*(mm|cm|m)?[.,;\s]*chiều?\s*d[àa]i\s*([\d.]+)\s*(mm|cm|m)?', s)
        if pattern_8:
            try:
                diameter = self.normalize_number(pattern_8.group(1))
                d_unit = pattern_8.group(2) or 'mm'  # default to mm if missing
                length = self.normalize_number(pattern_8.group(3))
                l_unit = pattern_8.group(4) or 'mm'  # default to mm if missing

                if any(v is None for v in [diameter, length]):
                    return []

                d_m = diameter * self.UNIT_TO_M.get(d_unit.lower(), 0.001)
                l_m = length * self.UNIT_TO_M.get(l_unit.lower(), 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []

        pattern_9 = re.search(r'đường\s*kính\s*([\d.]+)\s*(mm|cm|m)?[.,;:\s]*chiều\s*dài\s*[:]?[\s]*([\d.]+)\s*(mm|cm|m)?', s)
        if pattern_9:
            try:
                diameter = self.normalize_number(pattern_9.group(1))
                d_unit = pattern_9.group(2) or 'mm'  # default to mm if missing
                length = self.normalize_number(pattern_9.group(3))
                l_unit = pattern_9.group(4) or 'mm'  # default to mm if missing

                if any(v is None for v in [diameter, length]):
                    return []

                d_m = diameter * self.UNIT_TO_M.get(d_unit.lower(), 0.001)
                l_m = length * self.UNIT_TO_M.get(l_unit.lower(), 0.001)
                return [round(l_m, 4), round(d_m, 4)]
            except ValueError:
                return []

        return []


    def compute_mass_from_description(self, description):
        process_description = self.extract_volume_string(description)
        if not process_description or not isinstance(process_description, str):
            return None

        # Step 1: Extract known mass
        mass_ton = self.extract_mass_to_ton(process_description)
        if mass_ton is not None:
            return mass_ton

        # Step 2: Try rectangular volume
        for pat in self.patterns:
            if match := re.search(pat, process_description, flags=re.IGNORECASE):
                dims_text = match.group()
                dims_meters = self.extract_dimensions(dims_text)
                if len(dims_meters) == 3:
                    # Calculate volume in m³
                    volume_m3 = dims_meters[0] * dims_meters[1] * dims_meters[2]
                    # Convert volume (m³) to mass (tons)
                    mass_kg = volume_m3 * self.DENSITY
                    mass_ton = mass_kg / 1000
                    return round(mass_ton, 4)

        for pat in self.patterns_non_unit:
            if match := re.search(pat, process_description, flags=re.IGNORECASE):
                dims_text = match.group()
                dims_meters = self.extract_dimensions(dims_text)
                if len(dims_meters) == 3:
                    # Calculate volume in m³
                    volume_m3 = dims_meters[0] * dims_meters[1] * dims_meters[2]
                     # Convert volume (m³) to mass (tons)
                    mass_kg = volume_m3 * self.DENSITY
                    mass_ton = mass_kg / 1000
                    return round(mass_ton, 4)

        # Step 3: Try cylinder volume
        dims_cylinder = self.extract_cylinder_dimensions(process_description)
        if len(dims_cylinder) == 2:
            length, diameter = dims_cylinder
            # Calculate volume in m³
            volume_m3 = math.pi * (diameter / 2) ** 2 * length
            # Convert volume (m³) to mass (tons)
            mass_kg = volume_m3 * self.DENSITY
            mass_ton = mass_kg / 1000
            return round(mass_ton, 4)

        # Step 4: Fallback
        for pat in self.fallback_patterns:
            if re.fullmatch(pat, process_description, flags=re.IGNORECASE):
                # Default volume in m³, convert to tons
                volume_m3 = 0.5 / 1000
                mass_kg = volume_m3 * self.DENSITY
                mass_ton = mass_kg / 1000
                return round(mass_ton, 4)

        return None