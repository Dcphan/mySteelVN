MASS_PATTERNS = [
    r'(\d+\.?\d*)\s*kg\s*/\s*(\d+)\s*T[ấa]m', # eg: 219kg/50Tấm
    r'(\d+\.?\d*)kg\s*/\s*t[ấa]m',                        # eg: 23.55kg/tấm
    r'\(?\s*(\d+\.?\d*)\s*kg\s*/\s*(\d+)\s*t[ấa]m\s*\)?',  # ví dụ: (219kg/50Tấm), 219kg/50Tấm
    r'\(?\s*(\d+\.?\d*)\s*kg\s*/\s*t[ấa]m\s*\)?',          # ví dụ: (7kg/tấm), 7kg/tấm
    r'(\d+)\s*(c[áa]i|chiếc|t[ấa]m|thanh|cây|đ[ơo]n v[ịị]|pcs?|pces?|piece|unit[s]?)\s*=\s*(\d+\.?\d*)\s*(?:kgs|kg|g)',
    r'(\d+)\s*(?:cái|pcs|pce|chiếc|p)?\s*=\s*([\d.]+)\s*(?:kgs|kg|g)',
    r'([\d.]+)\s*(?:kgs|kg|g)?\s*=\s*([\d,]+)\s*(?:pcs|pce|cái|chiếc|cai)',
]

NON_CONVERTABLE_PATTERNS = [
    r'dày\s*([0-9.,]+)\s*mm.*?rộng\s*từ\s*([0-9.,]+)\s*mm\s*đến\s*([0-9.,]+)\s*mm' # eg: 3 lớp dày 2.3mm rộng từ 150mm đến 930mm
]

