import re

with open("phone_specs.json", "r", encoding= "utf-8") as f:
    data = f.read()

# Extract All Camera's Megapixel Values
mp_values = re.findall(r'(\d+)\s*MP', data)
print("Megapixel Values: ", mp_values)

# Extract All 5G bands
net5g_match = re.findall(r'"net5g":\s*"(.*?)"', data)

print("5G Bands:", net5g_match)

# Extract All GHz CPU Core Speeds
ghz_speeds = re.findall(r'(\d+\.\d+)\s*GHz', data)
print("GHz CPUs Speeds:", ghz_speeds)

# Extract All Models
models_match = re.findall(r'"models":\s*"(.*?)"', data)

print("Phones Models:", models_match)


# Extract All USD Prices
pattern = r'\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'


usd_prices = re.findall(pattern, data)

print("Phones Prices: ", usd_prices)