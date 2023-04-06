import urllib.request

url = "https://pyris.datajazz.io/api/coords?geojson=false&lat=45.0984&lon=5.5783"
with urllib.request.urlopen(url) as response:
    s = response.read()
    print(s)
