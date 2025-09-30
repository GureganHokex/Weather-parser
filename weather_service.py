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
        self.yandex_api_key = os.getenv("YANDEX_WEATHER_API_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.yandex_url = "https://api.weather.yandex.ru/v2/forecast"
        # Частые алиасы/сокращения городов (ключи в нижнем регистре)
        self.city_aliases: Dict[str, str] = {
            "спб": "Санкт-Петербург",
            "spb": "Санкт-Петербург",
            "питер": "Санкт-Петербург",
            "ленинград": "Санкт-Петербург",
            "мск": "Москва",
            "msk": "Москва",
            "москва": "Москва",
        }

    def get_weather_by_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        city_name = self._normalize_city_name(city_name)
        # Если есть ключ Яндекс Погоды, используем его как приоритетный провайдер
        if self.yandex_api_key:
            return self._get_yandex_by_city(city_name)
        if not self.api_key:
            data = self._get_weather_mock(city_name)
            data["source"] = "mock"
            return data

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
            formatted = self._format_weather_data(data)
            formatted["source"] = "live"
            return formatted
        except requests.RequestException:
            return None

    def get_weather_by_coords(
        self, latitude: float, longitude: float, fallback_city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if self.yandex_api_key:
            return self._get_yandex_by_coords(latitude, longitude, fallback_city)
        if not self.api_key:
            data = self._get_weather_mock(fallback_city or "Ваш город")
            data["source"] = "mock"
            return data

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
            formatted = self._format_weather_data(data)
            formatted["source"] = "live"
            return formatted
        except requests.RequestException:
            return None

    # --------------------
    # Yandex Weather
    # --------------------
    def _get_yandex_by_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        coords = self._geocode_city(city_name)
        if not coords:
            return None
        return self._get_yandex_by_coords(coords["lat"], coords["lon"], fallback_city=city_name)

    def _get_yandex_by_coords(
        self, latitude: float, longitude: float, fallback_city: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        headers = {"X-Yandex-Weather-Key": self.yandex_api_key}
        params = {"lat": latitude, "lon": longitude, "lang": "ru"}
        try:
            resp = requests.get(self.yandex_url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            formatted = self._format_yandex_data(data, fallback_city)
            formatted["source"] = "live_yandex"
            return formatted
        except requests.RequestException:
            return None

    def _geocode_city(self, city_name: str) -> Optional[Dict[str, float]]:
        city_name = self._normalize_city_name(city_name)
        # Простой геокодер через Nominatim (OSM). Соблюдаем требования — укажем User-Agent.
        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": city_name,
                    "format": "json",
                    "limit": 1,
                    "accept-language": "ru",
                },
                headers={"User-Agent": "weather-parser-app/1.0"},
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json()
            if not items:
                return None
            item = items[0]
            return {"lat": float(item["lat"]), "lon": float(item["lon"])}
        except requests.RequestException:
            return None

    def _format_yandex_data(self, data: Dict[str, Any], fallback_city: Optional[str]) -> Dict[str, Any]:
        fact = data.get("fact", {})
        geo = data.get("geo_object", {})
        locality = (geo.get("locality") or {}).get("name")
        country_name = (geo.get("country") or {}).get("name")

        temperature = fact.get("temp")
        feels_like = fact.get("feels_like")
        description = fact.get("condition", "").replace("-", " ").title()
        humidity = fact.get("humidity")
        # В API Яндекса давление приходит в мм рт. ст. (pressure_mm)
        pressure = fact.get("pressure_mm")
        wind_speed = fact.get("wind_speed")

        return {
            "city": locality or fallback_city or "Ваш город",
            "country": country_name,
            "temperature": round(temperature) if temperature is not None else None,
            "feels_like": round(feels_like) if feels_like is not None else None,
            "description": description,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _normalize_city_name(self, city_name: str) -> str:
        if not city_name:
            return city_name
        key = city_name.strip().lower()
        return self.city_aliases.get(key, city_name.strip())

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


