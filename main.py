import ctypes
import math
import os
import platform
import subprocess
import sys
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, font

import requests

# Define your theme colors
background_color = '#2D2D2D'  # Dark background
text_color = '#E1E1E1'  # Light text
button_color = '#5D3FD3'  # Purple buttons
button_hover_color = '#8167D3'  # Lighter purple for hover
button_text_color = '#FFFFFF'  # White text on buttons
custom_font = ('Helvetica', 12)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except ctypes.WinError as e:
        print(f"Admin check failed: {e}")
        return False


def run_as_admin(argv=None, debug=False):
    shell32 = ctypes.windll.shell32
    if argv is None and shell32.IsUserAnAdmin():
        return True  # Already an admin
    if argv is None:
        argv = sys.argv
    if hasattr(sys, '_MEIPASS'):
        # Support pyinstaller wrapped program.
        arguments = argv[1:]
    else:
        arguments = argv
    argument_line = u' '.join(arguments)
    executable = sys.executable
    if debug:
        print('Command line: ', executable, argument_line)
    retn = shell32.ShellExecuteW(None, u'runas', executable, argument_line, None, 1)
    if retn <= 32:
        return False
    return None


if platform.system() == "Windows":
    ret = run_as_admin()
    if ret is True:
        pass  # We are admin, and we continue with our code
    elif ret is None:
        sys.exit()  # We successfully relaunched as admin
    else:
        # We failed to relaunch as admin
        tk.Tk().withdraw()  # Prevents an empty tkinter window from appearing
        messagebox.showerror("Permission Error", "Failed to gain administrative permission."
                                                 " Please re-run the program as admin.")
        sys.exit()


def get_local_timezone():
    # Function to detect the local time zone
    local_timezone = datetime.now().astimezone().tzinfo
    return local_timezone


def set_time(date_time):
    if platform.system() == "Windows":
        subprocess.call(f'date {date_time.strftime("%m-%d-%y")} && time {date_time.strftime("%H:%M:%S")}', shell=True)
    else:
        subprocess.call(f'date -s "{date_time.strftime("%m/%d/%Y %H:%M:%S")}"', shell=True)


def get_real_time():
    # Get the real-world current time from an online service
    response = requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC')
    if response.status_code == 200:
        current_utc = datetime.strptime(response.json()['utc_datetime'], '%Y-%m-%dT%H:%M:%S.%f%z')
        local_timezone = get_local_timezone()  # Get the local timezone
        local_time = current_utc.astimezone(local_timezone)  # Convert UTC to local time
        return local_time.replace(tzinfo=None)
    else:
        raise Exception("Could not get real time from the internet")


def set_holiday(holiday_date):
    try:
        real_now = get_real_time()  # Fetch the real-world current time
    except Exception as e:
        print(f"Error fetching real-time: {e}")
        return  # or handle this in a way that's appropriate for your script

    # Create a potential holiday date for this year
    potential_holiday_this_year = holiday_date.replace(year=real_now.year)

    # Check if real current time is past the holiday this year
    if real_now < potential_holiday_this_year:
        # If real current time is before the holiday this year, set to last year's holiday
        holiday_date = holiday_date.replace(year=real_now.year - 1)
    else:
        # If real current time is after the holiday this year, the most recent occurrence is this year
        holiday_date = potential_holiday_this_year

    set_time(holiday_date)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Custom styling for buttons
def on_enter(e):
    e.widget['background'] = button_hover_color


def on_leave(e):
    e.widget['background'] = button_color


def set_time_twice():
    # This function sets the time twice when called
    set_time(get_real_time())  # First time setting
    time.sleep(0.005)
    set_time(get_real_time())  # Second time setting


def calculate_holiday_date(year, month, day_of_week, occurrence):
    """
    Calculate the date of a holiday that falls on a specific day of the week and occurrence in a month.

    Parameters:
    year (int): The year of the holiday.
    month (int): The month of the holiday (1-12).
    day_of_week (int): The day of the week the holiday falls on (0-6, Monday-Sunday).
    occurrence (int): The occurrence of the day of the week in the month (1-5).

    Returns:
    datetime: The calculated date of the holiday.
    """
    first_day_of_month = datetime(year, month, 1).weekday()
    days_to_add = (day_of_week - first_day_of_month + 7) % 7
    first_occurrence = datetime(year, month, 1 + days_to_add)
    holiday_date = first_occurrence + timedelta(days=7 * (occurrence - 1))
    return holiday_date


