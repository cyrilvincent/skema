import datetime
import re
import ipaddress
import shutil
import time

import requests


class Entity:

    ip: str
    nb_error = 0
    nb_error404 = 0
    nb_big_error = 0
    country = ""
    city = ""

    def __init__(self, ip: str):
        self.ip = ip

    @property
    def banned(self):
        return (self.nb_big_error > 0 or
                (self.nb_error404 + self.nb_big_error) > 9 or
                (self.nb_error + self.nb_error404 + self.nb_big_error) > 19)

    def __repr__(self):
        return f"{self.ip}{" BANNED" if self.banned else ""} {self.nb_big_error} {self.nb_error404} {self.nb_error}"


class Fail2Deny:

    def __init__(self):
        self.errors = ["/api/", "secrets"]
        self.errors404 = ["404"]
        self.big_errors = [".ssh", ".git", ".config", ".php", ".yaml", "yml"]
        self.row = 0
        self.entities: dict[str, Entity] = {}
        self.ip_pattern = r'^(?:\d{1,3}\.){3}\d{1,3}'
        self.whitelist = ["209.198.137.252",
                          "72.14.201.124"]
        self.geo_banneds: list[str] = []

    def parse(self, path: str):
        print(f"Parse {path}")
        with open(path) as f:
            for row in f:
                self.parse_row(row)

    def parse_row(self, row: str):
        match = re.search(self.ip_pattern, row)
        if match is not None:
            self.row += 1
            ip = match.group(0)
            if self.notin_whitelist(ip) and ip not in self.geo_banneds:
                error = self.test_errors(row)
                if error > 0:
                    if ip not in self.entities:
                        e = Entity(ip)
                        self.entities[ip] = e
                    e = self.entities[ip]
                    if error == 3:
                        e.nb_big_error += 1
                    elif error == 2:
                        e.nb_error404 += 1
                    else:
                        e.nb_error += 1

    def notin_whitelist(self, ip: str) -> bool:
        if ip in self.whitelist:
            return False
        if ip.startswith("127.0") or ip.startswith("10.") or ip.startswith("172.") or ip.startswith("192.168"):
            return False
        return True

    def test_errors(self, row) -> int:
        for e in self.big_errors:
            if e in row:
                return 3
        for e in self.errors404:
            if e in row:
                return 2
        for e in self.errors:
            if e in row:
                return 1
        return 0

    @property
    def banneds(self) -> list[Entity]:
        res = [e for e in self.entities.values() if e.banned]
        return sorted(res, key=lambda e: ipaddress.ip_address(e.ip))

    def geo_ip(self, ip: str):
        r = requests.get(f"https://api.ipinfo.io/lite/{ip}?token=48fcec1efc1798")
        return r.json()

    def check_countries(self):
        for b in f.banneds:
            try:
                geo = f.geo_ip(b.ip)
                b.country = geo["country_code"]
                b.city = geo["as_domain"]
            except:
                pass
            print(b.country, b.city)

    def append_geo(self, path):
        temp = path + ".tmp"
        shutil.copy(path, temp)
        print(f"Write {temp}")
        with open(temp, "w") as g:
            with open(path) as f:
                for row in f:
                    if row != "}\n":
                        g.write(row)
                    else:
                        for b in self.banneds:
                            g.write(f"\t{b.ip}\t1;\t# {b.country} {b.city} {datetime.date.today()}\n")
                        g.write("}\n")

    def parse_geo(self, path):
        pattern = self.ip_pattern[1:]
        with open(path) as f:
            for row in f:
                match = re.search(pattern, row)
                if match is not None:
                    ip = match.group(0)
                    self.geo_banneds.append(ip)



if __name__ == '__main__':
    f = Fail2Deny()
    f.parse_geo("../unicorn/geo_original.txt")
    print(f.geo_banneds)
    f.parse("../nginx/linux/logs/host.access.log")
    print(f.banneds)
    f.check_countries()
    f.append_geo("../unicorn/geo_original.txt")





