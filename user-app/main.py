import tkinter as tk
import sys
import webbrowser
sys.path.append('../')
sys.path.append('../IMU')
from time import strftime, localtime

from IMU import imu_communication_apis

class AIPetUserInterface:
    default_display_string = "Welcome to AIPet!"  # Your initial string content
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AIPet Monitor")

        # communication protocols initialize
        if not self.initialize_imu_communication():
            sys.exit()

        # Setting window size to 800x600
        self.root.geometry("800x600")

        # Title
        self.title_label = tk.Label(self.root, text="AIPet Monitor", font=("Helvetica", 24))
        self.title_label.place(relx=0.5, y=50, anchor=tk.CENTER)  # Centering the title

        # Text display box
        self.text_display = tk.Text(self.root, height=8, width=50, font=("Helvetica", 20))
        self.text_display.insert(tk.END, self.default_display_string)  # Display the initial string
        self.text_display.config(state='disabled')  # Disable editing
        self.text_display.place(relx=0.5, rely=0.4, anchor=tk.CENTER)  # Centering the text box

        # Current time display
        self.time_label = tk.Label(self.root, font=("Helvetica", 16))
        self.time_label.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-10, y=10)  # Placing time label in upper right corner

        # Button for getting pet travel distance
        self.get_distance_button = tk.Button(self.root, text="Generate Activity Report", command=self.generate_report, 
                                             width=30, height=2)
        self.get_distance_button.place(relx=0.25, rely=0.7, anchor=tk.CENTER)  # Placing the button below the text box

        # Button for living streaming (main)
        self.get_distance_button = tk.Button(self.root, text="Living Stream (Main Camera)", command=self.live_stream, 
                                             width=30, height=2)
        self.get_distance_button.place(relx=0.75, rely=0.7, anchor=tk.CENTER)  # Placing the button below the text box

        # Button for living streaming (sub)
        self.get_distance_button = tk.Button(self.root, text="Living Stream (Sub Camera)", command=self.live_stream, 
                                             width=30, height=2)
        self.get_distance_button.place(relx=0.25, rely=0.8, anchor=tk.CENTER)  # Placing the button below the text box

    def initialize_imu_communication(self):
        if not imu_communication_apis.initialize_app_publisher():   
            return False
        if not imu_communication_apis.initialize_app_subscriber():
            return False
        return True

    def update_time(self):
        current_time = strftime('%m/%d/%Y %H:%M', localtime())
        self.time_label.config(text=current_time)
        self.time_label.after(1000, self.update_time)

    def run_interface(self):
        self.update_time()
        self.root.mainloop()
    
    def generate_report(self):
        distance, ack, message = imu_communication_apis.get_imu_distance()

        audio_times = 0
        audio_period = 0

        if not ack:
            print("App: get distance error " + message)
        
        current_time = strftime('%m/%d/%Y %H:%M', localtime())
        display_string = """Current time is {}\nIn the past 24 hours:\nYour pet has traveled {} meters\nYour pet has made loud noises for {} times, in total {} sec.""".format(current_time, distance, audio_times, audio_period)
        
        self.text_display.config(state='normal')  # Enable editing to change the text
        self.text_display.delete(1.0, tk.END)  # Clear existing content in the text box
        self.text_display.insert(tk.END, display_string)  # Insert the new text
        self.text_display.config(state='disabled')  # Disable editing after updating
    
    def live_stream(self):
        webbrowser.open("http://131.179.32.244:8081/")


if __name__ == "__main__":
    gui = AIPetUserInterface()
    gui.run_interface()
