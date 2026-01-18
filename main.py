import os
import sys
import ctypes
import signal
import urllib.parse
import requests
import urllib3
import msvcrt
import logging
from flask import Flask, request, Response
from cryptography import x509

from certmgr import certmgr
from hostmgr import hostmgr
from obs import obs_is_online, obs_set_stream_and_start

logging.getLogger("werkzeug").disabled = True
import flask.cli
flask.cli.show_server_banner = lambda *args, **kwargs: None
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OBS_HOST = "127.0.0.1"  #自己填
OBS_PORT = 4455
OBS_PASSWORD = ""

TARGET_DOMAIN = "webcast5-mate-lf.amemv.com"
BASE_DIR = os.path.expanduser("~/.douyin_stream")
CA_CERT = os.path.join(BASE_DIR, "ca.pem")
CA_KEY = os.path.join(BASE_DIR, "ca.key")
SERVER_CERT = os.path.join(BASE_DIR, "server.pem")
SERVER_KEY = os.path.join(BASE_DIR, "server.key")

app = Flask(__name__)
cm = certmgr()
hm = hostmgr()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def relaunch_as_admin():
    params = " ".join([f'"{i}"' for i in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    sys.exit(0)

if not is_admin():
    relaunch_as_admin()

def ensure_cert():
    os.makedirs(BASE_DIR, exist_ok=True)

    if cm.is_certificate_expired(CA_CERT) or not os.path.exists(CA_KEY):
        ca_key = cm.generate_private_key(2048)
        ca_cert = cm.generate_ca(ca_key)
        cm.export_key(CA_KEY, ca_key)
        cm.export_cert(CA_CERT, ca_cert)
        cm.import_to_root(CA_CERT)
    else:
        with open(CA_KEY, "rb") as f:
            ca_key = cm.load_private_key(f.read())
        with open(CA_CERT, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())

    if cm.is_certificate_expired(SERVER_CERT) or not os.path.exists(SERVER_KEY):
        server_key = cm.generate_private_key(2048)
        server_cert = cm.generate_cert([TARGET_DOMAIN], server_key, ca_cert, ca_key)
        cm.export_key(SERVER_KEY, server_key)
        cm.export_cert(SERVER_CERT, server_cert)

def suspend_mediasdk():
    import psutil
    import win32api
    import win32con

    for p in psutil.process_iter(["pid", "name"]):
        if p.info["name"] == "MediaSDK_Server.exe":
            proc = psutil.Process(p.info["pid"])
            threads = proc.threads()
            if not threads:
                return

            target_thread = max(threads, key=lambda t: t.user_time + t.system_time)

            h_thread = win32api.OpenThread(win32con.THREAD_SUSPEND_RESUME, False, target_thread.id)
            win32api.SuspendThread(h_thread)
            win32api.CloseHandle(h_thread)
            print("已解决推流冲突")
            return

def stream_generator(resp):
    try:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                yield chunk
    finally:
        resp.close()

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy(path):
    url = f"https://{hm.real_ip}/{path}"
    headers = dict(request.headers)
    headers["Host"] = TARGET_DOMAIN

    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        stream=True,
        allow_redirects=False,
        verify=False,
    )

    if "webcast/room/create" in path:
        try:
            data = resp.json()
            rtmp = data["data"]["stream_url"]["rtmp_push_url"]
            u = urllib.parse.urlparse(rtmp)
            base, stream = u.path.rsplit("/", 1)
            server = f"{u.scheme}://{u.netloc}{base}"
            key = stream
            if u.query:
                key += "?" + u.query

            print("成功获取推流信息")
            print("推流地址:", server)
            print("推流码:", key)

            if obs_is_online(OBS_HOST, OBS_PORT, OBS_PASSWORD):
                print("obs在线且配置正确 正在尝试推送直播...")
                if obs_set_stream_and_start(OBS_HOST, OBS_PORT, OBS_PASSWORD, server, key):
                    print("推流成功")
                else:
                    print("推流失败")
            else:
                print("obs未开启或者未设置ws服务器")

            suspend_mediasdk()
            cleanup()

        except Exception as e:
            print("推流捕获异常:", e)

    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]

    return Response(stream_generator(resp), status=resp.status_code, headers=response_headers)

def cleanup(*_):
    hm.remove()
    os._exit(0)

def main():
    ensure_cert()
    hm.apply()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("请开始直播...")

    app.run(
        host="0.0.0.0",
        port=443,
        ssl_context=(SERVER_CERT, SERVER_KEY),
        threaded=True,
        debug=False,
        use_reloader=False,
    )

if __name__ == "__main__":
    main()
    print("按任意键退出...")
    msvcrt.getch()
