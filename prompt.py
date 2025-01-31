import os
import customtkinter
import threading
import re
from datetime import datetime
import configparser
import time
from playsound import playsound
import requests
import json
import beeminder
import settings
import logviewer
import platform
import math
import multiprocessing

def resource_path(relative_path):
    """Get the absolute path to a resource in the same folder as the script."""
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path)

class PromptWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Initialize the auto-submit timer
        self.auto_submit_timer = None
        self.auto_submit_time_limit = 60 * 1000  # 60 seconds in milliseconds

        self.config = configparser.ConfigParser()
        self.config.read(resource_path('config.ini'))
        self.appearance_mode = self.config['Settings']['appearance_mode']
        silent_ping_option = self.config['Settings']['silent_ping']

        self.alltags = (self.config['Tags']['tags']).split(',')

        self.tagArray = []
        self.tagList = []
        self.colorsList = ["DarkOrchid4", "DarkOrange3", "firebrick4", "navy", "forest green"]
        self.tag_end_index = 0

        # configure window
        if platform.system() == 'Darwin':
            self.wm_iconbitmap()
        else:
            self.after(250, lambda: self.iconbitmap(resource_path("img/tagtime.ico")))
        self.title("TagTime")
        self.center_window(400, 125)
        self.font = customtkinter.CTkFont(family="Helvetica", size=12)
        # Bring the window to the front
        self.lift()
        self.attributes("-topmost", True)
        self.after(1000, lambda: self.attributes("-topmost", False))  # Disable topmost after 1 second
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.sound = self.config['Settings']['sound']
        if silent_ping_option == "True":
            pass
        else:
            threading.Thread(target=playsound, args=(resource_path(f"sounds/{self.sound}"),), daemon=True).start()

        # configure frame
        self.frame = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame.pack(fill="both", expand=True)

        # text box
        current_time = datetime.now()
        formatted_time = current_time.strftime("%H:%M:%S")
        self.textbox = customtkinter.CTkLabel(self.frame, text=f"It's Tag Time! What Are You Doing RIGHT NOW ({formatted_time})?")
        self.textbox.pack(pady = 5, padx = 10)

        # tag input box
        self.taginput = customtkinter.CTkEntry(self.frame, placeholder_text="Enter tag(s)", width=350, height=32, border_color=["black", "grey"], font=self.font, fg_color="transparent", bg_color="transparent")
        self.taginput.pack(padx = 5)
        self.taginput.icursor(22)  # Set the cursor position
        self.taginput.bind("<Return>", self.on_enter_pressed_tag)
        self.tagnumber = 0
        self.tagtotal = 0
        self.taginput.focus_force()
        self.previoustag = "VENUSBOT"
        self.from_space = False

        self.framelength = self.taginput.winfo_reqwidth()
        self.framelength_total = 0
        self.framecount = 0

        # submit button frame
        self.submitframe = customtkinter.CTkFrame(self.frame, corner_radius=0, width=360, height=40, fg_color="transparent", bg_color="transparent")
        self.submitframe.pack_propagate(0)
        self.submitframe.pack()

        # submit button
        self.submitbutton = customtkinter.CTkButton(self.submitframe,
                                                text="Submit",
                                                text_color=["black", "white"],
                                                command=self.on_enter_pressed_tag,
                                                font=("Impact", 18),
                                                fg_color="transparent",
                                                hover_color="green",
                                                border_width=2,
                                                border_color=["black", "grey"],
                                                state="normal",
                                                width=80)
        self.submitbutton.pack(pady = 5, padx = 5, side = "right")

        self.swapcount = 0

        if silent_ping_option == "True":
            self.ping = "silent"
            self.withdraw()
            self.download_button_event()
            return
        else:
            pass

        # Start the auto-submit timer
        self.start_auto_submit_timer()

        # Schedule determinePingTime to run after the window loads
        self.after(750, self.startDeterminePingTime)


    def start_auto_submit_timer(self):
        if self.auto_submit_timer is not None:
            self.after_cancel(self.auto_submit_timer)
        self.auto_submit_timer = self.after(self.auto_submit_time_limit, self.auto_submit)

    def auto_submit(self):
        print("1 minute has passed! AFK Flags Set.")
        self.ping = "afk RETRO"
        self.download_button_event()

    def change_appearance_mode_event(self):
        customtkinter.set_appearance_mode(self.radiovar.get())
        self.focus_force()

    def center_window(self, width=400, height=490):
        # Get the screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate the position for the window to be centered
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Set the geometry of the window
        self.geometry(f'{width}x{height}+{x}+{y}')

    def on_enter_pressed_tag(self, event=0):
        self.ping = self.taginput.get()
        if self.ping == "":
            self.run_logviewer()
            return
        elif self.ping == "?":
            self.run_settings()
            self.taginput.delete(0, customtkinter.END)
            return
        elif self.ping == '"':
            last_tags = self.copy_tags_from_last_log_entry()
            if last_tags:
                self.taginput.delete(0, customtkinter.END)
                self.ping = last_tags
                print(self.ping)
                self.download_button_event()
            else:
                print("no previous logs")
            return
        else:
            self.download_button_event()
            return

    def reset_input(self):
        self.taginput.delete(0, customtkinter.END)
        self.taginput.focus()

    def download_button_event(self):

        # Regular expression to match words and phrases inside parentheses
        pattern = r'\(.*?\)|\S+'

        # Use re.findall to get all matches (both words and content inside parentheses)
        self.seperated_ping = re.findall(pattern, self.ping)

        # REPLACE TASK EDITOR TAGS
        task_tags = self.config['TaskEditor']['tasks']
        if task_tags != "NULL":
            task_tags_json = json.loads(task_tags)
            for item in self.seperated_ping:
                try:
                    if task_tags_json[f"{item}"] != "N/A":
                        original_text = task_tags_json[f"{item}"]
                        seperated_text = re.findall(pattern, original_text)
                        index = self.seperated_ping.index(item)
                        counter = 0
                        for new_item in seperated_text:
                            if counter == 0:
                                self.seperated_ping[index] = new_item
                            else:
                                self.seperated_ping.insert(index, new_item)
                            index += 1
                            counter += 1
                except Exception as e:
                    print(e)


        self.beeminder_tags = self.seperated_ping[:]
        self.log_entries_to_file()
        self.beeminder_check()
        if platform.system() == 'Darwin':
            os._exit(0)
        else:
            self.destroy()

    def log_entries_to_file(self):
        
        # Define the log file path
        log_file_path = resource_path('log.log')
        
        # Get the current time for the log entry
        if (self.second_to_last_ping_time):
            now = self.second_to_last_ping_time
        else:
            print("no second to last ping time")
            now = int(time.time())

        self.beeminder_time = now

        # format tags
        formatted_tags = ' '.join(self.seperated_ping)

        # Get the current time
        current_day = time.localtime()

        # Get the current day
        day = time.strftime("%A", current_day)

        # Get the first three letters of the day in uppercase
        day_abbr = day[:3].upper()

        if len(formatted_tags) > 50:
            new_formatted_tags = (formatted_tags[:len(formatted_tags)]).ljust(len(formatted_tags))
            if len(formatted_tags) < 56:
                spaces = 55 - len(formatted_tags)
                current_time = datetime.now().strftime("%m.%d %H:%M:%S")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time} {day_abbr}]\n'
            elif len(formatted_tags) < 60:
                spaces = 59 - len(formatted_tags)
                current_time = datetime.now().strftime("%m.%d %H:%M:%S")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            elif len(formatted_tags) < 63:
                spaces = 62 - len(formatted_tags)
                current_time = datetime.now().strftime("%m.%d %H:%M")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            elif len(formatted_tags) < 66:
                spaces = 65 - len(formatted_tags)
                current_time = datetime.now().strftime("%d %H:%M")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            elif len(formatted_tags) < 69:
                spaces = 68 - len(formatted_tags)
                current_time = datetime.now().strftime("%H:%M")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            elif len(formatted_tags) < 72:
                spaces = 71 - len(formatted_tags)
                current_time = datetime.now().strftime("%M")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            else:
                current_time = datetime.now().strftime("%m.%d %H:%M:%S")
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags}\n'

        else:
            new_formatted_tags = (formatted_tags[:50]).ljust(50)
            current_time = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
            log_entry = f'{now} {new_formatted_tags} [{current_time} {day_abbr}]\n'
        
        # Write the log entry to the log file
        with open(log_file_path, "a") as log_file:
            log_file.write(log_entry)
        
        # Clear the input fields after logging
        self.taginput.delete(0, customtkinter.END)

        refresh_token = self.config['Cloud']['refresh_token']

        try:
            # update cloud database
            self.withdraw()
            self.iconify()
            if refresh_token != "NULL":
                self.update_cloud_log(log_file_path)
                self.on_sync_log()
            else:
                print("Couldn't Sync to Cloud: Not Signed In")
        except Exception as e:
            print(e)
            print("FAILED TO SYNC TO CLOUD")

    def str_to_bool(self, value):
        return value.lower() in ("yes", "true", "t", "1")

    def tag_format(self, tag):
        length = len(tag)
        for i in range(9):
            self.taginput.insert(113, " ")
        length = len(self.taginput.get())

        self.taginput.icursor(113)
        self.tag_end_index = self.get_tag_index()
        self.taginput.focus_force()

    def get_last_word(self, tag):
        # Split the string by whitespace
        words = tag.split()
        # Check if the list is not empty and return the last word
        if words:
            return words[-1]
        else:
            return ""
        
    def remove_last_word(self, tag):
        last_word_match = re.search(r'\S+\s*$', tag)
        if last_word_match:
            last_word = last_word_match.group()
            new_string = tag[:last_word_match.start()]
            return new_string
        else:
            return tag
        
    def remove_frame(self):
        if self.tagArray:
            frame = self.tagArray.pop(-1)
            ogtag = self.tagList.pop(-1)
            frame.place_forget()
            tag = self.taginput.get()
            tag = self.remove_last_word(tag)
            self.taginput.delete(0, 113)
            self.taginput.insert(0, tag + ' ')
            self.tag_end_index = self.get_tag_index()
            tag_width = self.font.measure(ogtag)
            total = tag_width + 25
            self.framelength_total -= total + 2
        else:
            pass

    def get_tag_index(self):
        return self.taginput.index("end")
    
    def on_backspace_key(self, event):
        index = self.get_tag_index()
        if index <= 1:

            if self.tagArray:
                self.taginput.delete(0, 113)
                self.taginput.insert(0, "")
                self.tagList = []
                self.framelength_total = 0
                for item in self.tagArray:
                    frame = item
                    frame.place_forget()
                self.tagArray = []
            else:
                pass

            return
        if index <= (self.tag_end_index):
            self.remove_frame()

    def on_config_save(self):
        with open(resource_path('config.ini'), 'w') as configfile:
            self.config.write(configfile)

    def on_space_pressed_tag(self, event):
        tag = self.taginput.get()
        cursor_position = self.taginput.index("insert")
        current_text = self.taginput.get()[:cursor_position]

        if '(' in current_text:
            pass
        else:
            # Remove the last character (space) from the entry
            current_text = self.taginput.get()
            if current_text.endswith(' '):
                self.taginput.delete(len(current_text)-1, len(current_text))
            self.on_enter_pressed_tag(event)

    def on_comma_pressed_tag(self, event):
        tag = self.taginput.get()
        cursor_position = self.taginput.index("insert")
        current_text = self.taginput.get()[:cursor_position]

        if '(' in current_text:
            pass
        else:
            # Remove the last character (comma) from the entry
            current_text = self.taginput.get()
            if current_text.endswith(','):
                self.taginput.delete(len(current_text)-1, len(current_text))
            self.on_enter_pressed_tag(event)

    def run_settings(self):
        multiprocessing.Process(target=settings.main).start()

    def run_logviewer(self):
        multiprocessing.Process(target=logviewer.main).start()

    def on_sync_log(self):
        refresh_token = self.config['Cloud']['refresh_token']
        url = "https://hello-bgfsl5zz5q-uc.a.run.app/fetchlog"
        try:
            update_response = requests.post(
                url,
                json={
                    'refresh_token': refresh_token
                }
            )

            if update_response.status_code == 200:
                update_data = update_response.json()
                file_contents = update_data['file_content']
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
                print("Error in grabbing cloud log:", update_response.json())
        except Exception as e:
            print(e)

    def update_cloud_log(self, file_path):
        new_url = "https://hello-bgfsl5zz5q-uc.a.run.app/update_cloud_log"
        refresh_token = self.config['Cloud']['refresh_token']

        # Read the latest line from the file
        latest_line = ""
        with open(file_path, 'r') as file:
            # Move the cursor to the end of the file and read the last line
            lines = file.readlines()
            if lines:  # Check if the file is not empty
                latest_line = lines[-1].strip()  # Remove any trailing newlines or spaces

        # If no lines are found, exit the function early
        if not latest_line:
            return

        update_response = requests.post(
            new_url,
            json={
                'refresh_token': refresh_token,
                'new_log_entry': latest_line
            }
        )

        if update_response.status_code == 200:
            update_data = update_response.json()
            print("Success:", update_data['message'])
        else:
            print("Error in updating cloud log:", update_response.json())

    def copy_tags_from_last_log_entry(self):
        log_file_path = resource_path('log.log')

        # Read the last line of the log file
        try:
            with open(log_file_path, "rb") as log_file:
                log_file.seek(-2, os.SEEK_END)  # Go to the second last byte.
                while log_file.read(1) != b"\n":  # Until EOL is found...
                    log_file.seek(-2, os.SEEK_CUR)  # ...jump back the read byte plus one more.
                last_line = log_file.readline().decode().strip()
            
            # Extract the tags from the last log entry
            tags_section = last_line.split("[")[0].strip()  # Everything before the timestamp
            tags = tags_section.split(" ", 1)[1].rstrip()  # Remove the leading Unix timestamp and any trailing spaces
            return tags

        except Exception as e:
            print(f"Error reading log file: {e}")
            return None
        
    def beeminder_check(self):

        auth_token = self.config['Beeminder']['auth_token']
        gap = int(self.config['Settings']['gap'])
        gap_value = gap / 60
        if auth_token != "NULL":
            goal_tags = self.config['Beeminder']['goal_tags']
            goal_tags_json = json.loads(goal_tags)
            for tag in self.beeminder_tags:
                if '(' in tag or ')' in tag:
                    pass
                else:
                    for key, value in goal_tags_json.items():
                        for item in value.split(" "):
                            if tag == item.strip():
                                if len(self.beeminder_tags) > 1:
                                    combined_tags = " ".join(self.beeminder_tags)
                                else:
                                    combined_tags = (self.beeminder_tags[0]) if self.beeminder_tags else ""
                                try:
                                    beeminder.create_datapoint(auth_token, self.beeminder_time, key, combined_tags, gap_value)
                                    print(f"Successfully added datapoint to Beeminder Goal {key}!")
                                except Exception as e:
                                    print(e)

    def check_for_comment(self, string):
        # Regular expression to capture content inside parentheses
        match = re.search(r'\((.*?)\)', string)

        # Check if there is a match and print the result
        if match:
            content = match.group(1)  # Extract the content inside parentheses
            return content
        else:
            content = ''
            return content
        
    def on_closing(self):
        self.ping = "err"
        self.download_button_event()

    def startDeterminePingTime(self):
        thread = threading.Thread(target=self.determinePingTime, daemon=True)
        thread.start()

    def determinePingTime(self):

        seed1 = int(self.config['Settings']['seed'])
        tagtime_start1 = int(self.config['Settings']['urping'])
        gap1 = int(self.config['Settings']['gap'])
        now = int(time.time()) + 1

        # Constants used in the RNG (similar to Perl script)
        IA1 = 16807        # Multiplier
        IM1 = 2147483647   # Modulus (2^31 - 1)
        URPING1 = tagtime_start1  # Fixed start time
        SEED1 = seed1      # Initial seed value
        GAP1 = gap1            # Mean gap in minutes for exponential distribution

        # Initialize seed
        seed1 = SEED1

        # RNG equivalent to Perl's ran0 function
        def ran0():
            nonlocal seed1
            seed1 = (IA1 * seed1) % IM1
            return seed1

        # Function to generate a random number between 0 and 1
        def ran01():
            return ran0() / IM1

        # Exponential random number generator
        def exprand(gap):
            return -gap * math.log(ran01())

        def reset_rng():
            nonlocal seed1
            seed1 = SEED1

        # Function to generate the next ping time based on the exponential distribution
        def next_ping_time(prevping, gap):
            return max(prevping + 1, round(prevping + exprand(gap) * 60))
        
        reset_rng()

        last_ping_time = URPING1
        second_to_last_ping_time = None  # Variable to hold the second-to-last value

        while now > last_ping_time:
            second_to_last_ping_time = last_ping_time  # Store the current value as the previous
            last_ping_time = next_ping_time(last_ping_time, GAP1)

        self.second_to_last_ping_time = second_to_last_ping_time
        
def startup(parent):
    PromptWindow(parent)

def main():
    config = configparser.ConfigParser()
    config.read(resource_path('config.ini'))
    appearance_mode = config['Settings']['appearance_mode']
    customtkinter.set_appearance_mode(appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue")
    root = customtkinter.CTk()  # Create the main window
    root.withdraw()  # Hide the main window since we are only using Toplevels
    startup(root)
    root.mainloop()
 
if __name__ == "__main__":
    # main()
    config = configparser.ConfigParser()
    config.read(resource_path('config.ini'))
    appearance_mode = config['Settings']['appearance_mode']
    customtkinter.set_appearance_mode(appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue")
    root = customtkinter.CTk()  # Create the main window
    root.withdraw()  # Hide the main window since we are only using Toplevels
    startup(root)
    root.mainloop()
