import os
import threading
import time

_tunnel = None
_tunnel_url = None
_tunnel_status = "stopped"
_tunnel_error = None
_lock = threading.Lock()


def _get_authtoken():
    return os.environ.get("NGROK_AUTHTOKEN", "").strip()


def start_tunnel(port=5000, authtoken=None):
    global _tunnel, _tunnel_url, _tunnel_status, _tunnel_error
    with _lock:
        if _tunnel_status == "running" and _tunnel_url:
            return {"ok": True, "url": _tunnel_url, "status": "already_running"}
        try:
            from pyngrok import ngrok, conf
            token = authtoken or _get_authtoken()
            if not token:
                _tunnel_status = "error"
                _tunnel_error = "Χρειάζεται NGROK_AUTHTOKEN. Φτιάξε δωρεάν λογαριασμό στο ngrok.com και βάλε το token."
                return {"ok": False, "error": _tunnel_error}

            conf.get_default().auth_token = token
            _tunnel_status = "starting"
            _tunnel_error = None

            # Κλείσε τυχόν υπάρχοντα tunnels
            for t in ngrok.get_tunnels():
                ngrok.disconnect(t.public_url)

            tunnel = ngrok.connect(port, "http")
            _tunnel = tunnel
            _tunnel_url = tunnel.public_url
            # Προτίμα https αν υπάρχει
            if _tunnel_url.startswith("http://"):
                _tunnel_url = _tunnel_url.replace("http://", "https://", 1)
            _tunnel_status = "running"
            return {"ok": True, "url": _tunnel_url, "status": "running"}

        except Exception as e:
            _tunnel_status = "error"
            _tunnel_error = str(e)
            _tunnel_url = None
            return {"ok": False, "error": str(e)}


def stop_tunnel():
    global _tunnel, _tunnel_url, _tunnel_status, _tunnel_error
    with _lock:
        try:
            from pyngrok import ngrok
            for t in ngrok.get_tunnels():
                ngrok.disconnect(t.public_url)
            ngrok.kill()
        except Exception:
            pass
        _tunnel = None
        _tunnel_url = None
        _tunnel_status = "stopped"
        _tunnel_error = None
        return {"ok": True, "status": "stopped"}


def tunnel_status():
    return {
        "status": _tunnel_status,
        "url": _tunnel_url,
        "error": _tunnel_error,
        "has_token": bool(_get_authtoken()),
    }
