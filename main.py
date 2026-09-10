import os, sys, threading
import customtkinter as ctk
from tkinter import filedialog
import watcher

ctk.set_appearance_mode("System")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ISO2GOD Utility")
        self.geometry("640x590")
        self.resizable(False, False)
        bg_color = "#1E1E1E" if ctk.get_appearance_mode() == "Dark" else "#F5F5F7"
        self.configure(fg_color=bg_color)
        self.iso_path = ""
        self.god_path = ""
        self.out_path = os.path.expanduser("~/Desktop")
        
        self.lbl = ctk.CTkLabel(self, text="ISO2GOD Utility", font=("SF Pro Display", 18, "bold"))
        self.lbl.pack(pady=(20, 15))
        
        self.frame_mode = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_mode.pack(fill="x", pady=(5, 5), padx=30)
        ctk.CTkLabel(self.frame_mode, text="Operation Mode:", font=("SF Pro Text", 13, "bold")).pack(side="left", padx=(0, 10))
        self.mode_menu = ctk.CTkOptionMenu(
            self.frame_mode, values=["ISO to GOD (Standard)", "GOD to ISO (Reverse)"],
            font=("SF Pro Text", 13), corner_radius=6,
            fg_color=("#007AFF", "#0A84FF"), button_color=("#0062CC", "#007AFF"), command=self.toggle_mode
        )
        self.mode_menu.pack(side="left")
        
        self.frame_file = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_file.pack(fill="x", pady=(10, 5), padx=30)
        self.btn_browse = ctk.CTkButton(
            self.frame_file, text="Browse ISO...", font=("SF Pro Text", 13), corner_radius=6,
            fg_color=("#007AFF", "#0A84FF"), hover_color=("#0062CC", "#007AFF"), text_color="#FFFFFF", width=120, command=self.sel_file
        )
        self.btn_browse.pack(side="left", padx=(0, 15))
        self.lbl_file_name = ctk.CTkLabel(self.frame_file, text="No file selected", font=("SF Pro Text", 13), text_color=("#8E8E93", "#98989D"))
        self.lbl_file_name.pack(side="left")
        
        self.chk_ftp = ctk.CTkCheckBox(
            self, text="Enable Automated Post-Conversion FTP Upload", font=("SF Pro Text", 13),
            corner_radius=4, checkbox_width=18, checkbox_height=18, fg_color=("#007AFF", "#0A84FF"), command=self.toggle_ftp_drawer
        )
        self.chk_ftp.pack(anchor="w", padx=30, pady=(15, 10))

        self.frame_ftp_drawer = ctk.CTkFrame(self, fg_color=("#E5E5EA", "#2C2C2E"), corner_radius=10)
        self.frame_toggles = ctk.CTkFrame(self.frame_ftp_drawer, fg_color="transparent")
        self.frame_toggles.pack(fill="x", padx=15, pady=(10, 5))
        self.chk_custom_ip = ctk.CTkCheckBox(
            self.frame_toggles, text="Modify Network IP/Port", font=("SF Pro Text", 12),
            checkbox_width=16, checkbox_height=16, fg_color=("#007AFF", "#0A84FF"), command=self.refresh_sub_forms
        )
        self.chk_custom_ip.pack(side="left", padx=(0, 20))
        self.chk_custom_path = ctk.CTkCheckBox(
            self.frame_toggles, text="Modify Store Path", font=("SF Pro Text", 12),
            checkbox_width=16, checkbox_height=16, fg_color=("#007AFF", "#0A84FF"), command=self.refresh_sub_forms
        )
        self.chk_custom_path.pack(side="left")
        
        self.entry_kwargs = {"font": ("SF Pro Text", 12), "corner_radius": 6, "border_width": 1, "fg_color": ("#FFFFFF", "#1C1C1E"), "border_color": ("#C7C7CC", "#3A3A3C")}
        self.sub_frame_ip = ctk.CTkFrame(self.frame_ftp_drawer, fg_color="transparent")
        ctk.CTkLabel(self.sub_frame_ip, text="Console IP:", font=("SF Pro Text", 12)).grid(row=0, column=0, padx=(10, 5), pady=5, sticky="e")
        self.entry_ip = ctk.CTkEntry(self.sub_frame_ip, placeholder_text="192.168.1.50", width=130, **self.entry_kwargs)
        self.entry_ip.grid(row=0, column=1, padx=(0, 15), pady=5)
        self.entry_ip.insert(0, "192.168.1.50")
        ctk.CTkLabel(self.sub_frame_ip, text="Port:", font=("SF Pro Text", 12)).grid(row=0, column=2, padx=(5, 5), pady=5, sticky="e")
        self.entry_port = ctk.CTkEntry(self.sub_frame_ip, placeholder_text="21", width=50, **self.entry_kwargs)
        self.entry_port.grid(row=0, column=3, pady=5)
        self.entry_port.insert(0, "21")
        
        self.sub_frame_path = ctk.CTkFrame(self.frame_ftp_drawer, fg_color="transparent")
        ctk.CTkLabel(self.sub_frame_path, text="Remote Path:", font=("SF Pro Text", 12)).grid(row=0, column=0, padx=(10, 5), pady=5, sticky="e")
        self.entry_target_dir = ctk.CTkEntry(self.sub_frame_path, placeholder_text="Hdd1/Content/0000000000000000/", width=280, **self.entry_kwargs)
        self.entry_target_dir.grid(row=0, column=1, pady=5)
        self.entry_target_dir.insert(0, "Hdd1/Content/0000000000000000/")

        self.log_text = ctk.CTkTextbox(self, height=140, width=580, font=("SF Pro Text", 13), corner_radius=8, border_width=1, fg_color=("#FFFFFF", "#1C1C1E"), border_color=("#E5E5EA", "#2C2C2E"), text_color=("#000000", "#FFFFFF"))
        self.log_text.pack(pady=(15, 5), padx=30)
        self.append_log("✅ Ready!")

        self.frame_metrics = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_metrics.pack(fill="x", padx=35, pady=(5, 0))
        metric_font = ("SF Pro Text", 11, "bold")
        value_font = ("SF Pro Text", 11)
        txt_sec_color = ("#636366", "#AEAEB2")
        self.lbl_pct_t = ctk.CTkLabel(self.frame_metrics, text="Done: ", font=metric_font)
        self.lbl_pct_t.pack(side="left")
        self.lbl_pct = ctk.CTkLabel(self.frame_metrics, text="0%", font=value_font, text_color=txt_sec_color)
        self.lbl_pct.pack(side="left", padx=(0, 15))
        self.lbl_rem_t = ctk.CTkLabel(self.frame_metrics, text="Remaining: ", font=metric_font)
        self.lbl_rem_t.pack(side="left")
        self.lbl_rem = ctk.CTkLabel(self.frame_metrics, text="100%", font=value_font, text_color=txt_sec_color)
        self.lbl_rem.pack(side="left", padx=(0, 15))
        self.lbl_speed_t = ctk.CTkLabel(self.frame_metrics, text="Speed: ", font=metric_font)
        self.lbl_speed_t.pack(side="left")
        self.lbl_speed = ctk.CTkLabel(self.frame_metrics, text="--", font=value_font, text_color=txt_sec_color)
        self.lbl_speed.pack(side="left", padx=(0, 15))
        self.lbl_eta_t = ctk.CTkLabel(self.frame_metrics, text="ETA: ", font=metric_font)
        self.lbl_eta_t.pack(side="left")
        self.lbl_eta = ctk.CTkLabel(self.frame_metrics, text="--", font=value_font, text_color=txt_sec_color)
        self.lbl_eta.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(self, width=580, height=6, corner_radius=3, fg_color=("#E5E5EA", "#2C2C2E"), progress_color=("#007AFF", "#0A84FF"))
        self.progress_bar.pack(pady=(5, 15), padx=30)
        self.progress_bar.set(0.0)
        
        self.btn_go = ctk.CTkButton(self, text="Start Action", font=("SF Pro Text", 13, "bold"), corner_radius=6, fg_color=("#007AFF", "#0A84FF"), hover_color=("#0062CC", "#007AFF"), text_color="#FFFFFF", height=36, width=200)
        self.btn_go.configure(command=self.run_engine)
        self.btn_go.pack(pady=(0, 20))

    def toggle_ftp_drawer(self):
        if self.chk_ftp.get():
            self.frame_ftp_drawer.pack(pady=5, padx=30, fill="x", after=self.chk_ftp)
            self.refresh_sub_forms()
        else:
            self.frame_ftp_drawer.pack_forget()

    def refresh_sub_forms(self):
        if self.chk_custom_ip.get(): self.sub_frame_ip.pack(fill="x", padx=15, pady=(5, 10), before=self.sub_frame_path if self.chk_custom_path.get() else None)
        else: self.sub_frame_ip.pack_forget()
        if self.chk_custom_path.get(): self.sub_frame_path.pack(fill="x", padx=15, pady=(5, 10))
        else: self.sub_frame_path.pack_forget()

    def toggle_mode(self, current_choice):
        if "Reverse" in current_choice:
            self.btn_browse.configure(text="Browse GOD...")
            self.chk_ftp.configure(state="disabled")
            if self.chk_ftp.get(): self.chk_ftp.deselect(); self.toggle_ftp_drawer()
        else:
            self.btn_browse.configure(text="Browse ISO...")
            self.chk_ftp.configure(state="normal")

    def sel_file(self):
        current_choice = self.mode_menu.get()
        if "Reverse" in current_choice:
            self.god_path = filedialog.askopenfilename(title="Select GOD Master Identification File")
            if self.god_path: self.lbl_file_name.configure(text=os.path.basename(self.god_path))
        else:
            self.iso_path = filedialog.askopenfilename(filetypes=[("Xbox 360 ISO images", "*.iso")])
            if self.iso_path: self.lbl_file_name.configure(text=os.path.basename(self.iso_path))
            
    def append_log(self, text):
        self.log_text.configure(state="normal"); self.log_text.insert("end", text + "\n"); self.log_text.see("end"); self.log_text.configure(state="disabled")
        
    def update_progress(self, value, pct_done="0%", pct_rem="100%", eta="--", speed="--"):
        self.progress_bar.set(value); self.lbl_pct.configure(text=pct_done); self.lbl_rem.configure(text=pct_rem); self.lbl_eta.configure(text=eta); self.lbl_speed.configure(text=speed)
        
    def run_engine(self):
        current_choice = self.mode_menu.get()
        if "Reverse" in current_choice:
            if not self.god_path: return
            out_iso = filedialog.asksaveasfilename(defaultextension=".iso", filetypes=[("ISO Images", "*.iso")])
            if out_iso: threading.Thread(target=watcher.run_reverse_engine, args=(self.god_path, out_iso, self.append_log, self.update_progress), daemon=True).start()
        else:
            ip = self.entry_ip.get() if (self.chk_ftp.get() and self.chk_custom_ip.get()) else ("192.168.1.50" if self.chk_ftp.get() else "")
            threading.Thread(target=watcher.convert_and_upload, args=(self.iso_path, self.out_path, ip, "xbox", "xbox", self.append_log, self.update_progress), daemon=True).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
