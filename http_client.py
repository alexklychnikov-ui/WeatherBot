import requests
from typing import Optional, Dict, Any, Union


def get(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Optional[requests.Response]:
    """
    Выполняет GET запрос к указанному URL
    
    Args:
        url: URL для запроса
        params: Параметры запроса
        headers: Заголовки запроса
        timeout: Таймаут в секундах
    
    Returns:
        Response объект или None в случае ошибки
    """
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()  # Базовая проверка статуса
        return response
    except requests.exceptions.RequestException:
        return None


def post(url: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, 
         headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Optional[requests.Response]:
    """
    Выполняет POST запрос к указанному URL
    
    Args:
        url: URL для запроса
        data: Данные формы
        json_data: JSON данные
        headers: Заголовки запроса
        timeout: Таймаут в секундах
    
    Returns:
        Response объект или None в случае ошибки
    """
    try:
        response = requests.post(url, data=data, json=json_data, headers=headers, timeout=timeout)
        response.raise_for_status()  # Базовая проверка статуса
        return response
    except requests.exceptions.RequestException:
        return None


def get_simple(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, 
               timeout: int = 10) -> Optional[requests.Response]:
    """
    Простой GET запрос без автоматической проверки статуса (для совместимости)
    
    Args:
        url: URL для запроса
        params: Параметры запроса
        headers: Заголовки запроса
        timeout: Таймаут в секундах
    
    Returns:
        Response объект или None в случае ошибки
    """
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        return response
    except requests.exceptions.RequestException:
        return None
