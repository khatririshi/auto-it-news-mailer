#!/usr/bin/env python3

import json
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext

import schedule
from dotenv import set_key

from config import APP_CONFIG_FILE, ENV_FILE, get_settings
from fetch_news import fetch_it_news
from filter_news import filter_news as filter_news_core
from send_mail import send_email as send_email_core


class AutoMailerApp:
    def __init__(self, root: tk.Tk):
        settings = get_settings()

        self.root = root
        self.root.title("Auto IT News Mailer")
        self.root.geometry("780x680")
        self.root.minsize(700, 600)
        self.root.configure(bg="#0f1117")

        self.is_running = False
        self.scheduler_thread: threading.Thread | None = None

        self.send_time = tk.StringVar(value=settings.send_time)
        self.status_var = tk.StringVar(value="Stopped")
        self.last_sent_var = tk.StringVar(value="Never")
        self.next_send_var = tk.StringVar(value="-")
        self.articles_var = tk.StringVar(value=str(settings.max_articles))

        self.api_key_var = tk.StringVar(value=settings.news_api_key or "")
        self.sender_var = tk.StringVar(value=settings.sender_email or "")
        self.password_var = tk.StringVar(value=settings.sender_password or "")
        self.recipient_var = tk.StringVar(value=settings.recipient_email or "")

        self._build_ui()
        self._log("Welcome to Auto IT News Mailer. Fill in your settings and click Start.")

    def _save_config(self) -> None:
        existing_config = {}
        if APP_CONFIG_FILE.exists():
            try:
                existing_config = json.loads(APP_CONFIG_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing_config = {}

        existing_config.update(
            {
                "send_time": self.send_time.get().strip(),
                "max_articles": int(self.articles_var.get()),
            }
        )
        APP_CONFIG_FILE.write_text(
            json.dumps(existing_config, indent=2),
            encoding="utf-8",
        )

        set_key(str(ENV_FILE), "NEWS_API_KEY", self.api_key_var.get().strip())
        set_key(str(ENV_FILE), "SENDER_EMAIL", self.sender_var.get().strip())
        set_key(str(ENV_FILE), "SENDER_PASSWORD", self.password_var.get().strip())
        set_key(str(ENV_FILE), "RECIPIENT_EMAIL", self.recipient_var.get().strip())

    def _build_ui(self) -> None:
        title_font = ("Segoe UI", 11, "bold")
        label_font = ("Segoe UI", 9)
        entry_font = ("Consolas", 9)
        status_font = ("Segoe UI", 10, "bold")

        header = tk.Frame(self.root, bg="#0d47a1", height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Auto IT News Mailer",
            font=("Segoe UI", 15, "bold"),
            fg="white",
            bg="#0d47a1",
        ).pack(side="left", padx=20, pady=16)
        tk.Label(
            header,
            text="Automated daily IT news delivery",
            font=("Segoe UI", 9),
            fg="#90caf9",
            bg="#0d47a1",
        ).pack(side="left", pady=20)

        status_bar = tk.Frame(self.root, bg="#16213e", height=42)
        status_bar.pack(fill="x")
        status_bar.pack_propagate(False)
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            font=status_font,
            fg="#42a5f5",
            bg="#16213e",
        ).pack(side="left", padx=16, pady=10)
        tk.Label(
            status_bar,
            text="Last sent:",
            font=label_font,
            fg="#546e7a",
            bg="#16213e",
        ).pack(side="left", padx=(20, 4))
        tk.Label(
            status_bar,
            textvariable=self.last_sent_var,
            font=label_font,
            fg="#90caf9",
            bg="#16213e",
        ).pack(side="left")
        tk.Label(
            status_bar,
            text="Next send:",
            font=label_font,
            fg="#546e7a",
            bg="#16213e",
        ).pack(side="left", padx=(20, 4))
        tk.Label(
            status_bar,
            textvariable=self.next_send_var,
            font=label_font,
            fg="#90caf9",
            bg="#16213e",
        ).pack(side="left")

        content = tk.Frame(self.root, bg="#0f1117")
        content.pack(fill="both", expand=True, padx=16, pady=12)

        left = tk.Frame(content, bg="#0f1117")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self._card(
            left,
            "API and Email Credentials",
            [
                ("NewsAPI Key", self.api_key_var, False),
                ("Sender Gmail", self.sender_var, False),
                ("Gmail App Password", self.password_var, True),
                ("Recipient Email(s)", self.recipient_var, False),
            ],
        )

        sched_card = tk.LabelFrame(
            left,
            text="  Schedule Settings  ",
            font=title_font,
            fg="#42a5f5",
            bg="#1a1d27",
            bd=1,
            relief="solid",
            labelanchor="nw",
        )
        sched_card.pack(fill="x", pady=(0, 10))

        row1 = tk.Frame(sched_card, bg="#1a1d27")
        row1.pack(fill="x", padx=14, pady=10)
        tk.Label(
            row1,
            text="Send Time (24h):",
            font=label_font,
            fg="#90a4ae",
            bg="#1a1d27",
            width=18,
            anchor="w",
        ).pack(side="left")
        tk.Entry(
            row1,
            textvariable=self.send_time,
            font=entry_font,
            bg="#0f1117",
            fg="#e3e8f0",
            insertbackground="white",
            bd=0,
            highlightthickness=1,
            highlightbackground="#2a2d3e",
            width=10,
        ).pack(side="left", padx=(0, 20), ipady=4)
        tk.Label(
            row1,
            text="Max Articles:",
            font=label_font,
            fg="#90a4ae",
            bg="#1a1d27",
        ).pack(side="left")
        tk.Spinbox(
            row1,
            from_=5,
            to=15,
            textvariable=self.articles_var,
            font=entry_font,
            bg="#0f1117",
            fg="#e3e8f0",
            buttonbackground="#2a2d3e",
            bd=0,
            highlightthickness=1,
            highlightbackground="#2a2d3e",
            width=4,
        ).pack(side="left", padx=8, ipady=4)

        btn_frame = tk.Frame(left, bg="#0f1117")
        btn_frame.pack(fill="x", pady=4)

        self.start_btn = tk.Button(
            btn_frame,
            text="Start Scheduler",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg="#1565c0",
            activebackground="#0d47a1",
            activeforeground="white",
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            command=self._start_scheduler,
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = tk.Button(
            btn_frame,
            text="Stop",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg="#37474f",
            activebackground="#263238",
            activeforeground="white",
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            state="disabled",
            command=self._stop_scheduler,
        )
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.test_btn = tk.Button(
            btn_frame,
            text="Send Now",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg="#2e7d32",
            activebackground="#1b5e20",
            activeforeground="white",
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            command=self._send_now,
        )
        self.test_btn.pack(side="left")

        log_frame = tk.LabelFrame(
            left,
            text="  Activity Log  ",
            font=title_font,
            fg="#42a5f5",
            bg="#1a1d27",
            bd=1,
            relief="solid",
        )
        log_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 8),
            bg="#0a0d14",
            fg="#80cbc4",
            insertbackground="white",
            bd=0,
            wrap="word",
            state="disabled",
            height=10,
        )
        self.log_box.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_box.tag_config("info", foreground="#80cbc4")
        self.log_box.tag_config("success", foreground="#69f0ae")
        self.log_box.tag_config("error", foreground="#ef5350")
        self.log_box.tag_config("warn", foreground="#ffca28")

    def _card(self, parent: tk.Widget, title: str, fields: list[tuple[str, tk.StringVar, bool]]) -> None:
        card = tk.LabelFrame(
            parent,
            text=f"  {title}  ",
            font=("Segoe UI", 11, "bold"),
            fg="#42a5f5",
            bg="#1a1d27",
            bd=1,
            relief="solid",
            labelanchor="nw",
        )
        card.pack(fill="x", pady=(0, 10))

        for label, variable, secret in fields:
            row = tk.Frame(card, bg="#1a1d27")
            row.pack(fill="x", padx=14, pady=5)
            tk.Label(
                row,
                text=f"{label}:",
                font=("Segoe UI", 9),
                fg="#90a4ae",
                bg="#1a1d27",
                width=20,
                anchor="w",
            ).pack(side="left")
            entry = tk.Entry(
                row,
                textvariable=variable,
                show="*" if secret else "",
                font=("Consolas", 9),
                bg="#0f1117",
                fg="#e3e8f0",
                insertbackground="white",
                bd=0,
                highlightthickness=1,
                highlightbackground="#2a2d3e",
            )
            entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 4))

        tk.Frame(card, bg="#1a1d27", height=6).pack()

    def _log(self, message: str, level: str = "info") -> None:
        def _do() -> None:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"[{timestamp}]  {message}\n", level)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.root.after(0, _do)

    def _validate(self) -> bool:
        missing = []
        if not self.api_key_var.get().strip():
            missing.append("NewsAPI Key")
        if not self.sender_var.get().strip():
            missing.append("Sender Gmail")
        if not self.password_var.get().strip():
            missing.append("Gmail App Password")
        if not self.recipient_var.get().strip():
            missing.append("Recipient Email")

        if missing:
            messagebox.showerror("Missing Fields", "Please fill in:\n- " + "\n- ".join(missing))
            return False

        try:
            datetime.strptime(self.send_time.get().strip(), "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Send time must be in HH:MM format, for example 08:00.")
            return False

        try:
            value = int(self.articles_var.get())
        except ValueError:
            messagebox.showerror("Invalid Count", "Max Articles must be a number.")
            return False

        if value < 1:
            messagebox.showerror("Invalid Count", "Max Articles must be at least 1.")
            return False

        return True

    def _run_pipeline(self) -> None:
        self._log("Starting pipeline...")
        try:
            self._save_config()

            self._log("Fetching news from NewsAPI...")
            raw_articles = fetch_it_news()
            self._log(f"Got {len(raw_articles)} raw articles.")

            articles = filter_news_core(raw_articles) if raw_articles else []
            if not articles:
                self._log("No IT articles found after filtering.", "warn")

            self._log("Sending email via Gmail SMTP...")
            success = send_email_core(articles)

            if success:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                self.last_sent_var.set(now)
                self._log(f"Email sent successfully at {now}.", "success")
            else:
                self._log("Email failed. Check the log above for details.", "error")
        except Exception as exc:
            self._log(f"Error: {exc}", "error")

    def _scheduler_loop(self) -> None:
        send_time = self.send_time.get().strip()
        schedule.clear()
        schedule.every().day.at(send_time).do(self._run_pipeline)
        self._log(f"Scheduler running. Daily send at {send_time}.", "success")

        next_run = schedule.next_run()
        if next_run:
            self.next_send_var.set(next_run.strftime("%H:%M (%b %d)"))

        while self.is_running:
            schedule.run_pending()
            time.sleep(30)

        self._log("Scheduler stopped.", "warn")

    def _start_scheduler(self) -> None:
        if not self._validate():
            return

        self._save_config()
        self.is_running = True
        self.status_var.set("Running")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.test_btn.config(state="disabled")

        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self._log(f"Scheduler started. Daily send at {self.send_time.get().strip()}.", "success")

    def _stop_scheduler(self) -> None:
        self.is_running = False
        schedule.clear()
        self.status_var.set("Stopped")
        self.next_send_var.set("-")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.test_btn.config(state="normal")
        self._log("Scheduler stopped by user.", "warn")

    def _send_now(self) -> None:
        if not self._validate():
            return

        self._log("Manual send triggered...")
        threading.Thread(target=self._run_pipeline, daemon=True).start()

    def on_close(self) -> None:
        if self.is_running:
            if messagebox.askyesno("Quit", "Scheduler is running.\nStop it and quit?"):
                self._stop_scheduler()
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoMailerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.update_idletasks()
    width, height = root.winfo_width(), root.winfo_height()
    x_pos = (root.winfo_screenwidth() - width) // 2
    y_pos = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
    root.mainloop()