patterns = [
    # Case 1: Each number has its own unit
    r'(\d+[\.,]?\d*)\s*(mm|cm|m)\s*[x×*]\s*(\d+[\.,]?\d*)\s*(mm|cm|m)\s*[x×*]\s*(\d+[\.,]?\d*)\s*(mm|cm|m)',

    # Case 2: Unit at the end (common)
    r'\(?\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*\)?\s*(mm|cm|m)',

    # Case 3: With labels like dày, rộng, dài
    r'dày[:\s]*(\d+[\.,]?\d*)\s*(mm|cm|m)\s*[x×*]\s*rộng[:\s]*(\d+[\.,]?\d*)\s*(mm|cm|m)\s*[x×*]\s*(\d+[\.,]?\d*)(?:\s*(mm|cm|m))?',

    # Case 4: KT + dày format
    r'kt[:\s]*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*(mm|cm|m),?\s*d[àa]y[:\s]*(\d+[\.,]?\d*)\s*(mm|cm|m)',

    # Case 5: W L T
    r'w(\d+[\.,]?\d*)\s*[x×*]\s*l(\d+[\.,]?\d*)\s*[x×*]\s*t(\d+[\.,]?\d*)\s*(mm|cm|m)?',

    # (dài) 2500 x (rộng) 1000mm, dày 0.45mm
    r'dày\s*(\d+\.?\d*)\s*(mm|cm|m)?[^(\d]*?\(dài\)\s*(\d+\.?\d*)\s*[x×*]\s*\(rộng\)\s*(\d+\.?\d*)\s*(mm|cm|m)?',

    # khổ x dày
    r'khổ\s*([\d.,]+)\s*(mm|cm|m)?\s*[x×*]\s*([\d.,]+)\s*(mm|cm|m)?.*?dày\s*([\d.,]+)\s*(mm|cm|m)?',

    # 3D with tolerance
    r'(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\+?\d*[\.,]?\d*\s*(mm|cm|m)',

    # (0.8 x 385 x 662.5) x mm
    r'\(\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*\)\s*[x×*]?\s*(mm|cm|m)',

    # kích thước X x Y + độ dày Z
    r'kích\s*thước\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?[^.\d]*?đ[ộo]\s*d[àa]y\s*(\d+[\.,]?\d*)\s*(mm|cm|m)',

    # ✅ Case dài rộng cao (v1)
    r'd[àa]i\s*(\d+[\.,]?\d*)\s*[*x×]\s*r[ộo]ng\s*(\d+[\.,]?\d*)\s*[*x×]\s*c[aoô]\s*(\d+[\.,]?\d*)\s*\(?(mm|cm|m)\)?',

    # ✅ tolerance values
    r'(\d+[\.,]?\d*)\s*\(\+?[-/.\d]+\)\s*[x×*]\s*(\d+[\.,]?\d*)\s*\(\+?[-/.\d]+\)\s*[x×*]\s*(\d+[\.,]?\d*)\s*\(\+?[-/.\d]+\)\s*(mm|cm|m)',

    # ✅ dài rộng cao (v2) — fix dấu * thiếu cách
    r"DÀI\s*(\d+)\s*[*x]\s*RỘNG\s*(\d+)\s*[*x]\s*CAO\s*(\d+)\s*\((mm|cm|m)\)",

    r"(\d+ \(\+\d+\.\d+/\+\d+\.\d+\) [x*] \d+ \(\+\d+\.\d+/\+\d+\.\d+\) [x*] \d+ \(\+\d+\.\d+/\+\d+\.\d+\) (mm|cm|m))",

    r"(\d+\.?\d*)\s*[*x]\s*(\d+\.?\d*)\s*[*x]\s*(\d+\.?\d*)\s*\((mm|cm|m)\)",

    r'(\d+[\.,]?\d*)\s*-\s*(\d+[\.,]?\d*)\s*-\s*(\d+[\.,]?\d*)\s*(mm|cm|m)',

    r'\(\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*\)',

    r'd[àa]i[:\s]*(\d+[\.,]?\d*)\s*(mm|cm|m)[,;\s]+r[ộo]ng[:\s]*(\d+[\.,]?\d*)\s*(mm|cm|m)[,;\s]+d[àa]y[:\s]*(\d+[\.,]?\d*)\s*(mm|cm|m)',

        # ✅ Case: 0.109*48*96 INCH or x-separated
    r'\(?\s*(\d+[\.,]?\d*)\s*[*x×]\s*(\d+[\.,]?\d*)\s*[*x×]\s*(\d+[\.,]?\d*)\s*\)?\s*(inch|in)\b',

    r'\(.*?d[àa]i\s*(\d+[\.,]?\d*)\s*[x×*]\s*r[ộo]ng\s*(\d+[\.,]?\d*)\s*[x×*]\s*d[àa]y\s*(\d+[\.,]?\d*)\s*\)?\s*(mm|cm|m)?',

    r'kt[:\s]*d\s*(\d+[\.,]?\d*)\s*(mm|cm|m)\s*[*x×]\s*r\s*(\d+[\.,]?\d*)\s*(mm|cm|m)\s*[*x×]?\s*d[àa]y\s*(\d+[\.,]?\d*)\s*(mm|cm|m)',
    r'\(\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?\s*\)\s*[x×*]\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*(?:\(?\s*(mm|cm|m)\s*\)?)?',
    r"dài\s*(\d+\.?\d*)\s*[*x]\s*rộng\s*(\d+\.?\d*)\s*[*x]\s*cao\s*(\d+\.?\d*)\s*\((mm|cm|m)\)",
    r'd[ộo]\s*d[àa]y\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?[^.\d]*?kích\s*thước\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?',
    r"dày\s*(\d+\.?\d*)\s*(mm|cm|m).*?kích thước\s*(\d+\.?\d*)\s*[x*]\s*(\d+\.?\d*)\s*(mm|cm|m)",
    r'kích\s*thước\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?\s*[x×*]\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?[^.\d]*?đ[ộo]\s*d[àa]y\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?',

        # ✅ dài x rộng x dày (có đơn vị riêng từng phần)
    r'd[àa]i\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?\s*[x×*]\s*r[ộo]ng\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?\s*[x×*]\s*d[àa]y\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?',

    # ✅ rộng x dài x dày (trường hợp đảo chiều)
    r'r[ộo]ng\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?\s*[x×*]\s*d[àa]i\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?\s*[x×*]\s*d[àa]y\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?',

    r"(rộng\s*\d+\.?\d*\s*mm,\s*dài\s*\d+\.?\d*\s*mm,\s*dày\s*\d+\.?\d*\s*mm)",

        # ✅ Case: dày 0.45mm *1.2*2.0m
    r'(\d+[\.,]?\d*)\s*(mm|cm|m)?\s*[*x×]\s*(\d+[\.,]?\d*)\s*[*x×]\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?',
        # ✅ Case: 4ly x 1500 x 3000 ➜ dày (ly) × rộng × dài
    r'(\d+)\s*ly\s*[x×*]\s*(\d+[\.,]?\d*)\s*[x×*]\s*(\d+[\.,]?\d*)',
        # ✅ Case: 16mm THK x 6000mmL x 1500mmW
    r'(\d+[\.,]?\d*)\s*(mm|cm|m)?\s*thk\s*[x×*]\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?l\s*[x×*]\s*(\d+[\.,]?\d*)\s*(mm|cm|m)?w',

    r'd[àa]y\s*([\d.,]+)\s*(mm|cm|m)?\s*,?\s*r[ộo]ng\s*([\d.,]+)\s*(mm|cm|m)?\s*,?\s*d[àa]i\s*([\d.,]+)\s*(mm|cm|m)?',
    r't\s*([\d.,]+)[-_\s]*w\s*([\d.,]+)[-_\s]*l\s*([\d.,]+)\s*(mm|cm|m)?',
]

