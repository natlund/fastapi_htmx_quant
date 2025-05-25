import datetime
from decimal import Decimal


def calculate_non_return_rate_results(input_file_path: str, output_file_path: str) -> dict:
    inseminations = _parse_csv_file(file_path=input_file_path)

    bull_statistics = calculate_bull_statistics(inseminations)

    inseminations.sort(key = lambda x: x[1])  # Sort by date.

    cow_insems_dict = dict()

    for cow, insem_date, bull in inseminations:
        if cow not in cow_insems_dict:
            cow_insems_dict[cow] = [(insem_date, bull)]
        else:
            cow_insems_dict[cow].append((insem_date, bull))

    #################################################################################
    # Create Cow dictionary with extra derived info.
    cow_dict = dict()

    for cow, insems in cow_insems_dict.items():
        first_insem = insems[0]
        remaining_insems = insems[1:]  # (May be empty.)
        first_insemination_date = first_insem[0]
        new_insems = [first_insem + ("First Insemination", "")]

        previous_insem = first_insem
        for insem in remaining_insems:
            days_elapsed = (insem[0] - previous_insem[0]).days
            return_status = calculate_return_status(days_elapsed=days_elapsed)
            new_insems.append(insem + (return_status, days_elapsed))

        return_statuses = [x[2] for x in new_insems]
        has_one_day_return = True if "One Day Return" in return_statuses else False
        has_short_return = True if "Short Return" in return_statuses else False
        has_long_return = True if "Long Return" in return_statuses else False
        no_returns = True if len(new_insems) == 1 else False

        cow_dict[cow] = {
            "inseminations": new_insems,
            "first_insemination_date": first_insemination_date,
            "no_returns": no_returns,
            "has_one_day_return": has_one_day_return,
            "has_short_return": has_short_return,
            "has_long_return": has_long_return,
        }

    ###########################################################################################
    # Generate Non Return Rates.
    first_date = inseminations[0][1]
    last_date = inseminations[-1][1]

    full_season_unconfirmed_nrr = calculate_non_return_rate(
        cow_dict=cow_dict, start_date=first_date, cut_off_date=last_date
    )
    last_date_minus_24 = last_date - datetime.timedelta(days=24)
    full_season_confirmed_nrr = calculate_non_return_rate(
        cow_dict=cow_dict, start_date=first_date, cut_off_date=last_date_minus_24
    )
    end_of_six_weeks = first_date + datetime.timedelta(weeks=6)
    end_of_period = min(end_of_six_weeks, last_date)  # In case a real season is *less* than six weeks.
    end_of_period_minus_24 = end_of_period - datetime.timedelta(days=24)
    six_weeks_confirmed_nrr = calculate_non_return_rate(
        cow_dict=cow_dict, start_date=first_date, cut_off_date=end_of_period_minus_24
    )
    #######################################################################################
    # Generate other statistics.

    total_cows_submitted = len(cow_dict)
    total_inseminations = len(inseminations)

    return_status_statistics = calculate_return_status_statistics(cow_dict)

    cumulative_insemination_statistics = calculate_cumulative_insemination_statistics(cow_dict=cow_dict)

    ############################################################################################

    generate_augmented_insemination_file(  # Writes augmented insemination file to disk at "temp/cowpoke".
        cow_dict=cow_dict,
        output_file_path=output_file_path,
    )

    return {
        "first_insemination_date": first_date.strftime("%d-%b-%y"),
        "last_insemination_date": last_date.strftime("%d-%b-%y"),
        "bull_statistics": bull_statistics,
        "total_cows_submitted": total_cows_submitted,
        "total_inseminations": total_inseminations,
        "cum_insem_stats": cumulative_insemination_statistics,
        "nrr": {
            "full_season_unconfirmed": full_season_unconfirmed_nrr,
            "full_season_confirmed": full_season_confirmed_nrr,
            "six_weeks_confirmed": six_weeks_confirmed_nrr,
        },
        "rss": return_status_statistics,
    }


