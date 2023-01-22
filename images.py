from requests import get
from json import load
from json import dump
import webbrowser


url = "http://127.0.0.1:5000/items"

results = get(url)
data = results.json()

images = {}
with open("images.json", "r") as f:
    images = load(f)

    c = 0
    for item in data:
        if c > 10: break

        if item['location'] not in images:
            c += 1
            webbrowser.open(f"https://www.google.com/search?q={'+'.join(item['location'].split(' '))}", new=0, autoraise=True)
            inp = input("url pls")
            images[item['location']] = inp
            

with open("images.json", "w") as f:
    dump(images, f)
