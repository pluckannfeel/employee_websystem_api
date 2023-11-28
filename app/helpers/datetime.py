from datetime import datetime, date, timedelta


def get_date_time_now():
    now = datetime.now()

    return now.strftime("%d/%m/%Y %H:%M:%S")


def get_date_now(type_format: str) -> str:
    today = date.today()
    
    if(type_format == 'd1'):
        # dd/mm/YY
        return today.strftime("%d/%m/%Y")
    elif(type_format == 'd2'):
        # Textual month, day and year
        return today.strftime("%B %d, %Y")
    elif(type_format == 'd3'):
        # mm/dd/y
        return today.strftime("%m/%d/%y")
    elif(type_format == 'd4'):
        return today.strftime("%b-%d-%Y")
    
def to_day_string(day: int) -> str:
    if day == 1:
        return '1st'
    elif day == 2:
        return '2nd'
    elif day == 3:
        return '3rd'
    elif day == 21:
        return '21st'
    elif day == 22:
        return '22nd'
    elif day == 23:
        return '23rd'
    elif day == 31:
        return '31st'
    else:
        return f'{day}th'


def adjust_time(date, time_str):
    # If the time is "24:00", adjust to "00:00" and add one day to the date
    if time_str == "24:00":
        adjusted_datetime = date + timedelta(days=1)
        time_str = "00:00"
    else:
        adjusted_datetime = date

    # Combine the adjusted date with the time
    time = datetime.strptime(time_str, "%H:%M").time()
    return datetime.combine(adjusted_datetime.date(), time)

def convert_to_js_compatible_format(date_str):
    # Parse the input date string
    dt = datetime.fromisoformat(date_str)
    
    # Convert back to string in ISO format
    js_compatible_date_str = dt.isoformat()
    
    return js_compatible_date_str