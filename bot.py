import telebot
from telebot import types
import os
from dotenv import load_dotenv
import weather_app
import json
import threading
import time
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN: 
    raise ValueError("BOT_TOKEN не установлен")

bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    """Загружает данные пользователей из файла"""
    global user_data
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    except FileNotFoundError:
        user_data = {}

def save_user_data():
    """Сохраняет данные пользователей в файл"""
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

load_user_data()

def get_main_keyboard():
    """Создает главную клавиатуру"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('🌡️ Погода сейчас')
    btn2 = types.KeyboardButton('📅 Прогноз на 5 дней')
    btn3 = types.KeyboardButton('📍 Отправить местоположение', request_location=True)
    btn4 = types.KeyboardButton('🔔 Уведомления')
    btn5 = types.KeyboardButton('🌍 Сравнить города')
    btn6 = types.KeyboardButton('📊 Расширенные данные')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветствие и главное меню"""
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {
            'location': None,
            'notifications': False
        }
        save_user_data()
    
    welcome_text = """🌤️ Привет! Я бот погоды.

Мои возможности:
🌡️ Погода сейчас - текущая погода в городе
📅 Прогноз на 5 дней - детальный прогноз
📍 Поиск по геолокации - отправь местоположение
🔔 Уведомления - погодные оповещения каждые 2 часа
🌍 Сравнить города - сравнение погоды в двух городах
📊 Расширенные данные - полная информация о погоде

Выбери нужную функцию на клавиатуре ниже!"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())

@bot.message_handler(content_types=['location'])
def handle_location(message):
    """Обработка геолокации"""
    user_id = str(message.from_user.id)
    lat = message.location.latitude
    lon = message.location.longitude
    
    user_data[user_id]['location'] = {'lat': lat, 'lon': lon}
    save_user_data()
    
    weather = weather_app.get_current_weather(latitude=lat, longitude=lon)
    
    if "error" in weather:
        bot.send_message(message.chat.id, f"❌ {weather['error']}")
    else:
        text = format_current_weather(weather)
        bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == '🌡️ Погода сейчас')
def weather_now_handler(message):
    """Запрос текущей погоды"""
    msg = bot.send_message(message.chat.id, "Введите название города:")
    bot.register_next_step_handler(msg, get_weather_now)

def get_weather_now(message):
    """Получает текущую погоду по городу"""
    city = message.text.strip()
    weather = weather_app.get_current_weather(city=city)
    
    if "error" in weather:
        bot.send_message(message.chat.id, f"❌ {weather['error']}")
    else:
        text = format_current_weather(weather)
        bot.send_message(message.chat.id, text, parse_mode='HTML')

def format_current_weather(weather):
    """Форматирует данные о текущей погоде"""
    try:
        city = weather['name']
        temp = weather['main']['temp']
        feels_like = weather['main']['feels_like']
        humidity = weather['main']['humidity']
        pressure = weather['main']['pressure']
        wind_speed = weather['wind']['speed']
        description = weather['weather'][0]['description'].capitalize()
        
        text = f"""🌤️ <b>Погода в {city}</b>

