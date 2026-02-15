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
        fields = [field_name_lookup[x.strip()] for x in header.split(",")]
        field_indices = {
            field: idx for idx, field in enumerate(fields)
        }

        fields_to_parse = fields  # Just copy all fields.
        cow_dict = {}

        for row in f:
            row_values = [x.strip() for x in row.split(",")]
            if row_values[0] == "":
                continue

            eartag = row_values[field_indices["eartag"]]
            raw_lactation_data = {
                field: row_values[field_indices[field]]
                for field in fields_to_parse
            }
            lactation_data = _convert_raw_data(raw_lactation_data)
            cow_dict[eartag] = {"lactation_data": lactation_data}

    return cow_dict


field_name_lookup = {
    "Line No.": "line_number",
    "Eartag": "eartag",
    "Breed": "breed",
    "305 day Fat + Protein kg": "milk_solids",
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
        "milk_solids", "fat", "protein", "milk", "ave_SCC", "SCC_over_limit",
        "lact_len", "lact_num", "tests", "calving_interval", "CPI", "line_number"
    )
    for field in integer_fields:
        if field in raw_data:
            raw_data[field] = int(raw_data[field])

    decimal_fields = ("F+P_kg_per_day",)
    for field in decimal_fields:
        if field in raw_data:
            raw_data[field] = Decimal(raw_data[field])

    date_fields = ("birth_date", "calving_date")
    for field in date_fields:
        if field in raw_data:
            raw_data[field] = datetime.datetime.strptime(raw_data[field], "%d/%m/%y")

    return raw_data


def _calculate_statistics(cow_dict: dict) -> dict:
    weight_score_sortlist = []
    score_sortlist = []
    milk_solids_sortlist = []
    scc_sortlist = []

    for eartag, data in cow_dict.items():
        lactation_data = data["lactation_data"]

        fat_percentage = 100 * Decimal(lactation_data["fat"]) / Decimal(lactation_data["milk"])
        protein_percentage = 100 * Decimal(lactation_data["protein"]) / Decimal(lactation_data["milk"])
        milk_solid_percentage = 100 * Decimal(lactation_data["fat"]) / Decimal(lactation_data["milk"])

        weight_score, merit_score = _calculate_merit_score(lactation_data=lactation_data)

        cow_dict[eartag]["statistics"] = {
            "fat_percentage": fat_percentage,
            "protein_percentage": protein_percentage,
            "milk_solid_percentage": milk_solid_percentage,
            "weight_score": weight_score,
            "merit_score": merit_score,
        }

        milk_solids_sortlist.append((lactation_data["milk_solids"], eartag))
        scc_sortlist.append((lactation_data["ave_SCC"], eartag))
        weight_score_sortlist.append((weight_score, eartag))
        score_sortlist.append((merit_score, eartag))

    sorted_scores_eartags = sorted(score_sortlist, key=lambda x: x[0], reverse=True)
    for rank, (score, eartag) in enumerate(sorted_scores_eartags):
        cow_dict[eartag]["statistics"]["merit_score_rank"] = rank

    sorted_weight_scores_eartags = sorted(weight_score_sortlist, key=lambda x: x[0], reverse=True)
    for rank, (weight_score, eartag) in enumerate(sorted_weight_scores_eartags):
        cow_dict[eartag]["statistics"]["weight_score_rank"] = rank

    sorted_milk_solids_eartags = sorted(milk_solids_sortlist, key=lambda x: x[0], reverse=True)
    for rank, (milk_solids, eartag) in enumerate(sorted_milk_solids_eartags):
        cow_dict[eartag]["statistics"]["milk_solids_rank"] = rank

    sorted_scc_eartags = sorted(scc_sortlist, key=lambda x: x[0])
    for rank, (scc, eartag) in enumerate(sorted_scc_eartags):
        cow_dict[eartag]["statistics"]["SCC_rank"] = rank

    return cow_dict


def _calculate_merit_score(lactation_data: dict) -> tuple[Decimal, Decimal]:
    cow_weight = lactation_data.get("weight", 500)
    milk = lactation_data["milk"]
    fat = lactation_data["fat"]
    protein = lactation_data["protein"]

    milk_solids = lactation_data["milk_solids"]
    scc = lactation_data["ave_SCC"]

    weight_score = Decimal(milk_solids) / Decimal(cow_weight)
    score = Decimal("1.33") * fat + Decimal("3.13") * protein - Decimal("0.072") * milk - Decimal("0.4") * scc
    merit_score = score * weight_score

    merit_score = max(merit_score, 0)

    return weight_score, merit_score


if __name__ == "__main__":
    demo_file_name = "LatestLactation_2025_25_01_26.csv"
    calculate_lactation_results(lactation_file_path=demo_file_name)
