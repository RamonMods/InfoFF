# -*- coding: utf-8 -*-
# --- Nomes dos itens do Free Fire: mapa local ID -> nome/tipo/raridade. ---
import json
import os
import threading
from typing import Dict, Optional

CAMINHO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "itens.json"
)

TIPOS = {
    "C": "Personagem", "A": "Avatar", "B": "Banner", "H": "Cabeça",
    "T": "Camiseta", "O": "Calça", "S": "Sapato", "M": "Máscara",
    "F": "Pintura facial", "G": "Mochila", "W": "Skin de arma",
    "P": "Pin de perfil", "E": "Pet", "K": "Skin de pet", "L": "Habilidade de pet",
    "R": "Emote", "D": "Muralha", "Q": "Paraquedas", "Y": "Prancha",
    "V": "Veículo", "N": "Granada", "U": "Pacote",
}
RARIDADES = {
    "0": "—", "1": "Comum", "2": "Incomum", "3": "Rara",
    "4": "Épica", "5": "Lendária", "6": "Mítica", "7": "Dourada",
}

_mapa: Optional[Dict[str, list]] = None
_trava = threading.Lock()

# --- chaves que guardam IDs de item (não confundir com UID, nível ou pontos). ---
CHAVES_ID = {
    "avatar_id", "head_pic", "banner_id", "titulo_id", "badge_id", "pin_id",
    "arma_pve", "skin_id", "skill_id", "pet_id",
    "roupas", "habilidades", "skins_de_arma", "efeitos", "slots", "itens",
    "mochila",
}


def _carregar() -> Dict[str, list]:
    global _mapa
    if _mapa is None:
        with _trava:
            if _mapa is None:
                with open(CAMINHO, "r", encoding="utf-8") as arquivo:
                    _mapa = json.load(arquivo)
    return _mapa


def buscar(ident) -> Optional[Dict[str, str]]:
    # --- devolve nome, tipo e raridade de um ID de item. ---
    try:
        dados = _carregar().get(str(int(ident)))
    except (TypeError, ValueError):
        return None
    if not dados:
        return None
    return {
        "nome": dados[0],
        "tipo": TIPOS.get(dados[1], "Item"),
        "raridade": RARIDADES.get(dados[2], "—"),
    }


def nomes_do_perfil(jogador: Dict) -> Dict[str, Dict[str, str]]:
    # --- monta um dicionário só com os itens presentes na ficha. ---
    encontrados: Dict[str, Dict[str, str]] = {}

    def adicionar(ident):
        if isinstance(ident, int) and ident >= 10000:
            dado = buscar(ident)
            if dado:
                encontrados[str(ident)] = dado

    def caminhar(valor, chave=None):
        if isinstance(valor, dict):
            if chave == "pet":
                adicionar(valor.get("id"))
            for filho, conteudo in valor.items():
                caminhar(conteudo, filho)
        elif isinstance(valor, list):
            for conteudo in valor:
                if chave == "conquistas" and isinstance(conteudo, dict):
                    adicionar(conteudo.get("id"))
                caminhar(conteudo, chave)
        elif chave in CHAVES_ID:
            adicionar(valor)

    caminhar(jogador)
    return encontrados
