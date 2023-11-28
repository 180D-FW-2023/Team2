import tkinter as tk
from time import strftime, localtime

class AIPetUserInterface:
    display_string = "Hello world!"  # Your initial string content
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AIPet Monitor")

        # Setting window size to 800x600
        self.root.geometry("800x600")

        # Title
        self.title_label = tk.Label(self.root, text="AIPet Monitor", font=("Helvetica", 24))
        self.title_label.place(relx=0.5, y=50, anchor=tk.CENTER)  # Centering the title

        # Text display box
        self.text_display = tk.Text(self.root, height=10, width=50, font=("Helvetica", 20))
        self.text_display.insert(tk.END, self.display_string)  # Display the initial string
        self.text_display.config(state='disabled')  # Disable editing
        self.text_display.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # Centering the text box

        # Current time display
        self.time_label = tk.Label(self.root, font=("Helvetica", 12))
        self.time_label.place(relx=1.0, rely=0.0, anchor=tk.NE, x=-10, y=10)  # Placing time label in upper right corner

    def update_time(self):
        current_time = strftime('%m/%d/%Y %H:%M', localtime())
        self.time_label.config(text=current_time)
        self.time_label.after(1000, self.update_time)

    def run_interface(self):
        self.update_time()
        self.root.mainloop()

if __name__ == "__main__":
    gui = AIPetUserInterface()
    gui.run_interface()
