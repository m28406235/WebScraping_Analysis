def parse_specs(specs):
    data = {}
    category = None
    for table in specs.find_all("table"):
        for row in table.find_all("tr"):
            header = row.find("th")
            if header and header.get("rowspan"):
                category = header.text.strip()
                data[category] = {}
            title = row.find("td", class_="ttl")
            value = row.find("td", class_="nfo")
            if value and category:
                val = " ".join(value.text.strip().split())
                key = value.get("data-spec") or (title.text.strip() if title else None)
                if key:
                    target = data[category]
                    if key in target:
                        target[key] = [target[key], val] if isinstance(target[key], str) else target[key] + [val]
                    else:
                        target[key] = val
    return data