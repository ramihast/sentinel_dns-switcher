import json
import dns.resolver
from ping_tester import PingTester

class GameAnalyzer:
    def __init__(self, dns_list_path="dns_list.json", games_list_path="games_list.json"):
        with open(dns_list_path, "r", encoding="utf-8") as f:
            self.dns_list = json.load(f)
        with open(games_list_path, "r", encoding="utf-8") as f:
            self.games = json.load(f)
        self.ping_tester = PingTester(timeout=1)

    def analyze_game(self, game_name):
        if game_name not in self.games:
            print("❌ بازی یافت نشد.")
            return

        domains = self.games[game_name]
        results = []

        print(f"\n🎯 در حال تست بازی: {game_name}")
        for dns_item in self.dns_list:
            dns_ip = dns_item["ip"]
            total_ping = 0
            success_count = 0
            total_tests = 0

            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_ip]
            resolver.timeout = 1
            resolver.lifetime = 1

            for domain in domains:
                try:
                    answer = resolver.resolve(domain)
                    for a in answer:
                        ping = self.ping_tester.test_dns(a.address)
                        total_tests += 1
                        if ping:
                            total_ping += ping
                            success_count += 1
                except Exception:
                    total_tests += 1

            avg_ping = (total_ping / success_count) if success_count > 0 else None
            score = avg_ping if avg_ping else 9999
            results.append((dns_item["name"], avg_ping, success_count, total_tests, score))

        results.sort(key=lambda x: x[4])
        print("\n🏆 نتایج تست:")
        for name, avg, ok, total, score in results:
            if avg:
                print(f"✅ {name:<15} | میانگین پینگ: {avg:>6.1f} ms | موفقیت: {ok}/{total}")
            else:
                print(f"❌ {name:<15} | پاسخ‌گو نیست ({ok}/{total})")
