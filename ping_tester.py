import ping3
import time

class PingTester:
    def __init__(self, timeout=1):
        ping3.EXCEPTIONS = True
        self.timeout = timeout

    def test_dns(self, ip):
        try:
            start = time.time()
            ping_time = ping3.ping(ip, timeout=self.timeout)
            if ping_time is None:
                return None
            return round(ping_time * 1000, 2)  # convert to ms
        except Exception:
            return None
