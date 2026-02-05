# bench/latency_test.py (excerpt)
import concurrent.futures
import statistics
import time

from src.gate.gate_controller import GateController


def run_one(idx):
    start = time.time()
    # call execute_pricing_action directly
    result = GateController().execute_pricing_action(
        "publish_price",
        {"sku_id": "SKU-{}".format(idx), "new_price": 1.0},
        context={},
    )
    return (time.time() - start) * 1000


def main():
    iters = 200
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        latencies = list(ex.map(run_one, range(iters)))
    latencies.sort()
    import math

    p50 = latencies[int(len(latencies) * 0.5)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    print(f"p50={p50:.2f}ms p95={p95:.2f}ms p99={p99:.2f}ms")


if __name__ == "__main__":
    main()
