import requests
import json
from colorama import init, Fore, Back, Style

# Инициализация colorama для Windows
init(autoreset=True)


def get_country_info(country_name):
    """Получает информацию о стране из API"""
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"{Fore.RED}Ошибка при запросе: {e}")
        return None


def format_country_info(country_data):
    """Форматирует и выводит информацию о стране с цветами"""
    if not country_data:
        print(f"{Fore.RED}Страна не найдена!")
        return
    
    # Берем первую страну из результата
    country = country_data[0]
    
    print(f"\n{Back.BLUE}{Fore.WHITE} ИНФОРМАЦИЯ О СТРАНЕ {Style.RESET_ALL}\n")
    
    # Название страны
    name = country.get('name', {})
    print(f"{Fore.CYAN}🌍 Название:")
    print(f"  {Fore.GREEN}Обычное: {Fore.WHITE}{name.get('common', 'Не указано')}")
    print(f"  {Fore.GREEN}Официальное: {Fore.WHITE}{name.get('official', 'Не указано')}")
    
    # Родные названия
    native_names = name.get('nativeName', {})
    if native_names:
        print(f"\n{Fore.CYAN}🗣️  Родные названия:")
        for lang, names in native_names.items():
            print(f"  {Fore.YELLOW}{lang.upper()}: {Fore.WHITE}{names.get('common', 'Не указано')}")
    
    # Столица
    capital = country.get('capital', [])
    if capital:
        print(f"\n{Fore.CYAN}🏛️  Столица: {Fore.WHITE}{', '.join(capital)}")
    
    # Регион и субрегион
    region = country.get('region', 'Не указано')
    subregion = country.get('subregion', 'Не указано')
    print(f"\n{Fore.CYAN}🗺️  География:")
    print(f"  {Fore.GREEN}Регион: {Fore.WHITE}{region}")
    print(f"  {Fore.GREEN}Субрегион: {Fore.WHITE}{subregion}")
    
    # Население
    population = country.get('population', 0)
    print(f"\n{Fore.CYAN}👥 Население: {Fore.WHITE}{population:,}")
    
    # Площадь
    area = country.get('area', 0)
    print(f"{Fore.CYAN}📏 Площадь: {Fore.WHITE}{area:,} км²")
    
    # Языки
    languages = country.get('languages', {})
    if languages:
        print(f"\n{Fore.CYAN}🗣️  Языки:")
        for code, lang in languages.items():
            print(f"  {Fore.YELLOW}{code}: {Fore.WHITE}{lang}")
    
    # Валюты
    currencies = country.get('currencies', {})
    if currencies:
        print(f"\n{Fore.CYAN}💰 Валюты:")
        for code, currency in currencies.items():
            name = currency.get('name', 'Не указано')
            symbol = currency.get('symbol', '')
            print(f"  {Fore.YELLOW}{code}: {Fore.WHITE}{name} {symbol}")
    
    # Домены
    tld = country.get('tld', [])
    if tld:
        print(f"\n{Fore.CYAN}🌐 Домены: {Fore.WHITE}{', '.join(tld)}")
    
    # Код страны
    cca2 = country.get('cca2', 'Не указано')
    cca3 = country.get('cca3', 'Не указано')
    print(f"\n{Fore.CYAN}🏷️  Коды:")
    print(f"  {Fore.GREEN}ISO 2: {Fore.WHITE}{cca2}")
    print(f"  {Fore.GREEN}ISO 3: {Fore.WHITE}{cca3}")
    
    # Флаг
    flag = country.get('flag', '')
    if flag:
        print(f"\n{Fore.CYAN}🏁 Флаг: {flag}")
    
    # Карта
    maps = country.get('maps', {})
    google_maps = maps.get('googleMaps', '')
    if google_maps:
        print(f"\n{Fore.CYAN}🗺️  Карта: {Fore.BLUE}{google_maps}")
    
    print(f"\n{Fore.GREEN}{'='*50}")


def main():
    """Главная функция"""
    print(f"{Back.GREEN}{Fore.WHITE} СПРАВОЧНИК СТРАН {Style.RESET_ALL}")
    
    while True:
        print(f"\n{Fore.YELLOW}Введите название страны (или 'exit' для выхода):")
        country_name = input(f"{Fore.WHITE}> ").strip()
        
        if country_name.lower() in ['exit', 'выход', 'quit']:
            print(f"{Fore.GREEN}До свидания!")
            break
        
        if not country_name:
            print(f"{Fore.RED}Пожалуйста, введите название страны!")
            continue
        
        print(f"\n{Fore.YELLOW}Поиск информации о стране: {country_name}...")
        
        country_data = get_country_info(country_name)
        format_country_info(country_data)


if __name__ == "__main__":
    main()
