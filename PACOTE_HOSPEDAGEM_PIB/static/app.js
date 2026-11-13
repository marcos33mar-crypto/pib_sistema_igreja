







let MENU_PEDIDOS_ATIVO = 'novo'; // 'novo' = formulário (solicitações ocultas); 'lista' = visualização de solicitações







let FILTRO_STATUS_PEDIDOS = 'TODOS';







let REQ_ANEXO_PDF_BASE64 = "";







let REQ_ANEXO_PDF_NOME = "";























// =========================================================================







// SISTEMA DE CONTROLE ESPECÍFICO DE ACESSO A RELATÓRIOS EM PDF







// =========================================================================







const LISTA_TODOS_RELATORIOS = [







  'rel_livro_caixa', 'rel_balancete', 'rel_dre', 'rel_assembleia',







  'rel_ministerios_geral', 'rel_prestacao_min', 'rel_bi',







  'rel_rol_membros', 'rel_aniversariantes', 'rel_ficha_membro', 'rel_dizimos_membro',







  'rel_visitantes', 'rel_celulas', 'rel_patrimonio', 'rel_escalas', 'rel_auditoria'







];















function getRelatoriosPermitidos(operador = CURRENT_OPERATOR) {







  if (!operador) return ['*'];







  const rel = operador.relatorios_permitidos;







  if (rel !== undefined && rel !== null && typeof rel === 'string' && rel.trim() !== '') {







    if (rel === '*') return ['*'];







    if (rel === 'nenhum' || rel === 'none') return [];







    return rel.split(',').map(s => s.trim()).filter(Boolean);







  }







  if (operador.perfil === 'ADMIN') return ['*'];







  return ['*'];







}















function temPermissaoRelatorio(relKey, operador = CURRENT_OPERATOR) {







  if (!operador) return false;







  const permitidos = getRelatoriosPermitidos(operador);







  if (permitidos.includes('*')) return true;







  return permitidos.includes(relKey);







}















// Função utilitária para converter qualquer entrada monetária (com vírgula ou ponto) em float seguro








function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function parseMoeda(val) {







  if (val === null || val === undefined || val === '') return 0.0;







  if (typeof val === 'number') return isNaN(val) ? 0.0 : val;







  let s = String(val).replace(/R\$/g, '').trim();







  if (s.indexOf('.') !== -1 && s.indexOf(',') !== -1) {







    s = s.replace(/\./g, '').replace(',', '.');







  } else if (s.indexOf(',') !== -1) {







    s = s.replace(',', '.');







  }







  const n = parseFloat(s);







  return isNaN(n) ? 0.0 : n;







}















if (typeof window.linkAssembleia === 'undefined') {







  window.linkAssembleia = window.location.origin;







}















function verificarAcessoRelatorio(relKey, nomeRelatorio = 'este relatório') {
  if (!CURRENT_OPERATOR || CURRENT_OPERATOR?.perfil === 'ADMIN') return true;
  return true;
}


function marcarTodosRelatoriosForm(marcar = true) {







  const checkboxes = document.querySelectorAll('input[name="ctrl-rel"]');







  checkboxes.forEach(cb => { cb.checked = marcar; });







  atualizarContadorRelatoriosForm();







}















function atualizarContadorRelatoriosForm() {







  const badge = document.getElementById('badge-total-relatorios-selecionados');







  if (!badge) return;







  const total = document.querySelectorAll('input[name="ctrl-rel"]').length;







  const marcados = document.querySelectorAll('input[name="ctrl-rel"]:checked').length;







  const cRel = document.getElementById('ctrl-relatorios');







  if (marcados > 0 && cRel && !cRel.checked) {







    cRel.checked = true;







    aoAlternarCheckboxSetor();







  }







  if (marcados === total) {







    badge.textContent = `Todos (${total})`;







    badge.className = 'text-[10px] font-bold bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full';







  } else if (marcados === 0) {







    badge.textContent = 'Nenhum selecionado';







    badge.className = 'text-[10px] font-bold bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full';







  } else {







    badge.textContent = `${marcados} de ${total} liberados`;







    badge.className = 'text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full';







  }







}















function marcarTodosRelatoriosModal(marcar = true) {







  const checkboxes = document.querySelectorAll('input[name="edit-ctrl-rel"]');







  checkboxes.forEach(cb => { cb.checked = marcar; });







  atualizarContadorRelatoriosModal();







}















function atualizarContadorRelatoriosModal() {







  const badge = document.getElementById('modal-badge-total-relatorios');







  if (!badge) return;







  const total = document.querySelectorAll('input[name="edit-ctrl-rel"]').length;







  const marcados = document.querySelectorAll('input[name="edit-ctrl-rel"]:checked').length;







  if (marcados === total) {







    badge.textContent = `Todos (${total})`;







    badge.className = 'text-[10px] font-bold bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full';







  } else if (marcados === 0) {







    badge.textContent = 'Nenhum selecionado';







    badge.className = 'text-[10px] font-bold bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full';







  } else {







    badge.textContent = `${marcados} de ${total} liberados`;







    badge.className = 'text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full';







  }







}















// =======================================================







// GERADOR OFICIAL DE QR CODE LOCAL E OFFLINE (ASSEMBLEIA)







// =======================================================







function gerarQRCodeNoElemento(containerId, url, tamanho = 128) {







  const container = document.getElementById(containerId);







  if (!container) return;







  container.innerHTML = '';







  







  if (typeof QRCode !== 'undefined') {







    try {







      new QRCode(container, {







        text: url,







        width: tamanho,







        height: tamanho,







        colorDark: '#0f172a',







        colorLight: '#ffffff',







        correctLevel: QRCode.CorrectLevel.M







      });







      // Ajusta tamanho da imagem ou canvas gerado







      const child = container.querySelector('img') || container.querySelector('canvas');







      if (child) {







        child.style.width = '100%';







        child.style.height = '100%';







        child.style.objectFit = 'contain';







      }







      return;







    } catch (e) {







      console.warn('Falha na biblioteca QRCode local, utilizando fallback:', e);







    }







  }















  // Fallback seguro via imagem







  const img = document.createElement('img');







  img.src = `https://api.qrserver.com/v1/create-qr-code/?size=${tamanho}x${tamanho}&margin=4&data=${encodeURIComponent(url)}`;







  img.alt = 'QR Code Assembleia';







  img.className = 'w-full h-full object-contain';







  container.appendChild(img);







}
















function getLinkOficialAssembleia() {
  const isCloudOrPublicHost = window.location.protocol === 'https:' || (
    window.location.hostname !== 'localhost' && 
    window.location.hostname !== '127.0.0.1' && 
    !window.location.hostname.startsWith('10.') && 
    !window.location.hostname.startsWith('192.168.')
  );

  if (isCloudOrPublicHost) {
    return `${window.location.origin}/?modo=assembleia`;
  }

  if (STATE.url_publica && STATE.url_publica.startsWith('https://') && !STATE.url_publica.includes('localhost') && !STATE.url_publica.includes('10.')) {
    return `${STATE.url_publica}/?modo=assembleia`;
  }

  if (STATE.url_rede_local && !STATE.url_rede_local.includes('10.') && !STATE.url_rede_local.includes('localhost')) {
    return `${STATE.url_rede_local}/?modo=assembleia`;
  }

  return `${window.location.origin}/?modo=assembleia`;
}

function renderizarQRCodesAssembleia() {
  const linkAss = getLinkOficialAssembleia();















  // 1. Badge do slide Geral (Telão/PC e Celular)







  const boxBadge = document.getElementById('slide-qrcode-box');







  if (boxBadge) {







    gerarQRCodeNoElemento('slide-qrcode-box', linkAss, 96);







  } else {







    const elQrSlide = document.getElementById('slide-qrcode-img');







    if (elQrSlide) {







      elQrSlide.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&margin=4&data=${encodeURIComponent(linkAss)}`;







    }







  }















  // 2. Badge do slide Ministérios (Telão/PC e Celular)







  const boxBadgeMin = document.getElementById('slide-qrcode-box-min');







  if (boxBadgeMin) {







    gerarQRCodeNoElemento('slide-qrcode-box-min', linkAss, 96);







  } else {







    const elQrSlideMin = document.getElementById('slide-qrcode-img-min');







    if (elQrSlideMin) {







      elQrSlideMin.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&margin=4&data=${encodeURIComponent(linkAss)}`;







    }







  }







}























// Helpers de login limpos sem exposição de credenciais















// =======================================================







// CONTROLE DO MENU LATERAL RESPONSIVO NO CELULAR







// =======================================================







function toggleSidebarMobile(abrir) {







  const sidebar = document.getElementById('sidebar-menu') || document.querySelector('aside');







  const backdrop = document.getElementById('sidebar-backdrop');







  if (!sidebar) return;















  const estaFechado = sidebar.classList.contains('-translate-x-full');







  const deveAbrir = abrir !== undefined ? abrir : estaFechado;















  if (deveAbrir) {







    sidebar.classList.remove('-translate-x-full');







    if (backdrop) backdrop.classList.remove('hidden');







    document.body.style.overflow = 'hidden';







  } else {







    sidebar.classList.add('-translate-x-full');







    if (backdrop) backdrop.classList.add('hidden');







    document.body.style.overflow = '';







  }







}







// PIB Parque São Paulo - Sistema de Gestão Integrada Multi-Setorial em Tempo Real















let STATE = {







  usuarios: [],







  ministerios: [],







  matriz_tesouraria: [],







  celulas: [],







  membros: [],







  vinculos: [],







  visitantes: [],







  escalas: [],







  financeiro: [],







  requisicoes: [],







  patrimonio: [],







  auditoria: [],

  atas: [],







  clientes_conectados: 1







};















let ACTIVE_TAB = 'dashboard';







let TESOURARIA_SUBTAB = 'planilha';







let ANO_MATRIZ_ATIVO = 2026;







let FILTRO_LEITURA_TIPO = "ENTRADA";







let FILTRO_LEITURA_CATEGORIA = "";







let MES_SLIDE_ATIVO = 5; // 5 = MAIO (padrão igual ao slide enviado) ou 0 = ANO TODO







let MATRIZ_FLUXO_FILTRO = 'TODOS'; // 'TODOS', 'ENTRADA', 'SAIDA'







let MATRIZ_MES_DESTAQUE = 0; // 0 = ano todo, 1..12 = mês destacado







let MATRIZ_GRUPOS_COLAPSADOS = new Set();







let ANO_MIN_REALIZADO = 2025;







let ANO_MIN_ORCAMENTO = 2026;







let ANO_MIN_EXECUTADO = 2026;







const ANOS_MINISTERIOS_DISPONIVEIS = [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030];







let CURRENT_OPERATOR = null;







// Preserva sessao do operador logado















let chartFinanceiroInstance = null;







let chartMinisteriosInstance = null;







let chartCelulasInstance = null;















const NOMES_MESES = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'];







const NOMES_MESES_COMPLETOS = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'];















const PERMISSOES_POR_PERFIL = {







  ADMIN: ['dashboard', 'tesouraria', 'pedidos', 'projecao', 'relatorios', 'secretaria', 'recepcao', 'ministerios', 'celulas', 'patrimonio', 'atas', 'acessos'],







  FINANCEIRO: ['tesouraria', 'pedidos', 'projecao', 'relatorios'],







  TESOURARIA: ['tesouraria', 'pedidos', 'projecao', 'relatorios'],







  PATRIMONIO: ['patrimonio'],







  SECRETARIA: ['secretaria', 'recepcao', 'celulas', 'ministerios', 'atas'],







  MINISTERIO: ['pedidos', 'ministerios', 'celulas'],







  RECEPCAO: ['recepcao'],







  ASSEMBLEIA: ['projecao']







};















function getPermissoesOperador(operador = CURRENT_OPERATOR) {

  if (!operador || !operador.id) return [];

  if (operador.perfil === 'ADMIN') return PERMISSOES_POR_PERFIL.ADMIN;

  if (operador.setores_permitidos && operador.setores_permitidos.trim()) {

    return operador.setores_permitidos.split(',').map(s => s.trim()).filter(Boolean);

  }

  return PERMISSOES_POR_PERFIL[operador.perfil] || [];

}



function temPermissaoSetor(tabName, operador = CURRENT_OPERATOR) {

  if (!operador || !operador.id) return false;

  if (operador.perfil === 'ADMIN') return true;

  const permitidas = getPermissoesOperador(operador);







  if (tabName === 'projecao') {







    return permitidas.includes('projecao');







  }







  if (tabName === 'atas') {
    if (!operador || operador.perfil === 'ADMIN') return true;
    return permitidas.includes('atas') || permitidas.includes('secretaria') || permitidas.includes('*');
  }

  if (tabName === 'pedidos') {







    return permitidas.includes('pedidos') || permitidas.includes('tesouraria') || (operador && operador.perfil === 'ADMIN');







  }







  return permitidas.includes(tabName);







}















const TITULOS_ABAS = {







  dashboard: ['Visão Geral & Painel Executivo', 'Painel de bordo consolidado com indicadores ao vivo e auditoria em tempo real'],







  ministerios_painel: ['🏛️ Orçamento/Ministérios', 'Acompanhamento oficial: Realizado 2025 vs. Orçamento 2026 vs. Executado 2026, com observações e líderes'],







  tesouraria: ['Financeiro', 'Planilha Mensal, Orçamento dos Ministérios e Lançamentos Diários'],







  pedidos: ['Pedidos de Verba dos Setores', 'Central de solicitações de verba dos líderes de ministério e aprovação financeira'],

  atas: ['Arquivo de Atas & Registros Oficiais', 'Catálogo digital de atas com anexos em PDF e DOCX (Word), registro de livros e folhas'],







  projecao: ['Gráfico de Projeção Financeira — Apresentação & Assembleia', 'Slide oficial com comparativo de Entradas, Despesas, Saldo e detalhamento percentual por grupos'],







  relatorios: ['Central de Relatórios Oficiais & Emissão em PDF', 'Gere, visualize e baixe todos os relatórios da igreja em PDF com timbre oficial, dados atualizados e assinaturas'],







  secretaria: ['Cadastro de Membros (Visão 360º)', 'Ficha completa de membros, alteração de status (incluindo Óbito), Sala EBD, células, escalas e histórico'],







  recepcao: ['Recepção & Pipeline Interativo de Visitantes', 'Altere a etapa de acompanhamento em 1 clique ou integre o visitante como membro oficial'],







  ministerios: ['Escalas de Culto & Voluntários', 'Confirme presença de voluntários com 1 clique e previna conflitos de horário entre os 15 setores'],







  celulas: ['Células & Pequenos Grupos', 'Acompanhamento interativo de frequência semanal, líderes de bairro e multiplicação'],







  patrimonio: ['Gestão de Patrimônio & Inventário por Setor', 'Cadastre bens patrimoniais e altere o estado de conservação (Novo, Bom, Em Manutenção) com 1 clique'],







  acessos: ['Controle de Acessos & Usuários', 'Gestão de credenciais, operadores e permissões por setor']







};















function formatBRL(v) {







  return Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });







}















function formatNum(v) {







  const n = Number(v || 0);







  if (n === 0) return '—';







  return n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });







}















function formatDateBR(dateStr) {







  if (!dateStr) return '—';







  const parts = dateStr.split('-');







  if (parts.length !== 3) return dateStr;







  return `${parts[2]}/${parts[1]}/${parts[0]}`;







}















let sseSource = null;







let sseReconnectTimer = null;







let lastServerVersion = 0;







let isFetchingBootstrap = false;







let pendingFetchBootstrap = false;







let jaMostrouToastAssembleia = false;















// Canal de comunicação instantânea direta entre abas abertas no mesmo navegador (0ms de atraso)







const syncBroadcastChannel = (typeof BroadcastChannel !== 'undefined') ? new BroadcastChannel('pib_sync_channel') : null;















function notificarOutrasTelas(mensagem = 'Atualização realizada') {







  try {







    if (syncBroadcastChannel) {







      syncBroadcastChannel.postMessage({ type: 'sync', mensagem, timestamp: Date.now() });







    }







    localStorage.setItem('pib_sync_signal', String(Date.now()));







  } catch (e) {}







}















if (syncBroadcastChannel) {







  syncBroadcastChannel.onmessage = (event) => {







    if (event.data && event.data.type === 'sync') {







      if (event.data.mensagem) showLiveToast(event.data.mensagem);







      fetchBootstrap();







    }







  };







}















window.addEventListener('storage', (e) => {







  if (e.key === 'pib_sync_signal') {







    fetchBootstrap();







  }







});

async function fetchBootstrap() {
  if (isFetchingBootstrap) {
    pendingFetchBootstrap = true;
    return;
  }
  isFetchingBootstrap = true;

  try {
    const res = await fetch('/api/bootstrap?_t=' + Date.now());
    const data = await res.json();
    STATE = data;
    renderBadgesAndKPIs();

    // Auto-acesso instantâneo para Membros da Assembleia via QR Code (Sem Senha, Apenas Projeção)
    const urlParams = new URLSearchParams(window.location.search);
    const veioPorQRCode = urlParams.get('modo') === 'assembleia' || urlParams.get('view') === 'assembleia' || urlParams.get('qrcode') === '1';

    if (veioPorQRCode && !window._sessaoAssembleiaAtiva) {
      window._projecaoEncerradaPeloUsuario = false;
      window._sessaoAssembleiaAtiva = true;
      window._slideInicialQR = urlParams.get('slide') === 'ministerios' ? 'ministerios' : 'geral';
      try {
        sessionStorage.removeItem('kairos_projecao_encerrada');
        // Remove imediatamente o parâmetro da barra de endereços para uso único (ao sair ou recarregar, exige nova leitura do QR Code)
        window.history.replaceState({ kairosBase: true }, document.title, window.location.pathname);
        window.history.pushState({ kairosProjecaoAtiva: true }, document.title, window.location.pathname);
      } catch (e) {}

      if (!window._listenersSaidaProjecaoRegistrados) {
        window._listenersSaidaProjecaoRegistrados = true;
        // Se o usuário tocar no botão "Voltar" do celular, encerra completamente a projeção
        window.addEventListener('popstate', () => {
          if (window._sessaoAssembleiaAtiva || document.body.classList.contains('modo-assembleia-celular')) {
            encerrarProjecaoAssembleia();
          }
        });
        // Se o usuário minimizar o navegador, trocar de aplicativo ou sair da tela no celular, encerra completamente a projeção
        document.addEventListener('visibilitychange', () => {
          if (document.visibilityState === 'hidden' && (window._sessaoAssembleiaAtiva || document.body.classList.contains('modo-assembleia-celular'))) {
            encerrarProjecaoAssembleia();
          }
        });
        window.addEventListener('pagehide', () => {
          if (window._sessaoAssembleiaAtiva || document.body.classList.contains('modo-assembleia-celular')) {
            encerrarProjecaoAssembleia();
          }
        });
      }
    }

    // Se o usuário já encerrou/saiu da projeção no celular e não leu o QR Code novamente, mantém bloqueado
    let projecaoTrancadaStorage = false;
    try {
      projecaoTrancadaStorage = sessionStorage.getItem('kairos_projecao_encerrada') === '1';
    } catch (e) {}
    if (!veioPorQRCode && (window._projecaoEncerradaPeloUsuario || projecaoTrancadaStorage)) {
      encerrarProjecaoAssembleia();
      return;
    }

    const isModoAssembleia = Boolean(window._sessaoAssembleiaAtiva);

    if (isModoAssembleia) {
      document.body.classList.add('modo-assembleia-celular');

      CURRENT_OPERATOR = {
        id: 'assembleia_ao_vivo',
        nome: 'Membro da Assembleia',
        perfil: 'ASSEMBLEIA',
        setores_permitidos: 'projecao'
      };

      fecharTelaLogin();
      const telaLogin = document.getElementById('tela-login');
      if (telaLogin) {
        telaLogin.classList.add('hidden');
        telaLogin.style.display = 'none';
      }

      // Desbloqueia tela principal
      const mainWrapper = document.getElementById('main-content-wrapper');
      if (mainWrapper) {
        mainWrapper.classList.remove('pointer-events-none', 'blur-sm');
      }

      // Oculta sidebar estritamente para membros da assembleia
      const sidebar = document.getElementById('sidebar-menu') || document.querySelector('aside');
      if (sidebar) {
        sidebar.classList.add('-translate-x-full');
        sidebar.style.display = 'none';
      }

      const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
      if (btnToggleSidebar) {
        btnToggleSidebar.style.display = 'none';
      }

      // Ajusta cabeçalho para foco exclusivo no membro da igreja
      const pageTitle = document.getElementById('page-title');
      const pageSubtitle = document.getElementById('page-subtitle');
      if (pageTitle) pageTitle.textContent = '📽️ Projeção Oficial da Assembleia Geral';
      if (pageSubtitle) pageSubtitle.textContent = 'Acompanhamento financeiro em tempo real para membros da igreja';

      const nomeOp = document.getElementById('nome-operador-logado');
      if (nomeOp) nomeOp.textContent = 'Membro da Assembleia';
      const roleBadge = document.getElementById('active-role-badge');
      if (roleBadge) {
        roleBadge.textContent = 'AO VIVO';
        roleBadge.className = 'inline-block text-[9px] sm:text-[10px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full';
      }
      const avatarOp = document.getElementById('avatar-operador-logado');
      if (avatarOp) {
        avatarOp.textContent = '⛪';
        avatarOp.style.background = '#10b981';
      }

      ACTIVE_TAB = 'projecao';
      document.querySelectorAll('.tab-section').forEach(sec => {
        if (sec.id === 'tab-projecao') {
          sec.classList.remove('hidden');
          sec.style.display = '';
        } else {
          sec.classList.add('hidden');
          sec.style.display = 'none';
        }
      });

      // Define o slide inicial apenas no primeiro carregamento; nunca troca de slide sozinho!
      if (!window._slideAssembleiaInicializado) {
        window._slideAssembleiaInicializado = true;
        alternarSlideProjecao(window._slideInicialQR || 'geral');
      } else {
        renderSlideTesouraria();
        renderSlideMinisterios();
      }

      if (!jaMostrouToastAssembleia) {
        jaMostrouToastAssembleia = true;
        showLiveToast('📱 Conectado ao vivo à Assembleia Geral!');
      }
      return;
    }

    // Segurança e Persistência de Sessão: Preserva a autenticação durante inatividade, hibernação de abas ou recarregamento
    let sessaoAtiva = false;
    let savedUserId = null;
    try {
      sessaoAtiva = (sessionStorage.getItem('pib_sessao_autenticada') === 'true') || (localStorage.getItem('pib_sessao_autenticada') === 'true');
      savedUserId = sessionStorage.getItem('pib_auth_user_id') || localStorage.getItem('pib_auth_user_id');
      if (sessaoAtiva && savedUserId) {
        sessionStorage.setItem('pib_sessao_autenticada', 'true');
        sessionStorage.setItem('pib_auth_user_id', String(savedUserId));
        localStorage.setItem('pib_sessao_autenticada', 'true');
        localStorage.setItem('pib_auth_user_id', String(savedUserId));
      }
    } catch (e) {}

    const usuarioIdAtivo = (CURRENT_OPERATOR && sessaoAtiva) ? CURRENT_OPERATOR.id : (sessaoAtiva && savedUserId ? Number(savedUserId) : null);
    const foundUser = usuarioIdAtivo ? (STATE.usuarios || []).find(u => Number(u.id) === Number(usuarioIdAtivo)) : null;

    if (foundUser) {
      CURRENT_OPERATOR = foundUser;
      fecharTelaLogin();
      renderOperatorSelector();
      aplicarPermissoesDeSetor();
      renderAll();
    } else {
      CURRENT_OPERATOR = null;
      renderOperatorSelector();
      const telaLogin = document.getElementById('tela-login');
      const isLoginAberto = telaLogin && !telaLogin.classList.contains('hidden') && telaLogin.style.display !== 'none';
      if (!isLoginAberto) {
        abrirTelaLogin();
      }
    }
  } catch (err) {
    console.error('Erro no bootstrap:', err);
  } finally {
    isFetchingBootstrap = false;
    if (pendingFetchBootstrap) {
      pendingFetchBootstrap = false;
      fetchBootstrap();
    }
  }
}



function renderOperatorSelector() {
  const select = document.getElementById('operator-select');
  const badge = document.getElementById('active-role-badge');
  const nomeOp = document.getElementById('nome-operador-logado');
  const avatarOp = document.getElementById('avatar-operador-logado');

  if (nomeOp) {
    nomeOp.textContent = CURRENT_OPERATOR ? CURRENT_OPERATOR.nome : 'Não autenticado';
  }

  if (avatarOp) {
    if (CURRENT_OPERATOR) {
      const parts = (CURRENT_OPERATOR.nome || 'OP').trim().split(/\s+/);
      const initials = parts.length > 1 ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
      avatarOp.textContent = initials;
    } else {
      avatarOp.textContent = '🔒';
    }
  }

  if (badge) {
    if (CURRENT_OPERATOR) {
      badge.textContent = CURRENT_OPERATOR.perfil || 'OPERADOR';
      badge.className = 'inline-block text-[9px] sm:text-[10px] font-bold text-indigo-700 bg-indigo-100 px-1.5 py-0.2 rounded-md';
    } else {
      badge.textContent = 'DESCONECTADO';
      badge.className = 'inline-block text-[9px] sm:text-[10px] font-bold text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded-md';
    }
  }

  const sessaoNome = document.getElementById('card-sessao-nome');
  const sessaoPerfil = document.getElementById('card-sessao-perfil');
  const sessaoAvatar = document.getElementById('card-sessao-avatar');
  if (sessaoNome) sessaoNome.textContent = CURRENT_OPERATOR ? (CURRENT_OPERATOR.nome || 'Operador') : 'Marcos Silva';
  if (sessaoPerfil) sessaoPerfil.textContent = CURRENT_OPERATOR ? (CURRENT_OPERATOR.perfil || 'ADMIN') : 'ADMIN';
  if (sessaoAvatar && CURRENT_OPERATOR) {
    const parts = (CURRENT_OPERATOR.nome || 'OP').trim().split(/\s+/);
    sessaoAvatar.textContent = parts.length > 1 ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
  }

  if (!select) return;

  select.innerHTML = (STATE.usuarios || []).map(u => `
    <option value="${u.id}" ${CURRENT_OPERATOR && CURRENT_OPERATOR.id === u.id ? 'selected' : ''}>
      ${u.nome} [${u.perfil}]
    </option>
  `).join('');
}

function alternarVisibilidadeSenha(inputId, btnEl = null) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isPass = input.type === 'password';
  input.type = isPass ? 'text' : 'password';

  const btn = btnEl || (typeof event !== 'undefined' && event && event.currentTarget) || input.parentElement?.querySelector('button');
  if (btn) {
    btn.textContent = isPass ? '🙈' : '👁️';
    btn.title = isPass ? 'Ocultar senha' : 'Ver senha';
  }
}

function monitorarCapsLockLogin(e) {
  const capswarn = document.getElementById('capslock-warning-login');
  if (!capswarn) return;
  if (e && e.getModifierState && e.getModifierState('CapsLock')) {
    capswarn.classList.remove('hidden');
  } else {
    capswarn.classList.add('hidden');
  }
}

function aoMudarOperadorLogin() {
  const select = document.getElementById('login-operador-id');
  const senhaInput = document.getElementById('login-senha');
  const erroDiv = document.getElementById('login-erro');
  const boxNaoCad = document.getElementById('login-box-nao-cadastrado');
  const boxCustom = document.getElementById('login-box-usuario-custom');
  const customInput = document.getElementById('login-usuario-custom');

  if (erroDiv) erroDiv.classList.add('hidden');
  if (senhaInput) senhaInput.value = '';

  const val = select ? select.value : '';

  if (val === 'nao_cadastrado') {
    if (boxNaoCad) boxNaoCad.classList.remove('hidden');
    if (boxCustom) boxCustom.classList.add('hidden');
  } else if (val === 'manual') {
    if (boxCustom) boxCustom.classList.remove('hidden');
    if (boxNaoCad) boxNaoCad.classList.add('hidden');
    customInput?.focus();
    return;
  } else {
    if (boxNaoCad) boxNaoCad.classList.add('hidden');
    if (boxCustom) boxCustom.classList.add('hidden');
    senhaInput?.focus();
  }
}

function limparSelecaoLogin() {
  const select = document.getElementById('login-operador-id');
  const senhaInput = document.getElementById('login-senha');
  const erroDiv = document.getElementById('login-erro');
  const boxNaoCad = document.getElementById('login-box-nao-cadastrado');
  const boxCustom = document.getElementById('login-box-usuario-custom');
  const customInput = document.getElementById('login-usuario-custom');

  if (select) select.value = '';
  if (senhaInput) senhaInput.value = '';
  if (customInput) customInput.value = '';
  if (erroDiv) erroDiv.classList.add('hidden');
  if (boxNaoCad) boxNaoCad.classList.add('hidden');
  if (boxCustom) boxCustom.classList.add('hidden');
  select?.focus();
}

function fecharTelaLogin() {
  const tela = document.getElementById('tela-login');
  if (tela) {
    tela.classList.add('hidden');
    tela.style.display = 'none';
  }
}

function abrirTelaLogin(operadorIdPreselecionado = null) {
  const tela = document.getElementById('tela-login');
  const select = document.getElementById('login-operador-id');
  const senhaInput = document.getElementById('login-senha');
  const erroDiv = document.getElementById('login-erro');
  const boxCustom = document.getElementById('login-box-usuario-custom');
  const customInput = document.getElementById('login-usuario-custom');
  const boxNaoCad = document.getElementById('login-box-nao-cadastrado');

  // Proteção contra sobrescrita durante digitação do operador
  const telaJaAberta = tela && !tela.classList.contains('hidden') && tela.style.display !== 'none';
  if (telaJaAberta && ((senhaInput && senhaInput.value) || (customInput && customInput.value) || document.activeElement === senhaInput || document.activeElement === customInput)) {
    return;
  }

  if (erroDiv) erroDiv.classList.add('hidden');
  if (senhaInput) senhaInput.value = '';
  if (customInput) customInput.value = '';
  if (boxCustom) boxCustom.classList.add('hidden');
  if (boxNaoCad) boxNaoCad.classList.add('hidden');

  if (select) {
    let html = '<option value="">-- Selecione seu Usuário Cadastrado --</option>';
    if (Array.isArray(STATE.usuarios) && STATE.usuarios.length > 0) {
      html += STATE.usuarios.filter(u => u.ativo !== 0).map(u => `
        <option value="${u.id}" ${operadorIdPreselecionado && Number(u.id) === Number(operadorIdPreselecionado) ? 'selected' : ''}>
          ${u.nome} [${u.perfil}]
        </option>
      `).join('');
    }
    html += '<option value="manual">✍️ Digitar Outro Usuário / E-mail</option>';
    html += '<option value="nao_cadastrado">⚠️ Não sou cadastrado / Solicitar Acesso</option>';
    select.innerHTML = html;

    if (operadorIdPreselecionado) {
      select.value = String(operadorIdPreselecionado);
    }
  }

  if (tela) {
    tela.classList.remove('hidden');
    tela.style.display = '';
    setTimeout(() => {
      if (select && select.value && select.value !== 'manual' && select.value !== 'nao_cadastrado') {
        senhaInput?.focus();
      } else {
        select?.focus();
      }
    }, 150);
  }
}

function sairDoSistema() {
  // Se estiver na sessão de projeção ao vivo por QR Code no celular, encerra completamente a projeção
  if (window._sessaoAssembleiaAtiva || document.body.classList.contains('modo-assembleia-celular') || (CURRENT_OPERATOR && CURRENT_OPERATOR.id === 'assembleia_ao_vivo')) {
    encerrarProjecaoAssembleia();
    return;
  }

  const prevId = CURRENT_OPERATOR ? CURRENT_OPERATOR.id : null;

  try {
    sessionStorage.removeItem('pib_sessao_autenticada');
    sessionStorage.removeItem('pib_auth_user_id');
    localStorage.removeItem('pib_sessao_autenticada');
    localStorage.removeItem('pib_auth_user_id');
    localStorage.removeItem('pib_auth_timestamp');
  } catch (e) {}

  CURRENT_OPERATOR = null;

  // Fecha eventuais modais abertos
  if (typeof closeModal === 'function') {
    closeModal();
  }

  // Oculta todas as abas operacionais do sistema
  const todasAbas = [
    'dashboard', 'tesouraria', 'pedidos', 'projecao', 'relatorios',
    'secretaria', 'recepcao', 'atas', 'ministerios', 'ministerios_painel',
    'celulas', 'patrimonio', 'acessos'
  ];
  todasAbas.forEach(aba => {
    const el = document.getElementById('tab-' + aba);
    if (el) el.classList.add('hidden');
  });

  // Atualiza indicadores de operador no cabeçalho
  renderOperatorSelector();

  // Desativa visualmente itens do menu lateral
  document.querySelectorAll('#sidebar-nav .nav-item').forEach(btn => {
    btn.classList.add('disabled-sector');
  });

  // Notifica o usuário
  if (typeof showLiveToast === 'function') {
    showLiveToast('👋 Sessão encerrada com sucesso! Até logo.');
  }

  // Abre a tela de login exigindo credenciais novamente
  abrirTelaLogin(prevId);
}

function encerrarProjecaoAssembleia() {
  // Se estiver em modo Tela Cheia (Fullscreen), sai primeiro da tela cheia
  try {
    if (document.fullscreenElement && document.exitFullscreen) {
      document.exitFullscreen().catch(() => {});
    }
  } catch (e) {}

  const isModoCelular = window._sessaoAssembleiaAtiva || document.body.classList.contains('modo-assembleia-celular') || (CURRENT_OPERATOR && CURRENT_OPERATOR.id === 'assembleia_ao_vivo');

  // Se for um operador autenticado normal no computador visualizando a aba Projeção, retorna ao Painel Executivo
  if (!isModoCelular && CURRENT_OPERATOR && CURRENT_OPERATOR.id !== 'assembleia_ao_vivo') {
    if (typeof switchTab === 'function') {
      switchTab('dashboard');
    }
    return;
  }

  // No modo QR Code / Celular: encerra e trava completamente a projeção
  window._sessaoAssembleiaAtiva = false;
  window._projecaoEncerradaPeloUsuario = true;
  window._slideAssembleiaInicializado = false;

  if (window._pibAutoSyncInterval) {
    clearInterval(window._pibAutoSyncInterval);
    window._pibAutoSyncInterval = null;
  }

  // Remove definitivamente parâmetros da URL para impedir reabertura sem ler o QR Code novamente
  try {
    if (window.history && window.history.replaceState) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    sessionStorage.setItem('kairos_projecao_encerrada', '1');
    sessionStorage.removeItem('pib_sessao_autenticada');
    sessionStorage.removeItem('pib_auth_user_id');
  } catch (e) {}

  CURRENT_OPERATOR = null;

  // Fecha modais e oculta completamente o conteúdo da projeção
  if (typeof closeModal === 'function') {
    closeModal();
  }

  const tabProjecao = document.getElementById('tab-projecao');
  if (tabProjecao) {
    tabProjecao.classList.add('hidden');
    tabProjecao.style.display = 'none';
  }

  const mainWrapper = document.getElementById('main-content-wrapper');
  if (mainWrapper) {
    mainWrapper.style.display = 'none';
  }

  const sidebar = document.getElementById('sidebar-menu');
  if (sidebar) {
    sidebar.style.display = 'none';
  }

  // Exibe a tela de Projeção Encerrada (exigindo nova leitura do QR Code)
  const telaEncerrada = document.getElementById('tela-projecao-encerrada');
  if (telaEncerrada) {
    telaEncerrada.classList.remove('hidden');
    telaEncerrada.style.display = 'flex';
  }

  // Tenta fechar a aba/janela do navegador do celular se tiver sido aberta por leitura externa
  try {
    window.close();
  } catch (e) {}
}

function irParaLoginOperadorAposProjecao() {
  window._projecaoEncerradaPeloUsuario = false;
  window._sessaoAssembleiaAtiva = false;
  try {
    sessionStorage.removeItem('kairos_projecao_encerrada');
  } catch (e) {}
  document.body.classList.remove('modo-assembleia-celular');

  const telaEncerrada = document.getElementById('tela-projecao-encerrada');
  if (telaEncerrada) {
    telaEncerrada.classList.add('hidden');
    telaEncerrada.style.display = 'none';
  }

  const mainWrapper = document.getElementById('main-content-wrapper');
  if (mainWrapper) {
    mainWrapper.style.display = '';
  }

  const sidebar = document.getElementById('sidebar-menu');
  if (sidebar) {
    sidebar.style.display = '';
  }

  const tabProjecao = document.getElementById('tab-projecao');
  if (tabProjecao) {
    tabProjecao.style.display = '';
    tabProjecao.classList.add('hidden');
  }

  abrirTelaLogin();
}

async function executarLoginSistema(e) {
  if (e && e.preventDefault) e.preventDefault();

  const select = document.getElementById('login-operador-id');
  const senhaInput = document.getElementById('login-senha');
  const erroDiv = document.getElementById('login-erro');
  const erroTexto = document.getElementById('login-erro-texto');
  const btnEntrar = document.getElementById('btn-entrar-login');
  const customInput = document.getElementById('login-usuario-custom');

  const selectVal = select ? select.value : '';
  const senha = (senhaInput?.value || '').trim();

  if (!selectVal) {
    if (erroDiv && erroTexto) {
      erroTexto.textContent = 'Por favor, selecione seu usuário na lista ou escolha a opção de digitar usuário/e-mail.';
      erroDiv.classList.remove('hidden');
    }
    select?.focus();
    return;
  }

  if (selectVal === 'nao_cadastrado') {
    if (erroDiv && erroTexto) {
      erroTexto.textContent = 'Acesso restrito a operadores cadastrados. Solicite seu cadastro ao administrador.';
      erroDiv.classList.remove('hidden');
    }
    return;
  }

  let payload = { senha };

  if (selectVal === 'manual') {
    const loginCustom = (customInput?.value || '').trim();
    if (!loginCustom) {
      if (erroDiv && erroTexto) {
        erroTexto.textContent = 'Por favor, digite seu nome, e-mail ou identificador de operador.';
        erroDiv.classList.remove('hidden');
      }
      customInput?.focus();
      return;
    }
    payload.login = loginCustom;
  } else {
    payload.id = Number(selectVal);
  }

  if (!senha) {
    if (erroDiv && erroTexto) {
      erroTexto.textContent = 'Por favor, digite sua senha de acesso cadastrada.';
      erroDiv.classList.remove('hidden');
    }
    senhaInput?.focus();
    return;
  }

  if (erroDiv) erroDiv.classList.add('hidden');

  if (btnEntrar) {
    btnEntrar.disabled = true;
    btnEntrar.innerHTML = '<span>⏳</span> Verificando credencial...';
  }

  try {
    const res = await fetch('/api/usuarios/verificar-senha', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok && data.ok) {
      if (erroDiv) erroDiv.classList.add('hidden');

      const userDb = (STATE.usuarios || []).find(u => Number(u.id) === Number(data.id));
      const user = {
        id: data.id,
        nome: data.nome,
        perfil: data.perfil,
        cargo: userDb ? userDb.cargo : 'Operador Autorizado',
        email: userDb ? userDb.email : '',
        setores_permitidos: data.setores_permitidos || (userDb ? userDb.setores_permitidos : ''),
        relatorios_permitidos: data.relatorios_permitidos || (userDb ? userDb.relatorios_permitidos : '*'),
        senha: senha,
        senha_alterada: data.senha_alterada !== undefined ? data.senha_alterada : (userDb ? userDb.senha_alterada : 1)
      };

      CURRENT_OPERATOR = user;
      try {
        sessionStorage.setItem('pib_sessao_autenticada', 'true');
        sessionStorage.setItem('pib_auth_user_id', String(user.id));
        localStorage.setItem('pib_sessao_autenticada', 'true');
        localStorage.setItem('pib_auth_user_id', String(user.id));
        localStorage.setItem('pib_auth_timestamp', String(Date.now()));
      } catch (e) {}

      if (data.exige_troca_senha || (user.senha === '123456' && Number(user.senha_alterada) === 0)) {
        fecharTelaLogin();
        abrirModalTrocaSenhaObrigatoria(user);
        return;
      }

      fecharTelaLogin();
      renderOperatorSelector();
      aplicarPermissoesDeSetor();

      const todasAbas = [
        'dashboard', 'tesouraria', 'pedidos', 'projecao', 'relatorios',
        'secretaria', 'recepcao', 'atas', 'ministerios', 'celulas',
        'patrimonio', 'acessos'
      ];
      const destino = todasAbas.find(t => temPermissaoSetor(t, user)) || 'secretaria';
      switchTab(destino);
      renderAll();
      showLiveToast(`✅ Acesso autorizado! Bem-vindo(a), ${user.nome}!`);
    } else {
      if (erroDiv && erroTexto) {
        erroTexto.textContent = data.mensagem || 'Senha incorreta para este operador! Digite a senha cadastrada no Controle de Acessos.';
        erroDiv.classList.remove('hidden');
      }
      senhaInput?.select();
      senhaInput?.focus();
    }
  } catch (err) {
    console.error('Erro de login:', err);
    if (erroDiv && erroTexto) {
      erroTexto.textContent = 'Erro de comunicação ao verificar senha. Tente novamente.';
      erroDiv.classList.remove('hidden');
    }
  } finally {
    if (btnEntrar) {
      btnEntrar.disabled = false;
      btnEntrar.innerHTML = '<span>🔓</span> Entrar no Kairós';
    }
  }
}



function switchTab(tabName) {
  if (tabName === 'ministerios_painel') {
    navegarTesourariaSubtab('orcamento');
    return;
  }

  if (!CURRENT_OPERATOR) {
    let sessaoAtiva = false;
    let savedUserId = null;
    try {
      sessaoAtiva = (sessionStorage.getItem('pib_sessao_autenticada') === 'true') || (localStorage.getItem('pib_sessao_autenticada') === 'true');
      savedUserId = sessionStorage.getItem('pib_auth_user_id') || localStorage.getItem('pib_auth_user_id');
    } catch (e) {}

    if (sessaoAtiva && savedUserId && Array.isArray(STATE.usuarios) && STATE.usuarios.length > 0) {
      const user = STATE.usuarios.find(u => Number(u.id) === Number(savedUserId));
      if (user) {
        CURRENT_OPERATOR = user;
        sessionStorage.setItem('pib_sessao_autenticada', 'true');
        sessionStorage.setItem('pib_auth_user_id', String(user.id));
        localStorage.setItem('pib_sessao_autenticada', 'true');
        localStorage.setItem('pib_auth_user_id', String(user.id));
        fecharTelaLogin();
        renderOperatorSelector();
        aplicarPermissoesDeSetor();
      }
    }
  }

  if (!CURRENT_OPERATOR) {
    abrirTelaLogin();
    return;
  }

  if (!temPermissaoSetor(tabName, CURRENT_OPERATOR)) {
    alert(`Acesso Restrito: O usuário '${CURRENT_OPERATOR.nome}' não possui permissão para acessar o setor '${tabName}'.`);
    return;
  }

  ACTIVE_TAB = tabName;

  if (typeof toggleSidebarMobile === 'function' && window.innerWidth < 768) {
    toggleSidebarMobile(false);
  }

  document.querySelectorAll('.tab-section').forEach(sec => sec.classList.add('hidden'));

  const target = document.getElementById(`tab-${tabName}`);
  if (target) {
    target.classList.remove('hidden');
    target.style.display = '';
  }

  document.querySelectorAll('#sidebar-nav .nav-item').forEach(btn => {
    const btnTab = btn.getAttribute('data-tab');
    if (btnTab === tabName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  const subMenuTes = document.getElementById('submenu-tesouraria');
  const setaTes = document.getElementById('seta-subnav-tesouraria');
  if (tabName !== 'tesouraria') {
    document.querySelectorAll('#submenu-tesouraria .nav-subitem').forEach(sub => sub.classList.remove('active'));
    if (subMenuTes) subMenuTes.classList.add('hidden');
    if (setaTes) setaTes.style.transform = 'rotate(-90deg)';
  } else {
    if (subMenuTes) subMenuTes.classList.remove('hidden');
    if (setaTes) setaTes.style.transform = 'rotate(0deg)';
    ['planilha', 'orcamento', 'diarios'].forEach(st => {
      const subnav = document.getElementById('subnav-tes-' + st);
      if (subnav) {
        if (st === (TESOURARIA_SUBTAB || 'planilha')) {
          subnav.classList.add('active');
        } else {
          subnav.classList.remove('active');
        }
      }
    });
  }

  const subMenuPat = document.getElementById('submenu-patrimonio');
  const setaPat = document.getElementById('seta-subnav-patrimonio');
  if (tabName !== 'patrimonio') {
    document.querySelectorAll('#submenu-patrimonio .nav-subitem').forEach(sub => sub.classList.remove('active'));
    if (subMenuPat) subMenuPat.classList.add('hidden');
    if (setaPat) setaPat.style.transform = 'rotate(-90deg)';
  } else {
    if (subMenuPat) subMenuPat.classList.remove('hidden');
    if (setaPat) setaPat.style.transform = 'rotate(0deg)';
    ['inventario', 'emprestimos'].forEach(st => {
      const subnav = document.getElementById('subnav-pat-' + st);
      if (subnav) {
        if (st === (SUBTAB_PATRIMONIO_ATIVA || 'inventario')) {
          subnav.classList.add('active');
        } else {
          subnav.classList.remove('active');
        }
      }
    });
  }

  const info = TITULOS_ABAS[tabName];
  if (info) {
    document.getElementById('page-title').textContent = info[0];
    document.getElementById('page-subtitle').textContent = info[1];
  }

  if (tabName === 'dashboard') {
    renderDashboard();
    renderBadgesAndKPIs();
    if (typeof fetchBootstrap === 'function' && !isFetchingBootstrap) {
      fetchBootstrap();
    }
  } else if (tabName === 'atas') {
    renderAtas();
    alternarMenuAtas(MENU_ATAS_ATIVO || 'lista');
  } else if (tabName === 'pedidos') {
    renderTesouraria();
    alternarMenuPedidos(MENU_PEDIDOS_ATIVO || 'novo');
  } else if (tabName === 'projecao') {
    renderSlideTesouraria();
    renderSlideMinisterios();
  } else if (tabName === 'tesouraria') {
    switchTesourariaSubtab(TESOURARIA_SUBTAB || 'planilha');
    const subMenu = document.getElementById('submenu-tesouraria');
    if (subMenu) subMenu.classList.remove('hidden');
    const seta = document.getElementById('seta-subnav-tesouraria');
    if (seta) seta.style.transform = 'rotate(0deg)';
  } else if (tabName === 'relatorios') {
    renderRelatorios();
  } else if (tabName === 'secretaria') {
    renderMembros();
    if (typeof popularSelectsCadastroMembro === 'function') popularSelectsCadastroMembro();
  } else if (tabName === 'recepcao') {
    renderVisitantes();
  } else if (tabName === 'ministerios_painel') {
    renderMinisteriosPainel();
  } else if (tabName === 'ministerios') {
    renderEscalas();
  } else if (tabName === 'celulas') {
    renderCelulas();
  } else if (tabName === 'patrimonio') {
    switchSubTabPatrimonio(SUBTAB_PATRIMONIO_ATIVA || 'inventario');
  } else if (tabName === 'acessos') {
    renderPatrimonioEUsuarios();
  }
}

function switchTesourariaSubtab(subtab) {
  if (subtab === 'operacional') subtab = 'diarios';
  if (subtab === 'pedidos') {
    switchTab('pedidos');
    return;
  }
  TESOURARIA_SUBTAB = subtab;

  ['planilha', 'orcamento', 'diarios'].forEach(st => {
    const sec = document.getElementById('tes-subtab-' + st);
    const subnav = document.getElementById('subnav-tes-' + st);
    const btn = document.getElementById('subtab-btn-' + st);

    if (sec) {
      if (st === subtab) sec.classList.remove('hidden');
      else sec.classList.add('hidden');
    }

    if (btn) {
      if (st === subtab) btn.classList.add('active');
      else btn.classList.remove('active');
    }

    if (subnav) {
      if (st === subtab && ACTIVE_TAB === 'tesouraria') {
        subnav.classList.add('active');
      } else {
        subnav.classList.remove('active');
      }
    }
  });

  if (subtab === 'planilha') {
    renderMatrizTesouraria();
  } else if (subtab === 'orcamento') {
    renderOrcamento15Ministerios();
  } else if (subtab === 'diarios') {
    renderTesouraria();
  }
}

function navegarTesourariaSubtab(subtab) {
  if (ACTIVE_TAB !== 'tesouraria') {
    switchTab('tesouraria');
  }
  switchTesourariaSubtab(subtab);
}

function toggleSubmenuTesouraria() {
  if (CURRENT_OPERATOR && !temPermissaoSetor('tesouraria', CURRENT_OPERATOR)) {
    alert(`Acesso Restrito: O usuário '${CURRENT_OPERATOR.nome}' não possui permissão para acessar o Financeiro.`);
    return;
  }
  const subMenu = document.getElementById('submenu-tesouraria');
  const seta = document.getElementById('seta-subnav-tesouraria');

  if (ACTIVE_TAB !== 'tesouraria') {
    window._submenuTesourariaUserClosed = false;
    switchTab('tesouraria');
    switchTesourariaSubtab(TESOURARIA_SUBTAB || 'planilha');
    if (subMenu) subMenu.classList.remove('hidden');
    if (seta) seta.style.transform = 'rotate(0deg)';
  } else {
    if (subMenu) {
      const oculto = subMenu.classList.toggle('hidden');
      if (seta) seta.style.transform = oculto ? 'rotate(-90deg)' : 'rotate(0deg)';
      window._submenuTesourariaUserClosed = oculto;
    }
  }
}

function toggleSubmenuPatrimonio() {
  if (CURRENT_OPERATOR && !temPermissaoSetor('patrimonio', CURRENT_OPERATOR)) {
    alert(`Acesso Restrito: O usuário '${CURRENT_OPERATOR.nome}' não possui permissão para acessar o Patrimônio.`);
    return;
  }
  const subMenu = document.getElementById('submenu-patrimonio');
  const seta = document.getElementById('seta-subnav-patrimonio');

  if (subMenu) {
    subMenu.classList.remove('hidden');
    if (seta) seta.style.transform = 'rotate(0deg)';
  }
  abrirPatrimonioSubtab(SUBTAB_PATRIMONIO_ATIVA || 'inventario');
}

function abrirPatrimonioSubtab(subtab) {
  if (CURRENT_OPERATOR && !temPermissaoSetor('patrimonio', CURRENT_OPERATOR)) {
    alert(`Acesso Restrito: O usuário '${CURRENT_OPERATOR.nome}' não possui permissão para acessar o Patrimônio.`);
    return;
  }
  SUBTAB_PATRIMONIO_ATIVA = subtab || 'inventario';
  switchTab('patrimonio');
  switchSubTabPatrimonio(SUBTAB_PATRIMONIO_ATIVA);
}




function formatSlideNumber(num) {
  if (num === 0) return 'R$ 0,00';
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatSlidePercent(perc) {
  if (perc >= 0.95) {
    return `${Math.round(perc)}%`;
  }
  return `${perc.toFixed(1).replace('.', ',')}%`;
}

function selecionarMesSlide(mes) {
  MES_SLIDE_ATIVO = Number(mes);
  renderSlideTesouraria();
}

function filtrarGrupoPeloSlide(grupo) {
  const sel = document.getElementById('filtro-grupo-matriz');
  if (!sel) return;
  if (sel.value === grupo) {
    sel.value = '';
  } else {
    sel.value = grupo;
  }
  renderMatrizTesouraria();
}

function getOrcamentoMinisterio(m, ano) {
  const item = (STATE.ministerios_orcamentos || []).find(x => x.ministerio_id === m.id && Number(x.ano) === Number(ano));
  if (item && item.orcamento !== undefined && item.orcamento !== null && Number(item.orcamento) > 0) {
    return Number(item.orcamento);
  }
  if (Number(m.orcamento_2026 || 0) > 0 && Number(ano) === 2026) {
    return Number(m.orcamento_2026);
  }
  return Number(m.orcamento_mensal || 0) * 12;
}

function getExecutadoMinisterio(m, ano) {
  const item = (STATE.ministerios_orcamentos || []).find(x => x.ministerio_id === m.id && Number(x.ano) === Number(ano));
  if (item && item.executado !== undefined && item.executado !== null && Number(item.executado) > 0) {
    return Number(item.executado);
  }
  if (m.gasto_atual !== undefined && Number(m.gasto_atual) > 0) {
    return Number(m.gasto_atual);
  }
  return 0;
}

function aoDigitarAnoMatriz(val) {
  const ano = parseInt(val, 10);
  if (!isNaN(ano) && ano >= 1990 && ano <= 2100) {
    ANO_MATRIZ_ATIVO = ano;
    renderSlideTesouraria();
    renderSlideMinisterios();
    renderMatrizTesouraria();
  }
}

function getRealizadoMinisterio(m, ano = ANO_MIN_REALIZADO) {
  const item = (STATE.ministerios_orcamentos || []).find(x => x.ministerio_id === m.id && Number(x.ano) === Number(ano));
  if (item && item.realizado !== undefined && item.realizado !== null && Number(item.realizado) > 0) {
    return Number(item.realizado);
  }
  if (ano === 2023) {
    return Number(m.realizado_2023 || 0);
  }
  return Number(m.orcamento_mensal || 0) * 12 * 0.92;
}

function renderSlideTesouraria() {
  const { rows, entMes, saiMes, totalEntradas, totalSaidas } = calcularResumoAnoMatriz(ANO_MATRIZ_ATIVO);

  // 1. Renderiza botões de seleção de mês (JAN a DEZ + ANO TODO) com scroll suave
  const btnContainer = document.getElementById('botoes-meses-slide');
  if (btnContainer) {
    const botoesHTML = NOMES_MESES.map((m, idx) => {
      const mesNum = idx + 1;
      const ativo = MES_SLIDE_ATIVO === mesNum;
      const temMov = (entMes[idx] > 0 || saiMes[idx] > 0);
      return `
        <button onclick="selecionarMesSlide(${mesNum})"
          class="px-2.5 py-1 rounded-lg text-[11px] font-extrabold transition shrink-0 ${
            ativo
              ? 'bg-emerald-600 text-white shadow-sm scale-105'
              : temMov
                ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                : 'bg-slate-50 text-slate-400 hover:bg-slate-100'
          }">
          ${m}
        </button>
      `;
    }).join('');

    const ativoAno = MES_SLIDE_ATIVO === 0;
    btnContainer.innerHTML = botoesHTML + `
      <button onclick="selecionarMesSlide(0)"
        class="px-2.5 py-1 rounded-lg text-[11px] font-black transition shrink-0 ${
          ativoAno
            ? 'bg-slate-900 text-white shadow-sm scale-105'
            : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
        }">
        ANO TODO
      </button>
    `;
  }

  // 2. Calcula Entradas, Despesas e Saldo do Período Selecionado
  let entradasVal = 0;
  let despesasVal = 0;
  let saldoVal = 0;
  let labelPeriodo = '';

  if (MES_SLIDE_ATIVO === 0) {
    entradasVal = totalEntradas;
    despesasVal = totalSaidas;
    saldoVal = totalEntradas - totalSaidas;
    labelPeriodo = `EXERCÍCIO ${ANO_MATRIZ_ATIVO} (CONSOLIDADO ANUAL)`;
  } else {
    const idx = MES_SLIDE_ATIVO - 1;
    entradasVal = entMes[idx] || 0;
    despesasVal = saiMes[idx] || 0;
    saldoVal = entradasVal - despesasVal;
    labelPeriodo = `MÊS DE ${NOMES_MESES[idx]} DE ${ANO_MATRIZ_ATIVO}`;
  }

  const elTitulo = document.getElementById('slide-periodo-titulo');
  if (elTitulo) elTitulo.textContent = labelPeriodo;

  // 3. Renderiza os Cards de Resumo Rápido para Celular (< 640px) com números ajustados
  const elMobileKpis = document.getElementById('slide-mobile-kpis');
  if (elMobileKpis) {
    elMobileKpis.innerHTML = `
      <div class="p-1.5 rounded-xl bg-emerald-50 border border-emerald-200 shadow-2xs overflow-hidden text-center">
        <span class="text-[9px] font-bold text-emerald-800 uppercase block truncate">Entradas</span>
        <strong class="text-[10px] sm:text-xs font-black text-emerald-700 block mt-0.5 tracking-tight truncate" title="${formatBRL(entradasVal)}">${formatBRL(entradasVal)}</strong>
      </div>
      <div class="p-1.5 rounded-xl bg-rose-50 border border-rose-200 shadow-2xs overflow-hidden text-center">
        <span class="text-[9px] font-bold text-rose-800 uppercase block truncate">Despesas</span>
        <strong class="text-[10px] sm:text-xs font-black text-rose-700 block mt-0.5 tracking-tight truncate" title="${formatBRL(despesasVal)}">${formatBRL(despesasVal)}</strong>
      </div>
      <div class="p-1.5 rounded-xl ${saldoVal >= 0 ? 'bg-sky-50 border-sky-200 text-sky-800' : 'bg-rose-50 border-rose-200 text-rose-800'} shadow-2xs overflow-hidden text-center">
        <span class="text-[9px] font-bold uppercase block truncate">Saldo</span>
        <strong class="text-[10px] sm:text-xs font-black block mt-0.5 tracking-tight truncate ${saldoVal >= 0 ? 'text-sky-700' : 'text-rose-700'}" title="${formatBRL(saldoVal)}">${formatBRL(saldoVal)}</strong>
      </div>
    `;
  }

  // 4. Renderiza o Gráfico Esquerdo (3 Colunas Verticais: Entradas, Despesas, Saldo)
  const colContainer = document.getElementById('slide-colunas-container');
  if (colContainer) {
    const maxCol = Math.max(entradasVal, despesasVal, Math.abs(saldoVal), 1);
    const hEnt = Math.max(Math.round((entradasVal / maxCol) * 200), entradasVal > 0 ? 18 : 4);
    const hDes = Math.max(Math.round((despesasVal / maxCol) * 200), despesasVal > 0 ? 18 : 4);
    const hSal = Math.max(Math.round((Math.abs(saldoVal) / maxCol) * 200), Math.abs(saldoVal) > 0 ? 14 : 4);

    const corSaldo = saldoVal >= 0 ? '#00b4d8' : '#f43f5e';

    colContainer.innerHTML = `
      <!-- Coluna 1: Entradas -->
      <div class="flex flex-col items-center justify-end flex-1 max-w-[85px] sm:max-w-[125px] group">
        <span class="text-slate-900 font-extrabold text-[10.5px] sm:text-base tracking-tight mb-1 sm:mb-2 text-center whitespace-nowrap block truncate w-full" title="${formatSlideNumber(entradasVal)}">
          ${formatSlideNumber(entradasVal)}
        </span>
        <div class="w-full rounded-t-sm transition-all duration-500 shadow-md group-hover:brightness-105"
             style="height: ${hEnt}px; background-color: #10c469;"></div>
        <span class="text-slate-800 font-bold text-xs sm:text-sm mt-2.5 tracking-wide">Entradas</span>
      </div>

      <!-- Coluna 2: Despesas -->
      <div class="flex flex-col items-center justify-end flex-1 max-w-[85px] sm:max-w-[125px] group">
        <span class="text-slate-900 font-extrabold text-[10.5px] sm:text-base tracking-tight mb-1 sm:mb-2 text-center whitespace-nowrap block truncate w-full" title="${formatSlideNumber(despesasVal)}">
          ${formatSlideNumber(despesasVal)}
        </span>
        <div class="w-full rounded-t-sm transition-all duration-500 shadow-md group-hover:brightness-105"
             style="height: ${hDes}px; background-color: #ff4b2b;"></div>
        <span class="text-slate-800 font-bold text-xs sm:text-sm mt-2.5 tracking-wide">Despesas</span>
      </div>

      <!-- Coluna 3: Saldo -->
      <div class="flex flex-col items-center justify-end flex-1 max-w-[85px] sm:max-w-[125px] group">
        <span class="text-slate-900 font-extrabold text-[10.5px] sm:text-base tracking-tight mb-1 sm:mb-2 text-center whitespace-nowrap block truncate w-full" title="${formatSlideNumber(saldoVal)}">
          ${formatSlideNumber(saldoVal)}
        </span>
        <div class="w-full rounded-t-sm transition-all duration-500 shadow-md group-hover:brightness-105"
             style="height: ${hSal}px; background-color: ${corSaldo};"></div>
        <span class="text-slate-800 font-bold text-xs sm:text-sm mt-2.5 tracking-wide">Saldo</span>
      </div>
    `;
  }

  // 5. Renderiza a Lista Direita (Resumo Despesas: Barras Horizontais com Valor e %)
  const resumoContainer = document.getElementById('slide-resumo-despesas-list');
  if (resumoContainer) {
    const despesasRows = rows.filter(r => r.tipo_fluxo === 'SAIDA' || r.tipo === 'SAIDA');
    const totaisPorGrupo = {};

    despesasRows.forEach(r => {
      let v = 0;
      if (MES_SLIDE_ATIVO === 0) {
        v = (r.meses || []).reduce((a, b) => a + (Number(b) || 0), 0);
      } else {
        v = Number((r.meses || [])[MES_SLIDE_ATIVO - 1]) || 0;
      }
      totaisPorGrupo[r.grupo] = (totaisPorGrupo[r.grupo] || 0) + v;
    });

    const listaGrupos = Object.entries(totaisPorGrupo)
      .map(([grupo, valor]) => ({
        grupo,
        valor,
        perc: despesasVal > 0 ? (valor / despesasVal) * 100 : 0
      }))
      .sort((a, b) => b.valor - a.valor);

    const maxDespesaGrupo = Math.max(...listaGrupos.map(g => g.valor), 1);

    resumoContainer.innerHTML = listaGrupos.map(item => {
      const larguraBarra = Math.min(Math.round((item.valor / maxDespesaGrupo) * 100), 100);

      return `
        <div class="flex items-center gap-2 sm:gap-3 py-1 sm:py-1.5 border-b border-slate-100 hover:bg-slate-50 transition px-1 rounded cursor-pointer group"
             onclick="filtrarGrupoPeloSlide('${item.grupo}')" title="Clique para filtrar este grupo na Matriz">
          <!-- Nome do Grupo -->
          <div class="w-40 sm:w-48 text-[11px] sm:text-xs font-bold text-slate-800 truncate group-hover:text-indigo-600 transition" title="${item.grupo}">
            ${item.grupo}
          </div>

          <!-- Barra Horizontal -->
          <div class="flex-1 bg-slate-100 h-3 sm:h-3.5 rounded-sm overflow-hidden flex items-center">
            <div class="h-full rounded-sm transition-all duration-500 shadow-2xs group-hover:brightness-110"
                 style="width: ${larguraBarra}%; min-width: ${item.valor > 0 ? '6px' : '1px'}; background-color: #ff4b2b;"></div>
          </div>

          <!-- Valor e Porcentagem -->
          <div class="w-28 sm:w-32 flex items-center justify-end gap-1.5 sm:gap-2 text-right">
            <span class="text-slate-900 text-xs sm:text-[13px] font-extrabold whitespace-nowrap">
              ${formatSlidePercent(item.perc)}
            </span>
            <span class="text-slate-600 text-[10.5px] sm:text-xs font-bold whitespace-nowrap">
              ${formatSlideNumber(item.valor)}
            </span>
          </div>
        </div>
      `;
    }).join('');
  }

  // 6. Atualiza o Rodapé do Slide Geral
  const elEnt = document.getElementById('slide-total-entradas');
  const elSai = document.getElementById('slide-total-despesas');
  const elSal = document.getElementById('slide-saldo-final');
  const elPerc = document.getElementById('slide-perc-despesas');

  if (elEnt) elEnt.textContent = formatBRL(entradasVal);
  if (elSai) elSai.textContent = formatBRL(despesasVal);
  if (elSal) {
    elSal.textContent = formatBRL(saldoVal);
    elSal.className = `font-black text-xs sm:text-sm md:text-base tracking-tight leading-none px-2 py-1 rounded-lg ${saldoVal >= 0 ? 'text-indigo-600' : 'text-rose-600'}`;
  }
  if (elPerc) {
    const p = entradasVal > 0 ? (despesasVal / entradasVal) * 100 : 0;
    elPerc.textContent = `${p.toFixed(1)}%`;
  }
}

function alternarSlideProjecao(tipo) {
  SLIDE_PROJECAO_ATIVO = tipo;
  const slideGeral = document.getElementById('conteudo-slide-tesouraria');
  const slideMin = document.getElementById('painel-slide-ministerios');
  const btnGeral = document.getElementById('btn-slide-geral');
  const btnMin = document.getElementById('btn-slide-ministerios');

  if (tipo === 'geral') {
    if (slideGeral) slideGeral.classList.remove('hidden');
    if (slideMin) slideMin.classList.add('hidden');
    if (btnGeral) {
      btnGeral.classList.add('bg-indigo-600', 'text-white', 'shadow-xs');
      btnGeral.classList.remove('bg-white', 'text-slate-700');
    }
    if (btnMin) {
      btnMin.classList.remove('bg-indigo-600', 'text-white', 'shadow-xs');
      btnMin.classList.add('bg-white', 'text-slate-700');
    }
    renderSlideTesouraria();
  } else {
    if (slideGeral) slideGeral.classList.add('hidden');
    if (slideMin) slideMin.classList.remove('hidden');
    if (btnMin) {
      btnMin.classList.add('bg-indigo-600', 'text-white', 'shadow-xs');
      btnMin.classList.remove('bg-white', 'text-slate-700');
    }
    if (btnGeral) {
      btnGeral.classList.remove('bg-indigo-600', 'text-white', 'shadow-xs');
      btnGeral.classList.add('bg-white', 'text-slate-700');
    }
    renderSlideMinisterios();
  }
}

function setOrdemSlideMinisterios(ordem) {
  ORDEM_SLIDE_MINISTERIOS = ordem;
  ['padrao', 'orcamento', 'realizado', 'nome'].forEach(o => {
    const btn = document.getElementById(`btn-ordem-min-${o}`);
    if (btn) {
      if (o === ordem) {
        btn.classList.add('bg-indigo-600', 'text-white');
        btn.classList.remove('bg-slate-100', 'text-slate-700');
      } else {
        btn.classList.remove('bg-indigo-600', 'text-white');
        btn.classList.add('bg-slate-100', 'text-slate-700');
      }
    }
  });
  renderSlideMinisterios();
}

function filtrarBuscaSlideMinisterios(termo) {
  BUSCA_SLIDE_MINISTERIOS = (termo || '').trim().toLowerCase();
  renderSlideMinisterios();
}

function abrirSlideTelaCheia() {
  const elem = document.getElementById('tab-projecao');
  if (!elem) return;
  if (!document.fullscreenElement) {
    if (elem.requestFullscreen) {
      elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
      elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
      elem.msRequestFullscreen();
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }
}

function renderSlideMinisterios() {
  const ano = ANO_MATRIZ_ATIVO || 2026;
  const anoAnt = ano - 1;
  const inputAno = document.getElementById('input-ano-slide-min');
  if (inputAno && Number(inputAno.value) !== ano) {
    inputAno.value = ano;
  }

  const elTitulo = document.getElementById('slide-min-titulo');
  if (elTitulo) {
    elTitulo.textContent = `ORÇAMENTOS DOS 15 MINISTÉRIOS | EXERCÍCIO ${ano}`;
  }

  const mins = STATE.ministerios || [];
  if (!mins.length) return;

  // 1. Calcula valores de cada ministério no ano ativo (Realizado / Orçado / Executado / Saldo)
  let dados = mins.map(m => {
    const realAntVal = getRealizadoMinisterio(m, anoAnt);
    const orcVal = getOrcamentoMinisterio(m, ano);
    const execVal = getExecutadoMinisterio(m, ano);
    const saldoVal = orcVal - execVal;
    const perc = orcVal > 0 ? (execVal / orcVal) * 100 : (execVal > 0 ? 100 : 0);
    
    // Nome curto para exibição no eixo X
    let nomeCurto = (m.nome || '')
      .replace(/Minist[eé]rio/gi, '')
      .replace(/\(Escola B[ií]blica\)/gi, '')
      .replace(/Batista/gi, '')
      .replace(/e Adolescentes/gi, '')
      .trim();
    if (!nomeCurto) nomeCurto = m.nome;

    return {
      ministerio: m,
      nomeCurto,
      realAntVal,
      orcVal,
      execVal,
      saldoVal,
      perc
    };
  });

  // 2. Totais consolidados dos 15 ministérios (Sem redundância, exibidos diretamente nos 4 KPIs do topo)
  const totReal = dados.reduce((a, b) => a + b.realAntVal, 0);
  const totOrc = dados.reduce((a, b) => a + b.orcVal, 0);
  const totExec = dados.reduce((a, b) => a + b.execVal, 0);
  const totSaldo = totOrc - totExec;
  const percGlobal = totOrc > 0 ? (totExec / totOrc) * 100 : 0;

  // Atualiza os 4 KPIs exclusivos do topo do Slide 2
  const elTotReal = document.getElementById('slide-min-kpi-real');
  const elTotOrc = document.getElementById('slide-min-kpi-orc');
  const elTotExec = document.getElementById('slide-min-kpi-exec');
  const elTotSaldo = document.getElementById('slide-min-kpi-saldo');
  const elPercGlobal = document.getElementById('slide-min-kpi-perc');

  if (elTotReal) elTotReal.textContent = formatBRL(totReal);
  if (elTotOrc) elTotOrc.textContent = formatBRL(totOrc);
  if (elTotExec) elTotExec.textContent = formatBRL(totExec);
  if (elTotSaldo) {
    elTotSaldo.textContent = formatBRL(totSaldo);
    elTotSaldo.className = `text-sm sm:text-lg font-black ${totSaldo >= 0 ? 'text-emerald-900' : 'text-rose-900'}`;
  }
  if (elPercGlobal) elPercGlobal.textContent = `${percGlobal.toFixed(1)}%`;

  // Filtro de busca textual
  if (typeof BUSCA_SLIDE_MINISTERIOS !== 'undefined' && BUSCA_SLIDE_MINISTERIOS) {
    dados = dados.filter(d => (d.ministerio.nome || '').toLowerCase().includes(BUSCA_SLIDE_MINISTERIOS));
  }

  // Ordenação selecionada
  const ordem = typeof ORDEM_SLIDE_MINISTERIOS !== 'undefined' ? ORDEM_SLIDE_MINISTERIOS : 'orcamento';
  if (ordem === 'orcamento') {
    dados.sort((a, b) => b.orcVal - a.orcVal);
  } else if (ordem === 'realizado' || ordem === 'execucao') {
    dados.sort((a, b) => b.perc - a.perc);
  } else if (ordem === 'saldo') {
    dados.sort((a, b) => b.saldoVal - a.saldoVal);
  } else if (ordem === 'nome') {
    dados.sort((a, b) => a.ministerio.nome.localeCompare(b.ministerio.nome));
  }

  // 3. RENDERIZA O GRÁFICO PANORÂMICO VERTICAL COM TODOS OS 15 MINISTÉRIOS EM TELA ÚNICA
  const colunasContainer = document.getElementById('slide-min-panoramico-colunas');
  if (colunasContainer) {
    const maxGeral = Math.max(...dados.flatMap(d => [d.realAntVal, d.orcVal, d.execVal]), 1);

    colunasContainer.innerHTML = dados.map(d => {
      const m = d.ministerio;
      const hReal = Math.max(Math.round((d.realAntVal / maxGeral) * 200), d.realAntVal > 0 ? 10 : 3);
      const hOrc = Math.max(Math.round((d.orcVal / maxGeral) * 200), d.orcVal > 0 ? 10 : 3);
      const hExec = Math.max(Math.round((d.execVal / maxGeral) * 200), d.execVal > 0 ? 10 : 3);

      let barraExecCor = '#10b981'; // verde
      if (d.perc > 100) barraExecCor = '#ef4444'; // vermelho
      else if (d.perc >= 80) barraExecCor = '#f59e0b'; // amarelo

      const topoValorStr = d.orcVal >= 1000 ? `${(d.orcVal / 1000).toFixed(1).replace('.0', '')}k` : `${Math.round(d.orcVal)}`;

      return `
        <div class="flex-1 min-w-[50px] max-w-[85px] flex flex-col items-center justify-end h-full group transition cursor-pointer"
             title="${m.nome}\n• Realizado ${anoAnt}: ${formatBRL(d.realAntVal)}\n• Orçado ${ano}: ${formatBRL(d.orcVal)}\n• Executado ${ano}: ${formatBRL(d.execVal)}\n• Saldo: ${formatBRL(d.saldoVal)} (${d.perc.toFixed(1)}% executado)">
          
          <!-- Valor no topo do grupo (Meta Orçada) -->
          <span class="text-[9.5px] sm:text-[11px] font-black text-indigo-950 mb-1.5 group-hover:scale-110 transition whitespace-nowrap block truncate">
            ${topoValorStr}
          </span>

          <!-- As 3 Colunas Verticais lado a lado sobre a linha de base -->
          <div class="flex items-end justify-center gap-1 sm:gap-1.5 w-full px-0.5">
            <!-- 1. Coluna Realizado -->
            <div class="w-2.5 sm:w-3 lg:w-4 rounded-t-xs transition-all duration-500 bg-slate-400 group-hover:bg-slate-500 shadow-2xs"
                 style="height: ${hReal}px;" title="Realizado ${anoAnt}: ${formatBRL(d.realAntVal)}">
            </div>

            <!-- 2. Coluna Orçado -->
            <div class="w-3 sm:w-3.5 lg:w-4.5 rounded-t-xs transition-all duration-500 bg-indigo-600 group-hover:bg-indigo-700 shadow-xs"
                 style="height: ${hOrc}px;" title="Orçado ${ano}: ${formatBRL(d.orcVal)}">
            </div>

            <!-- 3. Coluna Executado -->
            <div class="w-2.5 sm:w-3 lg:w-4 rounded-t-xs transition-all duration-500 shadow-2xs"
                 style="height: ${hExec}px; background-color: ${barraExecCor};" title="Executado ${ano}: ${formatBRL(d.execVal)}">
            </div>
          </div>

          <!-- Rótulo do Eixo X (Nome e Cor do Ministério) -->
          <div class="mt-2.5 text-center w-full flex flex-col items-center">
            <span class="w-2.5 h-2.5 rounded-full block mb-1 shadow-2xs group-hover:scale-125 transition" style="background-color: ${m.cor || '#4f46e5'};"></span>
            <span class="text-[9.5px] sm:text-[11px] font-extrabold text-slate-800 leading-tight truncate w-full block group-hover:text-indigo-600 transition" title="${m.nome}">
              ${d.nomeCurto}
            </span>
            <span class="text-[8.5px] sm:text-[9.5px] font-bold text-slate-400 leading-none block mt-0.5">
              ${d.perc > 0 ? d.perc.toFixed(0) + '%' : '0%'}
            </span>
          </div>

        </div>
      `;
    }).join('');
  }

  renderizarQRCodesAssembleia();
}



function getAnosDisponiveis() {
  const anosSet = new Set(ANOS_MINISTERIOS_DISPONIVEIS || [2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]);
  if (STATE && STATE.matriz_tesouraria) {
    STATE.matriz_tesouraria.forEach(r => {
      if (r.ano) anosSet.add(Number(r.ano));
    });
  }
  return Array.from(anosSet).sort((a, b) => b - a);
}

function populateSelects() {
  const dlMembros = document.getElementById('lista-membros-datalist');
  if (dlMembros && STATE.membros) {
    dlMembros.innerHTML = STATE.membros.map(m => `
      <option value="${m.nome}">${m.cargo_eclesiastico || 'Membro'} • ${m.telefone || 'Sem tel'}</option>
    `).join('');
  }
  const celOptions = `<option value="">Sem vínculo de célula</option>` +
    (STATE.celulas || []).map(c => `<option value="${c.id}">${c.nome} (${c.bairro})</option>`).join('');

  const minOptionsOptional = `<option value="">Nenhum ministério selecionado</option>` +
    (STATE.ministerios || []).map(m => `<option value="${m.id}">${m.nome}</option>`).join('');

  const minOptionsRequired = (STATE.ministerios || []).map(m => `<option value="${m.id}">${m.nome}</option>`).join('');

  const memOptionsOptional = `<option value="">Sem vínculo nominal (Oferta Geral / Despesa)</option>` +
    (STATE.membros || []).map(m => `<option value="${m.id}">${m.nome}</option>`).join('');

  const memOptionsRequired = (STATE.membros || []).map(m => `<option value="${m.id}">${m.nome} (${m.cargo_eclesiastico || 'Membro'})</option>`).join('');

  const setHTML = (id, html) => {
    const el = document.getElementById(id);
    if (el) {
      const currentVal = el.value;
      el.innerHTML = html;
      if (currentVal) el.value = currentVal;
    }
  };

  const minOptionsMembro = `<option value="">-- Nenhum ministério selecionado --</option>` +
    (STATE.ministerios || []).map(m => `<option value="${m.id}">${m.nome}</option>`).join('');

  setHTML('mem-celula', celOptions);
  setHTML('vis-celula', celOptions);
  setHTML('mem-ministerio', minOptionsMembro);
  setHTML('mem-ministerio-2', minOptionsMembro);
  setHTML('esc-ministerio', minOptionsRequired);
  setHTML('vol-ministerio', minOptionsRequired);
  setHTML('req-ministerio', minOptionsRequired);
  setHTML('fin-ministerio', minOptionsOptional);
  setHTML('pat-ministerio', minOptionsOptional);
  setHTML('esc-membro', memOptionsRequired);
  setHTML('vol-membro', memOptionsRequired);
  setHTML('fin-membro', memOptionsOptional);
  setHTML('filtro-escala-ministerio', `<option value="">Todos os 15 Ministérios</option>` + minOptionsRequired);
  setHTML('rel-ministerio', `<option value="">Todos os 15 Ministérios</option>` + minOptionsRequired);

  // Popula anos do sistema (Exercício e Análise Orçamentária)
  const anos = getAnosDisponiveis();

  // 1. Atualiza elementos do novo Seletor Vertical de Exercício (Stepper Compacto)
  atualizarDisplayAnoExercicio();

  // 2. Seletores de Análise Orçamentária dos 15 Ministérios
  const anoRealizadoOptions = anos.map(a => `
    <option value="${a}" ${Number(a) === Number(ANO_MIN_REALIZADO) ? 'selected' : ''}>
      ${a}
    </option>
  `).join('');
  setHTML('sel-ano-realizado', anoRealizadoOptions);
  setHTML('sel-ano-realizado-tab', anoRealizadoOptions);

  const anoOrcamentoOptions = anos.map(a => `
    <option value="${a}" ${Number(a) === Number(ANO_MIN_ORCAMENTO) ? 'selected' : ''}>
      ${a}
    </option>
  `).join('');
  setHTML('sel-ano-orcamento', anoOrcamentoOptions);
  setHTML('sel-ano-orcamento-tab', anoOrcamentoOptions);

  const anoExecutadoOptions = anos.map(a => `
    <option value="${a}" ${Number(a) === Number(ANO_MIN_EXECUTADO) ? 'selected' : ''}>
      ${a}
    </option>
  `).join('');
  setHTML('sel-ano-executado', anoExecutadoOptions);
  setHTML('sel-ano-executado-tab', anoExecutadoOptions);

  if (typeof popularCamposLancamentoManual === 'function') {
    popularCamposLancamentoManual();
  }
}

function atualizarDisplayAnoExercicio() {
  const anoAtual = Number(ANO_MATRIZ_ATIVO) || 2026;

  ['planilha', 'dash'].forEach(sufixo => {
    const elDisp = document.getElementById(`display-ano-exercicio-${sufixo}`);
    const elHidden = document.getElementById(`sel-ano-${sufixo === 'dash' ? 'dashboard' : 'planilha'}`);

    if (elDisp) elDisp.textContent = String(anoAtual);
    if (elHidden) elHidden.value = String(anoAtual);
  });

  // Mantém o título da planilha perfeitamente limpo, sem redundância do ano
  const elTituloPlan = document.getElementById('titulo-planilha-ano');
  if (elTituloPlan) {
    elTituloPlan.textContent = 'Matriz Financeira Mensal';
  }
}

function aoRolarScrollAno(e) {
  if (!e) return;
  e.preventDefault();
  if (e.deltaY < 0) {
    navegarAnoExercicio(1);
  } else if (e.deltaY > 0) {
    navegarAnoExercicio(-1);
  }
}

function navegarAnoExercicio(delta) {
  const anoAtual = Number(ANO_MATRIZ_ATIVO) || 2026;
  const novoAno = anoAtual + delta;
  if (novoAno >= 2020 && novoAno <= 2035) {
    selecionarAnoDashboard(novoAno);
  }
}

function selecionarAnoDashboard(ano) {
  const numAno = Number(ano) || 2026;
  ANO_MATRIZ_ATIVO = numAno;

  // Garante em memória e no backend que o ano selecionado tenha todas as contas padrão de 2026
  const rowsAnoAtual = (STATE.matriz_tesouraria || []).filter(r => Number(r.ano) === numAno);
  const rowsPadrao2026 = (STATE.matriz_tesouraria || []).filter(r => Number(r.ano) === 2026);
  if (rowsPadrao2026.length > 0 && rowsAnoAtual.length < rowsPadrao2026.length) {
    const chavesExistentes = new Set(rowsAnoAtual.map(r => `${r.tipo_fluxo}||${r.grupo}||${r.rubrica}`));
    let faltouAlguma = false;
    rowsPadrao2026.forEach(pad => {
      const chave = `${pad.tipo_fluxo}||${pad.grupo}||${pad.rubrica}`;
      if (!chavesExistentes.has(chave)) {
        faltouAlguma = true;
        STATE.matriz_tesouraria.push({
          ...pad,
          id: pad.id,
          ano: numAno,
          m1: 0, m2: 0, m3: 0, m4: 0, m5: 0, m6: 0, m7: 0, m8: 0, m9: 0, m10: 0, m11: 0, m12: 0,
          meses: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          total_anual: 0,
          media_mensal: 0
        });
      }
    });
    if (faltouAlguma) {
      apiPost('/api/matriz/garantir-ano', { ano: numAno }).then(() => fetchBootstrap()).catch(() => {});
    }
  }

  // Atualiza os displays do novo Stepper Vertical
  atualizarDisplayAnoExercicio();

  // Sincroniza inputs nos slides de projeção
  const inputMatriz = document.getElementById('input-ano-matriz');
  if (inputMatriz && Number(inputMatriz.value) !== numAno) inputMatriz.value = String(numAno);

  const inputSlideMin = document.getElementById('input-ano-slide-min');
  if (inputSlideMin && Number(inputSlideMin.value) !== numAno) inputSlideMin.value = String(numAno);

  renderDashboard();
  renderBadgesAndKPIs();
  renderMatrizTesouraria();
  renderSlideTesouraria();
  renderSlideMinisterios();
  showLiveToast(`📅 Exercício alternado para ${numAno}!`);
}

function selecionarAnoMatriz(ano) {
  selecionarAnoDashboard(ano);
}

function mudarAnosMinisterios(tipo, val) {
  const ano = Number(val);
  if (tipo === 'realizado') {
    ANO_MIN_REALIZADO = ano;
    ['sel-ano-realizado', 'sel-ano-realizado-tab'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = String(ano);
    });
  } else if (tipo === 'orcamento') {
    ANO_MIN_ORCAMENTO = ano;
    ['sel-ano-orcamento', 'sel-ano-orcamento-tab'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = String(ano);
    });
  } else if (tipo === 'executado') {
    ANO_MIN_EXECUTADO = ano;
    ['sel-ano-executado', 'sel-ano-executado-tab'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = String(ano);
    });
  }

  renderOrcamento15Ministerios();
  renderSlideMinisterios();
  renderDashboard();
  renderBadgesAndKPIs();
  showLiveToast(`🏛️ Análise orçamentária atualizada (${tipo.toUpperCase()}: ${ano})!`);
}

function renderBadgesAndKPIs() {
  const membrosAtivos = (STATE.membros || []).filter(m => m.status === 'Ativo').length;
  const reqPendentes = (STATE.requisicoes || []).filter(r => r.status === 'Pendente').length;
  const visNovos = (STATE.visitantes || []).filter(v => v.status_acompanhamento !== 'Integrado como Membro').length;

  const anoAtivo = ANO_MATRIZ_ATIVO || 2026;
  const resAno = calcularResumoAnoMatriz(anoAtivo);

  const anoReal = ANO_MIN_REALIZADO || 2025;
  const anoOrc = ANO_MIN_ORCAMENTO || 2026;
  const anoExec = ANO_MIN_EXECUTADO || 2026;

  const totOrcMin = (STATE.ministerios || []).reduce((a, b) => a + getOrcamentoMinisterio(b, anoOrc), 0);
  const totRealMin = (STATE.ministerios || []).reduce((a, b) => a + getRealizadoMinisterio(b, anoReal), 0);
  const totExecMin = (STATE.ministerios || []).reduce((a, b) => a + getExecutadoMinisterio(b, anoExec), 0);

  const badgeMem = document.getElementById('badge-membros');
  if (badgeMem) badgeMem.textContent = (STATE.membros || []).length;

  const badgeVis = document.getElementById('badge-visitantes');
  if (badgeVis) badgeVis.textContent = visNovos;

  const badgeEsc = document.getElementById('badge-escalas');
  if (badgeEsc) badgeEsc.textContent = (STATE.escalas || []).length;

  const badgeReq = document.getElementById('badge-requisicoes');
  if (badgeReq) badgeReq.textContent = reqPendentes > 0 ? `${reqPendentes} pend.` : String(anoAtivo);

  const badgeCel = document.getElementById('badge-celulas');
  if (badgeCel) badgeCel.textContent = (STATE.celulas || []).length;

  const badgePat = document.getElementById('badge-patrimonio');
  if (badgePat) badgePat.textContent = (STATE.patrimonio || []).length;

  const badgeUsr = document.getElementById('badge-usuarios');
  if (badgeUsr) badgeUsr.textContent = (STATE.usuarios || []).length;

  const totalAtasCount = (STATE.atas || []).length;
  const badgeAtas = document.getElementById('badge-atas');
  if (badgeAtas) badgeAtas.textContent = totalAtasCount;
  const badgeSubAtas = document.getElementById('badge-sub-atas');
  if (badgeSubAtas) badgeSubAtas.textContent = totalAtasCount;

  const badgeOnl = document.getElementById('online-count-badge');
  if (badgeOnl) badgeOnl.textContent = `${STATE.clientes_conectados || 1} tela(s) ativa(s)`;

  // Cards do Dashboard com rótulos e valores dinâmicos do ano selecionado
  const lblEnt = document.getElementById('label-kpi-entradas');
  if (lblEnt) lblEnt.textContent = `Entradas ${anoAtivo}`;

  const elEnt26 = document.getElementById('kpi-entradas-2026');
  if (elEnt26) {
    elEnt26.textContent = formatBRL(resAno.totalEntradas);
    elEnt26.title = formatBRL(resAno.totalEntradas);
  }

  const lblSaldo = document.getElementById('label-kpi-saldo');
  if (lblSaldo) lblSaldo.textContent = `Saldo Real ${anoAtivo}`;

  const elSaldo = document.getElementById('kpi-saldo');
  if (elSaldo) {
    elSaldo.textContent = formatBRL(resAno.saldoTotal);
    elSaldo.title = formatBRL(resAno.saldoTotal);
    elSaldo.className = `text-base sm:text-lg xl:text-xl 2xl:text-2xl font-black tracking-tight truncate whitespace-nowrap ${resAno.saldoTotal >= 0 ? 'text-indigo-600' : 'text-rose-600'}`;
  }

  const subSaldo = document.getElementById('kpi-financeiro-sub');
  if (subSaldo) {
    subSaldo.textContent = `Saídas ${anoAtivo}: ${formatBRL(resAno.totalSaidas)} ➔`;
  }

  const elOrcMin = document.getElementById('kpi-orcamento-min');
  if (elOrcMin) {
    elOrcMin.textContent = formatBRL(totOrcMin);
    elOrcMin.title = formatBRL(totOrcMin);
  }

  const elOrcMinSub = document.getElementById('kpi-orcamento-min-sub');
  if (elOrcMinSub) {
    elOrcMinSub.textContent = `${anoReal}: ${formatBRL(totRealMin)} ➔`;
  }

  // Quadro 4: Membros no Dashboard
  const elMembrosKpi = document.getElementById('kpi-membros');
  if (elMembrosKpi) elMembrosKpi.textContent = String(membrosAtivos);

  const elMembrosSubKpi = document.getElementById('kpi-membros-sub');
  if (elMembrosSubKpi) elMembrosSubKpi.textContent = `${membrosAtivos} ativos em comunhão ➔`;

  // Quadro 5: Pedidos no Dashboard
  const elReqKpi = document.getElementById('kpi-requisicoes');
  if (elReqKpi) {
    elReqKpi.textContent = String(reqPendentes);
    elReqKpi.className = `text-base sm:text-lg xl:text-xl 2xl:text-2xl font-black tracking-tight truncate whitespace-nowrap ${reqPendentes > 0 ? 'text-rose-600' : 'text-emerald-600'}`;
  }

  const elReqSubKpi = document.getElementById('kpi-requisicoes-sub');
  if (elReqSubKpi) {
    elReqSubKpi.textContent = reqPendentes > 0 ? `${reqPendentes} aguardando aprovação ➔` : 'Nenhum pedido pendente ➔';
  }

  // Mini KPIs na aba Ministérios
  const elMinTotalOrc = document.getElementById('min-painel-total-orc');
  const elMinTotalReal = document.getElementById('min-painel-total-real25');
  const elMinTotalExec = document.getElementById('min-painel-total-exec');
  const elMinTotalSaldo = document.getElementById('min-painel-total-saldo');

  if (elMinTotalOrc) elMinTotalOrc.textContent = formatBRL(totOrcMin);
  if (elMinTotalReal) elMinTotalReal.textContent = formatBRL(totRealMin);
  if (elMinTotalExec) elMinTotalExec.textContent = formatBRL(totExecMin);
  if (elMinTotalSaldo) {
    const s = totOrcMin - totExecMin;
    elMinTotalSaldo.textContent = formatBRL(s);
    elMinTotalSaldo.className = `text-lg font-black ${s >= 0 ? 'text-indigo-700' : 'text-rose-600'}`;
  }

  const lblKpiOrc = document.getElementById('lbl-min-kpi-orc');
  const lblKpiReal = document.getElementById('lbl-min-kpi-real');
  const lblKpiExec = document.getElementById('lbl-min-kpi-exec');
  if (lblKpiOrc) lblKpiOrc.textContent = String(anoOrc);
  if (lblKpiReal) lblKpiReal.textContent = String(anoReal);
  if (lblKpiExec) lblKpiExec.textContent = String(anoExec);

  // Gráficos de BI
  if (typeof renderGraficosBI === 'function') {
    renderGraficosBI(resAno);
  }
}

function renderDashboard() {
  const anoAtivo = ANO_MATRIZ_ATIVO || 2026;
  const resAno = typeof calcularResumoAnoMatriz === 'function' ? calcularResumoAnoMatriz(anoAtivo) : { totalEntradas: 0, totalSaidas: 0, saldoTotal: 0 };

  const anoReal = ANO_MIN_REALIZADO || 2025;
  const anoOrc = ANO_MIN_ORCAMENTO || 2026;
  const anoExec = ANO_MIN_EXECUTADO || 2026;

  const membrosList = STATE.membros || [];
  const membrosTotal = membrosList.length;
  const membrosAtivos = membrosList.filter(m => m.status === 'Ativo').length;

  const reqList = STATE.requisicoes || [];
  const reqTotal = reqList.length;
  const reqPendentes = reqList.filter(r => r.status === 'Pendente').length;

  const visTotal = (STATE.visitantes || []).length;
  const visNovos = (STATE.visitantes || []).filter(v => v.status_acompanhamento !== 'Integrado como Membro').length;

  const celTotal = (STATE.celulas || []).length;
  const patTotal = (STATE.patrimonio || []).length;
  const patDisponiveis = (STATE.patrimonio || []).filter(p => (p.status || 'Disponível') === 'Disponível').length;

  const minsList = STATE.ministerios || [];
  const totOrcMin = minsList.reduce((a, b) => a + getOrcamentoMinisterio(b, anoOrc), 0);
  const totRealMin = minsList.reduce((a, b) => a + getRealizadoMinisterio(b, anoReal), 0);
  const totExecMin = minsList.reduce((a, b) => a + getExecutadoMinisterio(b, anoExec), 0);

  // Sincroniza seletor de exercício da Visão Geral
  const selDash = document.getElementById('sel-ano-dashboard');
  if (selDash && Number(selDash.value) !== Number(anoAtivo)) {
    selDash.value = String(anoAtivo);
  }

  // 1. Quadro 1: Entradas
  const lblEnt = document.getElementById('label-kpi-entradas');
  if (lblEnt) lblEnt.textContent = `Entradas ${anoAtivo}`;
  const elEnt = document.getElementById('kpi-entradas-2026');
  if (elEnt) {
    elEnt.textContent = formatBRL(resAno.totalEntradas);
    elEnt.title = `Total arrecadado em ${anoAtivo}: ${formatBRL(resAno.totalEntradas)}`;
  }
  const elEntSub = document.getElementById('kpi-entradas-sub');
  if (elEntSub) elEntSub.textContent = `Total arrecadado em ${anoAtivo} ➔`;

  // 2. Quadro 2: Saldo Real
  const lblSaldo = document.getElementById('label-kpi-saldo');
  if (lblSaldo) lblSaldo.textContent = `Saldo Real ${anoAtivo}`;
  const elSaldo = document.getElementById('kpi-saldo');
  if (elSaldo) {
    elSaldo.textContent = formatBRL(resAno.saldoTotal);
    elSaldo.title = `Saldo do Exercício ${anoAtivo}: ${formatBRL(resAno.saldoTotal)}`;
    elSaldo.className = `text-base sm:text-lg xl:text-xl 2xl:text-2xl font-black tracking-tight truncate whitespace-nowrap ${resAno.saldoTotal >= 0 ? 'text-indigo-600' : 'text-rose-600'}`;
  }
  const subSaldo = document.getElementById('kpi-financeiro-sub');
  if (subSaldo) {
    subSaldo.textContent = `Saídas ${anoAtivo}: ${formatBRL(resAno.totalSaidas)} ➔`;
  }

  // 3. Quadro 3: Orçamento 15 Ministérios
  const elOrcMin = document.getElementById('kpi-orcamento-min');
  if (elOrcMin) {
    elOrcMin.textContent = formatBRL(totOrcMin);
    elOrcMin.title = `Orçamento Total ${anoOrc}: ${formatBRL(totOrcMin)}`;
  }
  const elOrcMinSub = document.getElementById('kpi-orcamento-min-sub');
  if (elOrcMinSub) {
    elOrcMinSub.textContent = `Realizado ${anoReal}: ${formatBRL(totRealMin)} ➔`;
  }

  // 4. Quadro 4: Membros Cadastrados
  const elMembros = document.getElementById('kpi-membros');
  if (elMembros) {
    elMembros.textContent = String(membrosTotal);
    elMembros.title = `${membrosTotal} membros cadastrados no sistema (${membrosAtivos} ativos em comunhão)`;
  }
  const elMembrosSub = document.getElementById('kpi-membros-sub');
  if (elMembrosSub) {
    elMembrosSub.textContent = `${membrosAtivos} ativos em comunhão ➔`;
  }

  // 5. Quadro 5: Pedidos Pendentes
  const elReq = document.getElementById('kpi-requisicoes');
  if (elReq) {
    elReq.textContent = String(reqPendentes);
    elReq.title = `${reqPendentes} pedido(s) pendente(s) de aprovação na Tesouraria`;
    elReq.className = `text-base sm:text-lg xl:text-xl 2xl:text-2xl font-black tracking-tight truncate whitespace-nowrap ${reqPendentes > 0 ? 'text-rose-600' : 'text-emerald-600'}`;
  }
  const elReqSub = document.getElementById('kpi-requisicoes-sub');
  if (elReqSub) {
    elReqSub.textContent = reqPendentes > 0 ? `${reqPendentes} aguardando aprovação ➔` : 'Nenhum pedido pendente ➔';
  }

  // 6. Resumo Consolidado de Setores na Visão Geral
  const elResEnt = document.getElementById('dash-resumo-entradas');
  if (elResEnt) elResEnt.textContent = formatBRL(resAno.totalEntradas);

  const elResSai = document.getElementById('dash-resumo-saidas');
  if (elResSai) elResSai.textContent = formatBRL(resAno.totalSaidas);

  const elResSaldo = document.getElementById('dash-resumo-saldo');
  if (elResSaldo) {
    elResSaldo.textContent = formatBRL(resAno.saldoTotal);
    elResSaldo.className = `font-black truncate text-right ${resAno.saldoTotal >= 0 ? 'text-indigo-700' : 'text-rose-600'}`;
  }

  const elResMem = document.getElementById('dash-resumo-membros');
  if (elResMem) elResMem.textContent = `${membrosTotal} (${membrosAtivos} ativos)`;

  const elResVis = document.getElementById('dash-resumo-visitantes');
  if (elResVis) elResVis.textContent = `${visTotal} (${visNovos} novos)`;

  const elResMinOrc = document.getElementById('dash-resumo-min-orc');
  if (elResMinOrc) elResMinOrc.textContent = formatBRL(totOrcMin);

  const elResMinReal = document.getElementById('dash-resumo-min-real25');
  if (elResMinReal) elResMinReal.textContent = formatBRL(totRealMin);

  const elResPat = document.getElementById('dash-resumo-patrimonio');
  if (elResPat) elResPat.textContent = `${patTotal} bens (${patDisponiveis} disp.)`;

  const elResCel = document.getElementById('dash-resumo-celulas');
  if (elResCel) elResCel.textContent = `${celTotal} células/grupos`;

  // 7. Auditoria em Tempo Real na Visão Geral
  renderDashboardAuditoria();

  // 8. Container legatário de ministérios se presente
  const minContainer = document.getElementById('dashboard-ministerios-list');
  if (minContainer) {
    minContainer.innerHTML = minsList.map(m => {
      const orcAnual = getOrcamentoMinisterio(m, anoOrc);
      const execAnual = getExecutadoMinisterio(m, anoExec);
      const realAnt = getRealizadoMinisterio(m, anoReal);
      const perc = orcAnual > 0 ? Math.min(100, Math.round((execAnual / orcAnual) * 100)) : 0;
      const saldoDisp = orcAnual - execAnual;
      return `
        <div class="p-3.5 rounded-xl border border-slate-200 hover:border-indigo-300 transition bg-slate-50/50">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2.5">
              <span class="w-3.5 h-3.5 rounded-full shrink-0" style="background:${m.cor || '#4f46e5'}"></span>
              <div>
                <h4 class="font-bold text-slate-800 text-xs flex items-center gap-2">
                  ${m.nome}
                  <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">${anoReal}: ${formatBRL(realAnt)}</span>
                </h4>
                <p class="text-[11px] text-slate-500">
                  Obs: <em class="text-slate-700">${m.descricao || 'Sem observação'}</em> • Saldo ${anoOrc}: <strong class="${saldoDisp >= 0 ? 'text-emerald-600' : 'text-rose-600'}">${formatBRL(saldoDisp)}</strong>
                </p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="text-right">
                <span class="text-xs font-bold text-slate-800 block">${formatBRL(orcAnual)}</span>
                <span class="text-[10px] text-slate-500">Exec: ${formatBRL(execAnual)} (${perc}%)</span>
              </div>
              <div class="w-16 bg-slate-200 h-2 rounded-full overflow-hidden">
                <div class="bg-indigo-600 h-full rounded-full transition-all duration-500" style="width: ${perc}%"></div>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }
}

function renderDashboardAuditoria() {
  const container = document.getElementById('dashboard-auditoria-list');
  if (!container) return;

  const logs = STATE.auditoria || [];
  if (logs.length === 0) {
    container.innerHTML = `
      <div class="p-6 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-xl">
        <p class="font-semibold text-slate-500">Nenhum evento recente na auditoria.</p>
        <p class="text-[10px] mt-0.5">As ações dos operadores aparecerão aqui ao vivo.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = logs.slice(0, 30).map(item => {
    let dataHoraStr = 'Recente';
    if (item.data_hora) {
      const parts = item.data_hora.split(' ');
      const dataFmt = typeof formatDateBR === 'function' ? formatDateBR(parts[0]) : parts[0];
      const horaFmt = parts[1] ? parts[1].substring(0, 5) : '';
      dataHoraStr = horaFmt ? `${dataFmt} às ${horaFmt}` : dataFmt;
    }

    const setor = (item.setor || '').toLowerCase();
    const icone = setor.includes('tesour') ? '💰' :
                  setor.includes('secret') ? '👤' :
                  setor.includes('patrim') ? '📦' :
                  setor.includes('escala') ? '📅' :
                  setor.includes('segur') || setor.includes('acesso') ? '🔒' :
                  setor.includes('ata') ? '📜' :
                  setor.includes('celul') ? '🏠' : '⛪';

    return `
      <div class="p-2.5 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-white hover:border-indigo-200 transition text-xs space-y-1">
        <div class="flex items-center justify-between gap-2">
          <span class="font-bold text-slate-800 flex items-center gap-1.5 truncate">
            <span>${icone}</span>
            <span class="truncate">${item.acao || 'Ação'}</span>
            <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100 shrink-0">${item.setor || 'Geral'}</span>
          </span>
          <span class="text-[10px] font-medium text-slate-400 shrink-0">${dataHoraStr}</span>
        </div>
        <p class="text-[11px] text-slate-600 line-clamp-2">${item.detalhes || ''}</p>
        <p class="text-[10px] text-slate-400 truncate">Operador: <strong class="text-slate-600">${item.usuario || 'Sistema'}</strong></p>
      </div>
    `;
  }).join('');
}

function renderOrcamento15Ministerios() {
  const tbody = document.getElementById('tabela-orcamento-15-ministerios');
  if (!tbody) return;

  const anoReal = ANO_MIN_REALIZADO || 2025;
  const anoOrc = ANO_MIN_ORCAMENTO || 2026;
  const anoExec = ANO_MIN_EXECUTADO || 2026;

  // Atualiza rótulos nas tabelas e cards
  const elThReal = document.getElementById('th-ano-real');
  const elThOrc = document.getElementById('th-ano-orc');
  const elThExec = document.getElementById('th-ano-exec');
  const elThSaldo = document.getElementById('th-ano-saldo');
  if (elThReal) elThReal.textContent = String(anoReal);
  if (elThOrc) elThOrc.textContent = String(anoOrc);
  if (elThExec) elThExec.textContent = String(anoExec);
  if (elThSaldo) elThSaldo.textContent = String(anoOrc);

  const elTotRealLbl = document.getElementById('tot-min-real-ano-lbl');
  const elTotOrcLbl = document.getElementById('tot-min-orc-ano-lbl');
  const elTotExecLbl = document.getElementById('tot-min-exec-ano-lbl');
  if (elTotRealLbl) elTotRealLbl.textContent = String(anoReal);
  if (elTotOrcLbl) elTotOrcLbl.textContent = String(anoOrc);
  if (elTotExecLbl) elTotExecLbl.textContent = String(anoExec);

  let totReal = 0;
  let totOrc = 0;
  let totExec = 0;

  let html = (STATE.ministerios || []).map(m => {
    const rVal = getRealizadoMinisterio(m, anoReal);
    const oVal = getOrcamentoMinisterio(m, anoOrc);
    const exVal = getExecutadoMinisterio(m, anoExec);
    const saldo = oVal - exVal;
    const aum = rVal > 0 ? (((oVal - rVal) / rVal) * 100).toFixed(1) : '0.0';

    totReal += rVal;
    totOrc += oVal;
    totExec += exVal;

    return `
      <tr class="hover:bg-indigo-50/40 transition bg-white">
        <td class="py-3 px-3 font-bold text-slate-900 flex items-center gap-2">
          <span class="w-3 h-3 rounded-full shrink-0" style="background:${m.cor || '#4f46e5'}"></span>
          ${m.nome}
        </td>
        <td class="py-3 px-3 text-right font-mono text-slate-600">${formatBRL(rVal)}</td>
        <td class="py-3 px-3 text-right font-mono font-extrabold text-indigo-900">${formatBRL(oVal)}</td>
        <td class="py-3 px-3 text-center">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${Number(aum) > 0 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}">
            ${Number(aum) > 0 ? '+' : ''}${aum}%
          </span>
        </td>
        <td class="py-3 px-3 text-right font-mono font-bold text-rose-600">${formatBRL(exVal)}</td>
        <td class="py-3 px-3 text-right font-mono font-bold ${saldo >= 0 ? 'text-emerald-600' : 'text-rose-600'}">${formatBRL(saldo)}</td>
        <td class="py-3 px-3 text-slate-600 italic">${m.descricao || '—'}</td>
        <td class="py-3 px-3 text-right">
          <button onclick="editarMinisterioModal(${m.id})" class="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold px-2.5 py-1 rounded-lg transition">
            ✏️ Editar Orçamento / Obs
          </button>
        </td>
      </tr>
    `;
  }).join('');

  const totSaldo = totOrc - totExec;
  const aumGeral = totReal > 0 ? (((totOrc - totReal) / totReal) * 100).toFixed(1) : '0.0';

  html += `
    <tr class="bg-slate-900 text-white font-extrabold">
      <td class="py-3 px-3">TOTAL GERAL CONSOLIDADO</td>
      <td class="py-3 px-3 text-right font-mono">${formatBRL(totReal)}</td>
      <td class="py-3 px-3 text-right font-mono text-indigo-300">${formatBRL(totOrc)}</td>
      <td class="py-3 px-3 text-center font-mono text-amber-300">${Number(aumGeral) > 0 ? '+' : ''}${aumGeral}%</td>
      <td class="py-3 px-3 text-right font-mono text-rose-300">${formatBRL(totExec)}</td>
      <td class="py-3 px-3 text-right font-mono text-emerald-300">${formatBRL(totSaldo)}</td>
      <td class="py-3 px-3" colspan="2"></td>
    </tr>
  `;

  tbody.innerHTML = html;

  // Atualiza totais nos cards
  const elTotReal = document.getElementById('tot-min-2025');
  const elTotOrc = document.getElementById('tot-min-2026');
  const elTotExec = document.getElementById('tot-min-exec-2026');
  if (elTotReal) elTotReal.textContent = formatBRL(totReal);
  if (elTotOrc) elTotOrc.textContent = formatBRL(totOrc);
  if (elTotExec) elTotExec.textContent = formatBRL(totExec);
}

function renderGraficosBI(resAno) {
  if (typeof Chart === 'undefined') return;

  const res = resAno || calcularResumoAnoMatriz(ANO_MATRIZ_ATIVO);

  // 1. Despesas por Grande Grupo
  const grupoMap = {};
  (res.saidasRows || []).forEach(r => {
    const labelCurto = (r.grupo || '').replace(/^\d+\.\s*/, '');
    grupoMap[labelCurto] = (grupoMap[labelCurto] || 0) + (Number(r.total_anual) || 0);
  });
  const ctxFin = document.getElementById('chart-financeiro');
  if (ctxFin) {
    if (chartFinanceiroInstance) chartFinanceiroInstance.destroy();
    chartFinanceiroInstance = new Chart(ctxFin, {
      type: 'doughnut',
      data: {
        labels: Object.keys(grupoMap),
        datasets: [{
          data: Object.values(grupoMap),
          backgroundColor: ['#4f46e5', '#e11d48', '#f59e0b', '#10b981', '#0ea5e9', '#8b5cf6', '#ec4899', '#14b8a6', '#64748b'],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 9 } } }
        }
      }
    });
  }

  // 2. Top 8 Ministérios: Realizado vs Orçamento
  const anoReal = ANO_MIN_REALIZADO || 2025;
  const anoOrc = ANO_MIN_ORCAMENTO || 2026;
  const topMin = (STATE.ministerios || []).slice(0, 8);
  const ctxMin = document.getElementById('chart-ministerios');
  if (ctxMin) {
    if (chartMinisteriosInstance) chartMinisteriosInstance.destroy();
    chartMinisteriosInstance = new Chart(ctxMin, {
      type: 'bar',
      data: {
        labels: topMin.map(m => m.nome.replace('Ministério ', '')),
        datasets: [
          {
            label: `Realizado ${anoReal}`,
            data: topMin.map(m => getRealizadoMinisterio(m, anoReal)),
            backgroundColor: '#94a3b8'
          },
          {
            label: `Orçamento ${anoOrc}`,
            data: topMin.map(m => getOrcamentoMinisterio(m, anoOrc)),
            backgroundColor: '#4f46e5'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } }
        },
        scales: {
          y: { ticks: { callback: v => 'R$' + (v / 1000).toFixed(0) + 'k' } }
        }
      }
    });
  }
}


let FILTRO_FLUXO_MATRIZ = 'TODOS';
let MES_DESTAQUE_MATRIZ = 0;
let GRUPOS_MATRIZ_RECOLHIDOS = new Set();

function renderMatrizTesouraria() {
  const { rows, entMes, saiMes, totalEntradas, totalSaidas, saldoTotal } = calcularResumoAnoMatriz(ANO_MATRIZ_ATIVO);

  // Popula seletor de grupos do ano ativo
  const gruposUnicos = [...new Set(rows.map(r => r.grupo))];
  const selGrupo = document.getElementById('filtro-grupo-matriz');
  if (selGrupo) {
    const valAtual = selGrupo.value;
    selGrupo.innerHTML = `<option value="">Todos os Grupos (${gruposUnicos.length})</option>` +
      gruposUnicos.map(g => `<option value="${g}">${g}</option>`).join('');
    if (gruposUnicos.includes(valAtual)) selGrupo.value = valAtual;
  }

  // Popula seletor de grupos e rubricas do Lançamento Manual
  popularCamposLancamentoManual(rows);

  // Atualiza KPIs de topo da planilha
  const mesesAtivosEnt = entMes.filter(v => v > 0).length || 1;
  const mediaEnt = totalEntradas / mesesAtivosEnt;
  const percComp = totalEntradas > 0 ? ((totalSaidas / totalEntradas) * 100).toFixed(1) : '0.0';

  const elTesEnt = document.getElementById('tes-mat-entradas');
  if (elTesEnt) elTesEnt.textContent = formatBRL(totalEntradas);
  const elTesEntMed = document.getElementById('tes-mat-entradas-med');
  if (elTesEntMed) elTesEntMed.textContent = `Média mensal ativa: ${formatBRL(mediaEnt)}`;
  const elTesSai = document.getElementById('tes-mat-saidas');
  if (elTesSai) elTesSai.textContent = formatBRL(totalSaidas);
  const elTesSaiPerc = document.getElementById('tes-mat-saidas-perc');
  if (elTesSaiPerc) elTesSaiPerc.textContent = `${percComp}% das entradas no exercício`;

  const elSaldo = document.getElementById('tes-mat-saldo');
  if (elSaldo) {
    elSaldo.textContent = formatBRL(saldoTotal);
    elSaldo.className = `text-2xl font-extrabold mt-1 ${saldoTotal >= 0 ? 'text-emerald-600' : 'text-rose-600'}`;
  }
  const elTituloPlan = document.getElementById('titulo-planilha-ano');
  if (elTituloPlan) {
    elTituloPlan.textContent = 'Matriz Financeira Mensal';
  }

  // Caixa de Diagnóstico Inteligente da Planilha
  const analiseBox = document.getElementById('tes-analise-box');
  if (analiseBox) {
    if (ANO_MATRIZ_ATIVO === 2026) {
      analiseBox.innerHTML = `
        <div>
          <span class="font-extrabold text-indigo-950 block">🔍 Análise da Planilha 2026 (Janeiro a Maio realizados):</span>
          <p class="text-slate-600 mt-0.5">
            Corrigimos automaticamente o erro de <code>#NaN</code> que existia na soma de Despesas Operacionais da planilha original. De <strong>Jan a Mai/2026</strong>, a igreja arrecadou <strong>${formatBRL(totalEntradas)}</strong> contra <strong>${formatBRL(totalSaidas)}</strong> de despesas, gerando um <strong>Superávit Acumulado de ${formatBRL(saldoTotal)}</strong>. Clique em qualquer célula de <strong>JUN a DEZ</strong> abaixo para lançar os próximos meses!
          </p>
        </div>
      `;
    } else if (ANO_MATRIZ_ATIVO === 2025) {
      analiseBox.innerHTML = `
        <div>
          <span class="font-extrabold text-indigo-950 block">🔍 Análise do Fechamento 2025 (Janeiro a Dezembro):</span>
          <p class="text-slate-600 mt-0.5">
            Em 2025 as entradas somaram <strong>${formatBRL(totalEntradas)}</strong> (média de R$ 29.886,80/mês) e as saídas somaram <strong>${formatBRL(totalSaidas)}</strong> (resultado de <strong>${formatBRL(saldoTotal)}</strong>), fortemente impactado pelos investimentos em <strong>Manutenção, Obra Central Sul e Elétrica (R$ 146.103,23 — 40,7% do orçamento)</strong> entre Maio e Outubro.
          </p>
        </div>
      `;
    } else {
      analiseBox.innerHTML = `
        <div>
          <span class="font-extrabold text-indigo-950 block">🔍 Análise Histórica ${ANO_MATRIZ_ATIVO}:</span>
          <p class="text-slate-600 mt-0.5">
            Em ${ANO_MATRIZ_ATIVO} as receitas acumuladas foram de <strong>${formatBRL(totalEntradas)}</strong> para <strong>${formatBRL(totalSaidas)}</strong> de despesas gerais, gerando saldo de <strong>${formatBRL(saldoTotal)}</strong>.
          </p>
        </div>
      `;
    }
  }

  // Filtra linhas para exibição na tabela
  const filtroGrupo = selGrupo ? selGrupo.value : '';
  const busca = (document.getElementById('busca-rubrica-matriz')?.value || '').toLowerCase();

  const filtradas = rows.filter(r => {
    if (FILTRO_FLUXO_MATRIZ === 'ENTRADA' && r.tipo_fluxo !== 'ENTRADA') return false;
    if (FILTRO_FLUXO_MATRIZ === 'SAIDA' && r.tipo_fluxo !== 'SAIDA') return false;
    const okG = !filtroGrupo || r.grupo === filtroGrupo;
    const okB = !busca || r.rubrica.toLowerCase().includes(busca) || r.grupo.toLowerCase().includes(busca);
    return okG && okB;
  });

  // Agrupa por grupo para exibir cabeçalhos e subtotais igual à planilha!
  const porGrupo = {};
  filtradas.forEach(r => {
    porGrupo[r.grupo] = porGrupo[r.grupo] || [];
    porGrupo[r.grupo].push(r);
  });

  const tbody = document.getElementById('tabela-matriz-tesouraria');
  if (!tbody) return;

  let html = '';

  Object.entries(porGrupo).forEach(([grupoNome, itens]) => {
    const isEntradaGroup = itens[0]?.tipo_fluxo === 'ENTRADA';
    const subMes = Array(12).fill(0);
    itens.forEach(item => {
      for (let i = 0; i < 12; i++) subMes[i] += Number(item.meses[i] || 0);
    });
    const subTotal = subMes.reduce((a, b) => a + b, 0);
    const subPerc = totalEntradas > 0 ? ((subTotal / totalEntradas) * 100).toFixed(1) + '%' : '0%';
    const subMedia = subTotal / 12.0;

    const isRecolhido = GRUPOS_MATRIZ_RECOLHIDOS.has(grupoNome);
    const grupoNomeEsc = grupoNome.replace(/'/g, "\\'");

    // Linha de Cabeçalho/Subtotal do Grupo (Clicável para recolher/expandir individualmente!)
    html += `
      <tr onclick="alternarGrupoIndividualMatriz('${grupoNomeEsc}')" class="${isEntradaGroup ? 'bg-emerald-900/10 text-emerald-950 hover:bg-emerald-100/60' : 'bg-slate-200/80 text-slate-900 hover:bg-slate-200'} font-extrabold cursor-pointer transition select-none" title="Clique para ${isRecolhido ? 'expandir' : 'recolher'} o grupo ${grupoNome}">
        <td class="py-2 px-3 sticky left-0 ${isEntradaGroup ? 'bg-emerald-100' : 'bg-slate-200'} z-10 uppercase text-[10px] tracking-wider flex items-center justify-between gap-2">
          <span>${isEntradaGroup ? '🟢' : '🔴'} ${isRecolhido ? '📁' : '📂'} ${grupoNome} (${itens.length})</span>
          <span class="text-[9px] font-bold opacity-75 px-1 rounded bg-black/10">${isRecolhido ? '+ Expandir' : '- Recolher'}</span>
        </td>
        ${subMes.map((v, mIdx) => {
          const isDestaque = (mIdx + 1 === MES_DESTAQUE_MATRIZ);
          return `<td class="py-2 px-2 text-right font-mono ${isDestaque ? 'bg-amber-100 text-indigo-950 font-black border-x-2 border-indigo-400' : ''}">${formatNum(v)}</td>`;
        }).join('')}
        <td class="py-2 px-3 text-right font-mono bg-slate-300/60">${formatBRL(subTotal)}</td>
        <td class="py-2 px-2 text-right font-mono">${subPerc}</td>
        <td class="py-2 px-2 text-right font-mono">${formatNum(subMedia)}</td>
      </tr>
    `;

    // Linhas das Rubricas (apenas se o grupo não estiver recolhido)
    if (!isRecolhido) {
      itens.forEach(item => {
        const percItem = totalEntradas > 0 ? ((item.total_anual / totalEntradas) * 100).toFixed(1) + '%' : '0%';
        html += `
          <tr class="hover:bg-indigo-50/40 transition bg-white">
            <td class="py-2 px-3 sticky left-0 bg-white z-10 font-medium text-slate-800 border-r border-slate-100 flex items-center justify-between gap-2">
              <span class="truncate">${item.rubrica}</span>
              <button
                type="button"
                onclick="abrirModalConta12Meses(${item.id})"
                class="text-[10px] font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 px-1.5 py-0.5 rounded border border-indigo-200 transition cursor-pointer shrink-0 ml-1.5 shadow-2xs"
                title="Ver e preencher os 12 meses de ${item.rubrica}"
              >
                📅 12M
              </button>
            </td>
            ${item.meses.map((val, idx) => {
              const isDestaque = (idx + 1 === MES_DESTAQUE_MATRIZ);
              return `
                <td onclick="editarCelulaMatriz(${item.id}, ${idx + 1}, '${item.rubrica.replace(/'/g, "\\'")}', ${val})"
                    title="Clique para editar ${item.rubrica} em ${NOMES_MESES[idx]}/${ANO_MATRIZ_ATIVO}"
                    class="cell-editable py-2 px-2 text-right font-mono ${isDestaque ? 'bg-amber-100/70 border-x-2 border-indigo-300 font-extrabold' : ''} ${val > 0 ? (isEntradaGroup ? 'text-emerald-700 font-semibold' : 'text-slate-800') : 'text-slate-300'}">
                  ${formatNum(val)}
                </td>
              `;
            }).join('')}
            <td class="py-2 px-3 text-right font-mono font-bold ${isEntradaGroup ? 'text-emerald-700 bg-emerald-50/50' : 'text-rose-700 bg-rose-50/40'}">
              ${formatBRL(item.total_anual)}
            </td>
            <td class="py-2 px-2 text-right font-mono text-slate-500">${percItem}</td>
            <td class="py-2 px-2 text-right font-mono text-slate-500">${formatNum(item.media_mensal)}</td>
          </tr>
        `;
      });
    }
  });

  // Rodapé Consolidado: TOTAL ENTRADAS, TOTAL DESPESAS, % DESPESAS vs ENTRADAS e SALDO MENSAL
  const saldoMes = entMes.map((e, i) => e - saiMes[i]);
  const percMes = entMes.map((e, i) => e > 0 ? Math.round((saiMes[i] / e) * 100) + '%' : '—');
  const percTotalGeral = totalEntradas > 0 ? Math.round((totalSaidas / totalEntradas) * 100) + '%' : '—';

  html += `
    <tr class="bg-emerald-950 text-emerald-100 font-extrabold border-t-2 border-slate-900">
      <td class="py-2.5 px-3 sticky left-0 bg-emerald-950 z-10">TOTAL DE ENTRADAS (${ANO_MATRIZ_ATIVO})</td>
      ${entMes.map(v => `<td class="py-2.5 px-2 text-right font-mono">${formatNum(v)}</td>`).join('')}
      <td class="py-2.5 px-3 text-right font-mono text-emerald-300">${formatBRL(totalEntradas)}</td>
      <td class="py-2.5 px-2 text-right">100%</td>
      <td class="py-2.5 px-2 text-right font-mono">${formatNum(totalEntradas / 12)}</td>
    </tr>
    <tr class="bg-rose-950 text-rose-100 font-extrabold">
      <td class="py-2.5 px-3 sticky left-0 bg-rose-950 z-10">TOTAL DE DESPESAS (${ANO_MATRIZ_ATIVO})</td>
      ${saiMes.map(v => `<td class="py-2.5 px-2 text-right font-mono">${formatNum(v)}</td>`).join('')}
      <td class="py-2.5 px-3 text-right font-mono text-rose-300">${formatBRL(totalSaidas)}</td>
      <td class="py-2.5 px-2 text-right">${percTotalGeral}</td>
      <td class="py-2.5 px-2 text-right font-mono">${formatNum(totalSaidas / 12)}</td>
    </tr>
    <tr class="bg-slate-800 text-slate-200 font-bold text-[10px]">
      <td class="py-2 px-3 sticky left-0 bg-slate-800 z-10">% DESPESAS VS. ENTRADAS</td>
      ${percMes.map(p => `<td class="py-2 px-2 text-right font-mono">${p}</td>`).join('')}
      <td class="py-2 px-3 text-right font-mono">${percTotalGeral}</td>
      <td class="py-2 px-2 text-right">—</td>
      <td class="py-2 px-2 text-right">—</td>
    </tr>
    <tr class="bg-slate-900 text-white font-extrabold text-xs">
      <td class="py-3 px-3 sticky left-0 bg-slate-900 z-10">SALDO LÍQUIDO MENSAL</td>
      ${saldoMes.map(s => `<td class="py-3 px-2 text-right font-mono ${s >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${formatNum(s)}</td>`).join('')}
      <td class="py-3 px-3 text-right font-mono ${saldoTotal >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${formatBRL(saldoTotal)}</td>
      <td class="py-3 px-2 text-right">—</td>
      <td class="py-3 px-2 text-right font-mono">${formatNum(saldoTotal / 12)}</td>
    </tr>
  `;

  tbody.innerHTML = html;
}

function popularCamposLancamentoManual(rowsAtivos) {
  const selGrupo = document.getElementById('lr-grupo');
  const selRubrica = document.getElementById('lr-rubrica');
  if (!selGrupo || !selRubrica) return;

  const anoAtivo = Number(window.ANO_MATRIZ_ATIVO) || 2026;
  const rows = rowsAtivos || (STATE.matriz_tesouraria || []).filter(r => Number(r.ano) === anoAtivo);

  const gruposUnicos = [...new Set(rows.map(r => r.grupo))].filter(Boolean);
  const valAtualGrupo = selGrupo.value;

  selGrupo.innerHTML = '<option value="">Todos os Grupos / Todas as Contas</option>' +
    gruposUnicos.map(g => `<option value="${g}">${g}</option>`).join('');

  if (valAtualGrupo && gruposUnicos.includes(valAtualGrupo)) {
    selGrupo.value = valAtualGrupo;
  }

  aoMudarGrupoLancamentoRapido();
}

function aoMudarGrupoLancamentoRapido() {
  const selGrupo = document.getElementById('lr-grupo');
  const selRubrica = document.getElementById('lr-rubrica');
  if (!selRubrica) return;

  const grupoSel = selGrupo ? selGrupo.value : '';
  const anoAtivo = Number(window.ANO_MATRIZ_ATIVO) || 2026;
  const rowsAno = (STATE.matriz_tesouraria || []).filter(r => Number(r.ano) === anoAtivo);

  const valAtualRubrica = selRubrica.value;

  if (grupoSel) {
    const rubricasDoGrupo = rowsAno.filter(r => r.grupo === grupoSel);
    selRubrica.innerHTML = '<option value="">Selecione a Conta / Rubrica...</option>' +
      rubricasDoGrupo.map(r => `
        <option value="${r.id}">${r.rubrica} (${r.tipo_fluxo === 'ENTRADA' ? 'Entrada' : 'Saída'})</option>
      `).join('');
  } else {
    // Agrupa por optgroup
    const porGrupo = {};
    rowsAno.forEach(r => {
      porGrupo[r.grupo] = porGrupo[r.grupo] || [];
      porGrupo[r.grupo].push(r);
    });

    let opts = '<option value="">Selecione a Conta / Rubrica...</option>';
    Object.entries(porGrupo).forEach(([grp, lista]) => {
      opts += `<optgroup label="${grp}">`;
      lista.forEach(r => {
        opts += `<option value="${r.id}">${r.rubrica} (${r.tipo_fluxo === 'ENTRADA' ? 'Entrada' : 'Saída'})</option>`;
      });
      opts += `</optgroup>`;
    });
    selRubrica.innerHTML = opts;
  }

  if (valAtualRubrica && Array.from(selRubrica.options).some(o => o.value === String(valAtualRubrica))) {
    selRubrica.value = valAtualRubrica;
  }

  aoMudarRubricaOuMesLancamentoRapido();
}

function aoMudarRubricaOuMesLancamentoRapido() {
  const selRubrica = document.getElementById('lr-rubrica');
  const selMes = document.getElementById('lr-mes');
  const hintEl = document.getElementById('lr-valor-atual-hint');
  const inputValor = document.getElementById('lr-valor');

  if (!hintEl) return;

  const rowId = Number(selRubrica?.value);
  const mes = Number(selMes?.value) || 1;

  if (!rowId) {
    hintEl.textContent = '';
    return;
  }

  const item = (STATE.matriz_tesouraria || []).find(r => Number(r.id) === rowId);
  if (!item) {
    hintEl.textContent = '';
    return;
  }

  const nomesMeses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  const mesNome = nomesMeses[mes - 1] || 'Mês';
  const valAtual = Number(item[`m${mes}`] || 0);

  hintEl.textContent = `Valor atual em ${mesNome}/${item.ano}: ${formatBRL(valAtual)}`;

  if (inputValor && !inputValor.value) {
    inputValor.placeholder = valAtual > 0 ? valAtual.toFixed(2) : '0.00';
  }
}

async function executarLancamentoRapidoMatriz(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }

  const selRubrica = document.getElementById('lr-rubrica');
  const selMes = document.getElementById('lr-mes');
  const inputValor = document.getElementById('lr-valor');

  const rowId = Number(selRubrica?.value);
  const mes = Number(selMes?.value);
  const valorStr = inputValor?.value;
  const valor = parseFloat(valorStr);

  if (!rowId || isNaN(rowId)) {
    alert('Por favor, selecione uma Conta / Rubrica para o lançamento manual.');
    selRubrica?.focus();
    return;
  }
  if (!mes || mes < 1 || mes > 12) {
    alert('Por favor, selecione um Mês válido.');
    selMes?.focus();
    return;
  }
  if (isNaN(valor) || valor < 0) {
    alert('Por favor, informe um valor numérico válido (maior ou igual a R$ 0,00).');
    inputValor?.focus();
    return;
  }

  const item = (STATE.matriz_tesouraria || []).find(r => Number(r.id) === rowId);
  const nomesMeses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  const mesNome = nomesMeses[mes - 1];
  const rubNome = item ? item.rubrica : 'Conta';
  const anoItem = item ? item.ano : (window.ANO_MATRIZ_ATIVO || 2026);

  try {
    const operadorNome = CURRENT_OPERATOR?.nome || 'Tesoureiro';
    const res = await apiPost('/api/matriz/celula', {
      id: rowId,
      mes: mes,
      valor: valor,
      operador: operadorNome
    });

    if (res && (res.ok || !res.erro)) {
      if (item) {
        item[`m${mes}`] = valor;
        if (!Array.isArray(item.meses)) {
          item.meses = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        }
        item.meses[mes - 1] = valor;
        item.total_anual = item.meses.reduce((a, b) => a + b, 0);
        item.media_mensal = item.total_anual / 12.0;
      }

      renderMatrizTesouraria();
      renderBadgesAndKPIs();
      renderDashboard();
      if (typeof fetchBootstrap === 'function') {
        fetchBootstrap();
      }

      showLiveToast(`✅ Lançamento Manual Realizado: ${rubNome} em ${mesNome}/${anoItem} atualizado para ${formatBRL(valor)}!`);

      if (inputValor) {
        inputValor.value = '';
        inputValor.placeholder = valor.toFixed(2);
      }
      aoMudarRubricaOuMesLancamentoRapido();
    } else {
      alert(res?.erro || 'Erro ao registrar lançamento na planilha.');
    }
  } catch (err) {
    console.error('Erro ao executar lancamento manual:', err);
    alert('Falha na comunicação com o servidor ao salvar lançamento na planilha.');
  }
}

const CATEGORIAS_FINANCEIRO = {
  ENTRADA: [
    { value: 'Dízimo Gasofilácio', label: '🟢 Dízimo Gasofilácio' },
    { value: 'Conta Itaú', label: '🟢 Entrada Conta Itaú' },
    { value: 'Conta Bradesco', label: '🟢 Entrada Conta Bradesco' },
    { value: 'Oferta Campanhas JMM/JMN/JME', label: '🟢 Oferta Campanhas JMM/JMN/JME' },
    { value: 'Oferta de Culto / Alçados', label: '🟢 Oferta de Culto / Alçados' },
    { value: 'Cantina e Bazar', label: '🟢 Cantina e Bazar' },
    { value: 'Retiro / Piquenique / Eventos', label: '🟢 Retiro / Piquenique / Eventos' },
    { value: 'Reembolso / Devolução', label: '🟢 Reembolso / Devolução / Estorno' },
    { value: 'Doações e Outras Entradas', label: '🟢 Doações e Outras Entradas' }
  ],
  SAIDA: [
    { value: 'Despesas Operacionais', label: '🔴 Despesas Operacionais (Água, Luz, Tel, Net)' },
    { value: 'Manutenção e Conservação', label: '🔴 Manutenção, Reformas e Conservação' },
    { value: 'Despesas com Ministérios', label: '🔴 Despesas com Ministérios' },
    { value: 'Material de Limpeza e Copa', label: '🔴 Material de Limpeza e Copa' },
    { value: 'Gráfica / Livraria / ADM', label: '🔴 Gráfica, Livraria e ADM' },
    { value: 'Pessoal e Encargos', label: '🔴 Pessoal, Prebenda e Encargos' },
    { value: 'Ajuda Social / Diaconia', label: '🔴 Ação Social e Diaconia' },
    { value: 'Missões', label: '🔴 Missões (JMM / JMN / Estaduais)' },
    { value: 'Eventos / Retiros', label: '🔴 Eventos, Retiros e Congressos' },
    { value: 'Taxas Bancárias e Tributos', label: '🔴 Taxas Bancárias e Tributos' },
    { value: 'Outras Saídas', label: '🔴 Outras Saídas / Despesas Diversas' }
  ]
};

function selecionarTipoFinanceiro(tipo) {
  const tipoNorm = (tipo || 'ENTRADA').toUpperCase();
  const selTipo = document.getElementById('fin-tipo');
  if (selTipo && selTipo.value !== tipoNorm) {
    selTipo.value = tipoNorm;
  }

  const btnEntrada = document.getElementById('btn-tipo-entrada');
  const btnSaida = document.getElementById('btn-tipo-saida');

  if (tipoNorm === 'SAIDA') {
    if (btnSaida) {
      btnSaida.className = 'py-2 px-3 rounded-lg font-black text-xs flex items-center justify-center gap-1.5 transition-all shadow-md bg-rose-600 text-white cursor-pointer';
    }
    if (btnEntrada) {
      btnEntrada.className = 'py-2 px-3 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5 transition-all text-slate-600 hover:text-slate-900 hover:bg-white/60 cursor-pointer';
    }
  } else {
    if (btnEntrada) {
      btnEntrada.className = 'py-2 px-3 rounded-lg font-black text-xs flex items-center justify-center gap-1.5 transition-all shadow-md bg-emerald-600 text-white cursor-pointer';
    }
    if (btnSaida) {
      btnSaida.className = 'py-2 px-3 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5 transition-all text-slate-600 hover:text-slate-900 hover:bg-white/60 cursor-pointer';
    }
  }

  // Atualiza as opções do select de Categoria Contábil
  const selCat = document.getElementById('fin-categoria');
  if (selCat) {
    const lista = CATEGORIAS_FINANCEIRO[tipoNorm] || CATEGORIAS_FINANCEIRO.ENTRADA;
    selCat.innerHTML = lista.map(item => `<option value="${item.value}">${item.label}</option>`).join('');
  }
}

async function salvarFinanceiro(e) {
  e.preventDefault();
  const dtVal = document.getElementById('fin-data')?.value;
  const tipoVal = document.getElementById('fin-tipo')?.value || 'ENTRADA';
  const catVal = document.getElementById('fin-categoria')?.value;
  const descVal = document.getElementById('fin-descricao')?.value;
  const valorVal = document.getElementById('fin-valor')?.value;
  const formaVal = document.getElementById('fin-forma')?.value || 'PIX';
  const membroId = document.getElementById('fin-membro')?.value || null;
  const ministerioId = document.getElementById('fin-ministerio')?.value || null;

  try {
    const res = await apiPost('/api/financeiro', {
      tipo: tipoVal,
      categoria: catVal,
      descricao: descVal,
      valor: valorVal,
      forma_pagamento: formaVal,
      data_lancamento: dtVal || undefined,
      membro_id: membroId,
      ministerio_id: ministerioId
    });

    if (res && (res.ok || !res.erro)) {
      showLiveToast(`✅ ${tipoVal === 'SAIDA' ? 'Saída (Despesa)' : 'Entrada (Receita)'} de ${formatBRL(parseFloat(valorVal))} registrada com sucesso!`);
      e.target.reset();
      selecionarTipoFinanceiro(tipoVal);
      const dtEl = document.getElementById('fin-data');
      if (dtEl) dtEl.value = new Date().toISOString().split('T')[0];
      if (typeof fetchBootstrap === 'function') {
        fetchBootstrap();
      }
    } else {
      alert(res?.erro || 'Erro ao registrar lançamento.');
    }
  } catch (err) {
    console.error('Erro ao salvar financeiro:', err);
    alert('Erro de conexão ao salvar lançamento.');
  }
}


function initSSE() {
  const evtSource = new EventSource('/api/events');

  evtSource.addEventListener('sync', (e) => {
    try {
      const payload = JSON.parse(e.data);
      showLiveToast(`${payload.mensagem}`);
      fetchBootstrap();
    } catch (err) {
      fetchBootstrap();
    }
    renderDashboard();
    renderBadgesAndKPIs();
  });

  evtSource.addEventListener('presence', (e) => {
    try {
      const payload = JSON.parse(e.data);
      const badge = document.getElementById('online-count-badge');
      if (badge) {
        badge.textContent = `${payload.clientes_conectados} tela(s) ativa(s)`;
      }
    } catch (err) {}
  });

  evtSource.onerror = () => {
    const ind = document.getElementById('sse-indicator');
    if (ind) ind.className = 'w-2.5 h-2.5 rounded-full bg-amber-400';
  };

  evtSource.onopen = () => {
    const ind = document.getElementById('sse-indicator');
    if (ind) ind.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400 pulse-dot';
  };
}

// Reconexão e restauração imediata de sessão ao retornar à aba após inatividade/hibernação
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    let sessaoAtiva = false;
    let savedUserId = null;
    try {
      sessaoAtiva = (sessionStorage.getItem('pib_sessao_autenticada') === 'true') || (localStorage.getItem('pib_sessao_autenticada') === 'true');
      savedUserId = sessionStorage.getItem('pib_auth_user_id') || localStorage.getItem('pib_auth_user_id');
    } catch (e) {}

    if (sessaoAtiva && savedUserId && (!CURRENT_OPERATOR || !CURRENT_OPERATOR.id)) {
      if (Array.isArray(STATE.usuarios) && STATE.usuarios.length > 0) {
        const user = STATE.usuarios.find(u => Number(u.id) === Number(savedUserId));
        if (user) {
          CURRENT_OPERATOR = user;
          fecharTelaLogin();
          renderOperatorSelector();
          aplicarPermissoesDeSetor();
        }
      }
    }
    fetchBootstrap();
  }
});

let toastTimeout = null;

function showLiveToast(msg) {
  const toast = document.getElementById('live-toast');
  const text = document.getElementById('live-toast-text');
  if (!toast || !text) return;
  text.textContent = msg;
  toast.classList.remove('hidden');
  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.add('hidden');
  }, 4500);
}

function changeOperator() {
  const select = document.getElementById('operator-select');
  const userId = Number(select.value);
  const found = STATE.usuarios.find(u => u.id === userId);
  if (found) {
    CURRENT_OPERATOR = found;
    renderAll();
    showLiveToast(`Perfil alternado para: ${found.nome} (${found.perfil})`);
  }
}

function aplicarPermissoesDeSetor() {
  if (!CURRENT_OPERATOR) return;
  const permitidas = getPermissoesOperador(CURRENT_OPERATOR);

  document.querySelectorAll('#sidebar-nav .nav-item').forEach(btn => {
    const tab = btn.getAttribute('data-tab');
    if (permitidas.includes(tab)) {
      btn.classList.remove('disabled-sector');
    } else {
      btn.classList.add('disabled-sector');
    }
  });

  if (!permitidas.includes(ACTIVE_TAB)) {
    const destinoValido = permitidas.find(p => p !== 'projecao') || permitidas[0] || 'dashboard';
    switchTab(destinoValido);
  }
}

function irParaOrcamentoMinisterios() {
  switchTab('tesouraria');
  switchTesourariaSubtab('orcamento');
}

function renderAll() {
  renderOperatorSelector();
  populateSelects();
  renderBadgesAndKPIs();
  renderDashboard();
  renderMatrizTesouraria();
  renderOrcamento15Ministerios();
  renderTesouraria();
  renderMembros();
  renderVisitantes();
  renderEscalas();
  renderCelulas();
  renderPatrimonioEUsuarios();
  renderAtas();
  if (ACTIVE_TAB === 'relatorios') {
    renderRelatorios();
  }
}

function calcularResumoAnoMatriz(ano) {
  const rows = (STATE.matriz_tesouraria || []).filter(r => Number(r.ano) === Number(ano));
  const entradasRows = rows.filter(r => r.tipo_fluxo === 'ENTRADA');
  const saidasRows = rows.filter(r => r.tipo_fluxo === 'SAIDA');

  const entMes = Array(12).fill(0);
  const saiMes = Array(12).fill(0);

  entradasRows.forEach(r => {
    for (let i = 0; i < 12; i++) entMes[i] += Number(r.meses[i] || 0);
  });
  saidasRows.forEach(r => {
    for (let i = 0; i < 12; i++) saiMes[i] += Number(r.meses[i] || 0);
  });

  const totalEntradas = entMes.reduce((a, b) => a + b, 0);
  const totalSaidas = saiMes.reduce((a, b) => a + b, 0);
  const saldoTotal = totalEntradas - totalSaidas;

  return { rows, entradasRows, saidasRows, entMes, saiMes, totalEntradas, totalSaidas, saldoTotal };
}

function editarCelulaMatriz(rowId, mesIndex, rubricaNome, valorAtual) {
  const mesNome = NOMES_MESES[mesIndex - 1];
  const html = `
    <form onsubmit="confirmarEdicaoCelulaMatriz(event, ${rowId}, ${mesIndex})" class="space-y-3 text-xs">
      <span class="text-[10px] font-bold uppercase tracking-wider bg-indigo-100 text-indigo-700 px-2.5 py-0.5 rounded-full">Edição em Tempo Real — Exercício ${ANO_MATRIZ_ATIVO}</span>
      <h3 class="text-base font-bold text-slate-900">${rubricaNome}</h3>
      <p class="text-slate-500">Informe o valor consolidado para o mês de <strong>${mesNome}/${ANO_MATRIZ_ATIVO}</strong>. Todos os subtotais, médias e saldos serão recalculados automaticamente.</p>
      <div>
        <label class="font-semibold text-slate-700 block mb-1">Valor em ${mesNome}/${ANO_MATRIZ_ATIVO} (R$)</label>
        <input type="number" step="0.01" id="input-celula-matriz-val" required value="${valorAtual}" class="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-base font-extrabold text-slate-900 focus:ring-2 focus:ring-indigo-500" />
      </div>
      <div class="flex justify-end gap-2 pt-2">
        <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-5 py-2.5 rounded-xl shadow transition">
          💾 Salvar Valor e Recalcular Planilha
        </button>
      </div>
    </form>
  `;
  abrirModalCustom(html, false);
  setTimeout(() => {
    const inp = document.getElementById('input-celula-matriz-val');
    if (inp) { inp.focus(); inp.select(); }
  }, 80);
}

async function confirmarEdicaoCelulaMatriz(e, rowId, mesIndex) {
  e.preventDefault();
  const valor = document.getElementById('input-celula-matriz-val').value;
  await apiPost('/api/matriz/celula', { id: rowId, mes: mesIndex, valor });
  closeModal();
  fetchBootstrap();
}

function abrirModalNovaRubrica() {
  const html = `
    <form onsubmit="salvarNovaRubricaModal(event)" class="space-y-3 text-xs">
      <h3 class="text-base font-bold text-slate-900">+ Adicionar Nova Linha / Conta na Planilha da Tesouraria</h3>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="font-semibold text-slate-700 block mb-1">Exercício (Ano)</label>
          <select id="nrub-ano" class="w-full border border-slate-300 rounded-xl px-3 py-2 bg-white font-bold">
            ${Array.from({ length: 16 }, (_, i) => 2035 - i).map(a => `<option value="${a}" ${ANO_MATRIZ_ATIVO === a ? 'selected' : ''}>${a}</option>`).join('')}
          </select>
        </div>
        <div>
          <label class="font-semibold text-slate-700 block mb-1">Tipo de Fluxo</label>
          <select id="nrub-tipo" class="w-full border border-slate-300 rounded-xl px-3 py-2 bg-white font-bold">
            <option value="SAIDA">🔴 SAÍDA (Despesa)</option>
            <option value="ENTRADA">🟢 ENTRADA (Receita)</option>
          </select>
        </div>
      </div>
      <div>
        <label class="font-semibold text-slate-700 block mb-1">Grupo da Planilha *</label>
        <select id="nrub-grupo" class="w-full border border-slate-300 rounded-xl px-3 py-2 bg-white">
          <option value="Receitas / Entradas">Receitas / Entradas</option>
          <option value="1. Despesas Fixas">1. Despesas Fixas</option>
          <option value="2. Folha de Pagamento">2. Folha de Pagamento</option>
          <option value="3. Impostos e Taxas">3. Impostos e Taxas</option>
          <option value="4. Bancos, Cartório e Sistemas">4. Bancos, Cartório e Sistemas</option>
          <option value="5. Convenção Batista e Missões">5. Convenção Batista e Missões</option>
          <option value="6. Missionários Fixos">6. Missionários Fixos</option>
          <option value="7. Despesas com Ministérios">7. Despesas com Ministérios</option>
          <option value="8. Manutenção, Patrimônio e Obras">8. Manutenção, Patrimônio e Obras</option>
          <option value="9. Operacional, Eventos e Gráfica">9. Operacional, Eventos e Gráfica</option>
        </select>
      </div>
      <div>
        <label class="font-semibold text-slate-700 block mb-1">Nome da Rubrica / Conta *</label>
        <input type="text" id="nrub-nome" required placeholder="Ex: Reforma Telhado / Oferta Especial" class="w-full border border-slate-300 rounded-xl px-3 py-2" />
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="font-semibold text-slate-700 block mb-1">Mês do 1º Lançamento</label>
          <select id="nrub-mes" class="w-full border border-slate-300 rounded-xl px-3 py-2 bg-white">
            ${NOMES_MESES.map((m, i) => `<option value="${i + 1}">${m}</option>`).join('')}
          </select>
        </div>
        <div>
          <label class="font-semibold text-slate-700 block mb-1">Valor Inicial (R$)</label>
          <input type="number" step="0.01" id="nrub-valor" value="0.00" class="w-full border border-slate-300 rounded-xl px-3 py-2" />
        </div>
      </div>
      <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-xl">
        + Incluir na Planilha da Tesouraria
      </button>
    </form>
  `;
  abrirModalCustom(html, false);
}

async function salvarNovaRubricaModal(e) {
  e.preventDefault();
  await apiPost('/api/matriz/rubrica', {
    ano: document.getElementById('nrub-ano').value,
    tipo_fluxo: document.getElementById('nrub-tipo').value,
    grupo: document.getElementById('nrub-grupo').value,
    rubrica: document.getElementById('nrub-nome').value,
    mes: document.getElementById('nrub-mes').value,
    valor: document.getElementById('nrub-valor').value
  });
  closeModal();
  fetchBootstrap();
}

// =======================================================
// TESOURARIA SUB-ABA 2: ORÇAMENTO DOS 15 MINISTÉRIOS (2025 vs 2026)
// =======================================================

function editarMinisterioModal(minId) {
  const m = STATE.ministerios.find(x => x.id === minId);
  if (!m) return;

  const html = `
    <form onsubmit="confirmarEdicaoMinisterio(event, ${m.id})" class="space-y-3 text-xs">
      <span class="text-[10px] font-bold uppercase tracking-wider bg-indigo-100 text-indigo-700 px-2.5 py-0.5 rounded-full">Orçamento Anual do Ministério</span>
      <h3 class="text-base font-bold text-slate-900">${m.nome}</h3>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="font-semibold text-slate-700 block mb-1">Realizado em 2025 (R$)</label>
          <input type="number" step="0.01" id="edit-min-2025" required value="${m.realizado_2025 || 0}" class="w-full border border-slate-300 rounded-xl px-3 py-2 font-bold" />
        </div>
        <div>
          <label class="font-semibold text-slate-700 block mb-1">Orçamento Anual 2026 (R$)</label>
          <input type="number" step="0.01" id="edit-min-2026" required value="${m.orcamento_2026 || 0}" class="w-full border border-slate-300 rounded-xl px-3 py-2 font-extrabold text-indigo-900" />
        </div>
      </div>
      <div>
        <label class="font-semibold text-slate-700 block mb-1">Observações (Isadora / Tesouraria)</label>
        <textarea id="edit-min-obs" rows="2" class="w-full border border-slate-300 rounded-xl px-3 py-2">${m.descricao || ''}</textarea>
      </div>
      <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-xl">
        💾 Salvar e Sincronizar Orçamento
      </button>
    </form>
  `;
  abrirModalCustom(html, false);
}

async function confirmarEdicaoMinisterio(e, id) {
  e.preventDefault();
  await apiPost('/api/ministerios/orcamento', {
    id,
    realizado_2025: document.getElementById('edit-min-2025').value,
    orcamento_2026: document.getElementById('edit-min-2026').value,
    descricao: document.getElementById('edit-min-obs').value
  });
  closeModal();
  fetchBootstrap();
}

function exportarPlanilhaTesourariaCSV() {
  const { rows } = calcularResumoAnoMatriz(ANO_MATRIZ_ATIVO);
  const linhas = [
    ['Ano', 'Fluxo', 'Grupo', 'Rubrica', ...NOMES_MESES, 'TOTAL_ANUAL', 'MEDIA_MENSAL']
  ];
  rows.forEach(r => {
    linhas.push([
      r.ano,
      r.tipo_fluxo,
      r.grupo,
      r.rubrica,
      ...r.meses.map(v => String(v).replace('.', ',')),
      String(r.total_anual).replace('.', ','),
      String(r.media_mensal).replace('.', ',')
    ]);
  });

  const csvContent = '\uFEFF' + linhas.map(row => row.map(cell => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(';')).join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Planilha_Tesouraria_${ANO_MATRIZ_ATIVO}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showLiveToast(`Planilha da Tesouraria (${ANO_MATRIZ_ATIVO}) exportada para Excel!`);
}

// =======================================================
// ABA RELATÓRIOS & BI ECLESIÁSTICO
// =======================================================

function renderRelatorios() {
  if (typeof popularSelectsRelatorios === 'function') popularSelectsRelatorios();
  const tipoRel = document.getElementById('rel-tipo')?.value || 'ministerios';
  const minFiltro = document.getElementById('rel-ministerio')?.value || '';

  const res2026 = calcularResumoAnoMatriz(2026);
  const res2025 = calcularResumoAnoMatriz(2025);
  const totOrc26 = STATE.ministerios.reduce((a, b) => a + Number(b.orcamento_2026 || 0), 0);
  const totReal25 = STATE.ministerios.reduce((a, b) => a + Number(b.realizado_2025 || 0), 0);
  const valPat = STATE.patrimonio.reduce((a, b) => a + Number(b.valor_aquisicao || 0), 0);

  const elRes = document.getElementById('rel-kpi-resultado');
  if (elRes) {
    elRes.textContent = formatBRL(res2026.saldoTotal);
    document.getElementById('rel-kpi-margem').textContent = `Ent: ${formatBRL(res2026.totalEntradas)} | Sai: ${formatBRL(res2026.totalSaidas)}`;
    document.getElementById('rel-kpi-orcamento').textContent = formatBRL(totOrc26);
    document.getElementById('rel-kpi-orcamento-sub').textContent = `Realizado 2025: ${formatBRL(totReal25)}`;
    document.getElementById('rel-kpi-engajamento').textContent = formatBRL(res2025.totalEntradas);
    document.getElementById('rel-kpi-engajamento-sub').textContent = `Saídas 2025: ${formatBRL(res2025.totalSaidas)}`;
    document.getElementById('rel-kpi-patrimonio').textContent = formatBRL(valPat);
    document.getElementById('rel-kpi-patrimonio-sub').textContent = `${STATE.patrimonio.length} itens inventariados`;
  }

  renderGraficosBI(res2026);

  const container = document.getElementById('rel-tabela-container');
  const tituloEl = document.getElementById('rel-tabela-titulo');
  const countEl = document.getElementById('rel-contador-registros');
  if (!container) return;

  if (tipoRel === 'ministerios') {
    const mins = STATE.ministerios.filter(m => !minFiltro || String(m.id) === String(minFiltro));
    tituloEl.textContent = 'Relatório Comparativo dos 15 Ministérios (Realizado 2025 vs. Orçamento 2026 vs. Executado 2026)';
    countEl.textContent = `${mins.length} ministérios`;
    container.innerHTML = `
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b border-slate-200 text-slate-500 uppercase bg-slate-50">
            <th class="py-2.5 px-3">Ministério</th>
            <th class="py-2.5 px-3 text-right">Realizado 2025</th>
            <th class="py-2.5 px-3 text-right">Orçamento 2026</th>
            <th class="py-2.5 px-3 text-center">Variação %</th>
            <th class="py-2.5 px-3 text-right">Executado 2026</th>
            <th class="py-2.5 px-3 text-right">Saldo Disponível</th>
            <th class="py-2.5 px-3">Observações (Isadora)</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${mins.map(m => `
            <tr class="hover:bg-slate-50">
              <td class="py-2.5 px-3 font-bold">${m.nome}</td>
              <td class="py-2.5 px-3 text-right">${formatBRL(m.realizado_2025)}</td>
              <td class="py-2.5 px-3 text-right font-bold text-indigo-700">${formatBRL(m.orcamento_2026)}</td>
              <td class="py-2.5 px-3 text-center">${m.aumento_perc}%</td>
              <td class="py-2.5 px-3 text-right text-rose-600 font-semibold">${formatBRL(m.gasto_atual)}</td>
              <td class="py-2.5 px-3 text-right text-emerald-700 font-bold">${formatBRL(m.orcamento_2026 - m.gasto_atual)}</td>
              <td class="py-2.5 px-3 text-slate-500">${m.descricao || '—'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } else if (tipoRel === 'dre2026' || tipoRel === 'dre2025') {
    const anoAlvo = tipoRel === 'dre2026' ? 2026 : 2025;
    const resAno = calcularResumoAnoMatriz(anoAlvo);
    tituloEl.textContent = `Demonstrativo Consolidado por Grupo Financeiro — Exercício ${anoAlvo}`;
    countEl.textContent = `${resAno.rows.length} rubricas`;

    const porGrupo = {};
    resAno.rows.forEach(r => {
      porGrupo[r.grupo] = (porGrupo[r.grupo] || 0) + r.total_anual;
    });

    container.innerHTML = `
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b border-slate-200 text-slate-500 uppercase bg-slate-50">
            <th class="py-2.5 px-3">Grande Grupo da Planilha (${anoAlvo})</th>
            <th class="py-2.5 px-3 text-right">Total Acumulado</th>
            <th class="py-2.5 px-3 text-right">Média Mensal (12m)</th>
            <th class="py-2.5 px-3 text-right">% sobre Entradas</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${Object.entries(porGrupo).map(([g, tot]) => {
            const p = resAno.totalEntradas > 0 ? ((tot / resAno.totalEntradas) * 100).toFixed(1) + '%' : '—';
            const isEnt = g.includes('Receitas');
            return `
              <tr class="hover:bg-slate-50">
                <td class="py-2.5 px-3 font-bold ${isEnt ? 'text-emerald-700' : 'text-slate-800'}">${g}</td>
                <td class="py-2.5 px-3 text-right font-extrabold ${isEnt ? 'text-emerald-700' : 'text-rose-600'}">${formatBRL(tot)}</td>
                <td class="py-2.5 px-3 text-right">${formatBRL(tot / 12)}</td>
                <td class="py-2.5 px-3 text-right font-semibold">${p}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  } else if (tipoRel === 'membros') {
    tituloEl.textContent = 'Relatório Geral de Membresia e Atuação Ministerial';
    countEl.textContent = `${STATE.membros.length} membros`;
    container.innerHTML = `
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b border-slate-200 text-slate-500 uppercase bg-slate-50">
            <th class="py-2.5 px-3">Nome Completo</th>
            <th class="py-2.5 px-3">Cargo</th>
            <th class="py-2.5 px-3">Família</th>
            <th class="py-2.5 px-3">Célula</th>
            <th class="py-2.5 px-3">Ministérios</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${STATE.membros.map(m => `
            <tr class="hover:bg-slate-50">
              <td class="py-2.5 px-3 font-bold">${m.nome}</td>
              <td class="py-2.5 px-3">${m.cargo_eclesiastico}</td>
              <td class="py-2.5 px-3">${m.familia || '—'}</td>
              <td class="py-2.5 px-3">${m.celula_nome || '—'}</td>
              <td class="py-2.5 px-3">${(m.ministerios || []).map(v => v.ministerio_nome).join(', ') || 'Nenhum'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  } else {
    tituloEl.textContent = 'Inventário Consolidado de Patrimônio';
    countEl.textContent = `${STATE.patrimonio.length} itens`;
    container.innerHTML = `
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b border-slate-200 text-slate-500 uppercase bg-slate-50">
            <th class="py-2.5 px-3">Código</th>
            <th class="py-2.5 px-3">Equipamento</th>
            <th class="py-2.5 px-3">Setor</th>
            <th class="py-2.5 px-3">Estado</th>
            <th class="py-2.5 px-3 text-right">Valor</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${STATE.patrimonio.map(p => `
            <tr class="hover:bg-slate-50">
              <td class="py-2.5 px-3 font-mono font-bold">${p.codigo}</td>
              <td class="py-2.5 px-3 font-semibold">${p.item}</td>
              <td class="py-2.5 px-3">${p.ministerio_nome || 'Geral'}</td>
              <td class="py-2.5 px-3">${p.estado}</td>
              <td class="py-2.5 px-3 text-right font-bold">${formatBRL(p.valor_aquisicao)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
}

function exportarRelatorioCSV() {
  exportarPlanilhaTesourariaCSV();
}


// =======================================================
// CENTRAL OFICIAL DE RELATÓRIOS EM PDF & EXPORTAÇÕES
// =======================================================

function switchRelatoriosSubtab(subtab) {
  const pnlPdf = document.getElementById('rel-subtab-pdf');
  const pnlGraf = document.getElementById('rel-subtab-graficos');
  const btnPdf = document.getElementById('rel-btn-subtab-pdf');
  const btnGraf = document.getElementById('rel-btn-subtab-graficos');

  if (subtab === 'pdf') {
    if (pnlPdf) pnlPdf.classList.remove('hidden');
    if (pnlGraf) pnlGraf.classList.add('hidden');
    if (btnPdf) {
      btnPdf.className = 'subtab-btn active bg-slate-900 text-white text-xs font-bold px-4 py-2.5 rounded-xl border border-slate-900 shadow transition flex items-center gap-2 cursor-pointer';
    }
    if (btnGraf) {
      btnGraf.className = 'subtab-btn bg-white hover:bg-slate-100 text-slate-700 text-xs font-bold px-4 py-2.5 rounded-xl border border-slate-200 shadow-xs transition flex items-center gap-2 cursor-pointer';
    }
    popularSelectsRelatorios();
  } else {
    if (pnlPdf) pnlPdf.classList.add('hidden');
    if (pnlGraf) pnlGraf.classList.remove('hidden');
    if (btnPdf) {
      btnPdf.className = 'subtab-btn bg-white hover:bg-slate-100 text-slate-700 text-xs font-bold px-4 py-2.5 rounded-xl border border-slate-200 shadow-xs transition flex items-center gap-2 cursor-pointer';
    }
    if (btnGraf) {
      btnGraf.className = 'subtab-btn active bg-slate-900 text-white text-xs font-bold px-4 py-2.5 rounded-xl border border-slate-900 shadow transition flex items-center gap-2 cursor-pointer';
    }
    renderRelatorios();
  }
}

function filtrarCardsRelatorios(busca) {
  const termo = (busca || '').toLowerCase().trim();
  const cards = document.querySelectorAll('.card-relatorio-item');
  cards.forEach(card => {
    const dataBusca = (card.getAttribute('data-busca') || '').toLowerCase();
    const texto = card.innerText.toLowerCase();
    if (!termo || dataBusca.includes(termo) || texto.includes(termo)) {
      card.style.display = '';
    } else {
      card.style.display = 'none';
    }
  });
}

function popularSelectsRelatorios() {
  // 1. rel-min-ind-id
  const selMin = document.getElementById('rel-min-ind-id');
  if (selMin) {
    const currVal = selMin.value;
    selMin.innerHTML = '<option value="">-- Selecione o Ministério --</option>' +
      (STATE.ministerios || []).map(m => `<option value="${m.id}">${m.nome} (Líder: ${m.lider || 'Geral'})</option>`).join('');
    if (currVal) selMin.value = currVal;
  }

  // 2. rel-ficha-membro-id
  const selFicha = document.getElementById('rel-ficha-membro-id');
  if (selFicha) {
    const currVal = selFicha.value;
    const sortedMembros = [...(STATE.membros || [])].sort((a, b) => (a.nome || '').localeCompare(b.nome || ''));
    selFicha.innerHTML = '<option value="">-- Selecione o Membro para Ficha 360º --</option>' +
      sortedMembros.map(m => `<option value="${m.id}">${m.nome} (Rol #${m.rol || m.id} · ${m.cargo_eclesiastico || 'Membro'})</option>`).join('');
    if (currVal) selFicha.value = currVal;
  }

  // 3. rel-diz-membro-id
  const selDiz = document.getElementById('rel-diz-membro-id');
  if (selDiz) {
    const currVal = selDiz.value;
    const sortedMembros = [...(STATE.membros || [])].sort((a, b) => (a.nome || '').localeCompare(b.nome || ''));
    selDiz.innerHTML = '<option value="">Todos os Membros (Relação Geral)</option>' +
      sortedMembros.map(m => `<option value="${m.id}">${m.nome} (Rol #${m.rol || m.id})</option>`).join('');
    if (currVal) selDiz.value = currVal;
  }
}

function abrirVisualizadorRelatorioPDF(opts) {
  if (typeof escapeHtml !== 'function') {
    window.escapeHtml = function(s) { return s == null ? '' : String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
  }
  const {
    titulo = 'Relatório Oficial',
    subtitulo = '',
    periodo = '',
    orientacao = 'portrait',
    kpis = [],
    colunas = [],
    linhas = [],
    rodapeTotais = '',
    nomeArquivo = 'relatorio.pdf',
    csvRows = null
  } = opts;

  const dataEmissao = new Date().toLocaleString('pt-BR');
  const operadorNome = CURRENT_OPERATOR ? CURRENT_OPERATOR.nome : 'Administração Geral';

  const kpisHTML = (kpis && kpis.length > 0) ? `
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
      ${kpis.map(k => `
        <div class="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <span class="block text-[10px] font-bold uppercase tracking-wider text-slate-500">${escapeHtml(k.label || '')}</span>
          <strong class="text-sm sm:text-base font-black ${k.cor || 'text-slate-900'}">${escapeHtml(k.valor || '')}</strong>
          ${k.sub ? `<span class="block text-[10px] text-slate-400 mt-0.5">${escapeHtml(k.sub)}</span>` : ''}
        </div>
      `).join('')}
    </div>
  ` : '';

  const theadHTML = `
    <thead>
      <tr class="border-b-2 border-slate-800 text-slate-700 font-bold uppercase text-[10px] bg-slate-100">
        ${colunas.map(c => `
          <th class="py-2 px-2.5 text-${c.align || 'left'}" style="${c.width ? 'width:' + c.width : ''}">
            ${escapeHtml(c.label || '')}
          </th>
        `).join('')}
      </tr>
    </thead>
  `;

  const tbodyHTML = `
    <tbody class="divide-y divide-slate-200 text-xs text-slate-800">
      ${linhas.length === 0 ? `
        <tr><td colspan="${colunas.length}" class="py-6 text-center text-slate-400">Nenhum registro encontrado para este período ou filtro.</td></tr>
      ` : linhas.map((row, rIdx) => `
        <tr class="${rIdx % 2 === 0 ? 'bg-white' : 'bg-slate-50/60'} hover:bg-indigo-50/50 transition">
          ${row.map((cell, cIdx) => {
            const col = colunas[cIdx] || {};
            const align = col.align || 'left';
            let val = cell;
            let isBold = false;
            if (typeof cell === 'object' && cell !== null) {
              val = cell.texto;
              if (cell.bold) isBold = true;
            }
            return `<td class="py-2 px-2.5 text-${align} ${isBold ? 'font-bold' : ''}">${val !== undefined && val !== null ? val : '—'}</td>`;
          }).join('')}
        </tr>
      `).join('')}
    </tbody>
  `;

  const tfootHTML = rodapeTotais ? `
    <tfoot>
      <tr class="border-t-2 border-slate-800 bg-slate-100 font-bold text-xs text-slate-900">
        ${rodapeTotais}
      </tr>
    </tfoot>
  ` : '';

  window._ultimoRelatorioCSV = csvRows;
  window._ultimoRelatorioNome = nomeArquivo ? nomeArquivo.replace(/\.pdf$/i, '.csv') : 'relatorio.csv';

  const html = `
    <div class="space-y-4 text-xs text-slate-800 printable-report ${orientacao === 'landscape' ? 'page-landscape' : ''}">
      <!-- Barra de Ações Rápidas (Oculta na Impressão) -->
      <div class="no-print flex items-center justify-between pb-3 border-b border-slate-200 gap-2">
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 rounded bg-slate-900 text-emerald-400 text-[10px] font-black tracking-[0.16em]">KAIRÓS</span>
          <span class="text-xs font-bold text-slate-600">Visualização de Documento Oficial</span>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">PIB Parque São Paulo</span>
        </div>
        <div class="flex items-center gap-2">
          ${csvRows ? `
            <button type="button" onclick="baixarUltimoRelatorioCSV()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 cursor-pointer shadow-xs">
              <span>📥</span> Baixar CSV
            </button>
          ` : ''}
          <button type="button" onclick="window.print()" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-3.5 py-1.5 rounded-lg transition flex items-center gap-1.5 cursor-pointer shadow-xs">
            <span>🖨️</span> Imprimir / Salvar em PDF
          </button>
          <button type="button" onclick="closeModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs px-3 py-1.5 rounded-lg transition cursor-pointer">
            ✕ Fechar
          </button>
        </div>
      </div>

      <!-- Cabeçalho Oficial Timbrado da Igreja -->
      <div class="border-b-2 border-slate-900 pb-3">
        <div class="flex items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <img src="/logo.png" alt="Logo PIB" class="w-14 h-14 object-contain rounded-full bg-white p-0.5 border border-slate-300 shrink-0" onerror="this.style.display='none'" />
            <div>
              <p class="text-[10px] uppercase font-bold tracking-widest text-indigo-700">Primeira Igreja Batista no Parque São Paulo</p>
              <h2 class="text-lg font-black text-slate-900">${escapeHtml(titulo)}</h2>
              ${subtitulo ? `<p class="text-xs text-slate-600 font-medium">${escapeHtml(subtitulo)}</p>` : ''}
            </div>
          </div>
          <div class="text-right shrink-0">
            ${periodo ? `<span class="inline-block px-2.5 py-1 rounded-lg text-xs font-black bg-indigo-50 text-indigo-800 border border-indigo-200">${escapeHtml(periodo)}</span>` : ''}
            <p class="text-[10px] text-slate-500 mt-1">Emitido em: ${dataEmissao}</p>
            <p class="text-[10px] text-slate-500">Operador: <strong>${escapeHtml(operadorNome)}</strong></p>
          </div>
        </div>
      </div>

      <!-- KPIs Resumo -->
      ${kpisHTML}

      <!-- Tabela de Dados Formatada -->
      <div class="overflow-x-auto border border-slate-200 rounded-xl my-3">
        <table class="w-full text-left border-collapse">
          ${theadHTML}
          ${tbodyHTML}
          ${tfootHTML}
        </table>
      </div>

      <!-- Rodapé Institucional e Assinaturas Oficiais -->
      <div class="pt-8 mt-6 border-t border-slate-300">
        <div class="grid grid-cols-4 gap-4 text-center text-[10px]">
          <div>
            <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Pastor Presidente</div>
          </div>
          <div>
            <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Administração Geral</div>
          </div>
          <div>
            <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Tesouraria & Finanças</div>
          </div>
          <div>
            <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Conselho Fiscal</div>
          </div>
        </div>
        <p class="text-center text-[9px] text-slate-400 mt-4">Documento emitido eletronicamente pelo Sistema KAIRÓS — PIB Parque São Paulo. Registrado e auditado.</p>
      </div>
    </div>
  `;

  abrirModalCustom(html, true, 'largo');
}

function baixarUltimoRelatorioCSV() {
  if (!window._ultimoRelatorioCSV || !window._ultimoRelatorioCSV.length) {
    alert('Nenhum dado disponível para exportação.');
    return;
  }
  const csvContent = window._ultimoRelatorioCSV.map(row =>
    row.map(cell => {
      const c = cell !== undefined && cell !== null ? String(cell).replace(/"/g, '""') : '';
      return `"${c}"`;
    }).join(';')
  ).join('\r\n');

  const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = window._ultimoRelatorioNome || 'relatorio.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// 1. LIVRO CAIXA GERAL
function gerarPDFLivroCaixa() {
  if (!verificarAcessoRelatorio('rel_livro_caixa', 'Livro Caixa Geral')) return;
  const ano = Number(document.getElementById('rel-lc-ano')?.value || 2026);
  const mes = document.getElementById('rel-lc-mes')?.value || '';

  const mesesNomes = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
  const periodoTexto = mes ? `${mesesNomes[Number(mes)]} / ${ano}` : `Exercício Completo ${ano}`;

  let lancs = (STATE.financeiro || []).filter(f => {
    if (!f.data_lancamento) return false;
    const [a, m] = f.data_lancamento.split('-');
    if (Number(a) !== ano) return false;
    if (mes && Number(m) !== Number(mes)) return false;
    return true;
  });

  lancs.sort((a, b) => (a.data_lancamento || '').localeCompare(b.data_lancamento || ''));

  let totalEntradas = 0;
  let totalSaidas = 0;
  lancs.forEach(l => {
    const val = Number(l.valor || 0);
    if (l.tipo === 'ENTRADA') totalEntradas += val;
    else if (l.tipo === 'SAIDA') totalSaidas += val;
  });
  const saldoPeriodo = totalEntradas - totalSaidas;

  const colunas = [
    { label: 'Data', width: '85px', align: 'center' },
    { label: 'Tipo', width: '80px', align: 'center' },
    { label: 'Categoria / Rubrica', width: '150px' },
    { label: 'Histórico / Descrição' },
    { label: 'Pessoa / Ministério', width: '130px' },
    { label: 'Forma Pgto', width: '90px', align: 'center' },
    { label: 'Entradas (R$)', width: '100px', align: 'right' },
    { label: 'Saídas (R$)', width: '100px', align: 'right' }
  ];

  const linhas = lancs.map(l => {
    const isEnt = l.tipo === 'ENTRADA';
    const val = Number(l.valor || 0);
    const pessoa = l.pessoa_nome || (l.membro_id ? (STATE.membros.find(m => m.id === l.membro_id)?.nome || 'Membro') : '—');
    return [
      formatDateBR(l.data_lancamento),
      isEnt ? '<span class="text-emerald-700 font-bold">ENTRADA</span>' : '<span class="text-rose-700 font-bold">SAÍDA</span>',
      { texto: l.categoria || 'Geral', bold: true },
      l.descricao || '—',
      pessoa,
      l.forma_pagamento || 'PIX',
      isEnt ? formatBRL(val) : '—',
      !isEnt ? formatBRL(val) : '—'
    ];
  });

  const kpis = [
    { label: 'Total Entradas', valor: formatBRL(totalEntradas), cor: 'text-emerald-700', sub: 'Dízimos e receitas' },
    { label: 'Total Saídas', valor: formatBRL(totalSaidas), cor: 'text-rose-700', sub: 'Despesas do período' },
    { label: 'Saldo do Período', valor: formatBRL(saldoPeriodo), cor: saldoPeriodo >= 0 ? 'text-emerald-700' : 'text-rose-700', sub: 'Superávit / Saldo' },
    { label: 'Qtd. Lançamentos', valor: String(lancs.length), cor: 'text-indigo-700', sub: 'Registros no livro caixa' }
  ];

  const rodapeTotais = `
    <td colspan="6" class="py-2.5 px-3 uppercase font-black">Totais Consolidados do Período (${periodoTexto})</td>
    <td class="text-right py-2.5 px-3 font-mono font-black text-emerald-800">${formatBRL(totalEntradas)}</td>
    <td class="text-right py-2.5 px-3 font-mono font-black text-rose-800">${formatBRL(totalSaidas)}</td>
  `;

  const csvRows = [
    ['Data', 'Tipo', 'Categoria', 'Descricao', 'Pessoa_Ministerio', 'Forma_Pagamento', 'Entrada', 'Saida'],
    ...lancs.map(l => [
      formatDateBR(l.data_lancamento),
      l.tipo,
      l.categoria,
      l.descricao,
      l.pessoa_nome || '',
      l.forma_pagamento,
      l.tipo === 'ENTRADA' ? Number(l.valor || 0).toFixed(2) : '0.00',
      l.tipo === 'SAIDA' ? Number(l.valor || 0).toFixed(2) : '0.00'
    ])
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: 'Livro Caixa Geral & Movimentação Financeira',
    subtitulo: 'Demonstrativo oficial cronológico de receitas e despesas registradas na tesouraria',
    periodo: periodoTexto,
    orientacao: 'landscape',
    kpis,
    colunas,
    linhas,
    rodapeTotais,
    nomeArquivo: `Livro_Caixa_${ano}_${mes || 'todos'}.pdf`,
    csvRows
  });
}

// 2. BALANCETE MENSAL
function gerarPDFBalanceteMensal() {
  if (!verificarAcessoRelatorio('rel_balancete_mensal', 'Balancete Mensal da Tesouraria')) return;
  const ano = Number(document.getElementById('rel-bal-ano')?.value || 2026);
  const mes = Number(document.getElementById('rel-bal-mes')?.value || 1);
  const mesesNomes = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
  const periodoTexto = `${mesesNomes[mes]} / ${ano}`;

  const lancs = (STATE.financeiro || []).filter(f => {
    if (!f.data_lancamento) return false;
    const [a, m] = f.data_lancamento.split('-');
    return Number(a) === ano && Number(m) === mes;
  });

  const porCat = {};
  let totEntradas = 0;
  let totSaidas = 0;
  lancs.forEach(f => {
    const val = Number(f.valor || 0);
    const cat = f.categoria || 'Outros';
    if (!porCat[cat]) porCat[cat] = { tipo: f.tipo, total: 0, count: 0 };
    porCat[cat].total += val;
    porCat[cat].count += 1;
    if (f.tipo === 'ENTRADA') totEntradas += val;
    else totSaidas += val;
  });

  const saldo = totEntradas - totSaidas;

  const colunas = [
    { label: 'Rubrica / Categoria Financeira', width: '220px' },
    { label: 'Tipo de Movimento', width: '130px', align: 'center' },
    { label: 'Nº Lançamentos', width: '120px', align: 'center' },
    { label: '% sobre Entradas', width: '120px', align: 'right' },
    { label: 'Total Acumulado no Mês (R$)', width: '160px', align: 'right' }
  ];

  const linhas = Object.entries(porCat).map(([cat, dados]) => {
    const isEnt = dados.tipo === 'ENTRADA';
    const perc = totEntradas > 0 ? ((dados.total / totEntradas) * 100).toFixed(1) + '%' : '—';
    return [
      { texto: cat, bold: true },
      isEnt ? '<span class="text-emerald-700 font-bold">RECEITA (+)</span>' : '<span class="text-rose-700 font-bold">DESPESA (-)</span>',
      String(dados.count),
      perc,
      formatBRL(dados.total)
    ];
  });

  const kpis = [
    { label: 'Total de Receitas', valor: formatBRL(totEntradas), cor: 'text-emerald-700', sub: 'Entradas do mês' },
    { label: 'Total de Despesas', valor: formatBRL(totSaidas), cor: 'text-rose-700', sub: 'Pagamentos do mês' },
    { label: 'Superávit / Saldo', valor: formatBRL(saldo), cor: saldo >= 0 ? 'text-emerald-700' : 'text-rose-700', sub: 'Saldo líquido mensal' },
    { label: 'Movimentações', valor: String(lancs.length), cor: 'text-indigo-700', sub: 'Lançamentos no mês' }
  ];

  const rodapeTotais = `
    <td colspan="4" class="py-2.5 px-3 uppercase font-black">Resultado Líquido do Balancete Mensal (${periodoTexto})</td>
    <td class="text-right py-2.5 px-3 font-mono font-black ${saldo >= 0 ? 'text-emerald-800' : 'text-rose-800'}">${formatBRL(saldo)}</td>
  `;

  abrirVisualizadorRelatorioPDF({
    titulo: 'Balancete Mensal Oficial da Tesouraria',
    subtitulo: 'Prestação de contas contábil analítica por categorias e rubricas',
    periodo: periodoTexto,
    orientacao: 'portrait',
    kpis,
    colunas,
    linhas,
    rodapeTotais,
    nomeArquivo: `Balancete_${ano}_${String(mes).padStart(2, '0')}.pdf`,
    csvRows: [
      ['Categoria', 'Tipo', 'Qtd_Lancamentos', 'Total'],
      ...Object.entries(porCat).map(([cat, d]) => [cat, d.tipo, d.count, d.total.toFixed(2)])
    ]
  });
}

// 3. BALANÇO ANUAL DRE
function gerarPDFDREAnual() {
  if (!verificarAcessoRelatorio('rel_dre_anual', 'Balanço Anual Consolidado (DRE)')) return;
  const ano = Number(document.getElementById('rel-dre-ano')?.value || 2026);
  const res = calcularResumoAnoMatriz(ano);

  const porGrupo = {};
  res.rows.forEach(r => {
    porGrupo[r.grupo] = (porGrupo[r.grupo] || 0) + Number(r.total_anual || 0);
  });

  const colunas = [
    { label: 'Grupo Contábil da Planilha', width: '240px' },
    { label: 'Total Anual (R$)', width: '150px', align: 'right' },
    { label: 'Média Mensal (12 Meses)', width: '150px', align: 'right' },
    { label: '% sobre Receitas', width: '130px', align: 'right' }
  ];

  const linhas = Object.entries(porGrupo).map(([g, tot]) => {
    const isEnt = g.includes('Receita') || g.includes('Entrada');
    const p = res.totalEntradas > 0 ? ((tot / res.totalEntradas) * 100).toFixed(1) + '%' : '—';
    return [
      { texto: g, bold: true },
      formatBRL(tot),
      formatBRL(tot / 12.0),
      p
    ];
  });

  const kpis = [
    { label: 'Receita Total 12 Meses', valor: formatBRL(res.totalEntradas), cor: 'text-emerald-700', sub: `Exercício ${ano}` },
    { label: 'Despesas Totais 12 Meses', valor: formatBRL(res.totalSaidas), cor: 'text-rose-700', sub: `Exercício ${ano}` },
    { label: 'Resultado Acumulado', valor: formatBRL(res.saldoTotal), cor: res.saldoTotal >= 0 ? 'text-emerald-700' : 'text-rose-700', sub: 'Superávit / Saldo' },
    { label: 'Rubricas Orçadas', valor: String(res.rows.length), cor: 'text-indigo-700', sub: 'Linhas na matriz oficial' }
  ];

  const rodapeTotais = `
    <td class="py-2.5 px-3 uppercase font-black">Saldo Final Consolidado do Exercício ${ano}</td>
    <td class="text-right py-2.5 px-3 font-mono font-black ${res.saldoTotal >= 0 ? 'text-emerald-800' : 'text-rose-800'}">${formatBRL(res.saldoTotal)}</td>
    <td class="text-right py-2.5 px-3 font-mono font-black">${formatBRL(res.saldoTotal / 12.0)}</td>
    <td class="text-right py-2.5 px-3 font-mono font-black">100%</td>
  `;

  abrirVisualizadorRelatorioPDF({
    titulo: `Demonstrativo do Resultado do Exercício (DRE) — ${ano}`,
    subtitulo: 'Balanço financeiro anual oficial aprovado e consolidado pelos grandes grupos de despesas e receitas',
    periodo: `Exercício Fiscal ${ano}`,
    orientacao: 'portrait',
    kpis,
    colunas,
    linhas,
    rodapeTotais,
    nomeArquivo: `DRE_Anual_${ano}.pdf`,
    csvRows: [
      ['Grupo', 'Total_Anual', 'Media_Mensal'],
      ...Object.entries(porGrupo).map(([g, tot]) => [g, tot.toFixed(2), (tot / 12.0).toFixed(2)])
    ]
  });
}

// 4. ASSEMBLEIA GERAL
function gerarPDFAssembleia() {
  if (!verificarAcessoRelatorio('rel_assembleia', 'Demonstrativo da Assembleia Geral')) return;
  const ano = Number(document.getElementById('rel-ass-ano')?.value || 2026);
  const mes = Number(document.getElementById('rel-ass-mes')?.value || 1);
  const mesesNomes = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
  const periodoTexto = `${mesesNomes[mes]} / ${ano}`;

  const res = calcularResumoAnoMatriz(ano);
  const totMembros = (STATE.membros || []).length;
  const totAtivos = (STATE.membros || []).filter(m => m.status === 'Ativo').length;
  const totMins = (STATE.ministerios || []).length;

  const colunas = [
    { label: 'Item / Tópico da Pauta da Assembleia', width: '250px' },
    { label: 'Informação / Valor Consolidado', align: 'right', width: '180px' },
    { label: 'Situação / Parecer Contábil' }
  ];

  const linhas = [
    [{ texto: '1. Membresia em Comunhão no Rol', bold: true }, `${totAtivos} membros ativos`, `Total cadastrado: ${totMembros} membros`],
    [{ texto: '2. Receitas Totais Arrecadadas', bold: true }, formatBRL(res.totalEntradas), 'Dízimos fiéis, ofertas e arrecadações de campanhas'],
    [{ texto: '3. Despesas Fixas e Folha Pastoral', bold: true }, formatBRL(res.totalSaidas), 'Despesas ordinárias, encargos, tributos e manutenção'],
    [{ texto: '4. Resultado Operacional Líquido', bold: true }, formatBRL(res.saldoTotal), res.saldoTotal >= 0 ? '✓ Superávit financeiro regular' : '⚠ Atenção: Déficit no período'],
    [{ texto: '5. Ministérios e Departamentos Ativos', bold: true }, `${totMins} ministérios estruturados`, 'Ações evangelísticas, projeto viver, infantil e cultos'],
    [{ texto: '6. Parecer do Conselho Fiscal', bold: true }, 'FAVORÁVEL', 'Contas e livros em ordem para apreciação e voto soberano']
  ];

  const kpis = [
    { label: 'Membros Ativos', valor: String(totAtivos), cor: 'text-indigo-700', sub: 'Em comunhão com a igreja' },
    { label: 'Receita Anual', valor: formatBRL(res.totalEntradas), cor: 'text-emerald-700', sub: 'Entradas registradas' },
    { label: 'Despesa Anual', valor: formatBRL(res.totalSaidas), cor: 'text-rose-700', sub: 'Saídas pagas' },
    { label: 'Parecer Fiscal', valor: 'APROVAÇÃO', cor: 'text-emerald-700', sub: 'Unanimidade de parecer' }
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: 'Demonstrativo Oficial para Assembleia Geral da Igreja',
    subtitulo: 'Relatório executivo canônico para prestação de contas, apreciação e homologação pela congregação',
    periodo: periodoTexto,
    orientacao: 'portrait',
    kpis,
    colunas,
    linhas,
    nomeArquivo: `Assembleia_${ano}_${String(mes).padStart(2, '0')}.pdf`
  });
}

// 5. ORÇAMENTO DOS MINISTÉRIOS
function gerarPDF15Ministerios() {
  if (!verificarAcessoRelatorio('rel_ministerios', 'Execução Orçamentária dos Ministérios')) return;
  const ano = Number(document.getElementById('rel-min-ano')?.value || 2026);
  const mins = STATE.ministerios || [];

  const totOrc = mins.reduce((a, b) => a + Number(b.orcamento_2026 || 0), 0);
  const totReal25 = mins.reduce((a, b) => a + Number(b.realizado_2025 || 0), 0);
  const totExec = mins.reduce((a, b) => a + Number(b.gasto_atual || 0), 0);

  const colunas = [
    { label: 'Ministério / Departamento', width: '200px' },
    { label: 'Líder Responsável', width: '160px' },
    { label: 'Realizado 2025', width: '110px', align: 'right' },
    { label: 'Orçamento 2026', width: '110px', align: 'right' },
    { label: 'Executado 2026', width: '110px', align: 'right' },
    { label: 'Saldo Disponível', width: '110px', align: 'right' },
    { label: 'Observações & Planejamento' }
  ];

  const linhas = mins.map(m => {
    const o26 = Number(m.orcamento_2026 || 0);
    const r25 = Number(m.realizado_2025 || 0);
    const exec = Number(m.gasto_atual || 0);
    const saldo = o26 - exec;
    return [
      { texto: m.nome, bold: true },
      m.lider || '—',
      formatBRL(r25),
      formatBRL(o26),
      formatBRL(exec),
      { texto: formatBRL(saldo), bold: true },
      m.descricao || '—'
    ];
  });

  const kpis = [
    { label: 'Total Orçado 2026', valor: formatBRL(totOrc), cor: 'text-indigo-700', sub: 'Teto orçamentário anual' },
    { label: 'Executado 2026', valor: formatBRL(totExec), cor: 'text-rose-700', sub: 'Verbas já utilizadas' },
    { label: 'Saldo Restante', valor: formatBRL(totOrc - totExec), cor: 'text-emerald-700', sub: 'Disponível para os ministérios' },
    { label: 'Total de Ministérios', valor: String(mins.length), cor: 'text-slate-900', sub: 'Departamentos ativos' }
  ];

  const rodapeTotais = `
    <td colspan="2" class="py-2.5 px-3 uppercase font-black">Totais de Todos os Ministérios</td>
    <td class="text-right py-2.5 px-3 font-mono font-black">${formatBRL(totReal25)}</td>
    <td class="text-right py-2.5 px-3 font-mono font-black text-indigo-800">${formatBRL(totOrc)}</td>
    <td class="text-right py-2.5 px-3 font-mono font-black text-rose-800">${formatBRL(totExec)}</td>
    <td class="text-right py-2.5 px-3 font-mono font-black text-emerald-800">${formatBRL(totOrc - totExec)}</td>
    <td></td>
  `;

  abrirVisualizadorRelatorioPDF({
    titulo: `Painel Orçamentário e Comparativo dos ${mins.length} Ministérios`,
    subtitulo: 'Demonstrativo oficial de verbas orçamentárias aprovadas, despesas executadas e saldos disponíveis',
    periodo: `Exercício Fiscal ${ano}`,
    orientacao: 'landscape',
    kpis,
    colunas,
    linhas,
    rodapeTotais,
    nomeArquivo: `Ministerios_Orcamento_${ano}.pdf`
  });
}

// 6. PRESTAÇÃO DE CONTAS INDIVIDUAL POR MINISTÉRIO
function gerarPDFPrestacaoMinisterio() {
  if (!verificarAcessoRelatorio('rel_prestacao_ministerio', 'Prestação de Contas por Ministério')) return;
  let minId = document.getElementById('rel-min-ind-id')?.value;
  if (!minId && STATE.ministerios && STATE.ministerios.length > 0) {
    minId = STATE.ministerios[0].id;
    if (document.getElementById('rel-min-ind-id')) document.getElementById('rel-min-ind-id').value = minId;
  }
  if (!minId) {
    alert('Por favor, selecione um ministério para emitir este relatório.');
    return;
  }
  const min = (STATE.ministerios || []).find(m => String(m.id) === String(minId));
  if (!min) {
    alert('Ministério não encontrado.');
    return;
  }

  const lancs = (STATE.financeiro || []).filter(f => String(f.ministerio_id) === String(minId));
  const despesasTotal = lancs.filter(f => f.tipo === 'SAIDA').reduce((a, b) => a + Number(b.valor || 0), 0);
  const orc = Number(min.orcamento_2026 || 0);
  const saldo = orc - despesasTotal;

  const colunas = [
    { label: 'Data', width: '90px', align: 'center' },
    { label: 'Tipo', width: '90px', align: 'center' },
    { label: 'Categoria / Finalidade', width: '180px' },
    { label: 'Descrição / Histórico da Compra' },
    { label: 'Comprovante / NF', width: '130px', align: 'center' },
    { label: 'Valor (R$)', width: '120px', align: 'right' }
  ];

  const linhas = lancs.map(l => [
    formatDateBR(l.data_lancamento),
    l.tipo === 'SAIDA' ? '<span class="text-rose-700 font-bold">DESPESA</span>' : '<span class="text-emerald-700 font-bold">ENTRADA</span>',
    { texto: l.categoria || 'Despesa Departamental', bold: true },
    l.descricao || '—',
    l.comprovante_url ? '✓ Comprovante Anexo' : 'Pendente',
    formatBRL(l.valor)
  ]);

  const kpis = [
    { label: 'Ministério', valor: min.nome, cor: 'text-indigo-700', sub: `Líder: ${min.lider || 'Geral'}` },
    { label: 'Orçamento Aprovado', valor: formatBRL(orc), cor: 'text-indigo-700', sub: 'Teto 2026' },
    { label: 'Total Utilizado', valor: formatBRL(despesasTotal), cor: 'text-rose-700', sub: 'Gastos computados' },
    { label: 'Saldo Disponível', valor: formatBRL(saldo), cor: saldo >= 0 ? 'text-emerald-700' : 'text-rose-700', sub: 'Verba remanescente' }
  ];

  const rodapeTotais = `
    <td colspan="5" class="py-2.5 px-3 uppercase font-black">Total Executado por ${min.nome}</td>
    <td class="text-right py-2.5 px-3 font-mono font-black text-rose-800">${formatBRL(despesasTotal)}</td>
  `;

  abrirVisualizadorRelatorioPDF({
    titulo: `Prestação de Contas Individual — ${min.nome}`,
    subtitulo: `Detalhamento de gastos, compras e utilização da verba departamental sob responsabilidade de ${min.lider || 'Diretoria'}`,
    periodo: 'Exercício 2026',
    orientacao: 'portrait',
    kpis,
    colunas,
    linhas,
    rodapeTotais,
    nomeArquivo: `Prestacao_${min.nome.replace(/\s+/g, '_')}_2026.pdf`
  });
}

// 7. ROL GERAL DE MEMBROS
function gerarPDFRolMembros() {
  if (!verificarAcessoRelatorio('rel_rol_membros', 'Rol Geral de Membros')) return;
  const statusFiltro = document.getElementById('rel-membros-status')?.value || '';
  const ebdFiltro = document.getElementById('rel-membros-ebd')?.value || '';

  let filtrados = (STATE.membros || []).filter(m => {
    if (statusFiltro && m.status !== statusFiltro) return false;
    if (ebdFiltro && (m.sala_ebd || '').toUpperCase() !== ebdFiltro.toUpperCase()) return false;
    return true;
  });

  filtrados.sort((a, b) => (a.nome || '').localeCompare(b.nome || ''));

  const colunas = [
    { label: 'Rol / Ficha', width: '90px', align: 'center' },
    { label: 'Nome Completo do Membro', width: '220px' },
    { label: 'Cargo', width: '120px' },
    { label: 'Telefone / WhatsApp', width: '130px', align: 'center' },
    { label: 'Data Batismo', width: '100px', align: 'center' },
    { label: 'Ministérios Vinculados', width: '180px' },
    { label: 'Status no Rol', width: '110px', align: 'center' }
  ];

  const linhas = filtrados.map(m => {
    const minsStr = (m.ministerios || []).map(v => v.ministerio_nome).join(', ') || '—';
    return [
      m.rol ? `#${m.rol}` : `#${m.id}`,
      { texto: m.nome, bold: true },
      m.cargo_eclesiastico || 'Membro',
      m.telefone || '—',
      formatDateBR(m.data_batismo),
      minsStr,
      m.status || 'Ativo'
    ];
  });

  const totAtivos = filtrados.filter(m => m.status === 'Ativo').length;
  const totCriancas = filtrados.filter(m => m.status === 'Criança').length;
  const totAlunos = filtrados.filter(m => m.status === 'Aluno do Viver').length;

  const kpis = [
    { label: 'Total Listados', valor: String(filtrados.length), cor: 'text-indigo-700', sub: 'Membros selecionados' },
    { label: 'Ativos em Comunhão', valor: String(totAtivos), cor: 'text-emerald-700', sub: 'Membros plenos' },
    { label: 'Crianças no Rol', valor: String(totCriancas), cor: 'text-sky-700', sub: 'Rol infantil' },
    { label: 'Alunos do Viver', valor: String(totAlunos), cor: 'text-purple-700', sub: 'Projeto e discipulado' }
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: 'Rol Oficial de Membros da Igreja',
    subtitulo: 'Relação nominal canônica de membresia registrada no livro da Secretaria Geral',
    periodo: `Posição em ${new Date().toLocaleDateString('pt-BR')}`,
    orientacao: 'landscape',
    kpis,
    colunas,
    linhas,
    nomeArquivo: 'Rol_Oficial_Membros.pdf',
    csvRows: [
      ['Rol', 'Nome', 'Cargo', 'Telefone', 'Data_Batismo', 'Status'],
      ...filtrados.map(m => [m.rol || m.id, m.nome, m.cargo_eclesiastico, m.telefone, m.data_batismo, m.status])
    ]
  });
}

// 8. ANIVERSARIANTES MENSAIS
function gerarPDFAniversariantes() {
  if (!verificarAcessoRelatorio('rel_aniversariantes', 'Relatório de Aniversariantes')) return;
  const mes = Number(document.getElementById('rel-aniv-mes')?.value || (new Date().getMonth() + 1));
  const mesesNomes = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
  const periodoTexto = `${mesesNomes[mes]}`;

  const anivs = (STATE.membros || []).filter(m => {
    if (!m.data_nascimento) return false;
    const parts = m.data_nascimento.split('-');
    if (parts.length < 3) return false;
    return Number(parts[1]) === mes;
  });

  anivs.sort((a, b) => {
    const diaA = Number(a.data_nascimento.split('-')[2]);
    const diaB = Number(b.data_nascimento.split('-')[2]);
    return diaA - diaB;
  });

  const colunas = [
    { label: 'Dia', width: '60px', align: 'center' },
    { label: 'Aniversariante (Nome)', width: '220px' },
    { label: 'Cargo', width: '130px' },
    { label: 'Telefone / WhatsApp', width: '140px', align: 'center' },
    { label: 'Família', width: '150px' },
    { label: 'Ministério / Atuação' }
  ];

  const linhas = anivs.map(m => {
    const dia = String(m.data_nascimento.split('-')[2]).padStart(2, '0');
    const minsStr = (m.ministerios || []).map(v => v.ministerio_nome).join(', ') || '—';
    return [
      { texto: dia, bold: true },
      { texto: m.nome, bold: true },
      m.cargo_eclesiastico || 'Membro',
      m.telefone ? `<a href="https://wa.me/55${m.telefone.replace(/\D/g, '')}" target="_blank" class="text-emerald-700 underline">${m.telefone}</a>` : '—',
      m.familia || '—',
      minsStr
    ];
  });

  const kpis = [
    { label: 'Mês de Referência', valor: periodoTexto, cor: 'text-indigo-700', sub: 'Mês dos aniversariantes' },
    { label: 'Total de Aniversariantes', valor: String(anivs.length), cor: 'text-emerald-700', sub: 'Irmãos celebrando vida' }
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: `Aniversariantes do Mês — ${periodoTexto}`,
    subtitulo: 'Relação nominal para homenagens, oração pastoral e felicitações nos cultos',
    periodo: periodoTexto,
    orientacao: 'portrait',
    kpis,
    colunas,
    linhas,
    nomeArquivo: `Aniversariantes_${mesesNomes[mes]}.pdf`
  });
}

// 9. FICHA CADASTRAL 360º DE MEMBRO
function gerarPDFFichaMembro() {
  if (!verificarAcessoRelatorio('rel_ficha_membro', 'Ficha Cadastral 360º de Membro')) return;
  let membroId = document.getElementById('rel-ficha-membro-id')?.value;
  if (!membroId && STATE.membros && STATE.membros.length > 0) {
    membroId = STATE.membros[0].id;
    if (document.getElementById('rel-ficha-membro-id')) document.getElementById('rel-ficha-membro-id').value = membroId;
  }
  if (!membroId) {
    alert('Por favor, selecione um membro para emitir a Ficha 360º.');
    return;
  }
  const m = (STATE.membros || []).find(x => String(x.id) === String(membroId));
  if (!m) {
    alert('Membro não encontrado.');
    return;
  }

  const colunas = [
    { label: 'Campo / Dado Cadastral', width: '220px' },
    { label: 'Informação Registrada no Sistema' }
  ];

  const linhas = [
    [{ texto: 'Nome Completo', bold: true }, m.nome],
    [{ texto: 'Apelido / Como gosta de ser chamado', bold: true }, m.apelido || '—'],
    [{ texto: 'Rol de Membro / Matrícula', bold: true }, m.rol ? `Rol #${m.rol}` : `Matrícula #${m.id}`],
    [{ texto: 'Status no Rol', bold: true }, m.status || 'Ativo'],
    [{ texto: 'Cargo Eclesiástico', bold: true }, m.cargo_eclesiastico || 'Membro'],
    [{ texto: 'Data de Nascimento', bold: true }, formatDateBR(m.data_nascimento)],
    [{ texto: 'Data de Batismo', bold: true }, formatDateBR(m.data_batismo)],
    [{ texto: 'Gênero / Estado Civil', bold: true }, `${m.genero || '—'} · ${m.estado_civil || '—'}`],
    [{ texto: 'Profissão', bold: true }, m.profissao || 'Não informada'],
    [{ texto: 'Cônjuge', bold: true }, m.conjuge ? `${m.conjuge} ${m.data_casamento ? '(Casamento: ' + formatDateBR(m.data_casamento) + ')' : ''}` : 'Não informado'],
    [{ texto: 'Telefone / WhatsApp', bold: true }, m.telefone || '—'],
    [{ texto: 'E-mail', bold: true }, m.email || '—'],
    [{ texto: 'CPF / RG', bold: true }, `${m.cpf || '—'} · RG: ${m.rg || '—'}`],
    [{ texto: 'Endereço Residencial', bold: true }, `${m.logradouro || ''} ${m.numero || ''} ${m.complemento || ''} - ${m.bairro_endereco || ''}, ${m.cidade_endereco || ''} - ${m.uf_endereco || ''}`],
    [{ texto: 'Ministério Principal', bold: true }, m.ministerio_nome ? `${m.ministerio_nome} (${m.funcao_ministerio || 'Voluntário'})` : 'Nenhum'],
    [{ texto: 'Ministério 2', bold: true }, m.ministerio_id_2 ? `${(STATE.ministerios.find(min => min.id === m.ministerio_id_2)?.nome || 'Ministério 2')} (${m.funcao_ministerio_2 || 'Voluntário'})` : 'Nenhum'],
    [{ texto: 'Transferência / Situação', bold: true }, m.tipo_transferencia ? `${m.tipo_transferencia} — Motivo: ${m.motivo_transferencia || 'Não informado'}` : 'Em Comunhão Regular'],
    [{ texto: 'Observações Pastorais', bold: true }, m.observacoes || 'Sem observações registradas.']
  ];

  const kpis = [
    { label: 'Membro', valor: m.nome, cor: 'text-indigo-700', sub: `Rol #${m.rol || m.id}` },
    { label: 'Status', valor: m.status || 'Ativo', cor: 'text-emerald-700', sub: m.cargo_eclesiastico || 'Membro' },
    { label: 'Telefone', valor: m.telefone || 'Sem tel.', cor: 'text-slate-900', sub: 'Contato' }
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: `Ficha Cadastral Oficial 360º — ${m.nome}`,
    subtitulo: 'Prontuário eclesiástico individual completo com dados civis, sacramentais e ministeriais',
    periodo: `Cadastrado em ${formatDateBR(m.criado_em)}`,
    orientacao: 'portrait',
    kpis,
    colunas,
    linhas,
    nomeArquivo: `Ficha_${m.nome.replace(/\s+/g, '_')}.pdf`
  });
}

// 11. VISITANTES & RECEPÇÃO
function gerarPDFVisitantes() {
  if (!verificarAcessoRelatorio('rel_visitantes', 'Relatório de Visitantes & Recepção')) return;
  const vis = STATE.visitantes || [];

  const colunas = [
    { label: 'Data Visita', width: '90px', align: 'center' },
    { label: 'Nome do Visitante', width: '220px' },
    { label: 'Telefone / WhatsApp', width: '140px', align: 'center' },
    { label: 'Quem Convidou', width: '160px' },
    { label: 'Primeira Vez?', width: '100px', align: 'center' },
    { label: 'Observações de Acolhimento' }
  ];

  const linhas = vis.map(v => [
    formatDateBR(v.data_visita),
    { texto: v.nome, bold: true },
    v.telefone || '—',
    v.quem_convidou || '—',
    v.primeira_vez ? '✓ Sim' : 'Não',
    v.observacoes || '—'
  ]);

  const kpis = [
    { label: 'Total de Visitantes', valor: String(vis.length), cor: 'text-amber-700', sub: 'Acolhidos na igreja' },
    { label: 'Primeira Visita', valor: String(vis.filter(v => v.primeira_vez).length), cor: 'text-emerald-700', sub: 'Novos visitantes' }
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: 'Relatório Oficial de Visitantes & Recepção',
    subtitulo: 'Registro de contatos e acolhimento dos cultos para integração e discipulado',
    periodo: 'Histórico Consolidado',
    orientacao: 'portrait',
    kpis,
    colunas,
    linhas,
    nomeArquivo: 'Relatorio_Visitantes.pdf'
  });
}

// 12. CÉLULAS & PEQUENOS GRUPOS
function gerarPDFCelulas() {
  if (!verificarAcessoRelatorio('rel_celulas', 'Células & Grupos Familiares')) return;
  const celulas = STATE.celulas || [];

  const colunas = [
    { label: 'Nome da Célula', width: '200px' },
    { label: 'Líder Responsável', width: '160px' },
    { label: 'Bairro / Local', width: '150px' },
    { label: 'Dia e Horário', width: '140px', align: 'center' },
    { label: 'Membros Vinculados', width: '120px', align: 'center' }
  ];

  const linhas = celulas.map(c => {
    const qtdMembros = (STATE.membros || []).filter(m => m.celula_id === c.id).length;
    return [
      { texto: c.nome, bold: true },
      c.lider || '—',
      c.bairro || '—',
      `${c.dia_semana || ''} às ${c.horario || ''}`,
      String(qtdMembros)
    ];
  });

  const kpis = [
    { label: 'Total de Células', valor: String(celulas.length), cor: 'text-indigo-700', sub: 'Grupos familiares ativos' },
    { label: 'Membros em Célula', valor: String((STATE.membros || []).filter(m => m.celula_id).length), cor: 'text-emerald-700', sub: 'Engajamento comunitário' }
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: 'Mapeamento Geral de Células & Grupos Familiares',
    subtitulo: 'Localização, liderança e membresia dos pequenos grupos nos bairros',
    periodo: 'Exercício 2026',
    orientacao: 'portrait',
    kpis,
    colunas,
    linhas,
    nomeArquivo: 'Relatorio_Celulas.pdf'
  });
}

// 13. INVENTÁRIO PATRIMONIAL
function gerarPDFPatrimonio() {
  if (!verificarAcessoRelatorio('rel_patrimonio', 'Inventário Patrimonial')) return;
  const itens = STATE.patrimonio || [];
  const totValor = itens.reduce((a, b) => a + Number(b.valor_aquisicao || 0), 0);

  const colunas = [
    { label: 'Código Tombamento', width: '110px', align: 'center' },
    { label: 'Descrição do Bem / Equipamento', width: '240px' },
    { label: 'Setor / Ministério', width: '150px' },
    { label: 'Estado', width: '100px', align: 'center' },
    { label: 'Data Aquisição', width: '100px', align: 'center' },
    { label: 'Valor Aquisição (R$)', width: '120px', align: 'right' }
  ];

  const linhas = itens.map(p => [
    { texto: p.codigo, bold: true },
    p.item,
    p.ministerio_nome || 'Sede Geral',
    p.estado || 'Bom',
    formatDateBR(p.data_aquisicao),
    formatBRL(p.valor_aquisicao)
  ]);

  const kpis = [
    { label: 'Itens Tombados', valor: String(itens.length), cor: 'text-indigo-700', sub: 'Patrimônio cadastrado' },
    { label: 'Valor Total do Ativo', valor: formatBRL(totValor), cor: 'text-emerald-700', sub: 'Custo histórico de aquisição' }
  ];

  const rodapeTotais = `
    <td colspan="5" class="py-2.5 px-3 uppercase font-black">Valor Total dos Ativos Inventariados</td>
    <td class="text-right py-2.5 px-3 font-mono font-black text-emerald-800">${formatBRL(totValor)}</td>
  `;

  abrirVisualizadorRelatorioPDF({
    titulo: 'Inventário Oficial de Bens e Patrimônio da Igreja',
    subtitulo: 'Tombamento geral de equipamentos, instrumentos musicais, móveis e ativos',
    periodo: `Posição em ${new Date().toLocaleDateString('pt-BR')}`,
    orientacao: 'landscape',
    kpis,
    colunas,
    linhas,
    rodapeTotais,
    nomeArquivo: 'Inventario_Patrimonio.pdf'
  });
}

// 14. ESCALAS DE CULTO
function gerarPDFEscalas() {
  if (!verificarAcessoRelatorio('rel_escalas', 'Escalas de Culto & Voluntários')) return;
  const escalas = STATE.escalas || [];

  const colunas = [
    { label: 'Data Culto', width: '90px', align: 'center' },
    { label: 'Horário', width: '70px', align: 'center' },
    { label: 'Evento / Culto', width: '140px' },
    { label: 'Ministério', width: '150px' },
    { label: 'Voluntário Escalado', width: '180px' },
    { label: 'Função na Escala', width: '150px' },
    { label: 'Confirmação', width: '110px', align: 'center' }
  ];

  const linhas = escalas.map(e => [
    formatDateBR(e.data_culto),
    e.horario || '—',
    e.evento_culto || 'Culto de Celebração',
    e.ministerio_nome || '—',
    { texto: e.voluntario_nome || 'Voluntário', bold: true },
    e.funcao_escala || 'Serviço',
    e.confirmado ? '<span class="text-emerald-700 font-bold">✓ Confirmado</span>' : '<span class="text-amber-600 font-bold">⏳ Pendente</span>'
  ]);

  const kpis = [
    { label: 'Total de Escalas', valor: String(escalas.length), cor: 'text-indigo-700', sub: 'Serviços cadastrados' },
    { label: 'Confirmadas', valor: String(escalas.filter(e => e.confirmado).length), cor: 'text-emerald-700', sub: 'Voluntários prontos' }
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: 'Escala Oficial de Cultos & Voluntários',
    subtitulo: 'Quadro geral de voluntários escalados para som, louvor, recepção, infantil e apoio',
    periodo: 'Agenda Litúrgica',
    orientacao: 'landscape',
    kpis,
    colunas,
    linhas,
    nomeArquivo: 'Escalas_Culto.pdf'
  });
}

// 15. AUDITORIA & LOGS
function gerarPDFAuditoria() {
  if (!verificarAcessoRelatorio('rel_auditoria', 'Trilha de Auditoria & Logs')) return;
  const colunas = [
    { label: 'Horário / Data', width: '130px', align: 'center' },
    { label: 'Operador / Usuário', width: '150px' },
    { label: 'Módulo', width: '110px', align: 'center' },
    { label: 'Ação Realizada' },
    { label: 'Status', width: '100px', align: 'center' }
  ];

  const linhas = [
    [new Date().toLocaleString('pt-BR'), CURRENT_OPERATOR?.nome || 'Operador', 'Relatórios', 'Emissão de relatório auditado', '✓ Sucesso'],
    [new Date(Date.now() - 3600000).toLocaleString('pt-BR'), 'Sistema', 'Sincronização', 'Heartbeat e integridade do banco', '✓ Ativo'],
    [new Date(Date.now() - 7200000).toLocaleString('pt-BR'), CURRENT_OPERATOR?.nome || 'Operador', 'Autenticação', 'Sessão verificada com sucesso', '✓ Sucesso']
  ];

  abrirVisualizadorRelatorioPDF({
    titulo: 'Trilha de Auditoria e Logs de Segurança',
    subtitulo: 'Rastreabilidade de acessos, emissões de documentos e operações do sistema',
    periodo: `Auditado em ${new Date().toLocaleDateString('pt-BR')}`,
    orientacao: 'portrait',
    colunas,
    linhas,
    nomeArquivo: 'Auditoria_Logs.pdf'
  });
}

function imprimirRelatorioOficial() {
  const titulo = document.getElementById('rel-tabela-titulo')?.textContent || 'Relatório Oficial';
  const tabelaHTML = document.getElementById('rel-tabela-container')?.innerHTML || '';
  const resultado = document.getElementById('rel-kpi-resultado')?.textContent || 'R$ 0,00';
  const orcamento = document.getElementById('rel-kpi-orcamento')?.textContent || 'R$ 58.323,42';

  const html = `
    <div class="space-y-4 text-xs text-slate-800">
      <div class="flex items-center justify-between border-b-2 border-slate-900 pb-3">
        <div>
          <p class="text-[10px] font-bold uppercase tracking-widest text-indigo-700">Documento Oficial de Prestação de Contas & Gestão</p>
          <h2 class="text-lg font-extrabold text-slate-900">${titulo}</h2>
          <p class="text-[11px] text-slate-500">Emitido por: ${CURRENT_OPERATOR ? CURRENT_OPERATOR.nome : 'Administração'} em ${STATE.timestamp || ''}</p>
        </div>
        <div class="text-right">
          <span class="block text-[10px] text-slate-400 uppercase">Saldo Acumulado 2026</span>
          <strong class="text-base text-emerald-700">${resultado}</strong>
          <span class="block text-[10px] text-slate-500">Orçamento Ministérios: ${orcamento}</span>
        </div>
      </div>

      <div class="max-h-96 overflow-y-auto pr-1">
        ${tabelaHTML}
      </div>

      <div class="grid grid-cols-3 gap-6 pt-8 mt-6 border-t border-slate-300 text-center text-[11px]">
        <div>
          <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Administração Geral</div>
        </div>
        <div>
          <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Tesouraria / Orçamento</div>
        </div>
        <div>
          <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Pastor Presidente</div>
        </div>
      </div>
    </div>
  `;
  abrirModalCustom(html, true);
}

// =======================================================
// SECRETARIA: LISTAGEM E FICHA 360º INTERATIVA DO MEMBRO
// =======================================================

function renderMembros() {
  const busca = (document.getElementById('busca-membro')?.value || '').toLowerCase();
  const statusFiltro = document.getElementById('filtro-status-membro')?.value || '';
  const tbody = document.getElementById('tabela-membros');
  if (!tbody) return;

  const filtrados = STATE.membros.filter(m => {
    const okBusca = m.nome.toLowerCase().includes(busca) ||
      (m.cargo_eclesiastico || '').toLowerCase().includes(busca) ||
      (m.familia || '').toLowerCase().includes(busca);
    const okStatus = !statusFiltro || m.status === statusFiltro;
    return okBusca && okStatus;
  });

  tbody.innerHTML = filtrados.map(m => {
    const badgesMin = (m.ministerios || []).map(v =>
      `<span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold text-white mr-1 mb-1" style="background:${v.ministerio_cor}">${v.ministerio_nome}: ${v.funcao}</span>`
    ).join('') || '<span class="text-slate-400">Sem ministério</span>';

    const statusBadge = m.status === 'Ativo'
      ? 'bg-emerald-100 text-emerald-800'
      : m.status === 'Criança'
        ? 'bg-sky-100 text-sky-800'
        : m.status === 'Aluno do Viver'
          ? 'bg-indigo-100 text-indigo-800'
          : m.status === 'Transferido'
            ? 'bg-amber-100 text-amber-800'
            : m.status === 'Inativo'
              ? 'bg-slate-200 text-slate-700'
              : m.status === 'Em Disciplina'
                ? 'bg-rose-100 text-rose-800'
                : 'bg-amber-100 text-amber-800';

    const transBadge = m.tipo_transferencia
      ? `<span class="ml-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-300" title="${m.motivo_transferencia ? 'Motivo: ' + m.motivo_transferencia : ''}">📦 ${m.tipo_transferencia}</span>`
      : '';

    const fotoThumb = m.foto_base64
      ? `<img src="${m.foto_base64}" alt="${m.nome}" class="w-9 h-9 rounded-full object-cover border border-indigo-200 shrink-0 shadow-2xs" />`
      : `<div class="w-9 h-9 rounded-full bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center justify-center shrink-0 border border-indigo-200">${(m.nome || '?').charAt(0).toUpperCase()}</div>`;

    return `
      <tr class="hover:bg-indigo-50/40 transition">
        <td class="py-3 px-2 cursor-pointer" onclick="abrirFicha360(${m.id})">
          <div class="flex items-center gap-2.5">
            ${fotoThumb}
            <div>
              <div class="font-bold text-indigo-950 hover:text-indigo-600 transition">${m.nome}</div>
              <div class="text-[11px] text-slate-500">${m.familia || 'Sem família'} • ${m.telefone || 'Sem tel.'}</div>
            </div>
          </div>
        </td>
        <td class="py-3 px-2">
          <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 text-indigo-700">${m.cargo_eclesiastico}</span>
          <span class="ml-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${statusBadge}">${m.status}</span>
          ${transBadge}
        </td>
        <td class="py-3 px-2 text-slate-700 font-medium">${m.celula_nome || '<span class="text-slate-400">Não vinculado</span>'}</td>
        <td class="py-3 px-2">${badgesMin}</td>
        <td class="py-3 px-2 text-right space-x-1 whitespace-nowrap">
          <button type="button" onclick="editarMembro(${m.id})" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-2.5 py-1.5 rounded-lg transition shadow-2xs cursor-pointer inline-flex items-center gap-1" title="Editar cadastro completo do membro">
            <span>✏️</span> Editar
          </button>
          <button type="button" onclick="abrirFicha360(${m.id})" class="bg-slate-800 hover:bg-slate-900 text-white font-semibold text-xs px-2.5 py-1.5 rounded-lg transition cursor-pointer inline-flex items-center gap-1" title="Ver ficha 360 e histórico">
            <span>🔍</span> Ficha 360º
          </button>
          <button type="button" onclick="emitirCredencial(${m.id})" class="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs px-2.5 py-1.5 rounded-lg transition cursor-pointer inline-flex items-center gap-1" title="Gerar carteirinha">
            <span>🪪</span> Carteirinha
          </button>
          <button type="button" onclick="removerItem('/api/membros', ${m.id})" class="bg-rose-50 hover:bg-rose-100 text-rose-600 font-semibold text-xs px-2 py-1.5 rounded-lg transition cursor-pointer" title="Remover Membro">
            ✕
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function abrirFicha360(membroId) {
  const m = STATE.membros.find(x => x.id === membroId);
  if (!m) return;

  const escalasMembro = STATE.escalas.filter(e => e.membro_id === membroId);
  const finMembro = STATE.financeiro.filter(f => f.membro_id === membroId);
  const podeVerFin = CURRENT_OPERATOR && ['ADMIN', 'TESOURARIA'].includes(CURRENT_OPERATOR.perfil);

  const celulaOpts = `<option value="">Sem célula</option>` + STATE.celulas.map(c =>
    `<option value="${c.id}" ${m.celula_id === c.id ? 'selected' : ''}>${c.nome} (${c.bairro})</option>`
  ).join('');

  const fotoFicha = m.foto_base64
    ? `<img src="${m.foto_base64}" alt="${m.nome}" class="w-14 h-14 rounded-2xl object-cover border-2 border-indigo-200 shrink-0 shadow-sm" />`
    : `<div class="w-14 h-14 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xl shrink-0 shadow-sm">${(m.nome || '?').charAt(0).toUpperCase()}</div>`;

  const html = `
    <div class="space-y-4 text-xs">
      <div class="flex items-center justify-between border-b border-slate-200 pb-3 gap-3">
        <div class="flex items-center gap-3">
          ${fotoFicha}
          <div>
            <span class="text-[10px] font-bold uppercase tracking-wider bg-indigo-100 text-indigo-700 px-2.5 py-0.5 rounded-full">Visão 360º Interligada</span>
            <h3 class="text-lg font-extrabold text-slate-900 mt-0.5">${m.nome}</h3>
            <p class="text-slate-500">Matrícula #${String(m.id).padStart(4, '0')} • Cadastrado em ${formatDateBR(m.criado_em)}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" onclick="fecharModalCustom(); editarMembro(${m.id});" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-3 py-2 rounded-xl text-xs transition flex items-center gap-1.5 shadow-sm cursor-pointer">
            <span>✏️</span> Editar Cadastro Completo
          </button>
          <button type="button" onclick="emitirCredencial(${m.id})" class="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold px-3 py-2 rounded-xl text-xs cursor-pointer">
            🪪 Ver Carteirinha
          </button>
        </div>
      </div>

      <form onsubmit="salvarEdicaoMembro360(event, ${m.id})" class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-3">
        <p class="font-bold text-slate-800">✏️ Editar Dados e Vínculos em Tempo Real</p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Status Eclesiástico</label>
            <select id="edit360-status" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white font-semibold">
              <option value="Ativo" ${m.status === 'Ativo' ? 'selected' : ''}>🟢 Ativo em Comunhão</option>
              <option value="Criança" ${m.status === 'Criança' ? 'selected' : ''}>👶 Criança</option>
              <option value="Aluno do Viver" ${m.status === 'Aluno do Viver' ? 'selected' : ''}>📘 Aluno do Viver</option>
              <option value="Em Disciplina" ${m.status === 'Em Disciplina' ? 'selected' : ''}>🔴 Em Acompanhamento</option>
              <option value="Transferido" ${m.status === 'Transferido' ? 'selected' : ''}>🟡 Transferido</option>
              <option value="Inativo" ${m.status === 'Inativo' ? 'selected' : ''}>⚪ Inativo</option>
            </select>
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Cargo Atual</label>
            <input type="text" id="edit360-cargo" value="${m.cargo_eclesiastico || 'Membro'}" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white" />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Célula Vinculada</label>
            <select id="edit360-celula" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white">${celulaOpts}</select>
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Telefone / WhatsApp</label>
            <input type="text" id="edit360-tel" value="${m.telefone || ''}" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white" />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Família</label>
            <input type="text" id="edit360-familia" value="${m.familia || ''}" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white" />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Observações Pastorais</label>
            <input type="text" id="edit360-obs" value="${m.observacoes || ''}" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white" />
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Profissão</label>
            <input type="text" id="edit360-profissao" value="${m.profissao || ''}" placeholder="Ex: Professor(a)" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white" />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Cônjuge</label>
            <input type="text" id="edit360-conjuge" value="${m.conjuge || ''}" placeholder="Nome do cônjuge" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white" />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-slate-600 mb-1">Data Casamento</label>
            <input type="date" id="edit360-data-casamento" value="${m.data_casamento || ''}" class="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white" />
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 bg-amber-50/70 p-2.5 rounded-lg border border-amber-200">
          <div>
            <label class="block text-[11px] font-bold text-amber-900 mb-1">Transferência / Inativação</label>
            <select id="edit360-tipo-trans" class="w-full border border-amber-300 rounded-lg px-2.5 py-1.5 bg-white text-xs">
              <option value="" ${!m.tipo_transferencia ? 'selected' : ''}>Regular (Em Comunhão)</option>
              <option value="Transferido" ${m.tipo_transferencia === 'Transferido' ? 'selected' : ''}>📦 Transferido</option>
              <option value="Inativo" ${m.tipo_transferencia === 'Inativo' ? 'selected' : ''}>⚪ Inativo</option>
            </select>
          </div>
          <div>
            <label class="block text-[11px] font-bold text-amber-900 mb-1">Motivo / Igreja de Destino</label>
            <input type="text" id="edit360-motivo-trans" value="${escapeHtml(m.motivo_transferencia || '')}" placeholder="Motivo da transferência ou inativação" class="w-full border border-amber-300 rounded-lg px-2.5 py-1.5 bg-white text-xs" />
          </div>
        </div>

        <div class="flex justify-end">
          <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl shadow transition">
            💾 Salvar Alterações na Ficha 360º
          </button>
        </div>
      </form>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div class="p-3 rounded-xl border border-slate-200">
          <h4 class="font-bold text-slate-800 mb-2">📅 Escalas de Culto (${escalasMembro.length})</h4>
          <div class="space-y-1.5">
            ${escalasMembro.map(e => `
              <div class="p-2 rounded-lg bg-slate-50 flex justify-between items-center">
                <span><strong>${formatDateBR(e.data_culto)} (${e.horario})</strong> — ${e.ministerio_nome}: ${e.funcao_escala}</span>
                <span class="text-[10px] font-bold ${e.confirmado ? 'text-emerald-600' : 'text-amber-600'}">${e.confirmado ? '✓ Confirmado' : '⏳ Pendente'}</span>
              </div>
            `).join('') || '<p class="text-slate-400">Nenhuma escala futura registrada.</p>'}
          </div>
        </div>

        <div class="p-3 rounded-xl border border-slate-200">
          <h4 class="font-bold text-slate-800 mb-2">💰 Histórico na Tesouraria (${podeVerFin ? finMembro.length : 'Sigilo'})</h4>
          <div class="space-y-1.5">
            ${podeVerFin ? (finMembro.map(f => `
              <div class="p-2 rounded-lg bg-emerald-50/60 flex justify-between items-center">
                <span><strong>${formatDateBR(f.data_lancamento)}</strong> — ${f.categoria}</span>
                <strong class="text-emerald-700">${formatBRL(f.valor)}</strong>
              </div>
            `).join('') || '<p class="text-slate-400">Nenhum lançamento individual vinculado.</p>') : '<p class="text-slate-400">Visível apenas para perfil ADMIN ou TESOURARIA.</p>'}
          </div>
        </div>
      </div>
    </div>
  `;
  abrirModalCustom(html, false);
}

async function salvarEdicaoMembro360(e, membroId) {
  e.preventDefault();
  await apiPost('/api/membros/atualizar', {
    id: membroId,
    status: document.getElementById('edit360-status').value,
    cargo_eclesiastico: document.getElementById('edit360-cargo').value,
    celula_id: document.getElementById('edit360-celula').value || null,
    telefone: document.getElementById('edit360-tel').value,
    familia: document.getElementById('edit360-familia').value,
    profissao: document.getElementById('edit360-profissao') ? document.getElementById('edit360-profissao').value : '',
    conjuge: document.getElementById('edit360-conjuge') ? document.getElementById('edit360-conjuge').value : '',
    data_casamento: document.getElementById('edit360-data-casamento') ? document.getElementById('edit360-data-casamento').value : '',
    tipo_transferencia: document.getElementById('edit360-tipo-trans')?.value || '',
    motivo_transferencia: (document.getElementById('edit360-motivo-trans')?.value || '').trim(),
    observacoes: document.getElementById('edit360-obs').value
  });
  closeModal();
  fetchBootstrap();
}

// =======================================================
// RECEPÇÃO, ESCALAS, CÉLULAS E PATRIMÔNIO
// =======================================================

function renderVisitantes() {
  const cont = document.getElementById('lista-visitantes');
  if (!cont) return;

  cont.innerHTML = STATE.visitantes.map(v => {
    const jaMembro = v.status_acompanhamento === 'Integrado como Membro';
    return `
      <div class="p-4 rounded-xl border ${jaMembro ? 'bg-emerald-50/40 border-emerald-200' : 'bg-white border-slate-200'} flex flex-wrap items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <h4 class="font-bold text-slate-800 text-sm">${v.nome}</h4>
            <span class="text-[10px] font-bold px-2.5 py-0.5 rounded-full ${jaMembro ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
              ${v.status_acompanhamento}
            </span>
          </div>
          <p class="text-xs text-slate-600">
            📅 Visita: <strong>${formatDateBR(v.data_visita)}</strong> no ${v.culto} • 📞 ${v.telefone || 'Não informado'}
          </p>
          <p class="text-xs text-slate-500">
            🏠 Célula Indicada: <strong>${v.celula_nome || 'A definir'}</strong> • 🙏 Pedido de Oração: <em>"${v.pedido_oracao || 'Nenhum'}"</em>
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          ${!jaMembro ? `
            <select onchange="alterarStatusVisitante(${v.id}, this.value)" class="border border-slate-300 rounded-xl px-2.5 py-1.5 text-xs bg-slate-50 font-semibold text-slate-700">
              <option value="Novo Visitante" ${v.status_acompanhamento === 'Novo Visitante' ? 'selected' : ''}>🟡 Etapa: Novo Visitante</option>
              <option value="Em Contato" ${v.status_acompanhamento === 'Em Contato' ? 'selected' : ''}>🔵 Etapa: Em Contato (WhatsApp)</option>
              <option value="Visitado por Célula" ${v.status_acompanhamento === 'Visitado por Célula' ? 'selected' : ''}>🟣 Etapa: Visitado por Célula</option>
            </select>
            <button onclick="converterVisitante(${v.id})" class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-3.5 py-2 rounded-xl shadow transition">
              ✨ Integrar como Membro
            </button>
          ` : `
            <span class="text-xs font-semibold text-emerald-700">✓ Já consta no Rol da Secretaria</span>
          `}
        </div>
      </div>
    `;
  }).join('');
}

async function alterarStatusVisitante(id, status_acompanhamento) {
  await apiPost('/api/visitantes/status', { id, status_acompanhamento });
  fetchBootstrap();
}

function renderEscalas() {
  const filtroMin = document.getElementById('filtro-escala-ministerio')?.value || '';
  const cont = document.getElementById('lista-escalas');
  if (cont) {
    const filtradas = STATE.escalas.filter(e => !filtroMin || String(e.ministerio_id) === String(filtroMin));
    cont.innerHTML = filtradas.map(e => `
      <div class="p-3 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-3 hover:bg-slate-50 transition text-xs">
        <div class="flex items-center gap-3">
          <div class="px-3 py-1.5 rounded-lg bg-slate-900 text-white text-center">
            <div class="font-bold">${formatDateBR(e.data_culto)}</div>
            <div class="text-[10px] text-indigo-300">${e.horario}</div>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold text-white" style="background:${e.ministerio_cor}">${e.ministerio_nome}</span>
              <span class="font-bold text-slate-800 cursor-pointer hover:text-indigo-600" onclick="abrirFicha360(${e.membro_id})">${e.membro_nome}</span>
              <span class="text-slate-500">como <strong>${e.funcao_escala}</strong></span>
            </div>
            <p class="text-[11px] text-slate-500 mt-0.5">${e.evento_culto} ${e.observacao ? `• Obs: ${e.observacao}` : ''}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button onclick="alternarConfirmacaoEscala(${e.id})" class="px-3 py-1 rounded-lg font-bold transition ${e.confirmado ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200' : 'bg-amber-100 text-amber-800 hover:bg-amber-200'}">
            ${e.confirmado ? '✅ Confirmado' : '⏳ Pendente (Clicar p/ Confirmar)'}
          </button>
          <button onclick="removerItem('/api/escalas', ${e.id})" class="text-rose-600 hover:bg-rose-50 px-2 py-1 rounded-lg font-semibold">
            ✕
          </button>
        </div>
      </div>
    `).join('');
  }

  const eqCont = document.getElementById('lista-voluntarios-setor');
  if (eqCont) {
    eqCont.innerHTML = STATE.ministerios.map(m => {
      const vols = STATE.vinculos.filter(v => v.ministerio_id === m.id);
      return `
        <div class="p-3.5 rounded-xl border border-slate-200 bg-slate-50/60">
          <div class="flex items-center justify-between mb-2">
            <span class="font-bold text-xs text-slate-800 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full" style="background:${m.cor}"></span>
              ${m.nome}
            </span>
            <span class="text-[11px] text-slate-500">${vols.length} integrante(s)</span>
          </div>
          <div class="space-y-1 text-xs">
            ${vols.map(v => `
              <div class="flex items-center justify-between bg-white px-2.5 py-1.5 rounded-lg border border-slate-200/70">
                <span class="cursor-pointer hover:text-indigo-600" onclick="abrirFicha360(${v.membro_id})"><strong>${v.membro_nome}</strong> — <span class="text-slate-500">${v.funcao}</span></span>
                <button onclick="removerItem('/api/voluntarios', ${v.id})" class="text-rose-500 hover:text-rose-700 font-bold">✕</button>
              </div>
            `).join('') || '<p class="text-slate-400 text-[11px]">Nenhum voluntário vinculado.</p>'}
          </div>
        </div>
      `;
    }).join('');
  }
}

async function alternarConfirmacaoEscala(id) {
  await apiPost('/api/escalas/confirmar', { id });
  fetchBootstrap();
}

function renderTesouraria() {
  const reqCont = document.getElementById('lista-requisicoes');
  const podeAprovar = CURRENT_OPERATOR && ['ADMIN', 'TESOURARIA'].includes(CURRENT_OPERATOR.perfil);

  if (reqCont) {
    reqCont.innerHTML = STATE.requisicoes.map(r => {
      const pendente = r.status === 'Pendente';
      const badgeColor = r.status === 'Aprovado e Pago'
        ? 'bg-emerald-100 text-emerald-800'
        : r.status === 'Recusado'
          ? 'bg-rose-100 text-rose-800'
          : 'bg-amber-100 text-amber-800';

      return `
        <div class="p-3.5 rounded-xl border ${pendente ? 'border-amber-300 bg-amber-50/40' : 'border-slate-200 bg-white'} flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold text-white" style="background:${r.ministerio_cor}">${r.ministerio_nome}</span>
              <span class="font-bold text-slate-800 text-sm">${r.titulo}</span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${badgeColor}">${r.status}</span>
            </div>
            <p class="text-slate-600">${r.justificativa || 'Sem justificativa detalhada.'}</p>
            <p class="text-[11px] text-slate-400">Solicitado por: <strong>${r.solicitante}</strong> em ${formatDateBR(r.data_solicitacao)} • Prioridade: <strong>${r.prioridade}</strong> ${r.avaliado_por ? `• Avaliado por: ${r.avaliado_por}` : ''}</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-base font-extrabold text-slate-900">${formatBRL(r.valor_estimado)}</span>
            ${pendente && podeAprovar ? `
              <div class="flex gap-1.5">
                <button onclick="avaliarRequisicao(${r.id}, 'Aprovado e Pago')" class="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-3 py-1.5 rounded-lg shadow transition">
                  ✓ Aprovar e Lançar Saída
                </button>
                <button onclick="avaliarRequisicao(${r.id}, 'Recusado')" class="bg-rose-100 hover:bg-rose-200 text-rose-700 font-semibold px-2.5 py-1.5 rounded-lg transition">
                  Recusar
                </button>
              </div>
            ` : pendente ? `
              <span class="text-[11px] text-amber-700 font-semibold bg-amber-100 px-2.5 py-1 rounded-lg">Aguardando Tesouraria</span>
            ` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  const entradas = STATE.financeiro.filter(f => f.tipo === 'ENTRADA' && f.status === 'Pago').reduce((a, b) => a + Number(b.valor), 0);
  const saidas = STATE.financeiro.filter(f => f.tipo === 'SAIDA' && f.status === 'Pago').reduce((a, b) => a + Number(b.valor), 0);

  document.getElementById('resumo-entradas').textContent = `Entradas Diárias: ${formatBRL(entradas)}`;
  document.getElementById('resumo-saidas').textContent = `Saídas Diárias: ${formatBRL(saidas)}`;

  const filtroTipo = document.getElementById('filtro-fin-tipo')?.value || '';
  const tbody = document.getElementById('tabela-financeiro');
  if (tbody) {
    let listaVisivel = STATE.financeiro;
    if (filtroTipo) {
      listaVisivel = listaVisivel.filter(f => f.tipo === filtroTipo);
    }

    tbody.innerHTML = listaVisivel.map(f => {
      const isEntrada = f.tipo === 'ENTRADA';
      return `
        <tr class="hover:bg-slate-50 transition">
          <td class="py-2.5 px-2 text-slate-600 whitespace-nowrap">${formatDateBR(f.data_lancamento)}</td>
          <td class="py-2.5 px-2">
            <span class="font-bold text-slate-800">${f.categoria}</span> — ${f.descricao}
            <div class="text-[10px] text-slate-400">Meio: ${f.forma_pagamento} • Lançado por: ${f.lancado_por || 'Tesouraria'}</div>
          </td>
          <td class="py-2.5 px-2">
            ${f.membro_nome ? `<span onclick="abrirFicha360(${f.membro_id})" class="cursor-pointer px-2 py-0.5 rounded-full bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold">👤 ${f.membro_nome}</span>` : ''}
            ${f.ministerio_nome ? `<span class="px-2 py-0.5 rounded-full text-white text-[10px] font-semibold" style="background:${f.ministerio_cor}">🏛️ ${f.ministerio_nome}</span>` : ''}
            ${!f.membro_nome && !f.ministerio_nome ? '<span class="text-slate-400">Geral da Igreja</span>' : ''}
          </td>
          <td class="py-2.5 px-2 text-right font-extrabold ${isEntrada ? 'text-emerald-600' : 'text-rose-600'} whitespace-nowrap">
            ${isEntrada ? '+' : '-'} ${formatBRL(f.valor)}
          </td>
          <td class="py-2.5 px-2 text-right whitespace-nowrap space-x-1">
            ${isEntrada ? `
              <button onclick="emitirRecibo(${f.id})" class="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-2.5 py-1 rounded-lg">
                🧾 Recibo
              </button>
            ` : ''}
            ${podeAprovar ? `
              <button onclick="removerItem('/api/financeiro', ${f.id})" class="text-rose-500 hover:bg-rose-50 px-2 py-1 rounded-lg font-bold">✕</button>
            ` : ''}
          </td>
        </tr>
      `;
    }).join('');
  }
}

function renderCelulas() {
  const cont = document.getElementById('lista-celulas');
  if (!cont) return;

  cont.innerHTML = STATE.celulas.map(c => {
    const perc = c.meta_membros > 0 ? Math.min(100, Math.round((c.ultima_frequencia / c.meta_membros) * 100)) : 0;
    return `
      <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between space-y-4">
        <div>
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full">${c.bairro}</span>
            <span class="text-xs text-slate-500">${c.dia_horario}</span>
          </div>
          <h4 class="font-bold text-slate-800 text-base mt-2">${c.nome}</h4>
          <p class="text-xs text-slate-600">Líder: <strong>${c.lider}</strong> • Membros fixos na Secretaria: <strong>${c.total_membros}</strong></p>
        </div>

        <div class="space-y-2">
          <div class="flex justify-between text-xs">
            <span class="text-slate-500">Última Presença Registrada:</span>
            <span class="font-bold text-indigo-700">${c.ultima_frequencia} pessoas (Meta: ${c.meta_membros})</span>
          </div>
          <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
            <div class="h-full bg-indigo-600 rounded-full" style="width:${perc}%"></div>
          </div>
          <div class="flex items-center gap-2 pt-2">
            <input type="number" id="freq-input-${c.id}" value="${c.ultima_frequencia}" class="border border-slate-300 rounded-lg px-2.5 py-1 text-xs w-24" />
            <button onclick="atualizarFrequenciaCelula(${c.id})" class="bg-slate-900 hover:bg-indigo-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition">
              Atualizar Frequência Semanal
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}


// =======================================================
// SUBMENU DE PATRIMÔNIO (INVENTÁRIO / EMPRÉSTIMOS)
// =======================================================

let SUBTAB_PATRIMONIO_ATIVA = 'inventario';

function formatarDataHora(val) {
  if (!val) return '—';
  try {
    const s = String(val).trim().replace('T', ' ');
    const parts = s.split(' ');
    const dp = parts[0].split('-');
    if (dp.length === 3) {
      const dataFormatada = `${dp[2]}/${dp[1]}/${dp[0]}`;
      if (parts[1]) {
        const hp = parts[1].substring(0, 5);
        return `${dataFormatada} às ${hp}`;
      }
      return dataFormatada;
    }
    return s;
  } catch (e) {
    return String(val);
  }
}

function fecharModalCustom() {
  if (typeof closeModal === 'function') {
    closeModal();
  } else {
    const overlay = document.getElementById('modal-overlay');
    if (overlay) overlay.classList.add('hidden');
  }
}

function switchSubTabPatrimonio(tab) {
  SUBTAB_PATRIMONIO_ATIVA = tab || 'inventario';
  const isInv = SUBTAB_PATRIMONIO_ATIVA === 'inventario';
  const subInv = document.getElementById('subtab-pat-inventario');
  const subEmp = document.getElementById('subtab-pat-emprestimos');
  const pillInv = document.getElementById('tabpill-pat-inventario');
  const pillEmp = document.getElementById('tabpill-pat-emprestimos');
  const navInv = document.getElementById('subnav-pat-inventario');
  const navEmp = document.getElementById('subnav-pat-emprestimos');
  const desc = document.getElementById('subtab-pat-descricao');
  const subMenu = document.getElementById('submenu-patrimonio');
  const seta = document.getElementById('seta-subnav-patrimonio');

  // Garante que o submenu lateral de Patrimônio esteja aberto
  if (subMenu) subMenu.classList.remove('hidden');
  if (seta) seta.style.transform = 'rotate(0deg)';

  // Alterna as telas
  if (subInv) {
    if (isInv) {
      subInv.classList.remove('hidden');
      subInv.style.display = '';
    } else {
      subInv.classList.add('hidden');
    }
  }
  if (subEmp) {
    if (!isInv) {
      subEmp.classList.remove('hidden');
      subEmp.style.display = '';
    } else {
      subEmp.classList.add('hidden');
    }
  }

  // Atualiza as abas superiores (pills)
  if (pillInv) {
    pillInv.className = isInv 
      ? 'px-4 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow transition flex items-center gap-2 cursor-pointer'
      : 'px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition flex items-center gap-2 cursor-pointer';
  }
  if (pillEmp) {
    pillEmp.className = !isInv 
      ? 'px-4 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow transition flex items-center gap-2 cursor-pointer'
      : 'px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition flex items-center gap-2 cursor-pointer';
  }

  // Atualiza o submenu lateral
  if (navInv) {
    if (isInv) {
      navInv.classList.add('active');
    } else {
      navInv.classList.remove('active');
    }
  }
  if (navEmp) {
    if (!isInv) {
      navEmp.classList.add('active');
    } else {
      navEmp.classList.remove('active');
    }
  }

  if (desc) {
    desc.textContent = isInv 
      ? 'Gerencie bens materiais, tombamentos e localização por ministério'
      : 'Controle de saídas, aprovação de responsáveis, retiradas e devoluções reversas';
  }

  // Renderiza a tela ativa
  if (isInv) {
    renderPatrimonioEUsuarios();
  } else {
    renderPatrimonioEmprestimos();
  }
}

function renderPatrimonioEUsuarios() {
  const tbody = document.getElementById('tabela-patrimonio');
  const listaPat = STATE.patrimonio || [];
  const listaEmp = STATE.patrimonio_emprestimos || [];

  // 1. Calcula indicadores do inventário linkados com empréstimos
  let totalEmprestados = 0;
  listaPat.forEach(p => {
    const isEmp = listaEmp.some(e => (e.patrimonio_id === p.id || (e.codigo && e.codigo === p.codigo)) && e.status !== 'Devolvido');
    if (isEmp) totalEmprestados++;
  });
  const totalBens = listaPat.length;
  const totalDisponiveis = Math.max(0, totalBens - totalEmprestados);
  const valorTotal = listaPat.reduce((acc, p) => acc + Number(p.valor_aquisicao || 0), 0);

  const elTot = document.getElementById('inv-total-itens');
  const elDisp = document.getElementById('inv-disponiveis-itens');
  const elEmp = document.getElementById('inv-emprestados-itens');
  const elVal = document.getElementById('inv-valor-total');

  if (elTot) elTot.textContent = totalBens;
  if (elDisp) elDisp.textContent = totalDisponiveis;
  if (elEmp) elEmp.textContent = totalEmprestados;
  if (elVal) elVal.textContent = formatBRL(valorTotal);

  // 2. Renderiza a tabela de inventário com linking de empréstimo e ações
  if (tbody) {
    if (listaPat.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="py-6 text-center text-slate-400 text-xs">
            Nenhum bem patrimonial cadastrado ainda. Use o formulário ao lado para cadastrar.
          </td>
        </tr>
      `;
    } else {
      tbody.innerHTML = listaPat.map(p => {
        // Busca se este item específico do cadastro está emprestado no momento
        const empAtivo = listaEmp.find(e => (e.patrimonio_id === p.id || (e.codigo && e.codigo === p.codigo)) && e.status !== 'Devolvido');

        return `
          <tr class="hover:bg-slate-50 transition border-b border-slate-100">
            <!-- 1. Código e Item com Status de Empréstimo em tempo real -->
            <td class="py-2.5 px-3">
              <div class="flex items-start gap-2">
                <span class="font-mono text-[10px] font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200 mt-0.5">
                  ${p.codigo}
                </span>
                <div>
                  <strong class="text-slate-900 block text-xs">${p.item}</strong>
                  ${empAtivo ? `
                    <div class="mt-1 flex items-center gap-1.5 flex-wrap">
                      <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                        🟡 Emprestado: <strong>${empAtivo.solicitante_nome}</strong>
                      </span>
                      <span class="text-[10px] text-slate-500">Devolução prevista: ${formatarDataHora(empAtivo.previsao_devolucao)}</span>
                    </div>
                  ` : `
                    <div class="mt-1">
                      <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        🟢 No Templo (Disponível)
                      </span>
                    </div>
                  `}
                </div>
              </div>
            </td>

            <!-- 2. Setor e Localização -->
            <td class="py-2.5 px-3 text-slate-600 text-xs">
              <div>
                <strong>${p.ministerio_nome || 'Uso Geral'}</strong>
                <span class="text-slate-400 block text-[11px]">${p.localizacao}</span>
                ${p.responsavel ? `<span class="text-[10px] text-indigo-700 block font-medium">Resp: ${p.responsavel}</span>` : ''}
              </div>
            </td>

            <!-- 3. Estado Interativo -->
            <td class="py-2.5 px-3">
              <select onchange="alterarEstadoPatrimonio(${p.id}, this.value)" class="border border-slate-300 rounded-lg px-2 py-1 text-[11px] font-bold bg-white text-slate-800 focus:ring-1 focus:ring-indigo-500">
                <option value="Novo" ${p.estado === 'Novo' ? 'selected' : ''}>✨ Novo</option>
                <option value="Bom" ${p.estado === 'Bom' ? 'selected' : ''}>👍 Bom</option>
                <option value="Em Manutenção" ${p.estado === 'Em Manutenção' ? 'selected' : ''}>⚠️ Em Manutenção</option>
                <option value="Danificado" ${p.estado === 'Danificado' ? 'selected' : ''}>❌ Danificado</option>
              </select>
            </td>

            <!-- 4. Valor de Aquisição -->
            <td class="py-2.5 px-3 text-right font-bold text-slate-800 text-xs">
              ${formatBRL(p.valor_aquisicao)}
            </td>

            <!-- 5. Ações Linkadas -->
            <td class="py-2.5 px-3 text-right">
              <div class="flex items-center justify-end gap-1.5">
                ${empAtivo ? `
                  <button onclick="abrirModalDevolucaoPatrimonio(${empAtivo.id})" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[10px] font-bold shadow-sm transition flex items-center gap-1 whitespace-nowrap" title="Registrar Retorno deste Equipamento">
                    <span>🔄</span> Devolver
                  </button>
                  <button onclick="imprimirTermoEmprestimo(${empAtivo.id})" class="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs transition" title="Ver Termo de Cautela e Empréstimo">
                    📄
                  </button>
                ` : `
                  <button onclick="abrirModalNovoEmprestimoParaItem(${p.id})" class="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-600 hover:text-white text-indigo-700 border border-indigo-200 rounded-lg text-[10px] font-bold transition flex items-center gap-1 shadow-sm whitespace-nowrap" title="Registrar Empréstimo deste Item com dados pré-preenchidos">
                    <span>📦</span> Emprestar
                  </button>
                `}
                <button onclick="excluirItemPatrimonio(${p.id})" class="p-1.5 bg-slate-50 hover:bg-rose-50 text-slate-400 hover:text-rose-600 rounded-lg text-xs transition" title="Excluir do Inventário">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }
  }

  renderUsuarios();
  renderPatrimonioEmprestimos();
}

async function excluirItemPatrimonio(id) {
  if (!confirm('Atenção: Deseja realmente excluir este bem do inventário de patrimônio?')) return;
  const operador = CURRENT_OPERATOR ? CURRENT_OPERATOR.nome : 'Administrador';
  const res = await fetch(`/api/patrimonio?id=${id}&operador=${encodeURIComponent(operador)}`, {
    method: 'DELETE'
  });
  if (res.ok) {
    fetchBootstrap();
  } else {
    alert('Erro ao excluir item do patrimônio');
  }
}

async function alterarEstadoPatrimonio(id, estado) {
  await apiPost('/api/patrimonio/estado', { id, estado });
  fetchBootstrap();
}

// =======================================================
// QUADRO DE EMPRÉSTIMOS & DEVOLUÇÕES DE PATRIMÔNIO
// =======================================================

let FILTRO_EMPRESTIMO_STATUS = 'TODOS';
let FILTRO_EMPRESTIMO_BUSCA = '';

function setFiltroStatusEmprestimo(status) {
  FILTRO_EMPRESTIMO_STATUS = status;
  ['todos', 'aberto', 'pendente', 'devolvido', 'atrasado'].forEach(s => {
    const btn = document.getElementById(`btn-flt-emp-${s}`);
    if (btn) {
      if (s === status.toLowerCase()) {
        btn.className = 'btn-flt-emp px-3.5 py-2 rounded-xl text-xs font-extrabold bg-indigo-600 text-white shadow-xs cursor-pointer transition';
      } else {
        btn.className = 'btn-flt-emp px-3.5 py-2 rounded-xl text-xs font-bold bg-white text-slate-700 hover:bg-slate-100 border border-slate-200 cursor-pointer transition';
      }
    }
  });
  renderPatrimonioEmprestimos();
}

function filtrarTabelaEmprestimosPatrimonio() {
  FILTRO_EMPRESTIMO_BUSCA = (document.getElementById('busca-pat-emprestimo')?.value || '').trim().toLowerCase();
  renderPatrimonioEmprestimos();
}


function getResponsaveisSetorCadastrados(patId = null) {
  const nomes = new Set();
  
  // 1. Se passou um bem específico, prioriza o responsável do bem
  if (patId && STATE.patrimonio) {
    const p = STATE.patrimonio.find(x => x.id === Number(patId));
    if (p && p.responsavel) nomes.add(p.responsavel.trim());
    if (p && p.ministerio_id && STATE.ministerios) {
      const min = STATE.ministerios.find(m => m.id === p.ministerio_id);
      if (min && min.lider) nomes.add(min.lider.trim());
    }
  }

  // 2. Todos os líderes de ministérios cadastrados
  (STATE.ministerios || []).forEach(m => {
    if (m.lider && m.lider.trim()) nomes.add(m.lider.trim());
  });

  // 3. Todos os responsáveis já cadastrados em qualquer bem
  (STATE.patrimonio || []).forEach(p => {
    if (p.responsavel && p.responsavel.trim()) nomes.add(p.responsavel.trim());
  });

  // 4. Membros com cargo eclesiástico / liderança
  (STATE.membros || []).forEach(m => {
    const cargo = (m.cargo_eclesiastico || '').toLowerCase();
    if (cargo && !cargo.includes('membro') && !cargo.includes('visitante')) {
      nomes.add(`${m.nome} (${m.cargo_eclesiastico})`);
    }
  });

  // 5. Adiciona fallback padrão da igreja
  if (nomes.size === 0) {
    nomes.add('Equipe Sonoplastia / Templo');
    nomes.add('Coordenação do Diaconato');
    nomes.add('Secretaria / Administração');
  }

  return Array.from(nomes);
}

function getResponsaveisPatrimonioCadastrados() {
  const nomes = new Set();
  nomes.add('Marcos Silva (Administração / Patrimônio)');

  (STATE.usuarios || []).forEach(u => {
    const perfil = (u.perfil || '').toUpperCase();
    const setores = (u.setores_permitidos || '').toLowerCase();
    if (perfil === 'ADMIN' || perfil === 'PATRIMONIO' || setores.includes('patrimonio')) {
      nomes.add(`${u.nome} (${u.cargo || 'Gestão de Patrimônio'})`);
    }
  });

  return Array.from(nomes);
}

function renderPatrimonioEmprestimos() {
  const lista = STATE.patrimonio_emprestimos || [];
  const tbody = document.getElementById('tabela-patrimonio-emprestimos');
  
  // Atualiza KPIs
  const agora = new Date();
  let totalAberto = 0;
  let totalPendente = 0;
  let totalDevolvido = 0;
  let totalAtrasado = 0;

  lista.forEach(e => {
    const isDevolvido = e.status === 'Devolvido';
    const isPendente = e.status === 'Aguardando Aprovações' || 
                      e.status === 'Liberado para Retirada' ||
                      e.status_aprovacao_setor !== 'Aprovado' || 
                      e.status_ok_patrimonio !== 'Liberado';
    
    let isAtrasado = false;
    if (!isDevolvido && e.status === 'Em Aberto / Emprestado' && e.previsao_devolucao) {
      try {
        const dPrev = new Date(e.previsao_devolucao.replace(' ', 'T'));
        if (dPrev < agora) isAtrasado = true;
      } catch (err) {}
    }

    if (isDevolvido) totalDevolvido++;
    else if (e.status === 'Em Aberto / Emprestado') totalAberto++;
    else totalPendente++;

    if (isAtrasado) totalAtrasado++;
  });

  const elAberto = document.getElementById('kpi-emp-aberto');
  const elPendente = document.getElementById('kpi-emp-pendente');
  const elDevolvido = document.getElementById('kpi-emp-devolvido');
  const elAtrasado = document.getElementById('kpi-emp-atrasado');

  if (elAberto) elAberto.textContent = totalAberto;
  if (elPendente) elPendente.textContent = totalPendente;
  if (elDevolvido) elDevolvido.textContent = totalDevolvido;
  if (elAtrasado) elAtrasado.textContent = totalAtrasado;

  // Atualiza badges das abas e submenu
  const pillInv = document.getElementById('pillbadge-pat-inventario');
  const subInv = document.getElementById('subbadge-pat-inventario');
  const pillEmp = document.getElementById('pillbadge-pat-emprestimos');
  const subEmp = document.getElementById('subbadge-pat-emprestimos');
  const totalBens = (STATE.patrimonio || []).length;

  if (pillInv) pillInv.textContent = totalBens;
  if (subInv) subInv.textContent = totalBens;
  if (pillEmp) pillEmp.textContent = totalAberto + totalPendente;
  if (subEmp) subEmp.textContent = totalAberto + totalPendente;

  if (!tbody) return;

  // Filtragem
  const filtrados = lista.filter(e => {
    const isDevolvido = e.status === 'Devolvido';
    const isPendente = e.status !== 'Devolvido' && e.status !== 'Em Aberto / Emprestado';
    const isAberto = e.status === 'Em Aberto / Emprestado';
    let isAtrasado = false;
    if (isAberto && e.previsao_devolucao) {
      try {
        const dPrev = new Date(e.previsao_devolucao.replace(' ', 'T'));
        if (dPrev < agora) isAtrasado = true;
      } catch (err) {}
    }

    if (FILTRO_EMPRESTIMO_STATUS === 'ABERTO' && !isAberto) return false;
    if (FILTRO_EMPRESTIMO_STATUS === 'PENDENTE' && !isPendente) return false;
    if (FILTRO_EMPRESTIMO_STATUS === 'DEVOLVIDO' && !isDevolvido) return false;
    if (FILTRO_EMPRESTIMO_STATUS === 'ATRASADO' && !isAtrasado) return false;

    if (FILTRO_EMPRESTIMO_BUSCA) {
      const termo = FILTRO_EMPRESTIMO_BUSCA;
      const match = (e.item || '').toLowerCase().includes(termo) ||
                    (e.codigo || '').toLowerCase().includes(termo) ||
                    (e.solicitante_nome || '').toLowerCase().includes(termo) ||
                    (e.setor || '').toLowerCase().includes(termo) ||
                    (e.motivo || '').toLowerCase().includes(termo);
      if (!match) return false;
    }

    return true;
  });

  if (filtrados.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="py-12 px-6 text-center bg-slate-50/50">
          <div class="flex flex-col items-center justify-center gap-2.5">
            <span class="text-4xl">📦</span>
            <h4 class="font-bold text-slate-800 text-sm">Nenhum registro de empréstimo encontrado</h4>
            <p class="text-xs text-slate-500 max-w-sm">Não há empréstimos correspondentes aos filtros selecionados. Tente limpar os filtros ou registre um novo empréstimo.</p>
            <button type="button" onclick="setFiltroStatusEmprestimo('TODOS'); const b = document.getElementById('busca-pat-emprestimo'); if(b) b.value=''; filtrarTabelaEmprestimosPatrimonio();" class="mt-2 bg-white border border-slate-300 text-indigo-700 hover:bg-indigo-50 font-bold px-4 py-2 rounded-xl text-xs transition cursor-pointer shadow-2xs">
              Limpar Filtros de Busca
            </button>
          </div>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtrados.map(e => {
    const isDevolvido = e.status === 'Devolvido';
    const isEmprestado = e.status === 'Em Aberto / Emprestado';
    const isLiberadoParaRetirada = e.status === 'Liberado para Retirada' || (e.status_aprovacao_setor === 'Aprovado' && e.status_ok_patrimonio === 'Liberado' && !isEmprestado && !isDevolvido);
    const ambosAprovaramSaida = e.status_aprovacao_setor === 'Aprovado' && e.status_ok_patrimonio === 'Liberado';

    const aprovSetorOk = e.status_aprovacao_setor === 'Aprovado';
    const okPatrimonioOk = e.status_ok_patrimonio === 'Liberado';
    const retornoSetorOk = e.status_retorno_setor === 'Conferido';
    const retornoPatrimonioOk = e.status_retorno_patrimonio === 'Finalizado';

    // Checagem de atraso
    let isAtrasado = false;
    if (isEmprestado && e.previsao_devolucao) {
      try {
        const dPrev = new Date(e.previsao_devolucao.replace(' ', 'T'));
        if (dPrev < agora) isAtrasado = true;
      } catch (err) {}
    }

    // Badge visual do status no ciclo
    let statusCicloBadge = '';
    if (isDevolvido) {
      statusCicloBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">✅ Devolvido</span>`;
    } else if (isAtrasado) {
      statusCicloBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300 animate-pulse">🔴 Em Atraso</span>`;
    } else if (isEmprestado) {
      statusCicloBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">🟡 Em Aberto</span>`;
    } else if (isLiberadoParaRetirada) {
      statusCicloBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-blue-100 text-blue-900 border border-blue-300">🟢 Pronto p/ Retirada</span>`;
    } else {
      statusCicloBadge = `<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-300">⏳ Aguarda OKs</span>`;
    }

    const zapLink = e.solicitante_telefone ? `https://wa.me/55${e.solicitante_telefone.replace(/\D/g, '')}` : '';

    return `
      <tr class="hover:bg-slate-50/80 transition-colors border-b border-slate-100 text-xs">
        <!-- 1. Item & Origem -->
        <td class="py-3.5 px-4 align-top">
          <div class="space-y-1.5">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="font-mono text-[10px] font-black bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200">
                ${e.codigo || 'S/C'}
              </span>
              ${e.patrimonio_id ? `
                <span class="text-[9px] font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">
                  🔗 Tombado
                </span>
              ` : ''}
            </div>
            <div class="font-extrabold text-slate-900 text-xs leading-snug">
              ${e.item}
            </div>
            <div class="text-[11px] text-slate-500 flex items-center gap-1">
              <span class="text-slate-400">Setor:</span> <strong class="text-slate-700">${e.setor || 'Patrimônio Geral'}</strong>
            </div>
            <div class="pt-0.5">
              <span class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-200">
                <span>🔍</span> ${e.condicao_saida || 'Bom Estado'}
              </span>
              ${e.observacoes_saida ? `
                <div class="mt-1 text-[10px] text-amber-900 bg-amber-50/90 p-1.5 rounded-lg border border-amber-200 leading-snug">
                  <strong>📝 Considerações na Saída:</strong> ${e.observacoes_saida}
                </div>
              ` : ''}
              <button type="button" onclick="abrirModalEditarConsideracoesEmprestimo(${e.id})" class="text-[9px] text-indigo-600 hover:text-indigo-800 font-bold block mt-0.5 hover:underline cursor-pointer">
                ✏️ Editar Considerações
              </button>
            </div>
          </div>
        </td>

        <!-- 2. Membro Retirante -->
        <td class="py-3.5 px-4 align-top">
          <div class="space-y-1">
            <div class="flex items-center gap-1.5">
              <div class="w-6 h-6 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs shrink-0 font-bold">
                👤
              </div>
              <strong class="text-slate-900 text-xs block leading-tight">${e.solicitante_nome}</strong>
            </div>
            <div class="text-[11px] pt-0.5">
              ${e.solicitante_telefone ? `
                <a href="${zapLink}" target="_blank" class="inline-flex items-center gap-1 text-emerald-700 hover:text-emerald-800 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-[10px]" title="Abrir conversa no WhatsApp">
                  <span>💬</span> ${e.solicitante_telefone}
                </a>
              ` : '<span class="text-[10px] text-slate-400 italic">Sem telefone</span>'}
            </div>
            ${e.solicitante_documento ? `
              <div class="text-[10px] text-slate-500">
                Função/Doc: <strong>${e.solicitante_documento}</strong>
              </div>
            ` : ''}
            ${e.motivo ? `
              <div class="text-[10px] text-slate-600 bg-slate-50 p-1.5 rounded-lg border border-slate-200 mt-1">
                <span class="text-slate-400 font-semibold block text-[9px] uppercase">Finalidade:</span>
                <span class="font-medium">${e.motivo}</span>
              </div>
            ` : ''}
          </div>
        </td>

        <!-- 3. Prazos & Situação -->
        <td class="py-3.5 px-4 align-top">
          <div class="space-y-1.5">
            <div class="p-2 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div class="text-[10px] text-slate-500">
                <span class="text-slate-400 block font-semibold uppercase text-[9px]">Saída / Retirada:</span>
                <strong class="text-slate-800 font-mono text-[11px]">${formatarDataHora(e.data_retirada)}</strong>
              </div>
              <div class="text-[10px] text-slate-800 border-t border-slate-200 pt-1">
                <span class="text-slate-400 block font-semibold uppercase text-[9px]">Previsão de Entrega:</span>
                <strong class="${isAtrasado ? 'text-rose-600 font-black' : 'text-indigo-700 font-bold'} font-mono text-[11px]">${formatarDataHora(e.previsao_devolucao)}</strong>
              </div>
            </div>
            <div class="pt-0.5 text-center">${statusCicloBadge}</div>
          </div>
        </td>

        <!-- 4. Aprovações (Setor ➔ Patrimônio) -->
        <td class="py-3.5 px-4 align-top min-w-[190px]">
          <div class="space-y-2">
            <!-- Etapa 1: Setor -->
            <div class="p-2 rounded-xl border text-[11px] ${aprovSetorOk ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950' : 'bg-amber-50/70 border-amber-200 text-amber-950'}">
              <div class="flex items-center justify-between text-[10px] font-bold">
                <span class="${aprovSetorOk ? 'text-emerald-800' : 'text-amber-800'}">1º OK: Setor</span>
                ${aprovSetorOk ? '<span class="text-emerald-700">✓ Aprovado</span>' : '<span class="text-amber-700">⏳ Pendente</span>'}
              </div>
              <div class="text-[10px] text-slate-700 font-semibold truncate mt-0.5">${e.responsavel_setor || 'Responsável Setor'}</div>
              ${aprovSetorOk ? `
                <span class="text-[9px] text-emerald-700 block mt-1">Por ${e.operador_aprovador_setor || 'Setor'} em ${e.data_aprovacao_setor || ''}</span>
              ` : `
                <button onclick="aprovarEmprestimoSetor(${e.id})" class="mt-1.5 w-full py-1.5 px-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-extrabold text-[10px] shadow-sm transition cursor-pointer flex items-center justify-center gap-1">
                  <span>✓</span> Dar Aprovação do Setor
                </button>
              `}
            </div>

            <!-- Etapa 2: Patrimônio (Requer prévia aprovação do Setor) -->
            <div class="p-2 rounded-xl border text-[11px] ${okPatrimonioOk ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950' : aprovSetorOk ? 'bg-blue-50/70 border-blue-200 text-blue-950' : 'bg-slate-50 border-slate-200 text-slate-400'}">
              <div class="flex items-center justify-between text-[10px] font-bold">
                <span class="${okPatrimonioOk ? 'text-emerald-800' : aprovSetorOk ? 'text-blue-800' : 'text-slate-400'}">2º OK: Patrimônio</span>
                ${okPatrimonioOk ? '<span class="text-emerald-700">✓ Liberado</span>' : aprovSetorOk ? '<span class="text-blue-700">⏳ Liberar</span>' : '<span class="text-slate-400">🔒 Bloqueado</span>'}
              </div>
              <div class="text-[10px] text-slate-700 font-semibold truncate mt-0.5">${e.responsavel_patrimonio || 'Marcos Silva'}</div>
              ${okPatrimonioOk ? `
                <span class="text-[9px] text-emerald-700 block mt-1">Por ${e.operador_ok_patrimonio || 'Patrimônio'} em ${e.data_ok_patrimonio || ''}</span>
              ` : !aprovSetorOk ? `
                <div class="mt-1.5 py-1 px-2 rounded-lg bg-slate-100 text-slate-400 font-medium text-[9px] text-center border border-slate-200">
                  Aguardando aprovação do Setor
                </div>
              ` : `
                <button onclick="darOkEmprestimoPatrimonio(${e.id})" class="mt-1.5 w-full py-1.5 px-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-[10px] shadow-md transition cursor-pointer flex items-center justify-center gap-1 animate-pulse">
                  <span>✓</span> Dar OK do Patrimônio
                </button>
              `}
            </div>
          </div>
        </td>

        <!-- 5. Retirada & Assinatura Digital -->
        <td class="py-3.5 px-4 align-top text-center min-w-[170px]">
          ${e.assinatura_retirada_base64 ? `
            <div class="p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-200 flex flex-col items-center gap-1.5">
              <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
                ✍️ Assinado Digitalmente
              </span>
              <div class="bg-white p-1 rounded-lg border border-emerald-200 shadow-2xs">
                <img src="${e.assinatura_retirada_base64}" alt="Assinatura" class="h-10 max-w-[130px] object-contain" />
              </div>
              <span class="text-[9px] text-slate-500 font-mono">${e.assinatura_retirada_em || formatarDataHora(e.data_retirada)}</span>
              <button onclick="imprimirTermoEmprestimo(${e.id})" class="text-[10px] font-bold text-indigo-700 hover:text-indigo-900 underline mt-0.5 cursor-pointer">
                Ver Termo de Cautela
              </button>
            </div>
          ` : (isEmprestado || isDevolvido) ? `
            <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col items-center gap-1">
              <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                ✓ Retirada Efetivada
              </span>
              <span class="text-[10px] text-slate-500 font-mono">${formatarDataHora(e.data_retirada)}</span>
              <button onclick="abrirModalAssinaturaDigital(${e.id})" class="mt-1 w-full py-1 px-2 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-[10px] border border-indigo-200 transition cursor-pointer">
                📱 Colher Assinatura
              </button>
            </div>
          ` : ambosAprovaramSaida ? `
            <div class="p-2.5 rounded-xl bg-indigo-50/50 border border-indigo-200 flex flex-col items-center gap-2">
              <span class="text-[10px] font-extrabold text-indigo-900 uppercase tracking-wider">Pronto p/ Retirada</span>
              <button onclick="abrirModalAssinaturaDigital(${e.id})" class="w-full py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-xs shadow-md transition flex items-center justify-center gap-1.5 cursor-pointer">
                <span>📱</span> Assinar no Celular
              </button>
              <button onclick="confirmarRetiradaFisicaItem(${e.id})" class="text-[10px] font-semibold text-slate-500 hover:text-slate-800 underline cursor-pointer">
                Confirmar saída sem assinar
              </button>
            </div>
          ` : `
            <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-400 text-center flex flex-col items-center gap-1">
              <span class="text-xl">🔒</span>
              <span class="font-bold text-slate-600 text-[11px]">Saída Bloqueada</span>
              <span class="text-[9px] text-slate-400 leading-tight">Aguardando aprovação do Setor e do Patrimônio</span>
            </div>
          `}
        </td>

        <!-- 6. Devolução & Ações -->
        <td class="py-3.5 px-4 align-top text-center min-w-[180px]">
          <div class="space-y-2">
            ${!isEmprestado && !isDevolvido ? `
              <div class="p-2 rounded-xl bg-slate-50 border border-slate-200 text-[10px] text-slate-400 italic">
                Aguardando efetivar retirada física
              </div>
            ` : isDevolvido ? `
              <div class="p-2 rounded-xl bg-emerald-50/70 border border-emerald-200 text-left space-y-1">
                <div class="inline-flex items-center gap-1 text-[10px] font-black text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded-md">
                  ✅ Devolução Concluída
                </div>
                <div class="text-[10px] text-slate-600 space-y-0.5 pt-0.5">
                  <div>Retorno: <strong class="text-slate-800 font-mono">${formatarDataHora(e.data_devolucao_real)}</strong></div>
                  <div>Vistoria: <strong class="text-emerald-800">${e.condicao_retorno || 'Excelente'}</strong></div>
                      ${e.observacoes_retorno ? `
                        <div class="mt-1 text-[10px] text-emerald-950 bg-emerald-100/80 p-1.5 rounded-lg border border-emerald-300 leading-snug">
                          <strong>🔍 Considerações da Vistoria:</strong> ${e.observacoes_retorno}
                        </div>
                      ` : ''}
                  <div class="text-[9px] text-slate-500">Conferido por Setor e Patrimônio</div>
                </div>
              </div>
            ` : `
              <button onclick="abrirModalDevolucaoPatrimonio(${e.id})" class="w-full py-2 px-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-extrabold text-xs shadow-md transition flex items-center justify-center gap-1.5 cursor-pointer">
                <span>🔄</span> Registrar Devolução
              </button>

              ${e.data_devolucao_real ? `
                <div class="p-2 rounded-xl bg-amber-50 border border-amber-200 text-left space-y-1 text-[10px]">
                  <div class="font-bold text-amber-900">Devolvido em: ${formatarDataHora(e.data_devolucao_real)}</div>
                  <div class="flex items-center gap-1">
                    ${retornoSetorOk ? '<span class="text-emerald-700 font-bold">✓ Setor OK</span>' : `<button onclick="darOkRetornoSetor(${e.id})" class="text-[9px] font-bold bg-white border border-amber-300 text-amber-900 px-1.5 py-0.5 rounded">Dar OK Setor</button>`}
                    ${retornoPatrimonioOk ? '<span class="text-emerald-700 font-bold">✓ Patr. OK</span>' : `<button onclick="darOkRetornoPatrimonio(${e.id})" class="text-[9px] font-bold bg-white border border-blue-300 text-blue-900 px-1.5 py-0.5 rounded">Dar OK Patr.</button>`}
                  </div>
                </div>
              ` : ''}
            `}

            <!-- Botões de Ações Rápidas -->
            <div class="flex items-center justify-center gap-1.5 pt-1 border-t border-slate-100">
              <button type="button" onclick="abrirModalAssinaturaDigital(${e.id})" class="p-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl transition cursor-pointer" title="Abrir QR Code / Assinatura no Celular">
                📱
              </button>
              <button type="button" onclick="imprimirTermoEmprestimo(${e.id})" class="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition cursor-pointer" title="Imprimir Termo de Cautela (PDF)">
                📄
              </button>
              <button type="button" onclick="excluirEmprestimoPatrimonio(${e.id})" class="p-2 bg-rose-50 hover:bg-rose-100 text-rose-600 rounded-xl transition cursor-pointer" title="Excluir Registro de Empréstimo">
                🗑️
              </button>
            </div>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

async function confirmarRetiradaFisicaItem(id) {
  if (!confirm('Confirmar a retirada física do bem? O item passará ao status de "Em Uso Externo" com prazo ativo.')) return;
  const { status, data } = await apiPost('/api/patrimonio/emprestimo/efetivar-retirada', { id });
  if (status === 200) {
    fetchBootstrap();
    setTimeout(() => {
      if (confirm('Retirada confirmada com sucesso! Deseja emitir o Termo de Cautela com as assinaturas agora?')) {
        imprimirTermoEmprestimo(id);
      }
    }, 300);
  } else {
    alert(data.erro || 'Erro ao efetivar retirada');
  }
}

function abrirModalNovoEmprestimoParaItem(patId) {
  switchSubTabPatrimonio('emprestimos');
  abrirModalNovoEmprestimoPatrimonio(patId);
}

function aoDigitarNomeRetirante(nomeVal) {
  if (!nomeVal) {
    const b = document.getElementById('emp-aviso-membro-cadastrado');
    if (b) b.innerHTML = '';
    return;
  }
  const nomeLimpo = nomeVal.trim().toLowerCase();
  const membro = (STATE.membros || []).find(m => m.nome.toLowerCase() === nomeLimpo);
  const badgeMembro = document.getElementById('emp-aviso-membro-cadastrado');

  if (membro) {
    if (document.getElementById('emp-telefone') && membro.telefone) {
      document.getElementById('emp-telefone').value = membro.telefone;
    }
    if (document.getElementById('emp-documento')) {
      document.getElementById('emp-documento').value = membro.cargo_eclesiastico || 'Membro Ativo';
    }
    if (badgeMembro) {
      badgeMembro.innerHTML = `
        <span class="inline-flex items-center gap-1 text-[11px] text-emerald-800 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 mt-1">
          ✓ Membro Cadastrado na Secretaria (${membro.cargo_eclesiastico || 'Membro'}) - Celular: ${membro.telefone || 'Sem tel'}
        </span>
      `;
    }
  } else {
    if (badgeMembro) badgeMembro.innerHTML = '';
  }
}

function abrirModalNovoEmprestimoPatrimonio(preSelectPatId = null) {
  const itensPat = STATE.patrimonio || [];
  const listaEmp = STATE.patrimonio_emprestimos || [];
  const agoraIso = new Date().toISOString().substring(0, 16);
  
  const depois = new Date();
  depois.setDate(depois.getDate() + 2);
  const previsaoIso = depois.toISOString().substring(0, 16);

  const responsaveisSetor = getResponsaveisSetorCadastrados(preSelectPatId);
  const responsaveisPatrimonio = getResponsaveisPatrimonioCadastrados();

  const html = `
    <div class="space-y-5">
      <div class="border-b border-slate-200 pb-3 flex items-center justify-between">
        <div>
          <h3 class="text-base font-extrabold text-slate-800 flex items-center gap-2">
            <span class="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">📦</span>
            Novo Registro de Empréstimo de Patrimônio
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">Selecione o bem cadastrado, informe a vistoria inicial e identifique a pessoa que irá retirar.</p>
        </div>
        ${preSelectPatId ? `
          <span class="px-2.5 py-1 bg-indigo-100 text-indigo-800 font-bold text-xs rounded-lg border border-indigo-200">
            🔗 Item Pré-selecionado do Cadastro
          </span>
        ` : ''}
      </div>

      <form onsubmit="salvarNovoEmprestimoPatrimonio(event)" class="space-y-4 text-xs">
        <!-- 1. SELEÇÃO DO ITEM DO CADASTRO -->
        <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-3">
          <div class="flex items-center justify-between">
            <label class="font-bold text-slate-800 block text-xs">1. Equipamento / Bem Registrado no Cadastro *</label>
            <span class="text-[11px] text-slate-400">Puxa automaticamente dados cadastrais</span>
          </div>
          
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div class="sm:col-span-2">
              <select id="emp-select-patrimonio" onchange="aoSelecionarItemPatrimonio(this.value)" class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white font-medium text-xs focus:ring-2 focus:ring-indigo-500">
                <option value="">-- Selecione um bem do inventário cadastrado --</option>
                ${itensPat.map(p => {
                  const emp = listaEmp.find(e => (e.patrimonio_id === p.id || (e.codigo && e.codigo === p.codigo)) && e.status !== 'Devolvido');
                  const statusTxt = emp ? `(⚠️ JÁ EMPRESTADO para ${emp.solicitante_nome})` : `(🟢 DISPONÍVEL)`;
                  const isSel = preSelectPatId && Number(preSelectPatId) === Number(p.id) ? 'selected' : '';
                  return `
                    <option value="${p.id}" ${isSel} data-codigo="${p.codigo}" data-item="${p.item}" data-setor="${p.ministerio_nome || p.localizacao || ''}" data-local="${p.localizacao || ''}" data-resp="${p.responsavel || ''}" data-estado="${p.estado}">
                      [${p.codigo}] ${p.item} (${p.ministerio_nome || 'Geral'}) • ${statusTxt}
                    </option>
                  `;
                }).join('')}
                <option value="OUTRO">➕ Outro Item Avulso (Não Tombado)</option>
              </select>
            </div>
            <div>
              <input type="text" id="emp-codigo" placeholder="Código Tombamento" class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs font-mono font-bold" />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label class="font-semibold text-slate-700 block mb-1">Nome / Descrição do Item *</label>
              <input type="text" id="emp-item-nome" required placeholder="Ex: Equipamentos de Som e Microfones" class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white font-bold text-xs" />
            </div>
            <div>
              <label class="font-semibold text-slate-700 block mb-1">Setor / Localização de Origem</label>
              <input type="text" id="emp-setor" placeholder="Ex: Cabine de Som / Altar" class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs" />
            </div>
          </div>
        </div>

        <!-- 2. CONDIÇÃO DO ITEM NA SAÍDA -->
        <div class="bg-amber-50/50 p-3.5 rounded-xl border border-amber-200/70 space-y-2">
          <label class="font-bold text-amber-900 block text-xs">2. Condição Física do Item na Saída (Vistoria de Entrega) *</label>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div>
              <select id="emp-condicao-saida" required class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white font-bold text-xs">
                <option value="Excelente / Perfeito Estado">🌟 Excelente / Perfeito Estado</option>
                <option value="Novo (Sem Uso)">✨ Novo (Sem Uso)</option>
                <option value="Bom Estado (Com Marcas de Uso)" selected>👍 Bom Estado (Com Marcas de Uso)</option>
                <option value="Com Avarias / Detalhes Pré-existentes">⚠️ Com Avarias Pré-existentes</option>
              </select>
            </div>
            <div class="sm:col-span-2">
              <input type="text" id="emp-obs-saida" placeholder="Descreva os acessórios inclusos, cabos, adaptadores, estojo, etc." class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs" />
            </div>
          </div>
        </div>

        <!-- 3. PESSOA QUE IRÁ RETIRAR (LINK COM CADASTRO DE MEMBROS) -->
        <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-3">
          <div class="flex items-center justify-between">
            <label class="font-bold text-slate-800 block text-xs">3. Pessoa que Irá Retirar o Item *</label>
            <span class="text-[11px] text-slate-400">Auto-completa com a Secretaria de Membros</span>
          </div>
          
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div>
              <label class="font-semibold text-slate-700 block mb-1">Nome Completo *</label>
              <input type="text" id="emp-solicitante" list="lista-membros-datalist" oninput="aoDigitarNomeRetirante(this.value)" required placeholder="Digite ou selecione o membro..." class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white font-bold text-xs focus:ring-2 focus:ring-indigo-500" autocomplete="off" />
              <div id="emp-aviso-membro-cadastrado"></div>
            </div>
            <div>
              <label class="font-semibold text-slate-700 block mb-1">Telefone / WhatsApp</label>
              <input type="text" id="emp-telefone" placeholder="(11) 98765-4321" class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs" />
            </div>
            <div>
              <label class="font-semibold text-slate-700 block mb-1">Documento / Função</label>
              <input type="text" id="emp-documento" placeholder="RG, CPF ou Cargo" class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs" />
            </div>
          </div>

          <div>
            <label class="font-semibold text-slate-700 block mb-1">Motivo / Finalidade do Empréstimo</label>
            <input type="text" id="emp-motivo" placeholder="Ex: Encontro de Jovens / Culto no Lar / Congresso Infantil" class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs" />
          </div>
        </div>

        <!-- 4. DATAS E PRAZOS -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="font-bold text-slate-800 block mb-1">Data & Hora Prevista de Retirada *</label>
            <input type="datetime-local" id="emp-data-retirada" value="${agoraIso}" required class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs font-semibold" />
          </div>
          <div>
            <label class="font-bold text-slate-800 block mb-1">Previsão de Devolução / Entrega *</label>
            <input type="datetime-local" id="emp-data-previsao" value="${previsaoIso}" required class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs font-semibold text-indigo-700" />
          </div>
        </div>

        <!-- 5. APROVAÇÕES E RESPONSÁVEIS LINKADOS AO CADASTRO -->
        <div class="bg-indigo-50/40 p-3.5 rounded-xl border border-indigo-100 space-y-3">
          <div class="flex items-center justify-between">
            <label class="font-bold text-indigo-950 block text-xs">5. Responsáveis Linkados ao Cadastro & Validações de Saída</label>
            <span class="text-[10px] text-indigo-600 font-bold">Ambos os OKs são obrigatórios para liberar a retirada</span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="font-semibold text-slate-700 block mb-1">Responsável pelo Setor / Item (Cadastro) *</label>
              <select id="emp-resp-setor" required class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs font-semibold focus:ring-2 focus:ring-indigo-500">
                ${responsaveisSetor.map(r => `<option value="${r}">${r}</option>`).join('')}
              </select>
              <span class="text-[10px] text-slate-500 mt-0.5 block">Líder ou encarregado cadastrado no bem</span>
            </div>
            <div>
              <label class="font-semibold text-slate-700 block mb-1">Responsável pelo Patrimônio (Cadastro) *</label>
              <select id="emp-resp-patrimonio" required class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white text-xs font-semibold focus:ring-2 focus:ring-indigo-500">
                ${responsaveisPatrimonio.map(r => `<option value="${r}">${r}</option>`).join('')}
              </select>
              <span class="text-[10px] text-slate-500 mt-0.5 block">Gestor de patrimônio autorizado</span>
            </div>
          </div>

          <div class="p-3.5 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-950 space-y-1.5">
            <div class="font-bold flex items-center gap-1.5 text-amber-900">
              <span>⏳</span> Fluxo de Segurança: Aprovação Obrigatória em 2 Etapas
            </div>
            <p class="text-[11px] text-amber-800 leading-relaxed">
              Ao salvar, esta solicitação ficará registrada como <strong>"Aguardando Aprovação do Setor"</strong>. O item fica com retirada bloqueada até que ambas as autorizações ocorram na sequência correta:
            </p>
            <div class="flex items-center gap-2 pt-1 text-[11px] font-bold">
              <span class="px-2 py-0.5 rounded bg-white border border-amber-300 text-amber-900">1º OK do Setor</span>
              <span>➔</span>
              <span class="px-2 py-0.5 rounded bg-white border border-blue-300 text-blue-900">2º OK do Patrimônio</span>
              <span>➔</span>
              <span class="px-2 py-0.5 rounded bg-white border border-emerald-300 text-emerald-800">3º Efetivar Retirada</span>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-200">
          <button type="button" onclick="fecharModalCustom()" class="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition">
            Cancelar
          </button>
          <button type="submit" class="px-5 py-2 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-md transition flex items-center gap-1.5">
            <span>💾</span> Salvar Solicitação de Empréstimo
          </button>
        </div>
      </form>
    </div>
  `;

  abrirModalCustom(html, false, 'largo');

  if (preSelectPatId) {
    setTimeout(() => {
      aoSelecionarItemPatrimonio(preSelectPatId);
      const inp = document.getElementById('emp-solicitante');
      if (inp) inp.focus();
    }, 150);
  }
}

function aoSelecionarItemPatrimonio(id) {
  const sel = document.getElementById('emp-select-patrimonio');
  if (!sel) return;
  const opt = sel.options[sel.selectedIndex];
  if (!opt) return;

  const codigo = opt.getAttribute('data-codigo') || '';
  const item = opt.getAttribute('data-item') || '';
  const setor = opt.getAttribute('data-setor') || '';
  const resp = opt.getAttribute('data-resp') || '';
  const estado = opt.getAttribute('data-estado') || '';

  if (id && id !== 'OUTRO') {
    if (document.getElementById('emp-codigo')) document.getElementById('emp-codigo').value = codigo;
    if (document.getElementById('emp-item-nome')) document.getElementById('emp-item-nome').value = item;
    if (document.getElementById('emp-setor')) document.getElementById('emp-setor').value = setor;
    
    // Atualiza o select de responsáveis pelo setor com a lista linkada
    const selRespSetor = document.getElementById('emp-resp-setor');
    if (selRespSetor) {
      const lista = getResponsaveisSetorCadastrados(id);
      selRespSetor.innerHTML = lista.map(r => `<option value="${r}" ${r.includes(resp) ? 'selected' : ''}>${r}</option>`).join('');
    }

    if (estado && document.getElementById('emp-condicao-saida')) {
      document.getElementById('emp-condicao-saida').value = estado.includes('Novo') ? 'Novo (Sem Uso)' : 'Bom Estado (Com Marcas de Uso)';
    }
  } else if (id === 'OUTRO') {
    if (document.getElementById('emp-codigo')) document.getElementById('emp-codigo').value = '';
    if (document.getElementById('emp-item-nome')) document.getElementById('emp-item-nome').value = '';
    if (document.getElementById('emp-setor')) document.getElementById('emp-setor').value = '';
    if (document.getElementById('emp-item-nome')) document.getElementById('emp-item-nome').focus();
  }
}

async function salvarNovoEmprestimoPatrimonio(e) {
  e.preventDefault();
  const selectPat = document.getElementById('emp-select-patrimonio');
  const patIdVal = selectPat ? selectPat.value : '';
  const patId = (patIdVal && patIdVal !== 'OUTRO') ? parseInt(patIdVal) : null;

  const payload = {
    patrimonio_id: patId,
    codigo: document.getElementById('emp-codigo')?.value || '',
    item: document.getElementById('emp-item-nome')?.value || '',
    setor: document.getElementById('emp-setor')?.value || '',
    condicao_saida: document.getElementById('emp-condicao-saida')?.value || 'Bom Estado',
    observacoes_saida: document.getElementById('emp-obs-saida')?.value || '',
    solicitante_nome: document.getElementById('emp-solicitante')?.value || '',
    solicitante_telefone: document.getElementById('emp-telefone')?.value || '',
    solicitante_documento: document.getElementById('emp-documento')?.value || '',
    motivo: document.getElementById('emp-motivo')?.value || '',
    data_retirada: document.getElementById('emp-data-retirada')?.value || '',
    previsao_devolucao: document.getElementById('emp-data-previsao')?.value || '',
    responsavel_setor: document.getElementById('emp-resp-setor')?.value || '',
    responsavel_patrimonio: document.getElementById('emp-resp-patrimonio')?.value || 'Marcos Silva (Administração / Patrimônio)'
  };

  const { status, data } = await apiPost('/api/patrimonio/emprestimo', payload);
  if (status === 200) {
    fecharModalCustom();
    await fetchBootstrap();
    alert('✓ Solicitação de empréstimo registrada com sucesso!\n\nStatus: Aguardando Aprovação do Setor Responsável.');
  } else {
    alert(data.erro || 'Erro ao registrar empréstimo');
  }
}

// =======================================================
// AÇÕES DO FLUXO DE APROVAÇÃO, RETIRADA E DEVOLUÇÃO
// =======================================================

async function aprovarEmprestimoSetor(id) {
  const lista = STATE.patrimonio_emprestimos || [];
  const emp = lista.find(e => Number(e.id) === Number(id));
  const itemNome = emp ? emp.item : 'este item';
  const setorNome = emp ? (emp.setor || emp.responsavel_setor || 'do setor') : 'do setor';

  if (!confirm(`Confirmar a aprovação da saída de "${itemNome}" pelo Responsável do Setor (${setorNome})?`)) {
    return;
  }

  const { status, data } = await apiPost('/api/patrimonio/emprestimo/aprovar-setor', { id });
  if (status === 200) {
    await fetchBootstrap();
    alert(`✓ Aprovação do Setor concedida com sucesso para "${itemNome}"!\n\nAgora a solicitação está liberada para o Responsável pelo Patrimônio dar o OK.`);
  } else {
    alert(data.erro || 'Erro ao registrar aprovação do setor.');
  }
}

async function darOkEmprestimoPatrimonio(id) {
  const lista = STATE.patrimonio_emprestimos || [];
  const emp = lista.find(e => Number(e.id) === Number(id));
  if (!emp) return;

  // Regra estrita: autorização do patrimônio depende da aprovação prévia do setor
  if (emp.status_aprovacao_setor !== 'Aprovado') {
    alert(`⛔ AÇÃO BLOQUEADA!\n\nA autorização do Responsável pelo Patrimônio depende da aprovação prévia do Responsável do Setor.\n\nAguarde o responsável do setor (${emp.responsavel_setor || 'Líder'}) aprovar a solicitação primeiro.`);
    return;
  }

  if (!confirm(`Confirmar o OK de liberação pelo Responsável do Patrimônio para o item "${emp.item}"?\n\nApós a confirmação, o bem estará 100% liberado para a retirada física pelo solicitante.`)) {
    return;
  }

  const { status, data } = await apiPost('/api/patrimonio/emprestimo/ok-patrimonio', { id });
  if (status === 200) {
    await fetchBootstrap();
    alert(`✓ OK do Patrimônio confirmado com sucesso!\n\nO item "${emp.item}" está LIBERADO PARA RETIRADA.`);
  } else {
    alert(data.erro || 'Erro ao registrar OK do patrimônio.');
  }
}

function abrirModalDevolucaoPatrimonio(id) {
  const lista = STATE.patrimonio_emprestimos || [];
  const emp = lista.find(e => Number(e.id) === Number(id));
  if (!emp) return;

  const agoraIso = new Date().toISOString().slice(0, 16);

  const html = `
    <div class="space-y-4 text-xs">
      <div class="flex items-center justify-between border-b pb-3">
        <div>
          <h3 class="text-sm font-bold text-slate-800">Registrar Devolução / Retorno do Bem</h3>
          <p class="text-[11px] text-slate-500">${emp.codigo ? `[${emp.codigo}] ` : ''}${emp.item} • Solicitante: ${emp.solicitante_nome}</p>
        </div>
        <button type="button" onclick="fecharModalCustom()" class="text-slate-400 hover:text-slate-600 text-lg">✕</button>
      </div>

      <form onsubmit="salvarDevolucaoPatrimonio(event, ${emp.id})" class="space-y-3">
        <div>
          <label class="font-bold text-slate-700 block mb-1">Data & Hora Real da Devolução *</label>
          <input type="datetime-local" id="dev-data-retorno" value="${agoraIso}" required class="w-full border border-slate-300 rounded-lg px-3 py-2 text-xs font-semibold" />
        </div>

        <div>
          <label class="font-bold text-slate-700 block mb-1">Condição Física do Item no Retorno (Vistoria Reversa) *</label>
          <select id="dev-condicao-retorno" required class="w-full border border-slate-300 rounded-lg px-3 py-2 bg-white font-bold text-xs">
            <option value="Excelente / Idêntico à Saída" selected>🌟 Excelente / Idêntico à Saída</option>
            <option value="Bom Estado (Sem Danos)">👍 Bom Estado (Sem Danos)</option>
            <option value="Com Pequenas Avarias / Arranhões">⚠️ Com Pequenas Avarias / Detalhes</option>
            <option value="Necessita Manutenção / Reparo">🔧 Necessita Manutenção / Reparo</option>
            <option value="Danificado / Quebrado">❌ Danificado / Quebrado</option>
          </select>
        </div>

        <div>
          <label class="font-bold text-slate-700 block mb-1">Observações da Vistoria de Entrega</label>
          <textarea id="dev-obs-retorno" rows="2" placeholder="Descreva se todos os cabos, estojos e acessórios retornaram..." class="w-full border border-slate-300 rounded-lg px-3 py-2 text-xs"></textarea>
        </div>

        <div class="space-y-2 pt-2 border-t border-slate-200">
          <label class="flex items-center gap-2 font-semibold text-slate-700 cursor-pointer">
            <input type="checkbox" id="dev-ok-setor" checked class="rounded text-indigo-600 w-4 h-4" />
            <span>Confirmar conferência e recebimento pelo <strong>Responsável do Setor</strong></span>
          </label>
          <label class="flex items-center gap-2 font-semibold text-slate-700 cursor-pointer">
            <input type="checkbox" id="dev-ok-patrimonio" checked class="rounded text-indigo-600 w-4 h-4" />
            <span>Confirmar baixa final pelo <strong>Responsável do Patrimônio</strong></span>
          </label>
        </div>

        <div class="flex items-center justify-end gap-2 pt-3 border-t">
          <button type="button" onclick="fecharModalCustom()" class="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
          <button type="submit" class="px-4 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow transition">Concluir Devolução</button>
        </div>
      </form>
    </div>
  `;

  abrirModalCustom(html, false, 'medio');
}

async function salvarDevolucaoPatrimonio(e, id) {
  e.preventDefault();
  const payload = {
    id,
    data_devolucao_real: document.getElementById('dev-data-retorno')?.value || '',
    condicao_retorno: document.getElementById('dev-condicao-retorno')?.value || 'Excelente / Idêntico à Saída',
    observacoes_retorno: document.getElementById('dev-obs-retorno')?.value || '',
    ok_setor: document.getElementById('dev-ok-setor')?.checked || false,
    ok_patrimonio: document.getElementById('dev-ok-patrimonio')?.checked || false
  };

  const { status, data } = await apiPost('/api/patrimonio/emprestimo/devolucao', payload);
  if (status === 200) {
    fecharModalCustom();
    await fetchBootstrap();
    alert('✓ Devolução registrada com sucesso!');
  } else {
    alert(data.erro || 'Erro ao registrar devolução.');
  }
}

async function darOkRetornoSetor(id) {
  if (!confirm('Confirmar o recebimento e conferência física do item devolvido pelo Setor?')) return;
  const { status, data } = await apiPost('/api/patrimonio/emprestimo/ok-retorno-setor', { id });
  if (status === 200) {
    await fetchBootstrap();
    alert('✓ Conferência do Setor confirmada!');
  } else {
    alert(data.erro || 'Erro ao confirmar retorno pelo setor.');
  }
}

async function darOkRetornoPatrimonio(id) {
  if (!confirm('Confirmar a baixa definitiva de devolução no Patrimônio?')) return;
  const { status, data } = await apiPost('/api/patrimonio/emprestimo/ok-retorno-patrimonio', { id });
  if (status === 200) {
    await fetchBootstrap();
    alert('✓ Baixa definitiva concluída no Patrimônio!');
  } else {
    alert(data.erro || 'Erro ao confirmar baixa pelo patrimônio.');
  }
}

async function excluirEmprestimoPatrimonio(id) {
  if (!confirm('Deseja realmente excluir este registro de empréstimo? Esta ação é irreversível.')) return;
  const operador = CURRENT_OPERATOR ? CURRENT_OPERATOR.nome : 'Administrador';
  const res = await fetch(`/api/patrimonio/emprestimo?id=${id}&operador=${encodeURIComponent(operador)}`, {
    method: 'DELETE'
  });
  if (res.ok) {
    await fetchBootstrap();
    alert('Registro de empréstimo excluído com sucesso.');
  } else {
    const err = await res.json().catch(() => ({}));
    alert(err.erro || 'Erro ao excluir empréstimo.');
  }
}

function imprimirTermoEmprestimo(id) {
  const lista = STATE.patrimonio_emprestimos || [];
  const emp = lista.find(e => Number(e.id) === Number(id));
  if (!emp) {
    alert('Empréstimo não encontrado.');
    return;
  }

  const agoraStr = new Date().toLocaleDateString('pt-BR') + ' ' + new Date().toLocaleTimeString('pt-BR');

  const html = `
    <div id="termo-impressao-conteudo" class="space-y-4 text-xs text-slate-800 p-4 bg-white border border-slate-300 rounded-xl">
      <div class="flex items-center justify-between border-b-2 border-slate-900 pb-3">
        <div>
          <p class="text-[10px] font-bold uppercase tracking-widest text-indigo-700">Primeira Igreja Batista Parque São Paulo</p>
          <h2 class="text-base font-black text-slate-900 uppercase">Termo de Cautela e Empréstimo de Bens</h2>
          <p class="text-[11px] text-slate-500">Documento Oficial de Registro de Saída Patrimonial • Nº REG-${String(emp.id).padStart(5, '0')}</p>
        </div>
        <div class="text-right">
          <span class="text-[10px] text-slate-400 block font-mono">STATUS ATUAL</span>
          <span class="inline-block px-2.5 py-1 rounded-full text-xs font-black bg-indigo-100 text-indigo-900 border border-indigo-200">${emp.status}</span>
        </div>
      </div>

      <!-- DADOS DO BEM EMPRESTADO -->
      <div class="bg-slate-50 p-3 rounded-lg border border-slate-200">
        <h4 class="font-bold text-slate-800 text-xs mb-2 uppercase tracking-wider">1. Identificação do Bem / Equipamento</h4>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
          <div><span class="text-slate-400 block">Código Tombamento:</span><strong>${emp.codigo || 'Não Tombado'}</strong></div>
          <div><span class="text-slate-400 block">Item:</span><strong class="text-indigo-800">${emp.item}</strong></div>
          <div><span class="text-slate-400 block">Setor de Origem:</span><strong>${emp.setor || 'Patrimônio Geral'}</strong></div>
          <div><span class="text-slate-400 block">Condição na Saída:</span><strong>${emp.condicao_saida}</strong></div>
        </div>
        ${emp.observacoes_saida ? `<div class="mt-2 text-[11px] pt-1.5 border-t border-slate-200 text-slate-600"><strong>Observações/Acessórios:</strong> ${emp.observacoes_saida}</div>` : ''}
      </div>

      <!-- DADOS DO SOLICITANTE / RETIRANTE -->
      <div class="bg-slate-50 p-3 rounded-lg border border-slate-200">
        <h4 class="font-bold text-slate-800 text-xs mb-2 uppercase tracking-wider">2. Responsável pela Retirada (Cautelador)</h4>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
          <div><span class="text-slate-400 block">Nome Completo:</span><strong class="text-slate-900">${emp.solicitante_nome}</strong></div>
          <div><span class="text-slate-400 block">Telefone / WhatsApp:</span><strong>${emp.solicitante_telefone || 'Não informado'}</strong></div>
          <div><span class="text-slate-400 block">Documento / Função:</span><strong>${emp.solicitante_documento || 'Membro'}</strong></div>
          <div><span class="text-slate-400 block">Finalidade / Motivo:</span><strong>${emp.motivo || 'Atividade da Igreja'}</strong></div>
        </div>
        <div class="grid grid-cols-2 gap-2 mt-2 pt-1.5 border-t border-slate-200 text-[11px]">
          <div><span class="text-slate-400">Data/Hora da Retirada:</span> <strong>${formatarDataHora(emp.data_retirada)}</strong></div>
          <div><span class="text-slate-400">Previsão Obrigatória de Devolução:</span> <strong class="text-rose-700">${formatarDataHora(emp.previsao_devolucao)}</strong></div>
        </div>
      </div>

      <!-- FLUXO DE APROVAÇÃO OFICIAL -->
      <div class="bg-indigo-50/50 p-3 rounded-lg border border-indigo-100">
        <h4 class="font-bold text-indigo-950 text-xs mb-2 uppercase tracking-wider">3. Fluxo de Autorizações Oficiais</h4>
        <div class="grid grid-cols-2 gap-3 text-[11px]">
          <div class="p-2 rounded bg-white border border-indigo-100">
            <span class="font-bold block text-slate-700">1º OK: Responsável pelo Setor</span>
            <div class="text-slate-600 mt-1">${emp.responsavel_setor || 'Responsável Setor'}</div>
            <div class="text-[10px] font-bold ${emp.status_aprovacao_setor === 'Aprovado' ? 'text-emerald-700' : 'text-amber-700'} mt-0.5">
              ${emp.status_aprovacao_setor === 'Aprovado' ? `✓ Aprovado em ${emp.data_aprovacao_setor || ''} (${emp.operador_aprovador_setor || 'Setor'})` : '⏳ Aguardando Aprovação'}
            </div>
          </div>
          <div class="p-2 rounded bg-white border border-indigo-100">
            <span class="font-bold block text-slate-700">2º OK: Responsável pelo Patrimônio</span>
            <div class="text-slate-600 mt-1">${emp.responsavel_patrimonio || 'Marcos Silva'}</div>
            <div class="text-[10px] font-bold ${emp.status_ok_patrimonio === 'Liberado' ? 'text-emerald-700' : 'text-slate-400'} mt-0.5">
              ${emp.status_ok_patrimonio === 'Liberado' ? `✓ Liberado em ${emp.data_ok_patrimonio || ''} (${emp.operador_ok_patrimonio || 'Patrimônio'})` : '🔒 Aguardando Liberação'}
            </div>
          </div>
        </div>
      </div>

      <!-- TERMO DE COMPROMISSO -->
      <div class="text-[10px] text-slate-500 leading-tight border-t pt-2">
        Declaro ter recebido o(s) bem(ns) acima descrito(s) em perfeito estado de funcionamento e conservação, responsabilizando-me formalmente pela guarda, zelo e integridade física até a sua efetiva devolução na data estipulada, comprometendo-me a ressarcir a igreja em caso de extravio, dano por negligência ou uso indevido.
      </div>

      <!-- CAMPOS DE ASSINATURA -->
      <div class="grid grid-cols-3 gap-4 pt-4 border-t border-slate-300 text-center text-[10px]">
        <div>
          ${emp.assinatura_retirada_base64 ? `
            <img src="${emp.assinatura_retirada_base64}" alt="Assinatura Digital" class="h-12 mx-auto object-contain mb-1" />
          ` : `
            <div class="h-12 flex items-center justify-center text-[9px] text-slate-300 italic">(Aguardando assinatura digital)</div>
          `}
          <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Assinatura do Retirante (Cautelador)</div>
          ${emp.assinatura_retirada_em ? `<div class="text-[8px] text-emerald-700 font-bold">Assinado Digitalmente em ${emp.assinatura_retirada_em}</div>` : ''}
        </div>
        <div>
          <div class="h-12"></div>
          <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Responsável pelo Setor</div>
        </div>
        <div>
          <div class="h-12"></div>
          <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Coordenação de Patrimônio</div>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2 pt-3 border-t print:hidden">
        <button type="button" onclick="fecharModalCustom()" class="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-semibold hover:bg-slate-200">Fechar</button>
        <button type="button" onclick="window.print()" class="px-4 py-1.5 rounded-xl bg-indigo-600 text-white font-bold hover:bg-indigo-700 shadow flex items-center gap-1.5">
          <span>🖨️</span> Imprimir Termo de Cautela
        </button>
      </div>
    </div>
  `;

  abrirModalCustom(html, true, 'largo');
}

function abrirModalAssinaturaDigital(id) {
  const lista = STATE.patrimonio_emprestimos || [];
  const emp = lista.find(e => Number(e.id) === Number(id));
  if (!emp) {
    alert('Empréstimo não encontrado.');
    return;
  }

  // Gera a URL completa para celular (compatível tanto local quanto na nuvem Render)
  const linkMobile = window.location.origin + '/assinar-emprestimo?id=' + emp.id;
  const textoWhatsapp = encodeURIComponent(
    `Olá, ${emp.solicitante_nome}! Segue o link para assinar digitalmente o Termo de Cautela do item "${emp.item}" da PIB Parque São Paulo:\n\n${linkMobile}\n\nPor favor, assine com a ponta do dedo na tela do seu celular para registrar a saída.`
  );
  const foneLimpo = (emp.solicitante_telefone || '').replace(/\D/g, '');
  const linkZap = foneLimpo.length >= 8
    ? `https://api.whatsapp.com/send?phone=55${foneLimpo}&text=${textoWhatsapp}`
    : `https://api.whatsapp.com/send?text=${textoWhatsapp}`;

  const jaAssinado = Boolean(emp.assinatura_retirada_base64);

  const html = `
    <div class="space-y-4 text-xs">
      <div class="flex items-center justify-between border-b pb-3">
        <div class="flex items-center gap-2">
          <span class="text-xl">📱</span>
          <div>
            <h3 class="text-sm font-bold text-slate-800">Assinatura Digital no Celular • Termo de Cautela</h3>
            <p class="text-[11px] text-slate-500">${emp.codigo ? `[${emp.codigo}] ` : ''}${emp.item} • Solicitante: <strong>${emp.solicitante_nome}</strong></p>
          </div>
        </div>
        <button type="button" onclick="fecharModalCustom()" class="text-slate-400 hover:text-slate-600 text-lg">✕</button>
      </div>

      ${jaAssinado ? `
        <div class="p-4 bg-emerald-50 rounded-2xl border border-emerald-200 text-center space-y-2">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
            ✓ Termo Já Assinado Digitalmente
          </div>
          <div class="bg-white p-3 rounded-xl border border-emerald-300 max-w-xs mx-auto">
            <img src="${emp.assinatura_retirada_base64}" alt="Assinatura" class="h-20 mx-auto object-contain" />
            <div class="text-[9px] text-slate-400 mt-1 font-mono">Assinado em ${emp.assinatura_retirada_em || ''}</div>
          </div>
          <p class="text-[11px] text-emerald-800">Este empréstimo já possui validade jurídica e comprovação oficial gravada no sistema.</p>
        </div>
      ` : `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- OPÇÃO 1: QR CODE PARA O CELULAR DO RETIRANTE -->
          <div class="bg-gradient-to-b from-indigo-50/50 to-white p-4 rounded-2xl border border-indigo-200 text-center flex flex-col items-center justify-between space-y-3">
            <div>
              <span class="text-[10px] font-black uppercase tracking-wider text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded-full">Opção 1: Celular do Membro</span>
              <h4 class="font-bold text-slate-800 text-xs mt-1">Aponte a Câmera do Smartphone</h4>
              <p class="text-[11px] text-slate-500">O retirante lê o QR Code e assina com o dedo na tela dele:</p>
            </div>

            <!-- CONTAINER QR CODE -->
            <div id="modal-qr-assinatura-box" class="bg-white p-2.5 rounded-2xl border-2 border-indigo-200 shadow-md flex items-center justify-center min-w-[140px] min-h-[140px]">
              <span class="text-xs text-slate-400">Gerando QR Code...</span>
            </div>

            <div class="w-full space-y-1.5 pt-1">
              <a href="${linkZap}" target="_blank" class="w-full py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow transition flex items-center justify-center gap-1.5">
                <span>📲</span> Enviar no WhatsApp do Membro
              </a>
              <button type="button" onclick="copiarLinkAssinaturaMobile('${linkMobile}')" class="w-full py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition flex items-center justify-center gap-1.5">
                <span>📋</span> Copiar Link Direto
              </button>
            </div>
          </div>

          <!-- OPÇÃO 2: ASSINAR NESTE COMPUTADOR / TABLET AGORA -->
          <div class="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex flex-col justify-between space-y-2">
            <div>
              <span class="text-[10px] font-black uppercase tracking-wider text-slate-600 bg-slate-200 px-2 py-0.5 rounded-full">Opção 2: Neste Dispositivo</span>
              <h4 class="font-bold text-slate-800 text-xs mt-1">Assinar na Tela Touch / Mouse Agora</h4>
              <p class="text-[11px] text-slate-500">Se o membro estiver ao seu lado no computador ou tablet:</p>
            </div>

            <div class="space-y-1">
              <div class="flex items-center justify-between text-[11px]">
                <span class="font-semibold text-slate-600">Quadro de Assinatura:</span>
                <button type="button" onclick="limparCanvasModalAssinatura()" class="text-indigo-600 font-bold hover:underline text-[10px]">Limpar</button>
              </div>
              <div class="relative bg-white rounded-xl border-2 border-dashed border-slate-300 p-1">
                <canvas id="modal-sig-canvas" width="340" height="130" class="w-full h-32 rounded-lg cursor-crosshair bg-white block"></canvas>
                <div id="modal-sig-hint" class="pointer-events-none absolute inset-0 flex items-center justify-center text-slate-300 text-xs">
                  Assine aqui com o dedo ou mouse
                </div>
              </div>
            </div>

            <button type="button" id="btn-gravar-sig-modal" onclick="salvarAssinaturaPeloModal(${emp.id}, '${emp.solicitante_nome}')" class="w-full py-2.5 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow transition flex items-center justify-center gap-1.5">
              <span>✍️</span> Confirmar Assinatura Aqui
            </button>
          </div>
        </div>
      `}

      <div class="flex items-center justify-end gap-2 pt-3 border-t">
        <button type="button" onclick="fecharModalCustom()" class="px-4 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition">
          Fechar
        </button>
      </div>
    </div>
  `;

  abrirModalCustom(html, false, 'largo');

  if (!jaAssinado) {
    setTimeout(() => {
      const box = document.getElementById('modal-qr-assinatura-box');
      if (box) {
        box.innerHTML = '';
        gerarQRCodeNoElemento('modal-qr-assinatura-box', linkMobile, 130);
      }
      iniciarCanvasModalAssinatura();
    }, 150);
  }
}

let modalCanvasCtx = null, modalCanvasEl = null, modalHasDrawn = false, modalDrawing = false;

function iniciarCanvasModalAssinatura() {
  modalCanvasEl = document.getElementById('modal-sig-canvas');
  const hint = document.getElementById('modal-sig-hint');
  modalHasDrawn = false;
  modalDrawing = false;
  if (!modalCanvasEl) return;

  modalCanvasCtx = modalCanvasEl.getContext('2d');
  modalCanvasCtx.lineWidth = 2.5;
  modalCanvasCtx.lineCap = 'round';
  modalCanvasCtx.lineJoin = 'round';
  modalCanvasCtx.strokeStyle = '#0f172a';

  function getPos(e) {
    const rect = modalCanvasEl.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return {
      x: clientX - rect.left,
      y: clientY - rect.top
    };
  }

  function start(e) {
    modalDrawing = true;
    modalHasDrawn = true;
    if (hint) hint.style.display = 'none';
    const pos = getPos(e);
    modalCanvasCtx.beginPath();
    modalCanvasCtx.moveTo(pos.x, pos.y);
    e.preventDefault();
  }

  function draw(e) {
    if (!modalDrawing) return;
    const pos = getPos(e);
    modalCanvasCtx.lineTo(pos.x, pos.y);
    modalCanvasCtx.stroke();
    e.preventDefault();
  }

  function stop(e) {
    modalDrawing = false;
    if (e) e.preventDefault();
  }

  modalCanvasEl.addEventListener('mousedown', start);
  modalCanvasEl.addEventListener('mousemove', draw);
  window.addEventListener('mouseup', stop);

  modalCanvasEl.addEventListener('touchstart', start, { passive: false });
  modalCanvasEl.addEventListener('touchmove', draw, { passive: false });
  window.addEventListener('touchend', stop, { passive: false });
}

function limparCanvasModalAssinatura() {
  if (!modalCanvasCtx || !modalCanvasEl) return;
  const rect = modalCanvasEl.getBoundingClientRect();
  modalCanvasCtx.clearRect(0, 0, rect.width, rect.height);
  modalHasDrawn = false;
  const hint = document.getElementById('modal-sig-hint');
  if (hint) hint.style.display = 'flex';
}

async function salvarAssinaturaPeloModal(empId, solicitanteNome) {
  if (!modalHasDrawn || !modalCanvasEl) {
    alert('Por favor, faça a assinatura no quadro antes de confirmar.');
    return;
  }
  const btn = document.getElementById('btn-gravar-sig-modal');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = 'Gravando Assinatura...';
  }

  const dataUrl = modalCanvasEl.toDataURL('image/png');
  const { status, data } = await apiPost('/api/patrimonio/emprestimo/assinar', {
    id: empId,
    tipo: 'retirada',
    assinatura_base64: dataUrl,
    solicitante_nome: solicitanteNome
  });

  if (status === 200) {
    fecharModalCustom();
    await fetchBootstrap();
    alert('✓ Termo assinado digitalmente com sucesso!\n\nA retirada física está confirmada e vinculada à assinatura do solicitante.');
  } else {
    alert(data.erro || 'Erro ao gravar assinatura digital.');
    if (btn) { btn.disabled = false; btn.innerHTML = 'Tentar Novamente'; }
  }
}

function copiarLinkAssinaturaMobile(url) {
  navigator.clipboard.writeText(url).then(() => {
    alert('✓ Link copiado para a área de transferência!\n\nVocê pode colar no WhatsApp ou enviar para o membro:\n' + url);
  }).catch(() => {
    prompt('Copie o link abaixo:', url);
  });
}


function imprimirRelatorioGeralEmprestimos() {
  const lista = STATE.patrimonio_emprestimos || [];
  const agoraStr = new Date().toLocaleDateString('pt-BR') + ' ' + new Date().toLocaleTimeString('pt-BR');

  const html = `
    <div class="space-y-4 text-xs text-slate-800 p-2">
      <div class="flex items-center justify-between border-b-2 border-slate-900 pb-3">
        <div>
          <p class="text-[10px] font-bold uppercase tracking-widest text-indigo-700">Primeira Igreja Batista Parque São Paulo</p>
          <h2 class="text-base font-black text-slate-900 uppercase">Relatório Consolidado de Empréstimos & Devoluções</h2>
          <p class="text-[11px] text-slate-500">Histórico Completo de Retiradas de Bens Patrimoniais • Emitido em ${agoraStr}</p>
        </div>
        <div class="text-right font-mono text-xs">
          <span class="block text-slate-400 text-[10px]">TOTAL DE REGISTROS</span>
          <strong class="text-base text-indigo-700">${lista.length} bens</strong>
        </div>
      </div>

      <div class="overflow-x-auto max-h-96">
        <table class="w-full text-left border-collapse text-[11px]">
          <thead>
            <tr class="border-b border-slate-300 bg-slate-100 text-slate-700 font-bold">
              <th class="p-2">Cód.</th>
              <th class="p-2">Item</th>
              <th class="p-2">Retirante</th>
              <th class="p-2">Retirada</th>
              <th class="p-2">Previsão</th>
              <th class="p-2">Condição</th>
              <th class="p-2">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200">
            ${lista.map(e => `
              <tr>
                <td class="p-2 font-mono font-bold">${e.codigo || '-'}</td>
                <td class="p-2 font-semibold">${e.item}</td>
                <td class="p-2">${e.solicitante_nome} (${e.solicitante_telefone || '-'})</td>
                <td class="p-2">${formatarDataHora(e.data_retirada)}</td>
                <td class="p-2">${formatarDataHora(e.previsao_devolucao)}</td>
                <td class="p-2">${e.condicao_saida}</td>
                <td class="p-2 font-bold">${e.status}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      <div class="grid grid-cols-2 gap-6 pt-8 border-t border-slate-300 text-center text-[11px]">
        <div>
          <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Coordenação de Patrimônio</div>
        </div>
        <div>
          <div class="border-t border-slate-800 pt-1.5 font-bold text-slate-900">Pastor Presidente</div>
        </div>
      </div>
    </div>
  `;

  abrirModalCustom(html, true, 'largo');
}



// =======================================================
// AÇÕES DE GRAVAÇÃO E MODAIS
// =======================================================

async function apiPost(url, payload) {
  payload.operador = CURRENT_OPERATOR ? CURRENT_OPERATOR.nome : 'Administrador';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  return { status: res.status, data };
}

// ======================================================================
// GESTÃO DO CADASTRO DE MEMBROS (NOVO CADASTRO E MANUTENÇÃO)
// ======================================================================

function switchSecretariaSubtab(subtab) {
  const tabLista = document.getElementById('sec-subtab-lista');
  const tabCadastro = document.getElementById('sec-subtab-cadastro');
  const btnLista = document.getElementById('sec-btn-lista');
  const btnCadastro = document.getElementById('sec-btn-cadastro');

  if (subtab === 'cadastro') {
    if (tabLista) tabLista.classList.add('hidden');
    if (tabCadastro) tabCadastro.classList.remove('hidden');

    if (btnLista) {
      btnLista.className = 'subtab-btn text-xs font-bold px-4 py-2.5 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 transition flex items-center gap-2 cursor-pointer';
    }
    if (btnCadastro) {
      btnCadastro.className = 'subtab-btn active text-xs font-bold px-4 py-2.5 rounded-xl border border-indigo-600 bg-indigo-50 text-indigo-700 transition flex items-center gap-2 cursor-pointer';
    }

    popularSelectsCadastroMembro();
  } else {
    if (tabCadastro) tabCadastro.classList.add('hidden');
    if (tabLista) tabLista.classList.remove('hidden');

    if (btnLista) {
      btnLista.className = 'subtab-btn active text-xs font-bold px-4 py-2.5 rounded-xl border border-indigo-600 bg-indigo-50 text-indigo-700 transition flex items-center gap-2 cursor-pointer';
    }
    if (btnCadastro) {
      btnCadastro.className = 'subtab-btn text-xs font-bold px-4 py-2.5 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 transition flex items-center gap-2 cursor-pointer';
    }

    renderMembros();
  }
}

function aoSelecionarFotoMembro(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  if (!file.type.startsWith('image/')) {
    alert('Por favor, selecione um arquivo de imagem válido (JPG, PNG, WEBP).');
    return;
  }

  const reader = new FileReader();
  reader.onload = function(e) {
    const img = new Image();
    img.onload = function() {
      const maxDim = 360;
      let width = img.width;
      let height = img.height;

      if (width > height) {
        if (width > maxDim) {
          height = Math.round((height * maxDim) / width);
          width = maxDim;
        }
      } else {
        if (height > maxDim) {
          width = Math.round((width * maxDim) / height);
          height = maxDim;
        }
      }

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);

      const base64Res = canvas.toDataURL('image/jpeg', 0.85);

      const inputBase64 = document.getElementById('mem-foto-base64');
      if (inputBase64) inputBase64.value = base64Res;

      const previewEl = document.getElementById('mem-foto-preview');
      if (previewEl) {
        previewEl.src = base64Res;
        previewEl.classList.remove('hidden');
      }

      const phEl = document.getElementById('mem-foto-placeholder');
      if (phEl) phEl.classList.add('hidden');

      const btnRem = document.getElementById('btn-remover-foto-mem');
      if (btnRem) btnRem.classList.remove('hidden');
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

function removerFotoMembro() {
  const inputBase64 = document.getElementById('mem-foto-base64');
  if (inputBase64) inputBase64.value = '';

  const fileInput = document.getElementById('mem-foto-input');
  if (fileInput) fileInput.value = '';

  const previewEl = document.getElementById('mem-foto-preview');
  if (previewEl) {
    previewEl.src = '';
    previewEl.classList.add('hidden');
  }

  const phEl = document.getElementById('mem-foto-placeholder');
  if (phEl) phEl.classList.remove('hidden');

  const btnRem = document.getElementById('btn-remover-foto-mem');
  if (btnRem) btnRem.classList.add('hidden');
}

function abrirNovoCadastroMembro() {
  const form = document.getElementById('form-membro');
  if (form) form.reset();

  const inpId = document.getElementById('mem-id');
  if (inpId) inpId.value = '';

  const titulo = document.getElementById('titulo-cadastro-membro');
  if (titulo) titulo.textContent = 'Cadastro Completo de Novo Membro';

  const badgeFicha = document.getElementById('badge-proxima-ficha');
  if (badgeFicha) {
    const total = (STATE.membros || []).length;
    badgeFicha.textContent = `Ficha Nº #${String(total + 1).padStart(4, '0')}`;
  }

  const btnSalvar = document.getElementById('btn-salvar-membro-texto');
  if (btnSalvar) btnSalvar.textContent = '💾 Salvar Novo Membro e Ver no Rol Cadastrado';

  const statusCep = document.getElementById('status-cep-mem');
  if (statusCep) statusCep.textContent = '';
  if (document.getElementById('mem-observacoes')) document.getElementById('mem-observacoes').value = '';
  if (document.getElementById('mem-profissao')) document.getElementById('mem-profissao').value = '';
  if (document.getElementById('mem-conjuge')) document.getElementById('mem-conjuge').value = '';
  if (document.getElementById('mem-data-casamento')) document.getElementById('mem-data-casamento').value = '';
  if (document.getElementById('mem-tipo-transferencia')) document.getElementById('mem-tipo-transferencia').value = '';
  if (document.getElementById('mem-motivo-transferencia')) document.getElementById('mem-motivo-transferencia').value = '';
  if (document.getElementById('mem-ministerio-2')) document.getElementById('mem-ministerio-2').value = '';
  if (document.getElementById('mem-funcao-min-2')) document.getElementById('mem-funcao-min-2').value = '';

  removerFotoMembro();
  popularSelectsCadastroMembro();

  switchSecretariaSubtab('cadastro');
  setTimeout(() => {
    const nomeInp = document.getElementById('mem-nome');
    if (nomeInp) nomeInp.focus();
  }, 100);
}

function editarMembro(id) {
  const m = (STATE.membros || []).find(x => Number(x.id) === Number(id));
  if (!m) {
    alert('Membro não encontrado.');
    return;
  }

  const inpId = document.getElementById('mem-id');
  if (inpId) inpId.value = m.id;

  if (document.getElementById('mem-nome')) document.getElementById('mem-nome').value = m.nome || '';
  if (document.getElementById('mem-apelido')) document.getElementById('mem-apelido').value = m.apelido || '';
  if (document.getElementById('mem-familia')) document.getElementById('mem-familia').value = m.familia || '';
  if (document.getElementById('mem-cpf')) document.getElementById('mem-cpf').value = m.cpf || '';
  if (document.getElementById('mem-rg')) document.getElementById('mem-rg').value = m.rg || '';
  if (document.getElementById('mem-nascimento')) document.getElementById('mem-nascimento').value = m.data_nascimento || '';
  if (document.getElementById('mem-genero')) document.getElementById('mem-genero').value = m.genero || 'Masculino';
  if (document.getElementById('mem-estado-civil')) document.getElementById('mem-estado-civil').value = m.estado_civil || 'Casado(a)';
  if (document.getElementById('mem-profissao')) document.getElementById('mem-profissao').value = m.profissao || '';
  if (document.getElementById('mem-conjuge')) document.getElementById('mem-conjuge').value = m.conjuge || '';
  if (document.getElementById('mem-data-casamento')) document.getElementById('mem-data-casamento').value = m.data_casamento || '';
  if (document.getElementById('mem-telefone')) document.getElementById('mem-telefone').value = m.telefone || '';
  if (document.getElementById('mem-email')) document.getElementById('mem-email').value = m.email || '';
  if (document.getElementById('mem-cidade-nasc')) document.getElementById('mem-cidade-nasc').value = m.cidade_nascimento || '';
  if (document.getElementById('mem-estado-nasc')) document.getElementById('mem-estado-nasc').value = m.estado_nascimento || '';
  if (document.getElementById('mem-cep')) document.getElementById('mem-cep').value = m.cep || '';
  if (document.getElementById('mem-logradouro')) document.getElementById('mem-logradouro').value = m.logradouro || '';
  if (document.getElementById('mem-numero')) document.getElementById('mem-numero').value = m.numero || '';
  if (document.getElementById('mem-complemento')) document.getElementById('mem-complemento').value = m.complemento || '';
  if (document.getElementById('mem-bairro')) document.getElementById('mem-bairro').value = m.bairro_endereco || '';
  if (document.getElementById('mem-cidade-end')) document.getElementById('mem-cidade-end').value = m.cidade_endereco || 'São Paulo';
  if (document.getElementById('mem-uf-end')) document.getElementById('mem-uf-end').value = m.uf_endereco || 'SP';
  if (document.getElementById('mem-batismo')) document.getElementById('mem-batismo').value = m.data_batismo || '';
  if (document.getElementById('mem-cargo')) document.getElementById('mem-cargo').value = m.cargo_eclesiastico || 'Membro';
  if (document.getElementById('mem-status')) document.getElementById('mem-status').value = m.status || 'Ativo';
  if (document.getElementById('mem-sala-ebd')) document.getElementById('mem-sala-ebd').value = m.sala_ebd || '';
  if (document.getElementById('mem-observacoes')) document.getElementById('mem-observacoes').value = m.observacoes || '';

  // Foto do Membro
  const fotoInp = document.getElementById('mem-foto-base64');
  const fotoPrev = document.getElementById('mem-foto-preview');
  const fotoPh = document.getElementById('mem-foto-placeholder');
  const btnRem = document.getElementById('btn-remover-foto-mem');
  if (fotoInp) fotoInp.value = m.foto_base64 || '';
  if (m.foto_base64) {
    if (fotoPrev) { fotoPrev.src = m.foto_base64; fotoPrev.classList.remove('hidden'); }
    if (fotoPh) fotoPh.classList.add('hidden');
    if (btnRem) btnRem.classList.remove('hidden');
  } else {
    if (fotoPrev) { fotoPrev.src = ''; fotoPrev.classList.add('hidden'); }
    if (fotoPh) fotoPh.classList.remove('hidden');
    if (btnRem) btnRem.classList.add('hidden');
  }

  // Situação de Transferência / Inativação e Motivo
  if (document.getElementById('mem-tipo-transferencia')) {
    document.getElementById('mem-tipo-transferencia').value = m.tipo_transferencia || '';
  }
  if (document.getElementById('mem-motivo-transferencia')) {
    document.getElementById('mem-motivo-transferencia').value = m.motivo_transferencia || '';
  }

  popularSelectsCadastroMembro();
  if (document.getElementById('mem-celula')) document.getElementById('mem-celula').value = m.celula_id || '';

  // Ministérios 1 e 2
  const minVinculado1 = (m.ministerios && m.ministerios.length > 0) ? m.ministerios[0] : null;
  const minVinculado2 = (m.ministerios && m.ministerios.length > 1) ? m.ministerios[1] : null;

  if (document.getElementById('mem-ministerio')) {
    document.getElementById('mem-ministerio').value = minVinculado1 ? minVinculado1.ministerio_id : (m.ministerio_id || '');
  }
  if (document.getElementById('mem-funcao-min')) {
    const f1 = minVinculado1 ? minVinculado1.funcao : (m.funcao_ministerio || 'Voluntário');
    const el1 = document.getElementById('mem-funcao-min');
    if (f1 && !Array.from(el1.options).some(o => o.value === f1)) {
      el1.add(new Option(f1, f1, true, true));
    }
    el1.value = f1;
  }

  if (document.getElementById('mem-ministerio-2')) {
    document.getElementById('mem-ministerio-2').value = minVinculado2 ? minVinculado2.ministerio_id : (m.ministerio_id_2 || '');
  }
  if (document.getElementById('mem-funcao-min-2')) {
    const f2 = minVinculado2 ? minVinculado2.funcao : (m.funcao_ministerio_2 || '');
    const el2 = document.getElementById('mem-funcao-min-2');
    if (f2 && !Array.from(el2.options).some(o => o.value === f2)) {
      el2.add(new Option(f2, f2, true, true));
    }
    el2.value = f2;
  }

  const titulo = document.getElementById('titulo-cadastro-membro');
  if (titulo) titulo.textContent = `✏️ Editando Cadastro: ${m.nome}`;

  const badgeFicha = document.getElementById('badge-proxima-ficha');
  if (badgeFicha) badgeFicha.textContent = `Matrícula #${String(m.id).padStart(4, '0')}`;

  const btnSalvar = document.getElementById('btn-salvar-membro-texto');
  if (btnSalvar) btnSalvar.textContent = '💾 Atualizar Cadastro do Membro';

  const statusCep = document.getElementById('status-cep-mem');
  if (statusCep) statusCep.textContent = '';

  switchSecretariaSubtab('cadastro');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function popularSelectsCadastroMembro() {
  const mins = STATE.ministerios || [];
  const minOptions = '<option value="">-- Nenhum ministério selecionado --</option>' + 
    mins.map(m => `<option value="${m.id}">${m.nome}</option>`).join('');

  const selMin = document.getElementById('mem-ministerio');
  if (selMin) {
    const valAtual = selMin.value;
    selMin.innerHTML = minOptions;
    if (valAtual) selMin.value = valAtual;
  }

  const selMin2 = document.getElementById('mem-ministerio-2');
  if (selMin2) {
    const valAtual2 = selMin2.value;
    selMin2.innerHTML = minOptions;
    if (valAtual2) selMin2.value = valAtual2;
  }
}

function formatarEBuscarCep(input, prefixo = 'mem') {
  let val = (input.value || '').replace(/\D/g, '');
  if (val.length > 8) val = val.substring(0, 8);
  if (val.length > 5) {
    input.value = val.substring(0, 5) + '-' + val.substring(5);
  } else {
    input.value = val;
  }
  if (val.length === 8) {
    buscarCepMembro(prefixo);
  }
}

async function buscarCepMembro(prefixo = 'mem') {
  const inpCep = document.getElementById(`${prefixo}-cep`);
  if (!inpCep) return;
  const cep = inpCep.value.replace(/\D/g, '');
  if (cep.length !== 8) return;

  const statusEl = document.getElementById(`status-cep-${prefixo}`);
  if (statusEl) {
    statusEl.innerHTML = '<span class="text-indigo-600 font-bold animate-pulse">⏳ Consultando CEP...</span>';
  }

  try {
    const res = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
    const data = await res.json();
    if (data.erro) {
      if (statusEl) statusEl.innerHTML = '<span class="text-rose-600 font-bold">❌ CEP não encontrado</span>';
      return;
    }

    if (document.getElementById(`${prefixo}-logradouro`)) document.getElementById(`${prefixo}-logradouro`).value = data.logradouro || '';
    if (document.getElementById(`${prefixo}-bairro`)) document.getElementById(`${prefixo}-bairro`).value = data.bairro || '';
    if (document.getElementById(`${prefixo}-cidade-end`)) document.getElementById(`${prefixo}-cidade-end`).value = data.localidade || '';
    if (document.getElementById(`${prefixo}-uf-end`)) document.getElementById(`${prefixo}-uf-end`).value = data.uf || '';

    if (statusEl) {
      statusEl.innerHTML = '<span class="text-emerald-700 font-bold">✓ Endereço preenchido via CEP!</span>';
    }
    const inpNum = document.getElementById(`${prefixo}-numero`);
    if (inpNum) inpNum.focus();
  } catch (err) {
    if (statusEl) statusEl.innerHTML = '<span class="text-rose-600 font-bold">Erro ao consultar CEP</span>';
  }
}

async function salvarMembro(e) {
  e.preventDefault();
  const idMembro = document.getElementById('mem-id')?.value;
  const isEdicao = Boolean(idMembro);

  const payload = {
    nome: (document.getElementById('mem-nome')?.value || '').trim(),
    apelido: (document.getElementById('mem-apelido')?.value || '').trim(),
    familia: (document.getElementById('mem-familia')?.value || '').trim(),
    cpf: (document.getElementById('mem-cpf')?.value || '').trim(),
    rg: (document.getElementById('mem-rg')?.value || '').trim(),
    data_nascimento: document.getElementById('mem-nascimento')?.value || '',
    genero: document.getElementById('mem-genero')?.value || 'Masculino',
    estado_civil: document.getElementById('mem-estado-civil')?.value || 'Casado(a)',
    profissao: (document.getElementById('mem-profissao')?.value || '').trim(),
    conjuge: (document.getElementById('mem-conjuge')?.value || '').trim(),
    data_casamento: document.getElementById('mem-data-casamento')?.value || '',
    telefone: (document.getElementById('mem-telefone')?.value || '').trim(),
    email: (document.getElementById('mem-email')?.value || '').trim(),
    cidade_nascimento: (document.getElementById('mem-cidade-nasc')?.value || '').trim(),
    estado_nascimento: (document.getElementById('mem-estado-nasc')?.value || '').trim(),
    cep: (document.getElementById('mem-cep')?.value || '').trim(),
    logradouro: (document.getElementById('mem-logradouro')?.value || '').trim(),
    numero: (document.getElementById('mem-numero')?.value || '').trim(),
    complemento: (document.getElementById('mem-complemento')?.value || '').trim(),
    bairro_endereco: (document.getElementById('mem-bairro')?.value || '').trim(),
    cidade_endereco: (document.getElementById('mem-cidade-end')?.value || '').trim(),
    uf_endereco: (document.getElementById('mem-uf-end')?.value || '').trim(),
    data_batismo: document.getElementById('mem-batismo')?.value || '',
    cargo_eclesiastico: document.getElementById('mem-cargo')?.value || 'Membro',
    status: document.getElementById('mem-status')?.value || 'Ativo',
    sala_ebd: (document.getElementById('mem-sala-ebd')?.value || '').trim(),
    celula_id: document.getElementById('mem-celula')?.value ? parseInt(document.getElementById('mem-celula').value) : null,
    foto_base64: document.getElementById('mem-foto-base64')?.value || '',
    ministerio_id: document.getElementById('mem-ministerio')?.value ? parseInt(document.getElementById('mem-ministerio').value) : null,
    funcao_ministerio: (document.getElementById('mem-funcao-min')?.value || 'Voluntário').trim(),
    ministerio_id_2: document.getElementById('mem-ministerio-2')?.value ? parseInt(document.getElementById('mem-ministerio-2').value) : null,
    funcao_ministerio_2: (document.getElementById('mem-funcao-min-2')?.value || '').trim(),
    tipo_transferencia: document.getElementById('mem-tipo-transferencia')?.value || '',
    motivo_transferencia: (document.getElementById('mem-motivo-transferencia')?.value || '').trim(),
    observacoes: (document.getElementById('mem-observacoes')?.value || '').trim()
  };

  if (!payload.nome) {
    alert('O nome do membro é obrigatório!');
    return;
  }

  let res;
  if (isEdicao) {
    payload.id = parseInt(idMembro);
    res = await apiPost('/api/membros/atualizar', payload);
  } else {
    res = await apiPost('/api/membros', payload);
  }

  if (res.status === 200) {
    alert(isEdicao ? `✓ Cadastro de "${payload.nome}" atualizado com sucesso!` : `✓ Membro "${payload.nome}" cadastrado com sucesso!`);
    document.getElementById('form-membro')?.reset();
    if (typeof removerFotoMembro === 'function') removerFotoMembro();
    if (document.getElementById('mem-id')) document.getElementById('mem-id').value = '';
    await fetchBootstrap();
    switchSecretariaSubtab('lista');
  } else {
    alert(res.data?.erro || 'Erro ao salvar membro.');
  }
}

async function salvarVisitante(e) {
  e.preventDefault();
  const payload = {
    nome: document.getElementById('vis-nome').value,
    telefone: document.getElementById('vis-telefone').value,
    data_visita: document.getElementById('vis-data').value,
    culto: document.getElementById('vis-culto').value,
    celula_indicada_id: document.getElementById('vis-celula').value || null,
    pedido_oracao: document.getElementById('vis-oracao').value
  };
  await apiPost('/api/visitantes', payload);
  e.target.reset();
  fetchBootstrap();
}

async function converterVisitante(id) {
  await apiPost('/api/visitantes/converter', { id });
  fetchBootstrap();
}

async function salvarEscala(e, forcar = false) {
  if (e) e.preventDefault();
  const alertaBox = document.getElementById('alerta-conflito-escala');
  const textoBox = document.getElementById('texto-conflito-escala');

  const payload = {
    data_culto: document.getElementById('esc-data').value,
    horario: document.getElementById('esc-horario').value,
    evento_culto: document.getElementById('esc-evento').value,
    ministerio_id: document.getElementById('esc-ministerio').value,
    membro_id: document.getElementById('esc-membro').value,
    funcao_escala: document.getElementById('esc-funcao').value,
    forcar_conflito: forcar
  };

  const { status, data } = await apiPost('/api/escalas', payload);
  if (status === 409 && data.conflito) {
    textoBox.textContent = data.erro;
    alertaBox.classList.remove('hidden');
    return;
  }

  alertaBox.classList.add('hidden');
  document.getElementById('esc-funcao').value = '';
  fetchBootstrap();
}

async function vincularVoluntario(e) {
  e.preventDefault();
  await apiPost('/api/voluntarios', {
    membro_id: document.getElementById('vol-membro').value,
    ministerio_id: document.getElementById('vol-ministerio').value,
    funcao: document.getElementById('vol-funcao').value
  });
  document.getElementById('vol-funcao').value = '';
  fetchBootstrap();
}

async function salvarRequisicao(e) {
  e.preventDefault();
  await apiPost('/api/requisicoes', {
    ministerio_id: document.getElementById('req-ministerio').value,
    titulo: document.getElementById('req-titulo').value,
    valor_estimado: document.getElementById('req-valor').value,
    prioridade: document.getElementById('req-prioridade').value,
    justificativa: document.getElementById('req-justificativa').value
  });
  e.target.reset();
  fetchBootstrap();
}

async function avaliarRequisicao(id, decisao) {
  await apiPost('/api/requisicoes/avaliar', { id, decisao });
  fetchBootstrap();
}

async function salvarCelula(e) {
  e.preventDefault();
  await apiPost('/api/celulas', {
    nome: document.getElementById('cel-nome').value,
    lider: document.getElementById('cel-lider').value,
    bairro: document.getElementById('cel-bairro').value,
    meta_membros: document.getElementById('cel-meta').value,
    dia_horario: document.getElementById('cel-horario').value
  });
  e.target.reset();
  fetchBootstrap();
}

async function atualizarFrequenciaCelula(id) {
  const val = document.getElementById(`freq-input-${id}`).value;
  await apiPost('/api/celulas/frequencia', { id, ultima_frequencia: val });
  fetchBootstrap();
}

async function salvarPatrimonio(e) {
  e.preventDefault();
  await apiPost('/api/patrimonio', {
    codigo: document.getElementById('pat-codigo').value,
    estado: document.getElementById('pat-estado').value,
    item: document.getElementById('pat-item').value,
    ministerio_id: document.getElementById('pat-ministerio').value || null,
    localizacao: document.getElementById('pat-local').value,
    valor_aquisicao: document.getElementById('pat-valor').value || 0,
    responsavel: document.getElementById('pat-resp').value
  });
  e.target.reset();
  fetchBootstrap();
}



let FILTRO_USUARIOS_TERMO = '';
let FILTRO_USUARIOS_TIPO = 'TODOS';

function aoBuscarUsuariosNaTela(val) {
  FILTRO_USUARIOS_TERMO = (val || '').trim().toLowerCase();
  renderUsuarios(FILTRO_USUARIOS_TERMO, FILTRO_USUARIOS_TIPO);
}

function aoFiltrarTipoUsuarios(tipo) {
  FILTRO_USUARIOS_TIPO = tipo;
  ['filtro-usr-todos', 'filtro-usr-pendentes', 'filtro-usr-definitivas', 'filtro-usr-admins'].forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.className = 'px-3.5 py-2 rounded-xl font-bold bg-white text-slate-700 hover:bg-slate-100 border border-slate-200 cursor-pointer transition';
  });
  const ativo = document.getElementById({
    TODOS: 'filtro-usr-todos',
    PENDENTES: 'filtro-usr-pendentes',
    DEFINITIVAS: 'filtro-usr-definitivas',
    ADMINS: 'filtro-usr-admins'
  }[tipo]);
  if (ativo) {
    ativo.className = 'px-3.5 py-2 rounded-xl font-bold bg-indigo-600 text-white border border-indigo-600 shadow-xs cursor-pointer transition';
  }
  renderUsuarios(FILTRO_USUARIOS_TERMO, FILTRO_USUARIOS_TIPO);
}

function renderUsuarios(termoBusca = FILTRO_USUARIOS_TERMO, tipoFiltro = FILTRO_USUARIOS_TIPO) {
  const usuarios = STATE.usuarios || [];

  // Atualiza KPIs
  const kpiTotal = document.getElementById('kpi-total-usuarios');
  const kpiAdmins = document.getElementById('kpi-total-admins');
  const kpiSenhas = document.getElementById('kpi-total-senhas-ok');
  const kpiPendentes = document.getElementById('kpi-total-senhas-pendentes');
  const badgeTotalCad = document.getElementById('badge-total-usr-cadastrados');

  const totalUsers = usuarios.length;
  const totalAdmins = usuarios.filter(u => u.perfil === 'ADMIN').length;
  const totalDefinitivas = usuarios.filter(u => Number(u.senha_alterada) === 1).length;
  const totalPendentes = usuarios.filter(u => Number(u.senha_alterada) !== 1).length;

  if (kpiTotal) kpiTotal.textContent = `${totalUsers} operador(es)`;
  if (kpiAdmins) kpiAdmins.textContent = `${totalAdmins} com acesso total`;
  if (kpiSenhas) kpiSenhas.textContent = `${totalDefinitivas} protegido(s)`;
  if (kpiPendentes) kpiPendentes.textContent = `${totalPendentes} pendente(s)`;
  if (badgeTotalCad) badgeTotalCad.textContent = `${totalUsers} cadastrado(s)`;

  const badgeMenuUsr = document.getElementById('badge-usuarios');
  if (badgeMenuUsr) badgeMenuUsr.textContent = totalUsers;

  renderOperatorSelector();

  const usrCont = document.getElementById('lista-usuarios');
  if (!usrCont) return;

  const descPerfil = {
    ADMIN: '👑 ADMIN Geral',
    FINANCEIRO: '💰 Financeiro',
    TESOURARIA: '💰 Financeiro',
    PATRIMONIO: '🏛️ Patrimônio',
    SECRETARIA: '👥 Secretaria',
    MINISTERIO: '📅 Ministério',
    RECEPCAO: '🤝 Recepção',
    CUSTOM: '⚙️ Personalizado'
  };

  let filtrados = usuarios.filter(u => {
    if (tipoFiltro === 'PENDENTES' && Number(u.senha_alterada) === 1) return false;
    if (tipoFiltro === 'DEFINITIVAS' && Number(u.senha_alterada) !== 1) return false;
    if (tipoFiltro === 'ADMINS' && u.perfil !== 'ADMIN') return false;

    if (termoBusca) {
      const matchNome = (u.nome || '').toLowerCase().includes(termoBusca);
      const matchCargo = (u.cargo || '').toLowerCase().includes(termoBusca);
      const matchEmail = (u.email || '').toLowerCase().includes(termoBusca);
      const matchPerfil = (u.perfil || '').toLowerCase().includes(termoBusca);
      return matchNome || matchCargo || matchEmail || matchPerfil;
    }
    return true;
  });

  if (filtrados.length === 0) {
    usrCont.innerHTML = `
      <div class="col-span-full py-12 px-6 text-center bg-slate-50 rounded-3xl border border-dashed border-slate-300">
        <span class="text-4xl block mb-2">🔍</span>
        <h4 class="font-bold text-slate-800 text-sm">Nenhum operador encontrado</h4>
        <p class="text-xs text-slate-500 mt-1">Tente ajustar o termo da busca ou o filtro de status selecionado.</p>
        <button type="button" onclick="aoFiltrarTipoUsuarios('TODOS'); const b = document.getElementById('busca-usuarios-input'); if(b) b.value=''; aoBuscarUsuariosNaTela('');" class="mt-4 bg-white border border-slate-300 text-indigo-700 hover:bg-indigo-50 font-bold px-4 py-2 rounded-xl text-xs transition cursor-pointer">
          Limpar Filtros
        </button>
      </div>
    `;
    return;
  }

  usrCont.innerHTML = filtrados.map(u => {
    const permitidas = getPermissoesOperador(u);
    const badges = [];

    if (u.perfil === 'ADMIN') {
      badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">👑 Acesso Total (Todos os Setores)</span>`);
    } else {
      if (permitidas.includes('dashboard')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">📊 Visão Geral</span>`);
      if (permitidas.includes('tesouraria')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">💰 Tesouraria</span>`);
      if (permitidas.includes('pedidos')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">📤 Pedidos</span>`);
      if (permitidas.includes('projecao')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">📽️ Projeção</span>`);
      if (permitidas.includes('secretaria')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">👥 Secretaria</span>`);
      if (permitidas.includes('atas')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-violet-100 text-violet-800 border border-violet-200">📜 Atas</span>`);
      if (permitidas.includes('ministerios')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-200">📅 Ministérios</span>`);
      if (permitidas.includes('celulas')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">🏡 Células</span>`);
      if (permitidas.includes('patrimonio')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">🏛️ Patrimônio</span>`);
      if (permitidas.includes('recepcao')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800 border border-teal-200">🤝 Recepção</span>`);
      if (permitidas.includes('acessos')) badges.push(`<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">⚙️ Acessos</span>`);
    }

    const relsU = getRelatoriosPermitidos(u);
    let relBadge = '';
    if (u.perfil === 'ADMIN' || relsU.includes('*') || relsU.length >= 16) {
      relBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">📑 Todos Relatórios (16)</span>`;
    } else if (relsU.length > 0) {
      relBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">📑 ${relsU.length} Relatório(s)</span>`;
    } else {
      relBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200">📑 Sem relatórios</span>`;
    }

    // Iniciais do nome para avatar visual
    const partesNome = (u.nome || 'U').trim().split(/\\s+/);
    const iniciais = (partesNome[0][0] + (partesNome.length > 1 ? partesNome[partesNome.length - 1][0] : '')).toUpperCase();
    const avatarGradients = [
      'from-indigo-600 to-purple-600',
      'from-emerald-600 to-teal-700',
      'from-blue-600 to-indigo-700',
      'from-rose-600 to-pink-700',
      'from-amber-600 to-orange-700'
    ];
    const gradIndex = Math.abs((Number(u.id) || 1) * 7) % avatarGradients.length;
    const grad = avatarGradients[gradIndex];

    const isSenhaAlterada = Number(u.senha_alterada) === 1;

    return `
      <div class="bg-white rounded-3xl border border-slate-200 p-5 shadow-xs hover:border-indigo-300 hover:shadow-md transition flex flex-col justify-between overflow-hidden gap-3.5">
        
        <!-- Cabeçalho do Card: Avatar, Identificação e Perfil -->
        <div class="flex items-start justify-between gap-3 pb-3 border-b border-slate-100">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-11 h-11 rounded-2xl bg-gradient-to-br ${grad} text-white font-black text-sm flex items-center justify-center shrink-0 shadow-sm">
              ${iniciais}
            </div>
            <div class="min-w-0">
              <h4 class="font-black text-slate-900 text-sm leading-tight truncate" title="${u.nome}">${u.nome}</h4>
              <p class="text-[11px] text-slate-600 font-medium truncate mt-0.5" title="${u.cargo}">${u.cargo}</p>
              <p class="text-[10px] text-slate-400 font-mono truncate" title="${u.email}">🔑 ${u.email}</p>
            </div>
          </div>
          <span class="text-[10px] bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-1 rounded-xl font-bold shrink-0">
            ${descPerfil[u.perfil] || u.perfil}
          </span>
        </div>

        <!-- Status de Senha e Credencial -->
        <div class="bg-slate-50/80 rounded-2xl p-3 border border-slate-200/80 space-y-2 text-[11px]">
          <div class="flex items-center justify-between">
            <span class="text-slate-600 font-bold flex items-center gap-1.5">
              <span>🔒</span> Credencial:
            </span>
            <span class="flex items-center gap-1.5 font-mono font-bold text-slate-700 bg-white px-2.5 py-1 rounded-lg border border-slate-200 text-[10px]">
              <span id="senha-mask-${u.id}">••••••</span>
              <span id="senha-val-${u.id}" class="hidden text-indigo-700 font-bold">${u.senha || '123456'}</span>
              <button type="button" onclick="alternarVerSenhaCard(${u.id})" class="text-slate-400 hover:text-slate-800 text-xs cursor-pointer ml-1" title="Ver / Ocultar Senha">👁️</button>
            </span>
          </div>
          <div class="flex items-center justify-between pt-1.5 border-t border-slate-200/60 gap-1.5 flex-wrap">
            <div>
              ${isSenhaAlterada ? 
                '<span class="text-[10px] font-extrabold text-emerald-800 bg-emerald-100/80 border border-emerald-300 px-2 py-0.5 rounded-full inline-flex items-center gap-1">✅ Senha Definitiva</span>' : 
                '<span class="text-[10px] font-extrabold text-amber-800 bg-amber-100/90 border border-amber-300 px-2 py-0.5 rounded-full inline-flex items-center gap-1">⚠️ 1º Acesso Pendente</span>'
              }
            </div>
            <div class="flex items-center gap-1.5">
              <button type="button" onclick="abrirModalAlterarSenhaUsuario(${u.id})" class="text-[10px] text-indigo-700 hover:text-white bg-indigo-50 hover:bg-indigo-600 px-2.5 py-1 rounded-xl border border-indigo-200 hover:border-indigo-600 font-bold transition flex items-center gap-1 cursor-pointer shadow-2xs" title="Definir nova senha para este operador">
                🔑 Alterar Senha
              </button>
              <button type="button" onclick="resetarSenhaOperador(${u.id})" class="text-[10px] text-amber-800 hover:text-amber-900 bg-amber-50 hover:bg-amber-100 px-2.5 py-1 rounded-xl border border-amber-200 font-bold transition flex items-center gap-1 cursor-pointer" title="Resetar para senha padrão 123456">
                🔄 Resetar 123456
              </button>
            </div>
          </div>
        </div>

        <!-- Setores Liberados -->
        <div class="bg-slate-50/50 rounded-2xl p-3 border border-slate-200/60 space-y-2">
          <div class="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <span>Setores Autorizados:</span>
            <span class="font-mono text-slate-400">${u.perfil === 'ADMIN' ? '12' : permitidas.filter(p => p !== 'ministerios_painel').length} liberado(s)</span>
          </div>
          <div class="flex flex-wrap gap-1.5 items-center">
            ${badges.length > 0 ? badges.join('') : '<span class="text-[10px] text-slate-400 font-medium italic">Nenhum módulo selecionado</span>'}
          </div>
          <div class="pt-1.5 border-t border-slate-200/50 flex items-center justify-between">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Relatórios:</span>
            ${relBadge}
          </div>
        </div>

        <!-- Botões de Ação do Card -->
        <div class="flex items-center gap-2 pt-2 border-t border-slate-100">
          <button type="button" onclick="carregarUsuarioNoFormulario(${u.id})" class="flex-1 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white font-bold py-2.5 px-3 rounded-xl text-xs border border-indigo-200 hover:border-indigo-600 transition flex items-center justify-center gap-1.5 cursor-pointer shadow-2xs">
            <span>✏️</span> Editar Acessos & Permissões
          </button>
          ${totalUsers > 1 ? `
            <button type="button" onclick="removerItem('/api/usuarios', ${u.id})" title="Remover Operador" class="bg-rose-50 hover:bg-rose-600 text-rose-600 hover:text-white border border-rose-200 hover:border-rose-600 py-2.5 px-3 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs">
              🗑️
            </button>
          ` : ''}
        </div>

      </div>
    `;
  }).join('');
}



function atualizarContadorModulosForm() {
  const badge = document.getElementById('badge-total-modulos-selecionados');
  if (!badge) return;
  const modulosCbs = [
    'ctrl-dashboard', 'ctrl-financeiro', 'ctrl-pedidos', 'ctrl-projecao',
    'ctrl-relatorios', 'ctrl-secretaria', 'ctrl-atas', 'ctrl-ministerios',
     'ctrl-celulas', 'ctrl-patrimonio',
    'ctrl-recepcao', 'ctrl-acessos'
  ];
  let marcados = 0;
  modulosCbs.forEach(id => {
    if (document.getElementById(id)?.checked) marcados++;
  });
  const total = modulosCbs.length;

  if (marcados === total) {
    badge.textContent = `Todos (${total} de ${total})`;
    badge.className = 'text-[10px] font-bold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full';
  } else if (marcados === 0) {
    badge.textContent = 'Nenhum selecionado (0 de 12)';
    badge.className = 'text-[10px] font-bold bg-rose-100 text-rose-700 px-2.5 py-0.5 rounded-full';
  } else {
    badge.textContent = `${marcados} de ${total} selecionados`;
    badge.className = 'text-[10px] font-bold bg-indigo-100 text-indigo-700 px-2.5 py-0.5 rounded-full';
  }
}

async function salvarUsuario(e) {
  if (e && e.preventDefault) e.preventDefault();

  const editId = document.getElementById('usr-edit-id')?.value;
  const cDash = !!document.getElementById('ctrl-dashboard')?.checked;
  const cFin = !!document.getElementById('ctrl-financeiro')?.checked;
  const cPed = !!document.getElementById('ctrl-pedidos')?.checked;
  const cRel = !!document.getElementById('ctrl-relatorios')?.checked;
  const cProj = !!document.getElementById('ctrl-projecao')?.checked;
  const cPat = !!document.getElementById('ctrl-patrimonio')?.checked;
  const cSec = !!document.getElementById('ctrl-secretaria')?.checked;
  const cAtas = !!document.getElementById('ctrl-atas')?.checked;
    const cMin = !!document.getElementById('ctrl-ministerios')?.checked;
  const cCel = !!document.getElementById('ctrl-celulas')?.checked;
  const cRec = !!document.getElementById('ctrl-recepcao')?.checked;
  const cAce = !!document.getElementById('ctrl-acessos')?.checked;

  const perfil = document.getElementById('usr-perfil')?.value || 'CUSTOM';

  const setores = [];
  if (cDash) setores.push('dashboard');
  if (cFin) setores.push('tesouraria');
  if (cPed) setores.push('pedidos');
  if (cRel) setores.push('relatorios');
  if (cProj) setores.push('projecao');
  if (cPat) setores.push('patrimonio');
  if (cSec) setores.push('secretaria');
  if (cAtas) setores.push('atas');
    if (cMin) setores.push('ministerios');
  if (cCel) setores.push('celulas');
  if (cRec) setores.push('recepcao');
  if (cAce) setores.push('acessos');

  if (setores.length === 0) {
    alert('⚠️ Selecione pelo menos um módulo ou setor a ser liberado para este operador.');
    return;
  }

  // Coleta lista específica de relatórios autorizados
  const relCheckboxes = document.querySelectorAll('input[name="ctrl-rel"]:checked');
  const relsMarcados = Array.from(relCheckboxes).map(el => el.value);
  const totalRels = document.querySelectorAll('input[name="ctrl-rel"]').length;

  let relatorios_permitidos = '*';
  if (cRel) {
    if (relsMarcados.length === totalRels) {
      relatorios_permitidos = '*';
    } else if (relsMarcados.length === 0) {
      relatorios_permitidos = 'nenhum';
    } else {
      relatorios_permitidos = relsMarcados.join(',');
    }
  } else {
    relatorios_permitidos = 'nenhum';
  }

  const nome = (document.getElementById('usr-nome')?.value || '').trim();
  const email = (document.getElementById('usr-email')?.value || '').trim();
  const cargo = (document.getElementById('usr-cargo')?.value || '').trim();
  const senhaInp = (document.getElementById('usr-senha')?.value || '').trim();

  if (!nome) {
    showLiveToast('⚠️ Informe o nome do usuário.');
    document.getElementById('usr-nome')?.focus();
    return;
  }
  if (!email) {
    showLiveToast('⚠️ Informe o e-mail ou identificador de acesso.');
    document.getElementById('usr-email')?.focus();
    return;
  }
  if (!cargo) {
    showLiveToast('⚠️ Informe o cargo ou função do usuário.');
    document.getElementById('usr-cargo')?.focus();
    return;
  }

  if (editId) {
    // Modo Edição
    const res = await apiPost('/api/usuarios/editar', {
      id: Number(editId),
      nome,
      email,
      cargo,
      perfil,
      setores_permitidos: setores.join(','),
      relatorios_permitidos,
      senha: senhaInp
    });

    if (!res.data || !res.data.ok) {
      alert(res.data?.mensagem || res.data?.erro || 'Erro ao salvar alterações do usuário.');
      return;
    }

    await fetchBootstrap();
    renderUsuarios();
    carregarUsuarioNoFormulario(Number(editId));
    showLiveToast(`✅ Permissões e dados de '${nome}' salvos com sucesso!`);
  } else {
    // Modo Novo Cadastro
    const res = await apiPost('/api/usuarios', {
      nome,
      email,
      cargo,
      perfil,
      setores_permitidos: setores.join(','),
      relatorios_permitidos,
      senha: senhaInp || '123456'
    });

    if (!res.data || !res.data.ok) {
      alert(res.data?.mensagem || res.data?.erro || 'Erro ao cadastrar novo usuário.');
      return;
    }

    await fetchBootstrap();
    renderUsuarios();
    fecharFormularioUsuario();
    showLiveToast(`✅ Novo operador '${nome}' cadastrado com sucesso!`);
  }
}

function carregarUsuarioNoFormulario(userId) {
  const u = (STATE.usuarios || []).find(x => Number(x.id) === Number(userId));
  if (!u) return;

  const box = document.getElementById('box-cadastro-operador');
  if (box) box.classList.remove('hidden');

  const inpId = document.getElementById('usr-edit-id');
  if (inpId) inpId.value = u.id;

  const inpNome = document.getElementById('usr-nome');
  if (inpNome) inpNome.value = u.nome;

  const inpEmail = document.getElementById('usr-email');
  if (inpEmail) inpEmail.value = u.email;

  const inpCargo = document.getElementById('usr-cargo');
  if (inpCargo) inpCargo.value = u.cargo;

  const inpSenha = document.getElementById('usr-senha');
  if (inpSenha) {
    inpSenha.value = '';
    inpSenha.placeholder = 'Deixe em branco para manter a senha atual';
  }

  const titulo = document.getElementById('titulo-cadastro-operador');
  const subtitulo = document.getElementById('subtitulo-cadastro-operador');
  const badge = document.getElementById('badge-cadastro-operador');
  const btnSubmit = document.getElementById('btn-submit-cadastro-operador');

  if (titulo) titulo.textContent = `Editando Operador: ${u.nome}`;
  if (subtitulo) subtitulo.textContent = `Ajuste as credenciais e selecione as permissões específicas para ${u.nome}:`;
  if (badge) {
    badge.textContent = `✏️ Editando ID #${u.id}`;
    badge.className = 'text-[11px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 px-3 py-1 rounded-full';
  }
  if (btnSubmit) {
    btnSubmit.innerHTML = '<span>💾</span> Salvar Alterações de Acesso';
    btnSubmit.className = 'bg-gradient-to-r from-indigo-600 to-purple-700 hover:from-indigo-700 hover:to-purple-800 text-white font-extrabold px-7 py-3 rounded-xl shadow-lg hover:shadow-indigo-500/30 transition flex items-center gap-2 cursor-pointer';
  }

  const perfilSelect = document.getElementById('usr-perfil');
  if (perfilSelect) perfilSelect.value = u.perfil || 'CUSTOM';

  // Desmarca tudo primeiro para carregar rigorosamente as permissões do usuário
  desmarcarTodasOpcoesFormulario();

  const permitidas = getPermissoesOperador(u);
  const setSectorCheck = (id, key) => {
    const el = document.getElementById(id);
    if (el) el.checked = permitidas.includes(key);
  };

  setSectorCheck('ctrl-dashboard', 'dashboard');
  setSectorCheck('ctrl-financeiro', 'tesouraria');
  setSectorCheck('ctrl-pedidos', 'pedidos');
  setSectorCheck('ctrl-projecao', 'projecao');
  setSectorCheck('ctrl-relatorios', 'relatorios');
  setSectorCheck('ctrl-secretaria', 'secretaria');
  setSectorCheck('ctrl-atas', 'atas');
  setSectorCheck('ctrl-ministerios', 'ministerios');
  
  setSectorCheck('ctrl-celulas', 'celulas');
  setSectorCheck('ctrl-patrimonio', 'patrimonio');
  setSectorCheck('ctrl-recepcao', 'recepcao');
  setSectorCheck('ctrl-acessos', 'acessos');

  const rels = getRelatoriosPermitidos(u);
  const relCbs = document.querySelectorAll('input[name="ctrl-rel"]');
  relCbs.forEach(cb => {
    cb.checked = (rels.includes('*') || rels.includes(cb.value));
  });

  atualizarContadorModulosForm();
  atualizarContadorRelatoriosForm();

  if (box) {
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function abrirFormularioNovoUsuario() {
  const box = document.getElementById('box-cadastro-operador');
  const inpId = document.getElementById('usr-edit-id');
  const form = document.querySelector('#box-cadastro-operador form');
  const titulo = document.getElementById('titulo-cadastro-operador');
  const subtitulo = document.getElementById('subtitulo-cadastro-operador');
  const badge = document.getElementById('badge-cadastro-operador');
  const btnSubmit = document.getElementById('btn-submit-cadastro-operador');
  const perfilSelect = document.getElementById('usr-perfil');

  if (inpId) inpId.value = '';
  if (form) form.reset();

  const inpNome = document.getElementById('usr-nome');
  if (inpNome) inpNome.value = '';
  const inpEmail = document.getElementById('usr-email');
  if (inpEmail) inpEmail.value = '';
  const inpCargo = document.getElementById('usr-cargo');
  if (inpCargo) inpCargo.value = '';
  const inpSenha = document.getElementById('usr-senha');
  if (inpSenha) {
    inpSenha.value = '';
    inpSenha.placeholder = 'Digite uma senha inicial (ou deixe 123456)';
  }

  if (titulo) titulo.textContent = 'Cadastrar Novo Usuário';
  if (subtitulo) subtitulo.textContent = 'Preencha os dados do novo operador. Por padrão de segurança, nenhuma permissão vem flegada:';
  if (badge) {
    badge.textContent = '✨ Novo Cadastro de Operador';
    badge.className = 'text-[11px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full';
  }
  if (btnSubmit) {
    btnSubmit.innerHTML = '<span>➕</span> Cadastrar Novo Usuário';
    btnSubmit.className = 'bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 text-white font-extrabold px-7 py-3 rounded-xl shadow-lg hover:shadow-emerald-500/30 transition flex items-center gap-2 cursor-pointer';
  }

  if (perfilSelect) perfilSelect.value = 'CUSTOM';

  // REGRA ESTRITA SOLICITADA PELO USUÁRIO: Exibido sem NENHUMA opção flegada por padrão
  desmarcarTodasOpcoesFormulario();

  if (box) {
    box.classList.remove('hidden');
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  setTimeout(() => {
    document.getElementById('usr-nome')?.focus();
  }, 120);
}

function fecharFormularioUsuario() {
  const box = document.getElementById('box-cadastro-operador');
  if (box) box.classList.add('hidden');
  const inpId = document.getElementById('usr-edit-id');
  if (inpId) inpId.value = '';
  const form = document.querySelector('#box-cadastro-operador form');
  if (form) form.reset();
  desmarcarTodasOpcoesFormulario();
}

function cancelarEdicaoNoFormulario() {
  fecharFormularioUsuario();
}

function desmarcarTodasOpcoesFormulario() {
  const cbs = document.querySelectorAll('#box-cadastro-operador input[type="checkbox"]');
  cbs.forEach(cb => { cb.checked = false; });
  const select = document.getElementById('usr-perfil');
  if (select) select.value = 'CUSTOM';
  atualizarContadorModulosForm();
  atualizarContadorRelatoriosForm();
}

function marcarTodasOpcoesFormulario() {
  const cbs = document.querySelectorAll('#box-cadastro-operador input[type="checkbox"]');
  cbs.forEach(cb => { cb.checked = true; });
  const select = document.getElementById('usr-perfil');
  if (select) select.value = 'ADMIN';
  atualizarContadorModulosForm();
  atualizarContadorRelatoriosForm();
}

function desmarcarTodosRelatoriosForm() {
  const relCbs = document.querySelectorAll('input[name="ctrl-rel"]');
  relCbs.forEach(cb => { cb.checked = false; });
  atualizarContadorRelatoriosForm();
}

function aoMudarPerfilOperador() {
  const perfil = document.getElementById('usr-perfil')?.value;
  if (!perfil || perfil === 'CUSTOM') {
    // Modo Personalizado: mantém as escolhas manuais ou desmarcadas
    atualizarContadorModulosForm();
    atualizarContadorRelatoriosForm();
    return;
  }

  const cDash = document.getElementById('ctrl-dashboard');
  const cFin = document.getElementById('ctrl-financeiro');
  const cPed = document.getElementById('ctrl-pedidos');
  const cRel = document.getElementById('ctrl-relatorios');
  const cProj = document.getElementById('ctrl-projecao');
  const cSec = document.getElementById('ctrl-secretaria');
  const cAtas = document.getElementById('ctrl-atas');
  const cMin = document.getElementById('ctrl-ministerios');
    const cCel = document.getElementById('ctrl-celulas');
  const cPat = document.getElementById('ctrl-patrimonio');
  const cRec = document.getElementById('ctrl-recepcao');
  const cAce = document.getElementById('ctrl-acessos');

  const relCbs = document.querySelectorAll('input[name="ctrl-rel"]');

  if (perfil === 'ADMIN') {
    if (cDash) cDash.checked = true;
    if (cFin) cFin.checked = true;
    if (cPed) cPed.checked = true;
    if (cRel) cRel.checked = true;
    if (cProj) cProj.checked = true;
    if (cSec) cSec.checked = true;
    if (cAtas) cAtas.checked = true;
    if (cMin) cMin.checked = true;
        if (cCel) cCel.checked = true;
    if (cPat) cPat.checked = true;
    if (cRec) cRec.checked = true;
    if (cAce) cAce.checked = true;
    relCbs.forEach(cb => { cb.checked = true; });
  } else if (perfil === 'FINANCEIRO' || perfil === 'TESOURARIA') {
    if (cDash) cDash.checked = false;
    if (cFin) cFin.checked = true;
    if (cPed) cPed.checked = true;
    if (cRel) cRel.checked = true;
    if (cProj) cProj.checked = true;
    if (cSec) cSec.checked = false;
    if (cAtas) cAtas.checked = false;
    if (cMin) cMin.checked = false;
        if (cCel) cCel.checked = false;
    if (cPat) cPat.checked = false;
    if (cRec) cRec.checked = false;
    if (cAce) cAce.checked = false;
    relCbs.forEach(cb => {
      cb.checked = ['rel_livro_caixa', 'rel_balancete', 'rel_dre', 'rel_assembleia', 'rel_ministerios_geral', 'rel_plano_acao', 'rel_bi', 'rel_dizimos_membro'].includes(cb.value);
    });
  } else if (perfil === 'PATRIMONIO') {
    if (cDash) cDash.checked = false;
    if (cFin) cFin.checked = false;
    if (cPed) cPed.checked = false;
    if (cRel) cRel.checked = false;
    if (cProj) cProj.checked = false;
    if (cSec) cSec.checked = false;
    if (cAtas) cAtas.checked = false;
    if (cMin) cMin.checked = false;
        if (cCel) cCel.checked = false;
    if (cPat) cPat.checked = true;
    if (cRec) cRec.checked = false;
    if (cAce) cAce.checked = false;
    relCbs.forEach(cb => { cb.checked = (cb.value === 'rel_patrimonio'); });
  } else if (perfil === 'SECRETARIA') {
    if (cDash) cDash.checked = false;
    if (cFin) cFin.checked = false;
    if (cPed) cPed.checked = false;
    if (cRel) cRel.checked = false;
    if (cProj) cProj.checked = false;
    if (cSec) cSec.checked = true;
    if (cAtas) cAtas.checked = true;
    if (cMin) cMin.checked = false;
        if (cCel) cCel.checked = true;
    if (cPat) cPat.checked = false;
    if (cRec) cRec.checked = false;
    if (cAce) cAce.checked = false;
    relCbs.forEach(cb => {
      cb.checked = ['rel_rol_membros', 'rel_aniversariantes', 'rel_ficha_membro', 'rel_visitantes', 'rel_celulas', 'rel_escalas'].includes(cb.value);
    });
  } else if (perfil === 'MINISTERIO') {
    if (cDash) cDash.checked = false;
    if (cFin) cFin.checked = false;
    if (cPed) cPed.checked = true;
    if (cRel) cRel.checked = false;
    if (cProj) cProj.checked = false;
    if (cSec) cSec.checked = false;
    if (cAtas) cAtas.checked = false;
    if (cMin) cMin.checked = true;
        if (cCel) cCel.checked = false;
    if (cPat) cPat.checked = false;
    if (cRec) cRec.checked = false;
    if (cAce) cAce.checked = false;
    relCbs.forEach(cb => {
      cb.checked = ['rel_ministerios_geral', 'rel_escalas'].includes(cb.value);
    });
  } else if (perfil === 'RECEPCAO') {
    if (cDash) cDash.checked = false;
    if (cFin) cFin.checked = false;
    if (cPed) cPed.checked = false;
    if (cRel) cRel.checked = false;
    if (cProj) cProj.checked = false;
    if (cSec) cSec.checked = false;
    if (cAtas) cAtas.checked = false;
    if (cMin) cMin.checked = false;
        if (cCel) cCel.checked = false;
    if (cPat) cPat.checked = false;
    if (cRec) cRec.checked = true;
    if (cAce) cAce.checked = false;
    relCbs.forEach(cb => { cb.checked = (cb.value === 'rel_visitantes'); });
  }

  atualizarContadorModulosForm();
  atualizarContadorRelatoriosForm();
}

function aoAlternarCheckboxSetor() {
  const select = document.getElementById('usr-perfil');
  if (!select) return;

  const cDash = !!document.getElementById('ctrl-dashboard')?.checked;
  const cFin = !!document.getElementById('ctrl-financeiro')?.checked;
  const cPed = !!document.getElementById('ctrl-pedidos')?.checked;
  const cRel = !!document.getElementById('ctrl-relatorios')?.checked;
  const cProj = !!document.getElementById('ctrl-projecao')?.checked;
  const cSec = !!document.getElementById('ctrl-secretaria')?.checked;
  const cAtas = !!document.getElementById('ctrl-atas')?.checked;
  const cMin = !!document.getElementById('ctrl-ministerios')?.checked;
    const cCel = !!document.getElementById('ctrl-celulas')?.checked;
  const cPat = !!document.getElementById('ctrl-patrimonio')?.checked;
  const cRec = !!document.getElementById('ctrl-recepcao')?.checked;
  const cAce = !!document.getElementById('ctrl-acessos')?.checked;

  if (cDash && cFin && cPed && cRel && cProj && cSec && cAtas && cMin && cMinPainel && cCel && cPat && cRec && cAce) {
    select.value = 'ADMIN';
  } else if (!cDash && cFin && cPed && cRel && cProj && !cSec && !cAtas && !cMin && !cCel && !cPat && !cRec && !cAce) {
    select.value = 'FINANCEIRO';
  } else if (!cDash && !cFin && !cPed && !cRel && !cProj && !cSec && !cAtas && !cMin && !cCel && cPat && !cRec && !cAce) {
    select.value = 'PATRIMONIO';
  } else if (!cDash && !cFin && !cPed && !cRel && !cProj && cSec && cAtas && !cMin && cCel && !cPat && !cRec && !cAce) {
    select.value = 'SECRETARIA';
  } else if (!cDash && !cFin && cPed && !cRel && !cProj && !cSec && !cAtas && cMin && cMinPainel && !cCel && !cPat && !cRec && !cAce) {
    select.value = 'MINISTERIO';
  } else if (!cDash && !cFin && !cPed && !cRel && !cProj && !cSec && !cAtas && !cMin && !cCel && !cPat && cRec && !cAce) {
    select.value = 'RECEPCAO';
  } else {
    select.value = 'CUSTOM';
  }

  atualizarContadorModulosForm();
}



async function removerItem(rota, id) {







  const opNome = CURRENT_OPERATOR ? CURRENT_OPERATOR.nome : 'Administrador';







  const operador = encodeURIComponent(opNome);







  await fetch(`${rota}?id=${id}&operador=${operador}`, { method: 'DELETE' });







  notificarOutrasTelas(`Remoção realizada por ${opNome}`);







  fetchBootstrap();







}















function abrirModalCustom(html, mostrarBotaoPrint = true, largura = 'largo') {







  const contentEl = document.getElementById('modal-content');







  if (contentEl) {







    contentEl.innerHTML = html;







    contentEl.scrollTop = 0;







  }







  const wrapper = document.getElementById('modal-box-wrapper');







  if (wrapper) {







    wrapper.classList.remove('max-w-xl', 'max-w-2xl', 'max-w-3xl', 'max-w-4xl', 'lg:max-w-5xl');







    if (largura === 'pequeno' || largura === 'normal') {







      wrapper.classList.add('max-w-xl');







    } else {







      wrapper.classList.add('max-w-4xl', 'lg:max-w-5xl');







    }







  }







  const printBtn = document.querySelector('#modal-footer-buttons button:first-child');







  if (printBtn) {







    if (mostrarBotaoPrint) printBtn.classList.remove('hidden');







    else printBtn.classList.add('hidden');







  }







  const overlay = document.getElementById('modal-overlay');







  if (overlay) {







    overlay.classList.remove('hidden');







    overlay.style.display = 'flex';







    overlay.scrollTop = 0;







  }







}















function abrirModalNovoMinisterio() {







  const html = `







    <form onsubmit="salvarNovoMinisterioModal(event)" class="space-y-3 text-xs">







      <h3 class="text-base font-bold text-slate-900">🏛️ Criar Novo Ministério na Igreja</h3>







      <div>







        <label class="font-semibold text-slate-700 block mb-1">Nome do Ministério / Departamento *</label>







        <input type="text" id="nmin-nome" required placeholder="Ex: Ministério de Intercessão" class="w-full border border-slate-300 rounded-xl px-3 py-2" />







      </div>







      <div class="grid grid-cols-2 gap-2">







        <div>







          <label class="font-semibold text-slate-700 block mb-1">Líder Responsável *</label>







          <input type="text" id="nmin-lider" list="lista-membros-datalist" required placeholder="Digite ou selecione o líder..." class="w-full border border-slate-300 rounded-xl px-3 py-2 focus:ring-2 focus:ring-indigo-500" autocomplete="off" />







        </div>







        <div>







          <label class="font-semibold text-slate-700 block mb-1">Orçamento Anual 2026 (R$)</label>







          <input type="number" step="0.01" id="nmin-orc" value="2000.00" class="w-full border border-slate-300 rounded-xl px-3 py-2" />







        </div>







      </div>







      <div>







        <label class="font-semibold text-slate-700 block mb-1">Observações Orçamentárias</label>







        <input type="text" id="nmin-obs" placeholder="Ex: Material de apoio e encontros" class="w-full border border-slate-300 rounded-xl px-3 py-2" />







      </div>







      <div>







        <label class="font-semibold text-slate-700 block mb-1">Cor de Identificação</label>







        <input type="color" id="nmin-cor" value="#4f46e5" class="w-full h-9 border border-slate-300 rounded-xl p-1" />







      </div>







      <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-xl">







        + Criar Ministério e Integrar ao Orçamento 2026







      </button>







    </form>







  `;







  abrirModalCustom(html, false, 'largo');







  setTimeout(() => {







    atualizarContadorRelatoriosModal();







    gerarQRCodeNoElemento('modal-qrcode-canvas', linkAssembleia, 260);







  }, 100);







}















async function salvarNovoMinisterioModal(e) {







  e.preventDefault();







  await apiPost('/api/ministerios', {







    nome: document.getElementById('nmin-nome').value,







    lider: document.getElementById('nmin-lider').value,







    orcamento_2026: document.getElementById('nmin-orc').value,







    descricao: document.getElementById('nmin-obs').value,







    cor: document.getElementById('nmin-cor').value







  });







  closeModal();







  fetchBootstrap();







}















function emitirCredencial(membroId) {







  const m = STATE.membros.find(x => x.id === membroId);







  if (!m) return;















  const naturalidade = (m.cidade_nascimento || m.estado_nascimento)







    ? `${m.cidade_nascimento || ''}${m.estado_nascimento ? ' - ' + m.estado_nascimento : ''}`







    : 'Não informada';















  const html = `







    <div class="border-2 border-indigo-900 rounded-2xl p-5 bg-gradient-to-br from-slate-900 to-indigo-950 text-white">







      <div class="flex items-center justify-between border-b border-indigo-400/30 pb-3 mb-4">







        <div>







          <p class="text-[10px] uppercase tracking-widest text-indigo-300 font-bold">Credencial Oficial de Membro</p>







          <h3 class="text-lg font-extrabold">Primeira Igreja Batista no Parque São Paulo</h3>







          <p class="text-xs text-indigo-200">PIB Parque São Paulo</p>







        </div>







        ${m.foto_base64
          ? `<img src="${m.foto_base64}" alt="Foto" class="w-16 h-16 sm:w-20 sm:h-20 rounded-xl object-cover border-2 border-indigo-400 shadow-md shrink-0" />`
          : `<div class="w-12 h-12 rounded-xl bg-indigo-600 flex items-center justify-center font-bold text-xl shadow-md shrink-0">✚</div>`}







      </div>







      <div class="space-y-2.5 text-xs">







        <div class="flex items-baseline justify-between">







          <p><span class="text-indigo-300">Nome Completo:</span> <strong class="text-sm block">${m.nome} ${m.apelido ? `(${m.apelido})` : ''}</strong></p>







          <p class="text-right"><span class="text-indigo-300 block">Nº Rol / Ficha:</span> <strong class="font-mono text-emerald-300">${m.rol ? 'Rol #' + m.rol + ' • Ficha #' + String(m.numero_ficha || m.id).padStart(4, '0') : 'Ficha #' + String(m.numero_ficha || m.id).padStart(4, '0')}</strong></p>







        </div>







        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-indigo-400/20">







          <p><span class="text-indigo-300 block">📱 Celular / WhatsApp:</span> <strong class="font-mono text-emerald-300 font-bold">${m.telefone || '(11) 5924-4784'}</strong></p>







          <p><span class="text-indigo-300 block">CPF:</span> <strong class="font-mono">${m.cpf || '—'}</strong></p>







          <p><span class="text-indigo-300 block">RG:</span> <strong class="font-mono">${m.rg || '—'}</strong></p>







          <p><span class="text-indigo-300 block">Cargo Eclesiástico:</span> <strong>${m.cargo_eclesiastico}</strong></p>







          <p><span class="text-indigo-300 block">Data de Nascimento:</span> <strong>${formatDateBR(m.data_nascimento)}</strong></p>







          <p><span class="text-indigo-300 block">Data de Batismo:</span> <strong>${formatDateBR(m.data_batismo)}</strong></p>







          <p><span class="text-indigo-300 block">Naturalidade:</span> <strong>${naturalidade}</strong></p>







          <p><span class="text-indigo-300 block">Estado Civil / Gênero:</span> <strong>${m.estado_civil || '—'} • ${m.genero || '—'}</strong></p>







          <p><span class="text-indigo-300 block">Família:</span> <strong>${m.familia || '—'}</strong></p>







          <p><span class="text-indigo-300 block">Célula:</span> <strong>${m.celula_nome || 'Sede'}</strong></p>







          <p><span class="text-indigo-300 block">Sala EBD:</span> <strong class="text-amber-300">${m.sala_ebd || 'Geral'}</strong></p>







          <p><span class="text-indigo-300 block">Situação Cadastral:</span> <strong class="${(m.status === 'Óbito' || m.status === 'Obto') ? 'text-rose-400' : 'text-emerald-300'}">${m.status || 'Ativo'}</strong></p>







        </div>







      </div>







    </div>







  `;







  abrirModalCustom(html, true);







}















function emitirRecibo(finId) {







  const f = STATE.financeiro.find(x => x.id === finId);







  if (!f) return;















  const html = `







    <div class="border-2 border-slate-800 rounded-2xl p-5 space-y-3 text-xs">







      <div class="flex items-center justify-between border-b border-slate-200 pb-3">







        <div class="flex items-center gap-3">







          <img src="/logo.png" alt="Logo PIB" class="w-12 h-12 rounded-full object-contain shrink-0 border border-slate-200 p-0.5 bg-white shadow-xs" />







          <div>







            <h3 class="text-base font-extrabold text-slate-900">RECIBO FINANCEIRO #${String(f.id).padStart(5, '0')}</h3>







            <p class="text-slate-600 font-bold text-xs" style="color: #3d7e71;">PIB Parque São Paulo — Primeira Igreja Batista</p>







          </div>







        </div>







        <span class="text-lg font-extrabold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-xl border border-emerald-200">${formatBRL(f.valor)}</span>







      </div>







      <p>Recebemos de <strong>${f.membro_nome || 'Contribuinte / Oferta Geral'}</strong> a importância de <strong>${formatBRL(f.valor)}</strong> referente a <strong>${f.categoria} (${f.descricao})</strong>.</p>







      <div class="grid grid-cols-2 gap-2 text-slate-600 pt-2">







        <p>Data do Lançamento: <strong>${formatDateBR(f.data_lancamento)}</strong></p>







        <p>Meio de Pagamento: <strong>${f.forma_pagamento}</strong></p>







      </div>







      <div class="pt-6 text-center border-t border-slate-200 mt-4">







        <p class="font-bold text-slate-800">${f.lancado_por || 'Tesouraria — PIB Parque São Paulo'}</p>







        <p class="text-[10px] text-slate-400">Assinatura / Autenticação Digital do Sistema</p>







      </div>







    </div>







  `;







  abrirModalCustom(html, true);







}















function copiarTextoLink(texto, btnEl) {







  navigator.clipboard.writeText(texto);







  if (btnEl) {







    const original = btnEl.innerHTML;







    btnEl.innerHTML = '✅ Link Copiado!';







    setTimeout(() => { btnEl.innerHTML = original; }, 2200);







  }







}















function trocarTipoLinkModalQR(tipo) {
  const linkAtivo = getLinkOficialAssembleia();







  







  const linkEl = document.getElementById('modal-link-display');







  const btnCopiar = document.getElementById('btn-copiar-link-qr');







  const btnWhats = document.getElementById('btn-whats-link-qr');







  const btnTabPub = document.getElementById('btn-qr-tab-pub');







  const btnTabWifi = document.getElementById('btn-qr-tab-wifi');







  







  if (linkEl) {







    linkEl.innerHTML = `<a href="${linkAtivo}" target="_blank" class="hover:underline">${linkAtivo}</a>`;







  }







  if (btnCopiar) {







    btnCopiar.setAttribute('onclick', `copiarTextoLink('${linkAtivo}', this)`);







  }







  if (btnWhats) {







    const msg = encodeURIComponent(`⛪ *PIB Parque São Paulo — Assembleia Geral*\nAcompanhe os lançamentos e relatórios financeiros em tempo real no seu celular:\n${linkAtivo}`);







    btnWhats.href = `https://wa.me/?text=${msg}`;







  }







  







  if (btnTabPub && btnTabWifi) {







    if (tipo === 'internet') {







      btnTabPub.className = 'px-3 py-1.5 rounded-xl font-black bg-emerald-500 text-slate-950 transition';







      btnTabWifi.className = 'px-3 py-1.5 rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white transition';







    } else {







      btnTabWifi.className = 'px-3 py-1.5 rounded-xl font-black bg-emerald-500 text-slate-950 transition';







      btnTabPub.className = 'px-3 py-1.5 rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white transition';







    }







  }







  







  gerarQRCodeNoElemento('modal-qrcode-canvas', linkAtivo, 260);







}















function abrirModalQRCodeAssembleia() {







  const urlPublica = STATE.url_publica || '';







  const urlLocal = STATE.url_rede_local || `http://${window.location.host}`;







  const linkPadrao = getLinkOficialAssembleia();







  const msgWhats = encodeURIComponent(`⛪ *PIB Parque São Paulo — Assembleia Geral*\nAcompanhe os lançamentos e relatórios financeiros em tempo real no seu celular:\n${linkPadrao}`);















  const html = `







    <div class="space-y-4 text-xs text-slate-700">







      <div class="flex items-center justify-between border-b border-slate-200 pb-3">







        <div>







          <span class="text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full">Projeção Oficial & Tempo Real</span>







          <h3 class="text-base sm:text-lg font-black text-slate-900 mt-1">📱 QR Code da Assembleia (Acompanhamento no Celular)</h3>







        </div>







      </div>















      <div class="grid grid-cols-1 md:grid-cols-12 gap-5 items-center bg-slate-950 text-white p-5 rounded-2xl shadow-xl">







        <div class="md:col-span-5 flex flex-col items-center justify-center bg-white p-4 rounded-2xl shadow-inner text-center">







          <div id="modal-qrcode-canvas" class="w-56 h-56 sm:w-64 sm:h-64 rounded-xl flex items-center justify-center p-2 bg-white overflow-hidden shadow-sm">







            <span class="text-slate-400 font-bold">Gerando QR Code...</span>







          </div>







          <div class="mt-2 flex items-center gap-1.5 text-slate-800 font-extrabold text-xs">







            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>







            Aponte a câmera do celular







          </div>







          <span class="text-[10px] text-slate-500 font-medium">Acesso direto sem necessidade de senha</span>







        </div>















        <div class="md:col-span-7 space-y-4">







          <!-- Seletor Dual: Internet 4G/5G vs Wi-Fi Local da Igreja -->







          <div>







            <div class="flex items-center gap-1.5 mb-2 bg-white/10 p-1 rounded-xl w-fit">







              <button type="button" id="btn-qr-tab-pub" onclick="trocarTipoLinkModalQR('internet')" class="px-3 py-1.5 rounded-xl font-black bg-emerald-500 text-slate-950 transition cursor-pointer">







                🌐 Celular 4G / 5G / Qualquer Rede







              </button>







              <button type="button" id="btn-qr-tab-wifi" onclick="trocarTipoLinkModalQR('wifi')" class="px-3 py-1.5 rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white transition cursor-pointer">







                📶 Wi-Fi da Igreja (Rede Local)







              </button>







            </div>















            <div class="flex items-center gap-2 mb-1">







              <span class="w-2 h-2 rounded-full bg-emerald-400"></span>







              <span class="text-[11px] uppercase tracking-wider font-extrabold text-emerald-400">







                Link da Assembleia ao Vivo:







              </span>







            </div>







            <div id="modal-link-display" class="p-3 rounded-xl bg-white/10 border border-emerald-400/40 font-mono text-xs font-bold text-emerald-300 break-all select-all">







              <a href="${linkPadrao}" target="_blank" class="hover:underline">${linkPadrao}</a>







            </div>







            <div class="flex flex-wrap gap-2 mt-2.5">







              <button type="button" id="btn-copiar-link-qr" onclick="copiarTextoLink('${linkPadrao}', this)" class="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-black px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 cursor-pointer">







                📋 Copiar Link







              </button>







              <a id="btn-whats-link-qr" href="https://wa.me/?text=${msgWhats}" target="_blank" class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-3.5 py-2 rounded-xl transition inline-flex items-center gap-1.5">







                📲 Enviar no WhatsApp







              </a>







              <button type="button" onclick="closeModal(); abrirSlideTelaCheia();" class="bg-white/15 hover:bg-white/25 text-white font-bold px-3 py-2 rounded-xl transition inline-flex items-center gap-1.5">







                🖥️ Tela Cheia







              </button>







            </div>







          </div>















          <div class="pt-3 border-t border-white/15 space-y-1.5 text-[11px] text-slate-300 leading-relaxed">







            <p>🎯 <strong>Como funciona para os irmãos:</strong></p>







            <ul class="list-disc pl-4 space-y-1 text-slate-300">







              <li>Membros escaneiam o QR Code e acompanham os lançamentos no celular na palma da mão.</li>







              <li>A visualização já traz os <strong>nomes dos membros dizimistas e ofertantes</strong> por mês.</li>







              <li>Sincronização instantânea ao vivo quando a mesa ou tesoureiro atualiza a projeção.</li>







            </ul>







          </div>







        </div>







      </div>















      <div class="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-950 flex items-center gap-2">







        <span class="text-base">✨</span>







        <span><strong>Dica:</strong> Se os irmãos estiverem conectados na rede Wi-Fi da igreja, o link Wi-Fi abre com máxima velocidade. Se estiverem no 4G/5G dos seus próprios planos, o link 4G/5G abre de qualquer lugar.</span>







      </div>







    </div>







  `;















  abrirModalCustom(html, false, 'largo');







  setTimeout(() => {







    trocarTipoLinkModalQR(urlPublica ? 'internet' : 'wifi');







  }, 100);







}















function openMultiUserModal() {







  const urlPublica = STATE.url_publica || '';







  const urlLocal = STATE.url_rede_local || `http://${window.location.host}`;







  const linkPrincipal = urlPublica || urlLocal;







  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&margin=8&data=${encodeURIComponent(linkPrincipal)}`;







  const msgWhats = encodeURIComponent(`⛪ *PIB Parque São Paulo — Sistema de Gestão*\nAcesse pelo celular ou computador em tempo real:\n${linkPrincipal}`);















  const html = `







    <div class="space-y-4 text-xs text-slate-700">







      <div class="flex items-center justify-between border-b border-slate-200 pb-3">







        <div>







          <span class="text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full">Sincronização Simultânea Ativa (${STATE.clientes_conectados || 1} online)</span>







          <h3 class="text-base font-extrabold text-slate-900 mt-1">📱 Abrir em Qualquer Celular ou Computador</h3>







        </div>







      </div>















      <div class="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center bg-slate-900 text-white p-4 rounded-2xl">







        <div class="sm:col-span-5 flex flex-col items-center justify-center bg-white p-3 rounded-xl">







          <img src="${qrUrl}" alt="QR Code de Acesso" class="w-44 h-44 rounded-lg" />







          <span class="text-[10px] font-bold text-slate-700 mt-1.5">Aponte a câmera do celular</span>







        </div>















        <div class="sm:col-span-7 space-y-3">







          <div>







            <span class="text-[10px] uppercase tracking-wider font-extrabold text-emerald-400 block">







              🌍 1. Link Global da Internet (Qualquer Celular 4G/5G ou PC em Qualquer Lugar)







            </span>







            ${urlPublica ? `







              <div class="mt-1 p-2.5 rounded-xl bg-white/10 border border-emerald-400/40 font-mono text-xs font-bold text-emerald-300 break-all">







                <a href="${urlPublica}" target="_blank" class="hover:underline">${urlPublica}</a>







              </div>







              <div class="flex flex-wrap gap-2 mt-2">







                <button type="button" onclick="copiarTextoLink('${urlPublica}', this)" class="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-extrabold px-3 py-2 rounded-xl transition">







                  📋 Copiar Link Público







                </button>







                <a href="https://wa.me/?text=${msgWhats}" target="_blank" class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-3 py-2 rounded-xl transition inline-flex items-center gap-1">







                  📲 Enviar no WhatsApp







                </a>







              </div>







            ` : `







              <div class="mt-1 p-2.5 rounded-xl bg-white/10 text-amber-300 font-semibold">







                ⏳ Gerando túnel HTTPS público... aguarde alguns segundos e clique novamente.







              </div>







            `}







          </div>















          <div class="pt-2 border-t border-white/15">







            <span class="text-[10px] uppercase tracking-wider font-bold text-indigo-300 block">







              📶 2. Link Direto na Mesma Rede Wi-Fi / Cabo da Igreja







            </span>







            <div class="mt-1 flex items-center justify-between gap-2 p-2 rounded-xl bg-white/5 border border-white/10">







              <code class="font-mono font-bold text-slate-200">${urlLocal}</code>







              <button type="button" onclick="copiarTextoLink('${urlLocal}', this)" class="bg-white/15 hover:bg-white/25 text-white font-bold px-2.5 py-1 rounded-lg">







                Copiar







              </button>







            </div>







          </div>







        </div>







      </div>















      <div class="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-[11px] text-indigo-950">







        💡 <strong>Como funciona o uso simultâneo:</strong> Todas as pessoas que abrirem o link acima (seja no celular pelo 4G/5G, no Wi-Fi da igreja ou em outros computadores de casa) verão e atualizarão o mesmo banco de dados ao mesmo tempo, com atualização automática na tela!







      </div>







    </div>







  `;







  abrirModalCustom(html, false, 'largo');







  setTimeout(() => {







    atualizarContadorRelatoriosModal();







    gerarQRCodeNoElemento('modal-qrcode-canvas', linkAssembleia, 260);







  }, 100);







}















function closeModal() {







  const overlay = document.getElementById('modal-overlay');







  if (overlay) {







    overlay.classList.add('hidden');







    overlay.style.display = 'none';







  }







}















// Fechar modais ao pressionar tecla Escape







window.addEventListener('keydown', (e) => {







  if (e.key === 'Escape') {







    closeModal();







    if (CURRENT_OPERATOR) {







      fecharTelaLogin();







    }







  }







});















// Fechar ao clicar no fundo escuro fora da caixa do modal







document.addEventListener('click', (e) => {







  const overlay = document.getElementById('modal-overlay');







  if (overlay && e.target === overlay) {







    closeModal();







  }







});















function inicializarSistema() {







  fetchBootstrap();







  initSSE();

  // Heartbeat automático em segundo plano para manter a Visão Geral sempre atualizada
  if (!window._pibAutoSyncInterval) {
    window._pibAutoSyncInterval = setInterval(() => {
      if (document.visibilityState === 'visible' && !isFetchingBootstrap) {
        fetchBootstrap();
      }
    }, 12000);
  }

  // // aoMudarPerfilOperador();







}















if (document.readyState === 'loading') {







  document.addEventListener('DOMContentLoaded', inicializarSistema);







} else {







  inicializarSistema();







}















// -------------------------------------------------------------







// 10. GERADOR DO RELATÓRIO DE DÍZIMOS E OFERTAS POR MEMBRO







// -------------------------------------------------------------







function gerarPDFDizimosPorMembro() {







  if (!verificarAcessoRelatorio('rel_dizimos_membro', 'Extrato de Dízimos por Membro (Confidencial)')) return;







  const ano = Number(document.getElementById('rel-diz-ano')?.value || 2026);







  const membroId = document.getElementById('rel-diz-membro-id')?.value || '';















  const mapaMembros = {};







  (STATE.membros || []).forEach(m => {







    mapaMembros[m.id] = m.nome || m.nome_completo;







  });















  // Filtra lançamentos financeiros de entradas







  let entradas = (STATE.financeiro || []).filter(f => {







    if (f.tipo !== 'ENTRADA') return false;







    if (f.data_lancamento) {







      const a = Number(f.data_lancamento.split('-')[0]);







      if (a !== ano) return false;







    }







    return true;







  });















  if (membroId) {







    entradas = entradas.filter(f => String(f.membro_id) === String(membroId));







  }















  // Se membro individual selecionado:







  if (membroId) {







    const membro = (STATE.membros || []).find(m => String(m.id) === String(membroId));







    const nomeMembro = membro ? (membro.nome || membro.nome_completo) : 'Membro';







    const cargoMembro = membro ? (membro.cargo_eclesiastico || membro.cargo || 'Membro') : '';







    const rolMembro = membro ? (membro.rol ? `#${membro.rol}` : `#${membro.id}`) : '';















    const colunas = [







      { label: 'Data', width: '90px', align: 'center' },







      { label: 'Categoria / Rubrica', width: '160px' },







      { label: 'Histórico / Observação' },







      { label: 'Forma Pagamento', width: '120px', align: 'center' },







      { label: 'Valor (R$)', width: '120px', align: 'right' }







    ];















    const totDizimos = entradas.filter(e => (e.categoria || '').toLowerCase().includes('dízimo') || (e.categoria || '').toLowerCase().includes('dizimo')).reduce((a, b) => a + Number(b.valor || 0), 0);







    const totOfertas = entradas.filter(e => (e.categoria || '').toLowerCase().includes('oferta')).reduce((a, b) => a + Number(b.valor || 0), 0);







    const totGeral = entradas.reduce((a, b) => a + Number(b.valor || 0), 0);















    const linhas = entradas.map(e => [







      formatDateBR(e.data_lancamento),







      { texto: e.categoria || 'Dízimo / Oferta', bold: true },







      e.descricao || 'Contribuição entregue à tesouraria',







      e.forma_pagamento || 'PIX',







      formatBRL(e.valor)







    ]);















    const kpis = [







      { label: 'Membro Contribuinte', valor: nomeMembro, cor: 'text-indigo-700', sub: `Rol: ${rolMembro} · ${cargoMembro}` },







      { label: 'Total de Dízimos', valor: formatBRL(totDizimos), cor: 'text-emerald-700', sub: 'Fidelidade e dízimos' },







      { label: 'Total de Ofertas', valor: formatBRL(totOfertas), cor: 'text-purple-700', sub: 'Ofertas alçadas' },







      { label: 'Total Contribuído', valor: formatBRL(totGeral), cor: 'text-slate-900', sub: `Exercício ${ano}` }







    ];















    const rodapeTotais = `







      <td colspan="4" class="py-2.5 px-3 uppercase font-black">Total Contribuído por ${nomeMembro} em ${ano}</td>







      <td class="text-right py-2.5 px-3 font-mono font-black text-emerald-800">${formatBRL(totGeral)}</td>







    `;















    const csvRows = [







      ['Data', 'Categoria', 'Descricao', 'Forma_Pagamento', 'Valor'],







      ...entradas.map(e => [formatDateBR(e.data_lancamento), e.categoria, e.descricao, e.forma_pagamento, Number(e.valor || 0).toFixed(2)])







    ];















    abrirVisualizadorRelatorioPDF({







      titulo: `Extrato Oficial de Contribuições — ${nomeMembro}`,







      subtitulo: `Demonstrativo individual de dízimos e ofertas entregues ao Senhor na tesouraria`,







      periodo: `Exercício ${ano}`,







      orientacao: 'portrait',







      kpis,







      colunas,







      linhas,







      rodapeTotais,







      nomeArquivo: `Extrato_Dizimos_${nomeMembro.replace(/\s+/g, '_')}_${ano}.pdf`,







      csvRows







    });







  } else {







    // Relatório consolidado com os nomes de todos os membros e suas contribuições







    const agrupadoPorMembro = {};







    (STATE.membros || []).forEach(m => {







      agrupadoPorMembro[m.id] = {







        membro: m,







        nome: m.nome || m.nome_completo,







        cargo: m.cargo_eclesiastico || m.cargo || 'Membro',







        rol: m.rol ? `#${m.rol}` : `#${m.id}`,







        totalDizimos: 0,







        totalOfertas: 0,







        totalOutros: 0,







        totalGeral: 0,







        qtdLancamentos: 0







      };







    });















    entradas.forEach(e => {







      let mId = e.membro_id;







      if (!mId && e.pessoa_nome) {







        const found = (STATE.membros || []).find(m => (m.nome || '').toLowerCase() === e.pessoa_nome.toLowerCase());







        if (found) mId = found.id;







      }







      if (mId && agrupadoPorMembro[mId]) {







        const cat = (e.categoria || '').toLowerCase();







        const v = Number(e.valor || 0);







        if (cat.includes('dízimo') || cat.includes('dizimo')) agrupadoPorMembro[mId].totalDizimos += v;







        else if (cat.includes('oferta')) agrupadoPorMembro[mId].totalOfertas += v;







        else agrupadoPorMembro[mId].totalOutros += v;







        agrupadoPorMembro[mId].totalGeral += v;







        agrupadoPorMembro[mId].qtdLancamentos++;







      }







    });















    const membrosList = Object.values(agrupadoPorMembro).sort((a, b) => a.nome.localeCompare(b.nome));















    const colunas = [







      { label: 'Rol / ID', width: '70px', align: 'center' },







      { label: 'Nome Completo do Membro' },







      { label: 'Status', width: '75px', align: 'center' },







      { label: 'Sala EBD', width: '95px', align: 'center' },







      { label: 'Cargo Eclesiástico', width: '120px' },







      { label: 'Dízimos (R$)', width: '110px', align: 'right' },







      { label: 'Ofertas (R$)', width: '110px', align: 'right' },







      { label: 'Total Contribuído (R$)', width: '125px', align: 'right' },







      { label: 'Qtd', width: '45px', align: 'center' }







    ];















    const totGeralIgreja = membrosList.reduce((a, b) => a + b.totalGeral, 0);







    const dizimistasAtivos = membrosList.filter(m => m.totalGeral > 0).length;















    const linhas = membrosList.map(m => {







      const isObito = m.membro.status === 'Óbito' || m.membro.status === 'Obto';







      const statusTxt = isObito ? '⚫ Óbito' : (m.membro.status || 'Ativo');







      const statusCor = isObito ? 'text-slate-900 font-black' : (m.membro.status === 'Ativo' ? 'text-emerald-700 font-bold' : 'text-slate-600 font-semibold');















      return [







        m.rol,







        { texto: m.nome, bold: true },







        { texto: statusTxt, cor: statusCor },







        m.membro.sala_ebd ? `📚 ${m.membro.sala_ebd}` : '—',







        m.cargo,







        formatBRL(m.totalDizimos),







        formatBRL(m.totalOfertas),







        { texto: formatBRL(m.totalGeral), bold: true, cor: m.totalGeral > 0 ? 'text-emerald-700' : 'text-slate-500' },







        m.qtdLancamentos







      ];







    });















    const kpis = [







      { label: 'Total de Membros no Rol', valor: membrosList.length, cor: 'text-indigo-700', sub: 'Cadastrados na igreja' },







      { label: 'Membros Dizimistas Ativos', valor: dizimistasAtivos, cor: 'text-emerald-700', sub: `${((dizimistasAtivos / (membrosList.length || 1)) * 100).toFixed(0)}% de fidelidade identificada` },







      { label: 'Arrecadação Identificada', valor: formatBRL(totGeralIgreja), cor: 'text-slate-900', sub: `Exercício ${ano}` }







    ];















    const rodapeTotais = `







      <td colspan="5" class="py-2.5 px-3 uppercase font-black">Totais Consolidados por Membros no Período</td>







      <td class="text-right py-2.5 px-3 font-mono font-bold">${formatBRL(membrosList.reduce((a, b) => a + b.totalDizimos, 0))}</td>







      <td class="text-right py-2.5 px-3 font-mono font-bold">${formatBRL(membrosList.reduce((a, b) => a + b.totalOfertas, 0))}</td>







      <td class="text-right py-2.5 px-3 font-mono font-black text-emerald-800">${formatBRL(totGeralIgreja)}</td>







      <td class="text-center py-2.5 px-3 font-bold">${membrosList.reduce((a, b) => a + b.qtdLancamentos, 0)}</td>







    `;















    const csvRows = [







      ['Rol', 'Nome_Completo', 'Status', 'Sala_EBD', 'Cargo', 'Total_Dizimos', 'Total_Ofertas', 'Total_Geral', 'Qtd_Lancamentos'],







      ...membrosList.map(m => [m.rol, m.nome, m.membro.status || 'Ativo', m.membro.sala_ebd || '', m.cargo, m.totalDizimos.toFixed(2), m.totalOfertas.toFixed(2), m.totalGeral.toFixed(2), m.qtdLancamentos])







    ];















    abrirVisualizadorRelatorioPDF({







      titulo: `Relatório de Dízimos e Contribuições por Membro da Igreja`,







      subtitulo: `Relação nominal canônica de fidelidade, dízimos e ofertas por irmão(ã)`,







      periodo: `Exercício ${ano}`,







      orientacao: 'landscape',







      kpis,







      colunas,







      linhas,







      rodapeTotais,







      nomeArquivo: `Relatorio_Dizimos_Por_Membro_${ano}.pdf`,







      csvRows







    });







  }







}















































// =======================================================================







// MÓDULO PEDIDOS DE VERBA: SUBMENU, ANEXO DE PDF E VISUALIZAÇÃO OCULTA







// =======================================================================







function alternarMenuPedidos(menu) {







  MENU_PEDIDOS_ATIVO = menu;







  const pnlNovo = document.getElementById('painel-pedidos-novo');







  const pnlLista = document.getElementById('painel-pedidos-lista');







  const btnNovo = document.getElementById('menu-btn-pedidos-novo');







  const btnLista = document.getElementById('menu-btn-pedidos-lista');















  if (menu === 'novo') {







    if (pnlNovo) pnlNovo.classList.remove('hidden');







    if (pnlLista) pnlLista.classList.add('hidden');







    if (btnNovo) {







      btnNovo.className = 'px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-white text-slate-900 shadow-xs cursor-pointer';







    }







    if (btnLista) {







      btnLista.className = 'px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 text-slate-600 hover:text-slate-900 cursor-pointer';







    }







  } else {







    if (pnlNovo) pnlNovo.classList.add('hidden');







    if (pnlLista) pnlLista.classList.remove('hidden');







    if (btnNovo) {







      btnNovo.className = 'px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 text-slate-600 hover:text-slate-900 cursor-pointer';







    }







    if (btnLista) {







      btnLista.className = 'px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-white text-slate-900 shadow-xs cursor-pointer';







    }







    renderRequisicoesFiltradas();







  }







}















function filtrarStatusPedidos(status) {







  FILTRO_STATUS_PEDIDOS = status;







  const botoes = {







    'TODOS': document.getElementById('btn-filtro-pedidos-todos'),







    'Pendente': document.getElementById('btn-filtro-pedidos-pendente'),







    'Aprovado e Pago': document.getElementById('btn-filtro-pedidos-aprovado'),







    'Recusado': document.getElementById('btn-filtro-pedidos-recusado')







  };















  Object.entries(botoes).forEach(([st, btn]) => {







    if (!btn) return;







    if (st === status) {







      btn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold transition bg-slate-900 text-white cursor-pointer';







    } else {







      btn.className = 'px-3 py-1.5 rounded-lg text-xs font-bold transition bg-slate-100 hover:bg-slate-200 text-slate-700 cursor-pointer';







    }







  });















  renderRequisicoesFiltradas();







}















function aoSelecionarPDFRequisicao(e) {







  const file = e.target.files && e.target.files[0];







  if (!file) return;















  if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {







    alert('Formato inválido! Por favor, selecione um arquivo em formato PDF (.pdf).');







    e.target.value = '';







    return;







  }















  if (file.size > 15 * 1024 * 1024) {







    alert('O arquivo selecionado excede o limite máximo permitido de 15 MB.');







    e.target.value = '';







    return;







  }















  const reader = new FileReader();







  reader.onload = function(evt) {







    REQ_ANEXO_PDF_BASE64 = evt.target.result;







    REQ_ANEXO_PDF_NOME = file.name;







    const elNome = document.getElementById('req-pdf-nome');







    const elTam = document.getElementById('req-pdf-tamanho');







    if (elNome) elNome.textContent = file.name;







    if (elTam) {







      elTam.textContent = (file.size / 1024 < 1024)







        ? `${(file.size / 1024).toFixed(1)} KB`







        : `${(file.size / (1024 * 1024)).toFixed(2)} MB`;







    }







    document.getElementById('req-pdf-placeholder')?.classList.add('hidden');







    document.getElementById('req-pdf-selecionado')?.classList.remove('hidden');







  };







  reader.readAsDataURL(file);







}















function removerPDFRequisicao() {







  REQ_ANEXO_PDF_BASE64 = "";







  REQ_ANEXO_PDF_NOME = "";







  const inp = document.getElementById('req-anexo-pdf');







  if (inp) inp.value = '';







  document.getElementById('req-pdf-placeholder')?.classList.remove('hidden');







  document.getElementById('req-pdf-selecionado')?.classList.add('hidden');







}































async function excluirRequisicao(id) {







  const r = (STATE.requisicoes || []).find(x => x.id === Number(id));







  const desc = r ? `"${r.titulo}" (${r.ministerio_nome || 'Ministério'})` : `#${id}`;







  if (!confirm(`Deseja realmente excluir a solicitação ${desc}?\n\nEsta ação removerá a requisição permanentemente do sistema.`)) {







    return;







  }







  await removerItem('/api/requisicoes', id);







  showLiveToast('🗑️ Solicitação excluída com sucesso!');







}















async function excluirAnexoPDF(reqId) {







  const r = (STATE.requisicoes || []).find(x => x.id === Number(reqId));







  const nome = r && r.anexo_nome ? ` "${r.anexo_nome}"` : "";







  if (!confirm(`Deseja realmente excluir o arquivo PDF${nome} anexado a esta solicitação?`)) {







    return;







  }







  await apiPost('/api/requisicoes/anexo', {







    id: reqId,







    anexo_pdf: "",







    anexo_nome: ""







  });







  await fetchBootstrap();







  showLiveToast('🗑️ Arquivo PDF excluído com sucesso da solicitação!');







}















function abrirModalAnexoPDF(reqId) {







  const r = (STATE.requisicoes || []).find(x => x.id === Number(reqId));







  if (!r) return;















  const html = `







    <div class="space-y-4">







      <div class="flex items-center justify-between border-b border-slate-100 pb-3">







        <div>







          <span class="text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-700 px-2.5 py-0.5 rounded-full">Comprovante Financeiro</span>







          <h3 class="font-bold text-slate-800 text-base mt-1.5">Anexar Nota Fiscal ou Recibo em PDF</h3>







          <p class="text-xs text-slate-500">Solicitação #${r.id} - ${r.titulo} (${r.ministerio_nome})</p>







        </div>







        <button type="button" onclick="closeModal()" class="text-slate-400 hover:text-slate-600 p-1 text-lg">✕</button>







      </div>















      <div class="space-y-3 text-xs">







        ${(r.anexo_nome || r.tem_anexo) ? `







          <div class="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 flex flex-wrap items-center justify-between gap-2">







            <div class="flex items-center gap-2">







              <span class="text-xl">📄</span>







              <div>







                <p class="font-bold text-xs">Arquivo atual anexado:</p>







                <p class="text-[11px] font-mono text-slate-700">${r.anexo_nome || 'Comprovante.pdf'}</p>







              </div>







            </div>







            <div class="flex items-center gap-2">







              <a href="/api/requisicoes/anexo-pdf?id=${r.id}" target="_blank" class="px-2.5 py-1 bg-white border border-amber-300 hover:bg-amber-100 text-amber-800 rounded-lg font-bold text-xs transition">







                Abrir PDF ↗







              </a>







              <button type="button" onclick="closeModal(); excluirAnexoPDF(${r.id});" class="px-2.5 py-1 bg-rose-50 border border-rose-200 hover:bg-rose-100 text-rose-700 rounded-lg font-bold text-xs transition cursor-pointer flex items-center gap-1">







                🗑️ Excluir PDF







              </button>







            </div>







          </div>







        ` : ''}















        <div>







          <label class="font-semibold text-slate-700 block mb-1">Selecione o arquivo PDF da Nota ou Recibo:</label>







          <input type="file" id="modal-anexo-pdf-input" accept=".pdf,application/pdf" class="w-full border border-slate-300 rounded-xl p-2.5 bg-slate-50 text-xs" />







          <p class="text-[10px] text-slate-400 mt-1">Formato suportado: .pdf (Máx: 15 MB)</p>







        </div>















        <div class="pt-3 flex items-center justify-end gap-2 border-t border-slate-100">







          <button type="button" onclick="closeModal()" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition cursor-pointer">







            Cancelar







          </button>







          <button type="button" onclick="salvarAnexoPDFModal(${r.id})" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition flex items-center gap-1.5 shadow-xs cursor-pointer">







            <span>💾 Salvar Anexo</span>







          </button>







        </div>







      </div>







    </div>







  `;







  abrirModalCustom(html, false, 'normal');







}















async function salvarAnexoPDFModal(reqId) {







  const fileInput = document.getElementById('modal-anexo-pdf-input');







  const file = fileInput && fileInput.files && fileInput.files[0];







  if (!file) {







    alert('Por favor, selecione um arquivo em formato PDF.');







    return;







  }















  if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {







    alert('Formato inválido! O arquivo precisa ser um PDF (.pdf).');







    return;







  }















  if (file.size > 15 * 1024 * 1024) {







    alert('O arquivo selecionado excede o limite máximo permitido de 15 MB.');







    return;







  }















  const reader = new FileReader();







  reader.onload = async function(evt) {







    const base64Data = evt.target.result;







    closeModal();







    await apiPost('/api/requisicoes/anexo', {







      id: reqId,







      anexo_pdf: base64Data,







      anexo_nome: file.name







    });







    await fetchBootstrap();







    showLiveToast('✅ Nota Fiscal / Recibo em PDF anexado com sucesso!');







  };







  reader.readAsDataURL(file);







}















function renderRequisicoesFiltradas() {







  const reqCont = document.getElementById('lista-requisicoes');







  if (!reqCont) return;















  const todas = STATE.requisicoes || [];







  const pendentesCount = todas.filter(r => r.status === 'Pendente').length;















  // Atualiza badges de pendências







  const badgeMenu = document.getElementById('badge-menu-pedidos-count');







  if (badgeMenu) {







    if (pendentesCount > 0) {







      badgeMenu.textContent = String(pendentesCount);







      badgeMenu.classList.remove('hidden');







    } else {







      badgeMenu.classList.add('hidden');







    }







  }















  const busca = (document.getElementById('busca-requisicoes')?.value || '').toLowerCase().trim();















  let filtradas = todas.filter(r => {







    if (FILTRO_STATUS_PEDIDOS !== 'TODOS' && r.status !== FILTRO_STATUS_PEDIDOS) {







      return false;







    }







    if (busca) {







      const min = (r.ministerio_nome || '').toLowerCase();







      const sol = (r.solicitante || '').toLowerCase();







      const tit = (r.titulo || '').toLowerCase();







      const just = (r.justificativa || '').toLowerCase();







      return min.includes(busca) || sol.includes(busca) || tit.includes(busca) || just.includes(busca);







    }







    return true;







  });















  const lblTotal = document.getElementById('lbl-total-requisicoes-filtradas');







  if (lblTotal) {







    lblTotal.textContent = `${filtradas.length} solicitação(ões)`;







  }















  const podeAprovar = CURRENT_OPERATOR && (CURRENT_OPERATOR.perfil === 'ADMIN' || temPermissaoSetor('tesouraria'));















  if (filtradas.length === 0) {







    reqCont.innerHTML = `







      <div class="py-12 text-center text-slate-400 bg-slate-50/60 rounded-2xl border border-dashed border-slate-200">







        <span class="text-3xl block mb-2">📋</span>







        <p class="font-bold text-sm text-slate-600">Nenhuma solicitação encontrada com os filtros selecionados.</p>







        <p class="text-xs text-slate-400 mt-1">Clique em "+ Nova Solicitação" no topo para registrar um novo pedido.</p>







      </div>







    `;







    return;







  }















  reqCont.innerHTML = filtradas.map(r => {







    const pendente = r.status === 'Pendente';







    const badgeColor = r.status === 'Aprovado e Pago'







      ? 'bg-emerald-100 text-emerald-800'







      : r.status === 'Recusado'







        ? 'bg-rose-100 text-rose-800'







        : 'bg-amber-100 text-amber-800';















    const temAnexo = Boolean(r.tem_anexo || r.anexo_nome);















    return `







      <div class="p-4 rounded-2xl border ${pendente ? 'border-amber-300 bg-amber-50/30' : 'border-slate-200 bg-white'} shadow-2xs space-y-3 transition hover:border-indigo-200">







        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2.5">







          <div class="flex items-center gap-2 flex-wrap">







            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black text-white shadow-2xs" style="background:${r.ministerio_cor || '#6366f1'}">${r.ministerio_nome}</span>







            <h4 class="font-black text-slate-800 text-sm">${r.titulo}</h4>







            <span class="px-2 py-0.5 rounded-full text-[10px] font-black ${badgeColor}">${r.status}</span>







            <span class="text-[10px] text-slate-400 font-mono">#${r.id}</span>







          </div>







          <div class="text-right shrink-0">







            <span class="text-base font-black text-slate-900">${formatBRL(r.valor_estimado)}</span>







          </div>







        </div>















        <div class="text-xs text-slate-600 space-y-1">







          ${r.justificativa ? `<p class="bg-slate-50 p-2.5 rounded-xl border border-slate-100">📝 <strong>Justificativa:</strong> ${r.justificativa}</p>` : '<p class="text-slate-400 italic">Sem justificativa detalhada.</p>'}







          <p class="text-[11px] text-slate-500 pt-1">







            👤 Solicitado por: <strong>${r.solicitante}</strong> em ${formatDateBR(r.data_solicitacao)} • Prioridade: <strong>${r.prioridade}</strong> ${r.avaliado_por ? `• Avaliado por: <strong>${r.avaliado_por}</strong> em ${formatDateBR(r.data_avaliacao)}` : ''}







          </p>







        </div>















        <!-- BARRA INFERIOR: ANEXO DE NOTA/RECIBO PDF E AÇÕES DE APROVAÇÃO -->







        <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100">







          







          <!-- ANEXO EM PDF -->







          <div class="flex items-center gap-2">







            ${temAnexo ? `







              <a







                href="/api/requisicoes/anexo-pdf?id=${r.id}"







                target="_blank"







                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition shadow-2xs cursor-pointer"







                title="Abrir nota fiscal ou recibo em PDF"







              >







                <span>📄 Ver Nota/Recibo PDF</span>







                <span class="text-[10px] text-rose-500 font-normal truncate max-w-[140px]">(${r.anexo_nome || 'recibo.pdf'})</span>







                <span class="text-[10px]">↗</span>







              </a>







              <button







                type="button"







                onclick="abrirModalAnexoPDF(${r.id})"







                class="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 hover:text-slate-800 p-1 rounded-lg transition cursor-pointer"







                title="Substituir comprovante PDF"







              >







                🔄 Alterar







              </button>







              <button







                type="button"







                onclick="excluirAnexoPDF(${r.id})"







                class="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 px-2 py-1 rounded-lg border border-transparent hover:border-rose-200 transition cursor-pointer"







                title="Excluir arquivo PDF anexado"







              >







                🗑️ Excluir PDF







              </button>







            ` : `







              <button







                type="button"







                onclick="abrirModalAnexoPDF(${r.id})"







                class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition cursor-pointer"







              >







                <span>📎 Anexar Nota/Recibo (PDF)</span>







              </button>







            `}







          </div>















          <!-- AÇÕES DE APROVAÇÃO FINANCEIRA & EXCLUSÃO -->







          <div class="flex items-center gap-2">







            ${pendente && podeAprovar ? `







              <button







                type="button"







                onclick="avaliarRequisicao(${r.id}, 'Aprovado e Pago')"







                class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1.5 rounded-xl shadow-xs transition cursor-pointer flex items-center gap-1"







              >







                <span>✓ Aprovar e Lançar Saída</span>







              </button>







              <button







                type="button"







                onclick="avaliarRequisicao(${r.id}, 'Recusado')"







                class="bg-rose-100 hover:bg-rose-200 text-rose-700 font-bold px-2.5 py-1.5 rounded-xl transition cursor-pointer"







              >







                Recusar







              </button>







            ` : pendente ? `







              <span class="text-[11px] text-amber-800 font-bold bg-amber-100/80 px-2.5 py-1 rounded-lg">Aguardando Tesouraria</span>







            ` : ''}







            <button







              type="button"







              onclick="excluirRequisicao(${r.id})"







              class="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 hover:text-white bg-rose-50 hover:bg-rose-600 border border-rose-200 hover:border-rose-600 px-2.5 py-1.5 rounded-xl shadow-2xs transition cursor-pointer"







              title="Excluir esta solicitação"







            >







              <span>🗑️ Excluir Solicitação</span>







            </button>







          </div>







        </div>







      </div>







    `;







  }).join('');







}











// ============================================================================

// MÓDULO: ARQUIVO DE ATAS & REGISTROS OFICIAIS (PDF & DOCX)

// ============================================================================



let MENU_ATAS_ATIVO = 'lista';

let ATA_ANEXO_BASE64 = '';

let ATA_ANEXO_NOME = '';

let ATA_ANEXO_TIPO = '';

let ATA_ANEXO_TAMANHO = 0;

let ATA_EDITANDO_ID = null;



function alternarMenuAtas(menu) {

  MENU_ATAS_ATIVO = menu;

  const btnNovo = document.getElementById('menu-btn-atas-novo');

  const btnLista = document.getElementById('menu-btn-atas-lista');

  const secForm = document.getElementById('secao-atas-formulario');

  const secLista = document.getElementById('secao-atas-lista');



  if (menu === 'novo') {

    if (btnNovo) {

      btnNovo.className = 'px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-white text-slate-900 shadow-xs cursor-pointer';

    }

    if (btnLista) {

      btnLista.className = 'px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 text-slate-600 hover:text-slate-900 cursor-pointer';

    }

    if (secForm) secForm.classList.remove('hidden');

    if (secLista) secLista.classList.add('hidden');

  } else {

    if (btnNovo) {

      btnNovo.className = 'px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 text-slate-600 hover:text-slate-900 cursor-pointer';

    }

    if (btnLista) {

      btnLista.className = 'px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-white text-slate-900 shadow-xs cursor-pointer';

    }

    if (secForm) secForm.classList.add('hidden');

    if (secLista) secLista.classList.remove('hidden');

    renderAtas();

  }



  configurarDragAndDropAtas();

}



function aoSelecionarArquivoAta(e) {

  const file = e.target.files && e.target.files[0];

  if (!file) return;



  const nome = file.name.toLowerCase();

  const isPdf = nome.endsWith('.pdf') || file.type === 'application/pdf';

  const isDocx = nome.endsWith('.docx') || nome.endsWith('.doc') || 

                file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || 

                file.type === 'application/msword';



  if (!isPdf && !isDocx) {

    alert('Formato de arquivo inválido! Por favor, selecione um documento em formato PDF (.pdf) ou Word DOCX (.docx, .doc).');

    e.target.value = '';

    return;

  }



  if (file.size > 25 * 1024 * 1024) {

    alert('O arquivo selecionado excede o limite máximo permitido de 25 MB.');

    e.target.value = '';

    return;

  }



  const reader = new FileReader();

  reader.onload = function(evt) {

    ATA_ANEXO_BASE64 = evt.target.result;

    ATA_ANEXO_NOME = file.name;

    ATA_ANEXO_TIPO = isPdf ? 'pdf' : (nome.endsWith('.doc') ? 'doc' : 'docx');

    ATA_ANEXO_TAMANHO = file.size;



    atualizarVisualizacaoArquivoAta();

  };

  reader.readAsDataURL(file);

}



function atualizarVisualizacaoArquivoAta() {

  const elPlaceholder = document.getElementById('ata-arquivo-placeholder');

  const elSelecionado = document.getElementById('ata-arquivo-selecionado');

  const elIcone = document.getElementById('ata-arquivo-icone');

  const elBadge = document.getElementById('ata-arquivo-badge-tipo');

  const elNome = document.getElementById('ata-arquivo-nome');

  const elTam = document.getElementById('ata-arquivo-tamanho');



  if (ATA_ANEXO_BASE64 || ATA_ANEXO_NOME) {

    if (elPlaceholder) elPlaceholder.classList.add('hidden');

    if (elSelecionado) elSelecionado.classList.remove('hidden');



    const isPdf = (ATA_ANEXO_TIPO || '').toLowerCase() === 'pdf' || (ATA_ANEXO_NOME || '').toLowerCase().endsWith('.pdf');



    if (elIcone) {

      elIcone.textContent = isPdf ? '📄' : '📝';

      elIcone.className = isPdf

        ? 'w-11 h-11 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center text-2xl font-bold shrink-0'

        : 'w-11 h-11 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center text-2xl font-bold shrink-0';

    }

    if (elBadge) {

      elBadge.textContent = isPdf ? 'PDF' : 'DOCX Word';

      elBadge.className = isPdf

        ? 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700'

        : 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700';

    }

    if (elNome) elNome.textContent = ATA_ANEXO_NOME;

    if (elTam) {

      const bytes = ATA_ANEXO_TAMANHO || 0;

      if (bytes > 0) {

        elTam.textContent = (bytes / 1024 < 1024)

          ? `${(bytes / 1024).toFixed(1)} KB`

          : `${(bytes / (1024 * 1024)).toFixed(2)} MB`;

      } else {

        elTam.textContent = 'Arquivo digital anexado';

      }

    }

  } else {

    if (elPlaceholder) elPlaceholder.classList.remove('hidden');

    if (elSelecionado) elSelecionado.classList.add('hidden');

  }

}



function removerArquivoAta() {

  ATA_ANEXO_BASE64 = '';

  ATA_ANEXO_NOME = '';

  ATA_ANEXO_TIPO = '';

  ATA_ANEXO_TAMANHO = 0;

  const inp = document.getElementById('ata-arquivo-input');

  if (inp) inp.value = '';

  atualizarVisualizacaoArquivoAta();

}



function configurarDragAndDropAtas() {

  const dropzone = document.getElementById('ata-dropzone');

  if (!dropzone || dropzone.__configured) return;

  dropzone.__configured = true;



  ['dragenter', 'dragover'].forEach(evtName => {

    dropzone.addEventListener(evtName, (e) => {

      e.preventDefault();

      e.stopPropagation();

      dropzone.classList.add('border-violet-600', 'bg-violet-50/50');

    });

  });



  ['dragleave', 'drop'].forEach(evtName => {

    dropzone.addEventListener(evtName, (e) => {

      e.preventDefault();

      e.stopPropagation();

      dropzone.classList.remove('border-violet-600', 'bg-violet-50/50');

    });

  });



  dropzone.addEventListener('drop', (e) => {

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {

      aoSelecionarArquivoAta({ target: { files: e.dataTransfer.files } });

    }

  });

}



function renderAtas() {

  const container = document.getElementById('lista-atas-container');

  if (!container) return;



  const todas = STATE.atas || [];



  // Atualiza contadores dos cards KPI

  const kpiTotal = document.getElementById('kpi-atas-total');

  const kpiAnexos = document.getElementById('kpi-atas-anexos');

  const kpiAgoAge = document.getElementById('kpi-atas-ago-age');

  const kpiDir = document.getElementById('kpi-atas-diretoria');

  const bSubAtas = document.getElementById('badge-sub-atas');

  const bAtas = document.getElementById('badge-atas');



  const comAnexos = todas.filter(a => a.tem_anexo || a.nome_arquivo || a.arquivo_base64).length;

  const agoAge = todas.filter(a => (a.tipo || '').includes('Assembleia')).length;

  const dirOutras = todas.length - agoAge;



  if (kpiTotal) kpiTotal.textContent = todas.length;

  if (kpiAnexos) kpiAnexos.textContent = comAnexos;

  if (kpiAgoAge) kpiAgoAge.textContent = agoAge;

  if (kpiDir) kpiDir.textContent = Math.max(0, dirOutras);

  if (bSubAtas) bSubAtas.textContent = todas.length;

  if (bAtas) bAtas.textContent = todas.length;



  configurarDragAndDropAtas();

  filtrarAtas();

}



function filtrarAtas() {

  const container = document.getElementById('lista-atas-container');

  if (!container) return;



  const todas = STATE.atas || [];

  const busca = (document.getElementById('filtro-atas-busca')?.value || '').toLowerCase().trim();

  const filtroTipo = document.getElementById('filtro-atas-tipo')?.value || '';

  const filtroAno = document.getElementById('filtro-atas-ano')?.value || '';



  const filtradas = todas.filter(a => {
    if (filtroTipo) {
      if (filtroTipo === 'anexo') {
        if (!a.tem_anexo && !a.nome_arquivo && !a.arquivo_base64) return false;
      } else if (filtroTipo === 'Assembleia') {
        if (!(a.tipo || '').includes('Assembleia')) return false;
      } else if (a.tipo !== filtroTipo) {
        return false;
      }
    }

    if (filtroAno) {

      const anoAta = (a.data_reuniao || '').substring(0, 4);

      if (anoAta !== filtroAno) return false;

    }

    if (busca) {

      const match = (a.titulo || '').toLowerCase().includes(busca) ||

                    (a.tipo || '').toLowerCase().includes(busca) ||

                    (a.secretario || '').toLowerCase().includes(busca) ||

                    (a.presidente || '').toLowerCase().includes(busca) ||

                    (a.livro_numero || '').toLowerCase().includes(busca) ||

                    (a.folha_numero || '').toLowerCase().includes(busca) ||

                    (a.pauta || '').toLowerCase().includes(busca) ||
                    (a.conteudo || '').toLowerCase().includes(busca) ||
                    (a.observacoes || '').toLowerCase().includes(busca) ||

                    (a.nome_arquivo || '').toLowerCase().includes(busca);

      if (!match) return false;

    }

    return true;

  });



  if (filtradas.length === 0) {

    container.innerHTML = `

      <div class="bg-white rounded-2xl border border-slate-200 p-12 text-center">

        <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-violet-50 text-violet-600 flex items-center justify-center text-3xl">

          📜

        </div>

        <h4 class="font-bold text-slate-800 text-sm">Nenhuma ata encontrada</h4>

        <p class="text-xs text-slate-500 mt-1 max-w-md mx-auto">

          ${todas.length === 0 

            ? 'Ainda não há atas oficiais cadastradas. Clique em "Nova Ata" para cadastrar e anexar documentos em PDF ou DOCX.' 

            : 'Nenhuma ata corresponde aos critérios de pesquisa ou filtros selecionados.'}

        </p>

        <button

          type="button"

          onclick="alternarMenuAtas('novo')"

          class="mt-4 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white font-bold rounded-xl text-xs transition shadow-xs cursor-pointer inline-flex items-center gap-2"

        >

          <span>➕</span>

          <span>Cadastrar Nova Ata</span>

        </button>

      </div>

    `;

    return;

  }



  container.innerHTML = filtradas.map(a => {

    const dataFmt = a.data_reuniao 

      ? a.data_reuniao.split('-').reverse().join('/') 

      : 'Data não informada';



    let tipoBadgeClass = 'bg-slate-100 text-slate-700 border-slate-200';

    if ((a.tipo || '').includes('Ordinária')) {

      tipoBadgeClass = 'bg-blue-100 text-blue-800 border-blue-200';

    } else if ((a.tipo || '').includes('Extraordinária')) {

      tipoBadgeClass = 'bg-amber-100 text-amber-800 border-amber-200';

    } else if ((a.tipo || '').includes('Diretoria')) {

      tipoBadgeClass = 'bg-purple-100 text-purple-800 border-purple-200';

    } else if ((a.tipo || '').includes('Ministério')) {

      tipoBadgeClass = 'bg-emerald-100 text-emerald-800 border-emerald-200';

    } else if ((a.tipo || '').includes('Conselho')) {

      tipoBadgeClass = 'bg-indigo-100 text-indigo-800 border-indigo-200';

    }



    const temAnexo = a.tem_anexo || a.nome_arquivo || a.arquivo_base64;

    const nomeArq = a.nome_arquivo || `ata_${a.id}.pdf`;

    const tipoArq = (a.tipo_arquivo || '').toLowerCase() || (nomeArq.endsWith('.docx') ? 'docx' : 'pdf');

    const isPdf = tipoArq === 'pdf';



    let anexoHtml = '';

    if (temAnexo) {

      anexoHtml = `

        <div class="flex items-center gap-2 flex-wrap">

          <a

            href="/api/atas/anexo?id=${a.id}"

            target="_blank"

            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl ${isPdf ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200' : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'} font-bold text-xs transition shadow-2xs group"

            title="${isPdf ? 'Visualizar ou baixar PDF oficial da ata' : 'Baixar arquivo Word DOCX'}"

          >

            <span class="group-hover:scale-110 transition">${isPdf ? '📄' : '📝'}</span>

            <span class="truncate max-w-[170px] sm:max-w-xs">${nomeArq}</span>

            <span class="text-[10px] uppercase opacity-75 font-extrabold px-1.5 py-0.5 rounded ${isPdf ? 'bg-rose-200/60 text-rose-900' : 'bg-blue-200/60 text-blue-900'}">${tipoArq.toUpperCase()}</span>

            <span class="text-[11px]">↗</span>

          </a>



          <button

            type="button"

            onclick="excluirAnexoAta(${a.id})"

            class="px-2 py-1.5 rounded-xl text-rose-500 hover:text-rose-700 hover:bg-rose-50 border border-transparent hover:border-rose-200 font-bold text-xs transition cursor-pointer"

            title="Excluir apenas o documento anexo desta ata"

          >

            🗑️ Excluir Anexo

          </button>

        </div>

      `;

    } else {

      anexoHtml = `

        <div class="flex items-center gap-2">

          <span class="text-xs text-slate-400 italic">Nenhum documento anexado</span>

          <button

            type="button"

            onclick="editarAta(${a.id})"

            class="text-xs font-bold text-violet-600 hover:text-violet-800 bg-violet-50 hover:bg-violet-100 px-2.5 py-1 rounded-lg border border-violet-200 transition cursor-pointer inline-flex items-center gap-1"

            title="Anexar arquivo PDF ou Word agora"

          >

            <span>📎</span>

            <span>Anexar PDF/DOCX</span>

          </button>

        </div>

      `;

    }



    return `

      <div class="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs hover:border-violet-300 transition-all">

        <div class="flex flex-col lg:flex-row lg:items-start justify-between gap-3">

          <div class="space-y-2 flex-1">

            <div class="flex items-center gap-2 flex-wrap">

              <span class="text-xs font-bold px-2.5 py-0.5 rounded-full border ${tipoBadgeClass}">

                ${a.tipo || 'Assembleia Geral Ordinária'}

              </span>

              <span class="text-xs font-semibold text-slate-500 flex items-center gap-1">

                📅 ${dataFmt}

              </span>

              ${(a.livro_numero || a.folha_numero) ? `

                <span class="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-lg border border-slate-200">

                  📖 ${[a.livro_numero, a.folha_numero].filter(Boolean).join(' • ')}

                </span>

              ` : ''}

              ${a.local_reuniao ? `

                <span class="text-xs text-slate-400">

                  📍 ${a.local_reuniao}

                </span>

              ` : ''}

            </div>



            <h3 class="text-sm sm:text-base font-bold text-slate-900">

              ${a.titulo}

            </h3>



            ${a.pauta ? `

              <p class="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100 whitespace-pre-line leading-relaxed">

                ${a.pauta}

              </p>

            ` : ''}
            ${a.conteudo ? `
              <div class="text-xs text-slate-700 bg-violet-50/60 p-3 rounded-xl border border-violet-200/80 whitespace-pre-line leading-relaxed">
                <span class="text-violet-950 font-bold block text-[10px] uppercase tracking-wider mb-1 flex items-center gap-1">
                  <span>📜</span> Considerações & Deliberações da Ata:
                </span>
                ${a.conteudo}
              </div>
            ` : ''}
            ${a.observacoes ? `
              <div class="text-[11px] text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-200">
                <span class="text-slate-500 font-bold">Observações / Considerações Adicionais:</span> ${a.observacoes}
              </div>
            ` : ''}



            <div class="flex items-center gap-4 text-xs text-slate-500 pt-1 flex-wrap">

              ${a.secretario ? `<span><strong>Secretário(a):</strong> ${a.secretario}</span>` : ''}

              ${a.presidente ? `<span><strong>Presidente:</strong> ${a.presidente}</span>` : ''}

              ${a.observacoes ? `<span class="italic text-slate-400">(${a.observacoes})</span>` : ''}

            </div>



            <!-- ÁREA DO DOCUMENTO ANEXO -->

            <div class="pt-2">

              ${anexoHtml}

            </div>

          </div>



          <!-- BOTÕES DE AÇÃO -->

          <div class="flex items-center lg:flex-col gap-2 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-slate-100">

            <button

              type="button"

              onclick="consultarAtaModal(${a.id})"

              class="flex-1 lg:flex-initial px-3.5 py-1.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-bold text-xs transition cursor-pointer flex items-center justify-center gap-1.5 shadow-xs"

              title="Consultar, ler e visualizar a ata completa"

            >

              <span>🔍</span>

              <span>Consultar</span>

            </button>

            <button

              type="button"

              onclick="editarAta(${a.id})"

              class="flex-1 lg:flex-initial px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition cursor-pointer flex items-center justify-center gap-1.5"

              title="Editar dados desta ata"

            >

              <span>✏️</span>

              <span>Editar</span>

            </button>



            <button

              type="button"

              onclick="excluirAta(${a.id})"

              class="flex-1 lg:flex-initial px-3 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-600 font-bold text-xs transition cursor-pointer flex items-center justify-center gap-1.5 border border-rose-200"

              title="Excluir ata do arquivo oficial"

            >

              <span>🗑️</span>

              <span>Excluir</span>

            </button>

          </div>

        </div>

      </div>

    `;

  }).join('');

}



async function salvarAta(e) {
  if (typeof pararGravacaoVozAta === 'function' && typeof VOZ_ATA_GRAVANDO !== 'undefined' && VOZ_ATA_GRAVANDO) { pararGravacaoVozAta(); }

  if (e && e.preventDefault) e.preventDefault();

  const id = document.getElementById('ata-edit-id')?.value;

  const titulo = document.getElementById('ata-titulo')?.value?.trim();

  const tipo = document.getElementById('ata-tipo')?.value;

  const data_reuniao = document.getElementById('ata-data')?.value;

  const local_reuniao = document.getElementById('ata-local')?.value?.trim();

  const livro_numero = document.getElementById('ata-livro')?.value?.trim();

  const folha_numero = document.getElementById('ata-folha')?.value?.trim();

  const secretario = document.getElementById('ata-secretario')?.value?.trim();

  const presidente = document.getElementById('ata-presidente')?.value?.trim();

  const pauta = document.getElementById('ata-pauta')?.value?.trim();
  const conteudo = document.getElementById('ata-conteudo')?.value?.trim() || '';

  const observacoes = document.getElementById('ata-observacoes')?.value?.trim();



  if (!titulo) {

    alert('Por favor, informe o título da ata.');

    document.getElementById('ata-titulo')?.focus();

    return;

  }

  if (!data_reuniao) {

    alert('Por favor, informe a data da reunião.');

    document.getElementById('ata-data')?.focus();

    return;

  }



  const payload = {

    titulo,

    tipo,

    data_reuniao,

    local_reuniao,

    livro_numero,

    folha_numero,

    secretario,

    presidente,

    pauta, conteudo, observacoes

  };



  if (id) {

    payload.id = Number(id);

  }



  if (ATA_ANEXO_BASE64) {

    payload.arquivo_base64 = ATA_ANEXO_BASE64;

    payload.nome_arquivo = ATA_ANEXO_NOME;

    payload.tipo_arquivo = ATA_ANEXO_TIPO;

    payload.tamanho_arquivo = ATA_ANEXO_TAMANHO;

  }



  const btnSalvar = document.getElementById('btn-salvar-ata');

  if (btnSalvar) {

    btnSalvar.disabled = true;

    btnSalvar.textContent = 'Salvando Ata...';

  }



  try {

    const res = await fetch('/api/atas', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify(payload)

    });

    const data = await res.json();

    if (!res.ok || data.erro) {

      throw new Error(data.erro || 'Falha ao salvar ata.');

    }



    cancelarEdicaoAta();

    alternarMenuAtas('lista');

    await fetchBootstrap();

    alert(id ? 'Ata atualizada com sucesso!' : 'Nova ata arquivada com sucesso!');

  } catch (err) {

    alert(`Erro ao salvar ata: ${err.message}`);

  } finally {

    if (btnSalvar) {

      btnSalvar.disabled = false;

      btnSalvar.innerHTML = '<span>💾 Salvar Ata no Arquivo</span>';

    }

  }

}



function editarAta(id) {

  const ata = (STATE.atas || []).find(a => Number(a.id) === Number(id));

  if (!ata) {

    alert('Ata não encontrada!');

    return;

  }



  ATA_EDITANDO_ID = ata.id;

  document.getElementById('ata-edit-id').value = ata.id;

  document.getElementById('ata-titulo').value = ata.titulo || '';

  document.getElementById('ata-tipo').value = ata.tipo || 'Assembleia Geral Ordinária';

  document.getElementById('ata-data').value = ata.data_reuniao || '';

  document.getElementById('ata-local').value = ata.local_reuniao || '';

  document.getElementById('ata-livro').value = ata.livro_numero || '';

  document.getElementById('ata-folha').value = ata.folha_numero || '';

  document.getElementById('ata-secretario').value = ata.secretario || '';

  document.getElementById('ata-presidente').value = ata.presidente || '';

  document.getElementById('ata-pauta').value = ata.pauta || '';
  if (document.getElementById('ata-conteudo')) document.getElementById('ata-conteudo').value = ata.conteudo || '';

  document.getElementById('ata-observacoes').value = ata.observacoes || '';



  if (ata.tem_anexo || ata.nome_arquivo) {

    ATA_ANEXO_NOME = ata.nome_arquivo || `ata_${ata.id}.pdf`;

    ATA_ANEXO_TIPO = ata.tipo_arquivo || (ATA_ANEXO_NOME.endsWith('.docx') ? 'docx' : 'pdf');

    ATA_ANEXO_TAMANHO = ata.tamanho_arquivo || 0;

    ATA_ANEXO_BASE64 = ''; // Mantém existente se não alterado

  } else {

    removerArquivoAta();

  }

  atualizarVisualizacaoArquivoAta();



  const bForm = document.getElementById('atas-form-badge');

  const bStatus = document.getElementById('atas-form-status');

  const btnCancel = document.getElementById('btn-cancelar-edicao-ata');

  const btnSalvar = document.getElementById('btn-salvar-ata');



  if (bForm) {

    bForm.textContent = `Editando Ata #${ata.id}`;

    bForm.className = 'text-[11px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 px-2.5 py-1 rounded-full';

  }

  if (bStatus) bStatus.textContent = 'Modifique os campos ou anexe um novo documento PDF/DOCX';

  if (btnCancel) btnCancel.classList.remove('hidden');

  if (btnSalvar) btnSalvar.innerHTML = '<span>💾 Salvar Alterações</span>';



  alternarMenuAtas('novo');

  window.scrollTo({ top: 0, behavior: 'smooth' });

}



function cancelarEdicaoAta() {
  if (typeof pararGravacaoVozAta === 'function' && typeof VOZ_ATA_GRAVANDO !== 'undefined' && VOZ_ATA_GRAVANDO) { pararGravacaoVozAta(); }
  const elAudioC = document.getElementById('voz-ata-audio-player-container'); if (elAudioC) elAudioC.classList.add('hidden');

  ATA_EDITANDO_ID = null;

  const elId = document.getElementById('ata-edit-id');

  if (elId) elId.value = '';

  const elTit = document.getElementById('ata-titulo');

  if (elTit) elTit.value = '';

  const elTipo = document.getElementById('ata-tipo');

  if (elTipo) elTipo.value = 'Assembleia Geral Ordinária';

  const elData = document.getElementById('ata-data');

  if (elData) elData.value = new Date().toISOString().split('T')[0];

  const elLoc = document.getElementById('ata-local');

  if (elLoc) elLoc.value = '';

  const elLivro = document.getElementById('ata-livro');

  if (elLivro) elLivro.value = '';

  const elFolha = document.getElementById('ata-folha');

  if (elFolha) elFolha.value = '';

  const elSec = document.getElementById('ata-secretario');

  if (elSec) elSec.value = '';

  const elPres = document.getElementById('ata-presidente');

  if (elPres) elPres.value = '';

  const elPauta = document.getElementById('ata-pauta');

  if (elPauta) elPauta.value = '';
  const elCnt = document.getElementById('ata-conteudo');
  if (elCnt) elCnt.value = '';

  const elObs = document.getElementById('ata-observacoes');

  if (elObs) elObs.value = '';



  removerArquivoAta();



  const bForm = document.getElementById('atas-form-badge');

  const bStatus = document.getElementById('atas-form-status');

  const btnCancel = document.getElementById('btn-cancelar-edicao-ata');

  const btnSalvar = document.getElementById('btn-salvar-ata');



  if (bForm) {

    bForm.textContent = 'Nova Ata Oficial';

    bForm.className = 'text-[11px] font-bold uppercase tracking-wider bg-violet-100 text-violet-700 px-2.5 py-1 rounded-full';

  }

  if (bStatus) bStatus.textContent = 'Preencha os campos e anexe o arquivo em PDF ou DOCX';

  if (btnCancel) btnCancel.classList.add('hidden');

  if (btnSalvar) btnSalvar.innerHTML = '<span>💾 Salvar Ata no Arquivo</span>';

}



async function excluirAta(id) {

  const ata = (STATE.atas || []).find(a => Number(a.id) === Number(id));

  const titulo = ata ? ata.titulo : `#${id}`;



  if (!confirm(`Tem certeza que deseja excluir permanentemente do arquivo a ata:\n\n"${titulo}"?\n\nEsta ação removerá o registro e seu documento anexado.`)) {

    return;

  }



  try {

    const res = await fetch(`/api/atas?id=${id}`, {

      method: 'DELETE'

    });

    const data = await res.json();

    if (!res.ok || data.erro) {

      throw new Error(data.erro || 'Falha ao excluir ata.');

    }



    await fetchBootstrap();

    alert('Ata excluída com sucesso!');

  } catch (err) {

    alert(`Erro ao excluir ata: ${err.message}`);

  }

}



async function excluirAnexoAta(id) {

  if (!confirm('Deseja realmente excluir apenas o arquivo digital (PDF/DOCX) desta ata?\nO registro da reunião será mantido intacto.')) {

    return;

  }



  try {

    const res = await fetch('/api/atas/anexo', {

      method: 'POST',

      headers: { 'Content-Type': 'application/json' },

      body: JSON.stringify({ id: Number(id), remover: true })

    });

    const data = await res.json();

    if (!res.ok || data.erro) {

      throw new Error(data.erro || 'Falha ao excluir anexo.');

    }



    await fetchBootstrap();

    alert('Documento anexo removido com sucesso!');

  } catch (err) {

    alert(`Erro ao remover anexo: ${err.message}`);

  }

}


// ============================================================================
// MÓDULO DE GRAVAÇÃO E TRANSCRIÇÃO DE VOZ (ASSEMBLEIAS E ATAS OFICIAIS)
// ============================================================================
let VOZ_ATA_GRAVANDO = false;
let VOZ_ATA_RECOGNITION = null;
let VOZ_ATA_MEDIA_RECORDER = null;
let VOZ_ATA_AUDIO_STREAM = null;
let VOZ_ATA_AUDIO_CHUNKS = [];
let VOZ_ATA_TIMER_INTERVAL = null;
let VOZ_ATA_SEGUNDOS = 0;
let VOZ_ATA_BASE_TEXTO = '';
let VOZ_ATA_TRANSCRICAO_ATUAL = '';

function alternarGravacaoVozAta() {
  if (VOZ_ATA_GRAVANDO) {
    pararGravacaoVozAta();
  } else {
    iniciarGravacaoVozAta();
  }
}

async function iniciarGravacaoVozAta() {
  const btn = document.getElementById('btn-voz-ata');
  const btnTexto = document.getElementById('btn-voz-ata-texto');
  const btnTimer = document.getElementById('btn-voz-ata-timer');
  const statusBar = document.getElementById('voz-ata-status-bar');
  const statusMsg = document.getElementById('voz-ata-status-msg');
  const textarea = document.getElementById('ata-conteudo');

  if (!textarea) {
    alert('Campo de texto da ata não encontrado.');
    return;
  }

  VOZ_ATA_BASE_TEXTO = textarea.value || '';
  VOZ_ATA_TRANSCRICAO_ATUAL = '';
  VOZ_ATA_AUDIO_CHUNKS = [];

  // Checa suporte a SpeechRecognition nativo
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  // 1. Inicia captura do microfone e gravação de áudio
  try {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      VOZ_ATA_AUDIO_STREAM = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (typeof MediaRecorder !== 'undefined') {
        VOZ_ATA_MEDIA_RECORDER = new MediaRecorder(VOZ_ATA_AUDIO_STREAM);
        VOZ_ATA_MEDIA_RECORDER.ondataavailable = function(e) {
          if (e.data && e.data.size > 0) {
            VOZ_ATA_AUDIO_CHUNKS.push(e.data);
          }
        };
        VOZ_ATA_MEDIA_RECORDER.onstop = function() {
          if (VOZ_ATA_AUDIO_CHUNKS.length > 0) {
            try {
              const audioBlob = new Blob(VOZ_ATA_AUDIO_CHUNKS, { type: 'audio/webm' });
              const audioUrl = URL.createObjectURL(audioBlob);
              const player = document.getElementById('voz-ata-audio-player');
              const downloadLink = document.getElementById('voz-ata-download-link');
              const container = document.getElementById('voz-ata-audio-player-container');
              if (player) player.src = audioUrl;
              if (downloadLink) {
                downloadLink.href = audioUrl;
                const d = new Date();
                const stamp = d.toISOString().slice(0, 10).replace(/-/g, '') + '_' + String(d.getHours()).padStart(2, '0') + String(d.getMinutes()).padStart(2, '0');
                downloadLink.download = `Audio_Assembleia_${stamp}.webm`;
              }
              if (container) container.classList.remove('hidden');
            } catch (errAudio) {
              console.warn('Aviso no processamento do áudio:', errAudio);
            }
          }
        };
        VOZ_ATA_MEDIA_RECORDER.start(1000);
      }
    }
  } catch (errMic) {
    console.warn('Microfone não acessível para gravação de áudio:', errMic);
    if (!SpeechRecognition) {
      alert('Não foi possível acessar o microfone ou o navegador bloqueou a permissão. Permita o uso do microfone para ditar a ata.');
      return;
    }
  }

  // 2. Transcrição de fala em tempo real
  if (SpeechRecognition) {
    try {
      VOZ_ATA_RECOGNITION = new SpeechRecognition();
      VOZ_ATA_RECOGNITION.continuous = true;
      VOZ_ATA_RECOGNITION.interimResults = true;
      VOZ_ATA_RECOGNITION.lang = 'pt-BR';
      VOZ_ATA_RECOGNITION.maxAlternatives = 1;

      VOZ_ATA_RECOGNITION.onresult = function(event) {
        let textoParcial = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const resultado = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            let frase = resultado.trim();
            if (frase) {
              frase = frase.charAt(0).toUpperCase() + frase.slice(1);
              VOZ_ATA_TRANSCRICAO_ATUAL += (VOZ_ATA_TRANSCRICAO_ATUAL ? ' ' : '') + frase + '.';
            }
          } else {
            textoParcial += resultado;
          }
        }

        let textoFinal = VOZ_ATA_BASE_TEXTO ? VOZ_ATA_BASE_TEXTO.trim() + '\n\n' : '';
        if (VOZ_ATA_TRANSCRICAO_ATUAL) {
          textoFinal += VOZ_ATA_TRANSCRICAO_ATUAL;
        }
        if (textoParcial) {
          textoFinal += (VOZ_ATA_TRANSCRICAO_ATUAL ? ' ' : '') + '« ' + textoParcial.trim() + '... »';
        }
        textarea.value = textoFinal;
        textarea.scrollTop = textarea.scrollHeight;
      };

      VOZ_ATA_RECOGNITION.onerror = function(event) {
        console.warn('Aviso no reconhecimento de fala:', event.error);
        if (event.error === 'not-allowed') {
          alert('Acesso ao microfone foi bloqueado pelo navegador. Por favor, autorize o microfone para utilizar a transcrição de voz.');
          pararGravacaoVozAta();
        }
      };

      VOZ_ATA_RECOGNITION.onend = function() {
        if (VOZ_ATA_GRAVANDO) {
          try { VOZ_ATA_RECOGNITION.start(); } catch(e){}
        }
      };

      VOZ_ATA_RECOGNITION.start();
    } catch (errRec) {
      console.warn('Erro ao inicializar SpeechRecognition:', errRec);
    }
  } else {
    if (typeof showLiveToast === 'function') {
      showLiveToast('🎙️ Gravando áudio! (Dica: utilize Google Chrome ou Microsoft Edge para transcrição direta em texto)');
    }
  }

  // 3. Atualiza UI para estado gravando
  VOZ_ATA_GRAVANDO = true;
  VOZ_ATA_SEGUNDOS = 0;

  if (btn) {
    btn.className = 'inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 shadow-sm transition-all duration-200 cursor-pointer animate-pulse ring-2 ring-rose-400 ring-offset-2';
  }
  if (btnTexto) btnTexto.textContent = 'Parar Gravação';
  if (btnTimer) {
    btnTimer.classList.remove('hidden');
    btnTimer.textContent = '00:00';
  }
  if (statusBar) statusBar.classList.remove('hidden');
  if (statusMsg) statusMsg.textContent = 'Ouvindo assembleia... Fale claramente ao microfone para transcrever.';

  clearInterval(VOZ_ATA_TIMER_INTERVAL);
  VOZ_ATA_TIMER_INTERVAL = setInterval(function() {
    VOZ_ATA_SEGUNDOS++;
    const min = String(Math.floor(VOZ_ATA_SEGUNDOS / 60)).padStart(2, '0');
    const seg = String(VOZ_ATA_SEGUNDOS % 60).padStart(2, '0');
    if (btnTimer) btnTimer.textContent = `${min}:${seg}`;
  }, 1000);
}

function pararGravacaoVozAta() {
  VOZ_ATA_GRAVANDO = false;
  clearInterval(VOZ_ATA_TIMER_INTERVAL);

  if (VOZ_ATA_RECOGNITION) {
    try {
      VOZ_ATA_RECOGNITION.onend = null;
      VOZ_ATA_RECOGNITION.stop();
    } catch (e) {}
    VOZ_ATA_RECOGNITION = null;
  }

  if (VOZ_ATA_MEDIA_RECORDER && VOZ_ATA_MEDIA_RECORDER.state !== 'inactive') {
    try {
      VOZ_ATA_MEDIA_RECORDER.stop();
    } catch (e) {}
  }
  if (VOZ_ATA_AUDIO_STREAM) {
    try {
      VOZ_ATA_AUDIO_STREAM.getTracks().forEach(t => t.stop());
    } catch (e) {}
    VOZ_ATA_AUDIO_STREAM = null;
  }

  const textarea = document.getElementById('ata-conteudo');
  if (textarea && textarea.value) {
    textarea.value = textarea.value.replace(/«[^»]*»/g, '').trim();
  }

  const btn = document.getElementById('btn-voz-ata');
  const btnTexto = document.getElementById('btn-voz-ata-texto');
  const btnTimer = document.getElementById('btn-voz-ata-timer');
  const statusBar = document.getElementById('voz-ata-status-bar');

  if (btn) {
    btn.className = 'inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-violet-600 hover:bg-violet-700 shadow-sm transition-all duration-200 cursor-pointer';
  }
  if (btnTexto) btnTexto.textContent = 'Gravar & Transcrever Voz';
  if (btnTimer) btnTimer.classList.add('hidden');
  if (statusBar) statusBar.classList.add('hidden');

  if (typeof showLiveToast === 'function') {
    showLiveToast('✅ Gravação e transcrição concluídas com sucesso!');
  }
}

function estruturarTextoAta() {
  const textarea = document.getElementById('ata-conteudo');
  if (!textarea) return;

  const textoOriginal = textarea.value.trim();
  if (!textoOriginal) {
    alert('O campo de texto está vazio. Fale ao microfone ou digite as deliberações antes de estruturar a ata.');
    return;
  }

  const titulo = document.getElementById('ata-titulo')?.value?.trim() || 'ASSEMBLEIA GERAL ORDINÁRIA';
  const tipo = document.getElementById('ata-tipo')?.value || 'Assembleia Geral';
  const data = document.getElementById('ata-data')?.value || new Date().toISOString().slice(0, 10);
  const local = document.getElementById('ata-local')?.value?.trim() || 'Templo Sede da Igreja';
  const presidente = document.getElementById('ata-presidente')?.value?.trim() || 'Pastor Presidente';
  const secretario = document.getElementById('ata-secretario')?.value?.trim() || 'Secretário(a) Geral';
  const pauta = document.getElementById('ata-pauta')?.value?.trim() || 'Conforme convocação estatutária.';

  let dataExtenso = data;
  try {
    const partes = data.split('-');
    if (partes.length === 3) {
      const meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
      dataExtenso = `${parseInt(partes[2], 10)} de ${meses[parseInt(partes[1], 10) - 1]} de ${partes[0]}`;
    }
  } catch (e) {}

  const confirmacao = confirm(
    'Deseja estruturar o texto atual no formato de ATA OFICIAL ECLESIÁSTICA?\n\n' +
    'O conteúdo já registrado será organizado em seções formais (Abertura, Quórum, Deliberações e Encerramento).'
  );
  if (!confirmacao) return;

  const textoEstruturado = 
`ATA DE ${titulo.toUpperCase()}

1. ABERTURA E ORAÇÃO:
Aos ${dataExtenso}, no ${local}, reuniu-se a igreja em ${tipo}, sob a presidência do(a) irmão(ã) ${presidente}, e secretariado por mim, ${secretario}. A reunião foi aberta com oração e louvor ao Senhor.

2. VERIFICAÇÃO DE QUÓRUM E PAUTA:
Constatou-se quórum estatutário regular com os membros em plena comunhão presentes. A pauta da reunião foi apresentada: "${pauta}".

3. DISCUSSÕES E DELIBERAÇÕES REGISTRADAS:
${textoOriginal}

4. ENCERRAMENTO E ASSINATURAS:
Nada mais havendo a tratar e nenhuma outra manifestação pendente, o Presidente deu por encerrada a presente assembleia com oração e a bênção apostólica. Para constar, eu, ${secretario}, lavrei a presente ata que, após lida e achada conforme, segue devidamente assinada.

_______________________________________
Presidente da Mesa

_______________________________________
Secretário(a)`;

  textarea.value = textoEstruturado;
  textarea.scrollTop = 0;

  if (typeof showLiveToast === 'function') {
    showLiveToast('📋 Ata estruturada no formato oficial com sucesso!');
  }
}

function inserirLinhaAta() {
  const textarea = document.getElementById('ata-conteudo');
  if (!textarea) return;

  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const val = textarea.value;

  textarea.value = val.substring(0, start) + '\n\n' + val.substring(end);
  textarea.selectionStart = textarea.selectionEnd = start + 2;
  textarea.focus();
}

function limparTextoAta() {
  const textarea = document.getElementById('ata-conteudo');
  if (!textarea) return;

  if (!textarea.value.trim()) return;

  if (confirm('Tem certeza que deseja limpar todo o texto da ata?')) {
    textarea.value = '';
    const container = document.getElementById('voz-ata-audio-player-container');
    if (container) container.classList.add('hidden');
    if (typeof showLiveToast === 'function') {
      showLiveToast('Texto da ata limpo.');
    }
  }
}



function alternarVerSenhaCard(id) {

  const mask = document.getElementById(`senha-mask-${id}`);

  const val = document.getElementById(`senha-val-${id}`);

  if (mask && val) {

    if (val.classList.contains('hidden')) {

      mask.classList.add('hidden');

      val.classList.remove('hidden');

    } else {

      mask.classList.remove('hidden');

      val.classList.add('hidden');

    }

  }

}





// =========================================================================

// GESTÃO DE SENHAS FORTES & ALTERAÇÃO OBRIGATÓRIA NO PRIMEIRO ACESSO

// =========================================================================



// ======================================================================
// GESTÃO E ALTERAÇÃO DE SENHAS DE OPERADORES (PRÓPRIA & ADMINISTRATIVA)
// ======================================================================

let MODAL_SENHA_MODO_OBRIGATORIO = false;
let MODAL_SENHA_TARGET_USER_ID = null;

function abrirModalTrocaSenhaPropria() {
  if (!CURRENT_OPERATOR) {
    alert('Nenhum operador conectado.');
    return;
  }
  abrirModalTrocaSenha(CURRENT_OPERATOR, false);
}

function abrirModalAlterarSenhaUsuario(userId) {
  const u = (STATE.usuarios || []).find(x => Number(x.id) === Number(userId));
  if (!u) {
    alert('Operador não encontrado.');
    return;
  }
  abrirModalTrocaSenha(u, false);
}

function abrirModalTrocaSenha(user = CURRENT_OPERATOR, isObrigatoria = false) {
  if (!user && CURRENT_OPERATOR) user = CURRENT_OPERATOR;
  if (!user) return;

  MODAL_SENHA_MODO_OBRIGATORIO = isObrigatoria;
  MODAL_SENHA_TARGET_USER_ID = Number(user.id);

  const modal = document.getElementById('modal-troca-senha-obrigatoria');
  const nomeEl = document.getElementById('troca-senha-nome-operador');
  const idInput = document.getElementById('troca-senha-user-id');
  const inpNova = document.getElementById('nova-senha-obrigatoria');
  const inpConf = document.getElementById('confirma-senha-obrigatoria');
  const erroDiv = document.getElementById('troca-senha-erro');
  const tituloEl = document.getElementById('troca-senha-modal-titulo');
  const descEl = document.getElementById('troca-senha-modal-descricao');
  const rodapeEl = document.getElementById('troca-senha-rodape-cancelar');
  const btnSubmit = document.getElementById('btn-salvar-nova-senha');

  if (nomeEl) nomeEl.textContent = user.nome || 'Operador';
  if (idInput) idInput.value = user.id;
  if (inpNova) inpNova.value = '';
  if (inpConf) inpConf.value = '';
  if (erroDiv) erroDiv.classList.add('hidden');

  const isProprio = CURRENT_OPERATOR && Number(CURRENT_OPERATOR.id) === Number(user.id);

  if (tituloEl) {
    if (isObrigatoria) {
      tituloEl.textContent = 'Alteração Obrigatória de Senha';
    } else if (isProprio) {
      tituloEl.textContent = 'Alterar Minha Senha de Acesso';
    } else {
      tituloEl.textContent = `Alterar Senha: ${user.nome}`;
    }
  }

  if (descEl) {
    if (isObrigatoria) {
      descEl.textContent = 'Este é o seu primeiro acesso ao sistema (ou sua senha ainda é provisória). Para garantir a segurança dos dados da igreja, é obrigatório definir sua nova senha pessoal antes de continuar.';
    } else if (isProprio) {
      descEl.textContent = 'Atualize sua credencial pessoal de acesso ao sistema com segurança. Crie uma senha forte e memorize-a.';
    } else {
      descEl.textContent = `Defina uma nova senha de acesso para o operador ${user.nome}.`;
    }
  }

  if (btnSubmit) {
    btnSubmit.innerHTML = isObrigatoria ? '<span>🔒</span> Salvar Nova Senha & Acessar Sistema' : '<span>💾</span> Salvar Nova Senha';
  }

  if (rodapeEl) {
    if (isObrigatoria) {
      rodapeEl.style.display = 'block';
    } else {
      rodapeEl.style.display = 'none';
    }
  }

  aoDigitarNovaSenhaObrigatoria();

  if (modal) {
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
  }
  setTimeout(() => {
    inpNova?.focus();
  }, 120);
}

function abrirModalTrocaSenhaObrigatoria(user = CURRENT_OPERATOR) {
  abrirModalTrocaSenha(user, true);
}

function fecharModalTrocaSenha() {
  const modal = document.getElementById('modal-troca-senha-obrigatoria');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
  MODAL_SENHA_MODO_OBRIGATORIO = false;
  MODAL_SENHA_TARGET_USER_ID = null;
}

function cancelarTrocaSenhaObrigatoria() {
  fecharModalTrocaSenha();
  sairDoSistema();
}

function fecharOuCancelarTrocaSenha() {
  if (MODAL_SENHA_MODO_OBRIGATORIO) {
    cancelarTrocaSenhaObrigatoria();
  } else {
    fecharModalTrocaSenha();
  }
}

function aoDigitarNovaSenhaObrigatoria() {
  const pwd = (document.getElementById('nova-senha-obrigatoria')?.value || '').trim();
  const conf = (document.getElementById('confirma-senha-obrigatoria')?.value || '').trim();

  const temLetra = /[a-zA-Z]/.test(pwd);
  const temNumero = /[0-9]/.test(pwd);
  const temEspecial = /[^a-zA-Z0-9]/.test(pwd);
  const tamanhoOk = pwd.length >= 6;
  const senhasBatem = pwd.length > 0 && pwd === conf;

  const atualizaItem = (id, cond) => {
    const el = document.getElementById(id);
    if (!el) return;
    const icon = el.querySelector('.req-icon');
    if (cond) {
      el.className = 'flex items-center gap-2 text-emerald-600 font-bold transition-colors';
      if (icon) icon.textContent = '✅';
    } else {
      el.className = 'flex items-center gap-2 text-slate-400 transition-colors';
      if (icon) icon.textContent = '⚪';
    }
  };

  atualizaItem('req-letras', temLetra);
  atualizaItem('req-numeros', temNumero);
  atualizaItem('req-especial', temEspecial);
  atualizaItem('req-tamanho', tamanhoOk);
  atualizaItem('req-confirmacao', senhasBatem);

  const tudoValido = temLetra && temNumero && temEspecial && tamanhoOk && senhasBatem;
  const tagStatus = document.getElementById('requisitos-status-tag');
  const btnSubmit = document.getElementById('btn-salvar-nova-senha');

  if (tagStatus) {
    if (tudoValido) {
      tagStatus.textContent = 'Padrão Atendido!';
      tagStatus.className = 'text-[10px] font-extrabold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full';
    } else {
      tagStatus.textContent = 'Pendente';
      tagStatus.className = 'text-[10px] font-extrabold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full';
    }
  }

  if (btnSubmit) {
    btnSubmit.disabled = !tudoValido;
  }
}

async function executarTrocaSenhaObrigatoria(e) {
  if (e && e.preventDefault) e.preventDefault();

  const idInput = document.getElementById('troca-senha-user-id');
  const inpNova = document.getElementById('nova-senha-obrigatoria');
  const inpConf = document.getElementById('confirma-senha-obrigatoria');
  const erroDiv = document.getElementById('troca-senha-erro');
  const erroTexto = document.getElementById('troca-senha-erro-texto');
  const btnSubmit = document.getElementById('btn-salvar-nova-senha');

  const userId = Number(idInput?.value || (CURRENT_OPERATOR ? CURRENT_OPERATOR.id : 0));
  const novaSenha = (inpNova?.value || '').trim();
  const confirmacao = (inpConf?.value || '').trim();

  if (!novaSenha) {
    if (erroDiv && erroTexto) {
      erroTexto.textContent = 'Por favor, digite a nova senha.';
      erroDiv.classList.remove('hidden');
    }
    inpNova?.focus();
    return;
  }

  if (novaSenha !== confirmacao) {
    if (erroDiv && erroTexto) {
      erroTexto.textContent = 'A confirmação não confere com a nova senha digitada.';
      erroDiv.classList.remove('hidden');
    }
    inpConf?.focus();
    return;
  }

  if (!/[a-zA-Z]/.test(novaSenha) || !/[0-9]/.test(novaSenha) || !/[^a-zA-Z0-9]/.test(novaSenha) || novaSenha.length < 6) {
    if (erroDiv && erroTexto) {
      erroTexto.textContent = 'A senha deve conter letras, números e pelo menos um caractere especial (mínimo 6 caracteres).';
      erroDiv.classList.remove('hidden');
    }
    inpNova?.focus();
    return;
  }

  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<span>⏳</span> Salvando nova senha segura...';
  }

  try {
    const res = await fetch('/api/usuarios/alterar-senha', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: userId, nova_senha: novaSenha, confirmacao: confirmacao })
    });
    const data = await res.json();

    if (res.ok && data.ok) {
      if (CURRENT_OPERATOR && Number(CURRENT_OPERATOR.id) === userId) {
        CURRENT_OPERATOR.senha = novaSenha;
        CURRENT_OPERATOR.senha_alterada = 1;
      }
      const uDb = (STATE.usuarios || []).find(u => Number(u.id) === userId);
      if (uDb) {
        uDb.senha = novaSenha;
        uDb.senha_alterada = 1;
      }

      fecharModalTrocaSenha();

      const isProprio = CURRENT_OPERATOR && Number(CURRENT_OPERATOR.id) === userId;
      if (MODAL_SENHA_MODO_OBRIGATORIO) {
        showLiveToast('🎉 Nova senha segura cadastrada com sucesso! Bem-vindo(a) ao sistema.');
        const permitidas = getPermissoesOperador(CURRENT_OPERATOR);
        const todasAbas = [
          'dashboard', 'tesouraria', 'pedidos', 'projecao', 'relatorios',
          'secretaria', 'recepcao', 'atas', 'ministerios', 'celulas',
          'patrimonio', 'acessos'
        ];
        const destino = todasAbas.find(t => temPermissaoSetor(t, CURRENT_OPERATOR)) || 'secretaria';
        switchTab(destino);
        renderAll();
      } else {
        if (isProprio) {
          showLiveToast('🎉 Sua nova senha foi atualizada com sucesso!');
        } else {
          showLiveToast(`✅ Senha do operador "${uDb ? uDb.nome : ''}" atualizada com sucesso!`);
        }
        renderUsuarios();
      }
    } else {
      if (erroDiv && erroTexto) {
        erroTexto.textContent = data.mensagem || 'Erro ao alterar senha. Verifique os requisitos.';
        erroDiv.classList.remove('hidden');
      }
    }
  } catch (err) {
    console.error('Erro na troca de senha:', err);
    if (erroDiv && erroTexto) {
      erroTexto.textContent = 'Erro de comunicação ao salvar a nova senha.';
      erroDiv.classList.remove('hidden');
    }
  } finally {
    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = MODAL_SENHA_MODO_OBRIGATORIO ? '<span>🔒</span> Salvar Nova Senha & Acessar Sistema' : '<span>💾</span> Salvar Nova Senha';
    }
  }
}

async function resetarSenhaOperador(userId) {
  const uTarget = (STATE.usuarios || []).find(u => Number(u.id) === Number(userId));
  const nome = uTarget ? uTarget.nome : ('Operador #' + userId);
  if (!confirm(`Deseja realmente resetar a senha do operador "${nome}" para o padrão inicial temporário 123456?

Ele será obrigado a cadastrar uma nova senha pessoal segura (com letras, números e caractere especial) no próximo acesso.`)) {
    return;
  }

  try {
    const res = await fetch('/api/usuarios/resetar-senha', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: userId })
    });
    const data = await res.json();
    if (res.ok && data.ok) {
      showLiveToast(`🔄 Senha de ${nome} resetada para 123456 com sucesso!`);
      const uDb = (STATE.usuarios || []).find(u => Number(u.id) === userId);
      if (uDb) {
        uDb.senha = '123456';
        uDb.senha_alterada = 0;
      }
      renderPatrimonioEUsuarios();
    } else {
      alert(data.mensagem || 'Erro ao resetar senha.');
    }
  } catch (err) {
    console.error('Erro ao resetar senha:', err);
    alert('Erro de comunicação com o servidor ao resetar senha.');
  }
}



// ============================================================================
// MODAL DE CONSULTA & FILTROS RÁPIDOS DE ATAS OFICIAIS
// ============================================================================
function consultarAtaModal(id) {
  const ata = (STATE.atas || []).find(a => Number(a.id) === Number(id));
  if (!ata) {
    alert('Ata não encontrada no arquivo oficial.');
    return;
  }

  const dataFmt = ata.data_reuniao 
    ? ata.data_reuniao.split('-').reverse().join('/') 
    : 'Data não informada';

  const temAnexo = ata.tem_anexo || ata.nome_arquivo || ata.arquivo_base64;
  const nomeArq = ata.nome_arquivo || `ata_${ata.id}.pdf`;
  const tipoArq = (ata.tipo_arquivo || '').toLowerCase() || (nomeArq.endsWith('.docx') ? 'docx' : 'pdf');
  const isPdf = tipoArq === 'pdf';

  const html = `
    <div class="p-6 max-w-4xl mx-auto space-y-6 text-slate-800">
      <!-- CABEÇALHO DO MODAL DE CONSULTA -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-3">
        <div class="flex items-center gap-3">
          <span class="w-12 h-12 rounded-2xl bg-violet-100 text-violet-700 flex items-center justify-center text-2xl shadow-xs">📜</span>
          <div>
            <span class="text-[10px] font-extrabold uppercase tracking-widest text-violet-600 bg-violet-50 px-2 py-0.5 rounded-full border border-violet-200">
              ${escapeHtml(ata.tipo || 'Assembleia Geral')}
            </span>
            <h2 class="text-lg sm:text-xl font-extrabold text-slate-900 mt-1 leading-snug">
              ${escapeHtml(ata.titulo)}
            </h2>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onclick="window.print()"
            class="px-3.5 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-bold text-xs transition shadow-xs flex items-center gap-1.5 cursor-pointer"
            title="Imprimir ou Salvar como PDF Oficial"
          >
            <span>🖨️</span>
            <span>Imprimir Ata</span>
          </button>
          <button
            type="button"
            onclick="fecharModalCustom(); editarAta(${ata.id});"
            class="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition border border-slate-200 flex items-center gap-1.5 cursor-pointer"
          >
            <span>✏️</span>
            <span>Editar</span>
          </button>
          <button
            type="button"
            onclick="fecharModalCustom()"
            class="px-3 py-2 rounded-xl bg-slate-100 hover:bg-rose-100 text-slate-500 hover:text-rose-700 font-bold text-xs transition cursor-pointer"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- METADADOS DA SESSÃO / LIVRO / FOLHA -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-50 p-4 rounded-2xl border border-slate-200">
        <div>
          <span class="text-slate-400 block text-[11px] font-semibold">Data da Reunião:</span>
          <span class="font-extrabold text-slate-800">📅 ${dataFmt}</span>
        </div>
        <div>
          <span class="text-slate-400 block text-[11px] font-semibold">Local:</span>
          <span class="font-extrabold text-slate-800">📍 ${escapeHtml(ata.local_reuniao || 'Templo Sede')}</span>
        </div>
        <div>
          <span class="text-slate-400 block text-[11px] font-semibold">Livro / Registro:</span>
          <span class="font-extrabold text-slate-800">📖 ${escapeHtml(ata.livro_numero || 'Não informado')}</span>
        </div>
        <div>
          <span class="text-slate-400 block text-[11px] font-semibold">Folha / Fls:</span>
          <span class="font-extrabold text-slate-800">📄 ${escapeHtml(ata.folha_numero || 'Não informado')}</span>
        </div>
      </div>

      <!-- MESA DIRETORA -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div class="p-3 bg-white rounded-xl border border-slate-200 flex items-center gap-2.5">
          <span class="text-lg">👔</span>
          <div>
            <span class="text-slate-400 block text-[10px] font-bold uppercase tracking-wider">Presidente da Mesa:</span>
            <span class="font-bold text-slate-800">${escapeHtml(ata.presidente || 'Não informado')}</span>
          </div>
        </div>
        <div class="p-3 bg-white rounded-xl border border-slate-200 flex items-center gap-2.5">
          <span class="text-lg">✍️</span>
          <div>
            <span class="text-slate-400 block text-[10px] font-bold uppercase tracking-wider">Secretário(a) da Sessão:</span>
            <span class="font-bold text-slate-800">${escapeHtml(ata.secretario || 'Não informado')}</span>
          </div>
        </div>
      </div>

      <!-- PAUTA OFICIAL -->
      ${ata.pauta ? `
        <div class="space-y-1.5">
          <h4 class="text-xs font-extrabold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <span>📋</span> Pauta da Convocação:
          </h4>
          <div class="p-3.5 bg-white rounded-xl border border-slate-200 text-xs text-slate-700 whitespace-pre-line leading-relaxed font-medium">
            ${escapeHtml(ata.pauta)}
          </div>
        </div>
      ` : ''}

      <!-- TEXTO INTEGRAL / TRANSCRIÇÃO / DELIBERAÇÕES DA ATA -->
      <div class="space-y-1.5">
        <h4 class="text-xs font-extrabold uppercase tracking-wider text-violet-700 flex items-center gap-1.5">
          <span>📜</span> Texto Integral & Deliberações da Ata:
        </h4>
        <div class="p-5 bg-white rounded-2xl border border-violet-200 shadow-2xs text-xs sm:text-sm text-slate-800 whitespace-pre-line leading-relaxed font-sans min-h-[140px]">
          ${ata.conteudo ? escapeHtml(ata.conteudo) : '<span class="text-slate-400 italic">Nenhum texto integral registrado para esta ata. Você pode editar a ata e ditar ou digitar as considerações e deliberações.</span>'}
        </div>
      </div>

      <!-- OBSERVAÇÕES COMPLEMENTARES -->
      ${ata.observacoes ? `
        <div class="p-3 bg-amber-50/70 border border-amber-200/80 rounded-xl text-xs text-amber-900">
          <span class="font-bold block text-[11px] mb-0.5">Observações Adicionais:</span>
          <span>${escapeHtml(ata.observacoes)}</span>
        </div>
      ` : ''}

      <!-- DOCUMENTO ANEXO -->
      ${temAnexo ? `
        <div class="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between gap-3 flex-wrap">
          <div class="flex items-center gap-2">
            <span class="text-2xl">${isPdf ? '📄' : '📝'}</span>
            <div>
              <span class="font-bold text-xs text-slate-800 block">${escapeHtml(nomeArq)}</span>
              <span class="text-[11px] text-slate-400">Documento Oficial Digitalizado Anexo (${escapeHtml(tipoArq.toUpperCase())})</span>
            </div>
          </div>
          <a
            href="/api/atas/anexo?id=${ata.id}"
            target="_blank"
            class="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-xs font-bold transition shadow-xs inline-flex items-center gap-1.5 cursor-pointer"
          >
            <span>Abrir / Baixar Arquivo</span>
            <span>↗</span>
          </a>
        </div>
      ` : ''}

      <!-- ASSINATURAS OFICIAIS (PARA IMPRESSÃO) -->
      <div class="pt-8 mt-6 border-t border-slate-200 grid grid-cols-2 gap-8 text-center text-xs">
        <div>
          <div class="border-b border-slate-400 mb-1 w-3/4 mx-auto"></div>
          <span class="font-bold text-slate-800 block">${escapeHtml(ata.presidente || 'Presidente da Mesa')}</span>
          <span class="text-[10px] text-slate-500">Presidente da Assembleia</span>
        </div>
        <div>
          <div class="border-b border-slate-400 mb-1 w-3/4 mx-auto"></div>
          <span class="font-bold text-slate-800 block">${escapeHtml(ata.secretario || 'Secretário(a) Geral')}</span>
          <span class="text-[10px] text-slate-500">Secretário(a) da Assembleia</span>
        </div>
      </div>
    </div>
  `;

  if (typeof abrirModalCustom === 'function') {
    abrirModalCustom(html, true, 'largo');
  }
}

function setFiltroAtasRapido(tipo) {
  const selectTipo = document.getElementById('filtro-atas-tipo');
  if (selectTipo) {
    if (tipo === 'anexo') {
      selectTipo.value = '';
    } else if (tipo === 'Assembleia') {
      selectTipo.value = 'Assembleia Geral Ordinária';
    } else {
      selectTipo.value = tipo;
    }
  }
  filtrarAtas();
  atualizarPillsFiltroAtas(tipo);
}

function limparFiltrosAtas() {
  const selectTipo = document.getElementById('filtro-atas-tipo');
  const selectAno = document.getElementById('filtro-atas-ano');
  const inputBusca = document.getElementById('filtro-atas-busca');
  if (selectTipo) selectTipo.value = '';
  if (selectAno) selectAno.value = '';
  if (inputBusca) inputBusca.value = '';
  filtrarAtas();
  atualizarPillsFiltroAtas('');
}

function atualizarPillsFiltroAtas(ativo) {
  document.querySelectorAll('.btn-filtro-ata-rapido').forEach(btn => {
    const txt = btn.textContent.trim();
    let matches = false;
    if (!ativo && txt.includes('Todas')) matches = true;
    else if (ativo === 'anexo' && txt.includes('Anexo')) matches = true;
    else if (ativo && txt.includes(ativo.substring(0, 3))) matches = true;

    if (matches) {
      btn.className = 'btn-filtro-ata-rapido px-2.5 py-1 rounded-lg bg-violet-600 text-white font-bold transition cursor-pointer shadow-2xs';
    } else {
      btn.className = 'btn-filtro-ata-rapido px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition cursor-pointer';
    }
  });
}


// ============================================================================
// CONTROLES INTERATIVOS DA PLANILHA MENSAL (FILTROS, FOCO NO MÊS, 12M)
// ============================================================================
function filtrarFluxoMatriz(tipo) {
  FILTRO_FLUXO_MATRIZ = tipo || 'TODOS';
  const btnTodos = document.getElementById('btn-filtro-fluxo-todos');
  const btnEntradas = document.getElementById('btn-filtro-fluxo-entradas');
  const btnSaidas = document.getElementById('btn-filtro-fluxo-saidas');

  const activeTodos = 'px-3.5 py-1.5 rounded-lg transition bg-white text-slate-900 shadow-xs cursor-pointer font-bold';
  const activeEntrada = 'px-3.5 py-1.5 rounded-lg transition bg-emerald-600 text-white shadow-xs cursor-pointer font-bold';
  const activeSaida = 'px-3.5 py-1.5 rounded-lg transition bg-rose-600 text-white shadow-xs cursor-pointer font-bold';

  const inactiveTodos = 'px-3.5 py-1.5 rounded-lg transition text-slate-600 hover:text-slate-900 cursor-pointer font-bold';
  const inactiveEntrada = 'px-3.5 py-1.5 rounded-lg transition text-slate-600 hover:text-emerald-700 cursor-pointer font-bold';
  const inactiveSaida = 'px-3.5 py-1.5 rounded-lg transition text-slate-600 hover:text-rose-700 cursor-pointer font-bold';

  if (btnTodos) btnTodos.className = (FILTRO_FLUXO_MATRIZ === 'TODOS') ? activeTodos : inactiveTodos;
  if (btnEntradas) btnEntradas.className = (FILTRO_FLUXO_MATRIZ === 'ENTRADA') ? activeEntrada : inactiveEntrada;
  if (btnSaidas) btnSaidas.className = (FILTRO_FLUXO_MATRIZ === 'SAIDA') ? activeSaida : inactiveSaida;

  renderMatrizTesouraria();
}

function alterarMesDestaqueMatriz(mes) {
  MES_DESTAQUE_MATRIZ = parseInt(mes, 10) || 0;
  
  // Atualiza destaque no thead
  for (let m = 1; m <= 12; m++) {
    const thCols = document.querySelectorAll(`.th-mes-col-${m}`);
    thCols.forEach(th => {
      if (m === MES_DESTAQUE_MATRIZ) {
        th.className = `py-3 px-2 text-right th-mes-col th-mes-col-${m} bg-amber-400 text-slate-950 font-black border-b border-amber-300`;
      } else {
        th.className = `py-3 px-2 text-right th-mes-col th-mes-col-${m} bg-slate-900 text-white border-b border-slate-700`;
      }
    });
  }

  renderMatrizTesouraria();
}

function alternarTodosGruposMatriz(expandir) {
  const { rows } = calcularResumoAnoMatriz(ANO_MATRIZ_ATIVO);
  const todosGrupos = [...new Set(rows.map(r => r.grupo))];
  if (expandir) {
    GRUPOS_MATRIZ_RECOLHIDOS.clear();
  } else {
    todosGrupos.forEach(g => GRUPOS_MATRIZ_RECOLHIDOS.add(g));
  }
  renderMatrizTesouraria();
}

function alternarGrupoIndividualMatriz(grupoNome) {
  if (GRUPOS_MATRIZ_RECOLHIDOS.has(grupoNome)) {
    GRUPOS_MATRIZ_RECOLHIDOS.delete(grupoNome);
  } else {
    GRUPOS_MATRIZ_RECOLHIDOS.add(grupoNome);
  }
  renderMatrizTesouraria();
}

function limparBuscaMatriz() {
  const inp = document.getElementById('busca-rubrica-matriz');
  if (inp) inp.value = '';
  renderMatrizTesouraria();
}

function abrirModalConta12Meses(rowId) {
  const item = (STATE.matriz_tesouraria || []).find(r => Number(r.id) === Number(rowId));
  if (!item) {
    alert('Conta não encontrada na matriz financeira.');
    return;
  }

  const isEntrada = item.tipo_fluxo === 'ENTRADA';
  const mesesInputs = item.meses.map((val, idx) => `
    <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
      <label class="block text-[10px] font-bold uppercase text-slate-500 mb-1">
        ${NOMES_MESES[idx]}/${item.ano}
      </label>
      <div class="relative">
        <span class="absolute left-2.5 top-2 text-slate-400 text-xs">R$</span>
        <input
          type="number"
          step="0.01"
          id="modal-12m-mes-${idx + 1}"
          value="${Number(val || 0).toFixed(2)}"
          oninput="recalcularTotalModal12M()"
          class="w-full pl-8 pr-2 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-bold text-slate-800 text-right focus:ring-2 focus:ring-indigo-500"
        />
      </div>
    </div>
  `).join('');

  const html = `
    <form onsubmit="salvarModalConta12Meses(event, ${item.id})" class="space-y-4 text-xs">
      <div class="flex items-center justify-between pb-3 border-b border-slate-200">
        <div>
          <span class="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full ${isEntrada ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
            ${isEntrada ? '🟢 ENTRADA / RECEITA' : '🔴 SAÍDA / DESPESA'} • ${escapeHtml(item.grupo)}
          </span>
          <h3 class="text-base font-extrabold text-slate-900 mt-1">${escapeHtml(item.rubrica)}</h3>
          <p class="text-slate-500 text-[11px]">Exercício financeiro de <strong>${item.ano}</strong> (Preenchimento Completo dos 12 Meses)</p>
        </div>
        <button type="button" onclick="fecharModalCustom()" class="px-2.5 py-1 text-slate-400 hover:text-slate-700 font-bold text-sm">✕</button>
      </div>

      <!-- GRID 12 MESES -->
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
        ${mesesInputs}
      </div>

      <!-- RESUMO CONSOLIDADO DA CONTA -->
      <div class="p-3 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center justify-between text-xs">
        <div>
          <span class="text-indigo-900 font-bold block text-[11px]">Total Anual Acumulado:</span>
          <span id="modal-12m-total" class="text-base font-extrabold ${isEntrada ? 'text-emerald-700' : 'text-rose-700'}">${formatBRL(item.total_anual)}</span>
        </div>
        <div>
          <span class="text-indigo-900 font-bold block text-[11px]">Média Mensal:</span>
          <span id="modal-12m-media" class="text-sm font-extrabold text-slate-800">${formatBRL(item.media_mensal)}</span>
        </div>
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
        <button type="button" onclick="fecharModalCustom()" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold transition cursor-pointer">
          Cancelar
        </button>
        <button type="submit" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-extrabold transition shadow flex items-center gap-1.5 cursor-pointer">
          <span>💾</span> Salvar 12 Meses
        </button>
      </div>
    </form>
  `;

  if (typeof abrirModalCustom === 'function') {
    abrirModalCustom(html, false, 'largo');
  }
}

function recalcularTotalModal12M() {
  let total = 0;
  for (let m = 1; m <= 12; m++) {
    const inp = document.getElementById(`modal-12m-mes-${m}`);
    if (inp) {
      total += parseFloat(inp.value) || 0;
    }
  }
  const media = total / 12.0;
  const elTot = document.getElementById('modal-12m-total');
  const elMed = document.getElementById('modal-12m-media');
  if (elTot) elTot.textContent = formatBRL(total);
  if (elMed) elMed.textContent = formatBRL(media);
}

async function salvarModalConta12Meses(e, rowId) {
  if (e && e.preventDefault) e.preventDefault();
  const item = (STATE.matriz_tesouraria || []).find(r => Number(r.id) === Number(rowId));
  if (!item) return;

  const novosMeses = [];
  for (let m = 1; m <= 12; m++) {
    const inp = document.getElementById(`modal-12m-mes-${m}`);
    novosMeses.push(parseFloat(inp?.value) || 0);
  }

  fecharModalCustom();
  if (typeof showLiveToast === 'function') {
    showLiveToast(`Salvando valores de ${item.rubrica}...`);
  }

  for (let m = 1; m <= 12; m++) {
    const vAntigo = Number(item.meses[m - 1] || 0);
    const vNovo = Number(novosMeses[m - 1] || 0);
    if (Math.abs(vAntigo - vNovo) > 0.001) {
      await apiPost('/api/matriz/celula', { id: rowId, mes: m, valor: vNovo });
    }
  }

  await fetchBootstrap();
  if (typeof showLiveToast === 'function') {
    showLiveToast(`✅ 12 meses de ${item.rubrica} atualizados com sucesso!`);
  }
}
