import datetime
from dataclasses import dataclass
import re
import os


@dataclass
class AccessLog:

    datetime = datetime.datetime.now()
    ip: str = ""
    http_code: int = 0
    from_url: str = ""
    uri: str = ""
    verb: str = ""
    size: int = 0
    protocol: str = ""
    agent: str = ""

    def __repr__(self):
        return f"{self.ip} {self.datetime} {self.verb} {self.uri} {self.http_code} {self.from_url} {self.agent}"


class LogAggregate:

    date = datetime.date.today()
    hit = 0
    nb500 = 0
    nb400 = 0
    nb403 = 0
    nb404 = 0
    main = 1
    ip = 1
    ip_200 = 1
    api = 2
    guest = 1
    login = 0
    apl = 1
    sae = 0

    def __repr__(self):
        return (f"{self.date.year}{self.date.month:02d}{self.date.day:02d},{self.hit},{self.nb400},{self.nb403},"
                f"{self.nb404},{self.nb500},{self.ip},{self.ip_200},{self.main},{self.api},{self.guest},{self.login},"
                f"{self.apl},{self.sae}")


class HostAccessLogParser:

    def __init__(self):
        self.logs: list[AccessLog] = []
        self.agg = LogAggregate()
        self.ips = set()
        self.ips200 = set()

    def parse(self, path: str):
        print(f"Parsing {path}")
        with open(path) as f:
            for row in f:
                log = self.parse_row(row)
                print(log)
                self.logs.append(log)

    def aggregate(self):
        self.agg.date = self.logs[0].datetime.date()
        for log in self.logs:
            self.agg.hit += 1
            if log.http_code >= 500:
                self.agg.nb500 += 1
            if log.http_code >= 400:
                self.agg.nb400 += 1
                if log.http_code == 403:
                    self.agg.nb403 += 1
                elif log.http_code == 404:
                    self.agg.nb404 += 1
            if log.ip not in self.ips:
                self.agg.ip += 1
                self.ips.add(log.ip)
                if log.http_code == 200:
                    self.agg.ip_200 += 1
                    self.ips200.add(log.ip)
            if log.http_code == 200:
                if log.uri.startswith("/main-") and log.uri.endswith(".js") and log.verb == "GET":
                    self.agg.main += 1
                if log.uri.startswith("/api1"):
                    self.agg.api += 1
                    if log.uri == "/api1/auth/guest":
                        self.agg.guest += 1
                    elif log.uri == "/api1/auth/login":
                        self.agg.login += 1
                    elif log.uri.startswith("api1/apl"):
                        self.agg.apl += 1
                    elif log.uri.startswith("api1/sae"):
                        self.agg.sae += 1

    def parse_row(self, row: str) -> AccessLog:
        log = AccessLog()
        log.ip = self.parse_ip(row)
        log.datetime = self.parse_datetime(row)
        log.verb, log.uri, log.protocol = self.parse_http(row)
        log.http_code, log.size, log.from_url, log.agent = self.parse_http_end(row)
        return log

    def parse_ip(self, row: str) -> str:
        index = row.index("-")
        ip = row[:index].strip()
        return ip

    def parse_datetime(self, row: str):
        index = row.index("[")
        s = row[index + 1:]
        index = s.index("]")
        s = s[:index]
        dt = datetime.datetime.strptime(s, "%d/%b/%Y:%H:%M:%S %z")
        return dt

    def parse_http(self, row: str) -> tuple[str, str, str]:
        index = row.index('"')
        s = row[index + 1:]
        index = s.index('"')
        s = s[:index]
        values = s.split(" ")
        if len(values) > 2:
            return values[0], values[1], values[2]
        else:
            return values[0], "", ""

    def parse_http_end(self, row: str) -> tuple[int, int, str, str]:
        index = row.index('"')
        s = row[index + 1:]
        index = s.index('"')
        s = s[index + 2:]
        # index = s.index('"')
        # s = s[:index]
        values = s.split(" ")
        code = int(values[0])
        size = int(values[1])
        url = values[2].replace('"', "")
        agent = values[3].replace('"', "")
        return code, size, url, agent

    def save_csv(self, path: str):
        path = path.replace(".csv", f"_{self.logs[0].datetime.year}{self.logs[0].datetime.month:02d}.csv")
        if not os.path.exists(path):
            print(f"Creating {path}")
            with open(path, "w") as f:
                f.write("date,hit,400,403,404,500,ip,ip_200,main,api,guest,login,apl,sae\n")
        with open(path, "a") as f:
            print(f"Save to {path}")
            f.write(str(self.agg) + "\n")

    def process(self):
        self.parse("logs/host.access.log.1")
        self.aggregate()
        print(self.agg)
        self.save_csv("logs/log_report.csv")


if __name__ == '__main__':
    p = HostAccessLogParser()
    p.process()
