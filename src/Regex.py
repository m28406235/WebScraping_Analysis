import pandas as pd

phone_specs_df = pd.read_json("phone_specs.json")

normalized_phone_specs = {
    column_name.lower().replace(" ", "_"): (
        pd.json_normalize(phone_specs_df[column_name])
        if isinstance(phone_specs_df[column_name][0], (dict, list))
        else pd.DataFrame(phone_specs_df[column_name])
    )
    for column_name in phone_specs_df.columns
}

phone_names = normalized_phone_specs["phone_name"].squeeze()
chipsets = normalized_phone_specs["platform"]["chipset"].apply(
    lambda chipset: ", ".join([item.split(" (")[0].strip() for item in chipset])
    if isinstance(chipset, list)
    else chipset.split(" (")[0].strip()
    if isinstance(chipset, str)
    else chipset
)
battery_capacities = normalized_phone_specs["battery"]["batdescription1"].str.extract(r"(\d+)")[0].fillna(0).astype(int)
charging_speeds = normalized_phone_specs["battery"]["Charging"].str.extract(r"(\d+)")[0].fillna(0).astype(int)
prices = normalized_phone_specs["misc"]["price"].str.split(" / ").str[0].apply(
    lambda price: f"{price[0]}{price[1:].replace(',', '')}" if isinstance(price, str) and price and price[0] in "$€£₹"
    else f"€{price[6:9].replace(',', '')}" if isinstance(price, str) and pd.notna(price)
    else price
)
antutu_scores = normalized_phone_specs["tests"]["tbench"].str.extract(r"AnTuTu:\s*(\d+)")[0].fillna(0).astype(int)
display_info = normalized_phone_specs["display"]["displaytype"].str.strip().str.split(",").apply(
    lambda display: ", ".join([item.strip() for item in display]) if isinstance(display, list) else display
)
display_types = display_info.str.split(",").str[0].str.strip()
refresh_rates = display_info.str.extract(r"(\d+)\s*Hz")[0].astype("Int64")
brightness_from_display_info = display_info.str.extract(r"(\d+)\s*nits")[0]
brightness_from_tests = normalized_phone_specs["tests"]["Display"].str.extract(r"(\d+)\s*nits")[0]
brightness_levels = brightness_from_tests.combine_first(brightness_from_display_info).astype("Int64")

processed_phone_data = pd.DataFrame({
    "phone_name": phone_names,
    "chipset": chipsets,
    "battery_capacity": battery_capacities,
    "charging_speed": charging_speeds,
    "price": prices,
    "antutu_score": antutu_scores,
    "display_type": display_types,
    "refresh_rate": refresh_rates,
    "brightness": brightness_levels
})

pd.set_option("display.float_format", "{:,.0f}".format)

processed_phone_data["display_type"] = processed_phone_data["display_type"].apply(
    lambda display: "OLED-Based" if pd.notna(display) and "OLED" in str(display).upper() else "LCD-Based"
)
processed_phone_data["antutu_score"] = pd.to_numeric(processed_phone_data["antutu_score"], errors="coerce").astype("Int64")
mean_antutu_scores_by_chipset = processed_phone_data.groupby("chipset")["antutu_score"].transform("mean").round().astype("Int64")
processed_phone_data["antutu_score"] = processed_phone_data["antutu_score"].fillna(mean_antutu_scores_by_chipset).astype("Int64")

def get_processed_phone_data():
    return processed_phone_data