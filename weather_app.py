import requests
from dotenv import load_dotenv
import os
import http_client
import json
from datetime import datetime, timedelta
import hashlib

# Загружаем переменные окружения
load_dotenv()

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API ключ не найден. Создайте файл .env с API_KEY")

CACHE_DIR = '.cache'
CACHE_DURATION = timedelta(minutes=10)

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cache_key(lat: float, lon: float, endpoint: str) -> str:
    """Генерирует ключ кэша на основе координат и endpoint"""
    key_string = f"{lat:.4f}_{lon:.4f}_{endpoint}"
    return hashlib.md5(key_string.encode()).hexdigest()

def save_to_cache_by_key(data: dict, lat: float, lon: float, endpoint: str):
    """Сохраняет данные в кэш по ключу"""
    cache_key = get_cache_key(lat, lon, endpoint)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    cache_data = {
        'fetched_at': datetime.now().isoformat(),
        'lat': lat,
        'lon': lon,
        'endpoint': endpoint,
        'data': data
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

def load_from_cache_by_key(lat: float, lon: float, endpoint: str) -> dict:
    """Загружает данные из кэша по ключу"""
    cache_key = get_cache_key(lat, lon, endpoint)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            fetched_time = datetime.fromisoformat(cached_data['fetched_at'])
            
            if datetime.now() - fetched_time < CACHE_DURATION:
                return cached_data['data']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    
    return None


def get_coordinates(city: str) -> tuple:
    """Получает координаты города"""
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['lat'], data[0]['lon']
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def get_current_weather(city: str = None, latitude: float = None, longitude: float = None) -> dict:
    if city:
        print(f"Получаем погоду для города: {city}")
        return get_weather_by_city(city)
    
    if latitude and longitude:
        print(f"Получаем погоду для координат: {latitude}, {longitude}")
        return get_weather_by_coordinates(latitude, longitude)
    
    return {"error": "Укажите город или координаты"}


def get_weather_by_coordinates(latitude: float, longitude: float) -> dict:
    cached = load_from_cache_by_key(latitude, longitude, 'weather')
    if cached:
        return cached
    
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric&lang=ru"
    
    try:
        response = http_client.get_with_retries(url)
        if response and response.status_code == 200:
            data = response.json()
            save_to_cache_by_key(data, latitude, longitude, 'weather')
            return data
        else:
            return {"error": f"Ошибка запроса: {response.status_code if response else 'Нет ответа'}"}
    except Exception as e:
        return {"error": f"Ошибка получения погоды: {e}"}


def get_weather_by_city(city: str) -> dict:
    coords = get_coordinates(city)
    if not coords:
        return {"error": "Город не найден"}
    
    lat, lon = coords
    cached = load_from_cache_by_key(lat, lon, 'weather')
    if cached:
        return cached
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
    
    try:
        response = http_client.get_with_retries(url)
        if response and response.status_code == 200:
            data = response.json()
            save_to_cache_by_key(data, lat, lon, 'weather')
            return data
        else:
            return {"error": f"Ошибка запроса: {response.status_code if response else 'Нет ответа'}"}
    except Exception as e:
        return {"error": f"Ошибка получения погоды: {e}"}


def print_weather_info(weather_data: dict):
    """Выводит данные о погоде в простом формате"""
    if "error" in weather_data:
        print(f"❌ {weather_data['error']}")
        return
    
    try:
        city = weather_data['name']
        temp = weather_data['main']['temp']
        description = weather_data['weather'][0]['description']
        print(f"Погода в {city}: {temp}°C, {description}")
    except Exception as e:
        print(f"❌ Ошибка форматирования данных: {e}")


def get_hourly_weather(latitude: float, longitude: float) -> dict:
    """Получает почасовой прогноз погоды по координатам"""
    cached = load_from_cache_by_key(latitude, longitude, 'hourly')
    if cached:
        return cached
    
    url = f"https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric&lang=ru"
    
    try:
        response = http_client.get_with_retries(url)
        if response and response.status_code == 200:
            data = response.json()
            save_to_cache_by_key(data, latitude, longitude, 'hourly')
            return data
        else:
            return {"error": f"Ошибка запроса: {response.status_code if response else 'Нет ответа'}"}
    except Exception as e:
        return {"error": f"Ошибка получения почасового прогноса: {e}"}


def get_air_pollution(latitude: float, longitude: float) -> dict:
    """Получает данные о загрязнении воздуха по координатам"""
    cached = load_from_cache_by_key(latitude, longitude, 'air_pollution')
    if cached:
        return cached
    
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={API_KEY}"
    
    try:
        response = http_client.get_with_retries(url)
        if response and response.status_code == 200:
            data = response.json()['list'][0]['components']
            save_to_cache_by_key(data, latitude, longitude, 'air_pollution')
            return data
        else:
            return {"error": f"Ошибка запроса: {response.status_code if response else 'Нет ответа'}"}
    except Exception as e:
        return {"error": f"Ошибка получения данных о загрязнении воздуха: {e}"}

def analize_air_pollution(air_pollution: dict, extended: bool = False) -> str:
    """Анализирует данные о загрязнении воздуха и возвращает статус"""
    if "error" in air_pollution:
        return air_pollution["error"]
    
    quality_levels = {
        1: "Хорошо",
        2: "Удовлетворительно", 
        3: "Умеренно",
        4: "Плохо",
        5: "Очень плохо"
    }
    
    thresholds = {
        "so2": [(0, 20, 1), (20, 80, 2), (80, 250, 3), (250, 350, 4), (350, float('inf'), 5)],
        "no2": [(0, 40, 1), (40, 70, 2), (70, 150, 3), (150, 200, 4), (200, float('inf'), 5)],
        "pm10": [(0, 20, 1), (20, 50, 2), (50, 100, 3), (100, 200, 4), (200, float('inf'), 5)],
        "pm2_5": [(0, 10, 1), (10, 25, 2), (25, 50, 3), (50, 75, 4), (75, float('inf'), 5)],
        "o3": [(0, 60, 1), (60, 100, 2), (100, 140, 3), (140, 180, 4), (180, float('inf'), 5)],
        "co": [(0, 4400, 1), (4400, 9400, 2), (9400, 12400, 3), (12400, 15400, 4), (15400, float('inf'), 5)]
    }
    
    pollutant_names = {
        "so2": "SO₂",
        "no2": "NO₂", 
        "pm10": "PM₁₀",
        "pm2_5": "PM₂.₅",
        "o3": "O₃",
        "co": "CO"
    }
    
    results = []
    max_level = 1
    
    for pollutant, ranges in thresholds.items():
        if pollutant in air_pollution:
            value = air_pollution[pollutant]
            level = 1
            
            for min_val, max_val, lvl in ranges:
                if min_val <= value < max_val:
                    level = lvl
                    break
            
            max_level = max(max_level, level)
            
            status = quality_levels[level]
            name = pollutant_names.get(pollutant, pollutant)
            results.append(f"  {name}: {value} μg/m³ [{status}]")
    
    overall_status = quality_levels[max_level]
    
    output = f"\n🌬️  Качество воздуха: {overall_status}\n"
    output += "\n".join(results)
    
    if extended:
        output += "\n\n📊 Все компоненты воздуха:"
        for component, value in air_pollution.items():
            if component not in thresholds:
                output += f"\n  {component}: {value} μg/m³"
    
    warnings = []
    if max_level >= 4:
        warnings.append("⚠️  Высокий уровень загрязнения! Ограничьте время на улице.")
    elif max_level == 3:
        warnings.append("⚠️  Умеренное загрязнение. Чувствительным людям быть осторожнее.")
    
    if warnings:
        output += "\n" + "\n".join(warnings)
    
    return output


def main():
    """Главная функция для тестирования"""
    print("🌤️  Приложение погоды")
    
    # Проверяем наличие API ключа
    if not os.getenv('API_KEY'):
        print("❌ API ключ не найден!")
        print("📝 Создайте файл .env и добавьте: API_KEY=ваш_ключ")
        print("🔗 Получить ключ: https://openweathermap.org/api")
        return
    
    while True:
        print("\n" + "="*50)
        print("1. Погода по названию города")
        print("2. Погода по координатам")
        print("0. Выход")
        
        choice = input("Выберите опцию (0-2): ").strip()
        
        if choice == "0":
            print("До свидания!")
            break
        elif choice == "1":
            city = input("Введите название города: ").strip()
            if city:
                weather = get_current_weather(city=city)
                print_weather_info(weather)
        elif choice == "2":
            try:
                lat = float(input("Введите широту: "))
                lon = float(input("Введите долготу: "))
                weather = get_current_weather(latitude=lat, longitude=lon)
                print_weather_info(weather)
            except ValueError:
                print("❌ Неверный формат координат!")
        else:
            print("❌ Неверный выбор!")

'''
if __name__ == "__main__":
    main()

'''

if __name__ == "__main__":
    latitude = 55.7558
    longitude = 37.6173
    air_pollution = get_air_pollution(latitude, longitude)
    print(analize_air_pollution(air_pollution, extended=True))
