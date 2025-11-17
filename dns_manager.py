import json
import os

class DNSManager:
    def __init__(self, path="dns_list.json"):
        self.path = path
        self.dns_list = []
        self.load_dns()

    def load_dns(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.dns_list = json.load(f)
        else:
            self.dns_list = [
                {"name": "Google", "ip": "8.8.8.8", "protocol": "UDP"},
                {"name": "Cloudflare", "ip": "1.1.1.1", "protocol": "UDP"},
                {"name": "شکن", "ip": "178.x.x.x", "protocol": "UDP"},
                {"name": "رادار", "ip": "185.x.x.x", "protocol": "UDP"}
            ]
            self.save_dns()

    def save_dns(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.dns_list, f, indent=2, ensure_ascii=False)

    def list_dns(self):
        return self.dns_list
