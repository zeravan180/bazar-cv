import json, re, sys, time, urllib.request

URL = "https://iraqsm.com/"
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ar,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def plain(html):
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)

# per-dollar market rate in IQD, e.g. 1,694.5 or 1694.5 (Baghdad / Kifah)
NUM = re.compile(r"(?<![\d.,])(1[,]?[4-9]\d{2}(?:\.\d{1,2})?)(?![\d,])")

def pick(text):
    cands = []
    for m in re.finditer(r"بغداد|الكفاح", text):
        seg = text[m.end(): m.end() + 200]
        n = NUM.search(seg)
        if n:
            cands.append(n.group(1))
    if not cands:
        n = NUM.search(text)
        if n:
            cands.append(n.group(1))
    for c in cands:
        v = float(c.replace(",", ""))
        if 1400 <= v <= 2000:
            return v
    return None

def main():
    try:
        html = get(URL)
    except Exception as e:
        print("fetch failed:", e)
        sys.exit(1)
    per_usd = pick(plain(html))
    if not per_usd:
        print("could not find rate; page length", len(html))
        sys.exit(1)
    sell = int(round(per_usd * 100 / 50.0) * 50)
    try:
        old = json.load(open("rates.json"))["baghdad"]["s"]
        if abs(sell - old) / old > 0.08:
            print("change too large, skip", old, sell)
            sys.exit(1)
    except FileNotFoundError:
        pass
    except Exception:
        pass
    out = {"baghdad": {"b": sell - 50, "s": sell}, "ts": int(time.time() * 1000), "src": "iraqsm.com"}
    json.dump(out, open("rates.json", "w"), ensure_ascii=False)
    print("ok", out)

main()
