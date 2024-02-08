from datetime import datetime, time, timedelta


def calculate_single_night_shift(start_dt, end_dt):
    # Convert start and end times to minutes from start of the day
    start_minutes = start_dt.hour * 60 + start_dt.minute
    end_minutes = end_dt.hour * 60 + end_dt.minute
    if end_minutes < start_minutes:  # Shift ends on the next day
        end_minutes += 1440

    # Define night window in minutes from start of the day
    night_start_minutes = 22 * 60  # 22:00
    night_end_minutes = 5 * 60 + 1440  # 05:00 on the next day

    # Calculate overlap
    overlap_start = max(start_minutes, night_start_minutes)
    overlap_end = min(end_minutes, night_end_minutes)
    total_overlap_minutes = max(0, overlap_end - overlap_start)

    # Check if the shift starts after midnight but before 5 AM
    if start_minutes < 300:  # Shift starts after midnight but before 5 AM
        total_overlap_minutes = min(end_minutes, 5 * 60) - start_minutes

    # Check if the shift starts before 22:00 and ends after midnight
    if start_minutes < night_start_minutes and end_minutes > night_end_minutes:
        # Calculate time from start to 22:00 and from midnight to end
        if end_minutes > 24 * 60:  # Ends after 5 AM
            morning_overlap = min(end_minutes - 1440, 5 * 60)
        else:  # Ends before 5 AM
            morning_overlap = end_minutes - 1440
        total_overlap_minutes = (
            24 * 60 - start_minutes) + morning_overlap - (22 * 60)

    # Convert minutes to hours
    overlap_hours = total_overlap_minutes / 60

    return round(overlap_hours, 1)


def calculate_night_hours(shifts):
    results = []
    for start_dt, end_dt in shifts:
        # Convert start and end times to minutes from start of the day
        start_minutes = start_dt.hour * 60 + start_dt.minute
        end_minutes = end_dt.hour * 60 + end_dt.minute
        if end_minutes < start_minutes:  # Shift ends on the next day
            end_minutes += 1440

        # Define night window in minutes from start of the day
        night_start_minutes = 22 * 60  # 22:00
        night_end_minutes = 5 * 60 + 1440  # 05:00 on the next day

        # Calculate overlap
        overlap_start = max(start_minutes, night_start_minutes)
        overlap_end = min(end_minutes, night_end_minutes)
        total_overlap_minutes = max(0, overlap_end - overlap_start)

        # Check if the shift starts after midnight but before 5 AM
        if start_minutes < 300:  # Shift starts after midnight but before 5 AM
            total_overlap_minutes = min(end_minutes, 5 * 60) - start_minutes

        # Check if the shift starts before 22:00 and ends after midnight
        if start_minutes < night_start_minutes and end_minutes > night_end_minutes:
            # Calculate time from start to 22:00 and from midnight to end
            if end_minutes > 24 * 60:  # Ends after 5 AM
                morning_overlap = min(end_minutes - 1440, 5 * 60)
            else:  # Ends before 5 AM
                morning_overlap = end_minutes - 1440
            total_overlap_minutes = (
                24 * 60 - start_minutes) + morning_overlap - (22 * 60)

        # Convert minutes to hours
        overlap_hours = total_overlap_minutes / 60

        results.append({
            "start": start_dt.strftime('%Y-%m-%d %H:%M'),
            "end": end_dt.strftime('%Y-%m-%d %H:%M'),
            # Round to one decimal place
            "overlap_hours": round(overlap_hours, 1)
        })

    return results


japan_holidays = [
    # Fixed holidays
    "2024-01-01",  # New Year's Day
    "2024-01-02",
    "2024-01-03",
    "2024-01-10",  # Coming of Age Day (Second Monday of January)
    "2024-02-11",  # National Foundation Day
    "2024-02-23",  # The Emperor's Birthday
    "2024-03-20",  # Vernal Equinox Day
    "2024-04-29",  # Showa Day
    "2024-05-03",  # Constitution Memorial Day
    "2024-05-04",  # Greenery Day
    "2024-05-05",  # Children's Day
    "2024-07-15",  # Marine Day (Third Monday of July)
    "2024-08-11",  # Mountain Day
    "2024-09-16",  # Respect for the Aged Day (Third Monday of September)
    "2024-09-23",  # Autumnal Equinox Day
    "2024-10-14",  # Health and Sports Day (Second Monday of October)
    "2024-11-03",  # Culture Day
    "2024-11-23",  # Labour Thanksgiving Day
    # Specific dates you mentioned
    "2024-12-29",
    "2024-12-30",
    "2024-12-31",
    "2024-08-13",
    "2024-08-14",
    "2024-08-15"
]


def get_movable_holiday(year):
    """
    Calculate movable holidays for the given year and return them as a list of strings.
    The example provided calculates Coming of Age Day.
    """
    # Example: Coming of Age Day - Second Monday of January
    coming_of_age_day = datetime(
        year, 1, 1) + timedelta(days=(7 - datetime(year, 1, 1).weekday() + 7) % 7 + 7)
    # Format the date as string since the rest of the code expects string format
    coming_of_age_day_str = coming_of_age_day.strftime('%Y-%m-%d')
    return [coming_of_age_day_str]
    # Add similar calculations for other movable holidays


def is_holiday(date):
    """
    Check if a given date is a holiday. The function now directly accepts datetime.date or datetime.datetime objects.
    """
    year = date.year

    # Fixed holidays that occur on the same date every year, but dynamically adjust the year
    fixed_holidays = [
        f"{year}-01-01",  # New Year's Day
        f"{year}-01-02",  # New Year's Day
        f"{year}-01-03",  # New Year's Day
        f"{year}-02-11",  # National Foundation Day
        f"{year}-02-23",  # The Emperor's Birthday
        f"{year}-03-20",  # Vernal Equinox Day
        f"{year}-04-29",  # Showa Day
        f"{year}-05-03",  # Constitution Memorial Day
        f"{year}-05-04",  # Greenery Day
        f"{year}-05-05",  # Children's Day
        f"{year}-07-15",  # Marine Day
        f"{year}-08-11",  # Mountain Day
        f"{year}-09-16",  # Respect for the Aged Day
        f"{year}-09-23",  # Autumnal Equinox Day
        f"{year}-11-03",  # Culture Day
        f"{year}-11-23",  # Labour Thanksgiving Day
        f"{year}-12-23",  # The Emperor's Birthday
        f"{year}-12-29",  # Specific date you mentioned
        f"{year}-12-30",
        f"{year}-12-31",
        f"{year}-08-13",
        f"{year}-08-14",
        f"{year}-08-15"
    ]

    # Get movable holidays for the year
    movable_holidays = get_movable_holiday(year)

    # Combine fixed and movable holidays
    all_holidays = fixed_holidays + movable_holidays

    # Format the date to string to check in the list
    date_str = date.strftime('%Y-%m-%d')

    return date_str in all_holidays
