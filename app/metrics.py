from collections import defaultdict
from threading import Lock


class MetricsCollector:
    def __init__(self):
        self.lock = Lock()
        self.http_requests = defaultdict(int)  # (path, status) -> count
        self.webhook_requests = defaultdict(int)  # result -> count
        self.latency_buckets = defaultdict(int)  # bucket -> count
        self.latency_count = 0
        self.latency_sum = 0
    
    def record_request(self, path: str, status: int, latency_ms: int):
        with self.lock:
            self.http_requests[(path, status)] += 1
            
            # Record latency
            self.latency_count += 1
            self.latency_sum += latency_ms
            
            # Bucket latency
            if latency_ms <= 100:
                self.latency_buckets[100] += 1
            if latency_ms <= 500:
                self.latency_buckets[500] += 1
            self.latency_buckets[float('inf')] += 1
    
    def record_webhook(self, result: str):
        with self.lock:
            self.webhook_requests[result] += 1
    
    def generate_prometheus_format(self) -> str:
        lines = []
        
        # HTTP requests total
        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        with self.lock:
            for (path, status), count in sorted(self.http_requests.items()):
                lines.append(f'http_requests_total{{path="{path}",status="{status}"}} {count}')
        
        # Webhook requests total
        lines.append("# HELP webhook_requests_total Total webhook processing outcomes")
        lines.append("# TYPE webhook_requests_total counter")
        with self.lock:
            for result, count in sorted(self.webhook_requests.items()):
                lines.append(f'webhook_requests_total{{result="{result}"}} {count}')
        
        # Request latency histogram
        lines.append("# HELP request_latency_ms_bucket Request latency in milliseconds")
        lines.append("# TYPE request_latency_ms_bucket histogram")
        with self.lock:
            for bucket in [100, 500, float('inf')]:
                count = self.latency_buckets.get(bucket, 0)
                le = "+Inf" if bucket == float('inf') else str(bucket)
                lines.append(f'request_latency_ms_bucket{{le="{le}"}} {count}')
            lines.append(f'request_latency_ms_count {self.latency_count}')
            lines.append(f'request_latency_ms_sum {self.latency_sum}')
        
        return "\n".join(lines) + "\n"