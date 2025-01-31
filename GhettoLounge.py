from tkinter import Tk, Canvas, Toplevel, Label, Frame, Entry, StringVar, IntVar, Spinbox, Listbox, SINGLE
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
canvas.place(x=0, y=0, relwidth=1, relheight=1)  # Fill the entire window

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
    """
    Creates a custom-styled button using a Canvas for rounded corners,
    then binds a command to the entire Canvas region.
    """
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

def update_datetime():
    current_time = time.strftime("%H:%M:%S")
    current_date = time.strftime("%d/%m/%Y")
    canvas.itemconfig(datetime_text, text=f"Время: {current_time} | Дата: {current_date}")
    window.after(1000, update_datetime)

update_datetime()

# Initialize session data (storing multiple sessions)
session_data = {}
buttons = []

###############################################################################
# Saving and forcibly closing logic
###############################################################################
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
            existing_data[room].extend(sessions)

        # Save the updated data back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("Успех", "Данные успешно сохранены!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить данные.\n{e}")

def forcibly_stop_session(button_data):
    """Closes an occupied cabin forcibly and logs its session info."""
    if button_data["status"] == "occupied":
        rate_per_hour = 70000 if "VIP" in button_data["text"] else 45000
        end_time = time.time()
        elapsed_time = end_time - button_data["start_time"]
        hours = math.ceil(elapsed_time / 900) * 0.25
        cost_for_time = int(hours * rate_per_hour)

        total_services_cost = 0
        if "extra_services" in button_data and button_data["extra_services"]:
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
            "Дата": time.strftime("%d/%m/%Y", time.localtime(end_time)),
            "Комментарий": button_data.get("reservation_comment", "")
        }

        # Store in session_data
        if button_data["text"] not in session_data:
            session_data[button_data["text"]] = []
        session_data[button_data["text"]].append(session_info)

        # Reset the cabin’s state
        button_data["status"] = "vacant"
        for key in ["reservation_time", "extra_services", "reservation_comment", "start_time"]:
            if key in button_data:
                button_data.pop(key, None)

        canvas.itemconfig(button_data["id"], fill="#3AA655")

def forcibly_close_all_rooms():
    """Forcibly closes all occupied cabins."""
    any_occupied = False
    for b in buttons:
        if b["status"] == "occupied":
            any_occupied = True
            forcibly_stop_session(b)
    return any_occupied

