import datetime
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import Union

from matplotlib import pyplot as plt


class ReturnType(Enum):
    FIRST_INSEMINATION = "First Insemination"
    ONE_DAY = "1-Day Return"
    TWO_17_DAY = "2-17 Day Return"
    NORMAL = "Normal Return"
    LONG = "Long Return"


@dataclass
class Insemination:
    insemination_date: datetime.date
    bull: int
    return_type: ReturnType
    days_elapsed: str


def calculate_non_return_rate_results(
        herd_size_str,
        input_file_path: str,
        output_file_path: str,
        returns_bar_chart_file_path: str,
        cow_submission_graph_file_path: str,
) -> dict:
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
        new_insem = Insemination(
            insemination_date=first_insem[0],
            bull=first_insem[1],
            return_type=ReturnType.FIRST_INSEMINATION,
            days_elapsed="",
        )
        new_insems = [new_insem]

        previous_insem = first_insem
        for insem in remaining_insems:
            days_elapsed = (insem[0] - previous_insem[0]).days
            return_status = calculate_return_status(days_elapsed=days_elapsed)
            new_insem = Insemination(
                insemination_date=insem[0],
                bull=insem[1],
                return_type=return_status,
                days_elapsed=days_elapsed,
            )
            new_insems.append(new_insem)
            previous_insem = insem  # Bugfix!  This line was missing, causing ALL returns to compare to First Insem.

        return_statuses = [x.return_type for x in new_insems]
        has_one_day_return = True if ReturnType.ONE_DAY in return_statuses else False
        has_two_17_day_return = True if ReturnType.TWO_17_DAY in return_statuses else False
        has_long_return = True if ReturnType.LONG in return_statuses else False
        no_returns = True if len(new_insems) == 1 else False

        cow_dict[cow] = {
            "inseminations": new_insems,
            "first_insemination_date": first_insemination_date,
            "no_returns": no_returns,
            "has_one_day_return": has_one_day_return,
            "has_two_17_day_return": has_two_17_day_return,
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

    try:
        herd_size = int(herd_size_str)
    except ValueError:
        herd_size = None

    cumulative_insemination_statistics = calculate_cumulative_insemination_statistics(
        cow_dict=cow_dict, herd_size=herd_size
    )
    create_cow_submission_graph(cow_dict=cow_dict, graph_filename=cow_submission_graph_file_path)

    return_status_statistics = calculate_return_status_statistics(cow_dict=cow_dict)

    return_days_histogram = create_return_days_histogram(  # Writes bar chart file to disk at "temp/cowpoke".
        cow_dict=cow_dict, bar_chart_filename=returns_bar_chart_file_path
    )

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
        "return_days_histogram": return_days_histogram,
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
            if data["has_two_17_day_return"] or data["has_long_return"]:
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
    two_17_day_returns = 0
    normal_returns = 0
    long_returns = 0

    for cow, data in cow_dict.items():
        for insem in data["inseminations"]:
            total_inseminations += 1
            if insem.return_type == ReturnType.FIRST_INSEMINATION:
                first_inseminations += 1
            elif insem.return_type == ReturnType.ONE_DAY:
                one_day_returns += 1
            elif insem.return_type == ReturnType.TWO_17_DAY:
                two_17_day_returns += 1
            elif insem.return_type == ReturnType.NORMAL:
                normal_returns += 1
            elif insem.return_type == ReturnType.LONG:
                long_returns += 1

    total_returns = one_day_returns + two_17_day_returns + normal_returns + long_returns

    first_insemination_rate = 100 * Decimal(first_inseminations)/Decimal(total_inseminations)
    total_return_rate = 100 * Decimal(total_returns)/Decimal(total_inseminations)

    one_day_returns_pct_tot = 100 * Decimal(one_day_returns)/Decimal(total_inseminations)
    one_day_returns_pct_ret = 100 * Decimal(one_day_returns)/Decimal(total_returns)
    two_17_day_returns_pct_tot = 100 * Decimal(two_17_day_returns)/Decimal(total_inseminations)
    two_17_day_returns_pct_ret = 100 * Decimal(two_17_day_returns)/Decimal(total_returns)
    normal_returns_pct_tot = 100 * Decimal(normal_returns)/Decimal(total_inseminations)
    normal_returns_pct_ret = 100 * Decimal(normal_returns)/Decimal(total_returns)
    long_returns_pct_tot = 100 * Decimal(long_returns)/Decimal(total_inseminations)
    long_returns_pct_ret = 100 * Decimal(long_returns)/Decimal(total_returns)

    return {
        "total_inseminations": total_inseminations,
        "first_inseminations": first_inseminations,
        "first_insemination_rate": f"{first_insemination_rate:.1f}",
        "total_returns": total_returns,
        "total_return_rate": f"{total_return_rate:.1f}",
        "one_day_returns": one_day_returns,
        "one_day_returns_pct_total": f"{one_day_returns_pct_tot:.1f}",
        "one_day_returns_pct_returns": f"{one_day_returns_pct_ret:.1f}",
        "two_17_day_returns": two_17_day_returns,
        "two_17_day_returns_pct_total": f"{two_17_day_returns_pct_tot:.1f}",
        "two_17_day_returns_pct_returns": f"{two_17_day_returns_pct_ret:.1f}",
        "normal_returns": normal_returns,
        "normal_returns_pct_total": f"{normal_returns_pct_tot:.1f}",
        "normal_returns_pct_returns": f"{normal_returns_pct_ret:.1f}",
        "long_returns": long_returns,
        "long_returns_pct_total": f"{long_returns_pct_tot:.1f}",
        "long_returns_pct_returns": f"{long_returns_pct_ret:.1f}",
    }


def create_return_days_histogram(cow_dict: dict, bar_chart_filename: str) -> list:

    return_days_histogram = dict()

    for cow, data in cow_dict.items():
        for insem in data["inseminations"]:
            try:
                days_elapsed = int(insem.days_elapsed)
            except ValueError:
                continue
            if days_elapsed not in return_days_histogram:
                return_days_histogram[days_elapsed] = 1
            else:
                return_days_histogram[days_elapsed] += 1

    return_days_histogram_list = [(days, count) for days, count in return_days_histogram.items()]
    return_days_histogram_list.sort(key=lambda x: x[0])

    ########################################################################
    # Create Bar Chart of Counts of Returns by Days Elapsed.

    days = [day for (day, count) in return_days_histogram_list]
    counts = [count for (day, count) in return_days_histogram_list]

    num_bars_short = len([day for (day, count) in return_days_histogram_list if day < 18])
    num_bars_normal = len([day for (day, count) in return_days_histogram_list if 18 <= day <= 24])
    num_bars_long = len([day for (day, count) in return_days_histogram_list if 24 < day])
    colours = (["gold" for x in range(num_bars_short)]
               + ["green" for x in range(num_bars_normal)]
               + ["blue" for x in range(num_bars_long)])

    plt.cla()
    plt.bar(days, counts, color=colours, zorder=2)

    plt.xlabel("Days Since Previous Insemination")
    plt.ylabel("Count")
    plt.title("Counts of Returns by Days")

    max_days = max(return_days_histogram.keys())
    x_labels = range(0, max_days+1, 2)
    plt.xticks(ticks=x_labels, labels=x_labels)

    max_count = max(return_days_histogram.values())
    y_labels = range(0, max_count+1, 2)
    plt.yticks(ticks=y_labels, labels=y_labels)

    plt.grid(visible=True, axis='y', zorder=0)

    plt.savefig(bar_chart_filename)

    return return_days_histogram_list


def calculate_cumulative_insemination_statistics(cow_dict: dict, herd_size: Union[int, None]) -> dict:
    total_cows_submitted = len(cow_dict)

    first_submissions = [(cow, data["first_insemination_date"]) for cow, data in cow_dict.items()]
    first_submissions.sort(key=lambda x: x[1])  # Sort by date.

    start_date = first_submissions[0][1]
    end_week_1 = start_date + datetime.timedelta(weeks=1)
    end_week_2 = start_date + datetime.timedelta(weeks=2)
    end_week_3 = start_date + datetime.timedelta(weeks=3)

    week_1_count = 0
    week_2_count = 0
    week_3_count = 0
    for cow, insem_date in first_submissions:
        if insem_date < end_week_1:
            week_1_count += 1
        if end_week_1 <= insem_date < end_week_2:
            week_2_count += 1
        if end_week_2 <= insem_date < end_week_3:
            week_3_count += 1

    week_1_cum = week_1_count
    week_2_cum = week_1_cum + week_2_count
    week_3_cum = week_2_cum + week_3_count

    week_1_cum_pct = 100 * Decimal(week_1_cum)/Decimal(total_cows_submitted)
    week_2_cum_pct = 100 * Decimal(week_2_cum)/Decimal(total_cows_submitted)
    week_3_cum_pct = 100 * Decimal(week_3_cum)/Decimal(total_cows_submitted)

    submission_rate_dict = {
        "week_1_count": week_1_count,
        "week_1_cum": week_1_cum,
        "week_1_cum_pct": f"{week_1_cum_pct:.1f}%",
        "week_2_count": week_2_count,
        "week_2_cum": week_2_cum,
        "week_2_cum_pct": f"{week_2_cum_pct:.1f}%",
        "week_3_count": week_3_count,
        "week_3_cum": week_3_cum,
        "week_3_cum_pct": f"{week_3_cum_pct:.1f}%",
    }
    if herd_size is not None:
        week_1_pct_herd = 100 * Decimal(week_1_cum) / Decimal(herd_size)
        week_2_pct_herd = 100 * Decimal(week_2_cum) / Decimal(herd_size)
        week_3_pct_herd = 100 * Decimal(week_3_cum) / Decimal(herd_size)

        submission_rate_dict["week_1_pct_herd"] = f"{week_1_pct_herd:.1f}%"
        submission_rate_dict["week_2_pct_herd"] = f"{week_2_pct_herd:.1f}%"
        submission_rate_dict["week_3_pct_herd"] = f"{week_3_pct_herd:.1f}%"

    else:
        submission_rate_dict["week_1_pct_herd"] = "N/A"
        submission_rate_dict["week_2_pct_herd"] = "N/A"
        submission_rate_dict["week_3_pct_herd"] = "N/A"

    return submission_rate_dict


def create_cow_submission_graph(cow_dict: dict, graph_filename: str):
    date_dict = dict()

    for cow, data in cow_dict.items():
        first_insem_date = data["first_insemination_date"]
        if first_insem_date in date_dict:
            date_dict[first_insem_date]["cows"] += 1
        else:
            date_dict[first_insem_date] = {"cows": 1, "inseminations": 0}

        for insem in data["inseminations"]:
            if insem.insemination_date in date_dict:
                date_dict[insem.insemination_date]["inseminations"] += 1
            else:
                date_dict[insem.insemination_date] = {"inseminations": 1, "cows": 0}

    date_list = [(d, counts) for d, counts in date_dict.items()]
    date_list.sort(key=lambda x: x[0])

    start_date = date_list[0][0]

    day_cumulative_counts = []
    cow_cum_count = 0
    insems_cum_count = 0
    for d, counts in date_list:
        day = (d - start_date).days + 1
        cow_cum_count += counts["cows"]
        insems_cum_count += counts["inseminations"]
        day_cumulative_counts.append((day, cow_cum_count, insems_cum_count))

    x_days = [day for day, cum_cows, cum_insems in day_cumulative_counts]
    cows_cumulative = [cum_cows for day, cum_cows, cum_insems in day_cumulative_counts]
    insems_cumulative = [cum_insems for day, cum_cows, cum_insems in day_cumulative_counts]

    plt.cla()
    plt.plot(x_days, insems_cumulative, color="green", label="Inseminations")
    plt.plot(x_days, cows_cumulative, color="blue", label="Cow Submissions")
    plt.legend()

    plt.xlabel("Days into Season")
    plt.ylabel("Cumulative Counts")
    plt.title("Cow Submissions and Inseminations")

    max_days = x_days[-1]
    x_labels = range(0, max_days+1, 2)
    plt.xticks(ticks=x_labels, labels=x_labels)

    max_count = insems_cumulative[-1]
    y_labels = range(0, max_count+50, 100)
    plt.yticks(ticks=y_labels, labels=y_labels)

    plt.vlines([7, 14, 21], ymin=0, ymax=max_count, linestyles="dashed")
    plt.grid(visible=True, axis='y', linestyle="dashed", zorder=0)

    plt.savefig(graph_filename)


def calculate_return_status(days_elapsed: int) -> ReturnType:
    if days_elapsed < 1:
        return ReturnType.FIRST_INSEMINATION
    elif days_elapsed == 1:
        return ReturnType.ONE_DAY
    elif 1 < days_elapsed < 18:
        return ReturnType.TWO_17_DAY
    elif 18 <= days_elapsed <= 24:
        return ReturnType.NORMAL
    else:
        return ReturnType.LONG


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


def cow_id_sort_key(s):
    """
    Allows 'natural' sorting of Cow IDs where some IDs have a non-numeric prefix.
    Cow IDs are usually purely numeric (integers) eg. 1234, 78, 456.
    But some Cow IDs have a non-numeric prefix eg. A123, F567.
    For completeness, we'll also allow Cow IDs to be purely non-numeric eg. ABC, PQR.

    We want all numeric IDs to be sorted numerically, NOT lexically (alphabetically).
    And we want non-numeric-prefixed IDs to be sorted lexically by the prefix,
    then numerically by the numerical part.
    
    List [123, A12, A111, 45, xyz] should sort to
         [45, 123, A12, A111, xyz], whereas lexical sorting gives the unnatural
         [123, 45, A111, A12, xyz]
    """
    if s[0].isdigit():
        key = (["0", int(s)], s)
        return key

    prefix = ""
    numeric = 0  # In case no characters are digits.

    for k, char in enumerate(s):
        if char.isdigit():
            numeric = s[k:]
            break
        else:
            prefix += char

    key = ([prefix, int(numeric)], s)
    return key


def generate_augmented_insemination_file(cow_dict: dict, output_file_path: str):
    inseminations_per_cow = []
    for cow, data in cow_dict.items():
        inseminations_per_cow.append((cow, len(data["inseminations"])))

    inseminations_per_cow.sort(key=lambda x: cow_id_sort_key(x[0]))  # Sort by Cow ID.
    inseminations_per_cow.sort(key=lambda x: x[1], reverse=True)  # Sort by Num Inseminations.
    # Since sorts are *stable*, records with same Num Inseminations keep their original order (which was sorted).

    return_type_map = {
        ReturnType.FIRST_INSEMINATION: "",
        ReturnType.ONE_DAY: "Short",
        ReturnType.TWO_17_DAY: "Short",
        ReturnType.NORMAL: "Normal",
        ReturnType.LONG: "Long",
    }
    with open(output_file_path, "w") as g:
        header_tuple = ("Cow", "Mating Date", "Bull", "Return Type", "Days")
        header = ",".join(header_tuple) + "\n"
        g.write(header)

        for cow_id, num_insems in inseminations_per_cow:
            cow = str(cow_id)
            cow_insems = cow_dict[cow]["inseminations"]
            for insem in cow_insems:
                date_string = insem.insemination_date.strftime("%d-%b-%y")
                return_type = return_type_map[insem.return_type]
                line = f"{cow},{date_string},{insem.bull},{return_type},{insem.days_elapsed}" + "\n"
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

    cows = ["123", "A12", "A111", "45", "xyz"]
    cows.sort()
    print(cows)
    cows.sort(key=cow_id_sort_key)
    print(cows)

    result = calculate_non_return_rate_results(
        input_file_path="../temp/cowpoke/nrr_data.csv",
        output_file_path="../temp/cowpoke/nrr_data_output.csv",
        returns_bar_chart_file_path="../temp/cowpoke/return_days_bar_chart.svg",
    )
    for k, v in result.items():
        print(k, v)
