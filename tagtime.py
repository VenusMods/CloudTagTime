import math
import asyncio
from datetime import datetime
import time
import configparser
import threading
import pystray
from PIL import Image 
from plyer import notification
import os
import prompt
import settings
import logviewer
import platform
import multiprocessing
import requests
from notifypy import Notify

class GapChangedException(Exception):
    """Custom exception to indicate that the gap has changed."""
    pass

# Get the directory of the current script
def resource_path(relative_path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path)

def str_to_bool(value):
  return value.lower() in ("yes", "true", "t", "1")

def on_config_save(value):
        config.read(resource_path('config.ini'))
        config['Settings']['last_ping'] = value
        with open(resource_path('config.ini'), 'w') as configfile:
            config.write(configfile)

def on_config_save_first_time(value):
        config.read(resource_path('config.ini'))
        config['Settings']['first_time'] = value
        with open(resource_path('config.ini'), 'w') as configfile:
            config.write(configfile)

config = configparser.ConfigParser()
config.read(resource_path('config.ini'))
tagtime_start = int(config['Settings']['urping']) # ur-ping, start of tagtime
seed = int(config['Settings']['seed']) # the seed
gap = int(config['Settings']['gap']) # Average gap in minutes
first_time = str_to_bool(config['Settings']['first_time']) # first time?
last_ping = int(config['Settings']['last_ping'])

# Constants used in the RNG (similar to Perl script)
IA = 16807        # Multiplier
IM = 2147483647   # Modulus (2^31 - 1)
URPING = tagtime_start  # Fixed start time
SEED = seed      # Initial seed value
GAP = gap             # Mean gap in minutes for exponential distribution

# Initialize seed (This is a global variable, as it modifies state for each random call)
seed = SEED

# RNG equivalent to Perl's ran0 function
def ran0():
    global seed
    seed = (IA * seed) % IM
    return seed

# Function to generate a random number between 0 and 1
def ran01():
    return ran0() / IM

# Exponential random number generator
def exprand(gap):
    return -gap * math.log(ran01())

def reset_rng():
    global seed
    seed = SEED

def run_tagtime():
    multiprocessing.Process(target=prompt.main).start()

# Function to generate the next ping time based on the exponential distribution
def next_ping_time(prevping, gap):
    return max(prevping + 1, round(prevping + exprand(gap) * 60))

async def first_time_check(now, last_ping_time, gap):
    reset_rng() # Reset RNG to its initial state
    count = 0
    print("Starting first time check. Login to the Cloud in Settings To Sync Your Logs.")
    while (now > last_ping_time):
        last_ping_time = next_ping_time(last_ping_time, gap)
        count += 1
    print(f"Skipped over {count} prompts!")
    return last_ping_time

async def catch_up(now, start_time, last_ping_time, gap):
    count = 0
    print("Catching up since last ping...")
    log_file_path = resource_path("log.log")  # Define log file path

    while (last_ping_time > start_time):
        start_time = next_ping_time(start_time, gap)
        count += 1

    count = 0
    log_entries = []

    while (now > start_time):
        # Get the current timestamp
        new_ping_time_unix = int(start_time)

        # Convert UNIX timestamp to a datetime object
        new_ping_datetime = datetime.fromtimestamp(new_ping_time_unix)

        # Format the datetime object as desired
        formatted_last_ping_time = new_ping_datetime.strftime("%Y.%m.%d %H:%M:%S")

        # Get the day abbreviation
        day = new_ping_datetime.strftime("%a").upper()
        day_abbr = day[:3].upper()

        # format tags
        tags = "afk off RETRO"
        formatted_tags = (tags[:50]).ljust(50)

        # Format the log entry
        log_entry = f'{new_ping_time_unix} {formatted_tags} [{formatted_last_ping_time} {day_abbr}]\n'

        start_time = next_ping_time(start_time, gap)
        count += 1
        
        now = int(time.time())

        if new_ping_time_unix < now:
            # Write to the log file
            with open(log_file_path, "a") as log_file:
                log_file.write(log_entry)
            log_entries.append(log_entry)
        else:
            count -= 1

    print(f"you missed {count} pings!")

    # Combine the log entries into one big string and send to cloud
    combined_log = ''.join(log_entries)
    update_cloud_log(combined_log.rstrip('\n'))

    return start_time

