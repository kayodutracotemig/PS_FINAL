/* =========================================================
   STADIUM GUIDE — lógica do frontend
   Tudo roda dentro de uma função anônima ( () => { ... } )()
   para não "poluir" o escopo global do navegador.
   ========================================================= */
(() => {
  'use strict';

  /* ---------- estado e atalhos ---------- */

  // "state" guarda o que o app precisa lembrar enquanto está aberto
  const state = {
    token: localStorage.getItem('sg_token') || null,
    usuario: null,          // resposta de GET /perfil
    times: [],
    jogos: [],              // próximos jogos
    passados: [],           // jogos antigos
    favoritos: new Set(),   // ids dos jogos favoritados
    subtab: 'casa',         // aba atual da lista de jogos
    modo: 'driving',        // modo de transporte da rota
    avaliando: null,        // jogo que está sendo avaliado no modal
    nota: 0,
    timer: null,            // setInterval da contagem regressiva
    mapa: null,             // instância do Leaflet
  };

  // atalho: $('id') = document.getElementById('id')
  const $ = (id) => document.getElementById(id);

  // Cria um elemento. Usamos textContent (e NÃO innerHTML) para texto que
  // vem do usuário/servidor: assim "<script>" digitado num comentário
  // aparece como texto e não é executado (evita XSS).
  function el(tag, className, text) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  // tira acentos e põe minúsculo: 'Atlético MG' -> 'atletico mg'
  const normalizar = (t) =>
    (t || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

  function iniciais(nome) {
    const p = (nome || '').trim().split(/\s+/);
    const i = p.length > 1 ? p[0][0] + p[1][0] : (nome || '--').slice(0, 2);
    return i.toUpperCase();
  }

  const MESES = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'];

  // /jogos/proximos manda ISO ("2026-11-01T18:30:00");
  // /jogos/passados manda "01/11/2026 18:30". Esta função entende os dois.
  function lerData(texto) {
    if (texto.includes('/')) {
      const [d, h = '00:00'] = texto.split(' ');
      const [dd, mm, aaaa] = d.split('/').map(Number);
      const [hh, mi] = h.split(':').map(Number);
      return new Date(aaaa, mm - 1, dd, hh, mi);
    }
    return new Date(texto);
  }

  const hora = (d) => d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

  const ICONE_ESTRELA = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2 14.5 8.5 21.5 9 16 13.5 18 20.5 12 16.5 6 20.5 8 13.5 2.5 9 9.5 8.5Z"/></svg>';
  const ICONE_CORACAO = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-8-4.9-9.6-10C1.4 7.8 3.4 5 6.5 5c2 0 3.7 1.1 5.5 3.1C13.800 6.1 15.500 5 17.500 5c3.100 0 5.100 2.800 4.100 6C20 16.100 12 21 12 21Z"/></svg>';

  /* ---------- comunicação com a API ---------- */

  // Todas as chamadas ao Flask passam por aqui.
  //  - Authorization: o back lê o token deste cabeçalho
  //  - body: objeto que vira JSON
  //  - form: FormData (upload de foto) — NÃO colocamos Content-Type,
  //    o navegador define sozinho (com o "boundary" do multipart)
  async function api(path, { method = 'GET', body, form } = {}) {
    const headers = {};
    if (state.token) headers['Authorization'] = state.token;

    let corpo;
    if (form) {
      corpo = form;
    } else if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
      corpo = JSON.stringify(body);
    }

    const res = await fetch(path, { method, headers, body: corpo });
    // se a resposta não for JSON (ex.: página de erro), .catch devolve {}
    const dados = await res.json().catch(() => ({}));
    if (!res.ok) {
      const erro = new Error(dados.erro || `Erro no servidor (${res.status})`);
      erro.status = res.status;
      throw erro;
    }
    return dados;
  }

  /* ---------- interface: avisos, telas, botões ---------- */

  function toast(mensagem, tipo = 'success') {
    const stack = $('toast-stack');
    const t = el('div', `toast toast-${tipo}`);
    t.append(el('span', '', mensagem));
    stack.append(t);
    setTimeout(() => t.remove(), 3500);
  }

  // mostra só uma das telas principais
  function showView(nome) {
    if (nome !== 'dashboard') document.documentElement.removeAttribute('data-team');
    ['loading', 'auth', 'team-select', 'dashboard'].forEach((v) => {
      $(`view-${v}`).classList.toggle('hidden', v !== nome);
    });
  }

  function aplicarTemaDoTime(nome) {
    const time = normalizar(nome);
    if (time.includes('atletico')) document.documentElement.setAttribute('data-team', 'atletico');
    else if (time.includes('cruzeiro')) document.documentElement.setAttribute('data-team', 'cruzeiro');
    else document.documentElement.removeAttribute('data-team');
  }

  // desabilita o botão e mostra o "spinner" enquanto a requisição roda
  function ocupado(botao, sim) {
    if (!botao) return;
    botao.disabled = sim;
    const sp = botao.querySelector('.btn-spinner');
    if (sp) sp.hidden = !sim;
  }

  function irParaAba(nome) {
    document.querySelectorAll('.tab-panel').forEach((p) => p.classList.add('hidden'));
    $(`tab-${nome}`).classList.remove('hidden');
    document.querySelectorAll('.nav-item').forEach((b) =>
      b.classList.toggle('is-active', b.dataset.nav === nome));

    if (nome === 'jogos') carregarJogos();
    if (nome === 'localizacao') renderBanner();
    if (nome === 'perfil') renderPerfil();
  }

  // Modal de confirmação reutilizável: devolve uma Promise<boolean>
  function confirmar(titulo, texto) {
    return new Promise((resolve) => {
      $('modal-title').textContent = titulo;
      $('modal-text').textContent = texto;
      const fundo = $('modal-backdrop');
      fundo.classList.remove('hidden');
      const fechar = (resposta) => {
        fundo.classList.add('hidden');
        resolve(resposta);
      };
      $('modal-confirm').onclick = () => fechar(true);
      $('modal-cancel').onclick = () => fechar(false);
    });
  }

  /* ---------- tema claro / escuro ---------- */

  function aplicarTema(tema) {
    document.documentElement.setAttribute('data-theme', tema);
    localStorage.setItem('sg_tema', tema);
  }

  function iniciarTema() {
    const salvo = localStorage.getItem('sg_tema');
    const escuroNoSistema = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    aplicarTema(salvo || (escuroNoSistema ? 'dark' : 'light'));
    $('btn-theme-toggle').onclick = () => {
      const atual = document.documentElement.getAttribute('data-theme');
      aplicarTema(atual === 'dark' ? 'light' : 'dark');
    };
  }

  /* ---------- sessão: bootstrap, login, cadastro, logout ---------- */

  function limparSessao() {
    localStorage.removeItem('sg_token');
    state.token = null;
    state.usuario = null;
    clearInterval(state.timer);
    if (state.mapa) { state.mapa.remove(); state.mapa = null; }
  }

  // Decide qual tela mostrar assim que o app abre
  async function bootstrap() {
    if (!state.token) { showView('auth'); return; }
    showView('loading');
    try {
      state.usuario = await api('/perfil');
      if (!state.usuario.time) {
        state.times = await api('/times');
        renderTeamSelect();
        showView('team-select');
      } else {
        await entrarNoDashboard();
        showView('dashboard');
      }
    } catch (e) {
      // só apaga o token se o servidor disse que a sessão é inválida (401);
      // se o servidor só estava fora do ar, mantém o login
      if (e.status === 401) limparSessao();
      toast(e.message, 'error');
      showView('auth');
    }
  }

  async function fazerLogin(email, senha) {
    const res = await api('/usuarios/login', { method: 'POST', body: { email, senha } });
    localStorage.setItem('sg_token', res.token);
    state.token = res.token;
    await bootstrap();
  }

  function iniciarAuth() {
    // abas "Entrar" / "Criar conta"
    document.querySelectorAll('.auth-tab').forEach((aba) => {
      aba.onclick = () => {
        document.querySelectorAll('.auth-tab').forEach((t) => t.classList.remove('is-active'));
        aba.classList.add('is-active');
        $('form-login').classList.toggle('hidden', aba.dataset.authTab !== 'login');
        $('form-cadastro').classList.toggle('hidden', aba.dataset.authTab !== 'cadastro');
      };
    });

    // botão "ver" da senha
    document.querySelectorAll('[data-toggle-pass]').forEach((b) => {
      b.onclick = () => {
        const campo = b.parentElement.querySelector('input');
        const mostrar = campo.type === 'password';
        campo.type = mostrar ? 'text' : 'password';
        b.textContent = mostrar ? 'ocultar' : 'ver';
      };
    });

    // 'submit' dispara com clique no botão E com Enter no teclado.
    // preventDefault() impede o navegador de recarregar a página.
    $('form-login').addEventListener('submit', async (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      const email = (f.get('email') || '').trim();
      const senha = f.get('senha') || '';
      if (!email || !senha) { toast('Preencha e-mail e senha.', 'error'); return; }
      const botao = $('btn-do-login');
      ocupado(botao, true);
      try { await fazerLogin(email, senha); }
      catch (err) { toast(err.message, 'error'); }
      finally { ocupado(botao, false); }
    });

    $('form-cadastro').addEventListener('submit', async (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      const nome = (f.get('nome') || '').trim();
      const email = (f.get('email') || '').trim();
      const senha = f.get('senha') || '';
      if (!nome || !email || !senha) { toast('Preencha todos os campos.', 'error'); return; }
      if (!/^\S+@\S+\.\S+$/.test(email)) { toast('E-mail inválido.', 'error'); return; }
      if (senha.length < 4) { toast('A senha precisa ter ao menos 4 caracteres.', 'error'); return; }
      const botao = $('btn-do-cadastro');
      ocupado(botao, true);
      try {
        await api('/usuarios/cadastro', { method: 'POST', body: { nome, email, senha } });
        toast('Conta criada! Entrando…');
        await fazerLogin(email, senha);   // já entra direto
      } catch (err) { toast(err.message, 'error'); }
      finally { ocupado(botao, false); }
    });
  }

  async function sair() {
    try { await api('/usuarios/logout', { method: 'POST', body: { token: state.token } }); }
    catch (e) { /* mesmo se o servidor falhar, saímos localmente */ }
    limparSessao();
    $('form-login').reset();
    $('form-cadastro').reset();
    showView('auth');
  }

  /* ---------- seleção de time ---------- */

  function renderTeamSelect() {
    const grid = $('team-grid');
    grid.replaceChildren();
    state.times.forEach((t) => {
      const btn = el('button', 'team-card');
      btn.type = 'button';
      btn.append(el('span', 'team-badge', iniciais(t.nome)), el('span', 'team-card-name', t.nome), el('span', 'team-card-arrow', '→'));
      btn.onclick = async () => {
        try {
          await api('/times/selecionar', { method: 'POST', body: { token: state.token, time_id: t.id } });
          await bootstrap();
        } catch (e) { toast(e.message, 'error'); }
      };
      grid.append(btn);
    });
  }

  /* ---------- dashboard: cabeçalho e início ---------- */

  async function entrarNoDashboard() {
    const u = state.usuario;
    aplicarTemaDoTime(u.time);
    $('header-name').textContent = u.nome.split(' ')[0];
    $('header-team-name').textContent = u.time;
    $('header-team-badge').textContent = iniciais(u.time);
    setAvatar(u.foto);
    irParaAba('inicio');
    await carregarInicio();
  }

  function setAvatar(url) {
    [['avatar-img', 'avatar-fallback'], ['profile-avatar-img', 'profile-avatar-fallback']].forEach(([imgId, fbId]) => {
      const img = $(imgId);
      if (url) { img.src = url; img.hidden = false; } else { img.removeAttribute('src'); img.hidden = true; }
      $(fbId).style.display = url ? 'none' : '';
    });
  }

  async function carregarInicio() {
    try { state.jogos = await api('/jogos/proximos'); }
    catch (e) { state.jogos = []; toast(e.message, 'error'); }

    const jogo = state.jogos[0];
    const placar = $('scoreboard');
    if (!jogo) {
      placar.classList.add('scoreboard-empty');
      $('score-team-mine').textContent = state.usuario.time;
      $('score-team-rival').textContent = 'sem jogos marcados';
      clearInterval(state.timer);
    } else {
      const data = lerData(jogo.data_hora);
      placar.classList.remove('scoreboard-empty');
      $('score-campeonato').textContent = jogo.campeonato || '—';
      $('score-local').textContent = jogo.local === 'casa' ? 'Em casa' : 'Fora';
      $('score-team-mine').textContent = state.usuario.time;
      $('score-team-rival').textContent = jogo.adversario;
      $('score-data').textContent = data.toLocaleDateString('pt-BR');
      $('score-hora').textContent = hora(data);
      $('score-estadio').textContent = jogo.estadio || '—';
      iniciarContagem(data);
    }

    // a previsão é do SEU estádio, então usamos o próximo jogo EM CASA
    const jogoCasa = state.jogos.find((j) => j.local === 'casa');
    carregarOcupacao(jogoCasa, 'ocupacao-home-stats', 'ocupacao-home-grid', 'detalhe-organizada', 'detalhe-recomendado', 'ocupacao-home-aviso-setores', 'ocupacao-home-mapa3d');
  }

  function iniciarContagem(data) {
    clearInterval(state.timer);
    const atualizar = () => {
      const ms = Math.max(0, data - new Date());
      const dias = Math.floor(ms / 86400000);
      const horas = Math.floor((ms / 3600000) % 24);
      const mins = Math.floor((ms / 60000) % 60);
      $('cd-dias').textContent = String(dias).padStart(2, '0');
      $('cd-horas').textContent = String(horas).padStart(2, '0');
      $('cd-min').textContent = String(mins).padStart(2, '0');
    };
    atualizar();
    state.timer = setInterval(atualizar, 30000);   // reatualiza a cada 30 s
  }

  function renderOrganizadas(container, grupos, aviso) {
    container.replaceChildren();
    if (!grupos || !grupos.length) {
      container.textContent = 'Sem referência cadastrada.';
      return;
    }

    const lista = el('ul', 'organizacoes-lista');
    grupos.forEach((grupo) => {
      const item = el('li', 'organizacao-item');
      const titulo = el('strong', '', `${grupo.nome} — ${grupo.setor}`);
      const contexto = el('span', 'organizacao-contexto', grupo.contexto);
      item.append(titulo, contexto);
      lista.append(item);
    });
    container.append(lista);
    if (aviso) container.append(el('p', 'organizacoes-aviso', aviso));
  }

  const mapasIsometricos = {
    mineirao: {
      imagem: 'img/mapa-mineirao-setores.png',
      areas: {
        laranja: [
          [[492, 210], [603, 174], [721, 151], [848, 163], [982, 195], [1080, 245], [1045, 289], [944, 253], [833, 224], [720, 218], [620, 231], [531, 268]],
          [[527, 272], [619, 240], [719, 228], [832, 235], [941, 263], [1038, 301], [1004, 354], [913, 319], [819, 296], [717, 290], [627, 303], [552, 339]],
        ],
        vermelho: [
          [[1044, 270], [1110, 307], [1172, 366], [1215, 432], [1233, 493], [1218, 552], [1185, 575], [1174, 510], [1140, 443], [1098, 382], [1030, 333]],
          [[1007, 323], [1071, 361], [1126, 419], [1166, 483], [1189, 546], [1161, 580], [1139, 520], [1101, 463], [1052, 411], [990, 375]],
        ],
        amarelo: [
          [[374, 588], [457, 614], [551, 655], [660, 686], [776, 698], [891, 686], [1004, 651], [1095, 611], [1146, 638], [1086, 690], [994, 729], [890, 758], [773, 770], [650, 755], [534, 719], [431, 674]],
          [[414, 540], [492, 567], [581, 604], [679, 633], [782, 644], [886, 632], [986, 602], [1062, 568], [1100, 598], [1020, 641], [918, 673], [808, 689], [691, 680], [578, 649], [480, 608]],
        ],
        roxo: [
          [[313, 250], [379, 207], [453, 214], [522, 257], [578, 309], [555, 354], [498, 316], [447, 286], [393, 282], [344, 314]],
          [[300, 322], [348, 300], [399, 278], [454, 289], [506, 326], [543, 365], [524, 418], [483, 382], [436, 353], [389, 357], [342, 389], [310, 433]],
          [[310, 438], [352, 396], [403, 365], [452, 364], [498, 396], [527, 439], [520, 494], [486, 461], [446, 429], [404, 431], [364, 463], [332, 504]],
          [[332, 510], [373, 470], [414, 442], [458, 438], [496, 466], [514, 508], [504, 558], [474, 531], [438, 505], [400, 509], [369, 539], [344, 573]],
        ],
      },
    },
    arena_mrv: {
      imagem: 'img/mapa-arena-mrv-setores.png',
      areas: {
        inter_norte_visitante: [[[510, 169], [580, 158], [651, 180], [716, 211], [701, 258], [649, 239], [597, 223], [546, 225], [514, 204]]],
        inter_norte_mandante: [[[305, 211], [379, 189], [456, 203], [520, 236], [556, 269], [534, 307], [482, 282], [426, 261], [367, 255], [319, 279]]],
        arcelor_norte: [[[319, 270], [370, 250], [430, 260], [489, 284], [540, 310], [559, 343], [534, 369], [483, 346], [432, 326], [380, 321], [337, 341]]],
        brahma_norte: [[[340, 332], [385, 312], [438, 323], [491, 347], [543, 369], [566, 402], [541, 431], [490, 405], [442, 384], [397, 382], [360, 401]]],
        inter_sul: [[[790, 206], [845, 223], [903, 255], [956, 296], [985, 337], [959, 367], [917, 338], [872, 307], [827, 282], [787, 268]]],
        arcelor_sul: [[[823, 268], [869, 284], [918, 316], [965, 350], [997, 390], [974, 421], [930, 390], [884, 362], [841, 337], [810, 316]]],
        brahma_sul: [[[849, 324], [894, 345], [941, 377], [987, 410], [1024, 450], [999, 482], [954, 449], [908, 421], [868, 394], [836, 369]]],
        inter_leste: [[[1057, 392], [1115, 414], [1175, 451], [1225, 500], [1245, 550], [1219, 577], [1182, 541], [1136, 509], [1091, 477], [1050, 447]]],
        arcelor_leste: [[[1052, 454], [1100, 479], [1148, 512], [1192, 548], [1224, 587], [1200, 619], [1160, 584], [1118, 554], [1074, 525], [1038, 493]]],
        brahma_leste: [[[1028, 505], [1072, 531], [1118, 562], [1160, 596], [1193, 636], [1164, 669], [1124, 637], [1084, 606], [1042, 576], [1009, 543]]],
        inter_oeste: [[[296, 477], [326, 442], [369, 419], [416, 436], [454, 468], [477, 509], [452, 545], [414, 529], [376, 513], [337, 518], [305, 540]]],
        arcelor_oeste: [[[319, 531], [354, 505], [395, 494], [436, 511], [475, 540], [506, 578], [481, 616], [444, 592], [407, 572], [371, 574], [341, 598]]],
        brahma_oeste: [[[351, 589], [381, 563], [416, 552], [453, 569], [491, 600], [523, 640], [497, 676], [462, 649], [428, 628], [397, 632], [371, 654]]],
      },
    },
  };

  function corOcupacao(percent) {
    if (percent >= 90) return '#e3342f';
    if (percent >= 80) return '#f06b32';
    if (percent >= 70) return '#f0a230';
    if (percent >= 60) return '#e2c34a';
    if (percent >= 50) return '#9eb85b';
    return '#7393a2';
  }

  function pontoDentro(x, y, poligono) {
    let dentro = false;
    for (let i = 0, j = poligono.length - 1; i < poligono.length; j = i++) {
      const [xi, yi] = poligono[i], [xj, yj] = poligono[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) dentro = !dentro;
    }
    return dentro;
  }

  function renderMapaIsometrico(container, estadio, setores) {
    if (!container) return;
    const config = mapasIsometricos[estadio];
    if (!config) { container.replaceChildren(); return; }
    const ns = 'http://www.w3.org/2000/svg';
    const mapa = document.createElement('div');
    mapa.className = 'mapa-isometrico-figura';
    const titulo = document.createElement('div');
    titulo.className = 'mapa-isometrico-titulo';
    titulo.textContent = `Ocupação estimada — ${estadio === 'mineirao' ? 'Mineirão' : 'Arena MRV'}`;
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 1536 1024');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', `Mapa isométrico da ocupação prevista no ${estadio === 'mineirao' ? 'Mineirão' : 'Arena MRV'}`);
    const imagem = document.createElementNS(ns, 'image');
    imagem.setAttribute('href', config.imagem);
    imagem.setAttribute('width', '1536');
    imagem.setAttribute('height', '1024');
    svg.append(imagem);

    const porId = Object.fromEntries(setores.map((setor) => [setor.id, setor]));
    Object.entries(config.areas).forEach(([id, poligonos]) => {
      const setor = porId[id];
      if (!setor) return;
      const cor = corOcupacao(setor.ocupacao_percent);
      poligonos.forEach((pontos) => {
        const forma = document.createElementNS(ns, 'polygon');
        forma.setAttribute('points', pontos.map((p) => p.join(',')).join(' '));
        forma.setAttribute('fill', cor);
        forma.setAttribute('fill-opacity', '.52');
        forma.setAttribute('stroke', cor);
        forma.setAttribute('stroke-width', '4');
        forma.setAttribute('stroke-opacity', '.92');
        forma.classList.add('mapa-setor-forma');
        const title = document.createElementNS(ns, 'title');
        title.textContent = `${setor.nome}: ${setor.ocupacao_percent}% — cerca de ${setor.publico_previsto.toLocaleString('pt-BR')} pessoas`;
        forma.append(title);
        svg.append(forma);

        const xs = pontos.map((p) => p[0]), ys = pontos.map((p) => p[1]);
        const hash = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        for (let y = Math.min(...ys) + 8; y < Math.max(...ys); y += 22) {
          for (let x = Math.min(...xs) + 8; x < Math.max(...xs); x += 22) {
            if (!pontoDentro(x, y, pontos) || ((x * 17 + y * 31 + hash) % 100) >= setor.ocupacao_percent) continue;
            const pessoa = document.createElementNS(ns, 'circle');
            pessoa.setAttribute('cx', x);
            pessoa.setAttribute('cy', y);
            pessoa.setAttribute('r', '4.1');
            pessoa.setAttribute('fill', cor);
            pessoa.setAttribute('fill-opacity', '.9');
            pessoa.setAttribute('stroke', '#fff');
            pessoa.setAttribute('stroke-width', '1.1');
            pessoa.classList.add('mapa-assento-ocupado');
            svg.append(pessoa);
          }
        }
      });
    });
    mapa.append(titulo, svg);
    const legenda = el('div', 'mapa-isometrico-legenda');
    legenda.append(el('span', '', 'Mais vazio'), el('i'), el('span', '', 'Mais cheio · pontos = lugares ocupados previstos'));
    container.replaceChildren(mapa, legenda);
  }

  async function carregarOcupacao(jogo, statsId, gridId, orgId, recId, noteId, mapaId) {
    const stats = $(statsId), grid = $(gridId);
    grid.replaceChildren();
    if (mapaId) $(mapaId).replaceChildren();
    $(orgId).textContent = '—';
    $(recId).textContent = '—';
    if (noteId) $(noteId).textContent = '';
    if (!jogo) { stats.textContent = 'Sem jogos em casa por enquanto.'; return; }

    stats.textContent = 'Calculando previsão…';
    try {
      const p = await api('/ocupacao/previsao', {
        method: 'POST',
        body: {
          adversario: jogo.adversario,
          campeonato: jogo.campeonato,
          fase: jogo.fase,
          data_hora: jogo.data_hora,
        },
      });
      const baixo = p.cenarios.baixo.publico.toLocaleString('pt-BR');
      const alto = p.cenarios.alto.publico.toLocaleString('pt-BR');
      stats.textContent = `vs ${jogo.adversario}: ~${p.publico_previsto.toLocaleString('pt-BR')} pessoas (faixa ${baixo}–${alto}; ${p.ocupacao_geral}% da capacidade usada)`;
      stats.title = p.metodologia || '';
      renderMapaIsometrico($(mapaId), p.estadio === 'Mineirão' ? 'mineirao' : 'arena_mrv', p.setores);
      p.setores.forEach((s) => {
        const bloco = el('div', `setor-bloco setor-${s.cor || 'cinza'}`);
        const ocupacao = `${s.ocupacao_percent}%`;
        const publico = `~${s.publico_previsto.toLocaleString('pt-BR')} pessoas`;
        bloco.append(el('div', '', s.nome), el('div', '', ocupacao), el('small', '', publico));
        bloco.title = `${s.publico_previsto.toLocaleString('pt-BR')} previstos de ${s.capacidade.toLocaleString('pt-BR')} lugares; faixa ${s.ocupacao_baixa_percent}–${s.ocupacao_alta_percent}%`;
        grid.append(bloco);
      });
      if (noteId) $(noteId).textContent = p.aviso_setores || '';
      renderOrganizadas($(orgId), p.torcidas_organizadas, p.aviso_organizacao);
      const recomendacao = p.setor_recomendado;
      $(recId).textContent = recomendacao
        ? `${recomendacao.setor} — ${recomendacao.pontuacao}/100. ${recomendacao.motivo}`
        : 'Não foi possível recomendar um setor para este jogo.';
    } catch (e) {
      stats.textContent = 'Previsão indisponível no momento';
    }
  }

  async function comprarIngresso() {
    const botao = $('btn-comprar-ingresso');
    ocupado(botao, true);
    try {
      const { link } = await api('/ingressos/comprar');
      const janela = window.open(link, '_blank', 'noopener');
      if (!janela) window.location.href = link;   // pop-up bloqueado: abre na mesma aba
    } catch (e) { toast(e.message, 'error'); }
    finally { ocupado(botao, false); }
  }

  /* ---------- aba Jogos ---------- */

  async function carregarJogos() {
    $('lista-jogos').replaceChildren(el('div', 'empty-state', 'Carregando…'));
    try {
      // Promise.all dispara as 3 requisições ao mesmo tempo e espera todas
      const [proximos, passados, favs] = await Promise.all([
        api('/jogos/proximos'), api('/jogos/passados'), api('/favoritos'),
      ]);
      state.jogos = proximos;
      state.passados = passados;
      state.favoritos = new Set(favs.map((f) => f.jogo_id));
    } catch (e) { toast(e.message, 'error'); }
    renderJogos();
  }

  function renderJogos() {
    const lista = $('lista-jogos');
    lista.replaceChildren();
    $('detalhe-jogo-ocupacao').classList.add('hidden');

    const passados = state.subtab === 'passados';
    const jogos = passados ? state.passados : state.jogos.filter((j) => j.local === state.subtab);
    if (!jogos.length) { lista.append(el('div', 'empty-state', 'Nenhum jogo por aqui ainda.')); return; }
    jogos.forEach((j) => lista.append(cartaoJogo(j, passados)));
  }

  function cartaoJogo(j, passado) {
    const data = lerData(j.data_hora);
    const card = el('div', 'game-card');

    const bloco = el('div', 'game-date-block');
    bloco.append(el('span', 'day', String(data.getDate()).padStart(2, '0')), el('span', 'month', MESES[data.getMonth()]));

    const info = el('div', 'game-info');
    const meta = el('div', 'game-meta');
    meta.append(el('span', '', hora(data)), el('span', '', j.estadio || ''), el('span', '', j.campeonato || ''));
    info.append(el('div', 'game-rival', `vs ${j.adversario}`), meta);

    card.append(bloco, info, el('span', `game-side game-side-${j.local}`, j.local === 'casa' ? 'Casa' : 'Fora'));

    if (passado) {
      const b = el('button', 'game-avaliar-btn', j.ja_avaliado ? 'Avaliado' : 'Avaliar');
      b.type = 'button';
      if (j.ja_avaliado) { b.classList.add('ja-avaliado'); b.disabled = true; }
      b.onclick = () => abrirAvaliacao(j);
      card.append(b);
    } else {
      const fav = el('button', 'game-fav-btn');
      fav.type = 'button';
      fav.innerHTML = ICONE_CORACAO;                 // SVG fixo nosso (não vem do usuário)
      fav.title = 'Favoritar jogo';
      fav.classList.toggle('is-active', state.favoritos.has(j.id));
      fav.onclick = (ev) => { ev.stopPropagation(); alternarFavorito(j, fav); };
      card.append(fav);

      if (j.local === 'casa') {                      // clique no card mostra a previsão
        card.style.cursor = 'pointer';
        card.onclick = () => mostrarPrevisaoDoJogo(j);
      }
    }
    return card;
  }

  async function mostrarPrevisaoDoJogo(j) {
    $('detalhe-jogo-ocupacao').classList.remove('hidden');
    await carregarOcupacao(j, 'ocupacao-jogo-stats', 'ocupacao-jogo-grid', 'detalhe-jogo-organizada', 'detalhe-jogo-recomendado', 'ocupacao-jogo-aviso-setores', 'ocupacao-jogo-mapa3d');
    $('detalhe-jogo-ocupacao').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  async function alternarFavorito(jogo, botao) {
    try {
      const { favoritado } = await api(`/jogos/${jogo.id}/favoritar`, { method: 'POST' });
      if (favoritado) state.favoritos.add(jogo.id); else state.favoritos.delete(jogo.id);
      botao.classList.toggle('is-active', favoritado);
      toast(favoritado ? 'Jogo favoritado!' : 'Removido dos favoritos');
    } catch (e) { toast(e.message, 'error'); }
  }

  /* ---------- avaliação (modal com estrelas) ---------- */

  function renderEstrelas() {
    const box = $('rating-stars');
    box.replaceChildren();
    for (let i = 1; i <= 5; i++) {
      const b = el('button', 'rating-star');
      b.type = 'button';
      b.innerHTML = ICONE_ESTRELA;
      b.classList.toggle('is-filled', i <= state.nota);
      b.onclick = () => { state.nota = i; renderEstrelas(); };
      box.append(b);
    }
  }

  function abrirAvaliacao(jogo) {
    state.avaliando = jogo;
    state.nota = 0;
    $('avaliacao-jogo-nome').textContent = `vs ${jogo.adversario} — ${jogo.data_hora.split(' ')[0]}`;
    $('avaliacao-comentario').value = '';
    renderEstrelas();
    $('modal-avaliacao-backdrop').classList.remove('hidden');
  }

  const fecharAvaliacao = () => $('modal-avaliacao-backdrop').classList.add('hidden');

  async function enviarAvaliacao() {
    if (!state.nota) { toast('Escolha uma nota de 1 a 5 estrelas.', 'error'); return; }
    const botao = $('avaliacao-confirm');
    ocupado(botao, true);
    try {
      await api(`/jogos/${state.avaliando.id}/avaliar`, {
        method: 'POST',
        body: { nota: state.nota, comentario: $('avaliacao-comentario').value.trim() || null },
      });
      fecharAvaliacao();
      toast('Avaliação enviada. Valeu!');
      await carregarJogos();
    } catch (e) { toast(e.message, 'error'); }
    finally { ocupado(botao, false); }
  }

  /* ---------- aba Localização (rota até o estádio) ---------- */

  function estadioDoTime() {
    return normalizar(state.usuario.time).includes('atletico')
      ? { nome: 'Arena MRV', img: 'img/arena-mrv.jpg' }
      : { nome: 'Mineirão', img: 'img/mineirao.jpg' };
  }

  function renderBanner() {
    const e = estadioDoTime();
    const img = $('img-estadio-banner');
    img.src = e.img;
    img.alt = `Foto do ${e.nome}`;
  }

  // geolocation usa callbacks; embrulhamos numa Promise para poder usar await
  function obterPosicao() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) { reject(new Error('Seu navegador não tem geolocalização.')); return; }
      navigator.geolocation.getCurrentPosition(resolve, () => reject(new Error('geo')), { timeout: 10000 });
    });
  }

  async function calcularRota() {
    const botao = $('btn-como-chegar');
    ocupado(botao, true);
    try {
      let pos;
      try { pos = await obterPosicao(); }
      catch (e) {
        // sem permissão de localização: abre o estádio no Google Maps como alternativa
        toast('Não consegui sua localização. Abrindo o estádio no Google Maps.', 'error');
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(estadioDoTime().nome)}`, '_blank', 'noopener');
        return;
      }
      const { latitude, longitude } = pos.coords;
      const r = await api('/rota', { method: 'POST', body: { latitude, longitude, modo: state.modo } });
      mostrarRota(r, latitude, longitude);
    } catch (e) { toast(e.message, 'error'); }
    finally { ocupado(botao, false); }
  }

  function mostrarRota(r, lat, lon) {
    const box = $('rota-resultado');
    box.replaceChildren();
    box.classList.remove('hidden');

    [[`${r.distancia_km} km`, 'distância'], [`${r.duracao_min} min`, 'tempo (carro)'], [r.estadio_nome, 'destino']].forEach(([v, l]) => {
      const item = el('div', 'rota-resultado-item');
      item.append(el('span', 'rota-resultado-valor', v), el('span', 'rota-resultado-label', l));
      box.append(item);
    });

    if (state.modo !== 'driving') {
      box.append(el('div', 'rota-resultado-aviso', 'Distância e tempo são estimados pela rota de carro. Para horários reais de ônibus/metrô, use o botão abaixo.'));
    }
    // Google Maps tem transporte público de verdade
    const gm = { driving: 'driving', transit: 'transit', ride: 'driving' }[state.modo];
    const link = el('a', 'link-btn', 'Abrir rota no Google Maps');
    const destinoGoogle = estadioDoTime().nome;
    link.href = `https://www.google.com/maps/dir/?api=1&origin=${lat},${lon}&destination=${encodeURIComponent(destinoGoogle)}&travelmode=${gm}`;
    link.target = '_blank';
    link.rel = 'noopener';
    box.append(link);

    desenharMapa(lat, lon, r);
  }

  function desenharMapa(lat, lon, r) {
    const div = $('rota-mapa');
    div.classList.remove('hidden');          // o Leaflet precisa da div visível para medir o tamanho
    if (!window.L) return;                    // Leaflet não carregou (sem internet): segue sem mapa
    try {
      if (state.mapa) state.mapa.remove();
      state.mapa = L.map(div);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(state.mapa);
      L.marker([lat, lon]).addTo(state.mapa).bindPopup('Você');
      L.marker([r.dest_lat, r.dest_lon]).addTo(state.mapa).bindPopup(r.estadio_nome);
      state.mapa.fitBounds([[lat, lon], [r.dest_lat, r.dest_lon]], { padding: [30, 30] });
    } catch (e) { console.error('Mapa:', e); }
  }

  /* ---------- aba Perfil ---------- */

  function itemMini(titulo, meta, extra) {
    const item = el('div', 'perfil-mini-item');
    const info = el('div', 'perfil-mini-info');
    info.append(el('div', 'perfil-mini-rival', titulo), el('div', 'perfil-mini-meta', meta));
    if (extra) info.append(extra);
    item.append(info);
    return item;
  }

  async function renderPerfil() {
    // atualiza dados do perfil
    try { state.usuario = await api('/perfil'); } catch (e) { toast(e.message, 'error'); return; }
    const u = state.usuario;
    $('profile-nome').textContent = u.nome;
    $('profile-email').textContent = u.email;
    setAvatar(u.foto);
    $('current-team-badge').textContent = iniciais(u.time);
    $('current-team-name').textContent = u.time;

    // endereço: preenche o formulário com o que já está salvo
    const f = $('form-endereco');
    ['rua', 'numero', 'bairro', 'cidade', 'estado'].forEach((c) => { f.elements[c].value = (u.endereco && u.endereco[c]) || ''; });

    // trocar de time: lista os OUTROS times
    try { state.times = await api('/times'); } catch (e) { /* mantém lista antiga */ }
    const lista = $('switch-team-list');
    lista.replaceChildren();
    state.times.filter((t) => t.nome !== u.time).forEach((t) => {
      const row = el('button', 'switch-team-row');
      row.type = 'button';
      row.append(el('span', 'badge-mini', iniciais(t.nome)), el('span', '', t.nome), el('span', '', 'Trocar'));
      row.onclick = () => trocarTime(t);
      lista.append(row);
    });

    // favoritos e avaliações
    const [favs, avs] = await Promise.all([api('/favoritos').catch(() => []), api('/avaliacoes').catch(() => [])]);
    const boxF = $('perfil-favoritos');
    boxF.replaceChildren();
    if (!favs.length) boxF.append(el('div', 'empty-state', 'Nenhum jogo favoritado.'));
    favs.forEach((j) => boxF.append(itemMini(`vs ${j.adversario}`, `${j.data_hora} · ${j.estadio || ''}`)));

    const boxA = $('perfil-avaliacoes');
    boxA.replaceChildren();
    if (!avs.length) boxA.append(el('div', 'empty-state', 'Você ainda não avaliou nenhum jogo.'));
    avs.forEach((a) => {
      const estrelas = el('div', 'perfil-mini-stars');
      for (let i = 0; i < a.nota; i++) estrelas.insertAdjacentHTML('beforeend', ICONE_ESTRELA);
      const item = itemMini(`vs ${a.adversario}`, a.data_hora, a.comentario ? el('div', 'perfil-mini-comentario', a.comentario) : null);
      item.append(estrelas);
      boxA.append(item);
    });
  }

  async function trocarTime(time) {
    const ok = await confirmar('Trocar de time?', `Você vai passar a ver jogos e ingressos do ${time.nome}.`);
    if (!ok) return;
    try {
      await api('/times/mudar', { method: 'PUT', body: { token: state.token, time_id: time.id } });
      toast(`Agora você torce pelo ${time.nome}!`);
      await bootstrap();                     // recarrega tudo com o novo time
    } catch (e) { toast(e.message, 'error'); }
  }

  async function enviarFoto(arquivo) {
    if (!arquivo) return;
    const form = new FormData();
    form.append('token', state.token);       // o back lê o token do formulário nesta rota
    form.append('foto', arquivo);
    try {
      const r = await api('/perfil/foto', { method: 'PUT', form });
      state.usuario.foto = r.foto;
      setAvatar(r.foto);
      toast('Foto atualizada!');
    } catch (e) { toast(e.message, 'error'); }
  }

  async function salvarEndereco(e) {
    e.preventDefault();
    const f = new FormData(e.target);
    const dados = Object.fromEntries(f.entries());     // {rua:'...', numero:'...', ...}
    if (!dados.rua.trim() || !dados.cidade.trim() || !dados.estado) {
      toast('Rua, cidade e UF são obrigatórios.', 'error');
      return;
    }
    const botao = e.target.querySelector('button[type="submit"]');
    ocupado(botao, true);
    try {
      await api('/perfil/localizacao', { method: 'PUT', body: { token: state.token, ...dados } });
      toast('Endereço salvo!');
    } catch (err) { toast(err.message, 'error'); }
    finally { ocupado(botao, false); }
  }

  /* ---------- ligação dos eventos e início ---------- */

  function init() {
    iniciarTema();
    iniciarAuth();

    document.querySelectorAll('.nav-item').forEach((b) => { b.onclick = () => irParaAba(b.dataset.nav); });
    $('avatar-btn').onclick = () => irParaAba('perfil');

    document.querySelectorAll('.jogos-subtab').forEach((b) => {
      b.onclick = () => {
        document.querySelectorAll('.jogos-subtab').forEach((x) => x.classList.remove('is-active'));
        b.classList.add('is-active');
        state.subtab = b.dataset.jogosSub;     // data-jogos-sub  ->  dataset.jogosSub
        renderJogos();
      };
    });

    $('btn-comprar-ingresso').onclick = comprarIngresso;

    document.querySelectorAll('.rota-modo').forEach((b) => {
      b.onclick = () => {
        document.querySelectorAll('.rota-modo').forEach((x) => x.classList.remove('is-active'));
        b.classList.add('is-active');
        state.modo = b.dataset.modo;
      };
    });
    $('btn-como-chegar').onclick = calcularRota;

    $('input-foto').onchange = (ev) => enviarFoto(ev.target.files[0]);
    $('form-endereco').addEventListener('submit', salvarEndereco);
    $('btn-logout').onclick = sair;

    $('avaliacao-cancel').onclick = fecharAvaliacao;
    $('avaliacao-confirm').onclick = enviarAvaliacao;

    bootstrap();
  }

  init();
})();
