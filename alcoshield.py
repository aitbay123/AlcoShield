import requests
import asyncio
import geocoder
from aiogram import Bot, Dispatcher, types
import tkinter as tk
from tkinter import messagebox
from twilio.rest import Client
import threading
import time

# Telegram Bot Token
TOKEN = "8047510722:AAGJuvMZweRNiIeG3C3OILrW1-fAW8fNFR0"
CHAT_IDS = ["1705362210", "7978568198"]  # Список ID получателей

# URL сервера NodeMCU
NODEMCU_URL = "http://192.168.110.201/data"

# Интерфейс Tkinter
app = tk.Tk()
app.title("Детектор Алкоголя")
app.geometry("500x400")
tk.Label(app, text="Номер телефона").pack(pady=5)
phone_number = tk.Entry(app)
phone_number.pack(pady=5)

# Переключатель для выбора способа отправки сообщения
message_method = tk.StringVar(value="sms")  # По умолчанию SMS
tk.Label(app, text="Выберите способ отправки сообщения:").pack(pady=5)
tk.Radiobutton(app, text="SMS", variable=message_method, value="sms").pack(pady=5)
tk.Radiobutton(app, text="Telegram", variable=message_method, value="telegram").pack(pady=5)

tk.Label(app, text="Данные с датчика").pack(pady=5)
sensor_output = tk.Text(app, height=10, width=50)
sensor_output.pack(pady=5)

button_frame = tk.Frame(app)
button_frame.pack(pady=10)
monitoring = tk.BooleanVar(value=False)

# Функция для получения геолокации
def get_location():
    response = requests.get('https://ipinfo.io/json')
    location_data = response.json()
    loc = location_data['loc'].split(',')
    latitude = loc[0]
    longitude = loc[1]
    return latitude, longitude

# Функция отправки SMS
def send_sms(body, to_phone_number):
    account_sid = 'AC2531f63131fcde94961d73adbf3c3f2b'
    auth_token = '62a452e4fcd046361ce874c404dfcedf'
    from_phone_number = '+15053905827'

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=body,
        from_=from_phone_number,
        to=to_phone_number
    )

    messagebox.showinfo("Сообщение отправлено", f"Сообщение отправлено с SID: {message.sid}")

# Функция для отправки сообщения через Telegram
async def send_telegram_message(message_body):
    bot = Bot(token=TOKEN)
    for chat_id in CHAT_IDS:
        await bot.send_message(chat_id, message_body)
    messagebox.showinfo("Сообщение отправлено", "Сообщение отправлено через Telegram")

# Функция мониторинга с датчика
async def monitor_sensor():
    try:
        while True:
            response = requests.get(NODEMCU_URL)
            if response.status_code == 200:
                data = response.json()
                sensor_value = data.get("value", 0)
                sensor_output.insert(tk.END, f"Sensor values: {sensor_value}\n")
                sensor_output.see(tk.END)

                if sensor_value > 850:  # Условие для тревоги
                    latitude, longitude = get_location()
                    google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                    message_body = f"⚠️ Sensor showed {sensor_value}! Link to geolocation: {google_maps_link} ,please pick up Beka "

                    if message_method.get() == "sms":  # Отправка через SMS
                        send_sms(message_body, phone_number.get())
                    else:  # Отправка через Telegram
                        await send_telegram_message(message_body)
            else:
                print("Ошибка запроса к NodeMCU")

            await asyncio.sleep(10)  # Проверять каждые 10 секунд
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

# Функция для начала мониторинга
def start_monitoring():
    monitoring.set(True)
    threading.Thread(target=lambda: asyncio.run(monitor_sensor()), daemon=True).start()

# Функция для остановки мониторинга
def stop_monitoring():
    monitoring.set(False)

# Интерфейс кнопок для запуска/остановки мониторинга
start_button = tk.Button(button_frame, text="Start monitoring", command=start_monitoring)
start_button.grid(row=0, column=0, padx=5)
stop_button = tk.Button(button_frame, text="Stop monitoring", command=stop_monitoring)
stop_button.grid(row=0, column=1, padx=5)

# Запуск интерфейса Tkinter
app.mainloop()
