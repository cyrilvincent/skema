import urllib3

url = "https://pyris.datajazz.io/api/coords?geojson=false&lat=45.0984&lon=5.5783"
http = urllib3.PoolManager()
res = http.request("GET", url, timeout=10)
print(res.data)
