import pandas as pd

df = pd.read_json("phone_specs.json")
phone_specs = {key.lower().replace(" ", "_"): (pd.json_normalize(df[key]) if isinstance(df[key][0], (dict, list)) else pd.DataFrame(df[key])) for key in df.columns}

phone_name = phone_specs["phone_name"].squeeze()
chipset = phone_specs["platform"]["chipset"].apply(lambda x: ", ".join([item.strip() for item in x]) if isinstance(x, list) else x)
battery_capacity = phone_specs["battery"]["batdescription1"].str.extract(r"(\d+)")[0] + " mAh"
charging_info = phone_specs["battery"]["Charging"].str.extract(r"(\d+\s*W)")[0]
price_info = phone_specs["misc"]["price"].str.split(" / ").str[0].apply(lambda x: f"{x[0]}{x[2:]}" if isinstance(x, str) and x and x[0] in "$€£₹" else f"€{x[6:9]}" if isinstance(x, str) and pd.notna(x) else x)
antutu_benchmark_score = phone_specs["tests"]["tbench"].str.extract(r"AnTuTu:\s*(\d+)")[0]
display_type_info = phone_specs["display"]["displaytype"].str.strip().str.split(",").apply(lambda x: ", ".join([item.strip() for item in x]) if isinstance(x, list) else x)
display_type, refresh_rate, brightness_from_display_type = display_type_info.str.split(",").str[0].str.strip(), display_type_info.str.extract(r"(\d+\s*Hz)")[0], display_type_info.str.extract(r"(\d+\s*nits)")[0]
brightness_from_tests = phone_specs["tests"]["Display"].str.extract(r"(\d+\s*nits)")[0]
brightness = brightness_from_tests.combine_first(brightness_from_display_type)

phone_data = pd.DataFrame({"phone_name": phone_name, "chipset": chipset, "battery_capacity": battery_capacity, "charging_info": charging_info, "price_info": price_info, "antutu_benchmark_score": antutu_benchmark_score, "display_type": display_type, "refresh_rate": refresh_rate, "brightness": brightness})
pd.set_option("display.float_format", "{:,.0f}".format)

phone_data["display_type"] = phone_data["display_type"].apply(lambda x: "OLED-Based" if pd.notna(x) and "OLED" in str(x).upper() else "LCD-Based")
phone_data["antutu_benchmark_score"] = pd.to_numeric(phone_data["antutu_benchmark_score"], errors="coerce").astype("Int64")
mean_scores_by_chipset = phone_data.groupby("chipset")["antutu_benchmark_score"].transform("mean").round().astype("Int64")
phone_data["antutu_benchmark_score"] = phone_data["antutu_benchmark_score"].fillna(mean_scores_by_chipset).astype("Int64")

def get_phone_data():
    return phone_data