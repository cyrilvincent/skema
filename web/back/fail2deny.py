import re

class Entity:

    ip: str
    nb_error = 0
    nb_error404 = 0
    nb_big_error = 0

    def __init__(self, ip: str):
        self.ip = ip

    @property
    def banned(self):
        return self.nb_big_error > 1 or self.nb_error404 > 10 or self.nb_error > 20

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

    def parse(self, path: str):
        with open(path) as f:
            for row in f:
                self.parse_row(row)

    def parse_row(self, row: str):
        match = re.match(self.ip_pattern, row)
        if match is not None:
            ip = match.group(0)
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



if __name__ == '__main__':
    f = Fail2Deny()
    f.parse("../nginx/linux/logs/host.access.log")
    print(f.entities.values())



