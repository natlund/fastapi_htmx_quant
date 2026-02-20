import dataclasses
import datetime
from decimal import Decimal
from pathlib import Path

import seaborn as sns


def calculate_lactation_results(lactation_file_path: str, output_file_path: str) -> dict:
    cow_dict, cow_list, header_fields = _parse_lactation_csv_file(lactation_file_path=lactation_file_path)

    augmented_cow_dict = _calculate_statistics(cow_dict=cow_dict)

    _write_output_file(
        output_file_path=output_file_path, cow_dict=augmented_cow_dict, cow_list=cow_list, header_fields=header_fields
    )

    summary_stats = calculate_summary_statistics(cow_dict=augmented_cow_dict)
    # import pprint
    # pprint.pprint(summary_stats)

    create_graphs(cow_dict=augmented_cow_dict)

    return summary_stats


def _parse_lactation_csv_file(lactation_file_path: str) -> dict:
    with open(lactation_file_path) as f:
        header = f.readline()
        fields = [field_name_lookup[x.strip()] for x in header.split(",")]
        field_indices = {
            field: idx for idx, field in enumerate(fields)
        }

        fields_to_parse = fields  # Just copy all fields.
        cow_dict = {}
        cow_list = []

        for row in f:
            row_values = [x.strip() for x in row.split(",")]
            if row_values[0] == "":
                continue

            eartag = row_values[field_indices["eartag"]]
            cow_list.append(eartag)  # Keep track of the original ordering of cows in the CSV file.
            raw_lactation_data = {
                field: row_values[field_indices[field]]
                for field in fields_to_parse
            }
            lactation_data = _convert_raw_data(raw_lactation_data)
            cow_dict[eartag] = {"lactation_data": lactation_data}

    return cow_dict, cow_list, fields


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
    protein_percentage_rank_sortlist = []
    scc_sortlist = []

    for eartag, data in cow_dict.items():
        lactation_data = data["lactation_data"]

        fat_percentage = 100 * Decimal(lactation_data["fat"]) / Decimal(lactation_data["milk"])
        protein_percentage = 100 * Decimal(lactation_data["protein"]) / Decimal(lactation_data["milk"])
        milk_solids_percentage = 100 * Decimal(lactation_data["milk_solids"]) / Decimal(lactation_data["milk"])

        weight_score, merit_score = _calculate_merit_score(lactation_data=lactation_data)

        group = _calculate_group(lactation_data=lactation_data)

        cow_dict[eartag]["statistics"] = {
            "group": group,
            "fat_percentage": round(fat_percentage, 2),
            "protein_percentage": round(protein_percentage, 2),
            "milk_solids_percentage": round(milk_solids_percentage, 2),
            "weight_score": round(weight_score, 4),
            "merit_score": round(merit_score),
        }

        milk_solids_sortlist.append((lactation_data["milk_solids"], eartag))
        scc_sortlist.append((lactation_data["ave_SCC"], eartag))
        protein_percentage_rank_sortlist.append((protein_percentage, eartag))
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

    sorted_protein_percentage_eartags = sorted(protein_percentage_rank_sortlist, key=lambda x: x[0], reverse=True)
    for rank, (protein_percentage, eartag) in enumerate(sorted_protein_percentage_eartags):
        cow_dict[eartag]["statistics"]["protein_percentage_rank"] = rank

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


def _calculate_group(lactation_data: dict) -> str:
    days_in_milk = lactation_data["lact_len"]
    lactations = lactation_data["lact_num"]

    if 220 <= days_in_milk <= 305:
        if 1 <= lactations <= 2:
            return "2"
        if 3 <= lactations <= 8:
            return "1"

    return "3"


def _write_output_file(output_file_path: str, cow_dict: dict, cow_list: list, header_fields: list) -> None:
    reverse_field_lookup = {
        val: key for key, val in field_name_lookup.items()
    }
    reverse_statistics_field_lookup = {
        "fat_percentage": "Fat %",
        "protein_percentage": "Protein %",
        "protein_percentage_rank": "Protein % Rank",
        "milk_solids_percentage": "Milk Solids %",
        "milk_solids_rank": "Milk Solids Rank",
        "SCC_rank": "SCC Rank",
        "weight_score": "Weight Score",
        "weight_score_rank": "Weight Score Rank",
        "merit_score": "Score",
        "merit_score_rank": "Score Rank",
        "group": "Group",
    }
    reverse_field_lookup.update(reverse_statistics_field_lookup)

    augmented_header_fields = [
        "SCC_rank", "milk_solids_rank", "milk_solids_percentage",
        "fat_percentage", "protein_percentage", "protein_percentage_rank",
        "group", "weight_score", "weight_score_rank", "merit_score", "merit_score_rank"
    ]
    all_fields = header_fields + augmented_header_fields

    header = ",".join(reverse_field_lookup[x] for x in all_fields) + "\n"

    with open(output_file_path, "w") as g:
        g.write(header)

        for cow_eartag in cow_list:
            data = cow_dict[cow_eartag]
            lactation_data = data["lactation_data"]
            existing_row = [str(lactation_data[x]) for x in header_fields]
            statistics = data["statistics"]
            stats_row = [str(statistics[x]) for x in augmented_header_fields]
            row = existing_row + stats_row
            line = ",".join(row) + "\n"
            g.write(line)


########################################################################################################################
# Summary Statistics