🌡️ Температура: {temp}°C (ощущается как {feels_like}°C)
💧 Влажность: {humidity}%
🌪️ Ветер: {wind_speed} м/с
🔽 Давление: {pressure} hPa
☁️ {description}"""
        return text
    except Exception as e:
        return f"❌ Ошибка форматирования данных: {e}"

@bot.message_handler(func=lambda message: message.text == '📅 Прогноз на 5 дней')
def forecast_handler(message):
    """Прогноз на 5 дней"""
    user_id = str(message.from_user.id)
    
    if user_id not in user_data or not user_data[user_id].get('location'):
        bot.send_message(message.chat.id, "📍 Сначала отправьте ваше местоположение!")
        return
    
    location = user_data[user_id]['location']
    forecast = get_5day_forecast(location['lat'], location['lon'])
    
    if "error" in forecast:
        bot.send_message(message.chat.id, f"❌ {forecast['error']}")
        return
    
    show_forecast_menu(message.chat.id, forecast)

def get_5day_forecast(lat, lon):
    """Получает прогноз на 5 дней"""
    cached = weather_app.load_from_cache_by_key(lat, lon, 'forecast5d')
    if cached:
        return cached
    
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={weather_app.API_KEY}&units=metric&lang=ru"
    
    try:
        response = weather_app.http_client.get_with_retries(url)
        if response and response.status_code == 200:
            data = response.json()
            weather_app.save_to_cache_by_key(data, lat, lon, 'forecast5d')
            return data
        else:
            return {"error": "Ошибка получения прогноза"}
    except Exception as e:
        return {"error": str(e)}

def show_forecast_menu(chat_id, forecast_data, message_id=None):
    """Показывает меню прогноза на 5 дней"""
    days = {}
    
    for item in forecast_data['list']:
        date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
        if date not in days:
            days[date] = []
        days[date].append(item)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for date in list(days.keys())[:5]:
        day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m (%a)')
        avg_temp = sum(d['main']['temp'] for d in days[date]) / len(days[date])
        btn_text = f"{day_name} | {avg_temp:.1f}°C"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"day_{date}"))
    
    text = "📅 <b>Прогноз погоды на 5 дней</b>\n\nВыберите день для детальной информации:"
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('day_'))
def show_day_details(call):
    """Показывает детали конкретного дня"""
    user_id = str(call.from_user.id)
    date = call.data.replace('day_', '')
    
    if user_id not in user_data or not user_data[user_id].get('location'):
        bot.answer_callback_query(call.id, "❌ Местоположение не найдено")
        return
    
    location = user_data[user_id]['location']
    forecast = get_5day_forecast(location['lat'], location['lon'])
    
    day_data = [item for item in forecast['list'] 
                if datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d') == date]
    
    if not day_data:
        bot.answer_callback_query(call.id, "❌ Данные не найдены")
        return
    
    text = f"📅 <b>Прогноз на {datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')}</b>\n\n"
    
    for item in day_data[:8]:
        time = datetime.fromtimestamp(item['dt']).strftime('%H:%M')
        temp = item['main']['temp']
        desc = item['weather'][0]['description']
        text += f"🕐 {time}: {temp}°C, {desc}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_forecast"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                         parse_mode='HTML', reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_forecast')
def back_to_forecast(call):
    """Возврат к меню прогноза"""
    user_id = str(call.from_user.id)
    
    if user_id not in user_data or not user_data[user_id].get('location'):
        bot.answer_callback_query(call.id, "❌ Местоположение не найдено")
        return
    
    location = user_data[user_id]['location']
    forecast = get_5day_forecast(location['lat'], location['lon'])
    
    show_forecast_menu(call.message.chat.id, forecast, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text == '🔔 Уведомления')
def notifications_handler(message):
    """Управление уведомлениями"""
    user_id = str(message.from_user.id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    status = user_data.get(user_id, {}).get('notifications', False)
    
    if status:
        btn = types.InlineKeyboardButton("❌ Отключить", callback_data="notif_off")
        text = "🔔 Уведомления <b>включены</b>\n\nВы получаете погодные оповещения каждые 2 часа."
    else:
        btn = types.InlineKeyboardButton("✅ Включить", callback_data="notif_on")
        text = "🔕 Уведомления <b>отключены</b>\n\nВключите их, чтобы получать погодные оповещения."
    
    markup.add(btn)
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['notif_on', 'notif_off'])
def toggle_notifications(call):
    """Переключает уведомления"""
    user_id = str(call.from_user.id)
    
    if call.data == 'notif_on':
        user_data[user_id]['notifications'] = True
        text = "✅ Уведомления включены!"
    else:
        user_data[user_id]['notifications'] = False
        text = "❌ Уведомления отключены!"
    
    save_user_data()
    bot.answer_callback_query(call.id, text, show_alert=True)
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: message.text == '🌍 Сравнить города')
def compare_cities_handler(message):
    """Запрос сравнения городов"""
    msg = bot.send_message(message.chat.id, "Введите два города через запятую (например: Москва, Париж):")
    bot.register_next_step_handler(msg, compare_cities)

def compare_cities(message):
    """Сравнивает погоду в двух городах"""
    try:
        cities = [c.strip() for c in message.text.split(',')]
        if len(cities) != 2:
            bot.send_message(message.chat.id, "❌ Введите ровно два города через запятую!")
            return
        
        weather1 = weather_app.get_current_weather(city=cities[0])
        weather2 = weather_app.get_current_weather(city=cities[1])
        
        if "error" in weather1:
            bot.send_message(message.chat.id, f"❌ {cities[0]}: {weather1['error']}")
            return
        
        if "error" in weather2:
            bot.send_message(message.chat.id, f"❌ {cities[1]}: {weather2['error']}")
            return
        
        text = format_comparison(weather1, weather2)
        bot.send_message(message.chat.id, text, parse_mode='HTML')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

def format_comparison(w1, w2):
    """Форматирует сравнение двух городов"""
    text = f"""🌍 <b>Сравнение погоды</b>

