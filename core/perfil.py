# -*- coding: utf-8 -*-
# --- Consulta de perfil: GetPlayerPersonalShow e tradução dos campos. --- #
import re
import time
from typing import Dict, List, Optional

from core.garena import (
    GarenaError,
    _criptografar,
    _headers_jogo,
    _ler_campos,
    abrir_sessao,
    host_do_jogo,
    invalidar_sessao,
)
from proto import AccountPersonalShow_pb2, main_pb2

# --- rótulos dos enums que o jogo devolve como número. --- #
GENEROS = {0: "Não informado", 1: "Masculino", 2: "Feminino", 999: "Prefere não dizer"}
IDIOMAS = {
    0: "Não informado", 1: "Inglês", 2: "Chinês simplificado", 3: "Chinês tradicional",
    4: "Tailandês", 5: "Vietnamita", 6: "Indonésio", 7: "Português", 8: "Espanhol",
    9: "Russo", 10: "Coreano", 11: "Francês", 12: "Alemão", 13: "Turco", 14: "Híndi",
    15: "Japonês", 16: "Romeno", 17: "Árabe", 18: "Birmanês", 19: "Urdu", 20: "Bengali",
    999: "Prefere não dizer",
}
HORARIOS = {0: "Não informado", 1: "Dias úteis", 2: "Fins de semana", 999: "Qualquer dia"}
TURNOS = {0: "Não informado", 1: "Manhã", 2: "Tarde", 3: "Noite", 999: "Qualquer hora"}
MODOS = {0: "Não informado", 1: "Battle Royale", 2: "Contra Squad", 3: "Modos casuais", 999: "Todos"}
RANK_MOSTRADO = {0: "Nenhum", 1: "Rank BR", 2: "Rank CS", 999: "Todos"}
VETERANO = {0: "Conta nova", 1: "Pouco tempo", 2: "Tempo médio", 3: "Antiga", 4: "Muito antiga"}
TIPOS_CONTA = {0: "Visitante", 1: "Conta de jogo"}

# --- rótulos das tags sociais que o jogador escolhe no perfil. --- #
TAGS_SOCIAIS = {
    2101: "Moda", 2102: "Social", 2103: "Veterano", 2104: "Novato",
    2105: "Joga para vencer", 2106: "Joga por diversão", 2107: "Usa voz", 2108: "Sem voz",
}
TAGS_BATALHA = {
    1101: "Dominação", 1102: "Sem coroa", 1103: "Melhor parceiro", 1104: "Sniper",
    1105: "Corpo a corpo", 1106: "Pacificador", 1107: "Emboscada", 1108: "Suporte",
    1109: "Fúria", 1110: "Líder",
}


def _segundos(valor: int) -> int:
    # --- a Garena manda ora segundos, ora milissegundos. --- #
    valor = int(valor or 0)
    return valor // 1000 if valor > 10 ** 11 else valor


def _texto(valor) -> str:
    # --- nome/assinatura podem vir com tabs e espaços repetidos. --- #
    return re.sub(r"\s+", " ", (valor or "")).strip()


