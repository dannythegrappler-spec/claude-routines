import tkinter as tk
from tkinter import ttk
import json
import os

SAVE_FILE = "checklist.json"
# Correct full path: the .py file is INSIDE the "End of Day Checklist" folder
END_OF_DAY_FILE = r"C:\Users\danny\OneDrive\Desktop\Core Folders\Learning Python Scripts\Score\End of Day Checklist\End of Day Checklist.py"

class ChecklistApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Checklist")
        self.root.configure(bg="#0a0a0a")
    
        self.root.geometry("1880x980+20+20")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
     
        # Style
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12), padding=8)
        style.configure("Brown.TLabel", foreground="#c19c6e", background="#0a0a0a", font=("Helvetica", 16, "bold"))
     
        # Header
        ttk.Label(
            root,
            text="Checklist",
            style="Brown.TLabel"
        ).pack(pady=(30, 15))
     
        # Input area
        input_frame = tk.Frame(root, bg="#0a0a0a")
        input_frame.pack(fill="x", padx=40, pady=15)
     
        self.entry = tk.Entry(
            input_frame,
            bg="#1a1a1a",
            fg="white",
            insertbackground="white",
            font=("Helvetica", 14),
            relief="flat",
            highlightthickness=2,
            highlightbackground="#444444",
            highlightcolor="#c19c6e"
        )
        self.entry.insert(0, "Add a new item...")
        self.entry.bind("<FocusIn>", lambda e: self.entry.delete(0, tk.END) if self.entry.get() == "Add a new item..." else None)
        self.entry.pack(side="left", fill="x", expand=True, ipady=10)
     
        add_button = tk.Button(
            input_frame,
            text="Add Item",
            bg="#8b5a2b",
            fg="white",
            activebackground="#a16a3a",
            font=("Helvetica", 12, "bold"),
            bd=0,
            padx=24,
            pady=12,
            command=self.add_item
        )
        add_button.pack(side="right", padx=(20, 0))
     
        # List area (with scrollbar)
        self.items_canvas = tk.Canvas(root, bg="#0a0a0a", highlightthickness=0)
        self.items_canvas.pack(side="left", fill="both", expand=True, padx=40, pady=10)
     
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.items_canvas.yview)
        scrollbar.pack(side="right", fill="y")
     
        self.items_frame = tk.Frame(self.items_canvas, bg="#0a0a0a")
        self.items_canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
     
        self.items_frame.bind("<Configure>", lambda e: self.items_canvas.configure(scrollregion=self.items_canvas.bbox("all")))
        self.items_canvas.configure(yscrollcommand=scrollbar.set)
     
        # Bottom buttons frame
        bottom_frame = tk.Frame(root, bg="#0a0a0a")
        bottom_frame.pack(fill="x", padx=40, pady=(15, 30))
     
        # End of Day button (right side)
        end_of_day_button = tk.Button(
            bottom_frame,
            text="End of Day",
            bg="#2e5a2e",
            fg="white",
            activebackground="#3a6a3a",
            font=("Helvetica", 12, "bold"),
            bd=0,
            padx=28,
            pady=12,
            command=self.open_end_of_day_file
        )
        end_of_day_button.pack(side="right", padx=(15, 0))
     
        # Exit & Save button
        exit_button = tk.Button(
            bottom_frame,
            text="Exit & Save",
            bg="#4a2c1a",
            fg="white",
            activebackground="#5a3c2a",
            font=("Helvetica", 12, "bold"),
            bd=0,
            padx=28,
            pady=12,
            command=self.on_closing
        )
        exit_button.pack(side="right")
     
        # Load saved items
        self.load_items()
     
        # Bind keys
        self.root.bind("<Return>", lambda event: self.add_item())
        self.root.bind("<Escape>", lambda event: self.on_closing())

    def add_item(self):
        text = self.entry.get().strip()
        if not text or text == "Add a new item...":
            return
        self._create_item(text, completed=False, priority=False)
        self.entry.delete(0, tk.END)
        self.entry.focus_set()

    def _create_item(self, text, completed=False, priority=False):
        item_frame = tk.Frame(self.items_frame, bg="#0a0a0a")
        item_frame.pack(fill="x", pady=6)
       
        # Priority/flag button (yellow ⚑ toggles red)
        flag_btn = tk.Button(
            item_frame,
            text="⚑",
            fg="#f0c000" if not priority else "#ff4444",
            bg="#0a0a0a",
            activebackground="#222222",
            activeforeground="#ffdd44" if not priority else "#ff7777",
            bd=0,
            font=("Helvetica", 16, "bold"),
            width=2,
            relief="flat",
            command=lambda f=item_frame: self.toggle_priority(f)
        )
        flag_btn.pack(side="left", padx=(8, 2))
       
        # ↑ Arrow button - Left click = up, Right click = down
        move_btn = tk.Button(
            item_frame,
            text="↑",
            fg="#c19c6e",
            bg="#0a0a0a",
            activebackground="#222222",
            activeforeground="#e0b080",
            bd=0,
            font=("Helvetica", 14, "bold"),
            width=2
        )
        move_btn.pack(side="left", padx=(2, 3))
        
        # Bind left click (move up) and right click (move down)
        move_btn.bind("<Button-1>", lambda event, f=item_frame: self.move_item(f, direction="up"))
        move_btn.bind("<Button-3>", lambda event, f=item_frame: self.move_item(f, direction="down"))
       
        # Checkmark button
        check_text = "✔" if completed else "⬜"
        check_btn = tk.Button(
            item_frame,
            text=check_text,
            fg="#55ff55" if completed else "#777777",
            bg="#0a0a0a",
            activebackground="#222222",
            activeforeground="#88ff88" if completed else "#aaaaaa",
            bd=0,
            font=("Helvetica", 16, "bold"),
            width=3,
            command=lambda f=item_frame: self.toggle_complete(f)
        )
        check_btn.pack(side="left", padx=(3, 8))
       
        # Text label
        font_style = ("Helvetica", 14, "overstrike") if completed else ("Helvetica", 14)
        fg_color = "#a0805a" if completed else ("#ff4444" if priority else "#c19c6e")
        label = tk.Label(
            item_frame,
            text=text,
            fg=fg_color,
            bg="#0a0a0a",
            font=font_style,
            anchor="w"
        )
        label.pack(side="left", fill="x", expand=True)
       
        # Remove button
        remove_btn = tk.Button(
            item_frame,
            text="❌",
            fg="#ff5555",
            bg="#0a0a0a",
            activebackground="#222222",
            activeforeground="#ff7777",
            bd=0,
            font=("Helvetica", 14, "bold"),
            width=2,
            command=lambda f=item_frame: self.remove_item(f)
        )
        remove_btn.pack(side="right", padx=(15, 5))
       
        # Store attributes
        item_frame.completed = completed
        item_frame.priority = priority
        item_frame.label = label
        item_frame.check_btn = check_btn
        item_frame.move_btn = move_btn          # renamed for clarity
        item_frame.flag_btn = flag_btn
        item_frame.text = text
       
        self.update_move_up_buttons()

    def toggle_complete(self, item_frame):
        item_frame.completed = not item_frame.completed
        self._update_item_visuals(item_frame)
        self.save_items()

    def toggle_priority(self, item_frame):
        item_frame.priority = not item_frame.priority
        self._update_item_visuals(item_frame)
        self.save_items()

    def _update_item_visuals(self, item_frame):
        if item_frame.completed:
            fg_color = "#a0805a"
            font_style = ("Helvetica", 14, "overstrike")
            flag_fg = "#f0c000"
        else:
            fg_color = "#ff4444" if item_frame.priority else "#c19c6e"
            font_style = ("Helvetica", 14)
            flag_fg = "#ff4444" if item_frame.priority else "#f0c000"

        item_frame.label.configure(font=font_style, fg=fg_color)
        
        item_frame.flag_btn.configure(
            fg=flag_fg,
            activeforeground="#ff7777" if item_frame.priority else "#ffdd44"
        )

        if item_frame.completed:
            item_frame.check_btn.configure(text="✔", fg="#55ff55", activeforeground="#88ff88")
        else:
            item_frame.check_btn.configure(text="⬜", fg="#777777", activeforeground="#aaaaaa")

    def move_item(self, item_frame, direction="up"):
        children = list(self.items_frame.winfo_children())
        if len(children) < 2:
            return
        
        try:
            idx = children.index(item_frame)
        except ValueError:
            return
        
        if direction == "up":
            if idx <= 0:
                return
            target_idx = idx - 1
        elif direction == "down":
            if idx >= len(children) - 1:
                return
            target_idx = idx + 1
        else:
            return
        
        target_frame = children[target_idx]
        
        # Swap text
        current_text = item_frame.label.cget("text")
        target_text = target_frame.label.cget("text")
        item_frame.label.configure(text=target_text)
        target_frame.label.configure(text=current_text)
        
        # Swap completed
        current_completed = item_frame.completed
        target_completed = target_frame.completed
        item_frame.completed = target_completed
        target_frame.completed = current_completed
        
        # Swap priority
        current_priority = item_frame.priority
        target_priority = target_frame.priority
        item_frame.priority = target_priority
        target_frame.priority = current_priority
        
        # Update visuals
        self._update_item_visuals(item_frame)
        self._update_item_visuals(target_frame)
        
        self.save_items()

    def update_move_up_buttons(self):
        children = self.items_frame.winfo_children()
        for i, widget in enumerate(children):
            if hasattr(widget, "move_btn"):
                if i == 0:
                    widget.move_btn.pack_forget()
                else:
                    if not widget.move_btn.winfo_ismapped():
                        widget.move_btn.pack(side="left", padx=(2, 3), before=widget.check_btn)

    def remove_item(self, item_frame):
        item_frame.destroy()
        self.update_move_up_buttons()
        self.save_items()

    def save_items(self):
        items = []
        for widget in self.items_frame.winfo_children():
            if isinstance(widget, tk.Frame) and hasattr(widget, "label"):
                text = widget.label.cget("text")
                completed = widget.completed
                priority = widget.priority
                items.append({"text": text, "completed": completed, "priority": priority})
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_items(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                items = json.load(f)
            for item in items:
                self._create_item(
                    item["text"],
                    completed=item.get("completed", False),
                    priority=item.get("priority", False)
                )
        except Exception:
            pass

    def on_closing(self):
        self.save_items()
        self.root.destroy()

    def open_end_of_day_file(self):
        if os.path.exists(END_OF_DAY_FILE):
            try:
                os.startfile(END_OF_DAY_FILE)
            except Exception as e:
                print(f"Error opening file: {e}")
        else:
            print(f"File not found: {END_OF_DAY_FILE}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChecklistApp(root)
    root.mainloop()