def calculate_summary_statistics(cow_dict: dict) -> dict:
    number_of_cows = len(cow_dict)
    summary_statistics = {
        "number_of_cows": number_of_cows,
    }

    cows = []
    for eartag, data in cow_dict.items():
        if data["lactation_data"]["lact_num"] in (1, 2):
            cows.append(data)
    summary_statistics["one_and_two"] = calculate_group_data(cow_list=cows, herd_size=number_of_cows)

    cows = []
    for eartag, data in cow_dict.items():
        lactations = data["lactation_data"]["lact_num"]
        if 3 <= lactations <= 8:
            cows.append(data)
    summary_statistics["three_to_eight"] = calculate_group_data(cow_list=cows, herd_size=number_of_cows)

    cows = []
    for eartag, data in cow_dict.items():
        lactations = data["lactation_data"]["lact_num"]
        if 9 <= lactations:
            cows.append(data)
    summary_statistics["nine_plus"] = calculate_group_data(cow_list=cows, herd_size=number_of_cows)

    cows = []
    for eartag, data in cow_dict.items():
        cows.append(data)
    summary_statistics["total"] = calculate_group_data(cow_list=cows, herd_size=number_of_cows)

    cows = []
    for eartag, data in cow_dict.items():
        lactations = data["lactation_data"]["lact_num"]
        if lactations == 1:
            cows.append(data)
    summary_statistics["one"] = calculate_group_data(cow_list=cows, herd_size=number_of_cows)

    cows = []
    for eartag, data in cow_dict.items():
        lactations = data["lactation_data"]["lact_num"]
        if lactations == 2:
            cows.append(data)
    summary_statistics["two"] = calculate_group_data(cow_list=cows, herd_size=number_of_cows)

    return summary_statistics


def calculate_group_data(cow_list: list, herd_size: int) -> dict:
    # Lactation, No of Cows, % of Herd,
    # Vol of Milk kg, Avg Vol of Milk,
    # Milk Solids kg, Ave Milk Solids,
    # Days in Milk, Ave Weight, Avg Fat %, Avg Protein %

    num_cows = 0
    milk_vol = 0
    milk_solids = 0
    days_in_milk = 0
    weight = 0
    fat_pct = 0
    protein_pct = 0

    for cow in cow_list:
        lactation_data = cow["lactation_data"]
        statistics = cow["statistics"]
        num_cows += 1
        milk_vol += lactation_data["milk"]
        milk_solids += lactation_data["milk_solids"]
        days_in_milk += lactation_data["lact_len"]
        weight += lactation_data.get("weight", 500)
        fat_pct += statistics["fat_percentage"]
        protein_pct += statistics["protein_percentage"]

    return {
        "num_cows": num_cows,
        "pct_of_herd": round(100 * Decimal(num_cows) / herd_size),
        "milk_volume": milk_vol,
        "avg_milk_volume": round(Decimal(milk_vol) / num_cows),
        "milk_solids": milk_solids,
        "avg_milk_solids": round(Decimal(milk_solids) / num_cows),
        "days_in_milk": round(Decimal(days_in_milk) / num_cows),
        "avg_weight": round(Decimal(weight) / num_cows),
        "avg_fat_pct": round(Decimal(fat_pct) / num_cows, 2),
        "avg_protein_pct": round(Decimal(protein_pct) / num_cows, 2),
    }


@dataclasses.dataclass(frozen=True)
class FilePaths:
    src_dir = Path(__file__).parent.parent.parent
    temp_dir = src_dir.joinpath("temp", "cowpoke", "herd_improvement")

    output_csv = temp_dir.joinpath("lactation_calculations.csv")

    protein_pct_histogram = temp_dir.joinpath("protein_pct_histogram.svg")
    milk_solids_histogram = temp_dir.joinpath("milk_solids_histogram.svg")
    scc_histogram = temp_dir.joinpath("scc_histogram.svg")
    merit_score_histogram = temp_dir.joinpath("merit_score_histogram.svg")
    cow_age_chart = temp_dir.joinpath("cow_age_chart.svg")


def create_graphs(cow_dict: dict) -> dict:
    protein_percentage = []
    ave_scc = []
    milk_solids = []
    merit_score = []
    age = []

    for cow, data in cow_dict.items():
        stats = data["statistics"]
        lactation_data = data["lactation_data"]
        protein_percentage.append(stats["protein_percentage"])
        ave_scc.append(lactation_data["ave_SCC"])
        milk_solids.append(lactation_data["milk_solids"])
        merit_score.append(stats["merit_score"])
        age.append(lactation_data["lact_num"])

    sns.set_theme(style="darkgrid")

    g = sns.displot(data={"Protein %": protein_percentage}, x="Protein %", binwidth=0.1, binrange=[3,5.5], kde=True)
    g.savefig(FilePaths.protein_pct_histogram)

    g = sns.displot(data={"Milk Solids kg": milk_solids}, x="Milk Solids kg", binwidth=20, binrange=[300,900], kde=True)
    g.savefig(FilePaths.milk_solids_histogram)

    g = sns.displot(data={"Average SCC": ave_scc}, x="Average SCC", binwidth=50, stat="percent")
    g.savefig(FilePaths.scc_histogram)

    g = sns.displot(data={"Score": merit_score}, x="Score", binwidth=50, binrange=[0,1800], stat="percent", kde=True)
    g.savefig(FilePaths.merit_score_histogram)

    g = sns.catplot(data={"Age": age}, x="Age", kind="count", stat="percent")
    g.savefig(FilePaths.cow_age_chart)


if __name__ == "__main__":
    demo_file_name = "LatestLactation_2025_25_01_26.csv"
    output_file_path = "../../temp/cowpoke/herd_improvement/lactation_calculations.csv"
    calculate_lactation_results(lactation_file_path=demo_file_name, output_file_path=output_file_path)
