import os
import time
import statistics
import requests

try:
    import speedtest
except Exception:
    speedtest = None


_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

def _emit_metric(metric_callback, data):
    if not metric_callback:
        return
    try:
        metric_callback(data)
    except Exception:
        return


def _run_cloudflare_http_test(callback=None, metric_callback=None):
    try:
        session = requests.Session()
        session.headers.update(_DEFAULT_HEADERS)

        if callback:
            callback("正在测试延迟...")
        ping_samples = []
        for _ in range(5):
            start = time.perf_counter()
            r = session.get("https://speed.cloudflare.com/__down?bytes=0", timeout=10)
            r.raise_for_status()
            ping_samples.append((time.perf_counter() - start) * 1000)
        ping_ms = sum(ping_samples) / len(ping_samples)
        jitter_ms = float(statistics.pstdev(ping_samples)) if len(ping_samples) > 1 else 0.0

        if callback:
            callback("正在测试下载速度...")
        download_bytes = 25 * 1024 * 1024
        start = time.perf_counter()
        downloaded = 0
        last_emit = start
        with session.get(
            f"https://speed.cloudflare.com/__down?bytes={download_bytes}",
            stream=True,
            timeout=20,
        ) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=256 * 1024):
                if not chunk:
                    continue
                downloaded += len(chunk)
                now = time.perf_counter()
                if now - last_emit >= 0.2:
                    elapsed = max(now - start, 1e-6)
                    mbps = (downloaded * 8) / (elapsed * 1_000_000)
                    _emit_metric(metric_callback, {"phase": "download", "mbps": float(mbps)})
                    last_emit = now
        download_s = max(time.perf_counter() - start, 1e-6)
        download_mbps = (downloaded * 8) / (download_s * 1_000_000)
        _emit_metric(metric_callback, {"phase": "download", "mbps": float(download_mbps)})

        if callback:
            callback("正在测试上传速度...")
        upload_bytes = 8 * 1024 * 1024
        payload = os.urandom(upload_bytes)

        def payload_iter():
            mv = memoryview(payload)
            sent = 0
            start_u = time.perf_counter()
            last_emit_u = start_u
            chunk_size = 256 * 1024
            while sent < upload_bytes:
                end = min(sent + chunk_size, upload_bytes)
                chunk = bytes(mv[sent:end])
                sent = end
                now_u = time.perf_counter()
                if now_u - last_emit_u >= 0.2:
                    elapsed_u = max(now_u - start_u, 1e-6)
                    mbps_u = (sent * 8) / (elapsed_u * 1_000_000)
                    _emit_metric(metric_callback, {"phase": "upload", "mbps": float(mbps_u)})
                    last_emit_u = now_u
                yield chunk
            total_elapsed_u = max(time.perf_counter() - start_u, 1e-6)
            final_mbps_u = (upload_bytes * 8) / (total_elapsed_u * 1_000_000)
            _emit_metric(metric_callback, {"phase": "upload", "mbps": float(final_mbps_u)})

        start = time.perf_counter()
        r = session.post("https://speed.cloudflare.com/__up", data=payload_iter(), timeout=25)
        r.raise_for_status()
        upload_s = max(time.perf_counter() - start, 1e-6)
        upload_mbps = (upload_bytes * 8) / (upload_s * 1_000_000)

        return {
            "status": "success",
            "download": float(download_mbps),
            "upload": float(upload_mbps),
            "ping": float(ping_ms),
            "jitter": float(jitter_ms),
            "source": "cloudflare",
            "server": {
                "name": "Cloudflare",
                "sponsor": "Cloudflare",
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "source": "cloudflare"}


def _run_speedtest_cli(callback=None, metric_callback=None):
    if speedtest is None:
        return {"status": "error", "message": "speedtest 模块不可用", "source": "speedtest-cli"}

    try:
        st = speedtest.Speedtest()

        if callback:
            callback("正在寻找最佳服务器...")
        best_server = st.get_best_server()

        if callback:
            callback("正在测试下载速度...")
        download_speed = st.download() / 1_000_000

        if callback:
            callback("正在测试上传速度...")
        upload_speed = st.upload() / 1_000_000

        res = st.results.dict()

        return {
            "status": "success",
            "download": float(download_speed),
            "upload": float(upload_speed),
            "ping": float(res.get("ping", 0.0)),
            "jitter": None,
            "source": "speedtest-cli",
            "server": {
                "name": best_server.get("name") if isinstance(best_server, dict) else None,
                "sponsor": best_server.get("sponsor") if isinstance(best_server, dict) else None,
                "country": best_server.get("country") if isinstance(best_server, dict) else None,
                "host": best_server.get("host") if isinstance(best_server, dict) else None,
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "source": "speedtest-cli"}

def run_speed_test(callback=None, provider="auto", metric_callback=None):
    """
    运行网速测试
    callback: 用于进度回调的函数 (接收字符串消息)
    返回: {
        "download": 0.0, # Mbps
        "upload": 0.0,   # Mbps
        "ping": 0.0,
        "status": "success"
    } 或 {"status": "error", "message": "..."}
    """
    if provider == "cloudflare":
        return _run_cloudflare_http_test(callback=callback, metric_callback=metric_callback)

    if provider == "speedtest":
        return _run_speedtest_cli(callback=callback, metric_callback=metric_callback)

    result = _run_speedtest_cli(callback=callback, metric_callback=metric_callback)
    if result.get("status") == "success":
        return result

    if callback:
        callback("Speedtest 服务不可用，切换到备用测速服务...")
    fallback = _run_cloudflare_http_test(callback=callback, metric_callback=metric_callback)
    if fallback.get("status") == "success":
        return fallback

    return {
        "status": "error",
        "message": f"speedtest-cli: {result.get('message', '未知错误')} | cloudflare: {fallback.get('message', '未知错误')}",
    }

if __name__ == "__main__":
    def my_cb(msg): print(msg)
    print(run_speed_test(my_cb))
