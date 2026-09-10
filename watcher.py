import os, time, sys, subprocess, ftplib, threading, re

class ProgressFTP(ftplib.FTP):
    def __init__(self, host, user, passwd, log_callback, progress_callback, total_size):
        super().__init__(host, user, passwd, timeout=10)
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.total_size = total_size
        self.bytes_transferred = 0
        self.start_time = time.time()
        self.last_update_time = time.time()

    def upload_with_progress(self, local_path, remote_name):
        with open(local_path, 'rb') as f:
            self.storbinary(f'STOR {remote_name}', f, blocksize=1024*1024, callback=self.handle_chunk)

    def handle_chunk(self, chunk):
        self.bytes_transferred += len(chunk)
        current_time = time.time()
        if current_time - self.last_update_time >= 0.5 or self.bytes_transferred == self.total_size:
            elapsed = current_time - self.start_time
            speed = self.bytes_transferred / elapsed if elapsed > 0 else 0
            pct = (self.bytes_transferred / self.total_size) if self.total_size > 0 else 0
            remaining_bytes = max(0, self.total_size - self.bytes_transferred)
            eta = remaining_bytes / speed if speed > 0 else 0
            scaled_bar = 0.50 + (pct * 0.50)
            self.progress_callback(
                scaled_bar, f"{int(pct*100)}%", f"{int((1-pct)*100)}%", f"{eta:.1f}s" if eta > 0 else "--", f"{speed / (1024*1024):.2f} MB/s"
            )
            self.last_update_time = current_time

def run_reverse_engine(god_path, out_iso_path, log_callback, progress_callback):
    log_callback(f"🔄 Reversing GOD Container target: {os.path.basename(god_path)}")
    progress_callback(0.10, "10%", "90%", "--", "--")
    binary = "god2iso"
    for p in [os.path.expanduser("~/god2iso-backend/target/release/god2iso"), "god2iso"]:
        if os.path.exists(p): binary = p; break
    cmd = [binary, god_path, out_iso_path]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            clean_line = line.strip()
            if clean_line:
                log_callback(f"💬 {clean_line}")
                match = re.search(r'(\d+)%', clean_line)
                if match:
                    pct = float(match.group(1)) / 100.0
                    progress_callback(pct, f"{int(pct*100)}%", f"{int((1-pct)*100)}%", "--", "--")
        process.wait()
        if process.returncode == 0:
            log_callback(f"✅ Reverse compilation complete! Saved to: {out_iso_path}")
            progress_callback(1.0, "100%", "0%", "0s", "--")
        else:
            log_callback("❌ Reverse engine compilation failed.")
            progress_callback(0.0, "0%", "100%", "--", "--")
    except Exception as e:
        log_callback(f"❌ Error during execution: {e}")
        progress_callback(0.0, "0%", "100%", "--", "--")

def convert_and_upload(iso_path, out_dir, ip, user, pwd, log_callback, progress_callback):
    if not iso_path or not os.path.exists(iso_path):
        log_callback("❌ Error: Invalid or missing ISO path selected.")
        return
    log_callback(f"📦 Starting extraction for: {os.path.basename(iso_path)}")
    progress_callback(0.02, "0%", "100%", "--", "--")
    binary = "iso2god"
    for p in [os.path.expanduser("~/iso2god-rs-gui/target/release/iso2god"), os.path.expanduser("~/iso2god-rs-1.8.1/target/release/iso2god"), "iso2god"]:
        if os.path.exists(p): binary = p; break
    cmd = [binary, iso_path, out_dir]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            clean_line = line.strip()
            if clean_line: 
                log_callback(f"💬 {clean_line}")
                match = re.search(r'(\d+)%', clean_line)
                if match:
                    pct = float(match.group(1)) / 100.0
                    scaled_bar = pct * 0.50
                    progress_callback(scaled_bar, f"{int(pct*100)}%", f"{int((1-pct)*100)}%", "--", "--")
        process.wait()
        if process.returncode != 0:
            log_callback("❌ Conversion engine failed.")
            progress_callback(0.0, "0%", "100%", "--", "--")
            return
        log_callback("✅ Conversion completed successfully!")
        progress_callback(0.50, "100%", "0%", "0s", "--")
        generated_folders = [d for d in os.listdir(out_dir) if len(d) == 8 and os.path.isdir(os.path.join(out_dir, d))]
        if not generated_folders:
            log_callback("⚠️ Could not locate the generated GOD folder to begin upload pipeline.")
            return
        target_god_folder = os.path.join(out_dir, generated_folders)
        total_upload_size = 0
        files_to_upload = []
        for root, dirs, files in os.walk(target_god_folder):
            for file in files:
                fp = os.path.join(root, file)
                total_upload_size += os.path.getsize(fp)
                files_to_upload.append(fp)
        if ip and ip != "192.168.1.":
            log_callback(f"📡 Connecting to Xbox 360 FTP Server at {ip}...")
            try:
                ftp = ProgressFTP(ip, user, pwd, log_callback, progress_callback, total_upload_size)
                target_dir = "Hdd1/Content/0000000000000000/"
                try: ftp.cwd(target_dir)
                except:
                    ftp.mkd(target_dir)
                    ftp.cwd(target_dir)
                rel_base = os.path.dirname(target_god_folder)
                for fp in files_to_upload:
                    rel_path = os.path.relpath(fp, rel_base)
                    path_parts = rel_path.split(os.sep)
                    for i in range(len(path_parts) - 1):
                        try: ftp.mkd(path_parts[i])
                        except: pass
                        ftp.cwd(path_parts[i])
                    ftp.upload_with_progress(fp, path_parts[-1])
                    ftp.cwd("/")
                    ftp.cwd(target_dir)
                ftp.quit()
                log_callback("🏁 Upload process complete. Connection closed safely.")
            except Exception as ftp_err:
                log_callback(f"❌ FTP Failure: {ftp_err}")
        progress_callback(1.0, "100%", "0%", "0s", "--")
        time.sleep(2)
        progress_callback(0.0, "0%", "100%", "--", "--")
    except Exception as e:
        log_callback(f"❌ Structural Critical Error: {e}")
        progress_callback(0.0, "0%", "100%", "--", "--")
