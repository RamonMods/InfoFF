# -*- coding: utf-8 -*-
# --- API do InfoFF: serve o site e responde a ficha do jogador. --- #
import os
import re
import sys
import threading
import time
from typing import Dict, Tuple

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402

from core.garena import CLIENT_HOSTS, GarenaError  # noqa: E402
from core.perfil import consultar_perfil  # noqa: E402

app = Flask(__name__, static_folder=os.path.join(RAIZ, "public"), static_url_path="")
app.config["JSON_SORT_KEYS"] = False

# --- cache curto: duas consultas do mesmo UID em segundos custam uma só. --- #
_cache: Dict[Tuple[int, str], Tuple[float, Dict]] = {}
_cache_trava = threading.Lock()
CACHE_SEGUNDOS = int(os.environ.get("INFOFF_CACHE", "120"))

UID_VALIDO = re.compile(r"^\d{5,15}$")


def _cache_ler(chave: Tuple[int, str]):
    with _cache_trava:
        item = _cache.get(chave)
    if item and time.time() - item[0] < CACHE_SEGUNDOS:
        return item[1]
    return None


def _cache_gravar(chave: Tuple[int, str], valor: Dict) -> None:
    with _cache_trava:
        if len(_cache) > 500:
            _cache.clear()
        _cache[chave] = (time.time(), valor)


@app.after_request
def _cabecalhos(resposta):
    # --- a API é pública: libera o consumo por qualquer site/app. --- #
    if request.path.startswith("/info") or request.path.startswith("/api/"):
        resposta.headers["Access-Control-Allow-Origin"] = "*"
        resposta.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resposta.headers["Cache-Control"] = "public, max-age=60"
    elif resposta.mimetype in ("text/css", "application/javascript", "image/svg+xml"):
        resposta.headers["Cache-Control"] = "public, max-age=3600"
    elif resposta.mimetype == "text/html":
        resposta.headers["Cache-Control"] = "no-cache"
    return resposta


@app.route("/")
def inicio():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/healthz")
def healthz():
    return jsonify({"servico": "InfoFF", "status": "online"})


@app.route("/info", methods=["GET", "OPTIONS"])
@app.route("/api/info", methods=["GET", "OPTIONS"])
def info():
    # --- ficha do jogador: /info?uid=123456789&region=BR --- #
    if request.method == "OPTIONS":
        return ("", 204)

    uid_bruto = (request.args.get("uid") or "").strip()
    regiao = (request.args.get("region") or request.args.get("server_name") or "BR").strip().upper()

    if not UID_VALIDO.match(uid_bruto):
        return jsonify({
            "ok": False,
            "codigo": "uid_invalido",
            "erro": "O UID precisa ter de 5 a 15 dígitos, só números.",
        }), 400

    if regiao not in CLIENT_HOSTS:
        return jsonify({
            "ok": False,
            "codigo": "regiao_invalida",
            "erro": "Região '%s' não é suportada." % regiao,
            "regioes": sorted(CLIENT_HOSTS.keys()),
        }), 400

    uid = int(uid_bruto)
    chave = (uid, regiao)
    guardado = _cache_ler(chave)
    if guardado:
        resposta = dict(guardado)
        resposta["cache"] = True
        return jsonify(resposta)

    try:
        resultado = consultar_perfil(uid, regiao)
    except GarenaError as erro:
        if erro.codigo == "nao_encontrado":
            return jsonify({"ok": False, "codigo": erro.codigo, "erro": str(erro)}), 404
        if erro.codigo == "regiao":
            return jsonify({"ok": False, "codigo": erro.codigo, "erro": str(erro)}), 400
        return jsonify({"ok": False, "codigo": erro.codigo, "erro": str(erro)}), 502
    except Exception:
        return jsonify({
            "ok": False,
            "codigo": "interno",
            "erro": "Algo falhou ao consultar a Garena. Tente de novo em alguns segundos.",
        }), 500

    corpo = {
        "ok": True,
        "uid": uid,
        "regiao": regiao,
        "consultado_em": int(time.time()),
        "cache": False,
    }
    corpo.update(resultado)
    _cache_gravar(chave, corpo)
    return jsonify(corpo)


@app.errorhandler(404)
def _nao_achou(_erro):
    # --- rotas de arquivo do site caem aqui; a API responde JSON. --- #
    if request.path.startswith("/info") or request.path.startswith("/api/"):
        return jsonify({"ok": False, "codigo": "rota", "erro": "Rota não encontrada."}), 404
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=porta)