def _serializar_perfil(perfil) -> Dict:
    # --- transforma o protobuf em um dicionário pronto para a tela. --- #
    basic = perfil.basic_info
    profile = perfil.profile_info
    clan = perfil.clan_basic_info
    capitao = perfil.captain_basic_info
    pet = perfil.pet_info
    social = perfil.social_info
    credito = perfil.credit_score_info
    diamantes = perfil.diamond_cost_res

    tags_sociais = [TAGS_SOCIAIS.get(tag) for tag in social.social_tag if tag in TAGS_SOCIAIS]
    tags_batalha = [TAGS_BATALHA.get(tag) for tag in social.battle_tag if tag in TAGS_BATALHA]

    passes: List[Dict] = []
    for passe in perfil.history_ep_info:
        passes.append({
            "evento": _texto(passe.event_name) or "Temporada %d" % passe.ep_event_id,
            "nivel_maximo": int(passe.max_level),
            "badge_id": int(passe.ep_badge),
            "tem_passe": bool(passe.owned_pass),
        })

    conquistas = [
        {"id": int(item.ach_id), "nivel": int(item.level)}
        for item in perfil.equipped_ach
    ]

    destaques = []
    for destaque in basic.social_high_lights_with_basic_info.social_high_lights:
        destaques.append({"tipo": int(destaque.high_light), "valor": int(destaque.value)})

    return {
        "nome": _texto(basic.nickname) or "Jogador sem nome",
        "uid": int(basic.account_id),
        "regiao": _texto(basic.region) or "—",
        "nivel": int(basic.level),
        "exp": int(basic.exp),
        "likes": int(basic.liked),
        "tipo_conta": TIPOS_CONTA.get(int(basic.account_type), "Conta de jogo"),
        "conta_criada_em": _segundos(basic.create_at),
        "ultimo_login_em": _segundos(basic.last_login_at),
        "versao_cliente": _texto(basic.release_version) or "—",
        "passe_elite": bool(basic.has_elite_pass),
        "temporada_id": int(basic.season_id),
        "veterano": VETERANO.get(int(basic.veteran_leave_days_tag), "—"),
        "ranks": {
            "br": {
                "rank": int(basic.rank),
                "pontos": int(basic.ranking_points),
                "recorde": int(basic.max_rank),
                "pontos_recorde": int(basic.max_ranking_points),
                "posicao_pico": int(basic.peak_rank_pos),
                "visivel": bool(basic.show_br_rank),
            },
            "cs": {
                "rank": int(basic.cs_rank),
                "pontos": int(basic.cs_ranking_points),
                "recorde": int(basic.cs_max_rank),
                "posicao_pico": int(basic.cs_peak_rank_pos),
                "visivel": bool(basic.show_cs_rank),
            },
            "mostrado_no_perfil": RANK_MOSTRADO.get(int(social.rank_show), "—"),
            "bloqueado_cs": bool(basic.is_cs_ranking_ban),
        },
        "aparencia": {
            "avatar_id": int(profile.avatar_id),
            "skin_color": int(profile.skin_color),
            "banner_id": int(basic.banner_id),
            "head_pic": int(basic.head_pic),
            "titulo_id": int(basic.title),
            "badge_id": int(basic.badge_id),
            "badge_qtd": int(basic.badge_cnt),
            "pin_id": int(basic.pin_id),
            "roupas": [int(item) for item in profile.clothes],
            "habilidades": [int(item) for item in profile.equiped_skills],
            "skins_de_arma": [int(item) for item in basic.weapon_skin_shows],
            "conquistas": conquistas,
            "destaques": destaques,
        },
        "guilda": {
            "id": int(clan.clan_id),
            "nome": _texto(clan.clan_name) or "Sem guilda",
            "nivel": int(clan.clan_level),
            "membros": int(clan.member_num),
            "capacidade": int(clan.capacity),
            "honra": int(clan.honor_point),
            "lider": _texto(capitao.nickname) or "—",
            "lider_uid": int(capitao.account_id),
            "lider_nivel": int(capitao.level),
            "tem_guilda": int(clan.clan_id) > 0,
        },
        "pet": {
            "id": int(pet.id),
            "nome": _texto(pet.name) or "Sem pet",
            "nivel": int(pet.level),
            "exp": int(pet.exp),
            "skin_id": int(pet.skin_id),
            "skill_id": int(pet.selected_skill_id),
            "selecionado": bool(pet.is_selected),
            "tem_pet": int(pet.id) > 0,
        },
        "social": {
            "assinatura": _texto(social.signature) or "Sem assinatura",
            "genero": GENEROS.get(int(social.gender), "—"),
            "idioma": IDIOMAS.get(int(social.language), "—"),
            "dias_de_jogo": HORARIOS.get(int(social.time_online), "—"),
            "horario": TURNOS.get(int(social.time_active), "—"),
            "modo_preferido": MODOS.get(int(social.mode_prefer), "—"),
            "tags": tags_sociais,
            "tags_de_batalha": tags_batalha,
        },
        "honra": {
            "pontuacao": int(credito.credit_score),
            "partidas_semana": int(credito.weekly_match_cnt),
            "likes_periodo": int(credito.periodic_summary_like_cnt),
            "denuncias_periodo": int(credito.periodic_summary_illegal_cnt),
        },
        "diamantes_gastos": int(diamantes.diamond_cost),
        "passes": passes,
    }


def _pedir_perfil(sessao, token: str, host: str, uid: int) -> Optional[bytes]:
    mensagem = main_pb2.GetPlayerPersonalShow()
    mensagem.a = int(uid)
    mensagem.b = 7
    resposta = sessao.post(
        "https://%s/GetPlayerPersonalShow" % host,
        data=_criptografar(mensagem.SerializeToString()),
        timeout=25,
        verify=False,
        headers=_headers_jogo(token),
    )
    if resposta.status_code == 401:
        raise GarenaError("A Garena recusou o token desta sessão.", "sessao")
    if resposta.status_code in (400, 404):
        # --- o servidor responde 400 quando o UID não existe naquela região. --- #
        raise GarenaError("UID não encontrado nessa região.", "nao_encontrado")
    if resposta.status_code != 200:
        raise GarenaError("A consulta foi recusada pela Garena (HTTP %s)." % resposta.status_code, "consulta")
    if not resposta.content:
        raise GarenaError("A Garena devolveu uma resposta vazia.", "consulta")
    return resposta.content


def consultar_perfil(uid: int, regiao: str = "BR") -> Dict:
    # --- fluxo completo: sessão em cache -> pedido -> tradução. --- #
    regiao = (regiao or "BR").strip().upper()
    inicio = time.time()

    for tentativa in (1, 2):
        dados = abrir_sessao(regiao)
        host = host_do_jogo(dados.get("server_url"), regiao)
        try:
            bruto = _pedir_perfil(dados["sessao"], str(dados["token"]), host, uid)
        except GarenaError as erro:
            if erro.codigo == "sessao" and tentativa == 1:
                # --- token vencido: descarta a sessão e tenta uma vez mais. --- #
                invalidar_sessao(regiao)
                continue
            raise

        perfil = AccountPersonalShow_pb2.AccountPersonalShowInfo()
        try:
            perfil.ParseFromString(bruto)
        except Exception:
            raise GarenaError("Não foi possível ler a ficha devolvida pela Garena.", "consulta")

        jogador = _serializar_perfil(perfil)
        if not jogador["uid"]:
            # --- resposta vazia também significa UID inexistente. --- #
            raise GarenaError("UID não encontrado nessa região.", "nao_encontrado")
        jogador["regiao"] = jogador["regiao"] if jogador["regiao"] != "—" else regiao
        return {
            "jogador": jogador,
            "cluster": host,
            "tempo_ms": int((time.time() - inicio) * 1000),
        }

    raise GarenaError("Não foi possível abrir uma sessão válida com a Garena.", "sessao")
