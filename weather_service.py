import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv


class WeatherService:
    """
    Сервис получения и форматирования погоды.
    Выносит логику из консольного приложения для переиспользования в вебе.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        # Подхватим переменные окружения из .env при инициализации сервиса
        # (безошибочно, если файла нет)
        load_dotenv()
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather_by_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return self._get_weather_mock(city_name)

        params = {
            "q": city_name,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru",
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._format_weather_data(data)
        except requests.RequestException:
            return None

    def get_weather_by_coords(
        self, latitude: float, longitude: float, fallback_city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return self._get_weather_mock(fallback_city or "Ваш город")

        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru",
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._format_weather_data(data)
        except requests.RequestException:
            return None

    def _format_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "city": data.get("name"),
            "country": data.get("sys", {}).get("country"),
            "temperature": round(data.get("main", {}).get("temp")),
            "feels_like": round(data.get("main", {}).get("feels_like")),
            "description": (data.get("weather", [{}])[0].get("description", "").title()),
            "humidity": data.get("main", {}).get("humidity"),
            "pressure": data.get("main", {}).get("pressure"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _get_weather_mock(self, city_name: str) -> Dict[str, Any]:
        return {
            "city": city_name,
            "temperature": 22,
            "description": "Ясно",
            "humidity": 65,
            "pressure": 1013,
            "wind_speed": 3.2,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


def get_location_by_ip() -> Optional[Dict[str, Any]]:
    try:
        resp = requests.get("http://ip-api.com/json/", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "success":
            return {
                "city": data.get("city") or "Ваш город",
                "lat": data.get("lat"),
                "lon": data.get("lon"),
            }
        return None
    except requests.RequestException:
        return None


