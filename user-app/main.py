"""
Example script for testing the Azure ttk theme
Author: rdbende
License: MIT license
Source: https://github.com/rdbende/ttk-widget-factory
"""
import sys
sys.path.append('../')
sys.path.append('../IMU')
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import webbrowser
from time import strftime, localtime
from datetime import date
from IMU import trajectory_generation
from ObjectDetection_camera.gptsummarization import generate_summary
import os


class App(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self)

        self.root = parent

        # Make the app responsive
        for index in [0, 1, 2]:
            self.columnconfigure(index=index, weight=1)
            self.rowconfigure(index=index, weight=1)

        # Create value lists
        self.option_menu_list = ["", "Live Streaming Options", "Main Camera", "Side Camera"]
        self.combo_list = ["Combobox", "Editable item 1", "Editable item 2"]
        self.readonly_combo_list = ["Readonly combobox", "Item 1", "Item 2"]

        # Create control variables
        self.var_0 = tk.BooleanVar()
        self.var_1 = tk.BooleanVar(value=True)
        self.var_2 = tk.BooleanVar()
        self.var_3 = tk.IntVar(value=2)
        self.var_4 = tk.StringVar(value=self.option_menu_list[1])
        self.var_5 = tk.DoubleVar(value=75.0)

        # Create widgets :)
        self.setup_widgets()

    def update_time(self):
        current_time = strftime('%m/%d/%Y\n %H:%M', localtime())
        self.time_label.config(text=current_time)
        self.time_label.after(1000, self.update_time)
    
    def on_theme_change(self):
        # NOTE: The theme's real name is azure-<mode>
        if root.tk.call("ttk::style", "theme", "use") == "azure-dark":
            # Set light theme
            root.tk.call("set_theme", "light")
        else:
            # Set dark theme
            root.tk.call("set_theme", "dark")
    
    def live_stream(self):
        if self.var_4.get() == "Main Camera":
            webbrowser.open("www.YouTube.com/channel/UClrdoCQ1tNfZ6PFgktlCGLw/live")

    def fetch_report(self):
        # Change the image when the button is clicked
        trajectory_generation.generate_trajectory()

        # get today's date
        today_date = str(date.today())

        # fetch report
        report_csv_path = '../ObjectDetection_camera/pet_video_captin_report_'+ today_date + '.csv'
        report = generate_summary(report_csv_path)
        # print(report)
        self.test_label_2.config(text = report, font=("-size", 12, "-weight", "bold"))
        
        self.image_path = "pet_movement.png"  # Replace with your new image path
        pil_image = Image.open(self.image_path)
        tk_image = ImageTk.PhotoImage(pil_image)
        self.trajectory_label.configure(image=tk_image, justify="center")
        self.trajectory_label.image = tk_image  # Keep a reference to avoid garbage collection
        os.remove("pet_movement.png")


    def setup_widgets(self):
        # Create a Frame for the titless
        self.title_frame = ttk.LabelFrame(self, text="Welcome!", padding=(20, 10))
        self.title_frame.grid(
            row=1, column=0, padx=(20, 10), pady=(20, 10), sticky="nsew"
        )

        # Titles and times
        self.titles = ttk.Label(
            self.title_frame,
            text="AIPet",
            justify="center",
            font=("-size", 30, "-weight", "bold"),
        )
        self.titles.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        self.time_label = ttk.Label(self.title_frame, text="Time", justify="center",
            font=("-size", 15, "-weight", "bold"))
        self.time_label.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")
        self.update_time()
        
        # Separator
        self.separator = ttk.Separator(self)
        self.separator.grid(row=2, column=0, padx=(20, 10), pady=10, sticky="ew")

        # Create a Frame for the Themes changing
        self.theme_frame = ttk.LabelFrame(self, text="Themes", padding=(20, 10))
        self.theme_frame.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="nsew")

        # Radiobuttons for themes
        self.theme_radio_1 = ttk.Radiobutton(
            self.theme_frame, text="Light", variable=self.var_3, value=1,
            command=self.on_theme_change
        )
        self.theme_radio_1.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        self.theme_radio_2 = ttk.Radiobutton(
            self.theme_frame, text="Dark", variable=self.var_3, value=2,
            command=self.on_theme_change
        )
        self.theme_radio_2.grid(row=1, column=0, padx=5, pady=10, sticky="nsew")
        
        # Create a Frame for input widgets
        self.widgets_frame = ttk.Frame(self, padding=(0, 0, 0, 10))
        self.widgets_frame.grid(
            row=0, column=0, padx=20, pady=(30, 0), sticky="nsew", columnspan=3
        )
        self.widgets_frame.columnconfigure(index=0, weight=1)

        # Settings
        self.settings_button = ttk.Button(self.widgets_frame, text="Settings")
        self.settings_button.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        
        # Generate Report Button
        self.generate_report_button = ttk.Button(self.widgets_frame, text="Generate Report", command=self.fetch_report)
        self.generate_report_button.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")

        # OptionMenu
        self.live_streaming_optionmenu = ttk.OptionMenu(
            self.widgets_frame, self.var_4, *self.option_menu_list
        )
        self.live_streaming_optionmenu.grid(row=0, column=2, padx=5, pady=10, sticky="nsew")

        # open live streaming
        self.open_live_streaming_button = ttk.Button(self.widgets_frame, text="Open Live Streaming", command=self.live_stream)
        self.open_live_streaming_button.grid(row=0, column=3, padx=5, pady=10, sticky="nsew")

        # Disable notification
        self.switch = ttk.Checkbutton(
            self.widgets_frame, text="Disable Notification", style="Switch.TCheckbutton"
        )
        self.switch.grid(row=0, column=4, padx=5, pady=10, sticky="nsew")

        # Image frame
        self.image_frame = ttk.LabelFrame(self, text="Trajectory Plot", padding=(20, 10))
        self.image_frame.grid(row=1, column=2, padx=(20, 10), pady=(20, 10), sticky="nsew")

        # Trajectory
        self.trajectory_image_path = "../IMU/plotting_test/default2_re.png"  # Replace with your image path
        pil_trajectory_image = Image.open(self.trajectory_image_path)
        tk_trajectory_image = ImageTk.PhotoImage(pil_trajectory_image)

        self.trajectory_label = ttk.Label(
            self.image_frame,
            justify="center",
            font=("-size", 50, "-weight", "bold"),
            image=tk_trajectory_image
        )
        self.trajectory_label.image = tk_trajectory_image
        self.trajectory_label.grid(row=0, column=0, pady=10, columnspan=2, sticky="nsew")

        # Image frame 2
        self.image_frame_2 = ttk.LabelFrame(self, text="Screenshots", padding=(20, 10))
        self.image_frame_2.grid(row=1, column=3, padx=(20, 10), pady=(20, 10), sticky="nsew")
        # Screenshot
        self.screenshot_image_path = "../IMU/plotting_test/default_3_re.png"  # Replace with your image path
        pil_screenshot_image = Image.open(self.screenshot_image_path)
        tk_screenshot_image = ImageTk.PhotoImage(pil_screenshot_image)

        self.screenshot_label = ttk.Label(
            self.image_frame_2,
            justify="center",
            font=("-size", 50, "-weight", "bold"),
            image=tk_screenshot_image
        )
        self.screenshot_label.image = tk_screenshot_image
        self.screenshot_label.grid(row=0, column=1, pady=10, columnspan=2, sticky="nsew")

        # Separator
        self.separator_2 = ttk.Separator(self)
        self.separator_2.grid(row=2, column=2, padx=(20, 10), pady=10, sticky="ew", columnspan=2)

        # Report frame
        self.report_frame = ttk.LabelFrame(self, text="Report", padding=(20, 10))
        self.report_frame.grid(row=3, column=2, padx=(20, 10), pady=(20, 10), sticky="nsew", columnspan=2, rowspan=4)

        self.test_label_2 = ttk.Label(
            self.report_frame,
            text=" Welcome to AIPet!",
            justify="center",
            font=("-size", 50, "-weight", "bold"),
            wraplength=800
        )
        self.test_label_2.grid(row=0, column=0, pady=10, columnspan=2, rowspan=4)



if __name__ == "__main__":
    root = tk.Tk()
    root.title("")

    # Simply set the theme
    root.tk.call("source", "azure.tcl")
    root.tk.call("set_theme", "dark")

    app = App(root)
    app.pack(fill="both", expand=True)

    # Set a minsize for the window, and place it in the middle
    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
    y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
    root.geometry("+{}+{}".format(x_cordinate, y_cordinate-20))

    root.mainloop()