patterns_non_unit = [
    # ✅ General pattern: 160x308x15.5 (no unit, assume mm)
    r'\(?\s*(\d+[\.,]?\d*)\s*[*x×]\s*(\d+[\.,]?\d*)\s*[*x×]\s*(\d+[\.,]?\d*)\s*\)?',
    # ✅ Case: 200x500xT3 or 200×500×T3.0
    r'(\d+)[x×*](\d+)[x×*]t(\d+)[\.,]?\d*',
        # ✅ Case: 3.0T*159.3*1745 ➜ dày*T*rộng*dài
    r'(\d+[\.,]?\d*)\s*t\s*[*x×]\s*(\d+[\.,]?\d*)\s*[*x×]\s*(\d+[\.,]?\d*)',

]

cylinder_patterns = [
    r'([\d.]+)\s*[x×*]\s*([\d.]+)\s*(mm|cm|m)',
    r'\(f[=:=]?\s*[\d.]+\s*(mm|cm|m)?\s*,\s*d[àa]y\s*[\d.]+\s*(mm|cm|m)?\)',
    r'\(\s*[\d.]+\s*[x×*]\s*[\d.]+\s*\)\s*(mm|cm|m)',
    r'\((?:\s*phi\s*[\d.]+\s*(?:mm|cm|m)\s*,\s*d[àa]i\s*[\d.]+\s*(?:mm|cm|m)|\s*d[àa]i\s*[\d.]+\s*(?:mm|cm|m)\s*,\s*phi\s*[\d.]+\s*(?:mm|cm|m))\)',
    r'\(?\s*(phi)?\s*([\d.,]+)\s*(mm|cm|m)?\s*[x×*]\s*d[àa]i\s*([\d.,]+)\s*(mm|cm|m)?\s*\)?',
    r'\(?\s*(phi)?\s*([\d.,]+)\s*(mm|cm|m)?\s*[x×*]\s*([\d.,]+)\s*(mm|cm|m)?\s*\)?',
    r'd\s*=?\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?[,;]?\s*(chi[ềe]u\s*d[àa]i|d[àa]i)\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?',
    r'(chi[ềe]u\s*d[àa]i|d[àa]i)\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?[,;]?\s*d\s*=?\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?',
    r'phi\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?[,;\s]*d[àa]i\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?',
    r'd[àa]i\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?[,;\s]*phi\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?',
    r'đ[ườư]ng\s*k[íi]nh\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?[,;\s]*chi[ềe]u\s*d[àa]i[:\s]*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?',
    r'chi[ềe]u\s*d[àa]i[:\s]*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?[,;\s]*đ[ườư]ng\s*k[íi]nh\s*(\d+(?:[\.,]\d+)?)\s*(mm|cm|m)?',
    r'd[àa]y[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*d[àa]i[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*r[ộo]ng[:\s]*([\d.,]+)\s*(mm|cm|m)?',
    r'd[àa]i[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*r[ộo]ng[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*d[àa]y[:\s]*([\d.,]+)\s*(mm|cm|m)?',
    r'đường\s*kính[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*chi[ềê]u\s*d[àa]i[:\s]*([\d.,]+)\s*(mm|cm|m)?',
    r'chi[ềê]u\s*d[àa]i[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*đường\s*kính[:\s]*([\d.,]+)\s*(mm|cm|m)?',
    r'phi\s*([\d.,]+)\s*(mm|cm|m)?[,;\s]*chi[ềê]u\s*d[àa]i[:\s]*([\d.,]+)\s*(mm|cm|m)?',
    r'chi[ềê]u\s*d[àa]i[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*phi\s*([\d.,]+)\s*(mm|cm|m)?',
    r'tiết\s*diện\s*([\d.,]+)\s*(mm|cm|m)?[,;\s]*d[àa]i\s*([\d.,]+)\s*(mm|cm|m)?',
    r'([\d.,]+)\(l\)\s*[x×*]\s*([\d.,]+)\(t\)\s*[x×*]\s*([\d.,]+)\(w\)\s*(mm|cm|m)?',

]

special_circle_pattern = [
    r'chi[ềê]u\s*d[àa]i\s*[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*chi[ềê]u\s*r[ộo]ng\s*[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*đ[ưư]ờng\s*k[íi]nh\s*ngo[àa]i\s*[:\s]*([\d.,]+)\s*(mm|cm|m)?[,;\s]*đ[ưư]ờng\s*k[íi]nh\s*l[ỗo]\s*[:\s]*([\d.,]+)\s*(mm|cm|m)?',

]
