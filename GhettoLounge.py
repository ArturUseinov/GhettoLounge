from tkinter import Tk, Canvas, Toplevel, Label, Frame, Entry, StringVar, IntVar, Spinbox, Listbox, SINGLE, TclError
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import math
import json
import socket
from flask import Flask, render_template_string
import threading
from pyngrok import ngrok
from pyngrok import conf 
conf.get_default().auth_token = "AUTH_TOKEN"  # Replace with your ngrok auth token
import ctypes, sys
if sys.platform == "win32":
    import win32con, win32gui
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:                                     # running under python.exe
        hmenu = win32gui.GetSystemMenu(hwnd, False)
        win32gui.DeleteMenu(hmenu, win32con.SC_CLOSE, win32con.MF_BYCOMMAND)
from datetime import datetime, timedelta

# Initialize the main window
window = Tk()
window.title("Ghetto Lounge Management System")

window.configure(bg="#000000")  # Set background color

# Set minimum window size
window.minsize(950, 850)

# Add a canvas to draw elements
canvas = Canvas(window, bg="#000000", bd=0, highlightthickness=0)

CANVAS_W = 950    
OFF = 50          # horizontal shift to neutralise the old left margin
      

canvas.place(relx=0.5, y=0, anchor='n',   # centred horizontally
             width=CANVAS_W,              # fixed design width
             relheight=1)                 # still stretches vertically


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

def center_window(win, w=None, h=None):
    """Center *win* on the primary screen."""
    win.update_idletasks()                     # ←   make sure geometry is current
    if w is None or h is None:                
        w = w or win.winfo_width()
        h = h or win.winfo_height()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x  = (sw - w) // 2
    y  = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


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
    canvas.create_image(OFF, 30, image=logo, anchor="nw")  # Place the logo
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

# Web portal status label
web_status_label = Label(window, text="Web: OFF", fg="white", bg="red", font=("Arial", 12, "bold"))
canvas.create_window(800, 110, anchor='nw', window=web_status_label)

# Set up Flask app for remote monitoring
app = Flask(__name__)

