import os
import customtkinter
import threading
import re
import subprocess
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

class PromptWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Initialize the auto-submit timer
        self.auto_submit_timer = None
        self.auto_submit_time_limit = 60 * 1000  # 60 seconds in milliseconds

        # Get the directory of the current script
        self.script_dir = os.path.dirname(os.path.realpath(__file__))

        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(self.script_dir, 'config.ini'))
        # print(self.config['Cloud']['refresh_token'], " refresh token")
        # print(self.config['Beeminder']['auth_token'], " auth token")
        # print(self.config['Beeminder']['goal_tags'], " goal tags")
        # print(self.config['TaskEditor']['tasks'], " tasks")
        self.appearance_mode = self.config['Settings']['appearance_mode']
        silent_ping_option = self.config['Settings']['silent_ping']

        customtkinter.set_appearance_mode(self.appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
        customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue")

        # set paths
        self.img_path = os.path.join(self.script_dir, "img")

        self.alltags = (self.config['Tags']['tags']).split(',')

        self.tagArray = []
        self.tagList = []
        self.colorsList = ["DarkOrchid4", "DarkOrange3", "firebrick4", "navy", "forest green"]
        self.tag_end_index = 0

        # configure window
        # self.iconbitmap(os.path.join(self.img_path, 'tagtime.ico'))
        if platform.system() == 'Darwin':
            self.wm_iconbitmap()
        else:
            self.after(250, lambda: self.iconbitmap(os.path.join(self.img_path, 'tagtime.ico')))
        self.title("TagTime")
        self.center_window(400, 125)
        self.font = customtkinter.CTkFont(family="Helvetica", size=12)
        # Bring the window to the front
        self.lift()
        self.attributes("-topmost", True)
        self.after(1000, lambda: self.attributes("-topmost", False))  # Disable topmost after 1 second
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.sound_path = os.path.join(self.script_dir, "sounds")
        self.sound = self.config['Settings']['sound']
        if silent_ping_option == "True":
            print("silent ping is true, skipping sound")
        else:
            print("silent ping is not on, playing sound")
            threading.Thread(target=playsound, args=(os.path.join(self.sound_path, self.sound),), daemon=True).start()

        # self.overrideredirect(True)  # Remove the title bar
        # self.focus_force()

        # # Custom title bar frame
        # title_bar1 = customtkinter.CTkFrame(self, height=30, corner_radius=0)
        # title_bar1.pack(fill="x")

        # # Title label
        # title_label1 = customtkinter.CTkLabel(title_bar1, text="TagTime", font=self.font, text_color=["black", "white"])
        # title_label1.pack(side="left", padx=10)

        # # Close button
        # close_button1 = customtkinter.CTkButton(title_bar1, text="X", font=("Impact", 18), width=30, command=self.destroy, text_color=["black", "white"], fg_color="transparent", hover_color="red", corner_radius=0)
        # close_button1.pack(side="right")

        # # Minimize button
        # min_button1 = customtkinter.CTkButton(title_bar1, text="-", font=("Impact", 18), width=30, command=self.minimize_main_window, text_color=["black", "white"], fg_color="transparent", hover_color="orange", corner_radius=0)
        # min_button1.pack(side="right")

        # # Bind events for moving the window
        # title_bar1.bind("<Button-1>", lambda event: self.start_move(event, self))
        # title_bar1.bind("<B1-Motion>", lambda event: self.on_move(event, self))
        # title_label1.bind("<Button-1>", lambda event: self.start_move(event, self))
        # title_label1.bind("<B1-Motion>", lambda event: self.on_move(event, self))

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
        # self.taginput.bind("<KeyRelease>", self.update_listbox)
        # self.taginput.bind("<BackSpace>", self.on_backspace_key)
        # self.taginput.bind("<KeyRelease-space>", self.on_space_pressed_tag)
        # self.taginput.bind("<KeyRelease-comma>", self.on_comma_pressed_tag)
        self.tagnumber = 0
        self.tagtotal = 0
        self.taginput.focus_force()
        self.previoustag = "VENUSBOT"
        self.from_space = False
        # self.taginput.bind("<Down>", self.on_down_key)
        # self.taginput.bind("<Tab>", self.on_tab_key)

        # test box

        # entry = tk.Entry(self.frame)
        # entry.pack()
        # entry.bind("<KeyRelease>", update_listbox)

        # self.listboxframe = customtkinter.CTkFrame(self.listboxwindow, width=90, height = 40)
        # self.listboxframe.pack_propagate(0)
        # self.listboxframe.place(x=100, y=100)

        # self.listbox = CTkListbox(self.listboxframe, width=80, height=35, scrollbar_button_color="red", border_color="black", border_width=0)
        # self.listbox.place(x=0,y=0)
        # self.listbox.bind("<Double-Button-1>", self.select_suggestion)
        # self.listboxframe.place_forget()

        # advanced_mode = self.str_to_bool(self.config['Settings']['advanced_mode']) # ur-ping, start of tagtime

        # # comment input box
        # self.commentinput = customtkinter.CTkTextbox(self.frame, width=350, height=150, border_color=["black", "grey"])
        # self.commentinput.pack(pady = 15, padx = 5)
        # self.commentinput.bind("<Return>", self.on_enter_pressed_comment)
        # self.add_comment_placeholder("Comments...")

        # if not advanced_mode:
        #     self.commentinput.pack_forget()

        # # tags list frame
        # self.tagsframe = customtkinter.CTkFrame(self.frame, corner_radius=0, width=360, height=80, fg_color="transparent")
        # self.tagsframe.pack_propagate(0)
        # self.tagsframe.pack_forget()

        # # tags list text box
        # self.tagslist = customtkinter.CTkLabel(self.tagsframe, text=f"Tags:")
        # self.tagslist.place(x=10, y=5)

        # # tag frame 1
        # self.tagframe1 = customtkinter.CTkFrame(self.tagsframe, corner_radius=15, width=310, height=30, fg_color="transparent", bg_color="transparent")
        # self.tagframe1.pack_propagate(0)
        # self.tagframe1.place(x=self.tagslist.winfo_reqwidth() + 45, y=5)

        # # tag frame 2
        # self.tagframe2 = customtkinter.CTkFrame(self.tagsframe, corner_radius=15, width=350, height=30, fg_color="transparent")
        # self.tagframe2.pack_propagate(0)
        # self.tagframe2.place(x=5, y=43)

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

        # self.open_listbox()

        if silent_ping_option == "True":
            print("silent ping on")
            self.ping = "silent"
            self.withdraw()
            self.download_button_event()
            return
        else:
            print("silent ping not on")

        # Start the auto-submit timer
        self.start_auto_submit_timer()

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
        # self.minsize(width, height)
        # self.maxsize(width, height)

    def on_enter_pressed_tag(self, event=0):
        self.ping = self.taginput.get()
        if self.ping == "":
            self.run_logviewer()
            # threading.Thread(target=self.run_logviewer, daemon=True).start()
            return
        elif self.ping == "?":
            self.run_settings()
            # threading.Thread(target=self.run_settings, daemon=True).start()
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
        # elif (self.taginput.get()).strip() == self.previoustag.strip():
        #     self.download_button_event()
        #     return
        # elif '(' in self.taginput.get():
        #     self.download_button_event()
        #     return
        
        # if self.swapcount != 1:
        #     # self.swap_frames(self.tagsframe, self.submitframe)
        #     self.swapcount = 1
        # tag = self.taginput.get()
        # self.previoustag = tag
        # self.taglength = len(tag)
        # self.tagnumber += 1
        # if self.tagnumber != 1:
        #     tag = self.get_last_word(tag)
        # self.tagList.append(tag)
        
        # # Measure the width of the tag text in pixels
        # tag_width = self.font.measure(tag)

        # total = tag_width + 25

        # if self.framecount != 2:
        #     # test tag frame
        #     tagcolor = self.config['Settings']['tag_color']
        #     newframe = customtkinter.CTkFrame(self.taginput, corner_radius=15, width=total, height=24, fg_color=tagcolor, border_color=tagcolor, border_width=1)
        #     self.tagArray.append(newframe)
        #     newframe.pack_propagate(0)
        #     if self.tagnumber != 1:
        #         newframe.place(x = self.framelength_total, y = 4)
        #         self.framelength_total += total + 2
        #     else:
        #         newframe.place(x = 5, y = 4)
        #         self.framelength_total += total + 7

        #     # test tag frame text
        #     newtext = customtkinter.CTkLabel(newframe, text=tag, font=self.font, text_color="white")
        #     newtext.pack(pady = 1)

        #     # self.minimize_window(hide=True)
        #     self.tag_format(tag)
        # else:
        #     print("Max tags allowed!")

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
        print(task_tags, " task tags")
        if task_tags != "NULL":
            task_tags_json = json.loads(task_tags)
            print(task_tags_json)
            for item in self.seperated_ping:
                print(item, " item from self.seperated_ping")
                try:
                    if task_tags_json[f"{item}"] != "N/A":
                        original_text = task_tags_json[f"{item}"]
                        seperated_text = re.findall(pattern, original_text)
                        print(seperated_text, " seperated text")
                        index = self.seperated_ping.index(item)
                        counter = 0
                        for new_item in seperated_text:
                            print(new_item, " new_item")
                            if counter == 0:
                                self.seperated_ping[index] = new_item
                            else:
                                self.seperated_ping.insert(index, new_item)
                            index += 1
                            counter += 1
                except Exception as e:
                    print(e)


        self.beeminder_tags = self.seperated_ping[:]
        print(self.beeminder_tags, " BEEMINDER TAGS FROM DOWNLOAD EVENT")
        self.log_entries_to_file()
        self.beeminder_check()
        self.destroy()

    # def add_comment_placeholder(self, placeholder_text):
    #     widget = self.commentinput
    #     # Insert the placeholder text initially
    #     widget.insert("1.0", placeholder_text)
    #     widget.configure(text_color="grey")

    #     def on_focus_in(event):
    #         if widget.get("1.0", "end-1c") == placeholder_text:
    #             widget.delete("1.0", "end")
    #             widget.configure(text_color="white")

    #     def on_focus_out(event):
    #         if widget.get("1.0", "end-1c") == "":
    #             widget.insert("1.0", placeholder_text)
    #             widget.configure(text_color="grey")

    #     widget.bind("<FocusIn>", on_focus_in)
    #     widget.bind("<FocusOut>", on_focus_out)

    def log_entries_to_file(self):
        
        # Define the log file path
        log_file_path = os.path.join(self.script_dir, "log.log")
        
        # Get the current time for the log entry
        now = int(time.time())
        self.beeminder_time = now

        # format tags
        formatted_tags = ' '.join(self.seperated_ping)
        print(formatted_tags, " formatted tags")

        # Get the current time
        current_day = time.localtime()

        # Get the current day
        day = time.strftime("%A", current_day)

        # Get the first three letters of the day in uppercase
        day_abbr = day[:3].upper()

        if len(formatted_tags) > 50:
            new_formatted_tags = (formatted_tags[:len(formatted_tags)]).ljust(len(formatted_tags))
            if len(formatted_tags) < 56:
                print(len(formatted_tags), " len of formatted tags")
                spaces = 55 - len(formatted_tags)
                print(spaces, " spaces")
                current_time = datetime.now().strftime("%m.%d %H:%M:%S")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time} {day_abbr}]\n'
            elif len(formatted_tags) < 60:
                print(len(formatted_tags), " len of formatted tags")
                spaces = 59 - len(formatted_tags)
                print(spaces, " spaces")
                current_time = datetime.now().strftime("%m.%d %H:%M:%S")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            elif len(formatted_tags) < 63:
                print(len(formatted_tags), " len of formatted tags")
                spaces = 62 - len(formatted_tags)
                print(spaces, " spaces")
                current_time = datetime.now().strftime("%m.%d %H:%M")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            elif len(formatted_tags) < 66:
                print(len(formatted_tags), " len of formatted tags")
                spaces = 65 - len(formatted_tags)
                print(spaces, " spaces")
                current_time = datetime.now().strftime("%d %H:%M")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            elif len(formatted_tags) < 69:
                print(len(formatted_tags), " len of formatted tags")
                spaces = 68 - len(formatted_tags)
                print(spaces, " spaces")
                current_time = datetime.now().strftime("%H:%M")
                for i in range(spaces):
                    new_formatted_tags += ' '
                # Format the log entry
                log_entry = f'{now} {new_formatted_tags} [{current_time}]\n'
            elif len(formatted_tags) < 72:
                print(len(formatted_tags), " len of formatted tags")
                spaces = 71 - len(formatted_tags)
                print(spaces, " spaces")
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
            else:
                print("Couldn't Sync to Cloud: Not Signed In")
        except Exception as e:
            print(e)
            print("FAILED TO SYNC TO CLOUD")

    def str_to_bool(self, value):
        return value.lower() in ("yes", "true", "t", "1")
    
    # def open_listbox(self):
    #     self.listboxwindow = customtkinter.CTkToplevel(self.frame)
    #     self.listboxwindow.overrideredirect(True)
    #     self.listboxwindow.attributes("-topmost", True)
    #     self.center_window_listbox(90, 50)

    #     self.listboxframe = customtkinter.CTkFrame(self.listboxwindow, width=90, height = 100)
    #     self.listboxframe.pack_propagate(0)
    #     self.listboxframe.place(x=0, y=0)

    #     self.listbox = CTkListbox(self.listboxframe, width=80, height=100, scrollbar_button_color="red", border_color="black", border_width=0)
    #     self.listbox.place(x=0,y=0)
    #     self.listboxframe.place(x=0, y=0)
    #     self.listboxwindow.withdraw()

    # def center_window_listbox(self, width=400, height=490):
    #     # Get the main window position
    #     main_window_x = self.winfo_x()
    #     main_window_y = self.winfo_y()

    #     # Get the main window dimensions
    #     main_window_width = self.winfo_width()
    #     main_window_height = self.winfo_height()

    #     # Calculate the position for the listbox window to be centered within the main window
    #     x = main_window_x + (main_window_width - width) // 2
    #     y = main_window_y + (main_window_height - self.listboxwindow.winfo_height()) // 2

    #     # Set the geometry of the listbox window
    #     self.listboxwindow.geometry(f'{width}x{height}+{x-125}+{y+60}')
    #     # self.minsize(width, height)
    #     # self.maxsize(width, height)

    # def start_move(self, event, window):
    #         window.x = event.x
    #         window.y = event.y

    # def on_move(self, event, window):
    #     x = event.x_root - window.x
    #     y = event.y_root - window.y
    #     window.geometry(f"+{x}+{y}")
    #     if self.is_listbox_window_open():
    #         self.listboxwindow.geometry(f"+{x + 30}+{y + 90}")
    #     else:
    #         pass

    # def minimize_window(self, hide=False):
    #         print("minimizing window")
    #         hwnd = windll.user32.GetParent(self.listboxwindow.winfo_id())
    #         windll.user32.ShowWindow(hwnd, 0 if hide else 6)

    # def minimize_main_window(self, hide=False):
    #         print("minimizing window")
    #         hwnd = windll.user32.GetParent(self.winfo_id())
    #         windll.user32.ShowWindow(hwnd, 0 if hide else 6)

    # def get_position(self):
    #     x = self.winfo_x()
    #     y = self.winfo_y()
    #     # print(f"Window position: x={x}, y={y}")

    # def is_listbox_window_open(self):
    #     if self.listboxwindow is not None:
    #         return self.listboxwindow.state() == "normal"
    #     return False
    
    # def on_down_key(self, event):
    #     print("hello")
    #     self.listbox.activate(0)

    # def on_tab_key(self, event):
    #     print("hello")
    #     self.listbox.activate(0)

    # def on_listbox_click(self, event):
        # Inserts the selected suggestion into the entry.
        # self.taginput.delete(0, customtkinter.END)
        # self.taginput.insert(0, self.listbox.get())
        # self.minimize_window(hide=True)
        # self.on_enter_pressed_tag(event)

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
        print(index)
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
        with open(os.path.join(self.script_dir, 'config.ini'), 'w') as configfile:
            self.config.write(configfile)

    def on_space_pressed_tag(self, event):
        tag = self.taginput.get()
        cursor_position = self.taginput.index("insert")
        current_text = self.taginput.get()[:cursor_position]

        if '(' in current_text:
            print("currently a comment.")
        else:
            # Remove the last character (space) from the entry
            current_text = self.taginput.get()
            if current_text.endswith(' '):
                print("ends in space")
                self.taginput.delete(len(current_text)-1, len(current_text))
            self.on_enter_pressed_tag(event)

    def on_comma_pressed_tag(self, event):
        tag = self.taginput.get()
        cursor_position = self.taginput.index("insert")
        current_text = self.taginput.get()[:cursor_position]

        if '(' in current_text:
            print("currently a comment.")
        else:
            # Remove the last character (comma) from the entry
            current_text = self.taginput.get()
            if current_text.endswith(','):
                self.taginput.delete(len(current_text)-1, len(current_text))
            self.on_enter_pressed_tag(event)

    def run_settings(self):
        settings.SettingsWindow(self.parent)
        # try:
        #     # Start the process without waiting for it to complete
        #     subprocess.Popen(['python', os.path.join(self.script_dir, 'settings.py')])

        # except Exception as e:
        #     print(f"An error occurred: {e}")

    def run_logviewer(self):
        logviewer.LogViewerWindow(self.parent)
        # try:
        #     # Start the process without waiting for it to complete
        #     subprocess.Popen(['python', os.path.join(self.script_dir, 'logviewer.py')])

        # except Exception as e:
        #     print(f"An error occurred: {e}")

    def update_cloud_log(self, file_path):
        new_url = "https://hello-bgfsl5zz5q-uc.a.run.app/update_cloud_log"
        refresh_token = self.config['Cloud']['refresh_token']

        with open(file_path, 'r') as file:
            log_content = file.read()

        update_response = requests.post(
            new_url,
            json={
                'refresh_token': refresh_token,
                'file_name': os.path.basename(file_path),
                'file_content': log_content
            }
        )

        if update_response.status_code == 200:
            update_data = update_response.json()
            print("Success:", update_data['message'])
        else:
            print("Error in updating cloud log:", update_response.json())

    def copy_tags_from_last_log_entry(self):
        log_file_path = os.path.join(self.script_dir, "log.log")

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
                    print(tag, " has a comment!")
                    pass
                else:
                    for key, value in goal_tags_json.items():
                        for item in value.split(","):
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
            print(content)
            return content
        else:
            print("No parentheses found")
            content = ''
            return content
        
    def on_closing(self):
        self.ping = "err"
        self.download_button_event()
        
def main(parent):
    PromptWindow(parent)
 
if __name__ == "__main__":
    # main()
    root = customtkinter.CTk()  # Create the main window
    root.withdraw()  # Hide the main window since we are only using Toplevels
    main(root)
    root.mainloop()
