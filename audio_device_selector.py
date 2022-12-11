import sys
import subprocess

try:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.messagebox
except:
    print("\nPlease install Tkinter. Check:")
    print("  -> https://stackoverflow.com/a/66292120/2256056\n")
    exit(1) 



# Run the "pactl list short sources" command and store the output in a variable
devices = subprocess.getoutput([" pw-link -lio"])
devices_lines = devices.strip().split("\n")

# Filter the list to only include lines that contain the word "input"
input_devices = []
output_devices = []

input_devices_line_max_length = 0
output_devices_line_max_length = 0

for line in devices_lines:
    line_length = len(line)
    if "input" in line:
        input_devices.append(line)
        if line_length > input_devices_line_max_length:
            input_devices_line_max_length = line_length
    if "output" in line:
        output_devices.append(line)
        if line_length > output_devices_line_max_length:
            output_devices_line_max_length = line_length


class AudioDeviceSelector(tk.Tk):
    def __init__(self):
        super().__init__()

        # root window
        self.title('Soundbox Device Chooser')
        self.geometry('225x200')
        self.style = ttk.Style(self)
        
        self.style.configure('TCombobox', postoffset=(0,0,max(output_devices_line_max_length, input_devices_line_max_length) * 6,0))

        label_input = ttk.Label(self, text='Input Device:', width=20)
        label_input.grid(column=0, row=0, padx=10, pady=0,  sticky='w')
        
        combo1 = ttk.Combobox(self)
        combo1["values"] = input_devices
        combo1.grid(column=0, row=1, padx=15, pady=10, sticky='w')

        label_output = ttk.Label(self, text='Output Device:', width=20)
        label_output.grid(column=0, row=2, padx=10, pady=0,  sticky='w')

        combo2 = ttk.Combobox(self)
        combo2["values"] = output_devices
        combo2.grid(column=0, row=3, padx=15, pady=10, sticky='w')

        # create a variable to store the selected values
        selected = {"combo1": None, "combo2": None}

        # define a function to be called when the combo box changes
        def combo_change(event, name):
        # store the current value in the selected variable
            if event.widget.get():
                selected[name] = event.widget.get()

                if selected["combo1"] and selected["combo2"]:
                    button["state"] = "normal"

        # define a function to be called when the button is clicked
        def save_values():
        # open the file for writing
            with open("target_soundbox_audio_devices.txt", "w") as f:
                # write the values to the file
                input_val = selected["combo1"]
                output_val = selected["combo2"]
                f.write(input_val + "\n" + output_val)
                tkinter.messagebox.showinfo(title="Success!", message="Audio device names saved. Bye!")
                self.destroy()

        # bind the change event of the first combo box to the function
        combo1.bind("<<ComboboxSelected>>", lambda event: combo_change(event, "combo1"))

        # bind the change event of the second combo box to the function
        combo2.bind("<<ComboboxSelected>>", lambda event: combo_change(event, "combo2"))

        # create a button
        button = tk.Button(self, text="Save", command=save_values, width=20)
        button["state"] = "disabled"
        button.grid(column=0, row=4, padx=10, pady=10, sticky='w')
        self.mainloop()


if __name__ == "__main__":
    AudioDeviceSelector()