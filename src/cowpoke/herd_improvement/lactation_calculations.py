import datetime
from decimal import Decimal


def calculate_lactation_results(lactation_file_path: str) -> dict:
    cow_dict = _parse_lactation_csv_file(lactation_file_path=lactation_file_path)

    augmented_cow_dict = _calculate_statistics(cow_dict=cow_dict)

    import pprint
    pprint.pprint(augmented_cow_dict)

    return augmented_cow_dict


def _parse_lactation_csv_file(lactation_file_path: str) -> dict:
    with open(lactation_file_path) as f:
        header = f.readline()
        fields = [x.strip() for x in header.split(",")]
        field_indices = {
            field: idx for idx, field in enumerate(fields)
        }
        cow_dict = {}

        for row in f:
            field_values = [x.strip() for x in row.split(",")]
            if field_values[0] == "":
                continue
            eartag = field_values[field_indices["Eartag"]]
            cow_data = {
                field: field_values[field_indices[field]] for field in fields
            }
            converted_cow_data = _convert_raw_data(cow_data)
            relabeled_cow_data = {
                field_name_lookup[field]: val for field, val in converted_cow_data.items()
            }
            cow_dict[eartag] = {"raw_data": relabeled_cow_data}

    return cow_dict


field_name_lookup = {
    "Line No.": "line_number",
    "Eartag": "eartag",
    "Breed": "breed",
    "305 day Fat + Protein kg": "fat_and_protein",
    "305 day Fat kg": "fat",
    "305 day Protein kg": "protein",
    "305 day Milk kg": "milk",
    "F+P kg / day": "F+P_kg_per_day",
    "Ave SCC": "ave_SCC",
    "SCC over limit": "SCC_over_limit",
    "Lact len": "lact_len",
    "Lact num": "lact_num",
    "Tests": "tests",
    "Calv int": "calving_interval",
    "CPI": "CPI",
    "Birth Date": "birth_date",
    "Calving Date": "calving_date",
    "Johne's Group": "johnes_group",
    "Fertility Status": "fertility_status",
    "Sire name": "sire_name",
}


def _convert_raw_data(raw_data: dict) -> dict:
    integer_fields = (
        "305 day Fat + Protein kg", "305 day Fat kg", "305 day Protein kg", "305 day Milk kg",
        "Ave SCC", "SCC over limit", "Lact len", "Lact num", "Tests", "Calv int", "CPI", "Line No.",
    )
    for field in integer_fields:
        raw_data[field] = int(raw_data[field])

    decimal_fields = ("F+P kg / day",)
    for field in decimal_fields:
        raw_data[field] = Decimal(raw_data[field])

    date_fields = ("Birth Date", "Calving Date")
    for field in date_fields:
        raw_data[field] = datetime.datetime.strptime(raw_data[field], "%d/%m/%y")

    return raw_data


def _calculate_statistics(cow_dict: dict) -> dict:
    score_sortlist = []

    for eartag, data in cow_dict.items():
        raw_data = data["raw_data"]
        merit_score = _calculate_merit_score(raw_data=raw_data)

        score_sortlist.append((merit_score, eartag))

    sorted_scores_eartags = sorted(score_sortlist, key=lambda x: x[0], reverse=True)

    for rank, (score, eartag) in enumerate(sorted_scores_eartags):
        statistics = {
            "merit_score": score,
            "merit_score_rank": rank,
        }
        cow_dict[eartag]["statistics"] = statistics

    return cow_dict


def _calculate_merit_score(raw_data: dict) -> Decimal:
    cow_weight = raw_data.get("weight", 500)
    milk = raw_data["milk"]
    fat = raw_data["fat"]
    protein = raw_data["protein"]
    fat_and_protein = raw_data["fat_and_protein"]
    scc = raw_data["ave_SCC"]

    weight_score = Decimal(fat_and_protein) / Decimal(cow_weight)
    score = Decimal("1.33") * fat + Decimal("3.13") * protein - Decimal("0.072") * milk - Decimal("0.4") * scc
    merit_score = score * weight_score

    merit_score = max(merit_score, 0)

    return merit_score
