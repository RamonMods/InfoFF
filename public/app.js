/* --- InfoFF: consulta da ficha e montagem do dossiê. --- */

const form = document.getElementById("form-busca");
const campoUid = document.getElementById("uid");
const campoRegiao = document.getElementById("regiao");

const secaoResultado = document.getElementById("ficha");
const metaConsulta = document.getElementById("resultado-meta");
const caixaAviso = document.getElementById("aviso");
const caixaCarregando = document.getElementById("carregando");
const cronometro = document.getElementById("cronometro");
const dossie = document.getElementById("dossie");
const secoes = document.getElementById("secoes");

const REGIOES = {
  BR: "Brasil", US: "Estados Unidos", IND: "Índia", ME: "Oriente Médio",
  ID: "Indonésia", TH: "Tailândia", VN: "Vietnã", SG: "Singapura",
  MY: "Malásia", PH: "Filipinas", PK: "Paquistão", BD: "Bangladesh",
  EU: "Europa", RU: "Rússia", CIS: "Comunidade CIS", NA: "América do Norte",
  SAC: "América do Sul", AFR: "África", TW: "Taiwan",
};

let intervalo = null;
let inicioConsulta = 0;

/* --- endereço da API: no Render é o próprio site; no Pages vem do meta. --- */
const metaApi = document.querySelector('meta[name="infoff-api"]');
const servidoPelaApi = /(^|\.)onrender\.com$/.test(location.hostname)
  || location.hostname === "localhost"
  || location.hostname === "127.0.0.1";
const API_BASE = servidoPelaApi ? "" : ((metaApi && metaApi.content) || "").replace(/\/+$/, "");

/* --- utilidades de formatação --- */

