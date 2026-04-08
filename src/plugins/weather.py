"""Weather information tool."""

from typing import Dict
import os

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from src.core.tools.base import BaseTool, ToolParameter
from src.core.config import settings


class WeatherTool(BaseTool):
    """Gets current weather information for a location."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "location": ToolParameter(
                name="location",
                type="string",
                description="City name, zip code, or coordinates (e.g., 'London', '90210', '40.7,-74.0')",
                required=True,
            ),
            "units": ToolParameter(
                name="units",
                type="string",
                description="Temperature units",
                required=False,
                default="metric",
                enum=["metric", "imperial"],
            ),
        }

    async def execute(self, location: str, units: str = "metric") -> Dict:
        """
        Get weather information.

        Args:
            location: Location (city name, zip, or coordinates)
            units: metric (Celsius) or imperial (Fahrenheit)

        Returns:
            Weather information
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx not installed. Install with: pip install httpx")

        # Check for API key
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return {
                "error": "OpenWeatherMap API key not configured",
                "instructions": [
                    "Get a free API key from: https://openweathermap.org/api",
                    "Add to .env: OPENWEATHER_API_KEY=your_key_here",
                ],
                "location": location,
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Call OpenWeatherMap API
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": location,
                        "appid": api_key,
                        "units": units,
                    },
                )
                response.raise_for_status()
                data = response.json()

            # Parse response
            temp_unit = "°C" if units == "metric" else "°F"
            speed_unit = "m/s" if units == "metric" else "mph"

            result = {
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature": {
                    "current": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "min": data["main"]["temp_min"],
                    "max": data["main"]["temp_max"],
                    "unit": temp_unit,
                },
                "conditions": {
                    "main": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "icon": data["weather"][0]["icon"],
                },
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind": {
                    "speed": data["wind"]["speed"],
                    "direction": data["wind"].get("deg"),
                    "unit": speed_unit,
                },
                "clouds": data["clouds"]["all"],
                "visibility": data.get("visibility"),
                "summary": f"{data['weather'][0]['description'].title()} in {data['name']}, {data['main']['temp']}{temp_unit}",
            }

            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API key. Check your OPENWEATHER_API_KEY.")
            elif e.response.status_code == 404:
                raise ValueError(f"Location not found: {location}")
            else:
                raise ValueError(f"Weather API error: {e}")
        except Exception as e:
            raise ValueError(f"Failed to get weather: {e}")
