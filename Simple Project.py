# Парсер погоды - Weather Parser
# 06/09 - 2-3 недели!

import requests
import json
from datetime import datetime
import time
import os

class WeatherParser:
    def __init__(self, api_key=None):
        """
        Инициализация парсера погоды
        api_key - ключ для OpenWeatherMap API (опционально)
        """
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        
    def get_weather_by_city(self, city_name):
        """
        Получить погоду по названию города
        """
        if not self.api_key:
            return self._get_weather_mock(city_name)
            
        params = {
            'q': city_name,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'ru'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return self._format_weather_data(data)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении данных: {e}")
            return None

    def get_weather_by_coords(self, latitude, longitude, fallback_city=None):
        """
        Получить погоду по координатам (широта и долгота)
        """
        if not self.api_key:
            # Если нет ключа, вернем мок-данные. Если известен город — используем его.
            return self._get_weather_mock(fallback_city or "Ваш город")

        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': self.api_key,
            'units': 'metric',
            'lang': 'ru'
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return self._format_weather_data(data)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении данных по координатам: {e}")
            return None
    
    def _get_weather_mock(self, city_name):
        """
        Мок-данные для демонстрации (если нет API ключа)
        """
        mock_data = {
            'city': city_name,
            'temperature': 22,
            'description': 'Ясно',
            'humidity': 65,
            'pressure': 1013,
            'wind_speed': 3.2,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return mock_data
    
    def _format_weather_data(self, data):
        """
        Форматирование данных о погоде
        """
        formatted = {
            'city': data['name'],
            'country': data['sys']['country'],
            'temperature': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'description': data['weather'][0]['description'].title(),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return formatted
    
    def display_weather(self, weather_data):
        """
        Красивый вывод информации о погоде
        """
        if not weather_data:
            print("❌ Не удалось получить данные о погоде")
            return
            
        print("\n" + "="*50)
        title = weather_data['city'].upper()
        if 'country' in weather_data:
            title = f"{title}, {weather_data['country']}"
        print(f"🌤️  ПОГОДА В {title}")
        print("="*50)
        print(f"🌡️  Температура: {weather_data['temperature']}°C")
        if 'feels_like' in weather_data:
            print(f"🤔 Ощущается как: {weather_data['feels_like']}°C")
        print(f"☁️  Описание: {weather_data['description']}")
        print(f"💧 Влажность: {weather_data['humidity']}%")
        print(f"📊 Давление: {weather_data['pressure']} гПа")
        print(f"💨 Ветер: {weather_data['wind_speed']} м/с")
        print(f"🕐 Время: {weather_data['timestamp']}")
        print("="*50)


def get_location_by_ip():
    """
    Определить местоположение по IP через публичный сервис ip-api.com
    Возвращает словарь { city, lat, lon } или None
    """
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') == 'success':
            return {
                'city': data.get('city') or 'Ваш город',
                'lat': data.get('lat'),
                'lon': data.get('lon')
            }
        else:
            print("❌ Не удалось определить местоположение по IP")
            return None
    except requests.exceptions.RequestException:
        print("❌ Ошибка сети при определении местоположения")
        return None

def main():
    """
    Основная функция для демонстрации работы парсера
    """
    print("🌤️  Добро пожаловать в парсер погоды!")
    print("Для работы с реальными данными получите API ключ на openweathermap.org")
    print()
    
    # Пытаемся взять ключ из переменной окружения, затем спросим у пользователя
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        use_key = input("Есть API ключ OpenWeather? (y/n): ").strip().lower()
        if use_key == 'y':
            api_key = input("Введите API ключ: ").strip() or None

    # Создаем парсер (без API ключа - будет использовать мок-данные)
    parser = WeatherParser(api_key=api_key)
    
    while True:
        print("\nВыберите действие:")
        print("1. Узнать погоду в городе")
        print("2. Погода по моему местоположению (IP)")
        print("3. Выход")
        
        choice = input("\nВведите номер (1-3): ").strip()
        
        if choice == '1':
            city = input("Введите название города: ").strip()
            if city:
                print(f"\n🔍 Ищем погоду в городе {city}...")
                weather = parser.get_weather_by_city(city)
                parser.display_weather(weather)
            else:
                print("❌ Пожалуйста, введите название города")
                
        elif choice == '2':
            print("\n📍 Определяем ваше местоположение по IP...")
            loc = get_location_by_ip()
            if loc and loc.get('lat') is not None and loc.get('lon') is not None:
                city = loc.get('city') or 'Ваш город'
                print(f"Найдено: {city} (lat: {loc['lat']}, lon: {loc['lon']})")
                print("\n🔍 Получаем погоду по координатам...")
                weather = parser.get_weather_by_coords(loc['lat'], loc['lon'], fallback_city=city)
                parser.display_weather(weather)
            else:
                print("❌ Не удалось определить местоположение. Попробуйте вариант с городом.")

        elif choice == '3':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()