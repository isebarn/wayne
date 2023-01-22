from flask import Flask
from flask_restx import Resource, Api
from requests import get
from bs4 import BeautifulSoup
from functools import lru_cache
from json import load
from json import dump
from flask_caching import Cache
from datetime import datetime

weather_key = "131ebf70d4e74fc2aab115235232201"

weather_url = "http://api.weatherapi.com/v1/forecast.json?key={}&q={}&days=10&aqi=no&alerts=no"

app = Flask(__name__)
api = Api(app)

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

@api.route("/items")
class ItemsController(Resource):
    @cache.cached(timeout=3600*24)
    def get(self):
        response = get("https://www.usapowerlifting.com/calendar/")
        soup = BeautifulSoup(response.text, "lxml")

        states = soup.find_all("div", {"class": "event-state"})
        titles = soup.find_all("div", {"class": "event-name"})
        dates = soup.find_all("div", {"class": "event-date"})
        info = soup.find_all("div", {"class": "event-info"})
        event_links = soup.find_all("div", {"class": "event-button"})

        event_types = [
            x.get_text(strip=True, separator="\n").splitlines()[0] for x in info
        ]
        sanctions = [
            x.get_text(strip=True, separator="\n").splitlines()[1] for x in info
        ]
        locations = [
            x.get_text(strip=True, separator="\n").splitlines()[2] for x in info
        ]
        directors = [
            x.get_text(strip=True, separator="\n").splitlines()[4] for x in info
        ]

        images = {}
        with open("images.json", "r") as f:
            images = load(f)        

        data = [
            {
                "state": state.text,
                "title": title.text,
                "date": [datetime.strptime(x, '%b %d, %Y').isoformat() for x in date.text.split(" - ")],
                "event_type": event_type.split(": ")[-1],
                "sanction": sanction.split(": ")[-1],
                "location": location.split(": ")[-1],
                "image": images.get(location.split(": ")[-1]),
                "director": director,
                "registration": event_link.find_all("a")[-1]['href'] if event_link.find_all("a") else None
            }
            for state, title, date, event_type, sanction, location, director, event_link in zip(
                states,
                titles,
                dates,
                event_types,
                sanctions,
                locations,
                directors,
                event_links
            )
        ]

        for item in data:
            if -1 < (datetime.fromisoformat(item['date'][0]) - datetime.now()).days < 10:
                try:
                    place = "+".join(item['location'].replace(",", "").split(" "))
                    time = item['date'][0].split("T")[0]
                    weather = get(weather_url.format(weather_key, place))
                    day_forecast = next(x for x in weather.json()['forecast']['forecastday'] if time == x['date'])
                    item.update({"temp": day_forecast['day']['maxtemp_f'], "icon": day_forecast['day']['condition']['icon']})
                
                except Exception as e:
                    pass

        upcoming = [x for x in data if -1 < (datetime.fromisoformat(x['date'][-1]) - datetime.now()).days < 10]
        rest = [x for x in data if (datetime.fromisoformat(x['date'][-1]) - datetime.now()).days >= 10]

        return {
            "upcoming": upcoming,
            "rest": rest
        }


if __name__ == "__main__":
    app.run(debug=True)