###############################################################################
# Pop-up #1: "Добавить услугу"
###############################################################################
def add_extra_service(parent_window, button_data):
    service_popup = Toplevel(parent_window)
    service_popup.title("Добавить услугу")
    service_popup.geometry("300x250")
    service_popup.configure(bg="#1C1C1C")

    # Make it modal-like
    service_popup.transient(parent_window)
    service_popup.grab_set()
    service_popup.focus_force()

    Label(service_popup, text="Название услуги:", fg="white", bg="#1C1C1C", font=("Arial", 12)).pack(pady=5)
    service_name_var = StringVar()
    service_name_entry = Entry(service_popup, textvariable=service_name_var, font=("Arial", 12))
    service_name_entry.pack(pady=5)

    Label(service_popup, text="Стоимость (сум):\nПример: 100000 или 100,000 или 100.000",
          fg="white", bg="#1C1C1C", font=("Arial", 10)).pack(pady=5)

    cost_var = StringVar()
    service_cost_entry = Entry(service_popup, textvariable=cost_var, font=("Arial", 12))
    service_cost_entry.pack(pady=5)

    def add_service_action():
        name = service_name_var.get().strip()
        raw_cost = cost_var.get().strip()
        if not name:
            messagebox.showwarning("Предупреждение", "Введите название услуги.")
            return

        # Remove commas/dots so that "100,000" -> "100000" or "100.000" -> "100000"
        cost_str = raw_cost.replace(",", "").replace(".", "")
        if not cost_str.isdigit():
            messagebox.showwarning("Предупреждение", 
                                   "Введите корректную стоимость (только цифры и возможные запятые/точки).")
            return

        cost = int(cost_str)
        if cost <= 0:
            messagebox.showwarning("Предупреждение", "Введите корректную стоимость (больше нуля).")
            return

        if "extra_services" not in button_data or not button_data["extra_services"]:
            button_data["extra_services"] = []
        button_data["extra_services"].append({"Услуга": name, "Стоимость(сум)": cost})
        service_popup.destroy()

    create_popup_button(service_popup, "Добавить", add_service_action, bg_color="#3AA655")

    # Center on screen
    service_popup.update_idletasks()
    sw = service_popup.winfo_width()
    sh = service_popup.winfo_height()
    sx = (window.winfo_screenwidth() // 2) - (sw // 2)
    sy = (window.winfo_screenheight() // 2) - (sh // 2)
    service_popup.geometry(f"{sw}x{sh}+{sx}+{sy}")

###############################################################################
# Pop-up #2: "Убрать из заказа"
###############################################################################
def remove_extra_service(parent_window, button_data):
    if "extra_services" not in button_data or not button_data["extra_services"]:
        messagebox.showinfo("Информация", "Нет дополнительных услуг для удаления.")
        return

    remove_popup = Toplevel(parent_window)
    remove_popup.title("Убрать из заказа")
    remove_popup.geometry("300x300")
    remove_popup.configure(bg="#1C1C1C")

    # Make it modal-like
    remove_popup.transient(parent_window)
    remove_popup.grab_set()
    remove_popup.focus_force()

    Label(remove_popup, text="Выберите услугу для удаления:", 
          fg="white", bg="#1C1C1C", font=("Arial", 12)).pack(pady=5)

    # Create a list of unique (name, cost) combos
    unique_services = []
    for srv in button_data["extra_services"]:
        combo = (srv["Услуга"], srv["Стоимость(сум)"])
        if combo not in unique_services:
            unique_services.append(combo)

    listbox = Listbox(remove_popup, selectmode=SINGLE, font=("Arial", 12), width=28)
    listbox.pack(pady=5)

    for (srv_name, srv_cost) in unique_services:
        listbox.insert("end", f"{srv_name} ({srv_cost})")

    def remove_selected():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Предупреждение", "Выберите услугу для удаления.")
            return

        name, cost = unique_services[sel[0]]
        old_length = len(button_data["extra_services"])
        # Filter out all matching name+cost
        button_data["extra_services"] = [
            s for s in button_data["extra_services"]
            if not (s["Услуга"] == name and s["Стоимость(сум)"] == cost)
        ]
        new_length = len(button_data["extra_services"])
        removed_count = old_length - new_length

        messagebox.showinfo("Информация", 
                            f"Удалено {removed_count} записей услуги '{name}' (стоимость {cost}).")
        remove_popup.destroy()

    create_popup_button(remove_popup, "Удалить", remove_selected, bg_color="#cf2400", width=200, height=40)

    # Center on screen
    remove_popup.update_idletasks()
    rw = remove_popup.winfo_width()
    rh = remove_popup.winfo_height()
    rx = (window.winfo_screenwidth() // 2) - (rw // 2)
    ry = (window.winfo_screenheight() // 2) - (rh // 2)
    remove_popup.geometry(f"{rw}x{rh}+{rx}+{ry}")

###############################################################################
# Pop-up #3: "Выбор времени брони" (with optional comment)
###############################################################################
def pick_reservation_time(parent_window, initial_time=None, initial_comment=""):
    """
    Returns [new_time_string, new_comment_string] or None if cancelled.
    """
    time_popup = Toplevel(parent_window)
    time_popup.title("Выбор времени брони")
    time_popup.geometry("350x300")  # Enough space for spinboxes + comment
    time_popup.configure(bg="#1C1C1C")

    # Make it modal-like
    time_popup.transient(parent_window)
    time_popup.grab_set()
    time_popup.focus_force()

    Label(time_popup, text="Выберите время (часы и минуты):", 
          fg="white", bg="#1C1C1C", font=("Arial", 12)).pack(pady=5)

    # Parse initial_time if given
    if initial_time and ":" in initial_time:
        init_hour_str, init_min_str = initial_time.split(":")
        init_hour = int(init_hour_str)
        init_min = int(init_min_str)
    else:
        init_hour = 0
        init_min = 0

    hour_var = IntVar(value=init_hour)
    minute_var = IntVar(value=init_min)

    spin_frame = Frame(time_popup, bg="#1C1C1C")
    spin_frame.pack()

    hours_spin = Spinbox(spin_frame, from_=0, to=23, wrap=True, textvariable=hour_var, width=5, font=("Arial", 12))
    hours_spin.pack(side="left", padx=5)

    minutes_spin = Spinbox(spin_frame, from_=0, to=59, wrap=True, textvariable=minute_var, width=5, font=("Arial", 12))
    minutes_spin.pack(side="left")

    # A separator line
    Label(time_popup, text="", bg="#1C1C1C").pack(pady=5)
    Label(time_popup, text="——————————————", fg="white", bg="#1C1C1C", font=("Arial", 10)).pack(pady=0)
    Label(time_popup, text="", bg="#1C1C1C").pack(pady=5)

    Label(time_popup, text="Комментарий к брони:", 
          fg="white", bg="#1C1C1C", font=("Arial", 12)).pack(pady=0)

    comment_var = StringVar(value=initial_comment)
    comment_entry = Entry(time_popup, textvariable=comment_var, font=("Arial", 12), width=25)
    comment_entry.pack(pady=5)

    selected_data = [None, None]  # [time_string, comment_string]

    def confirm_time():
        hh = hour_var.get()
        mm = minute_var.get()
        selected_data[0] = f"{hh:02d}:{mm:02d}"
        selected_data[1] = comment_var.get().strip()
        time_popup.destroy()

    def cancel_time():
        time_popup.destroy()

    button_frame = Frame(time_popup, bg="#1C1C1C")
    button_frame.pack(pady=10)

    create_popup_button(button_frame, "OK", confirm_time, bg_color="#3AA655", width=100, height=40)
    create_popup_button(button_frame, "Отмена", cancel_time, bg_color="#F725E5", width=100, height=40)

    # Center on screen
    time_popup.update_idletasks()
    w = time_popup.winfo_width()
    h = time_popup.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (w // 2)
    y = (window.winfo_screenheight() // 2) - (h // 2)
    time_popup.geometry(f"{w}x{h}+{x}+{y}")

    time_popup.wait_window()

    # If confirm was pressed, selected_data[0] is not None
    return selected_data if selected_data[0] else None

###############################################################################
# Pop-up #4: The Cabin Popup
###############################################################################
def open_room_popup(button_data):
    popup = Toplevel(window)
    popup.geometry("400x600+275+275")
    popup.configure(bg="#1C1C1C")
    popup.title(button_data["text"])

    # Make it modal in style but typically we don't forcibly block main, 
    # you can choose to .grab_set() if you want "true" modal. 
    # (In the old stable code, we typically didn't grab_set for the main cabin popup.)
    # If you'd like the old approach, uncomment the lines below:
    # popup.transient(window)
    # popup.grab_set()
    # popup.focus_force()

    rate_per_hour = 70000 if "VIP" in button_data["text"] else 45000

    Label(
        popup,
        text=button_data["text"],
        font=("Arial", 20, "bold"),
        fg="white",
        bg="#1C1C1C"
    ).pack(pady=10)

    session_time_label = Label(popup, text="", font=("Arial", 16), fg="white", bg="#1C1C1C")
    session_time_label.pack(pady=5)

    # New label to show "Стоимость времени" (time-only)
    time_only_label = Label(popup, text="", font=("Arial", 14), fg="white", bg="#1C1C1C")
    time_only_label.pack(pady=5)

    # Existing label for total cost (time + extra services)
    current_cost_label = Label(popup, text="", font=("Arial", 16), fg="white", bg="#1C1C1C")
    current_cost_label.pack(pady=5)

    extra_services_label = Label(popup, text="", font=("Arial", 14), fg="white", bg="#1C1C1C")
    extra_services_label.pack(pady=5)

    reservation_comment_label = Label(popup, text="", font=("Arial", 12), fg="white", bg="#1C1C1C")
    reservation_comment_label.pack(pady=5)

    def get_current_cost_and_services():
        """Returns (total_cost, extra_services_string, time_only_cost)."""
        if button_data["status"] == "occupied":
            elapsed_time = time.time() - button_data["start_time"]
            hours = math.ceil(elapsed_time / 900) * 0.25
            cost_for_time = int(hours * rate_per_hour)

            total_services_cost = 0
            if "extra_services" in button_data and button_data["extra_services"]:
                for srv in button_data["extra_services"]:
                    total_services_cost += srv["Стоимость(сум)"]
                lines = [f"- {s['Услуга']}: {s['Стоимость(сум)']} сум" for s in button_data["extra_services"]]
                services_str = "\n".join(lines)
            else:
                services_str = "(Нет добавленных услуг)"

            total_cost = cost_for_time + total_services_cost
            return total_cost, services_str, cost_for_time
        return (0, "", 0)

    def update_session_info():
        """Continuously updates time/cost labels if the cabin is occupied."""
        if button_data["status"] == "occupied":
            elapsed_time = time.time() - button_data["start_time"]
            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)
            session_time_label.config(text=f"Время с открытия: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")

            total_cost, services_str, time_only_cost = get_current_cost_and_services()
            time_only_label.config(text=f"Стоимость времени: {time_only_cost} сум")
            current_cost_label.config(text=f"Текущая Стоимость (итог): {total_cost} сум")
            extra_services_label.config(text=f"Доп. услуги:\n{services_str}")
            session_time_label.after(1000, update_session_info)

        elif button_data["status"] == "reserved":
            # Show reserved time
            session_time_label.config(text=f"Зарезервировано на: {button_data['reservation_time']}")
            time_only_label.config(text="Стоимость времени: 0 сум")
            current_cost_label.config(text="")
            extra_services_label.config(text="")
            reservation_comment_label.config(
                text=f"Комментарий: {button_data.get('reservation_comment', '')}"
            )
        else:
            # vacant
            session_time_label.config(text="Кабинка свободна")
            time_only_label.config(text="Стоимость времени: 0 сум")
            current_cost_label.config(text="")
            extra_services_label.config(text="")
            reservation_comment_label.config(text="")

    ###########################################################################
    # Button callbacks inside the cabin popup
    ###########################################################################
    def start_session():
        if button_data["status"] == "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка уже занята!")
            return
        button_data["start_time"] = time.time()
        button_data["status"] = "occupied"
        button_data["extra_services"] = []
        canvas.itemconfig(button_data["id"], fill="#cf2400")
        popup.destroy()

    def reserve_room():
        if button_data["status"] == "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка уже занята!")
            return

        new_data = pick_reservation_time(
            popup,
            button_data.get("reservation_time"),
            button_data.get("reservation_comment", "")
        )
        # new_data => [new_time, new_comment]
        if new_data:
            new_time, new_comment = new_data
            button_data["status"] = "reserved"
            button_data["reservation_time"] = new_time
            button_data["reservation_comment"] = new_comment
            canvas.itemconfig(button_data["id"], fill="#FFD700")
            popup.destroy()

    def edit_reservation():
        if button_data["status"] != "reserved":
            messagebox.showwarning("Предупреждение", "Кабинка не зарезервирована!")
            return
        new_data = pick_reservation_time(
            popup,
            button_data["reservation_time"],
            button_data.get("reservation_comment", "")
        )
        if new_data:
            new_time, new_comment = new_data
            button_data["reservation_time"] = new_time
            button_data["reservation_comment"] = new_comment
            session_time_label.config(text=f"Зарезервировано на: {new_time}")
            reservation_comment_label.config(text=f"Комментарий: {new_comment}")

    def cancel_reservation():
        if button_data["status"] != "reserved":
            messagebox.showwarning("Предупреждение", "Кабинка не зарезервирована!")
            return
        button_data["status"] = "vacant"
        for k in ["reservation_time", "reservation_comment"]:
            if k in button_data:
                button_data.pop(k, None)
        canvas.itemconfig(button_data["id"], fill="#3AA655")
        popup.destroy()

    def stop_session():
        if button_data["status"] != "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка не занята!")
            return

        end_time = time.time()
        elapsed_time = end_time - button_data["start_time"]
        hours = math.ceil(elapsed_time / 900) * 0.25
        cost_for_time = int(hours * rate_per_hour)
        total_services_cost = 0
        if "extra_services" in button_data and button_data["extra_services"]:
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
            "Дата": time.strftime("%d/%m/%Y", time.localtime(end_time)),
            "Комментарий": button_data.get("reservation_comment", "")
        }

        # Store in session_data
        if button_data["text"] not in session_data:
            session_data[button_data["text"]] = []
        session_data[button_data["text"]].append(session_info)

        # Reset cabin data
        button_data["status"] = "vacant"
        canvas.itemconfig(button_data["id"], fill="#3AA655")
        for k in ["extra_services", "reservation_time", "reservation_comment", "start_time"]:
            if k in button_data:
                button_data.pop(k, None)

        popup.destroy()
        # Save and clear session_data
        save_session_data()
        session_data.clear()

        # Show billing
        billing_window = Toplevel(window)
        billing_window.title("Биллинг")
        billing_window.geometry("400x300")
        billing_window.configure(bg="#1C1C1C")

        # Make it modal-like
        billing_window.transient(window)
        billing_window.grab_set()
        billing_window.focus_force()

        Label(
            billing_window,
            text=f"Кабинка: {session_info['Кабинка']}",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#1C1C1C"
        ).pack(pady=5)

        Label(
            billing_window,
            text=f"Стоимость времени: {cost_for_time} сум",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#1C1C1C"
        ).pack(pady=5)

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

        # Center billing window
        billing_window.update_idletasks()
        bw = billing_window.winfo_width()
        bh = billing_window.winfo_height()
        bx = (window.winfo_screenwidth() // 2) - (bw // 2)
        by = (window.winfo_screenheight() // 2) - (bh // 2)
        billing_window.geometry(f"{bw}x{bh}+{bx}+{by}")

    def go_back():
        popup.destroy()

    ###########################################################################
    # Create the relevant buttons for each state
    ###########################################################################
    if button_data["status"] == "vacant":
        create_popup_button(popup, "Открыть кабинку", start_session, bg_color="#3AA655")
        create_popup_button(popup, "Зарезервировать кабинку", reserve_room, bg_color="#FFA500")
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5")

    elif button_data["status"] == "occupied":
        create_popup_button(popup, "Закрыть кабинку", stop_session, bg_color="#cf2400")
        create_popup_button(popup, "Добавить к заказу",
                            lambda: add_extra_service(popup, button_data),
                            bg_color="#3AA655")
        if button_data.get("extra_services"):
            create_popup_button(popup, "Убрать из заказа",
                                lambda: remove_extra_service(popup, button_data),
                                bg_color="#3AA655")
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5")

    elif button_data["status"] == "reserved":
        create_popup_button(popup, "Открыть кабинку", start_session, bg_color="#3AA655")
        create_popup_button(popup, "Изменить время брони", edit_reservation, bg_color="#FFA500")
        create_popup_button(popup, "Отменить резерв", cancel_reservation, bg_color="#FFA500")
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5")

    update_session_info()

    # Center the popup
    popup.update_idletasks()
    popup_width = popup.winfo_width()
    popup_height = popup.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (popup_width // 2)
    y = (window.winfo_screenheight() // 2) - (popup_height // 2)
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

###############################################################################
# Create the main cabin buttons on the canvas
###############################################################################
button_defs = [
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

button_width, button_height = 180, 70
vip_width, vip_height = 380, 70
x_start, y_start = 100, 250
x_spacing, y_spacing = 200, 100

for i, button_data in enumerate(button_defs):
    buttons.append(button_data)
    if button_data["size"] == "normal":
        col = i % 4
        row = i // 4
        x1 = x_start + col * x_spacing
        y1 = y_start + row * y_spacing
        x2 = x1 + button_width
        y2 = y1 + button_height
    else:
        col = i % 2
        x1 = x_start + col * (vip_width + 20)
        y1 = y_start + 2 * y_spacing  # Place VIP cabins further down
        x2 = x1 + vip_width
        y2 = y1 + vip_height

    if button_data["status"] == "vacant":
        color = "#3AA655"
    elif button_data["status"] == "occupied":
        color = "#cf2400"
    elif button_data["status"] == "reserved":
        color = "#FFD700"

    b_id = create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=15, color=color)
    button_data["id"] = b_id

    text_id = canvas.create_text(
        (x1 + x2) / 2,
        (y1 + y2) / 2,
        text=button_data["text"],
        fill="#FFFFFF",
        font=("Arial", 16, "bold")
    )
    # Bind to open the cabin popup
    canvas.tag_bind(b_id, "<Button-1>", lambda e, b=button_data: open_room_popup(b))
    canvas.tag_bind(text_id, "<Button-1>", lambda e, b=button_data: open_room_popup(b))

###############################################################################
# Exit button (Save & Quit)
###############################################################################
def exit_and_save():
    occupied_rooms = [b for b in buttons if b["status"] == "occupied"]
    if occupied_rooms:
        answer = messagebox.askyesno(
            "Предупреждение",
            "Есть открытые сессии! Они будут закрыты и данные будут сохранены.\nПродолжить?"
        )
        if not answer:
            return
        forcibly_close_all_rooms()
        if session_data:
            save_session_data()
            session_data.clear()
        window.destroy()
    else:
        if session_data:
            save_session_data()
            session_data.clear()
        window.destroy()

exit_button_id = create_rounded_rectangle(canvas, 375, 720, 575, 790, radius=15, color="#F725E5")
exit_text_id = canvas.create_text(
    475, 755,
    text="Выйти и сохранить",
    fill="#FFFFFF",
    font=("Arial", 20, "bold")
)
canvas.tag_bind(exit_button_id, "<Button-1>", lambda e: exit_and_save())
canvas.tag_bind(exit_text_id, "<Button-1>", lambda e: exit_and_save())

###############################################################################
# Handle the red window [X] close button
###############################################################################
def on_close():
    occupied_rooms = [b for b in buttons if b["status"] == "occupied"]
    if occupied_rooms:
        answer = messagebox.askyesno(
            "Предупреждение",
            "Есть открытые сессии! Они будут закрыты и данные будут сохранены.\nЗакрыть программу?"
        )
        if not answer:
            return
        forcibly_close_all_rooms()
        if session_data:
            save_session_data()
            session_data.clear()
        window.destroy()
    else:
        if session_data:
            answer = messagebox.askyesno(
                "Сохранить данные",
                "Есть несохранённые данные. Сохранить перед выходом?"
            )
            if answer:
                save_session_data()
                session_data.clear()
        window.destroy()

window.protocol("WM_DELETE_WINDOW", on_close)

window.update_idletasks()
window.geometry("950x850")
window.mainloop()
