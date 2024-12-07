import os
import sys
import customtkinter
import threading
import re
from datetime import datetime
import configparser
import webbrowser
import requests
import http.server
import socketserver
import urllib.parse
from PIL import Image
import beeminder
import json
import platform
from notifypy import Notify

class AuthorizationCodeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, app_instance=None, **kwargs):
        self.app_instance = app_instance
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Extract the authorization code from the URL
        if "/callback" in self.path:
            query = self.path.split('?')[-1]
            params = {key: value for (key, value) in [param.split('=') for param in query.split('&')]}
            state = params.get('state')
            authorization_code = params.get('code')

            if authorization_code:
                authorization_code = urllib.parse.unquote(authorization_code)

                # Respond to the browser
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Authorization successful! You can close this window.")

                # Send the authorization code in a JSON request to your hello URL
                self.send_authorization_code(authorization_code, state)

                self.on_sync_log()
                
                # Stop the server after handling the request
                self.server.shutdown()

    def send_authorization_code(self, code, state):
        url = "https://hello-bgfsl5zz5q-uc.a.run.app/getrefresh"
        try:
            update_response = requests.post(
                url,
                json={
                    'authorization_code': code,
                    'state': state
                }
            )

            if update_response.status_code == 200:
                update_data = update_response.json()
                refresh_token = update_data['refresh_token']

                # Call the on_token_submit method using the app_instance
                self.app_instance.refresh_token = refresh_token
                self.app_instance.on_token_submit()
            else:
                print("Error in getting refresh token:", update_response.status_code, update_response.text)
        except requests.exceptions.RequestException as e:
            # Print any exception that occurs during the request
            print(f"Request failed: {e}")

    def on_sync_log(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        config = configparser.ConfigParser()
        config.read(os.path.join(script_dir, 'config.ini'))

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

                file_path = os.path.join(script_dir, "log.log")

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

# Start the local server in a separate thread
def start_local_server(app_instance):
    # Save the original stdout and stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    # Redirect stdout and stderr to suppress output
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    
    try:
        PORT = 8080
        with socketserver.ThreadingTCPServer(("", PORT), lambda *args, **kwargs: AuthorizationCodeHandler(*args, app_instance=app_instance, **kwargs)) as httpd:
            httpd.serve_forever()
    finally:
        # Restore the original stdout and stderr
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr

class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.settings_menu()

    def settings_menu(self):

            # Get the directory of the current script
            self.script_dir = os.path.dirname(os.path.realpath(__file__))

            # set paths
            self.img_path = os.path.join(self.script_dir, "img")

            self.config = configparser.ConfigParser()
            self.config.read(os.path.join(self.script_dir, 'config.ini'))
            self.appearance_mode = self.config['Settings']['appearance_mode']

            customtkinter.set_appearance_mode(self.appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
            customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue")

            # get refresh token
            self.refresh_token = self.config['Cloud']['refresh_token']

            # get auth token
            self.auth_token = self.config['Beeminder']['auth_token']

            # configure window
            if platform.system() == 'Darwin':
                self.wm_iconbitmap()
            else:
                self.after(250, lambda: self.iconbitmap(os.path.join(self.img_path, 'tagtime.ico')))
            # self.iconbitmap(os.path.join(self.img_path, 'tagtime.ico'))
            self.title("TagTime Settings")
            self.center_window(400, 700)
            # self.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.font = customtkinter.CTkFont(family="Helvetica", size=12)

            # configure frame
            self.frame = customtkinter.CTkFrame(master=self, corner_radius=0)
            self.frame.pack(fill="both", expand=True)

            # google image
            self.google_img = customtkinter.CTkImage(light_image=Image.open(os.path.join(self.img_path, 'google.png')), dark_image=Image.open(os.path.join(self.img_path, 'google.png')), size=(50,50))

            # google image label
            self.google_logo = customtkinter.CTkLabel(self.frame, text="", image=self.google_img)
            self.google_logo.pack(pady=5)

            # Sign In Frame
            self.sign_in_frame = customtkinter.CTkFrame(self.frame, width=400, height=50, fg_color="transparent")
            # self.sign_in_frame.pack_propagate(0)
            self.sign_in_frame.pack(pady=5)

            if not self.bool_get_user_info_from_token():
                self.display_sign_in_stuff()
            else:
                self.email = self.get_user_info_from_token(self.refresh_token)
                self.display_signed_in()

            # beeminder image
            self.beeminder_img = customtkinter.CTkImage(light_image=Image.open(os.path.join(self.img_path, 'beeminder.png')), dark_image=Image.open(os.path.join(self.img_path, 'beeminder.png')), size=(60,60))

            # beeminder image label
            self.beeminder_logo = customtkinter.CTkLabel(self.frame, text="", image=self.beeminder_img)
            self.beeminder_logo.pack(pady=5)

            # Beeeminder Sign In Frame
            self.bee_sign_in_frame = customtkinter.CTkFrame(self.frame, width=400, height=50, fg_color="transparent")
            # self.sign_in_frame.pack_propagate(0)
            self.bee_sign_in_frame.pack(pady=5)

            self.username = beeminder.get_username(self.auth_token)
            if self.username:
                self.display_beeminder_signed_in()
            else:
                self.display_beeminder_sign_in()

            # rest of the options frame
            self.restoptions_frame = customtkinter.CTkFrame(self.frame, fg_color="transparent")
            self.restoptions_frame.pack(fill="both", expand=True)

            # task editor text
            self.task_editor_text = customtkinter.CTkLabel(self.restoptions_frame, text=f"Task Editor")
            self.task_editor_text.pack(pady = 5, padx = 10)

            # task editor button
            self.task_editor_button = customtkinter.CTkButton(master=self.restoptions_frame, text="Edit Tasks", width=100, command=self.on_edit_task_button,
                                                        fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
            self.task_editor_button.pack()

            # appearance mode text
            self.textbox = customtkinter.CTkLabel(self.restoptions_frame, text=f"Appearance Mode")
            self.textbox.pack(pady = 5, padx = 10)

            self.appearance_mode = self.config['Settings']['appearance_mode']

            # appearance mode dropdown
            self.dropdown = customtkinter.CTkOptionMenu(master=self.restoptions_frame, values=["Dark", "Light"], width=120, command=self.on_dropdown_click, text_color=["black", "white"],
                                                        fg_color=["white", "grey22"], bg_color="transparent", button_color=["grey70", "grey26"], corner_radius=0, button_hover_color="grey35")
            self.dropdown.set(self.appearance_mode)
            self.dropdown.pack()

            # sound text
            self.sound_text = customtkinter.CTkLabel(self.restoptions_frame, text=f"Ping Sound")
            self.sound_text.pack(pady = 5, padx = 10)

            sound = (self.config['Settings']['sound'].split('.'))[0]

            # sound dropdown
            self.sound_dropdown = customtkinter.CTkOptionMenu(master=self.restoptions_frame,
                                                                values=["silent", "blip", "blip-twang", "dadadum", "drip", "loud-ding", "loud-phaser", "loud-sorry", "loud-uh-oh", "pop", "quiet-doh", "whoosh"],
                                                                width=120, command=self.on_sound_dropdown_click, text_color=["black", "white"],
                                                                fg_color=["white", "grey22"], bg_color="transparent", button_color=["grey70", "grey26"], corner_radius=0, button_hover_color="grey35")
            self.sound_dropdown.set(sound)
            self.sound_dropdown.pack()

            # silent ping text
            self.silent_ping_text = customtkinter.CTkLabel(self.restoptions_frame, text=f"Silent Ping")
            self.silent_ping_text.pack(pady = 5, padx = 10)

            silent_ping_option = self.config['Settings']['silent_ping']

            # silent ping dropdown
            self.silent_ping_dropdown = customtkinter.CTkOptionMenu(master=self.restoptions_frame,
                                                                values=["False", "True"],
                                                                width=120, command=self.on_silent_ping_dropdown_click, text_color=["black", "white"],
                                                                fg_color=["white", "grey22"], bg_color="transparent", button_color=["grey70", "grey26"], corner_radius=0, button_hover_color="grey35")
            self.silent_ping_dropdown.set(silent_ping_option)
            self.silent_ping_dropdown.pack()

            # tag color frame
            self.tagcolor_frame = customtkinter.CTkFrame(self.restoptions_frame, fg_color="transparent", height=40)
            self.tagcolor_frame.pack_propagate(0)
            self.tagcolor_frame.pack(fill="x")

            # tag color text
            self.tagcolor_text = customtkinter.CTkLabel(self.tagcolor_frame, text=f"Tag Color")
            self.tagcolor_text.pack(side="left", pady = 5, padx = [150, 10])

            tagcolor = self.config['Settings']['tag_color']

            # tag color display frame
            self.tagcolor_test_frame = customtkinter.CTkFrame(self.tagcolor_frame, corner_radius=15, width=40, height=24, fg_color=tagcolor, border_color=tagcolor, border_width=1)
            self.tagcolor_test_frame.pack_propagate(0)
            self.tagcolor_test_frame.pack(side="left")

            # tag color display frame text
            self.tagcolor_test_text = customtkinter.CTkLabel(self.tagcolor_test_frame, text="Tag", text_color="white")
            self.tagcolor_test_text.pack()

            # tag color dropdown
            self.tagcolor_dropdown = customtkinter.CTkOptionMenu(master=self.restoptions_frame,
                                                                values=["DarkOrchid4", "DarkOrange3", "firebrick4", "navy", "forest green"],
                                                                width=120, command=self.on_tagcolor_dropdown_click, text_color=["black", "white"],
                                                                fg_color=["white", "grey22"], bg_color="transparent", button_color=["grey70", "grey26"], corner_radius=0, button_hover_color="grey35")
            self.tagcolor_dropdown.set(tagcolor)
            self.tagcolor_dropdown.pack()

            # average ping time text
            self.average_ping_time_text = customtkinter.CTkLabel(self.restoptions_frame, text=f"Average Ping Time (In Minutes)")
            self.average_ping_time_text.pack(pady = 5, padx = 10)

            gap = int(self.config['Settings']['gap'])

            # average ping time dropdown
            self.average_ping_time_dropdown = customtkinter.CTkOptionMenu(master=self.restoptions_frame,
                                                                values=["5", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55", "60",],
                                                                width=70, command=self.on_gap_dropdown_click, text_color=["black", "white"],
                                                                fg_color=["white", "grey22"], bg_color="transparent", button_color=["grey70", "grey26"], corner_radius=0, button_hover_color="grey35")
            self.average_ping_time_dropdown.set(gap)
            self.average_ping_time_dropdown.pack()

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

    def center_window_editgoals(self, width=400, height=490):
        # Get the screen width and height
        screen_width = self.editgoals_window.winfo_screenwidth()
        screen_height = self.editgoals_window.winfo_screenheight()

        # Calculate the position for the window to be centered
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Set the geometry of the window
        self.editgoals_window.geometry(f'{width}x{height}+{x}+{y}')
        # self.minsize(width, height)
        # self.maxsize(width, height)  

    def center_window_edittasks(self, width=400, height=490):
        # Get the screen width and height
        screen_width = self.task_editor_window.winfo_screenwidth()
        screen_height = self.task_editor_window.winfo_screenheight()

        # Calculate the position for the window to be centered
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Set the geometry of the window
        self.task_editor_window.geometry(f'{width}x{height}+{x}+{y}')
        # self.minsize(width, height)
        # self.maxsize(width, height)  

    def on_quit_click(self):
        self.destroy()

    def on_closing(self):
        self.withdraw()

    def on_dropdown_click(self, value):
        self.config['Settings']['appearance_mode'] = value
        customtkinter.set_appearance_mode(value)
        with open(os.path.join(self.script_dir, 'config.ini'), 'w') as configfile:
            self.config.write(configfile)

    def on_sound_dropdown_click(self, value):
        self.config['Settings']['sound'] = (value + ".wav")
        with open(os.path.join(self.script_dir, 'config.ini'), 'w') as configfile:
            self.config.write(configfile)

    def on_silent_ping_dropdown_click(self, value):
        self.config['Settings']['silent_ping'] = value
        with open(os.path.join(self.script_dir, 'config.ini'), 'w') as configfile:
            self.config.write(configfile)

    def on_tagcolor_dropdown_click(self, value):
        self.config['Settings']['tag_color'] = value
        self.tagcolor_test_frame.configure(fg_color=value, border_color=value)
        with open(os.path.join(self.script_dir, 'config.ini'), 'w') as configfile:
            self.config.write(configfile)

    def on_gap_dropdown_click(self, value):
        self.config['Settings']['gap'] = value
        with open(os.path.join(self.script_dir, 'config.ini'), 'w') as configfile:
            self.config.write(configfile)

    # def minimize_window(self, hide=False):
    #         print("minimizing window")
    #         hwnd = windll.user32.GetParent(self.logwindow.winfo_id())
    #         windll.user32.ShowWindow(hwnd, 0 if hide else 6)

    def process_log_file(self, log_file_path):
        # Regular expression to match the parts of the log entry
        pattern = re.compile(r'\d+\s+([\w,\s]+)\s+\[(.*)\]')

        results = []

        # Open and read the log file
        with open(log_file_path, 'r') as file:
            for line in file:
                # Extracting parts using the regular expression
                match = pattern.match(line)
                if match:
                    words_str = match.group(1).strip()  # Extract the words part
                    time_str = match.group(2).strip()  # Extract the time part

                    # # Splitting the words part into a list
                    # words_list = [word.strip() for word in words_str.split(',')]

                    # Store the extracted information in a dictionary
                    result = {
                        'words_list': words_str,
                        'time': time_str
                    }
                    results.append(result)
                else:
                    print(f"Log entry format is incorrect: {line.strip()}")

        return results
    
    def sign_in(self):
        # Start the local server in a new thread
        threading.Thread(target=start_local_server, args=(self,), daemon=True).start()

        webbrowser.open("https://hello-bgfsl5zz5q-uc.a.run.app")

    def sign_in_beeminder(self):

        webbrowser.open("https://www.beeminder.com/api/v1/auth_token.json")

    def on_token_submit(self):
        refresh_token = self.refresh_token
        self.email = self.get_user_info_from_token(refresh_token)
        if self.email == "fail":
            print("Failed to get email.")
        else:
            self.google_frame.pack_forget()
            self.display_signed_in()
            self.refresh_token = refresh_token
            self.config['Cloud']['refresh_token'] = self.refresh_token
            self.on_config_save()
            self.show_alert()

    def on_beeminder_token_submit(self):
        auth_token = self.submit_token_input.get()
        print(auth_token)
        self.username = beeminder.get_username(auth_token)
        if self.username:
            print(self.username)
            self.beeminder_frame.pack_forget()
            self.submit_token_frame.pack_forget()
            self.display_beeminder_signed_in()
            self.auth_token = auth_token
            self.config['Beeminder']['auth_token'] = self.auth_token
            self.on_config_save()
            self.show_beeminder_alert()
        else:
            print("failed")

    def get_user_info_from_token(self, refresh_token):
        if refresh_token != "NULL":
            url = "https://hello-bgfsl5zz5q-uc.a.run.app/getemail"
            update_response = requests.post(
                url,
                json={
                    'refresh_token': refresh_token
                }
            )

            if update_response.status_code == 200:
                update_data = update_response.json()
                email = update_data['user_info']['email']
                return email
            else:
                print("Error in updating cloud log:", update_response.json())
                return "fail"
        else:
            return "fail"
        
    def bool_get_user_info_from_token(self):
        if self.refresh_token != "NULL":
            url = "https://hello-bgfsl5zz5q-uc.a.run.app/getemail"
            update_response = requests.post(
                url,
                json={
                    'refresh_token': self.refresh_token
                }
            )

            if update_response.status_code == 200:
                return True
            else:
                return False
        else:
            return False
        
    def display_signed_in(self):
        self.signedin_text = customtkinter.CTkLabel(self.sign_in_frame, text=f"Signed in as: {self.email}")
        self.signedin_text.pack()

        self.signout_button = customtkinter.CTkButton(self.sign_in_frame, text="Logout", command=self.on_logout, width=80,
                                                      fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.signout_button.pack(pady=5)

    def display_beeminder_signed_in(self):
        self.bee_signedin_text = customtkinter.CTkLabel(self.bee_sign_in_frame, text=f"Signed in as: {self.username}")
        self.bee_signedin_text.pack()

        self.bee_editgoals_button = customtkinter.CTkButton(self.bee_sign_in_frame, text="Edit Goals", command=self.on_beeminder_editgoals, width=80,
                                                      fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.bee_editgoals_button.pack(side="left", pady=5, padx=(0, 5))

        self.bee_signout_button = customtkinter.CTkButton(self.bee_sign_in_frame, text="Logout", command=self.on_beeminder_logout, width=80,
                                                      fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.bee_signout_button.pack(side="left", pady=5, padx=(5, 0))

    def on_config_save(self):
        with open(os.path.join(self.script_dir, 'config.ini'), 'w') as configfile:
            self.config.write(configfile)

    def show_alert(self):
        self.show_info_message("Signed In!", "You are now signed in. Your logs will automatically sync to the cloud from now on. If you want to extract your log from the database, go to Log Viewer.")

    def show_beeminder_alert(self):
        self.show_info_message("Signed In!", "You are now signed in to Beeminder. You can now point tags to a certain goal in settings!")

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

        # Format the parsed time
        formatted_time = parsed_time.strftime(f"%B {day}{suffix}, %Y\n%H:%M:%S")
        return formatted_time

    def on_recent_selection(self, option):
        if option == "Most Recent" and self.previous_option == "Least Recent":
            self.fillgraph.reverse()

            # Destroy all widgets inside the resultsframe
            for widget in self.resultsframe.winfo_children():
                widget.destroy()

            self.display_fillgraph()
            self.previous_option = option
        elif option == "Least Recent" and self.previous_option == "Most Recent":
            self.fillgraph.reverse()

            # Destroy all widgets inside the resultsframe
            for widget in self.resultsframe.winfo_children():
                widget.destroy()

            self.display_fillgraph()
            self.previous_option = option

    def display_fillgraph(self):
        for item in self.fillgraph:
            # result box
            resultbox = customtkinter.CTkFrame(self.resultsframe, corner_radius=0, height=75)
            resultbox.pack_propagate(0)
            resultbox.pack(fill="both")

            resultgrid3 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=200, fg_color="transparent")
            resultgrid3.pack_propagate(0)
            resultgrid3.pack(fill="y", side="left")

            resultgrid1border = customtkinter.CTkFrame(resultbox, fg_color="black", corner_radius=0, width=6)
            resultgrid1border.pack_propagate(0)
            resultgrid1border.pack(fill="y", side="left")

            resultgrid1 = customtkinter.CTkFrame(resultbox, corner_radius=0, width=600, fg_color="transparent")
            resultgrid1.pack_propagate(0)
            resultgrid1.pack(fill="y", side="left")

            # result box divider
            resultboxdivider = customtkinter.CTkFrame(self.resultsframe, fg_color="black", corner_radius=0, height=6)
            resultboxdivider.pack_propagate(0)
            resultboxdivider.pack(fill="x")

            new_time = self.format_time(item["time"])

            # if item["comments"] == "":
            #     item["comments"] = "N/A"

            # tags label
            tags = customtkinter.CTkLabel(resultgrid1, text=item["words_list"], font=("Helvetica", 20))
            tags.pack(pady=25)

            # # comments label
            # comments = customtkinter.CTkLabel(resultgrid2, text=item["comments"])
            # comments.pack()

            # time label
            time = customtkinter.CTkLabel(resultgrid3, text=new_time, font=("Helvetica", 20))
            time.pack(pady=15)

    def on_logout(self):
        url = "https://hello-bgfsl5zz5q-uc.a.run.app/logout"
        update_response = requests.post(
            url,
            json={
                'refresh_token': self.refresh_token
            }
        )

        if update_response.status_code == 200:
            update_data = update_response.json()
            self.signedin_text.pack_forget()
            self.signout_button.pack_forget()
            self.restoptions_frame.pack_forget()
            self.display_sign_in_stuff()
            self.restoptions_frame.pack(fill="both", expand=True)
            self.config['Cloud']['refresh_token'] = 'NULL'
            self.on_config_save()
            self.show_info_message("Success!", "Successfully logged out.")
        else:
            print("Error logging out.")

    def on_beeminder_logout(self):
        self.config['Beeminder']['auth_token'] = "NULL"
        self.on_config_save()
        self.bee_signedin_text.pack_forget()
        self.bee_signout_button.pack_forget()
        self.bee_editgoals_button.pack_forget()
        self.restoptions_frame.pack_forget()
        self.display_beeminder_sign_in()
        self.restoptions_frame.pack(fill="both", expand=True)
        self.show_info_message("Success!", "Successfully logged out.")

    def display_sign_in_stuff(self):
        # Google Frame
        self.google_frame = customtkinter.CTkFrame(self.sign_in_frame, fg_color="transparent", width=400, height=50)
        # self.google_frame.pack_propagate(0)
        self.google_frame.pack(fill="both")

        # Sign In Text
        self.sign_in_text = customtkinter.CTkLabel(self.google_frame, text="Sign in with Google: ")
        self.sign_in_text.pack(side="left", padx=5, pady=5)

        # Sign in button
        self.sign_in_button = customtkinter.CTkButton(self.google_frame, text="Sign In", width=75, command=self.sign_in,
                                                      fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.sign_in_button.pack(side="left")

    def show_info_message(self, title, message):
        if platform.system() == 'Darwin':  # macOS
            # Use osascript to send a native macOS notification
            os.system(f'''
                    osascript -e 'display notification "{message}" with title "{title}"'
            ''')
        else:
            notification = Notify()
            notification.title = title
            notification.message = message
            notification.application_name = "TagTime"
            notification.icon = os.path.join(self.script_dir, "img", "tagtime.ico")

            notification.send(block=False)

    def display_beeminder_sign_in(self):
        # Beeminder Frame
        self.beeminder_frame = customtkinter.CTkFrame(self.bee_sign_in_frame, fg_color="transparent", height=40)
        # self.beeminder_frame.pack_propagate(0)
        self.beeminder_frame.pack(fill="y")

        # Sign In Text
        self.sign_in_text = customtkinter.CTkLabel(self.beeminder_frame, text="Sign in with Beeminder: ")
        self.sign_in_text.pack(side="left", padx=5, pady=5)

        # Sign in button
        self.sign_in_button = customtkinter.CTkButton(self.beeminder_frame, text="Sign In", width=75, command=self.sign_in_beeminder,
                                                      fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.sign_in_button.pack(side="left")

        # Submit Token Frame
        self.submit_token_frame = customtkinter.CTkFrame(self.bee_sign_in_frame, width=215, height=60, fg_color="transparent")
        self.submit_token_frame.pack_propagate(0)
        self.submit_token_frame.pack(fill="both")

        # Submit Token Text
        self.submit_token_text = customtkinter.CTkLabel(self.submit_token_frame, text="Enter Beeminder Auth Token:")
        self.submit_token_text.pack()

        # Submit Token Entry
        self.submit_token_input = customtkinter.CTkEntry(self.submit_token_frame, width=180, corner_radius=0)
        self.submit_token_input.pack(side="left", padx=5)

        # Submit Token button
        self.submit_token_button = customtkinter.CTkButton(self.submit_token_frame, text="✓", font=("Helvetica", 25), width=25, height=20, corner_radius=0, command=self.on_beeminder_token_submit,
                                                           fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.submit_token_button.pack(side="left")

    def on_beeminder_editgoals(self):
        self.goals = beeminder.get_all_goals(self.auth_token)
        print(self.goals)
        self.editgoals_window = customtkinter.CTkToplevel(self)
        if platform.system() == 'Darwin':
            self.wm_iconbitmap()
        else:
            self.editgoals_window.after(250, lambda: self.editgoals_window.iconbitmap(os.path.join(self.img_path, 'tagtime.ico')))
        self.editgoals_window.title("Edit Goals")
        self.center_window_editgoals(400, 300)
        self.editgoals_window.attributes("-topmost", True)
        self.editgoals_window.after(1000, lambda: self.editgoals_window.attributes("-topmost", False))  # Disable topmost after 1 second
        self.editgoals_window.focus_force()

        # Master frame
        self.master_frame = customtkinter.CTkScrollableFrame(self.editgoals_window, corner_radius=0, width=400, height=250)
        self.master_frame.pack()

        # Save Tags Button
        self.savegoal_button = customtkinter.CTkButton(self.editgoals_window, text="Save Tags", width=100, command=self.on_savegoal_button, corner_radius=0,
                                                        fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.savegoal_button.pack(side="right", pady=5, padx=20)

        goal_tags = self.config['Beeminder']['goal_tags']
        print(goal_tags, " goal tags")
        if goal_tags != "NULL":
            goal_tags_json = json.loads(goal_tags)
            print(goal_tags_json)

        if self.goals:
            for goal in self.goals:
                # column frame
                column_frame = customtkinter.CTkFrame(self.master_frame, fg_color="transparent", height=30, width=400, corner_radius=0)
                column_frame.pack_propagate(0)
                column_frame.pack()

                # goal frame
                goal_frame = customtkinter.CTkFrame(column_frame, fg_color="transparent", width=100, height=30, corner_radius=0)
                goal_frame.pack_propagate(0)
                goal_frame.pack(side="left")

                # goal label
                goal_label = customtkinter.CTkLabel(goal_frame, fg_color="transparent", corner_radius=0, text=goal, text_color=["black", "white"])
                goal_label.pack()


                # vertical divider
                vertical_divider = customtkinter.CTkFrame(column_frame, fg_color="black", width=4, corner_radius=0)
                vertical_divider.pack_propagate(0)
                vertical_divider.pack(fill="y", side="left")

                # tag frame
                tag_frame = customtkinter.CTkFrame(column_frame, fg_color="transparent", width=296, height=30, corner_radius=0)
                tag_frame.pack_propagate(0)
                tag_frame.pack(side="left")

                # tag entry box
                tag_entry = customtkinter.CTkEntry(tag_frame, width=296, height=30, fg_color="transparent", corner_radius=0, border_width=0)
                try:
                    tag_entry.insert(0, goal_tags_json[goal])
                except Exception as e:
                    tag_entry.insert(0, "N/A")
                tag_entry.pack_propagate(0)
                tag_entry.pack()


                # horizontal divider
                bottom_divider = customtkinter.CTkFrame(self.master_frame, fg_color="black", height=4, corner_radius=0)
                bottom_divider.pack_propagate(0)
                bottom_divider.pack(fill="x")

        

        # replace text
        # self.replace_text = customtkinter.CTkLabel(self.editgoals_window, text="Replace")
        # self.replace_text.pack(pady=5)

        # # tags replace box
        # self.tagsreplacebox = customtkinter.CTkComboBox(self.editgoals_window, width=125, height=25, values=self.alltags, text_color=["black", "white"],
        #                                                 border_width=0, corner_radius=0, fg_color=["white", "grey22"], button_color=["grey70", "grey26"], button_hover_color="grey35", bg_color="transparent")
        # self.tagsreplacebox.set("")
        # self.tagsreplacebox.pack()

        # # with text
        # self.replace_text = customtkinter.CTkLabel(self.editgoals_window, text="With", text_color=["black", "white"])
        # self.replace_text.pack(pady=5)

        # # replace entry box
        # self.replace_entry = customtkinter.CTkEntry(self.editgoals_window, width=125, height=25, text_color=["black", "white"],
        #                                                 border_width=0, corner_radius=0, fg_color=["white", "grey22"], bg_color="transparent")
        # self.replace_entry.pack()

        # # Replace Tags Button
        # self.replace_button = customtkinter.CTkButton(self.editgoals_window, text="Replace Tags", width=100, command=self.on_replace_button, corner_radius=0,
        #                                                 fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        # self.replace_button.pack(pady=20)

    def on_savegoal_button(self):
        self.goal_list = []
        self.tag_list = []

        self.loop_through_widgets(self.master_frame)

        print(self.goal_list)
        print(self.tag_list)

        goal_tags = {} 
        counter = 0
        for goal in self.goal_list:
            if self.tag_list[counter] == '':
                self.tag_list[counter] = "N/A"
            goal_tags[goal] = self.tag_list[counter]
            counter += 1

        print(goal_tags)
        self.config['Beeminder']['goal_tags'] = json.dumps(goal_tags)
        self.on_config_save()
        self.show_info_message("Success!", "Goal Tags Saved. Now anytime you use these tags, they will contribute to your goals!")

    def loop_through_widgets(self, frame):
        # Get all child widgets of resultbox
        for widget in frame.winfo_children():
            if isinstance(widget, customtkinter.CTkLabel):
                # Example: Print the text of CTkEntry widgets
                newtext = widget.cget("text")
                self.goal_list.append(newtext)
                print(newtext)
            if isinstance(widget, customtkinter.CTkEntry):
                # Example: Print the text of CTkEntry widgets
                newtext = widget.get()
                self.tag_list.append(newtext)
                print(newtext)
            elif isinstance(widget, customtkinter.CTkFrame):
                self.loop_through_widgets(widget)

    def on_edit_task_button(self):
        self.task_editor_window = customtkinter.CTkToplevel(self)
        if platform.system() == 'Darwin':
            self.wm_iconbitmap()
        else:
            self.task_editor_window.after(250, lambda: self.task_editor_window.iconbitmap(os.path.join(self.img_path, 'tagtime.ico')))
        self.task_editor_window.title("Edit Tasks")
        self.center_window_edittasks(400, 300)
        self.task_editor_window.attributes("-topmost", True)
        self.task_editor_window.after(1000, lambda: self.task_editor_window.attributes("-topmost", False))  # Disable topmost after 1 second
        self.task_editor_window.focus_force()

        # Master frame
        self.task_master_frame = customtkinter.CTkScrollableFrame(self.task_editor_window, corner_radius=0, width=400, height=250)
        self.task_master_frame.pack()

        # Save Tasks Button
        self.save_tasks_button = customtkinter.CTkButton(self.task_editor_window, text="Save Tasks", width=100, command=self.on_save_tasks_button, corner_radius=0,
                                                        fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.save_tasks_button.pack(side="right", pady=5, padx=20)

        task_tags = self.config['TaskEditor']['tasks']
        print(task_tags, " task tags")
        if task_tags != "NULL":
            task_tags_json = json.loads(task_tags)
            print(task_tags_json)

        for i in range(100):
            # column frame
            column_frame = customtkinter.CTkFrame(self.task_master_frame, fg_color="transparent", height=30, width=400, corner_radius=0)
            column_frame.pack_propagate(0)
            column_frame.pack()

            # goal frame
            goal_frame = customtkinter.CTkFrame(column_frame, fg_color="transparent", width=100, height=30, corner_radius=0)
            goal_frame.pack_propagate(0)
            goal_frame.pack(side="left")

            # goal label
            goal_label = customtkinter.CTkLabel(goal_frame, fg_color="transparent", corner_radius=0, text=(i + 1), text_color=["black", "white"])
            goal_label.pack(pady=2)


            # vertical divider
            vertical_divider = customtkinter.CTkFrame(column_frame, fg_color="black", width=4, corner_radius=0)
            vertical_divider.pack_propagate(0)
            vertical_divider.pack(fill="y", side="left")

            # tag frame
            tag_frame = customtkinter.CTkFrame(column_frame, fg_color="transparent", width=296, height=30, corner_radius=0)
            tag_frame.pack_propagate(0)
            tag_frame.pack(side="left")

            # tag entry box
            tag_entry = customtkinter.CTkEntry(tag_frame, width=296, height=30, fg_color="transparent", corner_radius=0, border_width=0)
            try:
                tag_entry.insert(0, task_tags_json[f"{i + 1}"])
            except Exception as e:
                tag_entry.insert(0, "N/A")
            tag_entry.pack_propagate(0)
            tag_entry.pack()


            # horizontal divider
            bottom_divider = customtkinter.CTkFrame(self.task_master_frame, fg_color="black", height=4, corner_radius=0)
            bottom_divider.pack_propagate(0)
            bottom_divider.pack(fill="x")

    def on_save_tasks_button(self):
        print("save tasks")
        self.task_list = []
        self.task_tag_list = []

        self.loop_through_widgets_task_editor(self.task_master_frame)

        print(self.task_list)
        print(self.task_tag_list)

        goal_tags = {} 
        counter = 0
        for goal in self.task_list:
            if self.task_tag_list[counter] == '':
                self.task_tag_list[counter] = "N/A"
            goal_tags[goal] = self.task_tag_list[counter]
            counter += 1

        print(goal_tags)
        self.config['TaskEditor']['tasks'] = json.dumps(goal_tags)
        self.on_config_save()
        self.show_info_message("Success!", "Tasks Saved. Now anytime you use these tasks to answer a ping, it will replace it will all of the tags you have set for it.")

    def loop_through_widgets_task_editor(self, frame):
        # Get all child widgets of resultbox
        for widget in frame.winfo_children():
            if isinstance(widget, customtkinter.CTkLabel):
                # Example: Print the text of CTkEntry widgets
                newtext = widget.cget("text")
                self.task_list.append(newtext)
                print(newtext)
            if isinstance(widget, customtkinter.CTkEntry):
                # Example: Print the text of CTkEntry widgets
                newtext = widget.get()
                self.task_tag_list.append(newtext)
                print(newtext)
            elif isinstance(widget, customtkinter.CTkFrame):
                self.loop_through_widgets_task_editor(widget)


def startup(parent):
    SettingsWindow(parent)

def main():
    print("starting settings")
    root = customtkinter.CTk()  # Create the main window
    root.withdraw()  # Hide the main window since we are only using Toplevels
    startup(root)
    root.mainloop()
            
if __name__ == "__main__":
    root = customtkinter.CTk()  # Create the main window
    root.withdraw()  # Hide the main window since we are only using Toplevels
    startup(root)
    root.mainloop()
