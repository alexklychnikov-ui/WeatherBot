import requests
import json
import http_client


def test_get(url, headers=None, params=None):
    """Выполняет GET запрос к указанному URL"""
    response = http_client.get_simple(url, params=params, headers=headers)
    
    if response is None:
        print(f"Ошибка GET запроса")
        return None
        
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    try:
        json_data = response.json()
        print(f"Response JSON:\n{json.dumps(json_data, indent=2, ensure_ascii=False)}")
    except:
        print(f"Response Text:\n{response.text}")
        
    return response


def test_post(url, data=None, json_data=None, headers=None):
    """Выполняет POST запрос к указанному URL"""
    response = http_client.post(url, data=data, json_data=json_data, headers=headers)
    
    if response is None:
        print(f"Ошибка POST запроса")
        return None
        
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    try:
        json_response = response.json()
        print(f"Response JSON:\n{json.dumps(json_response, indent=2, ensure_ascii=False)}")
    except:
        print(f"Response Text:\n{response.text}")
        
    return response

def test_get_country_requests(country: str): 
    url = f"https://restcountries.com/v3.1/name/{country}"
    response = test_get(url)
    return response

def get_dog_breeds():
    """ Получить список доступных пород собак """
    url = "https://dog.ceo/api/breeds/list/all"
    response = http_client.get_simple(url)
    
    if response and response.status_code == 200:
        try:
            data = response.json()
            return list(data.get('message', {}).keys())
        except:
            pass
    return []

def test_get_dog_requests(breed=None): 
    """ Получить случайное фото собаки определенной породы или любой """
    if breed:
        # Проверяем, существует ли порода
        breeds = get_dog_breeds()
        if breed not in breeds:
            print(f"Порода '{breed}' не найдена!")
            print("Доступные породы:", ", ".join(breeds[:10]) + "..." if len(breeds) > 10 else ", ".join(breeds))
            return None
        url = f"https://dog.ceo/api/breed/{breed}/images/random"
    else:
        url = "https://dog.ceo/api/breeds/image/random"
    
    response = http_client.get_simple(url)
    
    if response is None:
        print(f"Ошибка GET запроса")
        return None
        
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get('status') == 'success':
                image_url = data.get('message')
                print(f"Ссылка на изображение собаки: {image_url}")
            else:
                print(f"Ошибка API: {data.get('message', 'Неизвестная ошибка')}")
        except:
            print(f"Ошибка парсинга JSON")
    else:
        print(f"Ошибка запроса: {response.status_code}")
        
    return response

def test_get_bird_requests(species=None): 
    """ Получить информацию о птице через eBird API """
    if species:
        url = f"https://api.ebird.org/v2/data/obs/geo/recent?lat=40.7128&lng=-74.0060&speciesCode={species}"
    else:
        # Используем JSONPlaceholder как заглушку для демонстрации
        url = "https://jsonplaceholder.typicode.com/posts/1"
    response = test_get(url)
    return response

def main():
    """Главная функция для выбора типа запроса"""
    while True:
        print("\n" + "="*50)
        print("Тестовый модуль API запросов")
        print("0. Выход")
        print("1. GET запрос")
        print("2. POST запрос")
        print("3. GET запрос страны")
        print("4. GET запрос собаки")
        print("5. GET запрос птицы")
        print("="*50)
        
        choice = input("Выберите тип запроса (0-5): ")
        
        if choice == "0":
            print("Выход из программы")
            break
        elif choice == "1":
            url = input("Введите URL: ")
            
            # Опциональные заголовки
            headers_input = input("Заголовки (JSON формат, Enter для пропуска): ")
            headers = None
            if headers_input.strip():
                try:
                    headers = json.loads(headers_input)
                except:
                    print("Неверный формат заголовков, игнорируем")
            
            # Опциональные параметры
            params_input = input("Параметры (JSON формат, Enter для пропуска): ")
            params = None
            if params_input.strip():
                try:
                    params = json.loads(params_input)
                except:
                    print("Неверный формат параметров, игнорируем")
            
            test_get(url, headers, params)
        
        elif choice == "2":
            url = input("Введите URL: ")
            
            # Опциональные заголовки
            headers_input = input("Заголовки (JSON формат, Enter для пропуска): ")
            headers = None
            if headers_input.strip():
                try:
                    headers = json.loads(headers_input)
                except:
                    print("Неверный формат заголовков, игнорируем")
            
            # Выбор типа данных
            data_type = input("Тип данных (1-JSON, 2-form-data, Enter для пропуска): ")
            
            if data_type == "1":
                json_input = input("JSON данные: ")
                try:
                    json_data = json.loads(json_input)
                    test_post(url, json_data=json_data, headers=headers)
                except:
                    print("Неверный JSON формат")
            elif data_type == "2":
                data_input = input("Form данные (JSON формат): ")
                try:
                    data = json.loads(data_input)
                    test_post(url, data=data, headers=headers)
                except:
                    print("Неверный формат данных")
            else:
                test_post(url, headers=headers)
        elif choice == "3":
            country = input("Введите название страны: ")
            test_get_country_requests(country)
        elif choice == "4":
            print("Популярные породы: beagle, bulldog, husky, labrador, poodle, retriever")
            breed_input = input("Введите породу собаки (Enter для случайной): ").strip().lower()
            breed = breed_input if breed_input else None
            test_get_dog_requests(breed)
        elif choice == "5":
            species_input = input("Введите код вида птицы (Enter для демо): ").strip()
            species = species_input if species_input else None
            test_get_bird_requests(species)
        else:
            print("Неверный выбор")


if __name__ == "__main__":
    main()