async def loop_time(new_ping_time, now):
    global gap
    initial_gap = gap
    while (now < new_ping_time):
        await asyncio.sleep(2)
        now = int(time.time())

        # Check if gap has changed.
        config.read(resource_path('config.ini'))
        new_gap = int(config['Settings']['gap'])
        if initial_gap != new_gap:
            print("gap has changed.")
            gap = new_gap
            raise GapChangedException

def show_info_message(self, title, message):
    if platform.system() == 'Darwin':  # macOS
        # Use osascript to send a native macOS notification
        # os.system(f'''
        #         osascript -e 'display notification "{message}" with title "{title}"'
        # ''')
        notification = Notify()
        notification.title = title
        notification.message = message
        notification.application_name = "TagTime"

        notification.send(block=False)
    else:
        notification = Notify()
        notification.title = title
        notification.message = message
        notification.application_name = "TagTime"
        notification.icon = resource_path("img/tagtime.ico")

        notification.send(block=False)


# Asynchronous function to print "hello" at each ping time
async def tagtime_pings(start_time):
    global gap
    now = int(time.time())
    if (first_time):
        new_ping_time = await first_time_check(now, start_time, gap)
        on_config_save(str(int(new_ping_time)))
        on_config_save_first_time("False")
        show_info_message("TagTime Successfully Installed!", "TagTime will now ping you randomly! If you want to log in, go to settings.")
        run_tagtime()
    else:
        new_ping_time = int(config['Settings']['last_ping'])
        if now > new_ping_time:
            new_ping_time = await catch_up(now, start_time, new_ping_time, gap)
            on_config_save(str(int(new_ping_time)))
        else:
            print("Nothing to catch up on, Redo'ing first time method to put you back onto schedule. This is why you will see first time startup print statements next.")
            new_ping_time = await first_time_check(now, start_time, gap)
            on_config_save(str(int(new_ping_time)))
    while True:
        try:
            now = int(time.time())
            final_wait_time = int(new_ping_time) - now
            print(f"Next ping at {int(new_ping_time)}, which is in {final_wait_time:.2f} seconds.")
            on_config_save(str(int(new_ping_time)))
            await loop_time(new_ping_time, now)
            print(f"Ping at {int(new_ping_time)}")
            run_tagtime()
            new_ping_time = next_ping_time(new_ping_time, gap)
        except GapChangedException:
            print("Handling gap change, Redo'ing first time method to put you back onto schedule. This is why you will see first time startup print statements next.")
            print(gap, " new gap")
            now = int(time.time())
            new_ping_time = await first_time_check(now, start_time, gap)
            on_config_save(str(int(new_ping_time)))

def update_cloud_log(new_log_entry):
    new_url = "https://hello-bgfsl5zz5q-uc.a.run.app/update_cloud_log"
    refresh_token = config['Cloud']['refresh_token']

    if refresh_token == "NULL":
        return

    update_response = requests.post(
        new_url,
        json={
            'refresh_token': refresh_token,
            'new_log_entry': new_log_entry
        }
    )

    if update_response.status_code == 200:
        update_data = update_response.json()
        print("Success:", update_data['message'])
        file_contents = update_data['updated_log_content']
        print("Success: Grabbed Log from Cloud")

        file_path = resource_path('log.log')

        try:
            # Write the file contents to the log file in the root directory
            with open(file_path, "w") as file:
                file.write(file_contents)
            print(f"Log file updated: {file_path}")
        except Exception as e:
            print(f"Error writing to log file: {e}")

    else:
        print("Error in updating cloud log:", update_response.json())

def run_settings():
    multiprocessing.Process(target=settings.main).start()

def run_logviewer():
    multiprocessing.Process(target=logviewer.main).start()

def destroy(trayicon):
    trayicon.stop()  # Stop the tray icon
    os._exit(0)   # Exit the program

def create_tray_icon():
    # if platform.system() == 'Darwin':  # macOS
    #     return
    # elif platform.system() == "Windows":
    img_path = resource_path("img/tagtime.ico")
    image = Image.open(img_path)
    trayicon = pystray.Icon("Tagtime", image, menu=pystray.Menu(
        pystray.MenuItem("Settings", lambda: run_settings()),
        pystray.MenuItem("Log Viewer/Editor", lambda: run_logviewer()),
        pystray.MenuItem("Quit", lambda: destroy(trayicon))
    ))

    trayicon.run()

def start_asyncio_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(tagtime_pings(tagtime_start))

if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')
    asyncio_thread = threading.Thread(target=start_asyncio_loop, daemon=True)
    asyncio_thread.start()

    create_tray_icon()
