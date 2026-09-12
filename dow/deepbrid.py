"""deepbrid.py - espejo Python de KurWeb app/deepbrid/deepbrid.gd.

POST https://www.deepbrid.com/api/v1/generate/link
  headers: Authorization: Bearer <api_key>, Content-Type: application/x-www-form-urlencoded
  body: link=<url>
Devuelve: {"filename","size","host","origin","generate"} o {"error": msg}
"""
from __future__ import annotations
import os
import urllib.parse
import urllib.request
import json

API_BASE = "https://www.deepbrid.com/api/v1"
TIMEOUT = 60


UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def _post_form(url: str, body: dict, api_key: str = "") -> tuple[int, str]:
    data = urllib.parse.urlencode(body).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, json.dumps({"error": 1, "message": str(e)})


def generar_link(link: str, api_key: str = "") -> dict:
    """Genera link válido de descarga. Igual que deepbrid.gd generar_link()."""
    link = (link or "").strip()
    api_key = (api_key or os.getenv("DEEPBRID_API_KEY") or "").strip()
    if not link:
        return {"error": "link vacio"}
    if not api_key:
        return {"error": "sin api key"}
    _, text = _post_form(API_BASE + "/generate/link", {"link": link}, api_key)
    try:
        data = json.loads(text)
    except Exception:
        return {"error": "json parse error: " + text[:200]}
    if isinstance(data, dict):
        if int(data.get("error", 0)) != 0:
            return {"error": str(data.get("message", "desconocido"))}
        direct = data.get("link", "")
        if not direct:
            return {"error": "error vacio: " + text[:200]}
        return {
            "filename": data.get("filename", ""),
            "size": data.get("size", ""),
            "host": data.get("hoster", ""),
            "origin": data.get("original_link", ""),
            "generate": direct,
        }
    return {"error": "respuesta inesperada: " + text[:200]}


def hosts() -> list | dict:
    """GET /hosts (sin auth), igual que _on_hosts_pressed."""
    req = urllib.request.Request(API_BASE + "/hosts", method="GET",
                                     headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def user_info(api_key: str = "") -> dict:
    """GET /user con Bearer, igual que _on_info_pressed."""
    api_key = (api_key or os.getenv("DEEPBRID_API_KEY") or "").strip()
    if not api_key:
        return {"error": "sin api key"}
    req = urllib.request.Request(API_BASE + "/user", method="GET",
                                 headers={"Authorization": "Bearer " + api_key,
                                          "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))
