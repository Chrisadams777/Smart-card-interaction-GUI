import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from smartcard import readers
from smartcard.util import toHexString
import os
import json

# Global variables
selected_device = None
selected_card_type = None
error_handling_level = "detailed"
apdu_commands = {
    "SELECT": [0x00, 0xA4, 0x04, 0x00, 0x0E],  # Select command
    "READ_RECORD": [0x00, 0xB2, 0x01, 0x0C, 0x00],  # Read Record command
    "WRITE_BINARY": [0x00, 0xD6, 0x00, 0x00, 0x02, 0x01, 0x02],  # Write Binary command with example data
    "GET_RESPONSE": [0x00, 0xC0, 0x00, 0x00, 0x0A],  # Get Response command
    "VERIFY_PIN": [0x00, 0x20, 0x00, 0x80, 0x08] + [0x12, 0x34, 0x56, 0x78, 0x90, 0x12, 0x34, 0x56],  # Example PIN
    # Additional APDU commands for common operations
}

# Function to initialize the selected device
def initialize_device(device_name):
    global selected_device
    available_readers = readers()
    
    for reader in available_readers:
        if device_name in reader.name:
            selected_device = reader
            output_text.insert(tk.END, f"Selected device: {device_name}\n")
            return
    
    messagebox.showerror("Error", "Device not found.")

# Function to handle card operations
def perform_card_operation(operation):
    try:
        card = selected_device.createConnection()
        card.connect()
        
        if operation == "read":
            data = read_card_data(card, selected_card_type)
            output_text.insert(tk.END, f"Read Data: {data}\n")
        elif operation == "write":
            data_to_write = [int(i) for i in data_entry.get().split()]  # User-provided data
            write_card_data(card, selected_card_type, data_to_write)
            output_text.insert(tk.END, "Write operation complete.\n")
        elif operation == "emulate":
            transaction_type = transaction_var.get()
            emulate_pos_transaction(card, transaction_type)
            output_text.insert(tk.END, f"{transaction_type.capitalize()} transaction complete.\n")
        elif operation == "java_card":
            interact_with_java_card(card, operation="emulate_payment_card")
            output_text.insert(tk.END, "Java Card operation complete.\n")
        elif operation == "custom_apdu":
            custom_apdu = [int(i, 16) for i in apdu_entry.get().split()]  # User-provided APDU
            response = send_apdu_command(card, custom_apdu)
            output_text.insert(tk.END, f"APDU Response: {response}\n")
        elif operation == "brute_force":
            brute_force_mifare(card)
    except Exception as e:
        handle_error(e)

# Function to toggle error handling
def toggle_error_handling():
    global error_handling_level
    if error_handling_var.get():
        error_handling_level = "detailed"
    else:
        error_handling_level = "simple"
    output_text.insert(tk.END, f"Error handling set to: {error_handling_level}\n")

# Function to handle errors
def handle_error(error_message):
    if error_handling_level == "detailed":
        output_text.insert(tk.END, f"Error: {error_message}\n")
    else:
        output_text.insert(tk.END, "An error occurred. Please try again.\n")

# Function to send APDU command
def send_apdu_command(card, apdu_command):
    try:
        connection = card.createConnection()
        connection.connect()
        response, sw1, sw2 = connection.transmit(apdu_command)
        if sw1 == 0x90 and sw2 == 0x00:
            return toHexString(response)
        else:
            handle_error(f"APDU command failed with status words {sw1:X} {sw2:X}")
    except Exception as e:
        handle_error(e)

# Function to read data from the card
def read_card_data(card, card_type):
    if card_type == "MIFARE":
        apdu_command = [0xFF, 0xB0, 0x00, 0x04, 0x10]  # Read 16 bytes from block 4
        return send_apdu_command(card, apdu_command)
    elif card_type == "NDEF":
        apdu_command = [0x00, 0xB0, 0x00, 0x00, 0x20]  # Example APDU for reading NDEF tags
        return send_apdu_command(card, apdu_command)
    elif card_type == "Payment Card":
        apdu_command = [0x00, 0xB2, 0x01, 0x0C, 0x00]  # Example APDU for reading payment card data
        return send_apdu_command(card, apdu_command)
    else:
        raise ValueError("Unsupported card type.")

# Function to write data to the card
def write_card_data(card, card_type, data):
    if card_type == "MIFARE":
        apdu_command = [0xFF, 0xD6, 0x00, 0x04, len(data)] + data
        return send_apdu_command(card, apdu_command)
    elif card_type == "NDEF":
        apdu_command = [0x00, 0xD6, 0x00, 0x00, len(data)] + data  # Write data to NDEF tag
        return send_apdu_command(card, apdu_command)
    elif card_type == "Payment Card":
        apdu_command = [0x00, 0xD6, 0x00, 0x00, len(data)] + data  # Example APDU for writing payment card data
        return send_apdu_command(card, apdu_command)
    else:
        raise ValueError("Unsupported card type.")

# Function to emulate POS transaction
def emulate_pos_transaction(card, transaction_type):
    if transaction_type == "credit":
        apdu_command = [0x00, 0xA4, 0x04, 0x00, 0x0E]
    elif transaction_type == "debit":
        apdu_command = [0x00, 0xA4, 0x04, 0x00, 0x0F]
    elif transaction_type == "loyalty":
        apdu_command = [0x00, 0xA4, 0x04, 0x00, 0x10]
    elif transaction_type == "gift":
        apdu_command = [0x00, 0xA4, 0x04, 0x00, 0x11]
    elif transaction_type == "tap-to-pay":
        apdu_command = [0x00, 0xA4, 0x04, 0x00, 0x12]
    else:
        raise ValueError("Unsupported transaction type.")
    send_apdu_command(card, apdu_command)

