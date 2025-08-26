from datetime import datetime
from langchain.tools import tool
import pytz

@tool
def get_current_time_by_country(timezone: str) -> str:
    """
    Returns the current time (YYYY-MM-DD HH:MI:SS) for a given timezone.
    
    The timezone argument must be one of the following exact string values:
    1. 'Asia/Seoul' for South Korea, 'America/New_York' for USA, 'Europe/London' for UK.
    2. By leveraging your knowledge and using the time zone that applies to your country or city as a parameter
    
    Args:
        timezone (str): The name of the timezone.
    """
    
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S")
    except pytz.UnknownTimeZoneError:
        return f"Error: The timezone '{timezone}' is not supported."