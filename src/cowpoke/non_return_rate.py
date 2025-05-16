import datetime
from decimal import Decimal


def calculate_non_return_rate(input_file_path, output_file_path) -> dict:

    inseminations = _parse_csv_file(file_path=input_file_path)

    bull_statistics = calculate_bull_statistics(inseminations)

    inseminations.sort(key = lambda x: x[1])  # Sort by date.

    insem_dict = dict()

    for cow, insem_date, bull in inseminations:
        if cow not in insem_dict:
            insem_dict[cow] = [(insem_date, bull)]
        else:
            insem_dict[cow].append((insem_date, bull))

    extended_insem_dict = dict()
    first_insems = 0
    short_returns = 0
    normal_returns = 0
    long_returns = 0

    for cow, insems in insem_dict.items():
        first_insem = insems[0]
        first_insems += 1
        extended_insem_dict[cow] = [first_insem + ("", "")]

        remaining_insems = insems[1:]
        previous_insem = first_insem
        for ins in remaining_insems:
            days_elapsed = (ins[0] - previous_insem[0]).days
            return_status = calculate_return_status(days_elapsed=days_elapsed)
            previous_insem = ins

            if return_status == "Short Return":
                short_returns += 1
            elif return_status == "Normal Return":
                normal_returns += 1
            elif return_status == "Long Return":
                long_returns += 1

            extended_insem_dict[cow].append(ins + (return_status, days_elapsed))

    generate_augmented_insemination_file(  # Writes augmented insemination file to disk at "temp/cowpoke".
        extended_insem_dict=extended_insem_dict,
        output_file_path=output_file_path,
    )

    total_cows_submitted = len(insem_dict)

    non_returned_cows = 0
    for cow, insems in insem_dict.items():
        if len(insems) == 1:
            non_returned_cows += 1

    first_date = inseminations[0][1]
    last_date = inseminations[-1][1]

    total_inseminations = len(inseminations)
    eligible_matings = first_insems + normal_returns
    non_return_rate = 100 * Decimal(first_insems)/Decimal(eligible_matings)

    non_returned_cow_rate = 100 * Decimal(non_returned_cows)/Decimal(total_cows_submitted)

    total_returns = short_returns + normal_returns + long_returns
    total_return_rate = 100 * Decimal(total_returns)/Decimal(total_inseminations)
    first_mating_rate = 100 * Decimal(first_insems)/Decimal(total_inseminations)

    short_returns_pct_tot = 100 * Decimal(short_returns)/Decimal(total_inseminations)
    short_returns_pct_ret = 100 * Decimal(short_returns)/Decimal(total_returns)
    normal_returns_pct_tot = 100 * Decimal(normal_returns)/Decimal(total_inseminations)
    normal_returns_pct_ret = 100 * Decimal(normal_returns)/Decimal(total_returns)
    long_returns_pct_tot = 100 * Decimal(long_returns)/Decimal(total_inseminations)
    long_returns_pct_ret = 100 * Decimal(long_returns)/Decimal(total_returns)

    return {
        "first_insemination_date": first_date.strftime("%d-%b-%y"),
        "last_insemination_date": last_date.strftime("%d-%b-%y"),
        "bull_statistics": bull_statistics,
        "total_cows_submitted": total_cows_submitted,
        "total_inseminations": total_inseminations,
        "first_insems": first_insems,
        "eligible_returns": normal_returns,
        "eligible_matings": eligible_matings,
        "non_return_rate": f"{non_return_rate:.1f}",
        "non_returned_cows": non_returned_cows,
        "non_returned_cow_rate": f"{non_returned_cow_rate:.1f}",
        "total_returns": total_returns,
        "total_return_rate": f"{total_return_rate:.1f}",
        "first_mating_rate": f"{first_mating_rate:.1f}",
        "short_returns": short_returns,
        "short_returns_pct_total": f"{short_returns_pct_tot:.1f}",
        "short_returns_pct_returns": f"{short_returns_pct_ret:.1f}",
        "normal_returns": normal_returns,
        "normal_returns_pct_total": f"{normal_returns_pct_tot:.1f}",
        "normal_returns_pct_returns": f"{normal_returns_pct_ret:.1f}",
        "long_returns": long_returns,
        "long_returns_pct_total": f"{long_returns_pct_tot:.1f}",
        "long_returns_pct_returns": f"{long_returns_pct_ret:.1f}",
    }


def calculate_return_status(days_elapsed: int) -> str:
    if days_elapsed < 18:
        return "Short Return"
    elif 18 <= days_elapsed <= 24:
        return "Normal Return"
    else:
        return "Long Return"


def calculate_bull_statistics(inseminations: list) -> list:
    bull_dict = dict()

    for cow, insem_date, bull in inseminations:
        if bull in bull_dict:
            bull_dict[bull] += 1
        else:
            bull_dict[bull] = 1

    total_inseminations = len(inseminations)
    bull_list = []
    for bull, count in bull_dict.items():
        pct = 100 * Decimal(count)/Decimal(total_inseminations)
        bull_list.append({
            "bull_name": bull,
            "count": count,
            "pct": f"{pct:.1f}"
        })
    bull_list.sort(key=lambda x: x["count"], reverse=True)

    return bull_list


def generate_augmented_insemination_file(extended_insem_dict: dict, output_file_path: str):
    inseminations_per_cow = []
    for cow, insems in extended_insem_dict.items():
        inseminations_per_cow.append((int(cow), len(insems)))

    inseminations_per_cow.sort(key=lambda x: x[0])  # Sort by Cow ID.
    inseminations_per_cow.sort(key=lambda x: x[1], reverse=True)  # Sort by Num Inseminations.
    # Since sorts are *stable*, records with same Num Inseminations keep their original order (which was sorted).

    with open(output_file_path, "w") as g:
        header_tuple = ("Cow", "Mating Date", "Bull", "Return Type", "Days")
        header = ",".join(header_tuple) + "\n"
        g.write(header)

        for cow_id, num_insems in inseminations_per_cow:
            cow = str(cow_id)
            cow_insems = extended_insem_dict[cow]
            for mating_date, bull, rtn, days in cow_insems:
                date_string = mating_date.strftime("%d-%b-%y")
                return_type = rtn.split(" ")[0].strip()  # Convert eg. "Short Return" to just "Short".
                line = f"{cow}, {date_string}, {bull}, {return_type}, {days}" + "\n"
                g.write(line)


def _parse_csv_file(file_path) -> list:
    inseminations = []

    with open(file_path) as f:
        header = f.readline()
        fields = header.strip().split(",")
        lower_case_fields = [x.lower() for x in fields]

        for idx, field in enumerate(lower_case_fields):
            if "cow" in field:
                cow_idx = idx
            if "date" in field:
                date_idx = idx
            if "bull" in field:
                bull_idx = idx

        # File pointer is now at second line, where data starts.
        for line in f:
            parts = line.strip().split(",")

            cow = parts[cow_idx].strip()
            bull = parts[bull_idx].strip()
            date_string = parts[date_idx].strip()
            insem_date = datetime.datetime.strptime(date_string, "%d-%b-%y").date()

            inseminations.append((cow, insem_date, bull))

    return inseminations


if __name__ == "__main__":
    result = calculate_non_return_rate("../temp/cowpoke/nrr_data.csv")
    for k, v in result.items():
        print(k, v)
