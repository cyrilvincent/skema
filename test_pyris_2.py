import urllib.request
import ssl

url = "https://pyris.datajazz.io/api/coords?geojson=false&lat=45.0984&lon=5.5783"
ssl._create_default_https_context = ssl._create_unverified_context
with urllib.request.urlopen(url) as response:
    s = response.read()
    print(s)
