import math
import random
import asyncio
from datetime import datetime, timedelta
import time
import subprocess
import configparser
import threading
import pystray
from PIL import Image 
from plyer import notification
import os
import prompt
import settings
import logviewer

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

def str_to_bool(value):
  return value.lower() in ("yes", "true", "t", "1")

def on_config_save(value):
        config['Settings']['last_ping'] = value
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

def on_config_save_first_time(value):
        config['Settings']['first_time'] = value
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

config = configparser.ConfigParser()
config.read(os.path.join(script_dir, 'config.ini'))
tagtime_start = int(config['Settings']['urping']) # ur-ping, start of tagtime
seed = int(config['Settings']['seed']) # the seed
gap = int(config['Settings']['gap']) # Average gap in minutes
first_time = str_to_bool(config['Settings']['first_time']) # first time?
last_ping = int(config['Settings']['last_ping'])

random.seed(seed) # Set the seed

async def run_tagtime():
    try:
        prompt.main()

    except Exception as e:
        print(f"An error occurred: {e}")

# Function to generate the next ping time based on the exponential distribution
def next_ping_time(last_ping_time, gap):
    # print(last_ping_time, " last ping time")
    gap = int(config['Settings']['gap'])   
    wait_time_minutes = -gap * math.log(1 - random.random())
    # print("wait time minutes", wait_time_minutes)
    wait_time = timedelta(minutes=wait_time_minutes)
    # print(int(wait_time.total_seconds()), " wait time")
    new_ping_time = int(last_ping_time + wait_time.total_seconds())
    # print(new_ping_time)
    return new_ping_time

async def first_time_check(now, last_ping_time, gap):
    count = 0
    gap = int(config['Settings']['gap'])
    print("Starting first time check. Login to the Cloud in Settings To Sync Your Logs.")
    print("first time check: ", now, " now, ", last_ping_time, " last ping time")
    while (now > last_ping_time):
        last_ping_time = next_ping_time(last_ping_time, gap)
        count += 1
    print(f"Skipped over {count} prompts!")
    return last_ping_time

async def catch_up(now, start_time, last_ping_time, gap):
    count = 0
    gap = int(config['Settings']['gap'])
    print("Catching up since last ping...")
    log_file_path = os.path.join(script_dir, "log.log")  # Define log file path

    print(start_time, " initial start time")
    print(last_ping_time, " initial last ping time")

    while (last_ping_time > start_time):
        start_time = next_ping_time(start_time, gap)
        count += 1

    count = 0

    print(now, " now")
    print(start_time, " start time")

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
        else:
            count -= 1

    print(f"you missed {count} pings!")
    return start_time

async def loop_time(new_ping_time, now):
    while (now < new_ping_time):
        await asyncio.sleep(10)
        now = int(time.time())
        print(int(new_ping_time - now), " seconds left")

def show_info_message(title, message):
    img_path = os.path.join(script_dir, "img")
    notification.notify(
        title=title,
        message=message,
        app_name="TagTime",
        app_icon=os.path.join(img_path, 'tagtime.ico')
    )


# Asynchronous function to print "hello" at each ping time
async def tagtime_pings(start_time, gap):
    now = int(time.time())
    gap = int(config['Settings']['gap'])
    if (first_time):
        new_ping_time = await first_time_check(now, start_time, gap)
        print(now, " now")
        print(new_ping_time, " new ping")
        on_config_save(str(int(new_ping_time)))
        on_config_save_first_time("False")
        show_info_message("Success!", "TagTime Successfully Installed!\nTagTime will now ping you randomly! If you want to log in, go to settings.")
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(run_tagtime(), loop)
    else:
        new_ping_time = int(config['Settings']['last_ping'])
        if now > new_ping_time:
            new_ping_time = await catch_up(now, start_time, new_ping_time, gap)
            on_config_save(str(int(new_ping_time)))
    while True:
        gap = int(config['Settings']['gap'])
        now = int(time.time())
        final_wait_time = int(new_ping_time) - now
        print(f"Next ping at {int(new_ping_time)}, which is in {final_wait_time:.2f} seconds.")
        await loop_time(new_ping_time, now)
        print(f"Ping at {int(new_ping_time)}")
        on_config_save(str(int(new_ping_time)))
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(run_tagtime(), loop)
        new_ping_time = next_ping_time(new_ping_time, gap)

def run_settings():
    try:
        settings.main()

    except Exception as e:
        print(f"An error occurred: {e}")

def run_logviewer():
    try:
        logviewer.main()

    except Exception as e:
        print(f"An error occurred: {e}")

def destroy(trayicon):
    trayicon.stop()  # Stop the tray icon
    os._exit(0)   # Exit the program

async def create_tray_icon():
    img_path = os.path.join(script_dir, "img")
    image = Image.open(os.path.join(img_path, 'tagtime.ico'))
    trayicon = pystray.Icon("Tagtime", image, menu=pystray.Menu(
        pystray.MenuItem("Settings", run_settings),
        pystray.MenuItem("Log Viewer/Editor", run_logviewer),
        pystray.MenuItem("Quit", lambda: destroy(trayicon))
    ))

    threading.Thread(target=trayicon.run, daemon=True).start()

# Run the asyncio event loop
async def main():
    # task1 = asyncio.create_task(run_system_tray())
    task1 = asyncio.create_task(create_tray_icon())
    task2 = asyncio.create_task(tagtime_pings(tagtime_start, gap))
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())
