import os
import customtkinter
from tkinter import filedialog, messagebox
import re
from datetime import datetime
import configparser
import requests

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(script_dir, 'config.ini'))
appearance_mode = config['Settings']['appearance_mode']

customtkinter.set_appearance_mode(appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # set paths
        self.img_path = os.path.join(script_dir, "img")
        self.log_menu()

    def log_menu(self):

                self.title("Log Viewer/Editor")
                self.center_window(900, 750)
                self.font = customtkinter.CTkFont(family="Helvetica", size=12)
                self.iconbitmap(os.path.join(self.img_path, 'tagtime.ico'))

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

                # Export Log from Cloud text
                self.cloudlog_text = customtkinter.CTkLabel(self.topframe, text="Export Log From Cloud: ")
                self.cloudlog_text.pack(pady=10, side="left")

                # Export Log from Cloud Button
                self.cloudlog_button = customtkinter.CTkButton(self.topframe, text="Export", width=70, command=self.on_export_log,
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
                self.alltags = (config['Tags']['tags']).split(',')
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

                self.log_file_path = os.path.join(script_dir, 'log.log')
                self.fillgraph = self.process_log_file()
                self.fillgraph.reverse()
                self.is_reversed = True

                self.display_fillgraph()

                # Save Log Frame
                self.savelog_frame = customtkinter.CTkFrame(self.logframe, fg_color="transparent", corner_radius=0)
                self.savelog_frame.pack(fill="x")

                # Save Log Button
                self.savelog_button = customtkinter.CTkButton(self.savelog_frame, text="Save Log", width=100, height=35, font=("Helvetica", 18), command=self.on_save_log_button,
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

    def on_recent_selection(self, option):
        if option == "Most Recent" and self.previous_option == "Least Recent":
            self.fillgraph.reverse()
            self.is_reversed = True

            # Destroy all widgets inside the resultsframe
            for widget in self.resultsframe.winfo_children():
                widget.destroy()

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

            self.display_fillgraph()
            self.previous_option = option
            self.on_tag_flag = False
            self.tag_graph_list = []

    def process_log_file(self):
        # Regular expression to match the parts of the log entry
        pattern = re.compile(r'\d+\s+([\w,\s]+)\s+\[(.*)\]')

        results = []

        updated = False
        new_tags = []

        # Open and read the log file
        with open(self.log_file_path, 'r') as file:
            for line in file:
                # Extracting parts using the regular expression
                match = pattern.match(line)
                if match:
                    words_str = match.group(1).strip()  # Extract the words part
                    time_str = match.group(2).strip()  # Extract the time part

                    # Splitting the words part into a list
                    words_list = [word.strip() for word in words_str.split(',')]
                    for tag in words_list:
                        if tag not in self.alltags:
                            updated = True
                            self.alltags.append(tag)
                            new_tags.append(tag)

                    # Store the extracted information in a dictionary
                    result = {
                        'words_list': words_str,
                        'time': time_str
                    }
                    results.append(result)
                else:
                    print(f"Log entry format is incorrect: {line.strip()}")

        if updated:
            self.alltags.sort()
            for item in new_tags:
                config['Tags']['tags'] += ("," + item)
                self.on_config_save()
            self.tagscombobox.configure(values=self.alltags)
            self.tagscombobox.set("")

        return results
    
    def display_fillgraph(self):
        count = 0
        if appearance_mode == "Dark":
            new_fg_color = "transparent"
        elif appearance_mode == "Light":
            new_fg_color = "white"
        else:
            new_fg_color = "transparent"
        for item in self.fillgraph:
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
            resultgrid1_textbox.pack(pady=0)

            # result box divider
            resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color=["grey90", "black"], corner_radius=0, height=6)
            resultboxdivider.pack_propagate(0)
            resultboxdivider.pack(fill="x")

            new_time = self.format_time(item["time"])

            # time label
            time = customtkinter.CTkLabel(resultgrid3, text=new_time, font=("Helvetica", 20))
            time.pack(pady=15)

    def display_taggraph(self, tag):
        count = 0
        self.tag_graph_index = 0
        self.tag_graph_list = []
        if appearance_mode == "Dark":
            new_fg_color = "transparent"
        elif appearance_mode == "Light":
            new_fg_color = "white"
        else:
            new_fg_color = "transparent"
        for item in self.fillgraph:
            if tag in item['words_list']:
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
                resultgrid1_textbox.pack(pady=0)

                # result box divider
                resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color=["grey90", "black"], corner_radius=0, height=6)
                resultboxdivider.pack_propagate(0)
                resultboxdivider.pack(fill="x")

                new_time = self.format_time(item["time"])

                # time label
                time = customtkinter.CTkLabel(resultgrid3, text=new_time, font=("Helvetica", 20))
                time.pack(pady=15)

            self.tag_graph_index += 1

    def format_time(self, time_str):
        # Remove the weekday part
        time_str = ' '.join(time_str.split()[:-1])
        
        # Parse the original time string without the weekday
        parsed_time = datetime.strptime(time_str, "%Y.%m.%d %H:%M:%S")
        
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

        if self.on_tag_flag:
            self.loop_through_tag_widgets(self.resultsframe)
        else:
            self.loop_through_widgets(self.resultsframe)

        self.save_edited_log()
        self.display_alert()

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
                    self.fillgraph[tag_index]['words_list'] = newtext
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
                    self.fillgraph[self.editorcount]['words_list'] = newtext
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
            date_format = '%Y.%m.%d %H:%M:%S %a'

            # Parse the date-time string into a datetime object
            dt = datetime.strptime(date_time_str, date_format)

            # Convert the datetime object to a Unix timestamp
            unix_timestamp = int(dt.timestamp())

            new_formatted_tags = (tags[:50]).ljust(50)

            log_entry = f'{unix_timestamp} {new_formatted_tags} [{date_time_str}]\n'

            updated_lines.append(log_entry)

        # Write all updated lines to the log file, overwriting the existing file
        with open(self.log_file_path, "w") as log_file:
            log_file.writelines(updated_lines)

        if self.is_reversed:
            self.fillgraph.reverse()

    def display_alert(self):
        messagebox.showinfo("Log Saved!", "The updated log has now been saved.")

    def on_export_log(self):
        refresh_token = config['Cloud']['refresh_token']
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
                        messagebox.showinfo("Success", f"File saved as: {file_path}")
                    except Exception as e:
                        print(f"Error saving file: {e}")
                        messagebox.showerror("Error", f"Error saving file: {e}")
                else:
                    print("Save operation was canceled.")
            else:
                print("Error in updating cloud log:", update_response.json())
                messagebox.showerror("Error", "Error grabbing cloud log")
        except Exception as e:
            print(e)
            messagebox.showerror("Error", "No Log File Found. After you answer your first prompt, your log will be saved to the cloud.")

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
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

if __name__ == "__main__":
    app = App()
    app.mainloop()