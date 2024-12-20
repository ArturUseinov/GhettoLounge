from tkinter import Tk, Canvas, Toplevel, Label, Button, Frame, Entry, StringVar, IntVar
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import math
import json

# Initialize the main window
window = Tk()
window.title("Ghetto Lounge Management System")
window.geometry("950x850")  # Set the desired size explicitly
window.configure(bg="#000000")  # Set background color

# Set minimum window size
window.minsize(950, 850)

# Add a canvas to draw elements
canvas = Canvas(window, bg="#000000", bd=0, highlightthickness=0)
canvas.place(x=0, y=0, relwidth=1, relheight=1)  # Use relative width and height to fill the window

# Helper function to create rounded rectangles
def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=20, color="#FFFFFF"):
    points = [
        x1 + radius, y1,
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, fill=color, outline="")

# Function to create styled popup buttons
def create_popup_button(parent, text, command, bg_color="#F725E5", fg_color="#FFFFFF", width=300, height=50):
    button_canvas = Canvas(parent, width=width, height=height, bg=parent["bg"], bd=0, highlightthickness=0)
    button_canvas.pack(pady=10)
    x1, y1, x2, y2 = 10, 10, width - 10, height - 10  # Define button size with margins
    button_id = create_rounded_rectangle(button_canvas, x1, y1, x2, y2, radius=20, color=bg_color)
    text_id = button_canvas.create_text(
        (x1 + x2) / 2, (y1 + y2) / 2,
        text=text,
        fill=fg_color,
        font=("Arial", 14, "bold")
    )
    # Bind click events to both the rectangle and text
    button_canvas.tag_bind(button_id, "<Button-1>", lambda e: command())
    button_canvas.tag_bind(text_id, "<Button-1>", lambda e: command())
    return button_canvas

# Load and resize the logo
try:
    logo_path = "assets/logo.png"
    logo_image = Image.open(logo_path)
    logo_image = logo_image.resize((150, 150), Image.LANCZOS)
    logo = ImageTk.PhotoImage(logo_image)
    canvas.create_image(50, 30, image=logo, anchor="nw")  # Place the logo
except FileNotFoundError:
    print("Logo image not found. Please check the path.")

# Add "Ghetto" text in pink
canvas.create_text(
    500, 60,
    anchor="e",
    text="Ghetto",
    fill="#DD1DC3",
    font=("Arial", 48, "bold")
)

# Add "Lounge" text in ice blue
canvas.create_text(
    510, 60,
    anchor="w",
    text="Lounge",
    fill="#1DC3DD",
    font=("Arial", 48, "bold")
)

# Add "Время и дата:" text placeholder
datetime_text = canvas.create_text(
    475, 140,
    anchor="center",
    text="Время: 00:00:00 | Дата: 01/01/2000",
    fill="#FFFFFF",
    font=("Arial", 24, "bold")
)

# Function to update date and time dynamically
def update_datetime():
    current_time = time.strftime("%H:%M:%S")
    current_date = time.strftime("%d/%m/%Y")
    canvas.itemconfig(datetime_text, text=f"Время: {current_time} | Дата: {current_date}")
    window.after(1000, update_datetime)

# Start updating date and time
update_datetime()

# Initialize session data (storing multiple sessions)
session_data = {}

