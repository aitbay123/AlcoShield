import serial
import requests
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

SERIAL_PORT = 'COM15'
BAUD_RATE = 115200
BOT_TOKEN = '8446990872:AAEyg63AiQvcH448g07TmlUpCtvVsrMqeZ8'
CHAT_ID = '8320821009'
THRESHOLD_VALUE = 850
TELEGRAM_SENT_FLAG = False

FIXED_LATITUDE = 44.822397  
FIXED_LONGITUDE = 65.489347
LOCATION_INFO = "Точное фиксированное местоположение"
CURRENT_LAT = FIXED_LATITUDE
CURRENT_LON = FIXED_LONGITUDE

def get_fixed_location():
    global CURRENT_LAT, CURRENT_LON, LOCATION_INFO
    CURRENT_LAT = FIXED_LATITUDE
    CURRENT_LON = FIXED_LONGITUDE
    LOCATION_INFO = "Точное фиксированное местоположение"
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Геолокация: {LOCATION_INFO}, Широта: {CURRENT_LAT}, Долгота: {CURRENT_LON}")
    return

def send_telegram_location(latitude, longitude, caption):
    if latitude is None or longitude is None:
        send_telegram_message("⚠️ КРИТИЧЕСКИЙ УРОВЕНЬ АЛКОГОЛЯ! Местоположение неизвестно.")
        return

    url_location = f"https://api.telegram.org/bot{BOT_TOKEN}/sendLocation"
    try:
        requests.post(url_location, data={
            'chat_id': CHAT_ID,
            'latitude': latitude,
            'longitude': longitude
        }).raise_for_status()
        
        send_telegram_message(caption)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Уведомление отправлено.")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Ошибка Telegram: {e}")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': text}).raise_for_status()
    except requests.exceptions.RequestException:
        pass

class SerialMonitorApp:
    def __init__(self, master):
        self.master = master
        master.title("NodeMCU Alco-Blocker Monitor")
        master.geometry("500x350")
        
        self.alcohol_level = tk.StringVar(value="---")
        self.status_message = tk.StringVar(value="Ожидание данных...")
        self.geo_status = tk.StringVar(value=f"Geo: {LOCATION_INFO}")
        
        self.is_running = True
        self.telegram_sent_flag = False
        
        self.create_widgets()
        
        threading.Thread(target=get_fixed_location, daemon=True).start()
        
        self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
        self.serial_thread.start()

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("Data.TLabel", font=("Helvetica", 28, "bold"), foreground="#007bff")
        style.configure("Status.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("Alarm.TLabel", foreground="#dc3545")

        main_frame = ttk.Frame(self.master, padding="15")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Уровень алкоголя (A0):", style="TLabel").pack(pady=(10, 0))

        self.level_label = ttk.Label(main_frame, textvariable=self.alcohol_level, style="Data.TLabel")
        self.level_label.pack(pady=5)
        
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(main_frame, text="СТАТУС СИСТЕМЫ:", style="TLabel").pack()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_message, style="Status.TLabel")
        self.status_label.pack(pady=5)
        
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=(15, 0))
        
        ttk.Label(info_frame, text=f"COM: {SERIAL_PORT}@{BAUD_RATE}", style="TLabel").pack(side="left")
        self.geo_label = ttk.Label(info_frame, textvariable=self.geo_status, style="TLabel")
        self.geo_label.pack(side="right")
        
        ttk.Button(main_frame, text="Сброс флага Telegram", command=self.reset_telegram_flag).pack(pady=10)


    def update_gui(self, level, blocked_state):
        self.alcohol_level.set(str(level))
        
        if level > THRESHOLD_VALUE:
            self.level_label.config(foreground="#dc3545")
        else:
            self.level_label.config(foreground="#007bff")
            
        if blocked_state:
            self.status_message.set("⚠️ МОТОРЫ ЗАБЛОКИРОВАНЫ")
            self.status_label.config(foreground="#dc3545")
        else:
            self.status_message.set("🟢 ДВИЖЕНИЕ РАЗРЕШЕНО")
            self.status_label.config(foreground="#28a745")

        self.geo_status.set(f"Geo: {LOCATION_INFO}")
        
    def reset_telegram_flag(self):
        self.telegram_sent_flag = False
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Флаг Telegram сброшен вручную.")
        messagebox.showinfo("Сброс", "Флаг повторной отправки уведомлений Telegram сброшен.")

    def read_serial(self):
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            ser.reset_input_buffer()
            
        except serial.SerialException as e:
            self.status_message.set(f"ОШИБКА COM: {e}")
            messagebox.showerror("Ошибка COM", f"Не удалось открыть порт {SERIAL_PORT}: {e}")
            self.is_running = False
            return

        while self.is_running:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    
                    if line.startswith("Alcohol Level (A0):"):
                        try:
                            alcohol_level = int(line.split(':')[1].strip())
                            is_blocked = (alcohol_level > THRESHOLD_VALUE) 

                            self.master.after(0, self.update_gui, alcohol_level, is_blocked)

                            # Логика отправки: сообщение отправляется ТОЛЬКО один раз (когда флаг False)
                            if alcohol_level > THRESHOLD_VALUE and not self.telegram_sent_flag:
                                self.telegram_sent_flag = True
                                
                                threading.Thread(target=get_fixed_location, daemon=True).start()
                                
                                caption = (
                                    f"⚠️ КРИТИЧЕСКИЙ УРОВЕНЬ АЛКОГОЛЯ!\n"
                                    f"Значение: {alcohol_level}\n"
                                    f"Источник: {LOCATION_INFO}"
                                )
                                
                                threading.Thread(target=send_telegram_location, 
                                                 args=(CURRENT_LAT, CURRENT_LON, caption), 
                                                 daemon=True).start()

                            # Сброс флага: позволяет отправить новое сообщение, как только уровень падает ниже порога
                            elif alcohol_level <= THRESHOLD_VALUE and self.telegram_sent_flag:
                                self.telegram_sent_flag = False

                        except (ValueError, IndexError):
                            pass
                
                time.sleep(0.1) 

            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Критическая ошибка в потоке Serial: {e}")
                self.is_running = False
                break
        
        ser.close()

    def on_closing(self):
        self.is_running = False
        if self.serial_thread.is_alive():
            self.serial_thread.join(timeout=1)
        self.master.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = SerialMonitorApp(root)
    root.mainloop()