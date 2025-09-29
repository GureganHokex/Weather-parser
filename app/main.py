from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

from weather_service import WeatherService, get_location_by_ip


app = FastAPI(title="Weather Parser Web")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, q: Optional[str] = None) -> HTMLResponse:
    service = WeatherService()
    weather = None

    if q:
        weather = service.get_weather_by_city(q)
    else:
        loc = get_location_by_ip()
        if loc and (loc.get("lat") is not None and loc.get("lon") is not None):
            weather = service.get_weather_by_coords(loc["lat"], loc["lon"], fallback_city=loc.get("city"))

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "weather": weather, "query": q or ""},
    )


