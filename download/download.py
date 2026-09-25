"""download.py - espejo Python de kurweb.gd _stream_download/_stream_download_thread.

- Sigue redirects manual: max 10, codigos 301/302/303/307/308 via header Location
- UA: GodotDownloader/1.0 (igual que kurweb.gd)
- filename: Content-Disposition filename=, si no basename de URL, si no download.zip
- guarda por chunks en disco (streaming, sin cargar todo en RAM)
- crea el dir destino recursivo
- paso extra: mete un .txt de 10-20MB aleatorio y empaqueta archivo + txt en
  un zip. El zip queda en el mismo nombre (reemplaza al archivo crudo, que se
  borra) y eso es lo que devuelve la descarga.
"""
from __future__ import annotations
import os
import re
import urllib.parse
import urllib.request
import zipfile

from download.pad import generar_stream

UA = "GodotDownloader/1.0"
MAX_REDIRECTS = 10
CHUNK = 1024 * 64

# Relleno: temp.txt de 10 a 20MB sorteados (ver pad.mb_aleatorio).
NOMBRE_RELLENO = "temp.txt"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _filename(headers, url: str) -> str:
    cd = headers.get("Content-Disposition", "")
    if cd and "filename=" in cd:
        name = cd.split("filename=")[-1].strip().strip('"').strip("'")
        if name:
            return name
    path = urllib.parse.urlparse(url).path
    name = os.path.basename(path.rstrip("/"))
    name = name.split("?")[0]
    return name or "download.zip"


def empaquetar(ruta: str) -> str:
    """Arma un zip con el archivo + el temp.txt de relleno (10-20MB).

    El txt va al vuelo con generar_stream (no se escribe en disco). Al final
    el crudo se borra y el zip queda con el MISMO nombre de la ruta, para que
    quien llamaba la descarga siga encontrando el archivo donde estaba y no
    haya que tocar el consumidor.
    """
    tmp = ruta + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(ruta, os.path.basename(ruta))
        with zf.open(NOMBRE_RELLENO, "w") as zf_txt:
            for trozo in generar_stream():
                zf_txt.write(trozo)
    os.remove(ruta)
    os.replace(tmp, ruta)
    return ruta


def download(url: str, dest_dir: str, filename: str = "") -> str:
    """Descarga url (cdn, git, link generado) en dest_dir.

    Siempre: baja, le pega un temp.txt de 10-20MB aleatorios, lo empaqueta
    todo en un zip con el MISMO nombre, borra el crudo y devuelve esa ruta.
    """
    os.makedirs(dest_dir, exist_ok=True)
    opener = urllib.request.build_opener(_NoRedirect)
    current = url
    for _ in range(MAX_REDIRECTS):
        req = urllib.request.Request(current, method="GET",
                                     headers={"User-Agent": UA})
        try:
            resp = opener.open(req, timeout=60)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                loc = e.headers.get("Location", "").strip()
                if not loc:
                    raise RuntimeError("redirect sin Location")
                current = urllib.parse.urljoin(current, loc)
                continue
            raise
        if resp.status in (301, 302, 303, 307, 308):
            loc = resp.headers.get("Location", "").strip()
            resp.close()
            if not loc:
                raise RuntimeError("redirect sin Location")
            current = urllib.parse.urljoin(current, loc)
            continue
        name = filename or _filename(resp.headers, current)
        out = os.path.join(dest_dir, name)
        with open(out, "wb") as f:
            while True:
                chunk = resp.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)
        resp.close()
        return empaquetar(out)
    raise RuntimeError("demasiados redirects")
