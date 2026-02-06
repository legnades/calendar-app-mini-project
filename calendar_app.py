import os, sqlite3, threading, time, sys, json
from datetime import datetime
from tkinter import *
from tkinter import messagebox
from tkcalendar import Calendar
from plyer import notification
import socket

# windows-only extras
if os.name == "nt":
    import winsound
    import pystray
    from PIL import Image, ImageDraw

# ===============================
# Single instance + reopen logic
# ===============================
PORT = 50555

if os.name == "nt":
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", PORT))
        server.listen(1)
        IS_PRIMARY = True
    except OSError:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", PORT))
            s.send(b"SHOW")
            s.close()
        except:
            pass
        sys.exit(0)
else:
    IS_PRIMARY = True

# ===============================
# App folders & settings
# ===============================
APP_FOLDER = os.path.join(os.getenv("LOCALAPPDATA"), "ReminderApp")
os.makedirs(APP_FOLDER, exist_ok=True)

DB_FILE = os.path.join(APP_FOLDER, "reminders.db")
SETTINGS_FILE = os.path.join(APP_FOLDER, "settings.json")

DEFAULT_SETTINGS = {"theme": "dark"}

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(DEFAULT_SETTINGS, f)

with open(SETTINGS_FILE, "r") as f:
    SETTINGS = json.load(f)

# ===============================
# Database
# ===============================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS reminders(
id INTEGER PRIMARY KEY,
datetime TEXT,
text TEXT,
status TEXT DEFAULT 'pending'
)
""")
conn.commit()

# ===============================
# UI
# ===============================
root = Tk()
root.title("Qubify-IT's Prodlendar")
root.geometry("950x600")

# -------------------------------
# Theme handling
# -------------------------------
def apply_theme():
    dark = SETTINGS["theme"] == "dark"
    bg = "#0e1621" if dark else "#ffffff"
    fg = "#ffffff" if dark else "#000000"
    accent = "#1f2a3a" if dark else "#e6e6e6"

    root.config(bg=bg)
    for w in root.winfo_children():
        try:
            w.config(bg=bg, fg=fg)
        except:
            pass

apply_theme()

# -------------------------------
# Settings panel
# -------------------------------
settings_open = False

def toggle_theme():
    SETTINGS["theme"] = "light" if SETTINGS["theme"] == "dark" else "dark"
    with open(SETTINGS_FILE, "w") as f:
        json.dump(SETTINGS, f)
    apply_theme()

def toggle_settings():
    global settings_open
    if settings_open:
        settings_panel.pack_forget()
    else:
        settings_panel.pack(side=LEFT, fill=Y)
    settings_open = not settings_open

settings_panel = Frame(root, width=200)
Button(settings_panel, text="Toggle light mode", command=toggle_theme).pack(pady=10)

Button(root, text="⚙", command=toggle_settings).pack(anchor="nw", padx=6, pady=6)

# -------------------------------
# Main layout
# -------------------------------
left = Frame(root)
left.pack(side=LEFT, fill=BOTH, expand=True)

right = Frame(root, width=420)
right.pack(side=RIGHT, fill=BOTH)

Label(left, text="", fg="orange").pack()
edit_label = Label(left, text="", fg="orange")
edit_label.pack()

cal = Calendar(left, date_pattern="yyyy-mm-dd")
cal.pack(pady=10)

time_entry = Entry(left)
time_entry.pack()
time_entry.insert(0, "HH:MM")

note_entry = Text(left, width=60, height=5)
note_entry.pack(pady=10)

status_label = Label(left, text="", fg="green")
status_label.pack()

# -------------------------------
# Reminder list
# -------------------------------
selected_ids = set()
EDIT_MODE = False

list_frame = Frame(right)
list_frame.pack(fill=BOTH, expand=True)

def load():
    for w in list_frame.winfo_children():
        w.destroy()
    selected_ids.clear()

    for rid, dt, txt, st in c.execute("SELECT id, datetime, text, status FROM reminders ORDER BY datetime"):
        f = Frame(list_frame, bd=1, relief="solid", padx=8, pady=6)
        f.pack(fill=X, pady=4)
        Label(f, text=dt).pack(anchor="w")
        Label(f, text=txt, wraplength=360).pack(anchor="w")

        def sel(e, rid=rid, fr=f):
            if e.state & 0x0004:
                selected_ids.symmetric_difference_update({rid})
            else:
                selected_ids.clear()
                selected_ids.add(rid)
            load()

        f.bind("<Button-1>", sel)

load()

# -------------------------------
# Add / Edit logic
# -------------------------------
def save():
    global EDIT_MODE
    raw = f"{cal.get_date()} {time_entry.get().strip()}"
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M")
    except:
        messagebox.showerror("Invalid time", "Use format like 9:30 or 10:45")
        return

    txt = note_entry.get("1.0", END).strip()
    if not txt:
        messagebox.showerror("Missing text", "Enter reminder text")
        return

    if EDIT_MODE:
        for rid in selected_ids:
            c.execute("UPDATE reminders SET datetime=?, text=? WHERE id=?", (dt, txt, rid))
        EDIT_MODE = False
        edit_label.config(text="")
    else:
        c.execute("INSERT INTO reminders(datetime,text,status) VALUES(?,?,'pending')", (dt, txt))

    conn.commit()
    status_label.config(text="Saved")
    root.after(2000, lambda: status_label.config(text=""))
    load()

def edit():
    global EDIT_MODE
    if not selected_ids:
        return
    EDIT_MODE = True
    edit_label.config(text="Editing reminder(s)")

def delete_sel():
    for rid in selected_ids:
        c.execute("DELETE FROM reminders WHERE id=?", (rid,))
    conn.commit()
    load()

Button(left, text="Save", command=save).pack()
Button(right, text="Edit", command=edit).pack()
Button(right, text="Delete Selected", command=delete_sel).pack()

# -------------------------------
# Background checker
# -------------------------------
def checker():
    while True:
        now = datetime.now()
        for rid, dt, txt, st in c.execute("SELECT id, datetime, text, status FROM reminders"):
            if st == "pending" and datetime.strptime(dt, "%Y-%m-%d %H:%M") <= now:
                if os.name == "nt":
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                notification.notify(title="Reminder", message=txt, timeout=15)
                c.execute("UPDATE reminders SET status='passed' WHERE id=?", (rid,))
                conn.commit()
        time.sleep(5)

# -------------------------------
# Tray
# -------------------------------
def tray_icon():
    image = Image.new("RGB", (64, 64), "black")
    d = ImageDraw.Draw(image)
    d.rectangle([16, 16, 48, 48], fill="blue")

    def open_app(icon, item):
        root.after(0, restore_window)

    def exit_app(icon, item):
        icon.stop()
        root.quit()
        sys.exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Open", open_app),
        pystray.MenuItem("End process", exit_app)
    )

    icon = pystray.Icon("Prodlendar", image, "Prodlendar", menu)
    icon.run()

# -------------------------------
# Window control
# -------------------------------
def restore_window():
    root.deiconify()
    root.lift()
    root.focus_force()

def hide():
    root.withdraw()

root.protocol("WM_DELETE_WINDOW", hide)

def listen_for_show():
    while True:
        conn_, _ = server.accept()
        if conn_.recv(1024) == b"SHOW":
            root.after(0, restore_window)
        conn_.close()

# -------------------------------
# Threads
# -------------------------------
threading.Thread(target=checker, daemon=True).start()
threading.Thread(target=listen_for_show, daemon=True).start()

if os.name == "nt":
    threading.Thread(target=tray_icon, daemon=True).start()

root.mainloop()
