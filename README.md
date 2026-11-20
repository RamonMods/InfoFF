# InfoFF

Ficha completa de um jogador de Free Fire a partir do UID: nível, experiência, likes, ranks, guilda, pet, social, honra, itens equipados e histórico de passes. Site e API no mesmo serviço.

- Site: https://infoff.onrender.com
- Espelho estático (sem busca): https://ramonmods.github.io/InfoFF/

## Como usar

Digite o UID (5 a 15 dígitos), escolha a região e pronto. Sem login, sem senha — a consulta vai direto ao servidor do jogo.

O link fica compartilhável: `/?uid=8684131934&region=BR`.

## API

```
GET /info?uid=8684131934&region=BR
```

| Parâmetro | Obrigatório | O que é |
|---|---|---|
| `uid` | sim | ID do jogador, 5 a 15 dígitos |
| `region` | não | BR (padrão), US, IND, ME, ID, TH, VN, SG, MY, PH, PK, BD, EU, RU, CIS, NA, SAC, AFR, TW |

Também responde em `/api/info`. CORS liberado, resposta em JSON:

```json
{
  "ok": true,
  "uid": 8684131934,
  "regiao": "BR",
  "consultado_em": 1795190814,
  "cache": false,
  "jogador": {
    "nome": "DEUS !777",
    "uid": 8684131934,
    "regiao": "BR",
    "nivel": 1,
    "exp": 0,
    "likes": 102,
    "tipo_conta": "Conta de jogo",
    "conta_criada_em": 1720000000,
    "ultimo_login_em": 1795100000,
    "versao_cliente": "OB55",
    "passe_elite": false,
    "ranks": {
      "br": { "rank": 301, "pontos": 1000, "recorde": 301, "visivel": false },
      "cs": { "rank": 301, "pontos": 0, "recorde": 301, "visivel": false },
      "mostrado_no_perfil": "Nenhum",
      "bloqueado_cs": false
    },
    "aparencia": { "avatar_id": 102000005, "banner_id": 0, "titulo_id": 0, "badge_id": 1001000102 },
    "guilda": { "nome": "Sem guilda", "id": 0, "nivel": 0, "membros": 0, "capacidade": 0, "lider": "—" },
    "pet": { "nome": "Sem pet", "id": 0, "nivel": 0, "exp": 0 },
    "social": { "assinatura": "Sem assinatura", "genero": "Não informado", "idioma": "Português" },
    "honra": { "pontuacao": 100, "partidas_semana": 0, "likes_periodo": 0, "denuncias_periodo": 0 },
    "diamantes_gastos": 800,
    "passes": []
  },
  "cluster": "client.us.freefiremobile.com",
  "tempo_ms": 8697
}
```

Erros vêm com `ok: false`, `codigo` e `erro`:

| HTTP | `codigo` | Quando acontece |
|---|---|---|
| 400 | `uid_invalido` | UID fora de 5 a 15 dígitos |
| 400 | `regiao_invalida` | Região fora da lista |
| 404 | `nao_encontrado` | UID não existe nessa região |
| 502 | `login` / `conta` / `consulta` | A Garena recusou a consulta |
| 500 | `interno` | Falha inesperada |

O campo `ranks.br.rank` é o código do rank no servidor (ex.: `301`); use `pontos` e `recorde` para exibir progresso.

## Rodando local

```bash
pip install -r api/requirements.txt
python api/app.py
```

Abre em `http://127.0.0.1:5000`. A primeira consulta de cada região cria uma conta de sessão nova e leva uns 10 s; depois fica em cache por uma hora.

Variáveis de ambiente:

| Variável | Padrão | Para quê |
|---|---|---|
| `PORT` | `5000` | Porta do servidor local |
| `FF_RELEASE_VERSION` | `OB55` | Versão do cliente que o login anuncia |
| `FF_SESSION_TTL` | `3600` | Segundos que a sessão da Garena fica em cache |
| `INFOFF_CACHE` | `120` | Segundos que uma ficha consultada fica em cache |
| `FF_ACCOUNT_BR` | — | Conta fixa no formato `uid:senha` (opcional; sem ela o serviço cria uma guest) |

## Estrutura

```
api/            Flask: serve o site e responde /info
core/           cliente da Garena (login, sessão, JWT) e leitura da ficha
proto/          protobufs do cliente do jogo
public/         site (HTML, CSS, JS, ícones, fontes)
render.yaml     serviço do Render
```

---

Se o InfoFF te ajudou, um café ajuda a manter as contas de consulta no ar: **[pixgg.com/ramon](https://pixgg.com/ramon)**