function escapar(texto) {
  return String(texto == null ? "" : texto)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function numero(valor) {
  const n = Number(valor || 0);
  return Number.isFinite(n) ? n.toLocaleString("pt-BR") : "0";
}

/* --- UID, ids de item e códigos não levam separador de milhar. --- */
function codigo(valor) {
  return String(valor == null || valor === "" ? 0 : valor);
}

function data(unix) {
  const segundos = Number(unix || 0);
  if (!segundos) return null;
  const d = new Date(segundos * 1000);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function horaCompleta(unix) {
  const d = new Date(Number(unix || Date.now() / 1000) * 1000);
  return d.toLocaleString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

/* --- blocos do dossiê --- */

function campo(rotulo, valor, opcoes = {}) {
  const vazio = valor === null || valor === undefined || valor === "";
  const classes = ["campo-valor"];
  if (opcoes.num) classes.push("num");
  if (vazio) classes.push("vazio");

  const conteudo = vazio
    ? escapar(opcoes.vazio || "—")
    : escapar(valor) + (opcoes.miudo ? `<span class="miudo">${escapar(opcoes.miudo)}</span>` : "");

  return `<div class="campo${opcoes.largo ? " largo" : ""}">
      <span class="campo-rotulo">${escapar(rotulo)}</span>
      <span class="${classes.join(" ")}">${conteudo}</span>
    </div>`;
}

function secao(indice, titulo, corpo) {
  return `<section class="secao">
      <h4><b>${indice}</b>${escapar(titulo)}</h4>
      ${corpo}
    </section>`;
}

function grade(campos) {
  return `<div class="grade">${campos.join("")}</div>`;
}

function tags(lista) {
  if (!lista || !lista.length) return "";
  return `<div class="tags">${lista.map((t) => `<span class="tag">${escapar(t)}</span>`).join("")}</div>`;
}

function montarSecoes(jogador) {
  const ranks = jogador.ranks || {};
  const br = ranks.br || {};
  const cs = ranks.cs || {};
  const guilda = jogador.guilda || {};
  const pet = jogador.pet || {};
  const social = jogador.social || {};
  const honra = jogador.honra || {};
  const aparencia = jogador.aparencia || {};
  const passes = jogador.passes || [];

  const blocos = [];

  blocos.push(secao("01", "Identificação", grade([
    campo("Nível", numero(jogador.nivel), { num: true }),
    campo("Experiência", numero(jogador.exp), { num: true }),
    campo("Likes", numero(jogador.likes), { num: true }),
    campo("Tipo de conta", jogador.tipo_conta),
    campo("Conta criada em", data(jogador.conta_criada_em), { vazio: "Não informado" }),
    campo("Último login", data(jogador.ultimo_login_em), { vazio: "Não informado" }),
    campo("Cliente", jogador.versao_cliente),
    campo("Veterano", jogador.veterano),
    campo("Passe Elite", jogador.passe_elite ? "Sim" : "Não"),
    campo("Temporada", numero(jogador.temporada_id), { num: true }),
  ])));

  blocos.push(secao("02", "Ranks", grade([
    campo("Pontos BR", numero(br.pontos), { num: true, miudo: "recorde " + numero(br.pontos_recorde) + " pts" }),
    campo("Código BR", codigo(br.rank), { num: true, miudo: "código do servidor" }),
    campo("Pontos CS", numero(cs.pontos), { num: true, miudo: "recorde " + numero(cs.pontos_recorde) + " pts" }),
    campo("Código CS", codigo(cs.rank), { num: true, miudo: "código do servidor" }),
    campo("Rank no perfil", ranks.mostrado_no_perfil || "—"),
    campo("Rank CS", cs.bloqueado_cs ? "Bloqueado" : "Liberado"),
  ])));

  blocos.push(secao("03", "Guilda", grade([
    campo("Nome", guilda.tem_guilda ? guilda.nome : "Sem guilda", { largo: true, vazio: "Sem guilda" }),
    campo("ID", codigo(guilda.id), { num: true }),
    campo("Nível", numero(guilda.nivel), { num: true }),
    campo("Membros", numero(guilda.membros) + " / " + numero(guilda.capacidade), { num: true }),
    campo("Honra", numero(guilda.honra), { num: true }),
    campo("Líder", guilda.tem_guilda ? guilda.lider : "—", { largo: true }),
    campo("UID do líder", codigo(guilda.lider_uid), { num: true }),
  ])));

  blocos.push(secao("04", "Pet", grade([
    campo("Nome", pet.tem_pet ? pet.nome : "Sem pet", { vazio: "Sem pet" }),
    campo("ID", codigo(pet.id), { num: true }),
    campo("Nível", numero(pet.nivel), { num: true }),
    campo("Experiência", numero(pet.exp), { num: true }),
    campo("Skin", codigo(pet.skin_id), { num: true }),
    campo("Habilidade", codigo(pet.skill_id), { num: true }),
  ])));

  const tagsSociais = tags(social.tags);
  const tagsBatalha = tags(social.tags_de_batalha);

  blocos.push(secao("05", "Social", grade([
    campo("Assinatura", social.assinatura, { largo: true, vazio: "Sem assinatura" }),
    campo("Gênero", social.genero),
    campo("Idioma", social.idioma),
    campo("Dias de jogo", social.dias_de_jogo),
    campo("Horário", social.horario),
    campo("Modo preferido", social.modo_preferido),
    tagsSociais ? `<div class="campo largo"><span class="campo-rotulo">Tags</span>${tagsSociais}</div>` : "",
    tagsBatalha ? `<div class="campo largo"><span class="campo-rotulo">Tags de batalha</span>${tagsBatalha}</div>` : "",
  ])));

  blocos.push(secao("06", "Aparência", grade([
    campo("Avatar", codigo(aparencia.avatar_id), { num: true }),
    campo("Banner", codigo(aparencia.banner_id), { num: true }),
    campo("Título", codigo(aparencia.titulo_id), { num: true }),
    campo("Badge", codigo(aparencia.badge_id), { num: true, miudo: numero(aparencia.badge_qtd) + " badges" }),
    campo("Pin", codigo(aparencia.pin_id), { num: true }),
    campo("Cor de pele", codigo(aparencia.skin_color), { num: true }),
    campo("Roupas", numero((aparencia.roupas || []).length) + " itens", { num: true }),
    campo("Habilidades", numero((aparencia.habilidades || []).length) + " itens", { num: true }),
    campo("Skins de arma", numero((aparencia.skins_de_arma || []).length) + " itens", { num: true }),
    campo("Conquistas", numero((aparencia.conquistas || []).length) + " equipadas", { num: true }),
  ])));

  blocos.push(secao("07", "Honra e gastos", grade([
    campo("Pontuação de honra", numero(honra.pontuacao), { num: true }),
    campo("Partidas na semana", numero(honra.partidas_semana), { num: true }),
    campo("Likes no período", numero(honra.likes_periodo), { num: true }),
    campo("Denúncias no período", numero(honra.denuncias_periodo), { num: true }),
    campo("Diamantes gastos", numero(jogador.diamantes_gastos), { num: true }),
  ])));

  if (passes.length) {
    const lista = passes.map((passe) => `
      <div class="passe">
        <span class="passe-nome">${escapar(passe.evento)}</span>
        <span class="passe-meta">nível ${numero(passe.nivel_maximo)}${passe.tem_passe ? " · passe" : ""}</span>
      </div>`).join("");
    blocos.push(secao("08", "Histórico de passes", `<div class="lista-passes">${lista}</div>`));
  }

  return blocos.join("");
}

/* --- estados da tela --- */

function limparEstados() {
  caixaAviso.hidden = true;
  caixaAviso.innerHTML = "";
  caixaCarregando.hidden = true;
  dossie.hidden = true;
}

function mostrarAviso(titulo, detalhe) {
  caixaAviso.innerHTML = `<p>${escapar(titulo)}${detalhe ? `<small>${escapar(detalhe)}</small>` : ""}</p>`;
  caixaAviso.hidden = false;
}

function comecarCronometro() {
  inicioConsulta = performance.now();
  cronometro.textContent = "0,0 s";
  intervalo = setInterval(() => {
    const segundos = (performance.now() - inicioConsulta) / 1000;
    cronometro.textContent = segundos.toFixed(1).replace(".", ",") + " s";
  }, 100);
}

function pararCronometro() {
  if (intervalo) clearInterval(intervalo);
  intervalo = null;
}

/* --- renderização do dossiê --- */

function mostrarDossie(dados) {
  const jogador = dados.jogador || {};
  const inicial = (jogador.nome || "?").trim().charAt(0) || "?";

  document.getElementById("monograma").textContent = inicial;
  document.getElementById("jogador-nome").textContent = jogador.nome || "Jogador sem nome";
  document.getElementById("jogador-uid").textContent = "UID " + codigo(jogador.uid);
  document.getElementById("jogador-regiao").textContent = REGIOES[jogador.regiao] || jogador.regiao;
  document.getElementById("jogador-nivel").textContent = "Nível " + numero(jogador.nivel);

  const assinatura = (jogador.social || {}).assinatura;
  const assinaturaEl = document.getElementById("jogador-assinatura");
  assinaturaEl.textContent = assinatura && assinatura !== "Sem assinatura" ? "“" + assinatura + "”" : "";
  assinaturaEl.hidden = !assinaturaEl.textContent;

  document.getElementById("dossie-registro").textContent = "Registro nº " + codigo(jogador.uid);
  document.getElementById("dossie-selo").textContent = jogador.regiao;

  const segundos = ((dados.tempo_ms || 0) / 1000).toFixed(1).replace(".", ",");
  document.getElementById("dossie-consulta").textContent =
    "Consultado em " + horaCompleta(dados.consultado_em) + " · " + segundos + " s";

  secoes.innerHTML = montarSecoes(jogador);
  dossie.hidden = false;
}

/* --- consulta --- */

async function consultar(uid, regiao) {
  limparEstados();
  secaoResultado.hidden = false;
  caixaCarregando.hidden = false;
  comecarCronometro();

  const botao = form.querySelector("button");
  botao.disabled = true;
  metaConsulta.textContent = "UID " + uid + " · " + regiao;

  try {
    const resposta = await fetch(`${API_BASE}/info?uid=${encodeURIComponent(uid)}&region=${encodeURIComponent(regiao)}`, {
      headers: { Accept: "application/json" },
    });
    const dados = await resposta.json().catch(() => null);

    if (!resposta.ok || !dados || !dados.ok) {
      const mensagem = (dados && dados.erro) || "Não foi possível abrir a ficha agora.";
      const dica = dados && dados.codigo === "nao_encontrado"
        ? "Confira o UID e a região: o mesmo UID pode existir só em um servidor."
        : resposta.status >= 500
          ? "O servidor do jogo pode estar instável. Tente de novo em alguns segundos."
          : "";
      mostrarAviso(mensagem, dica);
      metaConsulta.textContent = "UID " + uid + " · " + regiao;
      return;
    }

    mostrarDossie(dados);
    metaConsulta.textContent = "UID " + codigo(dados.uid) + " · " + dados.regiao +
      (dados.cache ? " · resposta guardada" : "");
  } catch (erro) {
    mostrarAviso("A consulta não chegou ao servidor.", "Verifique sua conexão e tente de novo.");
  } finally {
    pararCronometro();
    caixaCarregando.hidden = true;
    botao.disabled = false;
  }
}

/* --- eventos --- */

form.addEventListener("submit", (evento) => {
  evento.preventDefault();
  const uid = (campoUid.value || "").replace(/\D/g, "");
  const regiao = campoRegiao.value;

  if (uid.length < 5) {
    limparEstados();
    secaoResultado.hidden = false;
    mostrarAviso("O UID precisa ter pelo menos 5 dígitos.", "Ele aparece no perfil do jogador, dentro do jogo.");
    campoUid.focus();
    return;
  }

  campoUid.value = uid;
  const url = new URL(window.location.href);
  url.searchParams.set("uid", uid);
  url.searchParams.set("region", regiao);
  history.replaceState(null, "", url);

  consultar(uid, regiao);
  secaoResultado.scrollIntoView({ behavior: "smooth", block: "start" });
});

campoUid.addEventListener("input", () => {
  campoUid.value = campoUid.value.replace(/\D/g, "").slice(0, 15);
});

/* --- link direto: /?uid=...&region=... --- */
(function abrirDoLink() {
  const params = new URLSearchParams(window.location.search);
  const uid = (params.get("uid") || "").replace(/\D/g, "");
  const regiao = (params.get("region") || params.get("server_name") || "").toUpperCase();
  if (uid.length >= 5) {
    campoUid.value = uid;
    if (REGIOES[regiao]) campoRegiao.value = regiao;
    consultar(uid, campoRegiao.value);
  }
})();

/* --- service worker: casca offline e abertura instantânea. --- */
if ("serviceWorker" in navigator && location.protocol === "https:") {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  });
}