def get_holiday_date(year, holiday_name):
    """
    Calculate the date of a given holiday for a specific year.

    Parameters:
    year (int): The year for which to calculate the holiday.
    holiday_name (str): The name of the holiday to calculate.

    Returns:
    datetime: The date of the holiday for the given year.
    """
    if holiday_name == "Thanksgiving":
        # 4th Thursday of November
        return calculate_holiday_date(year, 11, 3, 4)
    elif holiday_name == "Easter":
        # Calculated via a different function, not shown here
        return calc_easter_date(year)
    else:
        return None


def calc_easter_date(year):
    """
    Calculate the date of Easter for a given year.
    Returns a datetime object representing Easter's date for that year.
    """
    try:
        # Algorithm to calculate the date of Easter
        special_years = [1954, 1981, 2049, 2076]
        specyr_sub = 7
        a = year % 19
        b = year % 4
        c = year % 7
        d = (19 * a + 24) % 30
        e = (2 * b + 4 * c + 6 * d + 5) % 7

        if year in special_years:
            day = (22 + d + e) - specyr_sub
        else:
            day = 22 + d + e

        # Ensure day is within the valid range for March or April
        if day > 31:
            return datetime(year, 4, day - 31)  # April
        else:
            return datetime(year, 3, day)  # March

    except Exception as e:
        print(f"An error occurred calculating Easter date: {e}")
        return None


holidays = {
    "Valentine's Day": datetime(1, 2, 14),
    "St. Patrick's Day": datetime(1, 3, 17),
    "Easter": calc_easter_date(2023),
    "Thanksgiving": get_holiday_date(2023, "Thanksgiving"),
    "Halloween": datetime(1, 10, 27),
    "Christmas": datetime(1, 12, 27)
}

try:
    if __name__ == '__main__':
        # GUI setup
        root = tk.Tk()
        root.title("Holiday Replay")
        app_font = font.Font(family='Helvetica', size=12)

        root.iconphoto(False, tk.PhotoImage(file=resource_path('header_icon.png')))

        # Prevent resizing, set a minimum size
        root.resizable(False, True)
        root.minsize(400, 200)

        # Apply the background color to the main window
        root.configure(bg=background_color)

        # Padding at the top of the app
        top_padding = tk.Frame(root, height=20, bg=background_color)
        top_padding.pack(side=tk.TOP, fill=tk.X)

        for holiday, date in holidays.items():
            if isinstance(date, datetime):
                # If the date is a variable date, calculate it for the current year
                if holiday == "Thanksgiving":
                    date = calculate_holiday_date(datetime.now().year, 11, 3, 4)
                elif holiday == "Easter":
                    date = calc_easter_date(2023)
                # Update the button command to handle both fixed and variable dates
                button = tk.Button(root, text=holiday, command=lambda d=date: set_holiday(d),
                                   bg=button_color, fg=button_text_color, font=custom_font)
                button.pack(pady=10, padx=100, fill=tk.BOTH)
                button.bind("<Enter>", on_enter)
                button.bind("<Leave>", on_leave)

        reset_button = tk.Button(root, text="Reset Time to Current",
                                 command=set_time_twice,
                                 bg=button_color, fg=button_text_color, font=custom_font)
        reset_button.pack(pady=50, padx=100, fill=tk.BOTH)
        reset_button.bind("<Enter>", on_enter)
        reset_button.bind("<Leave>", on_leave)

        # Set the window to be on top only at the start
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)

        # Centering the window on the screen
        root.update_idletasks()

        # Get the screen width and height
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Calculate position x, y
        x = (screen_width / 2) - (root.winfo_width() / 2)
        y = (screen_height / 2) - (root.winfo_height() / 2)
        root.geometry(f'+{int(x)}+{int(y)}')

        root.mainloop()

except Exception as e:
    messagebox.showerror(f"Error: {e}")
