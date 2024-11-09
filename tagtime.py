import math
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
import customtkinter
import platform

class GapChangedException(Exception):
    """Custom exception to indicate that the gap has changed."""
    pass

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

def str_to_bool(value):
  return value.lower() in ("yes", "true", "t", "1")

def on_config_save(value):
        config.read(os.path.join(script_dir, 'config.ini'))
        config['Settings']['last_ping'] = value
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

def on_config_save_first_time(value):
        config.read(os.path.join(script_dir, 'config.ini'))
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

# Constants used in the RNG (similar to Perl script)
IA = 16807        # Multiplier
IM = 2147483647   # Modulus (2^31 - 1)
URPING = tagtime_start  # Fixed start time
SEED = seed      # Initial seed value
GAP = gap             # Mean gap in minutes for exponential distribution

# Initialize seed (This is a global variable, as it modifies state for each random call)
seed = SEED

# random.seed(seed) # Set the seed
# local_random = random.Random(seed)

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
    # print(config['Cloud']['refresh_token'], " refresh token")
    # print(config['Beeminder']['auth_token'], " auth token")
    # print(config['Beeminder']['goal_tags'], " goal tags")
    # print(config['TaskEditor']['tasks'], " tasks")
    prompt.PromptWindow(root)
    # try:
    #     prompt.main()

    # except Exception as e:
    #     print(f"An error occurred: {e}")

# Function to generate the next ping time based on the exponential distribution
def next_ping_time(prevping, gap):
    # # print(last_ping_time, " last ping time")
    # gap = int(config['Settings']['gap'])   
    # wait_time_minutes = -gap * math.log(1 - local_random.random())
    # # print("wait time minutes", wait_time_minutes)
    # wait_time = timedelta(minutes=wait_time_minutes)
    # # print(int(wait_time.total_seconds()), " wait time")
    # new_ping_time = int(last_ping_time + wait_time.total_seconds())
    # # print(new_ping_time)
    # return new_ping_time
    return max(prevping + 1, round(prevping + exprand(gap) * 60))

async def first_time_check(now, last_ping_time, gap):
    reset_rng() # Reset RNG to its initial state
    count = 0
    print("Starting first time check. Login to the Cloud in Settings To Sync Your Logs.")
    print("first time check: ", now, " now, ", last_ping_time, " last ping time")
    while (now > last_ping_time):
        last_ping_time = next_ping_time(last_ping_time, gap)
        count += 1
    print(f"Skipped over {count} prompts!")
    return last_ping_time

async def catch_up(now, start_time, last_ping_time, gap):
    count = 0
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
    global gap
    initial_gap = gap
    while (now < new_ping_time):
        await asyncio.sleep(2)
        now = int(time.time())
        # print(int(new_ping_time - now), " seconds left")

        # Check if gap has changed.
        config.read(os.path.join(script_dir, 'config.ini'))
        new_gap = int(config['Settings']['gap'])
        if initial_gap != new_gap:
            print("gap has changed.")
            gap = new_gap
            raise GapChangedException

def show_info_message(title, message):
    if platform.system() == 'Darwin':  # macOS
        # Use osascript to send a native macOS notification
        os.system(f'''
                osascript -e 'display notification "{message}" with title "{title}"'
        ''')
    else:
        img_path = os.path.join(script_dir, "img")
        notification.notify(
            title=title,
            message=message,
            app_name="TagTime",
            app_icon=os.path.join(img_path, 'tagtime.ico')
        )


# Asynchronous function to print "hello" at each ping time
async def tagtime_pings(start_time):
    global gap
    now = int(time.time())
    if (first_time):
        new_ping_time = await first_time_check(now, start_time, gap)
        print(now, " now")
        print(new_ping_time, " new ping")
        on_config_save(str(int(new_ping_time)))
        on_config_save_first_time("False")
        show_info_message("Success!", "TagTime Successfully Installed!\nTagTime will now ping you randomly! If you want to log in, go to settings.")
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

def run_settings():
    settings.SettingsWindow(root)
    # try:
    #     # subprocess.Popen(['python', os.path.join(script_dir, 'settings.py')])
    #     settings.main()

    # except Exception as e:
    #     print(f"An error occurred: {e}")

def run_logviewer():
    logviewer.LogViewerWindow(root)
    # try:
    #     # subprocess.Popen(['python', os.path.join(script_dir, 'logviewer.py')])
    #     logviewer.main()

    # except Exception as e:
    #     print(f"An error occurred: {e}")

def destroy(trayicon):
    trayicon.stop()  # Stop the tray icon
    os._exit(0)   # Exit the program

async def create_tray_icon():
    if platform.system() == 'Darwin':  # macOS
        return
    img_path = os.path.join(script_dir, "img")
    image = Image.open(os.path.join(img_path, 'tagtime.ico'))
    trayicon = pystray.Icon("Tagtime", image, menu=pystray.Menu(
        pystray.MenuItem("Settings", lambda: run_settings()),
        pystray.MenuItem("Log Viewer/Editor", lambda: run_logviewer()),
        pystray.MenuItem("Quit", lambda: destroy(trayicon))
    ))

    threading.Thread(target=trayicon.run, daemon=True).start()
    # trayicon.run()

# Combine asyncio and Tkinter event loops
def run_asyncio_in_tkinter():
    async def asyncio_task_runner():
        # task1 = asyncio.create_task(run_system_tray())
        task1 = asyncio.create_task(create_tray_icon())
        task2 = asyncio.create_task(tagtime_pings(tagtime_start))
        await asyncio.gather(task1, task2)

    # Start the asyncio loop
    asyncio.ensure_future(asyncio_task_runner())

    # Set up a repeating task for asyncio within Tkinter
    def tkinter_poll():
        try:
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))
        finally:
            root.after(100, tkinter_poll)

    tkinter_poll()

# Combined asyncio and Tkinter event loops
# def run_asyncio_in_tkinter():
#     async def asyncio_task_runner():
#         # task1 = asyncio.create_task(run_system_tray())
#         task1 = asyncio.create_task(create_tray_icon())
#         task2 = asyncio.create_task(tagtime_pings(tagtime_start, gap))  # Example, replace with actual values
#         await asyncio.gather(task1, task2)

#     # Create a new thread for asyncio
#     def start_asyncio_loop():
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(asyncio_task_runner())

#     # Start asyncio in a separate thread
#     threading.Thread(target=start_asyncio_loop, daemon=True).start()

#     # Set up a repeating task for asyncio within Tkinter
#     def tkinter_poll():
#         root.after(100, tkinter_poll)

#     tkinter_poll()

if __name__ == "__main__":
    global root
    root = customtkinter.CTk()  # The root window of customtkinter
    root.withdraw()   # Hide the root window since we only use Toplevels

    # Run asyncio and Tkinter together
    run_asyncio_in_tkinter()

    # Start Tkinter mainloop
    root.mainloop()

# # Run the asyncio event loop
# async def main():
#     # task1 = asyncio.create_task(run_system_tray())
#     task1 = asyncio.create_task(create_tray_icon())
#     task2 = asyncio.create_task(tagtime_pings(tagtime_start, gap))

#     # Start Tkinter mainloop in the main thread
#     loop = asyncio.get_event_loop()
#     global root
#     root = customtkinter.CTk()  # The root window of customtkinter
#     root.withdraw()   # Hide the root window since we only use Toplevels
#     threading.Thread(target=root.mainloop).start()

#     await asyncio.gather(task1, task2)

# if __name__ == "__main__":
#     asyncio.run(main())
