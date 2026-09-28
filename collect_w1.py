import os, time, csv, requests
from datetime import datetime, timedelta, timezone

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
OUT_DIR = "data/w1_7"
BASE = "https://fapi.binance.com"

def fetch_force(symbol, start_ms, end_ms, limit=1000):
    url = f"{BASE}/fapi/v1/allForceOrders"
    params = {"symbol": symbol, "startTime": start_ms, "endTime": end_ms, "limit": limit}
    r = requests.get(url, params=params, timeout=15)
    if r.status_code == 451:
        url2 = f"{BASE}/fapi/v1/forceOrders"
        r = requests.get(url2, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def ensure_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

def load_last_ms(csv_path):
    if not os.path.exists(csv_path):
        return None
    try:
        with open(csv_path, "r") as f:
            rows = list(csv.reader(f))
            if len(rows) <= 1:
                return None
            last = rows[-1]
            for v in reversed(last):
                if v.isdigit() and len(v) >= 12:
                    return int(v)
    except:
        pass
    return None

def append_csv(path, rows):
    exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["symbol","side","price","qty","time","orig_time"])
        for r in rows:
            w.writerow([r.get("symbol"), r.get("side") or r.get("Side"), r.get("price") or r.get("Price"), r.get("origQty") or r.get("qty"), r.get("time"), r.get("time")])

if __name__ == "__main__":
    ensure_dir()
    try:
        ip = requests.get("https://ifconfig.me", timeout=5).text
        print(f"Runner IP: {ip}")
        test = requests.get(f"{BASE}/fapi/v1/forceOrders", params={"symbol":"BTCUSDT","limit":1}, timeout=10)
        print(f"Test forceOrders status: {test.status_code}")
    except Exception as e:
        print(f"IP/test failed: {e}")

    now_ms = int(datetime.now(timezone.utc).timestamp()*1000)
    seven_days_ago_ms = now_ms - 7*24*3600*1000

    for symbol in SYMBOLS:
        csv_path = os.path.join(OUT_DIR, f"liq_{symbol}.csv")
        last_ms = load_last_ms(csv_path)
        start = last_ms + 1 if last_ms else seven_days_ago_ms
        print(f"[{symbol}] collecting from {start} to {now_ms}")
        cur = start
        while cur < now_ms:
            end = min(cur + 3600*1000 - 1, now_ms)
            try:
                data = fetch_force(symbol, cur, end)
                if data:
                    append_csv(csv_path, data)
                    print(f"  {cur} -> {len(data)} rows")
            except Exception as e:
                print(f"  fetch error {cur}: {e}")
                time.sleep(2)
            cur = end + 1
            time.sleep(0.3)
