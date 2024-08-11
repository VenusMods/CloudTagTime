import os
import sys
import customtkinter
from tkinter import messagebox
import threading
import re
from datetime import datetime
import configparser
import webbrowser
import requests
import http.server
import socketserver
import urllib.parse

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(script_dir, 'config.ini'))
appearance_mode = config['Settings']['appearance_mode']

customtkinter.set_appearance_mode(appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue")

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

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # set paths
        self.img_path = os.path.join(script_dir, "img")

        self.settings_menu()

    def settings_menu(self):
            # get refresh token
            self.refresh_token = config['Cloud']['refresh_token']

            # configure window
            self.iconbitmap(os.path.join(self.img_path, 'tagtime.ico'))
            self.title("TagTime")
            self.center_window(400, 400)
            # self.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.font = customtkinter.CTkFont(family="Helvetica", size=12)

            # configure frame
            self.frame = customtkinter.CTkFrame(master=self, corner_radius=0)
            self.frame.pack(fill="both", expand=True)

            # Sign In Frame
            self.sign_in_frame = customtkinter.CTkFrame(self.frame, width=400, height=50, fg_color="transparent")
            # self.sign_in_frame.pack_propagate(0)
            self.sign_in_frame.pack(pady=5)

            if not self.bool_get_user_info_from_token():
                self.display_sign_in_stuff()
            else:
                self.email = self.get_user_info_from_token(self.refresh_token)
                self.display_signed_in()

            # rest of the options frame
            self.restoptions_frame = customtkinter.CTkFrame(self.frame, fg_color="transparent")
            self.restoptions_frame.pack(fill="both", expand=True)

            # appearance mode text
            self.textbox = customtkinter.CTkLabel(self.restoptions_frame, text=f"Appearance Mode")
            self.textbox.pack(pady = 5, padx = 10)

            appearance_mode = config['Settings']['appearance_mode']

            # appearance mode dropdown
            self.dropdown = customtkinter.CTkOptionMenu(master=self.restoptions_frame, values=["Dark", "Light"], width=120, command=self.on_dropdown_click, text_color=["black", "white"],
                                                        fg_color=["white", "grey22"], bg_color="transparent", button_color=["grey70", "grey26"], corner_radius=0, button_hover_color="grey35")
            self.dropdown.set(appearance_mode)
            self.dropdown.pack()

            # sound text
            self.sound_text = customtkinter.CTkLabel(self.restoptions_frame, text=f"Ping Sound")
            self.sound_text.pack(pady = 5, padx = 10)

            sound = (config['Settings']['sound'].split('.'))[0]

            # sound dropdown
            self.sound_dropdown = customtkinter.CTkOptionMenu(master=self.restoptions_frame,
                                                                values=["blip", "blip-twang", "dadadum", "drip", "loud-ding", "loud-phaser", "loud-sorry", "loud-uh-oh", "pop", "quiet-doh", "whoosh"],
                                                                width=120, command=self.on_sound_dropdown_click, text_color=["black", "white"],
                                                                fg_color=["white", "grey22"], bg_color="transparent", button_color=["grey70", "grey26"], corner_radius=0, button_hover_color="grey35")
            self.sound_dropdown.set(sound)
            self.sound_dropdown.pack()

            # tag color frame
            self.tagcolor_frame = customtkinter.CTkFrame(self.restoptions_frame, fg_color="transparent", height=40)
            self.tagcolor_frame.pack_propagate(0)
            self.tagcolor_frame.pack(fill="x")

            # tag color text
            self.tagcolor_text = customtkinter.CTkLabel(self.tagcolor_frame, text=f"Tag Color")
            self.tagcolor_text.pack(side="left", pady = 5, padx = [150, 10])

            tagcolor = config['Settings']['tag_color']

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

            gap = int(config['Settings']['gap'])

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

    def on_quit_click(self):
        self.destroy()

    def on_closing(self):
        self.withdraw()

    def on_dropdown_click(self, value):
        config['Settings']['appearance_mode'] = value
        customtkinter.set_appearance_mode(value)
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

    def on_sound_dropdown_click(self, value):
        config['Settings']['sound'] = (value + ".wav")
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

    def on_tagcolor_dropdown_click(self, value):
        config['Settings']['tag_color'] = value
        self.tagcolor_test_frame.configure(fg_color=value, border_color=value)
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

    def on_gap_dropdown_click(self, value):
        config['Settings']['gap'] = value
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

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

    def on_token_submit(self):
        refresh_token = self.refresh_token
        self.email = self.get_user_info_from_token(refresh_token)
        if self.email == "fail":
            print("Failed to get email.")
        else:
            self.submit_token_frame.pack_forget()
            self.google_frame.pack_forget()
            self.display_signed_in()
            self.refresh_token = refresh_token
            config['Cloud']['refresh_token'] = self.refresh_token
            self.on_config_save()
            self.show_alert()

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
        self.signedin_text.pack(pady=5)

        self.signout_button = customtkinter.CTkButton(self.sign_in_frame, text="Logout", command=self.on_logout, width=80,
                                                      fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.signout_button.pack()

    def on_config_save(self):
        with open(os.path.join(script_dir, 'config.ini'), 'w') as configfile:
            config.write(configfile)

    def show_alert(self):
        messagebox.showinfo("Config Saved!", "You are now signed in. Your refresh token has been saved in config.ini. Your logs will automatically sync to the cloud from now on. If you want to extract your log from the database, go to Log Viewer.")

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
            config['Cloud']['refresh_token'] = 'NULL'
            self.on_config_save()
            messagebox.showinfo("Success!", "Successfully logged out.")
        else:
            print("Error logging out.")

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

        # Submit Token Frame
        self.submit_token_frame = customtkinter.CTkFrame(self.frame, width=400, height=60, fg_color="transparent")
        self.submit_token_frame.pack_propagate(0)
        self.submit_token_frame.pack(fill="both")

        # Submit Token Text
        self.submit_token_text = customtkinter.CTkLabel(self.submit_token_frame, text="Enter Access Token:")
        self.submit_token_text.pack()

        # Submit Token Entry
        self.submit_token_input = customtkinter.CTkEntry(self.submit_token_frame, width=350, corner_radius=0)
        self.submit_token_input.pack(side="left", padx=5)

        # Submit Token button
        self.submit_token_button = customtkinter.CTkButton(self.submit_token_frame, text="✓", font=("Helvetica", 25), width=25, height=20, corner_radius=0, command=self.on_token_submit,
                                                           fg_color=["white", "grey22"], border_color=["grey70", "grey22"], border_width=2, text_color=["black", "white"], hover_color=["grey98", "grey35"])
        self.submit_token_button.pack(side="left")

            
if __name__ == "__main__":
    app = App()
    app.mainloop()
