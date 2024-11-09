import os
import customtkinter
from tkinter import filedialog
import re
from datetime import datetime
import configparser
import requests
from plyer import notification
import time
import json
import beeminder
import platform

class LogViewerWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        # Get the directory of the current script
        self.script_dir = os.path.dirname(os.path.realpath(__file__))

        # set paths
        self.img_path = os.path.join(self.script_dir, "img")
        self.log_menu()

    def log_menu(self):
                
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(self.script_dir, 'config.ini'))
        self.appearance_mode = self.config['Settings']['appearance_mode']
        
        customtkinter.set_appearance_mode(self.appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
        customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue")

        self.title("Log Viewer/Editor")
        self.center_window(900, 750)
        self.font = customtkinter.CTkFont(family="Helvetica", size=12)
        if platform.system() == 'Darwin':
            self.wm_iconbitmap()
        else:
            self.after(250, lambda: self.iconbitmap(os.path.join(self.img_path, 'tagtime.ico')))
        # self.iconbitmap(os.path.join(self.img_path, 'tagtime.ico'))

        self.attributes("-topmost", True)
        self.after(1000, lambda: self.attributes("-topmost", False))  # Disable topmost after 1 second

        # self.logwindow.deiconify()
        # self.minimize_window()

        # configure frame
        self.logframe = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.logframe.pack(fill="both", expand=True)

        # top frame
        self.topframe = customtkinter.CTkFrame(master=self.logframe, corner_radius=0, height=40, fg_color="transparent", width=850)
        self.topframe.pack_propagate(0)
        self.topframe.pack(pady=5)

        # # Export Log from Cloud text
        # self.cloudlog_text = customtkinter.CTkLabel(self.topframe, text="Export Log From Cloud: ")
        # self.cloudlog_text.pack(pady=10, side="left")

        # Export Log from Cloud Button
        self.importlog_button = customtkinter.CTkButton(self.topframe, text="Import Log to Cloud", width=70, command=self.on_import_log, corner_radius=0,
                                                        fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.importlog_button.pack(side="left", padx=5)

        # Export Log from Cloud Button
        self.cloudlog_button = customtkinter.CTkButton(self.topframe, text="Export Log From Cloud", width=70, command=self.on_export_log, corner_radius=0,
                                                        fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.cloudlog_button.pack(side="left", padx=5)

        # sort by combo box
        self.sortbybox = customtkinter.CTkOptionMenu(self.topframe, width=125, height=25, values=["Most Recent", "Least Recent"], command=self.on_recent_selection, text_color=["black", "white"],
                                                        fg_color=["white", "grey22"], bg_color="transparent", button_color=["grey70", "grey26"], corner_radius=0, button_hover_color="grey35")
        self.sortbybox.pack(side="right")

        self.previous_option = self.sortbybox.get()

        # sort by text
        self.sortbytext = customtkinter.CTkLabel(self.topframe, text="Sort By: ")
        self.sortbytext.pack(pady=10, padx=(10, 0), side="right")

        # grab tags from config
        self.alltags = (self.config['Tags']['tags']).split(',')
        self.alltags.sort()

        # tags combo box
        self.tagscombobox = customtkinter.CTkComboBox(self.topframe, width=125, height=25, values=self.alltags, command=self.on_search_tag, 
                                                        border_width=0, corner_radius=0, fg_color=["white", "grey22"], button_color=["grey70", "grey26"], button_hover_color="grey35", bg_color="transparent")
        self.tagscombobox.set("")
        self.tagscombobox.pack(side="right")
        self.tagscombobox.bind("<Return>", self.on_tagscombobox_enter)

        self.previous_tag = self.tagscombobox.get()
        self.on_tag_flag = False
        self.tag_graph_list = []

        # tags text
        self.tagstext = customtkinter.CTkLabel(self.topframe, text="Search Tag(s): ")
        self.tagstext.pack(pady=10, side="right")

        # Replace Tags Button
        self.replacetags_button = customtkinter.CTkButton(self.topframe, text="Replace Tags", width=90, command=self.on_replace_tag_button, corner_radius=0,
                                                        fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.replacetags_button.pack(side="right", padx=10)

        # frame for headers
        self.headersframe = customtkinter.CTkFrame(master=self.logframe, fg_color="transparent", height=30, width=800, corner_radius=0)
        self.headersframe.pack(fill="y")

        # second frame for headers
        self.headers1frame = customtkinter.CTkFrame(master=self.headersframe, fg_color="transparent", height=30, width=823, corner_radius=0, bg_color="transparent", border_color="black", border_width=0)
        self.headers1frame.pack_propagate(0)
        self.headers1frame.pack(fill="y")

        # fifth frame for headers
        self.headers4frame = customtkinter.CTkFrame(master=self.headers1frame, fg_color="transparent", height=30, width=215, corner_radius=0, border_color="black", border_width=0)
        self.headers4frame.pack_propagate(0)
        self.headers4frame.pack(fill="y", side="left")

        # third frame for headers
        self.headers2frame = customtkinter.CTkFrame(master=self.headers1frame, fg_color="transparent", height=30, width=580, corner_radius=0, border_color="black", border_width=0)
        self.headers2frame.pack_propagate(0)
        self.headers2frame.pack(fill="y", side="left")

        # text for third section
        self.thirdheadertext = customtkinter.CTkLabel(self.headers4frame, text="Date/Time", font=("Helvetica", 18))
        self.thirdheadertext.pack(pady=3)

        # text for first section
        self.firstheadertext = customtkinter.CTkLabel(self.headers2frame, text="Tag(s)", font=("Helvetica", 18))
        self.firstheadertext.pack(pady=3)

        # results frame
        self.resultsframe = customtkinter.CTkScrollableFrame(master=self.logframe, width=800, height=600)
        self.resultsframe.pack()

        self.log_file_path = os.path.join(self.script_dir, 'log.log')
        self.fillgraph = self.process_log_file()
        self.fillgraph.reverse()
        self.is_reversed = True

        self.display_fillgraph()

        # Save Log Frame
        self.savelog_frame = customtkinter.CTkFrame(self.logframe, fg_color="transparent", corner_radius=0)
        self.savelog_frame.pack(fill="x")

        # Save Log Button
        self.savelog_button = customtkinter.CTkButton(self.savelog_frame, text="Save Log", width=100, height=35, font=("Helvetica", 18), command=self.on_save_log_button, corner_radius=0,
                                                        fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.savelog_button.pack(pady=10, padx=39, side="right")

    def center_window(self, width=610, height=740):
        # Get the screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate the position for the window to be centered
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Set the geometry of the window
        self.geometry(f'{width}x{height}+{x}+{y}')

    def center_window_replace(self, width=610, height=740):
        # Get the screen width and height
        screen_width = self.replace_window.winfo_screenwidth()
        screen_height = self.replace_window.winfo_screenheight()

        # Calculate the position for the window to be centered
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Set the geometry of the window
        self.replace_window.geometry(f'{width}x{height}+{x}+{y}')
        self.replace_window.minsize(width, height)
        self.replace_window.maxsize(width, height)

    def on_recent_selection(self, option):
        if option == "Most Recent" and self.previous_option == "Least Recent":
            self.fillgraph.reverse()
            self.is_reversed = True

            # Destroy all widgets inside the resultsframe
            for widget in self.resultsframe.winfo_children():
                widget.destroy()

            self.tagscombobox.set("")
            self.display_fillgraph()
            self.previous_option = option
            self.on_tag_flag = False
            self.tag_graph_list = []
        elif option == "Least Recent" and self.previous_option == "Most Recent":
            self.fillgraph.reverse()
            self.is_reversed = False

            # Destroy all widgets inside the resultsframe
            for widget in self.resultsframe.winfo_children():
                widget.destroy()

            self.tagscombobox.set("")
            self.display_fillgraph()
            self.previous_option = option
            self.on_tag_flag = False
            self.tag_graph_list = []

    def process_log_file(self):
        # Regular expression to match the parts of the log entry
        pattern = re.compile(
            r'^(\d+)\s+'  # Match the Unix timestamp at the beginning
            r'([^\[\]]+?)\s*'  # Match everything between the timestamp and square brackets (non-greedy)
            r'(?:\[(.*?)\])?'  # Optional square brackets with content inside
        )

        results = []

        updated = False
        new_tags = []
        current_tags = []

        # Open and read the log file
        with open(self.log_file_path, 'r') as file:

            for line in file:
                # Extract parts using the regular expression
                match = re.match(r'(\d+)\s+(.*?)(\s*\[.*\])?$', line)
                if match:
                    unix_timestamp = int(match.group(1))  # Unix timestamp
                    words_str = match.group(2).strip()  # Everything between timestamp and brackets
                    if '[' in words_str or ']' in words_str:
                        words_str = re.sub(r'\[.*?\]', '', words_str).strip()
                    time_str = match.group(3).strip() if match.group(3) else ''
                    # print(unix_timestamp)
                    # print(words_str)
                    # print(time_str)

                    # Split the words into a list
                    words_list = re.findall(r'\(.*?\)|\S+', words_str)

                    # Process the tags
                    for tag in words_list:
                        if '(' in tag or ')' in tag:
                            pass
                        else:
                            if tag not in current_tags:
                                current_tags.append(tag)
                            if tag not in self.alltags:
                                updated = True
                                self.alltags.append(tag)
                                new_tags.append(tag)

                    # Convert the timestamp to a datetime object
                    dt_object = datetime.fromtimestamp(unix_timestamp)

                    # Format the datetime object to the desired format for date and time
                    current_time = dt_object.strftime("%Y.%m.%d %H:%M:%S")

                    # Get the current day from the timestamp
                    current_day = time.localtime(unix_timestamp)

                    # Get the full name of the day
                    day = time.strftime("%A", current_day)

                    # Get the first three letters of the day in uppercase
                    day_abbr = day[:3].upper()

                    # Combine the formatted date and time with the day abbreviation
                    formatted_output = f"{current_time} {day_abbr}"        

                    # Store the extracted information in a dictionary
                    result = {
                        'words_list': words_str,
                        'time': formatted_output,
                        'unix': unix_timestamp
                    }
                    results.append(result)
                else:
                    print(f"Log entry format is incorrect: {line.strip()}")

        if updated:
            self.alltags.sort()
            for item in new_tags:
                if self.config['Tags']['tags'] == 'NULL':
                    self.config['Tags']['tags'] = item
                else:
                    self.config['Tags']['tags'] += ("," + item)
                self.on_config_save()
            self.tagscombobox.configure(values=self.alltags)
            self.tagscombobox.set("")

        sorted_tags = sorted(current_tags)
        self.config['Tags']['tags'] = ','.join(sorted_tags)
        self.alltags = sorted_tags
        self.on_config_save()
        self.tagscombobox.configure(values=self.alltags)

        return results
    
    def display_fillgraph(self):
        count = 0
        self.add100count = 0
        self.entries = []
        if self.appearance_mode == "Dark":
            new_fg_color = "transparent"
        elif self.appearance_mode == "Light":
            new_fg_color = "white"
        else:
            new_fg_color = "transparent"
            
        for item in self.fillgraph:

            if count <= 99:
                # result box
                resultbox = customtkinter.CTkFrame(self.resultsframe, corner_radius=0, height=75)
                resultbox.pack_propagate(0)
                resultbox.pack(fill="both")

                resultgrid3 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=200, fg_color=new_fg_color)
                resultgrid3.pack_propagate(0)
                resultgrid3.pack(fill="y", side="left")

                resultgrid1border = customtkinter.CTkFrame(resultbox, fg_color=["grey90", "black"], corner_radius=0, width=6)
                resultgrid1border.pack_propagate(0)
                resultgrid1border.pack(fill="y", side="left")

                resultgrid1 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=600, fg_color=new_fg_color)
                resultgrid1.pack_propagate(0)
                resultgrid1.pack(fill="y", side="left")

                count += 1

                resultgrid1_textbox = customtkinter.CTkEntry(resultgrid1, fg_color="transparent", border_width=0, font=("Helvetica", 20), height=90, width=600, corner_radius=0)
                resultgrid1_textbox.pack_propagate(0)
                resultgrid1_textbox.insert(0, item["words_list"])
                resultgrid1_textbox.bind('<Shift-Down>', self.on_shift_down)
                resultgrid1_textbox.bind('<Shift-Up>', self.on_shift_up)
                resultgrid1_textbox.bind('<Down>', self.on_down)
                resultgrid1_textbox.bind('<Up>', self.on_up)
                resultgrid1_textbox.pack(pady=0)
                self.entries.append(resultgrid1_textbox)

                # result box divider
                resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color=["grey90", "black"], corner_radius=0, height=6)
                resultboxdivider.pack_propagate(0)
                resultboxdivider.pack(fill="x")

                new_time = self.format_time(item["time"], item["unix"])

                # time label
                time = customtkinter.CTkLabel(resultgrid3, text=new_time, font=("Helvetica", 20))
                time.pack(pady=15)
            else:
                print("100 tags reached")

                # add 100 more frame
                self.add100box = customtkinter.CTkButton(self.resultsframe, corner_radius=0, height=40, fg_color="transparent", text="Next 100 Tags", command=self.on_next100_button, font=("Helvetica", 20),
                                                                                                                                            text_color=["black", "white"], hover_color=["grey98", "grey35"])
                self.add100box.pack_propagate(0)
                self.add100box.pack(fill="both")

                count = 0
                break

    def display_100more(self):
        count = 0
        self.entries = []
        if self.appearance_mode == "Dark":
            new_fg_color = "transparent"
        elif self.appearance_mode == "Light":
            new_fg_color = "white"
        else:
            new_fg_color = "transparent"

        # add 100 more frame
        self.prev100box = customtkinter.CTkButton(self.resultsframe, corner_radius=0, height=40, fg_color="transparent", text="Previous 100 Tags", command=self.on_prev100_button, font=("Helvetica", 20),
                                                                                                                                            text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.prev100box.pack_propagate(0)
        self.prev100box.pack(fill="both")

        # result box divider
        resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color=["grey90", "black"], corner_radius=0, height=6)
        resultboxdivider.pack_propagate(0)
        resultboxdivider.pack(fill="x")
            
        for item in self.fillgraph[self.add100count:]:

            if count <= 99:
                # result box
                resultbox = customtkinter.CTkFrame(self.resultsframe, corner_radius=0, height=75)
                resultbox.pack_propagate(0)
                resultbox.pack(fill="both")

                resultgrid3 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=200, fg_color=new_fg_color)
                resultgrid3.pack_propagate(0)
                resultgrid3.pack(fill="y", side="left")

                resultgrid1border = customtkinter.CTkFrame(resultbox, fg_color=["grey90", "black"], corner_radius=0, width=6)
                resultgrid1border.pack_propagate(0)
                resultgrid1border.pack(fill="y", side="left")

                resultgrid1 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=600, fg_color=new_fg_color)
                resultgrid1.pack_propagate(0)
                resultgrid1.pack(fill="y", side="left")

                count += 1

                resultgrid1_textbox = customtkinter.CTkEntry(resultgrid1, fg_color="transparent", border_width=0, font=("Helvetica", 20), height=90, width=600, corner_radius=0)
                resultgrid1_textbox.pack_propagate(0)
                resultgrid1_textbox.insert(0, item["words_list"])
                resultgrid1_textbox.bind('<Shift-Down>', self.on_shift_down)
                resultgrid1_textbox.bind('<Shift-Up>', self.on_shift_up)
                resultgrid1_textbox.bind('<Down>', self.on_down)
                resultgrid1_textbox.bind('<Up>', self.on_up)
                resultgrid1_textbox.pack(pady=0)
                self.entries.append(resultgrid1_textbox)

                # result box divider
                resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color=["grey90", "black"], corner_radius=0, height=6)
                resultboxdivider.pack_propagate(0)
                resultboxdivider.pack(fill="x")

                new_time = self.format_time(item["time"], item["unix"])

                # time label
                time = customtkinter.CTkLabel(resultgrid3, text=new_time, font=("Helvetica", 20))
                time.pack(pady=15)
            else:
                print("100 tags reached")

                # add 100 more frame
                self.add100box = customtkinter.CTkButton(self.resultsframe, corner_radius=0, height=40, fg_color="transparent", text="Next 100 Tags", command=self.on_next100_button, font=("Helvetica", 20),
                                                                                                                                            text_color=["black", "white"], hover_color=["grey98", "grey35"])
                self.add100box.pack_propagate(0)
                self.add100box.pack(fill="both")

                count = 0
                break

    def display_taggraph(self, tag):
        count = 0
        self.add100count = 0
        self.tag_graph_index = 0
        self.previous_tag_index = 0
        self.previous_tag_list = []
        self.sortedtag = tag
        self.tag_graph_list = []
        self.entries = []
        if self.appearance_mode == "Dark":
            new_fg_color = "transparent"
        elif self.appearance_mode == "Light":
            new_fg_color = "white"
        else:
            new_fg_color = "transparent"

        for item in self.fillgraph:

            if count <= 99:

                all_words = re.findall(r'\(.*?\)|\S+', item['words_list'])
                for words in all_words:
                    if '(' in words or ')' in words:
                        pass
                    else:
                        if tag == words:
                            # result box
                            resultbox = customtkinter.CTkFrame(self.resultsframe, corner_radius=0, height=75)
                            resultbox.pack_propagate(0)
                            resultbox.pack(fill="both")

                            resultgrid3 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=200, fg_color=new_fg_color)
                            resultgrid3.pack_propagate(0)
                            resultgrid3.pack(fill="y", side="left")

                            resultgrid1border = customtkinter.CTkFrame(resultbox, fg_color=["grey90", "black"], corner_radius=0, width=6)
                            resultgrid1border.pack_propagate(0)
                            resultgrid1border.pack(fill="y", side="left")

                            resultgrid1 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=600, fg_color=new_fg_color)
                            resultgrid1.pack_propagate(0)
                            resultgrid1.pack(fill="y", side="left")

                            count += 1
                            self.tag_graph_list.append(self.tag_graph_index)

                            resultgrid1_textbox = customtkinter.CTkEntry(resultgrid1, fg_color="transparent", border_width=0, font=("Helvetica", 20), height=90, width=600, corner_radius=0)
                            resultgrid1_textbox.pack_propagate(0)
                            resultgrid1_textbox.insert(0, item["words_list"])
                            resultgrid1_textbox.bind('<Shift-Down>', self.on_shift_down)
                            resultgrid1_textbox.bind('<Shift-Up>', self.on_shift_up)
                            resultgrid1_textbox.bind('<Down>', self.on_down)
                            resultgrid1_textbox.bind('<Up>', self.on_up)
                            resultgrid1_textbox.pack(pady=0)
                            self.entries.append(resultgrid1_textbox)

                            # result box divider
                            resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color=["grey90", "black"], corner_radius=0, height=6)
                            resultboxdivider.pack_propagate(0)
                            resultboxdivider.pack(fill="x")

                            new_time = self.format_time(item["time"], item["unix"])

                            # time label
                            time = customtkinter.CTkLabel(resultgrid3, text=new_time, font=("Helvetica", 20))
                            time.pack(pady=15)
                            break

                self.tag_graph_index += 1

            else:
                print("100 tags reached")

                # add 100 more frame
                self.add100box = customtkinter.CTkButton(self.resultsframe, corner_radius=0, height=40, fg_color="transparent", text="Next 100 Tags", command=self.on_next100sortedtags_button, font=("Helvetica", 20),
                                                                                                                                            text_color=["black", "white"], hover_color=["grey98", "grey35"])
                self.add100box.pack_propagate(0)
                self.add100box.pack(fill="both")

                count = 0
                print(self.tag_graph_index)
                break

    def display_100more_taggraph(self, tag):
        count = 0
        self.entries = []
        if self.appearance_mode == "Dark":
            new_fg_color = "transparent"
        elif self.appearance_mode == "Light":
            new_fg_color = "white"
        else:
            new_fg_color = "transparent"

        # add 100 more frame
        self.prev100box = customtkinter.CTkButton(self.resultsframe, corner_radius=0, height=40, fg_color="transparent", text="Previous 100 Tags", command=self.on_prev100sortedtags_button, font=("Helvetica", 20),
                                                                                                                                            text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.prev100box.pack_propagate(0)
        self.prev100box.pack(fill="both")

        # result box divider
        resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color=["grey90", "black"], corner_radius=0, height=6)
        resultboxdivider.pack_propagate(0)
        resultboxdivider.pack(fill="x")

        for item in self.fillgraph[self.previous_tag_index:]:

            if count <= 99:

                all_words = re.findall(r'\(.*?\)|\S+', item['words_list'])
                for words in all_words:
                    if '(' in words or ')' in words:
                        pass
                    else:
                        if tag == words:
                            # result box
                            resultbox = customtkinter.CTkFrame(self.resultsframe, corner_radius=0, height=75)
                            resultbox.pack_propagate(0)
                            resultbox.pack(fill="both")

                            resultgrid3 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=200, fg_color=new_fg_color)
                            resultgrid3.pack_propagate(0)
                            resultgrid3.pack(fill="y", side="left")

                            resultgrid1border = customtkinter.CTkFrame(resultbox, fg_color=["grey90", "black"], corner_radius=0, width=6)
                            resultgrid1border.pack_propagate(0)
                            resultgrid1border.pack(fill="y", side="left")

                            resultgrid1 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=600, fg_color=new_fg_color)
                            resultgrid1.pack_propagate(0)
                            resultgrid1.pack(fill="y", side="left")

                            count += 1
                            self.tag_graph_list.append(self.tag_graph_index)

                            resultgrid1_textbox = customtkinter.CTkEntry(resultgrid1, fg_color="transparent", border_width=0, font=("Helvetica", 20), height=90, width=600, corner_radius=0)
                            resultgrid1_textbox.pack_propagate(0)
                            resultgrid1_textbox.insert(0, item["words_list"])
                            resultgrid1_textbox.bind('<Shift-Down>', self.on_shift_down)
                            resultgrid1_textbox.bind('<Shift-Up>', self.on_shift_up)
                            resultgrid1_textbox.bind('<Down>', self.on_down)
                            resultgrid1_textbox.bind('<Up>', self.on_up)
                            resultgrid1_textbox.pack(pady=0)
                            self.entries.append(resultgrid1_textbox)

                            # result box divider
                            resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color=["grey90", "black"], corner_radius=0, height=6)
                            resultboxdivider.pack_propagate(0)
                            resultboxdivider.pack(fill="x")

                            new_time = self.format_time(item["time"], item["unix"])

                            # time label
                            time = customtkinter.CTkLabel(resultgrid3, text=new_time, font=("Helvetica", 20))
                            time.pack(pady=15)
                            break

                self.tag_graph_index += 1

            else:
                print("100 tags reached")

                # add 100 more frame
                self.add100box = customtkinter.CTkButton(self.resultsframe, corner_radius=0, height=40, fg_color="transparent", text="Next 100 Tags", command=self.on_next100sortedtags_button, font=("Helvetica", 20),
                                                                                                                                            text_color=["black", "white"], hover_color=["grey98", "grey35"])
                self.add100box.pack_propagate(0)
                self.add100box.pack(fill="both")

                count = 0
                break

    def format_time(self, time_str, unix):
        # Remove the weekday part
        time_str = ' '.join(time_str.split()[:-1])
        
        # Parse the original time string without the weekday
        try:
            parsed_time = datetime.strptime(time_str, "%Y.%m.%d %H:%M:%S")
        except ValueError as e:
            print(e)
            # Convert the timestamp to a datetime object
            dt_object = datetime.fromtimestamp(int(unix))

            # Format the datetime object to the desired format for date and time
            current_time = dt_object.strftime("%Y.%m.%d %H:%M:%S")

            parsed_time = datetime.strptime(current_time, "%Y.%m.%d %H:%M:%S")
        
        # Get the day of the month
        day = parsed_time.day

        # Determine the appropriate ordinal suffix
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

        # Format the parsed time into the desired format
        formatted_time = parsed_time.strftime(f"%B {day}{suffix}, %Y\n%H:%M:%S")
        return formatted_time
    
    def on_save_log_button(self):
        self.editorcount = 0

        if self.add100count != 0:
            self.editorcount += self.add100count

        self.updated_tags = []

        if self.on_tag_flag:
            self.loop_through_tag_widgets(self.resultsframe)
        else:
            self.loop_through_widgets(self.resultsframe)

        if self.updated_tags:
            self.beeminder_check()

        self.save_edited_log()
        self.display_alert()
        self.sync_cloud_log()

    def loop_through_tag_widgets(self, frame):
        # Get all child widgets of resultbox
        for widget in frame.winfo_children():
            if isinstance(widget, customtkinter.CTkEntry):
                # Example: Print the text of CTkEntry widgets
                newtext = widget.get()

                tag_index = self.tag_graph_list[self.editorcount]

                if self.fillgraph[tag_index]['words_list'] == newtext:
                    pass
                else:
                    old_words = self.fillgraph[tag_index]['words_list']
                    self.fillgraph[tag_index]['words_list'] = newtext
                    new_words = self.fillgraph[tag_index]['words_list']
                    weekly_border = int(time.time()) - 604800
                    if self.fillgraph[self.editorcount]['unix'] < weekly_border:
                        print("LOG IS OLDER THAN 7 DAYS")
                        pass
                    else:
                        print("WITHIN 7 DAYS! GOOD TO GO!")
                        result = {
                            'old_words': old_words,
                            'new_words': new_words,
                            'unix': self.fillgraph[self.editorcount]['unix']
                        }
                        self.updated_tags.append(result)
                self.editorcount += 1
            elif isinstance(widget, customtkinter.CTkFrame):
                self.loop_through_tag_widgets(widget)

        # for i in range (len(self.fillgraph)):
        #     print(self.fillgraph[i])

    def loop_through_widgets(self, frame):
        # Get all child widgets of resultbox
        for widget in frame.winfo_children():
            if isinstance(widget, customtkinter.CTkEntry):
                # Example: Print the text of CTkEntry widgets
                newtext = widget.get()

                if self.fillgraph[self.editorcount]['words_list'] == newtext:
                    pass
                else:
                    old_words = self.fillgraph[self.editorcount]['words_list']
                    self.fillgraph[self.editorcount]['words_list'] = newtext
                    new_words = self.fillgraph[self.editorcount]['words_list']
                    weekly_border = int(time.time()) - 604800
                    if self.fillgraph[self.editorcount]['unix'] < weekly_border:
                        print("LOG IS OLDER THAN 7 DAYS")
                        pass
                    else:
                        print("WITHIN 7 DAYS! GOOD TO GO!")
                        result = {
                            'old_words': old_words,
                            'new_words': new_words,
                            'unix': self.fillgraph[self.editorcount]['unix']
                        }
                        self.updated_tags.append(result)
                    print(self.editorcount)
                self.editorcount += 1
            elif isinstance(widget, customtkinter.CTkFrame):
                self.loop_through_widgets(widget)

        # for i in range (len(self.fillgraph)):
        #     print(self.fillgraph[i])

    def save_edited_log(self):
        if self.is_reversed:
            self.fillgraph.reverse()

        updated_lines = []

        for item in self.fillgraph:
            tags = item['words_list']
            # Define the format of the date-time string
            date_time_str = item['time']
            day_abbr = date_time_str[-3:]
            unix_timestamp = int(item['unix'])



            # date_format = '%Y.%m.%d %H:%M:%S %a'

            # cleaned_date_time_str = date_time_str.split(';')[0].strip()

            # # Parse the date-time string into a datetime object
            # try:
            #     dt = datetime.strptime(cleaned_date_time_str, date_format)
            # except ValueError as e:
            #     print(e)
            #     print("BAD BAD")
            #     # Convert the timestamp to a datetime object
            #     dt_object = datetime.fromtimestamp(unix_time)

            #     # Format the datetime object to the desired format for date and time
            #     current_time = dt_object.strftime("%Y.%m.%d %H:%M:%S")

            #     # Get the current day from the timestamp
            #     current_day = time.localtime(unix_time)

            #     # Get the full name of the day
            #     day = time.strftime("%A", current_day)

            #     # Get the first three letters of the day in uppercase
            #     day_abbr = day[:3].upper()

            #     # Combine the formatted date and time with the day abbreviation
            #     formatted_output = f"{current_time} {day_abbr}"
            #     dt = datetime.strptime(formatted_output, date_format)
            #     date_time_str = formatted_output


            # # Convert the datetime object to a Unix timestamp
            # unix_timestamp = int(dt.timestamp())



            
            # if len(tags) > 50:
            #     new_formatted_tags = (tags[:len(tags)]).ljust(len(tags))
            # else:
            #     new_formatted_tags = (tags[:50]).ljust(50)

            # log_entry = f'{unix_timestamp} {new_formatted_tags} [{date_time_str}]\n'


            if len(tags) > 50:
                new_formatted_tags = (tags[:len(tags)]).ljust(len(tags))
                if len(tags) < 56:
                    spaces = 55 - len(tags)
                    date_time_obj = datetime.fromtimestamp(unix_timestamp)
                    current_time = date_time_obj.strftime("%m.%d %H:%M:%S")
                    for i in range(spaces):
                        new_formatted_tags += ' '
                    # Format the log entry
                    log_entry = f'{unix_timestamp} {new_formatted_tags} [{current_time} {day_abbr}]\n'
                elif len(tags) < 60:
                    spaces = 59 - len(tags)
                    date_time_obj = datetime.fromtimestamp(unix_timestamp)
                    current_time = date_time_obj.strftime("%m.%d %H:%M:%S")
                    for i in range(spaces):
                        new_formatted_tags += ' '
                    # Format the log entry
                    log_entry = f'{unix_timestamp} {new_formatted_tags} [{current_time}]\n'
                elif len(tags) < 63:
                    spaces = 62 - len(tags)
                    date_time_obj = datetime.fromtimestamp(unix_timestamp)
                    current_time = date_time_obj.strftime("%m.%d %H:%M")
                    for i in range(spaces):
                        new_formatted_tags += ' '
                    # Format the log entry
                    log_entry = f'{unix_timestamp} {new_formatted_tags} [{current_time}]\n'
                elif len(tags) < 66:
                    spaces = 65 - len(tags)
                    date_time_obj = datetime.fromtimestamp(unix_timestamp)
                    current_time = date_time_obj.strftime("%d %H:%M")
                    for i in range(spaces):
                        new_formatted_tags += ' '
                    # Format the log entry
                    log_entry = f'{unix_timestamp} {new_formatted_tags} [{current_time}]\n'
                elif len(tags) < 69:
                    spaces = 68 - len(tags)
                    date_time_obj = datetime.fromtimestamp(unix_timestamp)
                    current_time = date_time_obj.strftime("%H:%M")
                    for i in range(spaces):
                        new_formatted_tags += ' '
                    # Format the log entry
                    log_entry = f'{unix_timestamp} {new_formatted_tags} [{current_time}]\n'
                elif len(tags) < 72:
                    spaces = 71 - len(tags)
                    date_time_obj = datetime.fromtimestamp(unix_timestamp)
                    current_time = date_time_obj.strftime("%M")
                    for i in range(spaces):
                        new_formatted_tags += ' '
                    # Format the log entry
                    log_entry = f'{unix_timestamp} {new_formatted_tags} [{current_time}]\n'
                else:
                    date_time_obj = datetime.fromtimestamp(unix_timestamp)
                    current_time = date_time_obj.strftime("%m.%d %H:%M:%S")
                    # Format the log entry
                    log_entry = f'{unix_timestamp} {new_formatted_tags}\n'

            else:
                new_formatted_tags = (tags[:50]).ljust(50)
                date_time_obj = datetime.fromtimestamp(unix_timestamp)
                current_time = date_time_obj.strftime("%Y.%m.%d %H:%M:%S")
                log_entry = f'{unix_timestamp} {new_formatted_tags} [{current_time} {day_abbr}]\n'


            updated_lines.append(log_entry)

        # Write all updated lines to the log file, overwriting the existing file
        with open(self.log_file_path, "w") as log_file:
            log_file.writelines(updated_lines)

        if self.is_reversed:
            self.fillgraph.reverse()

    def display_alert(self):
        self.show_info_message("Log Saved!", "The updated log has now been saved.")

    def on_import_log(self):
        refresh_token = self.config['Cloud']['refresh_token']
        if refresh_token == "NULL":
            self.show_info_message("Error", "Currently not signed in to Google.")
            return
        
        # Prompt the user to select a file to import
        file_path = filedialog.askopenfilename(
            title="Select Log File to Import",
            filetypes=[("Log Files", "*.log"), ("All Files", "*.*")]
        )

        if not file_path:
            print("Import operation was canceled.")
            return
        
        try:
            # Read the selected file's content
            with open(file_path, "r") as file:
                file_contents = file.read()

            # print(f"Selected file content: {file_contents}")

            # Replace the cloud log with the imported content
            url = "https://hello-bgfsl5zz5q-uc.a.run.app/import_cloud_log"
            update_response = requests.post(
                url,
                json={
                    'refresh_token': refresh_token,
                    'file_name': "log.log",  # The cloud log file name
                    'file_content': file_contents
                }
            )

            if update_response.status_code == 200:
                print("Success: Replaced cloud log with imported file.")
                self.show_info_message("Success", "Cloud log successfully replaced with the imported file.")
            else:
                print("Error in replacing cloud log:", update_response.json())
                self.show_info_message("Error", "Error replacing cloud log.")
        except Exception as e:
            print(f"Error importing file: {e}")
            self.show_info_message("Error", f"Error importing file: {e}")
        


    def on_export_log(self):
        refresh_token = self.config['Cloud']['refresh_token']
        if refresh_token == "NULL":
            self.show_info_message("Error", "Currently not signed in to Google.")
            return
        
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
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".log",
                    filetypes=[("Log Files", "*.log"), ("All Files", "*.*")],
                    title="Save Log File As"
                )

                if file_path:
                    try:
                        # Write the file contents to the specified file
                        with open(file_path, "w") as file:
                            file.write(file_contents)
                        print(f"File saved as: {file_path}")
                        self.show_info_message("Success", f"File saved as: {file_path}")
                    except Exception as e:
                        print(f"Error saving file: {e}")
                        self.show_info_message("Error", f"Error saving file: {e}")
                else:
                    print("Save operation was canceled.")
            else:
                print("Error in updating cloud log:", update_response.json())
                self.show_info_message("Error", "Error grabbing cloud log")
        except Exception as e:
            print(e)
            self.show_info_message("Error", "No Log File Found. After you answer your first prompt, your log will be saved to the cloud.")

    def on_search_tag(self, tag):
        self.sort_by_tag(tag)

    def sort_by_tag(self, tag):
        if tag != self.previous_tag:
            self.tag_graph_list = []
            # Destroy all widgets inside the resultsframe
            for widget in self.resultsframe.winfo_children():
                widget.destroy()

            self.display_taggraph(tag)
            self.previous_tag = tag
            self.on_tag_flag = True

    def on_tagscombobox_enter(self, event):
        tag = self.tagscombobox.get()
        self.on_search_tag(tag)

    def on_config_save(self):
        with open(os.path.join(self.script_dir, 'config.ini'), 'w') as configfile:
            self.config.write(configfile)

    def show_info_message(self, title, message):
        if platform.system() == 'Darwin':  # macOS
            # Use osascript to send a native macOS notification
            os.system(f'''
                    osascript -e 'display notification "{message}" with title "{title}"'
            ''')
        else:
            img_path = os.path.join(self.script_dir, "img")
            notification.notify(
                title=title,
                message=message,
                app_name="TagTime",
                app_icon=os.path.join(img_path, 'tagtime.ico')
            )

    def on_next100_button(self):
        print("hello")
        # Destroy all widgets inside the resultsframe
        for widget in self.resultsframe.winfo_children():
            widget.destroy()

        # Reset the scroll position to the top
        self.resultsframe._parent_canvas.yview_moveto(0)

        self.add100count += 100
        
        self.display_100more()

    def on_prev100_button(self):
        print("hello")
        # Destroy all widgets inside the resultsframe
        for widget in self.resultsframe.winfo_children():
            widget.destroy()

        # Reset the scroll position to the top
        self.resultsframe._parent_canvas.yview_moveto(0)

        print(self.add100count)

        self.add100count -= 100

        print(self.add100count)

        if self.add100count == 0:
            self.display_fillgraph()
        else:
            self.display_100more()

    def on_next100sortedtags_button(self):
        print("hello")
        # Destroy all widgets inside the resultsframe
        for widget in self.resultsframe.winfo_children():
            widget.destroy()

        # Reset the scroll position to the top
        self.resultsframe._parent_canvas.yview_moveto(0)

        self.add100count += 100
        self.previous_tag_index = self.tag_graph_index
        self.previous_tag_list.append(self.previous_tag_index)
        print(self.previous_tag_list, " and ", self.previous_tag_index, " and ", self.tag_graph_index)
        
        self.display_100more_taggraph(self.sortedtag)

    def on_prev100sortedtags_button(self):
        print("hello")
        # Destroy all widgets inside the resultsframe
        for widget in self.resultsframe.winfo_children():
            widget.destroy()

        # Reset the scroll position to the top
        self.resultsframe._parent_canvas.yview_moveto(0)

        print(self.add100count)
        print(self.tag_graph_index)

        self.add100count -= 100
        print(self.previous_tag_list)

        if len(self.previous_tag_list) <= 1:
            self.previous_tag_index = 0
        else:
            self.previous_tag_list.pop()
            self.previous_tag_index = self.previous_tag_list[-1]
            self.tag_graph_index = self.previous_tag_index

        print(self.add100count)
        print(self.tag_graph_index)

        if self.add100count == 0:
            self.display_taggraph(self.sortedtag)
        else:
            self.display_100more_taggraph(self.sortedtag)

    def ensure_widget_visible(self, widget):
        # Get the widget's position relative to the root window
        widget_top = widget.winfo_rooty()

        # Get the scrollable frame's position relative to the root window
        frame_top = self.resultsframe.winfo_rooty()

        # Calculate the widget's position relative to the scrollable frame
        widget_top = widget_top - frame_top

        # Get the bottom position similarly
        widget_bottom = widget_top + widget.winfo_height()
        # print(widget_top, widget_bottom)

        # Get the height of the scrollable frame and the visible area
        canvas_height = self.resultsframe._parent_canvas.winfo_height()
        frame_height = self.resultsframe.winfo_reqheight()
        # print(frame_height, canvas_height)

        # Get the current view range (start and end)
        start, end = self.resultsframe._parent_canvas.yview()
        # print(start, end)

        # Convert start and end to pixel positions
        start_pixel = start * frame_height
        end_pixel = end * frame_height
        # print(start_pixel, end_pixel)

        # Calculate the scroll step as a fraction of the widget height relative to the total frame height
        widget_height = widget.winfo_height()
        scroll_step = ((widget_height + 6) / frame_height)

        # Check if the widget is out of view and adjust the view
        if widget_top < start_pixel:
            # Scroll up to bring the widget into view
            new_start = max(start - scroll_step, 0)  # Ensure we don't go out of bounds
            self.resultsframe._parent_canvas.yview_moveto(new_start)
        elif widget_bottom > end_pixel:
            # Scroll down to bring the widget into view
            new_start = min(start + scroll_step, 1 - (end - start))  # Ensure we don't go out of bounds
            self.resultsframe._parent_canvas.yview_moveto(new_start)

    def on_shift_down(self, event):
        current_entry = event.widget.master
        current_text = current_entry.get()
        current_index = self.entries.index(current_entry)
        
        if current_index < len(self.entries) - 1:
            next_entry = self.entries[current_index + 1]
            next_entry.delete(0, "end")
            next_entry.insert(0, current_text)
            next_entry.focus_set()

            self.ensure_widget_visible(next_entry)

    def on_shift_up(self, event):
        current_entry = event.widget.master
        current_text = current_entry.get()
        current_index = self.entries.index(current_entry)
        
        if current_index > 0:
            previous_entry = self.entries[current_index - 1]
            previous_entry.delete(0, "end")
            previous_entry.insert(0, current_text)
            previous_entry.focus_set()

            self.ensure_widget_visible(previous_entry)

    def on_down(self, event):
        current_entry = event.widget.master
        current_index = self.entries.index(current_entry)
        
        if current_index < len(self.entries) - 1:
            next_entry = self.entries[current_index + 1]
            next_entry.focus_set()

            self.ensure_widget_visible(next_entry)

    def on_up(self, event):
        current_entry = event.widget.master
        current_index = self.entries.index(current_entry)
        
        if current_index > 0:
            previous_entry = self.entries[current_index - 1]
            previous_entry.focus_set()

            self.ensure_widget_visible(previous_entry)

    def on_replace_tag_button(self):
        print("on replace tag button")
        self.replace_window = customtkinter.CTkToplevel(self)
        if platform.system() == 'Darwin':
            self.wm_iconbitmap()
        else:
            self.replace_window.after(250, lambda: self.replace_window.iconbitmap(os.path.join(self.img_path, 'tagtime.ico')))
        self.replace_window.title("Replace Tags")
        self.center_window_replace(300, 200)
        self.replace_window.attributes("-topmost", True)
        self.replace_window.after(1000, lambda: self.replace_window.attributes("-topmost", False))  # Disable topmost after 1 second
        self.replace_window.focus_force()

        # replace text
        self.replace_text = customtkinter.CTkLabel(self.replace_window, text="Replace")
        self.replace_text.pack(pady=5)

        # tags replace box
        self.tagsreplacebox = customtkinter.CTkComboBox(self.replace_window, width=125, height=25, values=self.alltags, text_color=["black", "white"],
                                                        border_width=0, corner_radius=0, fg_color=["white", "grey22"], button_color=["grey70", "grey26"], button_hover_color="grey35", bg_color="transparent")
        self.tagsreplacebox.set("")
        self.tagsreplacebox.pack()

        # with text
        self.replace_text = customtkinter.CTkLabel(self.replace_window, text="With", text_color=["black", "white"])
        self.replace_text.pack(pady=5)

        # replace entry box
        self.replace_entry = customtkinter.CTkEntry(self.replace_window, width=125, height=25, text_color=["black", "white"],
                                                        border_width=0, corner_radius=0, fg_color=["white", "grey22"], bg_color="transparent")
        self.replace_entry.pack()

        # Replace Tags Button
        self.replace_button = customtkinter.CTkButton(self.replace_window, text="Replace Tags", width=100, command=self.on_replace_button, corner_radius=0,
                                                        fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.replace_button.pack(pady=20)

    def on_replace_button(self):
        self.updated_tags = []
        old_tag = self.tagsreplacebox.get()
        new_tag = self.replace_entry.get()
        changed = False
        if old_tag and new_tag:
            print(old_tag, new_tag)
            for item in self.fillgraph:

                all_words = re.findall(r'\(.*?\)|\S+', item['words_list'])
                for words in all_words:
                    if '(' in words or ')' in words:
                        pass
                    else:
                        if old_tag == words:
                            print(all_words)
                            index = all_words.index(words)
                            all_words[index] = new_tag
                            print(all_words, " after")
                            old_words = item['words_list']
                            item['words_list'] = ' '.join(all_words)
                            new_words = item['words_list']
                            print(item['words_list'], " after")
                            changed = True

                            weekly_border = int(time.time()) - 604800
                            if item['unix'] < weekly_border:
                                print("LOG IS OLDER THAN 7 DAYS")
                                pass
                            else:
                                print("WITHIN 7 DAYS! GOOD TO GO!")
                                result = {
                                    'old_words': old_words,
                                    'new_words': new_words,
                                    'unix': item['unix']
                                }
                                self.updated_tags.append(result)

                            break

            if changed:
                if self.updated_tags:
                    self.beeminder_check()
                self.save_edited_log()
                self.display_alert()
                self.sync_cloud_log()

                # Destroy all widgets inside the resultsframe
                for widget in self.resultsframe.winfo_children():
                    widget.destroy()

                # Reset the scroll position to the top
                self.resultsframe._parent_canvas.yview_moveto(0)

                print(self.alltags)
                new_index = self.alltags.index(old_tag)
                if new_index:
                    self.alltags[new_index] = new_tag

                # Reset combo boxes
                self.tagsreplacebox.configure(values=self.alltags)
                self.tagscombobox.configure(values=self.alltags)

                # display new fillgraph
                self.tagscombobox.set("")
                self.display_fillgraph()

    def beeminder_check(self):
        auth_token = self.config['Beeminder']['auth_token']
        gap = int(self.config['Settings']['gap'])
        gap_value = gap / 60
        if auth_token != "NULL":
            goal_tags = self.config['Beeminder']['goal_tags']
            goal_tags_json = json.loads(goal_tags)
            print(self.updated_tags, " updated tags")
            for item in self.updated_tags:
                tagtime_old_goals = []
                tagtime_new_goals = []
                print(item['old_words'], " old words")
                print(item['new_words'], " new words")
                print(item['unix'], " timestamp")
                cleaned_string = re.sub(r'\(.*?\)', '', item['old_words'])

                # Strip extra spaces if needed
                old_tags = cleaned_string.strip().split(' ')
                print(old_tags)

                cleaned_string = re.sub(r'\(.*?\)', '', item['new_words'])

                # Strip extra spaces if needed
                new_tags = cleaned_string.strip().split(' ')
                print(new_tags)

                for tag in old_tags:
                    if tag != '':
                        for key, value in goal_tags_json.items():
                            for val in value.split(" "):
                                if tag == val.strip():
                                    result = {
                                        'key': key,
                                        'tags': item['new_words'],
                                        'unix': item['unix']
                                    }
                                    tagtime_old_goals.append(result)

                print(f"Old tags has {len(tagtime_old_goals)} tags that point to goals, those goals are: {tagtime_old_goals}")
                if len(tagtime_old_goals) <= 0:
                    print("old tags have no beeminder tags, checking new tags")
                    for tag in new_tags:
                        if tag != '':
                            for key, value in goal_tags_json.items():
                                for val in value.split(" "):
                                    if tag == val.strip():
                                        result = {
                                            'key': key,
                                            'tags': item['new_words'],
                                            'unix': item['unix']
                                        }
                                        tagtime_new_goals.append(result)

                    print(f"New tags has {len(tagtime_new_goals)} tags that point to goals, those goals are: {tagtime_new_goals}")
                    if len(tagtime_new_goals) <= 0:
                        # Case 1
                        print("old tags and new tags dont have any beeminder goals")
                        pass
                    else:
                        # Case 2
                        for item in tagtime_new_goals:
                            print(f"creating new datapoint for goal: {item['key']} with the tags: {item['tags']} and the timestamp: {item['unix']}")
                            beeminder.create_datapoint(auth_token, item['unix'], item['key'], item['tags'], gap_value)
                            continue

                else:
                    print("old tags do have beeminder tags, checking new tags")
                    for tag in new_tags:
                        if tag != '':
                            for key, value in goal_tags_json.items():
                                for val in value.split(" "):
                                    if tag == val.strip():
                                        result = {
                                            'key': key,
                                            'tags': item['new_words'],
                                            'unix': item['unix']
                                        }
                                        tagtime_new_goals.append(result)

                    print(f"New tags has {len(tagtime_new_goals)} tags that point to goals, those goals are: {tagtime_new_goals}")
                    if len(tagtime_new_goals) <= 0:
                        # Case 3
                        for items in tagtime_old_goals:
                            print(f"Deleting datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                            beeminder.log_delete_datapoint(auth_token, items['key'], items['unix'], item['old_words'], gap_value)
                            continue
                    else:
                        print("old tags and new tags both have beeminder goals, calculate rest")
                        if len(tagtime_old_goals) == len(tagtime_new_goals):
                            match = 0
                            for old_item in tagtime_old_goals:
                                for new_item in tagtime_new_goals:
                                    if old_item['key'] == new_item['key']:
                                        match += 1
                                        print(old_item['key'], " old item ", new_item['key'], " new item ", " is a match!")
                                        break
                            print(match)
                            if match == len(tagtime_old_goals):
                                # Case 4
                                for items in tagtime_new_goals:
                                    print(f"Updating datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                                    beeminder.log_update_datapoint(auth_token, items['key'], items['unix'], item['old_words'], item['new_words'])
                                    continue
                            elif match == 0:
                                # Case 5
                                print("No beeminders tags from old log are current in new log, delete old datapoint, create new")
                                for items in tagtime_old_goals:
                                    print(f"Deleting datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                                    beeminder.log_delete_datapoint(auth_token, items['key'], items['unix'], item['old_words'], gap_value)
                                for item in tagtime_new_goals:
                                    print(f"Creating new datapoint for goal: {item['key']} with the tags: {item['tags']} and the timestamp: {item['unix']}")
                                    beeminder.create_datapoint(auth_token, item['unix'], item['key'], item['tags'], gap_value)
                                continue
                            else:
                                # Case 8
                                print("some beeminder tags are still the samee, but some are missing, and there are new ones, delete any missing ones, update others, create new")
                                delete_tags = []
                                update_tags = []
                                create_tags = []
                                for old_item in tagtime_old_goals:
                                    match = 0
                                    for new_item in tagtime_new_goals:
                                        if old_item['key'] == new_item['key']:
                                            match += 1
                                            print(old_item['key'], " old item ", new_item['key'], " new item ", " is a match!")
                                            update_tags.append(old_item)
                                            break

                                    if match == 0:
                                        delete_tags.append(old_item)

                                for new_item in tagtime_new_goals:
                                    match = 0
                                    for old_item in tagtime_old_goals:
                                        if new_item['key'] == old_item['key']:
                                            match += 1
                                            print(old_item['key'], " old item ", new_item['key'], " new item ", " is a match!")
                                            break
                                    print(match)
                                    if match == 0:
                                        create_tags.append(new_item)

                                for items in delete_tags:
                                    print(f"Deleting datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                                    beeminder.log_delete_datapoint(auth_token, items['key'], items['unix'], item['old_words'], gap_value)
                                for items in update_tags:
                                    print(f"Updating datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                                    beeminder.log_update_datapoint(auth_token, items['key'], items['unix'], item['old_words'], item['new_words'])
                                for item in create_tags:
                                    print(f"Creating new datapoint for goal: {item['key']} with the tags: {item['tags']} and the timestamp: {item['unix']}")
                                    beeminder.create_datapoint(auth_token, item['unix'], item['key'], item['tags'], gap_value)
                                continue
                        else:
                            print("different goals for sure, calculate rest")
                            match = 0
                            for old_item in tagtime_old_goals:
                                for new_item in tagtime_new_goals:
                                    if old_item['key'] == new_item['key']:
                                        match += 1
                                        print(old_item['key'], " old item ", new_item['key'], " new item ", " is a match!")
                                        break
                            if match == 0:
                                # Case 5
                                print("No beeminders tags from old log are current in new log, delete old datapoint, create new")
                                for items in tagtime_old_goals:
                                    print(f"Deleting datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                                    beeminder.log_delete_datapoint(auth_token, items['key'], items['unix'], item['old_words'], gap_value)
                                for item in tagtime_new_goals:
                                    print(f"Creating new datapoint for goal: {item['key']} with the tags: {item['tags']} and the timestamp: {item['unix']}")
                                    beeminder.create_datapoint(auth_token, item['unix'], item['key'], item['tags'], gap_value)
                                continue
                                
                            elif match == len(tagtime_old_goals):
                                # Case 6
                                print("all beeminder tags from old log are current in new log, but new log has extra beeminder tags, update old, create new")
                                create_tags = []
                                for new_item in tagtime_new_goals:
                                    match = 0
                                    for old_item in tagtime_old_goals:
                                        if new_item['key'] == old_item['key']:
                                            match += 1
                                            print(old_item['key'], " old item ", new_item['key'], " new item ", " is a match!")
                                            break
                                    print(match)
                                    if match == 0:
                                        create_tags.append(new_item)

                                for items in tagtime_old_goals:
                                    print(f"Updating datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                                    beeminder.log_update_datapoint(auth_token, items['key'], items['unix'], item['old_words'], item['new_words'])
                                for item in create_tags:
                                    print(f"Creating new datapoint for goal: {item['key']} with the tags: {item['tags']} and the timestamp: {item['unix']}")
                                    beeminder.create_datapoint(auth_token, item['unix'], item['key'], item['tags'], gap_value)
                                continue
                            else:
                                # Case 7, 8
                                print("some beeminder tags are still the samee, but some are missing, and there are new ones, delete any missing ones, update others, create new")
                                print("lengths dont add up")
                                delete_tags = []
                                update_tags = []
                                create_tags = []
                                for old_item in tagtime_old_goals:
                                    match = 0
                                    for new_item in tagtime_new_goals:
                                        if old_item['key'] == new_item['key']:
                                            match += 1
                                            print(old_item['key'], " old item ", new_item['key'], " new item ", " is a match!")
                                            update_tags.append(old_item)
                                            break

                                    if match == 0:
                                        delete_tags.append(old_item)

                                for new_item in tagtime_new_goals:
                                    match = 0
                                    for old_item in tagtime_old_goals:
                                        if new_item['key'] == old_item['key']:
                                            match += 1
                                            print(old_item['key'], " old item ", new_item['key'], " new item ", " is a match!")
                                            break
                                    print(match)
                                    if match == 0:
                                        create_tags.append(new_item)

                                for items in delete_tags:
                                    print(f"Deleting datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                                    beeminder.log_delete_datapoint(auth_token, items['key'], items['unix'], item['old_words'], gap_value)
                                for items in update_tags:
                                    print(f"Updating datapoint for goal: {items['key']} with the tags: {items['tags']} and the timestamp: {items['unix']}")
                                    beeminder.log_update_datapoint(auth_token, items['key'], items['unix'], item['old_words'], item['new_words'])
                                for item in create_tags:
                                    print(f"Creating new datapoint for goal: {item['key']} with the tags: {item['tags']} and the timestamp: {item['unix']}")
                                    beeminder.create_datapoint(auth_token, item['unix'], item['key'], item['tags'], gap_value)
                                continue

    def sync_cloud_log(self):
        refresh_token = self.config['Cloud']['refresh_token']
        if refresh_token == "NULL":
            self.show_info_message("Error", "Currently not signed in to Google.")
            return
        
        file_path = os.path.join(self.script_dir, "log.log")
        
        try:
            # Ensure the file exists
            if not os.path.exists(file_path):
                print(f"Error: {file_path} does not exist.")
                self.show_info_message("Error", "Local log.log file not found.")
                return

            # Read the content of the log.log file
            with open(file_path, "r") as file:
                file_contents = file.read()

            # print(f"Selected file content: {file_contents}")

            # Replace the cloud log with the imported content
            url = "https://hello-bgfsl5zz5q-uc.a.run.app/import_cloud_log"
            update_response = requests.post(
                url,
                json={
                    'refresh_token': refresh_token,
                    'file_name': "log.log",  # The cloud log file name
                    'file_content': file_contents
                }
            )

            if update_response.status_code == 200:
                print("Success: Replaced cloud log with imported file.")
                self.show_info_message("Success", "Cloud log successfully replaced with the imported file.")
            else:
                print("Error in replacing cloud log:", update_response.json())
                self.show_info_message("Error", "Error replacing cloud log.")
        except Exception as e:
            print(f"Error importing file: {e}")
            self.show_info_message("Error", f"Error importing file: {e}")

def main(parent):
    LogViewerWindow(parent)

if __name__ == "__main__":
    root = customtkinter.CTk()  # Create the main window
    root.withdraw()  # Hide the main window since we are only using Toplevels
    main(root)
    root.mainloop()