def calculate_non_return_rate(cow_dict: dict, start_date: datetime.date, cut_off_date: datetime.date) -> dict:

        total_cows = 0
        excluded_from_analysis = 0
        eligible_cows = 0
        non_return_cows = 0
        one_day_return_cows = 0
        returned_cows = 0

        for cow, data in cow_dict.items():
            if cut_off_date < data["first_insemination_date"]:
                continue

            total_cows += 1
            if data["has_short_return"] or data["has_long_return"]:
                excluded_from_analysis += 1
                continue
            else:
                eligible_cows += 1
                if data["no_returns"]:
                    non_return_cows += 1
                elif data["has_one_day_return"]:
                    one_day_return_cows += 1
                else:
                    returned_cows += 1

        non_return_rate = 100 * Decimal(non_return_cows + one_day_return_cows)/Decimal(eligible_cows)

        return {
            "start_date": start_date.strftime("%d-%b-%y"),
            "cutoff_date": cut_off_date.strftime("%d-%b-%y"),
            "total_cows": total_cows,
            "excluded_from_analysis": excluded_from_analysis,
            "eligible_cows": eligible_cows,
            "non_return_cows": non_return_cows,
            "one_day_return_cows": one_day_return_cows,
            "returned_cows": returned_cows,
            "non_return_rate": f"{non_return_rate:.1f}",
        }


def calculate_return_status_statistics(cow_dict: dict) -> dict:
    total_inseminations = 0
    first_inseminations = 0
    one_day_returns = 0
    short_returns = 0
    normal_returns = 0
    long_returns = 0

    for cow, data in cow_dict.items():
        for insem in data["inseminations"]:
            total_inseminations += 1
            return_type = insem[2]
            if return_type == "First Insemination":
                first_inseminations += 1
            elif return_type == "One Day Return":
                one_day_returns += 1
            elif return_type == "Short Return":
                short_returns += 1
            elif return_type == "Normal Return":
                normal_returns += 1
            elif return_type == "Long Return":
                long_returns += 1

    total_returns = one_day_returns + short_returns + normal_returns + long_returns

    first_insemination_rate = 100 * Decimal(first_inseminations)/Decimal(total_inseminations)
    total_return_rate = 100 * Decimal(total_returns)/Decimal(total_inseminations)

    one_day_returns_pct_tot = 100 * Decimal(one_day_returns)/Decimal(total_inseminations)
    one_day_returns_pct_ret = 100 * Decimal(one_day_returns)/Decimal(total_returns)
    short_returns_pct_tot = 100 * Decimal(short_returns)/Decimal(total_inseminations)
    short_returns_pct_ret = 100 * Decimal(short_returns)/Decimal(total_returns)
    normal_returns_pct_tot = 100 * Decimal(normal_returns)/Decimal(total_inseminations)
    normal_returns_pct_ret = 100 * Decimal(normal_returns)/Decimal(total_returns)
    long_returns_pct_tot = 100 * Decimal(long_returns)/Decimal(total_inseminations)
    long_returns_pct_ret = 100 * Decimal(long_returns)/Decimal(total_returns)


    return_days_histogram = dict()
    for cow, data in cow_dict.items():
        for insem in data["inseminations"]:
            days_elapsed_str = insem[3]
            try:
                days_elapsed = int(days_elapsed_str)
            except ValueError:
                continue
            if days_elapsed not in return_days_histogram:
                return_days_histogram[days_elapsed] = 1
            else:
                return_days_histogram[days_elapsed] += 1

    return_days_histogram_list = [(days, count) for days, count in return_days_histogram.items()]
    return_days_histogram_list.sort(key=lambda x: x[0])

    return {
        "total_inseminations": total_inseminations,
        "first_inseminations": first_inseminations,
        "first_insemination_rate": f"{first_insemination_rate:.1f}",
        "total_returns": total_returns,
        "total_return_rate": f"{total_return_rate:.1f}",
        "one_day_returns": one_day_returns,
        "one_day_returns_pct_total": f"{one_day_returns_pct_tot:.1f}",
        "one_day_returns_pct_returns": f"{one_day_returns_pct_ret:.1f}",
        "short_returns": short_returns,
        "short_returns_pct_total": f"{short_returns_pct_tot:.1f}",
        "short_returns_pct_returns": f"{short_returns_pct_ret:.1f}",
        "normal_returns": normal_returns,
        "normal_returns_pct_total": f"{normal_returns_pct_tot:.1f}",
        "normal_returns_pct_returns": f"{normal_returns_pct_ret:.1f}",
        "long_returns": long_returns,
        "long_returns_pct_total": f"{long_returns_pct_tot:.1f}",
        "long_returns_pct_returns": f"{long_returns_pct_ret:.1f}",
        "return_days_histogram": return_days_histogram_list,
    }


