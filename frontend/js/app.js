/* =========================================================
   STADIUM GUIDE — app.js
   SPA em JS puro, sem dependências, falando direto com a API
   Flask (mesma origem): /usuarios, /times, /perfil, /ingressos, /jogos
   ========================================================= */

(() => {
  'use strict';

  /* ---------------- estado global ---------------- */
  const state = {
    token: localStorage.getItem('sg_token') || null,
    usuario: null,   // { id, nome, email, time, foto, endereco }
    times: [],       // [{id, nome}]
    jogos: [],       // próximos jogos do time atual
  };

  const els = {};    // cache de elementos, preenchido em init()

  /* ---------------- helpers de API ---------------- */
  async function api(path, { method = 'GET', body, isForm = false, auth = false } = {}) {
    const headers = {};
    if (!isForm) headers['Content-Type'] = 'application/json';
    if (auth && state.token) headers['Authorization'] = state.token;

    const opts = { method, headers };
    if (body !== undefined) opts.body = isForm ? body : JSON.stringify(body);

    let res;
    try {
      res = await fetch(path, opts);
    } catch (e) {
      throw new Error('Não foi possível falar com o servidor. Verifique sua conexão.');
    }

    let data = null;
    try { data = await res.json(); } catch (e) { /* resposta sem corpo */ }

    if (!res.ok) {
      const msg = (data && data.erro) ? data.erro : 'Algo deu errado. Tente novamente.';
      throw new Error(msg);
    }
    return data;
  }

  const Api = {
    cadastrar: (nome, email, senha) => api('/usuarios/cadastro', { method: 'POST', body: { nome, email, senha } }),
    login: (email, senha) => api('/usuarios/login', { method: 'POST', body: { email, senha } }),
    logout: (token) => api('/usuarios/logout', { method: 'POST', body: { token } }),

    listarTimes: () => api('/times'),
    selecionarTime: (token, time_id) => api('/times/selecionar', { method: 'POST', body: { token, time_id } }),
    mudarTime: (token, time_id) => api('/times/mudar', { method: 'PUT', body: { token, time_id } }),

    perfil: () => api('/perfil', { auth: true }),
    atualizarLocalizacao: (payload) => api('/perfil/localizacao', { method: 'PUT', body: payload }),
    atualizarFoto: (formData) => api('/perfil/foto', { method: 'PUT', body: formData, isForm: true }),

    comprarIngresso: () => api('/ingressos/comprar', { auth: true }),
    proximosJogos: () => api('/jogos/proximos', { auth: true }),
  };

  /* ---------------- toasts ---------------- */
  function toast(message, type = 'info') {
    const stack = els.toastStack;
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `
      <svg viewBox="0 0 24 24"><path d="M12 8v5M12 16h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>
      <span>${escapeHtml(message)}</span>`;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      el.style.transition = '.18s ease';
      setTimeout(() => el.remove(), 200);
    }, 3600);
  }

  function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  /* ---------------- botões com spinner ---------------- */
  function setBtnLoading(btn, loading) {
    if (!btn) return;
    const spinner = btn.querySelector('.btn-spinner');
    btn.disabled = loading;
    if (spinner) spinner.hidden = !loading;
  }

  /* ---------------- controle de telas ---------------- */
  function showView(name) {
    ['loading', 'auth', 'team-select', 'dashboard'].forEach((v) => {
      document.getElementById(`view-${v}`).classList.toggle('hidden', v !== name);
    });
  }

  function showTab(name) {
    document.querySelectorAll('.tab-panel').forEach((p) => p.classList.add('hidden'));
    document.getElementById(`tab-${name}`).classList.remove('hidden');
    document.querySelectorAll('.nav-item').forEach((btn) => {
      btn.classList.toggle('is-active', btn.dataset.nav === name);
    });
    if (name === 'jogos') renderListaJogos();
  }

  /* ---------------- iniciais de time (badge) ---------------- */
  function iniciais(nome) {
    return nome
      .split(' ')
      .filter((p) => p.length > 1 || /[A-Za-zÀ-ú]/.test(p))
      .slice(0, 2)
      .map((p) => p[0])
      .join('')
      .toUpperCase();
  }

  /* ---------------- datas ---------------- */
  const MESES = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];

  function parseDataHora(str) {
    // formato vindo da API: dd/mm/yyyy HH:MM
    const [datePart, timePart] = str.split(' ');
    const [d, m, y] = datePart.split('/').map(Number);
    const [hh, mm] = timePart.split(':').map(Number);
    return new Date(y, m - 1, d, hh, mm);
  }

  /* =========================================================
     BOOTSTRAP — decide qual tela mostrar ao carregar
     ========================================================= */
  async function bootstrap() {
    showView('loading');

    if (!state.token) {
      showView('auth');
      return;
    }

    try {
      const perfil = await Api.perfil();
      guardarPerfil(perfil);

      if (!perfil.time) {
        await carregarTimesParaSelecao();
        showView('team-select');
      } else {
        await entrarNoDashboard();
      }
    } catch (e) {
      // token inválido/expirado
      encerrarSessaoLocal();
      showView('auth');
    }
  }

  function guardarPerfil(perfil) {
    state.usuario = perfil;
  }

  function encerrarSessaoLocal() {
    state.token = null;
    state.usuario = null;
    localStorage.removeItem('sg_token');
  }

  /* =========================================================
     AUTENTICAÇÃO
     ========================================================= */
  function initAuth() {
    document.querySelectorAll('[data-auth-tab]').forEach((tab) => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('[data-auth-tab]').forEach((t) => t.classList.remove('is-active'));
        tab.classList.add('is-active');
        const alvo = tab.dataset.authTab;
        els.formLogin.classList.toggle('hidden', alvo !== 'login');
        els.formCadastro.classList.toggle('hidden', alvo !== 'cadastro');
      });
    });

    document.querySelectorAll('[data-toggle-pass]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const input = btn.previousElementSibling;
        const isPass = input.type === 'password';
        input.type = isPass ? 'text' : 'password';
        btn.textContent = isPass ? 'ocultar' : 'ver';
      });
    });

    els.formLogin.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const fd = new FormData(els.formLogin);
      const email = fd.get('email').trim();
      const senha = fd.get('senha');
      const btn = els.formLogin.querySelector('button[type="submit"]');

      setBtnLoading(btn, true);
      try {
        const resultado = await Api.login(email, senha);
        state.token = resultado.token;
        localStorage.setItem('sg_token', state.token);
        toast(`Bem-vindo de volta, ${resultado.nome.split(' ')[0]}!`, 'success');
        await bootstrap();
      } catch (e) {
        toast(e.message, 'error');
      } finally {
        setBtnLoading(btn, false);
      }
    });

    els.formCadastro.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const fd = new FormData(els.formCadastro);
      const nome = fd.get('nome').trim();
      const email = fd.get('email').trim();
      const senha = fd.get('senha');
      const btn = els.formCadastro.querySelector('button[type="submit"]');

      setBtnLoading(btn, true);
      try {
        await Api.cadastrar(nome, email, senha);
        const resultado = await Api.login(email, senha);
        state.token = resultado.token;
        localStorage.setItem('sg_token', state.token);
        toast(`Conta criada! Bora escolher seu time, ${nome.split(' ')[0]}.`, 'success');
        await bootstrap();
      } catch (e) {
        toast(e.message, 'error');
      } finally {
        setBtnLoading(btn, false);
      }
    });
  }

  /* =========================================================
     SELEÇÃO DE TIME (primeiro acesso)
     ========================================================= */
  async function carregarTimesParaSelecao() {
    state.times = await Api.listarTimes();
    const grid = els.teamGrid;
    grid.innerHTML = '';

    state.times.forEach((time) => {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'team-card';
      card.innerHTML = `
        <span class="team-badge">${escapeHtml(iniciais(time.nome))}</span>
        <span>
          <span class="team-card-name">${escapeHtml(time.nome)}</span>
          <span class="team-card-hint">ver jogos e comprar ingressos</span>
        </span>
        <svg class="team-card-arrow" viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg>`;
      card.addEventListener('click', () => selecionarTime(time));
      grid.appendChild(card);
    });
  }

  async function selecionarTime(time) {
    try {
      await Api.selecionarTime(state.token, time.id);
      toast(`Fechado! Torcendo pelo ${time.nome} agora.`, 'success');
      await entrarNoDashboard();
    } catch (e) {
      toast(e.message, 'error');
    }
  }

  /* =========================================================
     DASHBOARD
     ========================================================= */
  async function entrarNoDashboard() {
    const perfil = await Api.perfil();
    guardarPerfil(perfil);

    try {
      state.jogos = await Api.proximosJogos();
    } catch (e) {
      state.jogos = [];
    }

    renderHeader();
    renderPerfil();
    renderScoreboardEPreview();
    showView('dashboard');
    showTab('inicio');
  }

  function renderHeader() {
    const u = state.usuario;
    els.headerName.textContent = u.nome.split(' ')[0];
    els.headerTeamName.textContent = u.time || '—';
    els.headerTeamBadge.textContent = u.time ? iniciais(u.time) : '--';
    setAvatar(els.avatarImg, els.avatarFallback, u.foto);
  }

  function setAvatar(imgEl, fallbackEl, foto) {
    if (foto) {
      imgEl.src = foto;
      imgEl.hidden = false;
      fallbackEl.hidden = true;
    } else {
      imgEl.hidden = true;
      fallbackEl.hidden = false;
    }
  }

  function renderPerfil() {
    const u = state.usuario;
    els.profileNome.textContent = u.nome;
    els.profileEmail.textContent = u.email;
    setAvatar(els.profileAvatarImg, els.profileAvatarFallback, u.foto);

    els.currentTeamBadge.textContent = u.time ? iniciais(u.time) : '--';
    els.currentTeamName.textContent = u.time || 'nenhum time selecionado';

    // lista de outros times para trocar
    els.switchTeamList.innerHTML = '';
    state.times
      .filter((t) => t.nome !== u.time)
      .forEach((t) => {
        const row = document.createElement('button');
        row.type = 'button';
        row.className = 'switch-team-row';
        row.innerHTML = `
          <span class="badge-mini">${escapeHtml(iniciais(t.nome))}</span>
          <span>${escapeHtml(t.nome)}</span>
          <span>trocar</span>`;
        row.addEventListener('click', () => confirmarTrocaDeTime(t));
        els.switchTeamList.appendChild(row);
      });

    // endereço
    const end = u.endereco || {};
    const form = els.formEndereco;
    form.rua.value = end.rua || '';
    form.numero.value = end.numero || '';
    form.bairro.value = end.bairro || '';
    form.cidade.value = end.cidade || '';
    form.estado.value = end.estado || '';
  }

  function confirmarTrocaDeTime(time) {
    abrirModal({
      titulo: 'Trocar de time?',
      texto: `Você vai deixar de ver os jogos e ingressos do ${state.usuario.time} e passar a acompanhar o ${time.nome}.`,
      onConfirm: async () => {
        try {
          await Api.mudarTime(state.token, time.id);
          toast(`Agora você torce pelo ${time.nome}!`, 'success');
          await entrarNoDashboard();
        } catch (e) {
          toast(e.message, 'error');
        }
      },
    });
  }

  /* -------- placar (próximo jogo) + prévia -------- */
  let countdownTimer = null;

  function renderScoreboardEPreview() {
    const board = els.scoreboard;
    const jogos = state.jogos;

    if (!jogos.length) {
      board.classList.add('scoreboard-empty');
      els.scoreCampeonato.textContent = 'sem jogos marcados';
      els.scoreLocal.textContent = '—';
      els.scoreTeamMine.textContent = state.usuario.time || 'seu time';
      els.scoreTeamRival.textContent = '?';
      els.scoreData.textContent = '--/--/----';
      els.scoreHora.textContent = '--:--';
      els.scoreEstadio.textContent = '—';
      setCountdown(null);
      els.previewJogos.innerHTML = `<div class="empty-state">Nenhum jogo por enquanto. Volta aqui em breve!</div>`;
      return;
    }

    board.classList.remove('scoreboard-empty');
    const proximo = jogos[0];
    els.scoreCampeonato.textContent = proximo.campeonato || 'Amistoso';
    els.scoreLocal.textContent = proximo.local === 'casa' ? 'Mandante' : 'Visitante';
    els.scoreTeamMine.textContent = state.usuario.time;
    els.scoreTeamRival.textContent = proximo.adversario;

    const [dataStr, horaStr] = proximo.data_hora.split(' ');
    els.scoreData.textContent = dataStr;
    els.scoreHora.textContent = horaStr;
    els.scoreEstadio.textContent = proximo.estadio || '—';

    setCountdown(parseDataHora(proximo.data_hora));

    // prévia: do 2º ao 4º jogo (o 1º já está no placar)
    renderListaDeJogos(els.previewJogos, jogos.slice(1, 4), true);
  }

  function setCountdown(dataAlvo) {
    if (countdownTimer) clearInterval(countdownTimer);
    if (!dataAlvo) {
      els.cdDias.textContent = els.cdHoras.textContent = els.cdMin.textContent = '00';
      return;
    }
    const tick = () => {
      const diff = dataAlvo.getTime() - Date.now();
      if (diff <= 0) {
        els.cdDias.textContent = els.cdHoras.textContent = els.cdMin.textContent = '00';
        clearInterval(countdownTimer);
        return;
      }
      const totalMin = Math.floor(diff / 60000);
      const dias = Math.floor(totalMin / (60 * 24));
      const horas = Math.floor((totalMin % (60 * 24)) / 60);
      const min = totalMin % 60;
      els.cdDias.textContent = String(dias).padStart(2, '0');
      els.cdHoras.textContent = String(horas).padStart(2, '0');
      els.cdMin.textContent = String(min).padStart(2, '0');
    };
    tick();
    countdownTimer = setInterval(tick, 30000);
  }

  /* -------- lista completa de jogos -------- */
  function renderListaJogos() {
    renderListaDeJogos(els.listaJogos, state.jogos, false);
  }

  function renderListaDeJogos(container, jogos, compacto) {
    container.innerHTML = '';
    if (!jogos.length) {
      container.innerHTML = `<div class="empty-state">Nenhum jogo agendado.</div>`;
      return;
    }
    jogos.forEach((jogo) => {
      const data = parseDataHora(jogo.data_hora);
      const [, horaStr] = jogo.data_hora.split(' ');
      const isCasa = jogo.local === 'casa';

      const card = document.createElement('div');
      card.className = 'game-card';
      card.innerHTML = `
        <div class="game-date-block">
          <span class="day">${String(data.getDate()).padStart(2, '0')}</span>
          <span class="month">${MESES[data.getMonth()]}</span>
        </div>
        <div class="game-info">
          <div class="game-rival">${escapeHtml(jogo.adversario)}</div>
          <div class="game-meta">
            <span>${horaStr}</span>
            <span>·</span>
            <span>${escapeHtml(jogo.estadio || '')}</span>
            ${compacto ? '' : `<span>·</span><span>${escapeHtml(jogo.campeonato || '')}</span>`}
          </div>
        </div>
        <span class="game-side ${isCasa ? 'game-side-casa' : 'game-side-fora'}">${isCasa ? 'Casa' : 'Fora'}</span>`;
      container.appendChild(card);
    });
  }

  /* =========================================================
     INGRESSOS
     ========================================================= */
  function initIngressos() {
    els.btnComprarIngresso.addEventListener('click', async () => {
      setBtnLoading(els.btnComprarIngresso, true);
      try {
        const resultado = await Api.comprarIngresso();
        window.open(resultado.link, '_blank', 'noopener');
      } catch (e) {
        toast(e.message, 'error');
      } finally {
        setBtnLoading(els.btnComprarIngresso, false);
      }
    });
  }

  /* =========================================================
     PERFIL — foto, endereço, logout
     ========================================================= */
  function initPerfil() {
    els.avatarBtn.addEventListener('click', () => {
      showTab('perfil');
      document.querySelectorAll('.nav-item').forEach((b) => b.classList.toggle('is-active', b.dataset.nav === 'perfil'));
    });

    els.inputFoto.addEventListener('change', async () => {
      const arquivo = els.inputFoto.files[0];
      if (!arquivo) return;

      const fd = new FormData();
      fd.append('token', state.token);
      fd.append('foto', arquivo);

      try {
        const resultado = await Api.atualizarFoto(fd);
        state.usuario.foto = resultado.foto;
        renderHeader();
        renderPerfil();
        toast('Foto atualizada!', 'success');
      } catch (e) {
        toast(e.message, 'error');
      } finally {
        els.inputFoto.value = '';
      }
    });

    els.formEndereco.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const fd = new FormData(els.formEndereco);
      const payload = {
        token: state.token,
        rua: fd.get('rua').trim(),
        numero: fd.get('numero').trim(),
        bairro: fd.get('bairro').trim(),
        cidade: fd.get('cidade').trim(),
        estado: fd.get('estado'),
      };
      const btn = els.formEndereco.querySelector('button[type="submit"]');
      setBtnLoading(btn, true);
      try {
        const resultado = await Api.atualizarLocalizacao(payload);
        state.usuario.endereco = resultado.endereco;
        toast('Endereço salvo!', 'success');
      } catch (e) {
        toast(e.message, 'error');
      } finally {
        setBtnLoading(btn, false);
      }
    });

    els.btnLogout.addEventListener('click', async () => {
      try {
        await Api.logout(state.token);
      } catch (e) {
        /* mesmo se falhar no servidor, encerramos localmente */
      }
      encerrarSessaoLocal();
      toast('Até a próxima!', 'success');
      showView('auth');
      els.formLogin.reset();
    });
  }

  /* =========================================================
     NAVEGAÇÃO INFERIOR + MODAL genérico
     ========================================================= */
  function initNav() {
    document.querySelectorAll('[data-nav]').forEach((btn) => {
      btn.addEventListener('click', () => showTab(btn.dataset.nav));
    });
  }

  function abrirModal({ titulo, texto, onConfirm }) {
    els.modalTitle.textContent = titulo;
    els.modalText.textContent = texto;
    els.modalBackdrop.classList.remove('hidden');

    const fechar = () => els.modalBackdrop.classList.add('hidden');
    const confirmar = async () => { fechar(); await onConfirm(); };

    els.modalCancel.onclick = fechar;
    els.modalConfirm.onclick = confirmar;
    els.modalBackdrop.onclick = (ev) => { if (ev.target === els.modalBackdrop) fechar(); };
  }

  /* =========================================================
     INIT
     ========================================================= */
  function cacheEls() {
    els.toastStack = document.getElementById('toast-stack');

    els.formLogin = document.getElementById('form-login');
    els.formCadastro = document.getElementById('form-cadastro');

    els.teamGrid = document.getElementById('team-grid');

    els.avatarBtn = document.getElementById('avatar-btn');
    els.avatarImg = document.getElementById('avatar-img');
    els.avatarFallback = document.getElementById('avatar-fallback');
    els.headerName = document.getElementById('header-name');
    els.headerTeamName = document.getElementById('header-team-name');
    els.headerTeamBadge = document.getElementById('header-team-badge');

    els.scoreboard = document.getElementById('scoreboard');
    els.scoreCampeonato = document.getElementById('score-campeonato');
    els.scoreLocal = document.getElementById('score-local');
    els.scoreTeamMine = document.getElementById('score-team-mine');
    els.scoreTeamRival = document.getElementById('score-team-rival');
    els.scoreData = document.getElementById('score-data');
    els.scoreHora = document.getElementById('score-hora');
    els.scoreEstadio = document.getElementById('score-estadio');
    els.cdDias = document.getElementById('cd-dias');
    els.cdHoras = document.getElementById('cd-horas');
    els.cdMin = document.getElementById('cd-min');
    els.previewJogos = document.getElementById('preview-jogos');
    els.listaJogos = document.getElementById('lista-jogos');

    els.btnComprarIngresso = document.getElementById('btn-comprar-ingresso');

    els.profileAvatarImg = document.getElementById('profile-avatar-img');
    els.profileAvatarFallback = document.getElementById('profile-avatar-fallback');
    els.inputFoto = document.getElementById('input-foto');
    els.profileNome = document.getElementById('profile-nome');
    els.profileEmail = document.getElementById('profile-email');
    els.currentTeamBadge = document.getElementById('current-team-badge');
    els.currentTeamName = document.getElementById('current-team-name');
    els.switchTeamList = document.getElementById('switch-team-list');
    els.formEndereco = document.getElementById('form-endereco');
    els.btnLogout = document.getElementById('btn-logout');

    els.modalBackdrop = document.getElementById('modal-backdrop');
    els.modalTitle = document.getElementById('modal-title');
    els.modalText = document.getElementById('modal-text');
    els.modalCancel = document.getElementById('modal-cancel');
    els.modalConfirm = document.getElementById('modal-confirm');
  }

  async function init() {
    cacheEls();
    initAuth();
    initNav();
    initIngressos();
    initPerfil();

    // times ficam disponíveis também para a troca dentro do perfil
    try { state.times = await Api.listarTimes(); } catch (e) { state.times = []; }

    await bootstrap();
  }

  document.addEventListener('DOMContentLoaded', init);
})();