import time
import json
import logging
from pathlib import Path
from collections import defaultdict

class MetricsCollector:
    def __init__(self, workspace: Path, reportEvery:int):
        self.reset()
        self.workspace = workspace
        self.reportEvery = reportEvery

    def reset(self):
        self.total = 0
        self.success = 0
        self.failures = 0
        self.latencies = []
        self.exceptions = defaultdict(int)
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def end(self, success: bool, exception: str = None):
        self.total += 1

        if success:
            self.success += 1
        else:
            self.failures += 1
            if exception:
                self.exceptions[exception] += 1

        if self.start_time:
            self.latencies.append(time.time() - self.start_time)

        self.start_time = None

    def shouldReport(self) -> bool:
        return self.total > 0 and self.total % self.reportEvery == 0
    
    def generateReport(self):
        successRate = (self.success / self.total) * 100 if self.total else 0
        avgLatency = sum(self.latencies) / len(self.latencies) if self.latencies else 0

        report = {
            "totalExecutions": self.total,
            "successRate": round(successRate, 2),
            "failures": self.failures,
            "avgLatencySec": round(avgLatency, 3),
            "exceptions": dict(self.exceptions),
        }

        path = self.workspace / f"metrics_report_{self.total}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logging.info(f"📊 Reporte generado: {path}")
        return report