def add_extra_service(button_data):
    # Popup to add a service
    service_popup = Toplevel(window)
    service_popup.title("Добавить услугу")
    service_popup.geometry("300x250")
    service_popup.configure(bg="#1C1C1C")
    service_popup.attributes("-topmost", True)

    Label(service_popup, text="Название услуги:", fg="white", bg="#1C1C1C", font=("Arial", 12)).pack(pady=5)
    service_name_var = StringVar()
    service_name_entry = Entry(service_popup, textvariable=service_name_var, font=("Arial", 12))
    service_name_entry.pack(pady=5)

    Label(service_popup, text="Стоимость (сум):\nПример: 100000 или 100,000 или 100.000", 
          fg="white", bg="#1C1C1C", font=("Arial", 10)).pack(pady=5)

    cost_var = StringVar()
    service_cost_entry = Entry(service_popup, textvariable=cost_var, font=("Arial", 12))
    service_cost_entry.pack(pady=5)

    def add_service():
        name = service_name_var.get().strip()
        raw_cost = cost_var.get().strip()
        
        if not name:
            messagebox.showwarning("Предупреждение", "Введите название услуги.")
            return
        
        # Remove commas and periods from the raw cost string
        cost_str = raw_cost.replace(",", "").replace(".", "")
        
        if not cost_str.isdigit():
            messagebox.showwarning("Предупреждение", "Введите корректную стоимость (только цифры и возможные запятые/точки).")
            return
        
        cost = int(cost_str)
        if cost <= 0:
            messagebox.showwarning("Предупреждение", "Введите корректную стоимость (больше нуля).")
            return

        # Append to extra services list
        if "extra_services" not in button_data:
            button_data["extra_services"] = []
        button_data["extra_services"].append({"Услуга": name, "Стоимость(сум)": cost})
        service_popup.destroy()

    create_popup_button(service_popup, "Добавить", add_service, bg_color="#3AA655")

    # Center the service popup
    service_popup.update_idletasks()
    sw = service_popup.winfo_width()
    sh = service_popup.winfo_height()
    sx = (window.winfo_screenwidth() // 2) - (sw // 2)
    sy = (window.winfo_screenheight() // 2) - (sh // 2)
    service_popup.geometry(f"{sw}x{sh}+{sx}+{sy}")

# Function to save session data to a file
def save_session_data():
    file_path = "Otchet.json"
    try:
        # Try to load existing data from the file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or is empty, start with an empty dictionary
            existing_data = {}

        # Merge sessions into existing_data
        for room, sessions in session_data.items():
            if room not in existing_data:
                existing_data[room] = []
            # sessions is a list of session infos
            existing_data[room].extend(sessions)

        # Save the updated data back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("Успех", "Данные успешно сохранены!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить данные.\n{e}")

# Function to open a popup window for room management
def open_room_popup(button_data):
    popup = Toplevel(window)
    popup.geometry("400x500+275+275")  # Increased height for extra button
    popup.configure(bg="#1C1C1C")
    popup.title(button_data["text"])

    # Make the pop-up window stay on top
    popup.attributes("-topmost", True)

    rate_per_hour = 70000 if "VIP" in button_data["text"] else 45000

    # Room name label
    Label(
        popup,
        text=button_data["text"],
        font=("Arial", 20, "bold"),
        fg="white",
        bg="#1C1C1C"
    ).pack(pady=10)

    # Session time label
    session_time_label = Label(
        popup,
        text="",
        font=("Arial", 16),
        fg="white",
        bg="#1C1C1C"
    )
    session_time_label.pack(pady=5)

    # Function to update session time
    def update_session_time():
        if button_data["status"] == "occupied":
            elapsed_time = time.time() - button_data["start_time"]
            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)
            session_time_label.config(
                text=f"Время с открытия: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            )
            session_time_label.after(1000, update_session_time)
        elif button_data["status"] == "reserved":
            session_time_label.config(
                text=f"Зарезервировано на: {button_data['reservation_time']}"
            )
        else:
            session_time_label.config(text="Кабинка свободна")

    # Start updating session time
    update_session_time()

    # Start session logic
    def start_session():
        if button_data["status"] == "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка уже занята!")
            return
        button_data["start_time"] = time.time()
        button_data["status"] = "occupied"
        button_data["extra_services"] = []
        canvas.itemconfig(button_data["id"], fill="#cf2400")  # Change color to red
        popup.destroy()

    # Reserve room logic
    def reserve_room():
        if button_data["status"] == "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка уже занята!")
            return
        reservation_time = time.strftime("%H:%M")
        button_data["status"] = "reserved"
        button_data["reservation_time"] = reservation_time
        canvas.itemconfig(button_data["id"], fill="#FFD700")  # Change color to gold
        popup.destroy()

    # Cancel reservation logic
    def cancel_reservation():
        if button_data["status"] != "reserved":
            messagebox.showwarning("Предупреждение", "Кабинка не зарезервирована!")
            return
        button_data["status"] = "vacant"
        del button_data["reservation_time"]
        canvas.itemconfig(button_data["id"], fill="#3AA655")  # Change color to green
        popup.destroy()

    # Stop session logic
    def stop_session():
        if button_data["status"] != "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка не занята!")
            return
        end_time = time.time()
        elapsed_time = end_time - button_data["start_time"]
        # Round up to nearest 15 minutes
        hours = math.ceil(elapsed_time / 900) * 0.25
        cost_for_time = int(hours * rate_per_hour)

        # Calculate total services cost
        total_services_cost = 0
        if "extra_services" in button_data:
            for srv in button_data["extra_services"]:
                total_services_cost += srv["Стоимость(сум)"]

        total_cost = cost_for_time + total_services_cost

        session_info = {
            "Кабинка": button_data["text"],
            "Время начала": time.strftime("%H:%M:%S", time.localtime(button_data["start_time"])),
            "Время окончания": time.strftime("%H:%M:%S", time.localtime(end_time)),
            "Длительность (часов)": hours,
            "Стоимость_времени(сум)": cost_for_time,
            "Дополнительные услуги": button_data.get("extra_services", []),
            "Итоговая_стоимость(сум)": total_cost,
            "Дата": time.strftime("%d/%m/%Y", time.localtime(end_time))
        }

        # Save session data in a list format for each room
        if button_data["text"] not in session_data:
            session_data[button_data["text"]] = []
        session_data[button_data["text"]].append(session_info)

        # Reset room status
        button_data["status"] = "vacant"
        canvas.itemconfig(button_data["id"], fill="#3AA655")  # Green

        popup.destroy()

        # Immediately save to JSON to prevent data loss
        save_session_data()

        # Clear session_data after saving to avoid duplication
        session_data.clear()

        # Create a custom billing window
        billing_window = Toplevel(window)
        billing_window.title("Биллинг")
        billing_window.geometry("400x300")  # Adjust the size as needed
        billing_window.configure(bg="#1C1C1C")
        billing_window.attributes("-topmost", True)

        Label(
            billing_window,
            text=f"Стоимость времени: {cost_for_time} сум",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#1C1C1C"
        ).pack(pady=5)

        # If there are extra services, list them
        if session_info["Дополнительные услуги"]:
            Label(
                billing_window,
                text="Дополнительные услуги:",
                font=("Arial", 14, "bold"),
                fg="white",
                bg="#1C1C1C"
            ).pack(pady=5)
            for srv in session_info["Дополнительные услуги"]:
                Label(
                    billing_window,
                    text=f"{srv['Услуга']}: {srv['Стоимость(сум)']} сум",
                    font=("Arial", 12),
                    fg="white",
                    bg="#1C1C1C"
                ).pack(pady=2)

        Label(
            billing_window,
            text=f"Общая стоимость: {total_cost} сум",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#1C1C1C"
        ).pack(pady=10)

        Label(
            billing_window,
            text=f"Время игры: {hours} часов",
            font=("Arial", 14),
            fg="white",
            bg="#1C1C1C"
        ).pack(pady=5)

        def close_billing_window():
            billing_window.destroy()

        create_popup_button(billing_window, "ОК", close_billing_window, bg_color="#F725E5")

        # Center the billing window
        billing_window.update_idletasks()
        bw = billing_window.winfo_width()
        bh = billing_window.winfo_height()
        bx = (window.winfo_screenwidth() // 2) - (bw // 2)
        by = (window.winfo_screenheight() // 2) - (bh // 2)
        billing_window.geometry(f"{bw}x{bh}+{bx}+{by}")

    # Back button
    def go_back():
        popup.destroy()

    # Buttons based on room status
    if button_data["status"] == "vacant":
        create_popup_button(popup, "Открыть кабинку", start_session, bg_color="#3AA655")
        create_popup_button(popup, "Зарезервировать кабинку", reserve_room, bg_color="#FFA500")
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5")
    elif button_data["status"] == "occupied":
        create_popup_button(popup, "Закрыть кабинку", stop_session, bg_color="#cf2400")
        # Add "Добавить к заказу" button
        create_popup_button(popup, "Добавить к заказу", lambda: add_extra_service(button_data), bg_color="#3AA655")
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5")
    elif button_data["status"] == "reserved":
        create_popup_button(popup, "Открыть кабинку", start_session, bg_color="#3AA655")
        create_popup_button(popup, "Отменить резерв", cancel_reservation, bg_color="#FFA500")
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5")

    # Center the popup window
    popup.update_idletasks()
    popup_width = popup.winfo_width()
    popup_height = popup.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (popup_width // 2)
    y = (window.winfo_screenheight() // 2) - (popup_height // 2)
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

# Define button details
buttons = [
    {"text": "Кабинка №1", "status": "vacant", "size": "normal", "start_time": None},
    {"text": "Кабинка №2", "status": "vacant", "size": "normal", "start_time": None},
    {"text": "Кабинка №3", "status": "vacant", "size": "normal", "start_time": None},
    {"text": "Кабинка №4", "status": "vacant", "size": "normal", "start_time": None},
    {"text": "Кабинка №5", "status": "vacant", "size": "normal", "start_time": None},
    {"text": "Кабинка №6", "status": "vacant", "size": "normal", "start_time": None},
    {"text": "Кабинка №7", "status": "vacant", "size": "normal", "start_time": None},
    {"text": "Кабинка №8", "status": "vacant", "size": "normal", "start_time": None},
    {"text": "VIP-Кабинка 1", "status": "vacant", "size": "large", "start_time": None},
    {"text": "VIP-Кабинка 2", "status": "vacant", "size": "large", "start_time": None}
]

# Adjusted button layout details
button_width, button_height = 180, 70  # Default button size
vip_width, vip_height = 380, 70  # VIP button size
x_start, y_start = 100, 250  # Starting position
x_spacing, y_spacing = 200, 100  # Spacing between normal buttons

# Create buttons dynamically
for i, button in enumerate(buttons):
    if button["size"] == "normal":
        col = i % 4  # Determine column
        row = i // 4  # Determine row
        x1 = x_start + col * x_spacing
        y1 = y_start + row * y_spacing
        x2 = x1 + button_width
        y2 = y1 + button_height
    else:
        col = i % 2
        x1 = x_start + col * (vip_width + 20)
        y1 = y_start + 2 * y_spacing  # Adjusted for VIP cabins
        x2 = x1 + vip_width
        y2 = y1 + vip_height

    # Set color based on status
    if button["status"] == "vacant":
        color = "#3AA655"  # Green
    elif button["status"] == "occupied":
        color = "#cf2400"  # Red
    elif button["status"] == "reserved":
        color = "#FFD700"  # Gold

    button_id = create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=15, color=color)
    button["id"] = button_id

    # Add button text and bind its click to the same functionality
    text_id = canvas.create_text(
        (x1 + x2) / 2,
        (y1 + y2) / 2,
        text=button["text"],
        fill="#FFFFFF",
        font=("Arial", 16, "bold")
    )
    # Bind click events to both the button and its text
    canvas.tag_bind(button_id, "<Button-1>", lambda e, b=button: open_room_popup(b))
    canvas.tag_bind(text_id, "<Button-1>", lambda e, b=button: open_room_popup(b))

# Exit and Save function
def exit_and_save():
    # Since we save sessions at room close, session_data should be empty now.
    # If there's anything left in session_data (e.g. unsaved), it will save now.
    if session_data:
        save_session_data()
        session_data.clear()
    window.destroy()

# Add "Выйти и сохранить" button with functionality
exit_button_id = create_rounded_rectangle(canvas, 375, 720, 575, 790, radius=15, color="#F725E5")
exit_text_id = canvas.create_text(475, 755, text="Выйти и сохранить", fill="#FFFFFF", font=("Arial", 20, "bold"))
canvas.tag_bind(exit_button_id, "<Button-1>", lambda e: exit_and_save())
canvas.tag_bind(exit_text_id, "<Button-1>", lambda e: exit_and_save())

# Reapply the window geometry after all widgets are added
window.update_idletasks()
window.geometry("950x850")

# Start the Tkinter main loop
window.mainloop()
