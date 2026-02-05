import os, sqlite3, threading, time
from datetime import datetime
from tkinter import *
from tkinter import messagebox
from tkcalendar import Calendar
from plyer import notification

APP_FOLDER = os.path.join(os.getenv("LOCALAPPDATA"), "ReminderApp")
os.makedirs(APP_FOLDER, exist_ok=True)
DB_FILE = os.path.join(APP_FOLDER, "reminders.db")

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS reminders(
id INTEGER PRIMARY KEY, datetime TEXT, text TEXT, status TEXT DEFAULT 'pending')""")
try:
    c.execute("SELECT status FROM reminders LIMIT 1")
except:
    c.execute("ALTER TABLE reminders ADD COLUMN status TEXT DEFAULT 'pending'")
conn.commit()

root = Tk()
root.title("Qubify-IT's Prodlendar")
root.geometry("950x600")

# top bar
top = Frame(root)
top.pack(fill=X)

toggle_btn = Button(top, text="Show reminders")
toggle_btn.pack(side=RIGHT, padx=10, pady=5)

# main panels
left = Frame(root)
left.pack(side=LEFT, fill=BOTH, expand=True)

right = Frame(root, width=420)

# left panel
cal = Calendar(left, date_pattern="yyyy-mm-dd")
cal.pack(pady=10)

time_entry = Entry(left)
time_entry.pack()
time_entry.insert(0, "HH:MM")

note_entry = Text(left, width=60, height=5)
note_entry.pack(pady=10)

add_btn = Button(left, text="Add Reminder")
add_btn.pack()

status_label = Label(left, text="", fg="green")
status_label.pack(pady=(4, 0))

# right panel layout
right_top = Frame(right)
right_top.pack(fill=X)

right_body = Frame(right)
right_body.pack(fill=BOTH, expand=True)

right_bottom = Frame(right)
right_bottom.pack(fill=X)

canvas = Canvas(right_body, highlightthickness=0)
canvas.pack(side=LEFT, fill=BOTH, expand=True)

scroll = Scrollbar(right_body, command=canvas.yview)
scroll.pack(side=RIGHT, fill=Y)

canvas.configure(yscrollcommand=scroll.set)

list_frame = Frame(canvas)
canvas_window = canvas.create_window((0, 0), window=list_frame, anchor="nw")

canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width - 12))
list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

def on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)

Button(right_bottom, text="Delete Selected", command=lambda: delete_sel()).pack(pady=8)

# reminder system
selected_ids = set()
cards = []

def select_card(event, rid, card):
    if event.state & 0x0004:  # Ctrl
        if rid in selected_ids:
            selected_ids.remove(rid)
            bg = "#f5f5f5"
        else:
            selected_ids.add(rid)
            bg = "#cce6ff"
        card.config(bg=bg)
        for w in card.winfo_children():
            w.config(bg=bg)
    else:
        selected_ids.clear()
        selected_ids.add(rid)
        for f, fid in cards:
            bg = "#cce6ff" if fid == rid else "#f5f5f5"
            f.config(bg=bg)
            for w in f.winfo_children():
                w.config(bg=bg)

def load():
    for w in list_frame.winfo_children():
        w.destroy()
    cards.clear()

    for rid, dt, txt, st in c.execute("""
        SELECT id, datetime, text, status FROM reminders
        ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, datetime
    """):
        card = Frame(list_frame, bd=1, relief="solid", bg="#f5f5f5", padx=10, pady=8)
        card.pack(fill=X, padx=8, pady=6)

        s = "[PASSED]" if st == "passed" else "[PENDING]"
        Label(card, text=f"{s}  {dt}", anchor="w", bg="#f5f5f5").pack(fill=X)
        Label(card, text=txt, wraplength=360, justify=LEFT,
              anchor="w", bg="#f5f5f5").pack(fill=X, pady=(4, 0))

        card.bind("<Button-1>", lambda e, rid=rid, fr=card: select_card(e, rid, fr))
        for w in card.winfo_children():
            w.bind("<Button-1>", lambda e, rid=rid, fr=card: select_card(e, rid, fr))

        cards.append((card, rid))

def add():
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

    c.execute(
        "INSERT INTO reminders(datetime,text,status) VALUES(?,?,'pending')",
        (dt, txt)
    )
    conn.commit()

    note_entry.delete("1.0", END)
    note_entry.focus()

    status_label.config(text="Reminder added")
    root.after(2000, lambda: status_label.config(text=""))

    load()

def delete_sel():
    if not selected_ids:
        return
    for rid in selected_ids:
        c.execute("DELETE FROM reminders WHERE id=?", (rid,))
    conn.commit()
    selected_ids.clear()
    load()

def toggle():
    if right.winfo_ismapped():
        right.pack_forget()
        toggle_btn.config(text="Show reminders")
    else:
        right.pack(side=RIGHT, fill=BOTH)
        toggle_btn.config(text="Hide reminders")
        load()

toggle_btn.config(command=toggle)
add_btn.config(command=add)

def hide():
    root.withdraw()

root.protocol("WM_DELETE_WINDOW", hide)

def checker():
    while True:
        now = datetime.now()
        for rid, dt, txt, st in c.execute("SELECT id, datetime, text, status FROM reminders"):
            if st == "pending" and datetime.strptime(dt, "%Y-%m-%d %H:%M") <= now:
                notification.notify(title="Reminder", message=txt, timeout=15)
                c.execute("UPDATE reminders SET status='passed' WHERE id=?", (rid,))
                conn.commit()
                root.after(0, load)
        time.sleep(5)

threading.Thread(target=checker, daemon=True).start()
root.mainloop()
