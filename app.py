import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
import os

API_URL = 'http://127.0.0.1:5000'
DATA_FILE = 'data.json'

def load_user_id():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
            return data.get('user_id')
    return None

def save_user_id(user_id):
    with open(DATA_FILE, 'w') as file:
        json.dump({'user_id': user_id}, file)

root = tk.Tk()
root.title("SahyogCareForYou Attendance")
root.geometry("400x500")
root.configure(bg='#f0f0f0')
root.resizable(False, False)

style = ttk.Style()
style.theme_use('clam')
style.configure('TLabel', background='#f0f0f0', font=('Arial', 12))
style.configure('TEntry', font=('Arial', 12))
style.configure('TButton', font=('Arial', 12, 'bold'), padding=10)
style.configure('TFrame', background='#f0f0f0')

logo = tk.PhotoImage(file="logo.png")
logo_label = tk.Label(root, image=logo, bg='#f0f0f0')
logo_label.pack(pady=(20, 10))

main_frame = ttk.Frame(root, padding="20 10 20 20")
main_frame.pack(fill=tk.BOTH, expand=True)

manager_dropdown = tk.StringVar()

def fetch_managers():
    response = requests.get(f'{API_URL}/managers')
    if response.status_code == 200:
        managers = response.json()
        manager_menu['menu'].delete(0, 'end')
        for manager in managers:
            manager_menu['menu'].add_command(label=manager['fullname'],
                                             command=tk._setit(manager_dropdown, manager['id']))

def register_user():
    fullname = name_entry.get()
    manager_id = manager_dropdown.get()

    if not fullname or not manager_id:
        messagebox.showerror("Error", "All fields are required!")
        return

    data = {"fullname": fullname, "manager_id": manager_id}
    response = requests.post(f'{API_URL}/register', json=data)

    if response.status_code == 200:
        user_data = response.json()
        save_user_id(user_data['user_id'])
        messagebox.showinfo("Success", "User Registered")
        show_checkin_checkout_buttons()
    else:
        messagebox.showerror("Error", response.json().get('error'))

def show_checkin_checkout_buttons():
    user_id = load_user_id()

    if user_id:
        for widget in main_frame.winfo_children():
            widget.destroy()

        checkin_button = ttk.Button(main_frame, text="Check In", command=lambda: check_in(user_id), width=15)
        checkout_button = ttk.Button(main_frame, text="Check Out", command=lambda: check_out(user_id), width=15)

        checkin_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        checkout_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Check if user has already checked in today and disable the button
        checkin_status = check_if_checked_in_today(user_id)
        if checkin_status:
            checkin_button.state(['disabled'])

def check_if_checked_in_today(user_id):
    response = requests.get(f"{API_URL}/checkin_status/{user_id}")

    if response.status_code == 200:
        return response.json().get('checked_in')
    return False

def check_in(user_id):
    data = {"user_id": user_id}
    response = requests.post(f"{API_URL}/checkin", json=data)

    if response.status_code == 200:
        messagebox.showinfo("Check-in", "Checked in successfully!")
        for child in main_frame.winfo_children():
            if child['text'] == "Check In":
                child.state(['disabled'])
    else:
        messagebox.showerror("Error", response.json().get('error'))

def check_out(user_id):
    data = {"user_id": user_id}
    response = requests.post(f"{API_URL}/checkout", json=data)

    if response.status_code == 200:
        messagebox.showinfo("Check-out", "Checked out successfully!")
        for child in main_frame.winfo_children():
            if child['text'] == "Check In":
                child.state(['!disabled'])
    else:
        messagebox.showerror("Error", response.json().get('error'))

name_label = ttk.Label(main_frame, text="Full Name")
name_entry = ttk.Entry(main_frame, width=30)
manager_label = ttk.Label(main_frame, text="Select Manager")
manager_menu = ttk.OptionMenu(main_frame, manager_dropdown, "Fetching managers...")
register_button = ttk.Button(main_frame, text="Register", command=register_user)

name_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
name_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
manager_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
manager_menu.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
register_button.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))

main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

user_id = load_user_id()
if user_id:
    show_checkin_checkout_buttons()
else:
    fetch_managers()

root.mainloop()