def calculate_cumulative_insemination_statistics(cow_dict: dict) -> dict:
    total_cows_submitted = len(cow_dict)

    first_submissions = [(cow, data["first_insemination_date"]) for cow, data in cow_dict.items()]
    first_submissions.sort(key=lambda x: x[1])  # Sort by date.

    start_date = first_submissions[0][1]
    week_1 = start_date + datetime.timedelta(weeks=1)
    week_2 = start_date + datetime.timedelta(weeks=2)
    week_3 = start_date + datetime.timedelta(weeks=3)

    week_1_count = 0
    week_2_count = 0
    week_3_count = 0
    for cow, insem_date in first_submissions:
        if insem_date < week_1:
            week_1_count += 1
        if insem_date < week_2:
            week_2_count += 1
        if insem_date < week_3:
            week_3_count += 1

    week_1_cum_pct = 100 * Decimal(week_1_count)/Decimal(total_cows_submitted)
    week_2_cum_pct = 100 * Decimal(week_2_count)/Decimal(total_cows_submitted)
    week_3_cum_pct = 100 * Decimal(week_3_count)/Decimal(total_cows_submitted)

    return {
        "week_1_count": week_1_count,
        "week_1_cum_pct": f"{week_1_cum_pct:.1f}",
        "week_2_count": week_2_count,
        "week_2_cum_pct": f"{week_2_cum_pct:.1f}",
        "week_3_count": week_3_count,
        "week_3_cum_pct": f"{week_3_cum_pct:.1f}",
    }


def calculate_return_status(days_elapsed: int) -> str:
    if days_elapsed == 1:
        return "One Day Return"
    elif 1 < days_elapsed < 18:
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


def generate_augmented_insemination_file(cow_dict: dict, output_file_path: str):
    inseminations_per_cow = []
    for cow, data in cow_dict.items():
        inseminations_per_cow.append((int(cow), len(data["inseminations"])))

    inseminations_per_cow.sort(key=lambda x: x[0])  # Sort by Cow ID.
    inseminations_per_cow.sort(key=lambda x: x[1], reverse=True)  # Sort by Num Inseminations.
    # Since sorts are *stable*, records with same Num Inseminations keep their original order (which was sorted).

    with open(output_file_path, "w") as g:
        return_type_map = {
            "First Insemination": "",
            "One Day Return": "Short",
            "Short Return": "Short",
            "Normal Return": "Normal",
            "Long Return": "Long",
        }
        header_tuple = ("Cow", "Mating Date", "Bull", "Return Type", "Days")
        header = ",".join(header_tuple) + "\n"
        g.write(header)

        for cow_id, num_insems in inseminations_per_cow:
            cow = str(cow_id)
            cow_insems = cow_dict[cow]["inseminations"]
            for mating_date, bull, rtn, days in cow_insems:
                date_string = mating_date.strftime("%d-%b-%y")
                return_type = return_type_map[rtn.strip()]
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
