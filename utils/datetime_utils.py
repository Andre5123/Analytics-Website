from datetime import datetime
import pytz

def toSQLDATETIME(date): #JSON file
    try:
        newDate = datetime.fromisoformat(date.replace("Z", "+00:00"))
        newDate = newDate.strftime("%Y-%m-%d %H:%M:%S")
        return newDate
    except ValueError as e:
        print("Parsing Error:",e)

def toJSStringDate(date): #From SQL format
    # Parse sql format
    dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    tz = "America/Toronto"
    tzInfo = pytz.timezone(tz)
    dt = tzInfo.localize(dt)

    #JS format:

    weekday = dt.strftime("%a")
    month = dt.strftime("%b")
    day = dt.strftime("%d")
    year = dt.strftime("%Y")
    time = dt.strftime("%H:%M:%S")
    gmt_offset = dt.strftime("GMT%z")
    tzname = "Eastern Standard Time"
    return f"{weekday} {month} {day} {year} {time} {gmt_offset} ({tzname})"

SQL_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def now_utc_sql():
    """
    Returns the current UTC time formatted for SQL (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now(pytz.UTC).strftime(SQL_DATETIME_FORMAT)