📍 <b>{w1['name']}</b> vs <b>{w2['name']}</b>

🌡️ Температура:
   {w1['name']}: {w1['main']['temp']}°C
   {w2['name']}: {w2['main']['temp']}°C
   Разница: {abs(w1['main']['temp'] - w2['main']['temp']):.1f}°C

💧 Влажность:
   {w1['name']}: {w1['main']['humidity']}%
   {w2['name']}: {w2['main']['humidity']}%

🌪️ Ветер:
   {w1['name']}: {w1['wind']['speed']} м/с
   {w2['name']}: {w2['wind']['speed']} м/с

☁️ Описание:
   {w1['name']}: {w1['weather'][0]['description']}
   {w2['name']}: {w2['weather'][0]['description']}"""
    
    return text

@bot.message_handler(func=lambda message: message.text == '📊 Расширенные данные')
def extended_data_handler(message):
    """Запрос расширенных данных"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📍 По геолокации", callback_data="ext_geo")
    btn2 = types.InlineKeyboardButton("🏙️ По городу", callback_data="ext_city")
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, "Выберите способ поиска:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'ext_geo')
def extended_by_geo(call):
    """Расширенные данные по геолокации"""
    user_id = str(call.from_user.id)
    
    if user_id not in user_data or not user_data[user_id].get('location'):
        bot.answer_callback_query(call.id, "❌ Сначала отправьте местоположение!", show_alert=True)
        return
    
    location = user_data[user_id]['location']
    show_extended_data(call.message.chat.id, lat=location['lat'], lon=location['lon'])
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'ext_city')
def extended_by_city_request(call):
    """Запрос города для расширенных данных"""
    msg = bot.send_message(call.message.chat.id, "Введите название города:")
    bot.register_next_step_handler(msg, extended_by_city)
    bot.answer_callback_query(call.id)

def extended_by_city(message):
    """Расширенные данные по городу"""
    city = message.text.strip()
    coords = weather_app.get_coordinates(city)
    
    if not coords:
        bot.send_message(message.chat.id, "❌ Город не найден!")
        return
    
    show_extended_data(message.chat.id, lat=coords[0], lon=coords[1], city=city)

def show_extended_data(chat_id, lat, lon, city=None):
    """Показывает расширенные данные о погоде"""
    weather = weather_app.get_weather_by_coordinates(lat, lon)
    air_pollution = weather_app.get_air_pollution(lat, lon)
    
    if "error" in weather:
        bot.send_message(chat_id, f"❌ {weather['error']}")
        return
    
    try:
        name = city if city else weather['name']
        temp = weather['main']['temp']
        feels_like = weather['main']['feels_like']
        humidity = weather['main']['humidity']
        pressure = weather['main']['pressure']
        wind_speed = weather['wind']['speed']
        clouds = weather['clouds']['all']
        description = weather['weather'][0]['description'].capitalize()
        
        sunrise = datetime.fromtimestamp(weather['sys']['sunrise']).strftime('%H:%M')
        sunset = datetime.fromtimestamp(weather['sys']['sunset']).strftime('%H:%M')
        
        text = f"""📊 <b>Расширенные данные: {name}</b>

🌡️ Температура: {temp}°C
🤚 Ощущается: {feels_like}°C
💧 Влажность: {humidity}%
🔽 Давление: {pressure} hPa
🌪️ Ветер: {wind_speed} м/с
☁️ Облачность: {clouds}%
🌥️ {description}

🌅 Восход: {sunrise}
🌇 Закат: {sunset}"""
        
        if not isinstance(air_pollution, dict) or "error" not in air_pollution:
            air_text = weather_app.analize_air_pollution(air_pollution, extended=True)
            text += f"\n{air_text}"
        
        bot.send_message(chat_id, text, parse_mode='HTML')
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")

def weather_notification_worker():
    """Фоновая задача для отправки уведомлений"""
    while True:
        try:
            time.sleep(7200)
            
            for user_id, data in user_data.items():
                if data.get('notifications') and data.get('location'):
                    location = data['location']
                    weather = weather_app.get_current_weather(
                        latitude=location['lat'], 
                        longitude=location['lon']
                    )
                    
                    if "error" not in weather:
                        text = f"🔔 <b>Погодное уведомление</b>\n\n"
                        text += format_current_weather(weather)
                        
                        try:
                            bot.send_message(int(user_id), text, parse_mode='HTML')
                        except:
                            pass
        except:
            pass

notification_thread = threading.Thread(target=weather_notification_worker, daemon=True)
notification_thread.start()

print("🤖 Бот запущен...")
bot.polling(none_stop=True)