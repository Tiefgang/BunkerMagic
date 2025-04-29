import tkinter as tk
from tkinter import ttk
import threading

from tools import load_devices, save_devices, ping_device
from artnet import ArtNetController

# GUI class
class DeviceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Device Monitor")
        self.root.attributes('-fullscreen', True)

        self.tab_control = ttk.Notebook(root)
        self.devices_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.devices_tab, text="Devices")

        columns = ("MAC", "IP", "Name", "Rows", "Columns", "Selected", "Status")
        self.tree = ttk.Treeview(self.devices_tab, columns=columns, show="headings", height=10)
        column_widths = {
            "MAC": 150,
            "IP": 120,
            "Name": 100,
            "Rows": 80,
            "Columns": 80,
            "Selected": 80,
            "Status": 100
        }

        ## Track the currently active device and its ArtNetController
        self.active_controller = None
        self.active_device_mac = None

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[col], anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_item_double_click)

        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.save_button = tk.Button(button_frame, text="Save Changes", command=self.save_changes)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = tk.Button(button_frame, text="Exit", command=self.close_app)
        self.exit_button.pack(side=tk.RIGHT, padx=5)

        self.tab_control.pack(expand=1, fill="both")
        self.start_monitoring()

    def update_device_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        devices = load_devices()
        for mac, info in devices.items():
            ip = info.get("ip", "Unknown")
            name = info.get("name", "")
            rows = info.get("rows", 0)
            columns = info.get("columns", 0)
            selected = info.get("selected", False)
            item_id = self.tree.insert("", "end",
                                       values=(mac, ip, name, rows, columns, "✔" if selected else "✘", "Unknown"))

            self.tree.bind("<ButtonRelease-1>", self.toggle_selected)  # Handle selection toggle

    def toggle_selected(self, event):
        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)

        if column_id == "#6":  # "Selected" column index
            values = list(self.tree.item(item_id, "values"))
            mac = values[0]

            devices = load_devices()
            if mac in devices:
                current_state = devices[mac].get("selected", False)
                devices[mac]["selected"] = not current_state
                values[5] = "✔" if not current_state else "✘"  # Toggle UI display
                self.tree.item(item_id, values=values)
                save_devices(devices)

    def save_changes(self):
        devices = load_devices()
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            mac, ip, name, rows, columns, selected = values[0], values[1], values[2], int(values[3]), int(values[4]), \
            values[5]
            if mac in devices:
                devices[mac]["ip"] = ip
                devices[mac]["name"] = name
                devices[mac]["rows"] = rows
                devices[mac]["columns"] = columns
                devices[mac]["selected"] = selected
        save_devices(devices)

    def on_item_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)

        if not item_id:  # Ensure a row is clicked
            return

        col_index = int(column_id.strip("#")) - 1  # Convert column to index

        # Start controller only if clicking on MAC (col 0) or IP (col 1)
        if col_index not in (0, 1):
            return

        values = self.tree.item(item_id, "values")
        mac = values[0]  # Extract MAC address (unique device identifier)

        devices = load_devices()
        if mac not in devices:
            return  # Safety check

        # Stop the previous controller if a different device is clicked
        if self.active_device_mac and self.active_device_mac != mac:
            if self.active_controller:
                self.active_controller.stop()
            self.active_controller = None
            self.active_device_mac = None

        # Start a new ArtNetController for the clicked device
        config = {
            "ip": devices[mac]["ip"],
            "rows": devices[mac]["rows"],
            "columns": devices[mac]["columns"],
        }
        self.active_device_mac = mac
        self.active_controller = ArtNetController(config)
        self.active_controller.start()

    def open_touchscreen_numpad(self, current_value):
        popup = tk.Toplevel(self.root)
        popup.title("Enter Value")
        popup.geometry("300x400")

        popup.transient(self.root)  # Ensure it stays on top
        popup.update_idletasks()  # Allow Tkinter to finish rendering
        popup.grab_set()  # Apply grab after rendering

        value = tk.StringVar(value=str(int(current_value)) if str(current_value).isdigit() else "0")
        entry = tk.Entry(popup, textvariable=value, font=("Arial", 24), justify="center")
        entry.pack(pady=10)

        button_frame = tk.Frame(popup)
        button_frame.pack()

        def append_number(num):
            new_val = value.get() + str(num)
            value.set(str(int(new_val)))  # Remove leading zero

        def clear_value():
            value.set("")

        for i in range(3):
            for j in range(3):
                num = i * 3 + j + 1
                tk.Button(button_frame, text=str(num), command=lambda n=num: append_number(n), width=5, height=2).grid(
                    row=i, column=j)

        tk.Button(button_frame, text="0", command=lambda: append_number(0), width=5, height=2).grid(row=3, column=1)

        # Create bottom row for "Clear" and "OK" buttons
        bottom_frame = tk.Frame(popup)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="Clear", command=clear_value, width=10, height=2).pack(side=tk.LEFT, padx=10)
        tk.Button(bottom_frame, text="OK", command=popup.destroy, width=10, height=2).pack(side=tk.RIGHT, padx=10)

        popup.wait_window()
        return value.get()

    def open_touchscreen_keyboard(self, current_value):
        popup = tk.Toplevel(self.root)
        popup.title("Enter Name")
        popup.geometry("400x500")

        popup.transient(self.root)
        popup.update_idletasks()
        popup.grab_set()

        value = tk.StringVar(value=str(current_value))
        entry = tk.Entry(popup, textvariable=value, font=("Arial", 24), justify="center")
        entry.pack(pady=10)

        button_frame = tk.Frame(popup)
        button_frame.pack()

        def append_letter(letter):
            value.set(value.get() + letter)

        def clear_value():
            value.set("")

        letters = [
            "QWERTYUIOP",
            "ASDFGHJKL",
            "ZXCVBNM"
        ]

        for row_index, row in enumerate(letters):
            for col_index, letter in enumerate(row):
                tk.Button(button_frame, text=letter, command=lambda l=letter: append_letter(l),
                          width=5, height=2).grid(row=row_index, column=col_index)

        tk.Button(button_frame, text="Clear", command=clear_value, width=10, height=2).grid(row=3, column=0,
                                                                                            columnspan=5)
        tk.Button(button_frame, text="OK", command=popup.destroy, width=10, height=2).grid(row=3, column=5,
                                                                                           columnspan=5)

        popup.wait_window()
        return value.get()

    def close_app(self):
        exit(0)

    def start_monitoring(self):
        self.update_device_list()
        threading.Thread(target=self.monitor_devices, daemon=True).start()

    def monitor_devices(self):
        devices = load_devices()
        for item in self.tree.get_children():
            mac = self.tree.item(item, "values")[0]
            ip = devices.get(mac, {}).get("ip", "Unknown")
            status = "Active" if ping_device(ip) else "Inactive"
            print(f"device {ip} set to {status}")
            devices[mac]["status"] = status
            self.tree.item(item, values=(mac, ip, self.tree.item(item, "values")[2], self.tree.item(item, "values")[3],
                                         self.tree.item(item, "values")[4], self.tree.item(item, "values")[5], status))
            self.tree.tag_configure("Active", foreground="green")
            self.tree.tag_configure("Inactive", foreground="white", background="red")
            self.tree.item(item, tags=(status,))
        self.root.after(5000, self.monitor_devices)  # Refresh every 5 seconds