@app.route("/")
def index():
    rooms = []
    for b in buttons:
        room = {"name": b["text"], "status": b["status"]}
        # Determine block color
        if b["status"] == "vacant":
            room["color"] = "#3AA655"
        elif b["status"] == "occupied":
            room["color"] = "#cf2400"
        elif b["status"] == "reserved":
            room["color"] = "#FFD700"
        # Add details based on status
        if b["status"] == "occupied":
            start_time_str = time.strftime("%H:%M:%S", time.localtime(b["start_time"]))
            elapsed_sec = time.time() - b["start_time"]
            hours = int(elapsed_sec // 3600)
            minutes = int((elapsed_sec % 3600) // 60)
            room["start_time"] = start_time_str
            room["elapsed"] = f"{hours} ч {minutes} мин"
            rate = 80000 if "VIP" in b["text"] else 50000
            cost = int(math.ceil(elapsed_sec / 900) * 0.25 * rate)
            room["cost"] = cost
            room["extra_services"] = b.get("extra_services", [])
        elif b["status"] == "reserved":
            room["reservation_time"] = b.get("reservation_time", "")
            room["reservation_comment"] = b.get("reservation_comment", "")
        rooms.append(room)
    # Statistics for last 24 hours
    total_sessions = 0
    total_revenue = 0
    try:
        with open("Otchet.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        now = datetime.now()
        sessions_list = []
        for sessions in data.values():
            for session in sessions:
                date_str = session.get("Дата")
                end_str = session.get("Время окончания")
                if date_str and end_str:
                    dt = datetime.strptime(f"{date_str} {end_str}", "%d/%m/%Y %H:%M:%S")
                    if now - dt <= timedelta(hours=24):
                        total_sessions += 1
                        total_revenue += int(session.get("Итоговая_стоимость(сум)", 0))
                        sessions_list.append(session)
                        
            sessions_list.sort(
        key=lambda s: datetime.strptime(
            f"{s['Дата']} {s['Время начала']}", "%d/%m/%Y %H:%M:%S"
        )
    )
                        

    except FileNotFoundError:
        pass
    stats = {"total_sessions": total_sessions, "total_revenue": total_revenue}
    html = r"""<!DOCTYPE html>
    <html>
    <head>
        <title>Ghetto Lounge Status</title>
        <style>
            body { background-color: black; color: white; font-family: Arial, sans-serif; }
            .room-block { display: inline-block; width: 160px; margin: 10px; padding: 5px; color: white; vertical-align: top; border-radius: 8px; }
            details { margin-top: 5px; }
            details p, details li { color: black; }
        </style>
    </head>
    <body>
        <h1>Ghetto Lounge: Remote Monitoring</h1>
        <div>
            {% for room in rooms %}
            <div class="room-block" style="background-color: {{ room.color }};">
                <details>
                    <summary style="font-weight: bold; cursor: pointer; {% if room.color == '#FFD700' %} color: black; {% endif %}">
                        {{ room.name }} - {{ room.status.capitalize() }}
                    </summary>
                    {% if room.status == 'occupied' %}
                    <p>Начало: {{ room.start_time }}</p>
                    <p>Прошло: {{ room.elapsed }}</p>
                    <p>Стоимость: {{ room.cost }} сум</p>
                    {% if room.extra_services %}
                    <p>Услуги:</p>
                    <ul>
                        {% for srv in room.extra_services %}
                        <li>{{ srv["Услуга"] }} ({{ srv["Стоимость(сум)"] }} сум)</li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    {% elif room.status == 'reserved' %}
                    <p>Забронировано на: {{ room.reservation_time }}</p>
                    <p>Комментарий: {{ room.reservation_comment }}</p>
                    {% else %}
                    <p>Свободно</p>
                    {% endif %}
                </details>
            </div>
            {% endfor %}
        </div>
        <hr />
        <div>
            <p>Статистика за последние 24 часов:</p>
            <p>Всего сессий: {{ stats.total_sessions }}</p>
            <p>Общая выручка: {{ stats.total_revenue }} сум</p>
        </div>
        <p>Сессии за последние 24 часа:</p>
<table border="1">
  <thead>
    <tr>
      <th>Кабинка</th><th>Время начала</th><th>Время окончания</th>
      <th>Длительность (часов)</th><th>Стоимость_времени(сум)</th>
      <th>Дополнительные услуги</th><th>Итоговая_стоимость(сум)</th>
      <th>Дата</th><th>Комментарий</th>
    </tr>
  </thead>
  <tbody>
  {% for sess in sessions %}
    <tr>
      <td>{{ sess["Кабинка"] }}</td>
      <td>{{ sess["Время начала"] }}</td>
      <td>{{ sess["Время окончания"] }}</td>
      <td>{{ sess["Длительность (часов)"] }}</td>
      <td>{{ sess["Стоимость_времени(сум)"] }}</td>
      <td>
        {% if sess["Дополнительные услуги"] %}
          <ul>
          {% for srv in sess["Дополнительные услуги"] %}
            <li>{{ srv["Услуга"] }} ({{ srv["Стоимость(сум)"] }} сум)</li>
          {% endfor %}
          </ul>
        {% else %}
          Нет
        {% endif %}
      </td>
      <td>{{ sess["Итоговая_стоимость(сум)"] }}</td>
      <td>{{ sess["Дата"] }}</td>
      <td>{{ sess["Комментарий"] }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>
    </body>
    </html>"""
    return render_template_string(html, rooms=rooms, stats=stats, sessions=sessions_list)

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
        rate_per_hour = 80000 if "VIP" in button_data["text"] else 50000
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

    Label(service_popup, text="Стоимость (сум):\nПример: 100000 или 100,000 или 100.000", fg="white", bg="#1C1C1C", font=("Arial", 10)).pack(pady=5)

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
            messagebox.showwarning("Предупреждение", "Введите корректную стоимость (только цифры и возможные запятые/точки).")
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
    center_window(service_popup)

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

    Label(remove_popup, text="Выберите услугу для удаления:", fg="white", bg="#1C1C1C", font=("Arial", 12)).pack(pady=5)

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

    create_popup_button(remove_popup, "Удалить", remove_selected, bg_color="#cf2400", width=240, height=40)

    # Center on screen
    center_window(remove_popup)

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

    Label(time_popup, text="Выберите время (часы и минуты):", fg="white", bg="#1C1C1C", font=("Arial", 12)).pack(pady=5)

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

    Label(time_popup, text="Комментарий к брони:", fg="white", bg="#1C1C1C", font=("Arial", 12)).pack(pady=0)

    comment_var = StringVar(value=initial_comment)
    comment_entry = Entry(time_popup, textvariable=comment_var, font=("Arial", 12), width=25)
    comment_entry.pack(pady=5)

    selected_data = [None, None]  # [time_string, comment_string]

    def confirm_time():
        try:
            hh = int(hour_var.get())
            mm = int(minute_var.get())
        except (ValueError, TclError):
            messagebox.showerror("Ошибка", "Введите корректный час и минуту (0-23 / 0-59).")
            return

        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            messagebox.showerror("Ошибка", "Часы 0-23, минуты 0-59.")
            return

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
    center_window(time_popup)

    time_popup.wait_window()

    # If confirm was pressed, selected_data[0] is not None
    return selected_data if selected_data[0] else None

###############################################################################
# Pop-up #4: The Cabin Popup
###############################################################################
def open_room_popup(button_data):
    popup = Toplevel(window)
    popup.title(button_data["text"])
    popup.configure(bg="#1C1C1C")
    popup.geometry("400x600")     
    center_window(popup)          


    rate = 80000 if "VIP" in button_data["text"] else 50000

    # Header
    Label(popup, text=button_data["text"],
          fg="white", bg="#1C1C1C", font=("Arial", 20, "bold")).pack(pady=8)

    # Live-info labels
    session_time_label  = Label(popup, fg="white", bg="#1C1C1C", font=("Arial", 16))
    time_only_label     = Label(popup, fg="white", bg="#1C1C1C", font=("Arial", 14))
    current_cost_label  = Label(popup, fg="white", bg="#1C1C1C", font=("Arial", 16))
    extra_services_label= Label(popup, fg="white", bg="#1C1C1C", font=("Arial", 12), justify="left")
    reservation_comment = Label(popup, fg="white", bg="#1C1C1C", font=("Arial", 12))
    for w in (session_time_label, time_only_label,
              current_cost_label, extra_services_label, reservation_comment):
        w.pack(pady=2)

    # Live-update loop
    def update_session_info():
        if not popup.winfo_exists():      # window was closed → stop refreshing
            return
        if button_data["status"] == "occupied":
            elapsed = time.time() - button_data["start_time"]
            h, rem  = divmod(elapsed, 3600)
            m, s    = divmod(rem, 60)
            session_time_label.config(
                text=f"Время с открытия: {int(h):02}:{int(m):02}:{int(s):02}")
            quarter_hours = math.ceil(elapsed / 900) * 0.25
            time_cost = int(quarter_hours * rate)
            extras_cost = sum(srv["Стоимость(сум)"]
                              for srv in button_data.get("extra_services", []))
            current_cost_label.config(
                text=f"Текущая стоимость (итого): {time_cost + extras_cost} сум")
            time_only_label.config(text=f"Стоимость времени: {time_cost} сум")
            if button_data.get("extra_services"):
                extras = "\n".join(f"- {s['Услуга']}: {s['Стоимость(сум)']} сум"
                                   for s in button_data["extra_services"])
                extra_services_label.config(text=f"Доп. услуги:\n{extras}")
            else:
                extra_services_label.config(text="Доп. услуги: нет")
            reservation_comment.config(text="")
            
        elif button_data["status"] == "reserved":
            session_time_label.config(
                text=f"Зарезервировано на: {button_data.get('reservation_time','')}")
            time_only_label.config(text="Стоимость времени: 0 сум")
            current_cost_label.config(text="")
            extra_services_label.config(text="")
            reservation_comment.config(text=f"Комментарий: {button_data.get('reservation_comment','')}")
        else:  # vacant
            session_time_label.config(text="Кабинка свободна")
            for w in (time_only_label, current_cost_label,
                      extra_services_label, reservation_comment):
                w.config(text="")
        # re-arm loop
        popup.after(1000, update_session_info)
    update_session_info()

    def start_session():
        if button_data["status"] == "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка уже занята!")
            return
        button_data["start_time"] = time.time()
        button_data["status"] = "occupied"
        button_data["extra_services"] = []
        canvas.itemconfig(button_data["id"], fill="#cf2400")
        popup.destroy()

    def close_session():
        if button_data["status"] != "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка не занята!")
            return
        # Calculate costs and log
        rate = 80000 if "VIP" in button_data["text"] else 50000
        end_time = time.time()
        elapsed_time = end_time - button_data["start_time"]
        hours = math.ceil(elapsed_time / 900) * 0.25
        cost_for_time = int(hours * rate)
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
        if button_data["text"] not in session_data:
            session_data[button_data["text"]] = []
        session_data[button_data["text"]].append(session_info)

        button_data["status"] = "vacant"
        for key in ["reservation_time", "extra_services", "reservation_comment", "start_time"]:
            if key in button_data:
                button_data.pop(key, None)
        canvas.itemconfig(button_data["id"], fill="#3AA655")
        popup.destroy()

        # Save and clear session_data
        save_session_data()
        session_data.clear()

        # Show billing summary
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
        center_window(billing_window)

    def reserve_session():
        if button_data["status"] == "occupied":
            messagebox.showwarning("Предупреждение", "Кабинка занята, бронирование невозможно.")
            return
        new_data = pick_reservation_time(popup,
                                        button_data.get("reservation_time", ""),
                                        button_data.get("reservation_comment", ""))
        if new_data:
            new_time, new_comment = new_data
            button_data["status"] = "reserved"
            button_data["reservation_time"] = new_time
            button_data["reservation_comment"] = new_comment
            canvas.itemconfig(button_data["id"], fill="#FFD700")
            popup.destroy()

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
        
    def change_reservation():
        if button_data["status"] != "reserved":
            messagebox.showwarning("Предупреждение", "Кабинка не зарезервирована!")
            return

        new_data = pick_reservation_time(
            popup,
            button_data.get("reservation_time", ""),
            button_data.get("reservation_comment", "")
        )
        if new_data:
            new_time, new_comment = new_data
            button_data["reservation_time"] = new_time
            button_data["reservation_comment"] = new_comment
            # refresh labels in the still-open popup
            session_time_label.config(text=f"Зарезервировано на: {new_time}")
            reservation_comment.config(text=f"Комментарий: {new_comment}")
            canvas.itemconfig(button_data["id"], fill="#FFD700")

    def go_back():
        popup.destroy()

    # Create the relevant buttons for each state
    if button_data["status"] == "vacant":
        create_popup_button(popup, "Открыть кабинку", start_session, bg_color="#3AA655", fg_color="#FFFFFF", width=240, height=50)
        create_popup_button(popup, "Забронировать", reserve_session, bg_color="#FFD700", fg_color="#000000", width=240, height=50)
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5", width=240, height=50)
    elif button_data["status"] == "occupied":
        create_popup_button(popup, "Добавить услугу", lambda b=button_data: add_extra_service(popup, b), bg_color="#3AA655", width=240, height=50)
        create_popup_button(popup, "Убрать услугу", lambda b=button_data: remove_extra_service(popup, b), bg_color="#cf2400", width=240, height=50)
        create_popup_button(popup, "Закрыть кабинку", close_session, bg_color="#F725E5", width=240, height=50)
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5", width=240, height=50)
    elif button_data["status"] == "reserved":
        create_popup_button(popup, "Изменить время брони", change_reservation,bg_color="#4682B4", width=240, height=50)
        create_popup_button(popup, "Занять", start_session, bg_color="#3AA655", width=240, height=50)
        create_popup_button(popup, "Отменить бронь", cancel_reservation, bg_color="#cf2400", width=240, height=50)
        create_popup_button(popup, "Назад", go_back, bg_color="#F725E5", width=240, height=50)
        popup.grab_set()

###############################################################################
# Main cabin layout
###############################################################################
button_width, button_height = 180, 70
vip_width, vip_height = 380, 70
x_start, y_start = 100 - OFF, 250
x_spacing, y_spacing = 200, 100

button_defs = [
    {"text": f"Кабинка {i+1}", "status": "vacant", "size": "normal"} for i in range(8)
] + [
    {"text": f"VIP Кабинка {i+1}", "status": "vacant", "size": "vip"} for i in range(2)
]

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
        col = (i - 8) % 2  
        x1 = x_start + col * (vip_width + 20)
        y1 = y_start + 2 * y_spacing
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
    try:
        ngrok.kill()  # Ensure the Ngrok tunnel is closed
    except Exception as e:
        print(f"Error closing Ngrok tunnel: {e}")
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
        answer = messagebox.askyesno(
            "Сохранить данные",
            "Есть несохранённые данные. Сохранить перед выходом?"
        )
        if answer:
            save_session_data()
            session_data.clear()
    try:
        ngrok.kill()  # Ensure the Ngrok tunnel is closed
    except Exception as e:
        print(f"Error closing Ngrok tunnel: {e}")
    window.destroy()
window.protocol("WM_DELETE_WINDOW", on_close)
# Start the Flask thread
flask_thread = threading.Thread(target=app.run, kwargs={"port":5050, "use_reloader":False}, daemon=True)
flask_thread.start()


try:
    ngrok.kill()  # closes any pre-existing ngrok processes for this user
    # Use the custom domain
    public_url = ngrok.connect(5050, domain="gator-dynamic-usually.ngrok-free.app").public_url
    print(f"Public URL: {public_url}")
    web_status_label.config(text="Web: ON", bg="green")
except Exception as err:
    # If ngrok fails (no internet, cert error, etc.) just keep running locally
    print("Ngrok error:", err)
    web_status_label.config(text="Web: LOCAL", bg="orange")
    public_url = "local only"

# Function to check and reconnect the Ngrok tunnel
def is_internet_connected():
    """Check if the internet connection is active."""
    try:
        # Attempt to connect to a reliable host (Google's public DNS server)
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# ------------------------------------------------------------------
# Ngrok watchdog ---------------------------------------------------
# ------------------------------------------------------------------
def check_and_reconnect_tunnel():
    # """Launch a single background thread that checks the tunnel forever."""
    global public_url

    def perform_check():
        try:
            # 1) Internet up?
            if not is_internet_connected():
                raise RuntimeError("No internet connection.")

            # 2) Is the reserved-domain tunnel alive?
            for t in ngrok.get_tunnels():
                if t.public_url == "https://gator-dynamic-usually.ngrok-free.app":
                    web_status_label.config(text="Web: ON", bg="green")
                    return                       # <- all good, nothing to do

            raise RuntimeError("Reserved tunnel not found.")  # -> reconnect

        except Exception as e:
            print(f"Ngrok check failed: {e}")
            web_status_label.config(text="Web: LOCAL", bg="orange")

            try:
                ngrok.kill()                     # nuke any leftovers
                time.sleep(2)
            except Exception as kill_err:
                print(f"Ngrok kill error: {kill_err}")

            try:
                public_url = ngrok.connect(
                    5050,
                    domain="gator-dynamic-usually.ngrok-free.app"
                ).public_url
                print(f"Re-connected: {public_url}")
                web_status_label.config(text="Web: ON", bg="green")
            except Exception as rec_err:
                print(f"Reconnect failed: {rec_err}")
                public_url = "local only"

    # ------------------- watchdog loop ----------------------------
    def watchdog():
        while True:
            perform_check()
            time.sleep(30)       # wait 30 s before next check

    threading.Thread(target=watchdog, daemon=True).start()

# kick it off once at startup
check_and_reconnect_tunnel()

center_window(window, 950, 850)
window.mainloop()