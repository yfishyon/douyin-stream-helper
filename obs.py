from obswebsocket import obsws, requests, exceptions


def obs_is_online(host, port, password):
    try:
        s = socket.create_connection((host, port), 1)
        s.close()
        return True
    except Exception:
        return False

def obs_set_stream_and_start(host, port, password, server, key):
    ws = obsws(host, port, password)
    try:
        ws.connect()

        ws.call(
            requests.SetStreamServiceSettings(
                streamServiceType="rtmp_custom",
                streamServiceSettings={
                    "server": server,
                    "key": key,
                    "use_auth": False,
                },
            )
        )

        ws.call(requests.StartStream())
        print("成功推送到obs 直播已开启")
        return True
    except exceptions.OBSWebSocketError:
        return False
    finally:
        try:
            ws.disconnect()
        except Exception:
            pass