# Function to interact with Java Card
def interact_with_java_card(card, operation):
    if operation == "emulate_payment_card":
        select_applet_command = [0x00, 0xA4, 0x04, 0x00, 0x0A]
        send_apdu_command(card, select_applet_command)
        
        # Example: Emulate a payment transaction on Java Card
        transaction_command = [0x00, 0xB2, 0x01, 0x0C, 0x00]
        send_apdu_command(card, transaction_command)
        output_text.insert(tk.END, "Payment card emulation complete.\n")
    elif operation == "custom_applet":
        # Example: Flash a custom Java applet
        applet_binary = [0xC9, 0x01, 0x02, 0x03]  # Replace with actual binary data
        install_applet_command = [0x80, 0xE6, 0x02, 0x00, len(applet_binary)] + applet_binary
        send_apdu_command(card, install_applet_command)
        output_text.insert(tk.END, "Custom Java applet flashed successfully.\n")

# Brute-force utility for MIFARE cards
def brute_force_mifare(card):
    output_text.insert(tk.END, "Starting brute-force on MIFARE card...\n")
    # Example brute-force logic
    for block in range(0x00, 0x10):
        apdu_command = [0xFF, 0xB0, 0x00, block, 0x10]
        response = send_apdu_command(card, apdu_command)
        output_text.insert(tk.END, f"Block {block:02X}: {response}\n")
    output_text.insert(tk.END, "Brute-force complete.\n")

# Save data to file
def save_data():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        try:
            data = {"device": selected_device.name, "card_type": selected_card_type}
            with open(file_path, "w") as file:
                json.dump(data, file)
            output_text.insert(tk.END, f"Data saved to {file_path}\n")
        except Exception as e:
            handle_error(e)

# Load data from file
def load_data():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if file_path:
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
            output_text.insert(tk.END, f"Loaded data: {data}\n")
        except Exception as e:
            handle_error(e)

# GUI Setup
root = tk.Tk()
root.title("Smart Card Interaction GUI")
root.geometry("800x600")

# Device Selection
device_label = tk.Label(root, text="Select Device:")
device_label.pack(pady=5)
device_var = tk.StringVar()
device_dropdown = ttk.Combobox(root, textvariable=device_var)
device_dropdown['values'] = ("ACR122U", "Omnikey 3021")
device_dropdown.pack(pady=5)
device_dropdown.current(0)

def on_device_select(event):
    initialize_device(device_var.get())

device_dropdown.bind("<<ComboboxSelected>>", on_device_select)

# Card Type Selection
card_type_label = tk.Label(root, text="Select Card Type:")
card_type_label.pack(pady=5)
card_type_var = tk.StringVar()
card_type_dropdown = ttk.Combobox(root, textvariable=card_type_var)
card_type_dropdown['values'] = ("Payment Card", "MIFARE", "NDEF")
card_type_dropdown.pack(pady=5)
card_type_dropdown.current(0)

def on_card_type_select(event):
    global selected_card_type
    selected_card_type = card_type_var.get()
    output_text.insert(tk.END, f"Selected card type: {selected_card_type}\n")

card_type_dropdown.bind("<<ComboboxSelected>>", on_card_type_select)

# Buttons for operations
read_button = tk.Button(root, text="Read Data", command=lambda: perform_card_operation("read"))
read_button.pack(pady=5)

write_button = tk.Button(root, text="Write Data", command=lambda: perform_card_operation("write"))
write_button.pack(pady=5)

data_entry_label = tk.Label(root, text="Data to Write (space-separated bytes):")
data_entry_label.pack(pady=5)
data_entry = tk.Entry(root, width=50)
data_entry.pack(pady=5)

emulate_button = tk.Button(root, text="Emulate POS Transaction", command=lambda: perform_card_operation("emulate"))
emulate_button.pack(pady=5)

transaction_label = tk.Label(root, text="Select Transaction Type:")
transaction_label.pack(pady=5)
transaction_var = tk.StringVar()
transaction_dropdown = ttk.Combobox(root, textvariable=transaction_var)
transaction_dropdown['values'] = ("credit", "debit", "loyalty", "gift", "tap-to-pay")
transaction_dropdown.pack(pady=5)
transaction_dropdown.current(0)

java_button = tk.Button(root, text="Java Card Interaction", command=lambda: perform_card_operation("java_card"))
java_button.pack(pady=5)

apdu_label = tk.Label(root, text="Custom APDU Command (space-separated hex bytes):")
apdu_label.pack(pady=5)
apdu_entry = tk.Entry(root, width=50)
apdu_entry.pack(pady=5)

custom_apdu_button = tk.Button(root, text="Send Custom APDU", command=lambda: perform_card_operation("custom_apdu"))
custom_apdu_button.pack(pady=5)

brute_force_button = tk.Button(root, text="Brute-Force MIFARE", command=lambda: perform_card_operation("brute_force"))
brute_force_button.pack(pady=5)

# Error Handling Toggle
error_handling_var = tk.BooleanVar(value=True)
error_handling_checkbox = tk.Checkbutton(root, text="Detailed Error Handling", variable=error_handling_var, command=toggle_error_handling)
error_handling_checkbox.pack(pady=5)

# Save and Load Data
save_button = tk.Button(root, text="Save Data", command=save_data)
save_button.pack(pady=5)

load_button = tk.Button(root, text="Load Data", command=load_data)
load_button.pack(pady=5)

# Output Text Area
output_label = tk.Label(root, text="Output:")
output_label.pack(pady=5)
output_text = tk.Text(root, height=15, width=80)
output_text.pack(pady=5)

# Run the GUI
root.mainloop()
