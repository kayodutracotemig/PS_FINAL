# Guia de apresentação — Stadium Guide

Este guia explica a organização do projeto e o papel de cada arquivo relevante. A ideia principal é ajudar o torcedor do Atlético-MG ou do Cruzeiro a se preparar para ir ao estádio: acompanhar os jogos, consultar uma previsão de ocupação, planejar a rota e encontrar informações úteis do estádio.

## 1. Como explicar o projeto em poucas palavras

> O Stadium Guide é uma aplicação web para torcedores do Atlético-MG e do Cruzeiro. A interface é feita com HTML, CSS e JavaScript. O servidor usa Python com Flask para autenticar usuários, aplicar as regras do sistema e consultar ou atualizar os dados guardados em um banco SQLite. O projeto também integra serviços externos para consultar jogos, calcular rotas e abrir a navegação no Google Maps.

## 2. Como as partes se conectam

```text
Navegador
  index.html + estilo.css + app.js
          │ requisições HTTP com JSON
          ▼
Flask — backend/app.py
  Controllers: recebem e validam a requisição
          ▼
  Services: executam as regras de negócio
          ▼
  Models: consultam e gravam dados com SQLAlchemy
          ▼
  SQLite — usuários, times, jogos, favoritos e avaliações
```

O Flask também entrega os arquivos do frontend. Assim, página e API usam a mesma origem. O navegador não acessa o banco diretamente: ele conversa com o servidor, e o servidor faz as consultas.

### Exemplo: entrar no app

1. A pessoa preenche e-mail e senha na página.
2. `frontend/js/app.js` envia os dados para `POST /usuarios/login`.
3. `backend/controllers/usuario_controller.py` recebe a requisição e chama `LoginService`.
4. O serviço localiza o usuário, confere o hash da senha e cria um token de sessão.
5. O controller devolve o token como JSON.
6. O frontend guarda o token no `localStorage` e o envia nas próximas requisições pelo cabeçalho `Authorization`.

## 3. Estrutura de pastas

| Pasta | Para que serve |
|---|---|
| `backend/` | Servidor Flask, regras, modelos do banco e scripts de administração dos jogos. |
| `backend/controllers/` | Rotas HTTP. Traduzem requisições e respostas entre o navegador e os serviços. |
| `backend/models/` | Estrutura das tabelas e operações de consulta ao banco. |
| `backend/services/` | Regras de negócio e integrações externas. |
| `backend/repositories/` | Pasta reservada para uma camada de consultas; atualmente contém apenas `.gitkeep`. As consultas são feitas diretamente pelos models/serviços. |
| `backend/static/fotos/` | Destino das fotos de perfil enviadas pelos usuários. O repositório mantém a pasta com `.gitkeep`, mas ignora as fotos. |
| `backend/instance/` | Dados locais do Flask, incluindo o banco SQLite criado durante a execução. |
| `frontend/` | Interface que o usuário vê no navegador. |
| `frontend/css/` | Aparência, temas e adaptação para telas diferentes. |
| `frontend/js/` | Interações da interface e chamadas à API. |
| `frontend/img/` | Fotos dos estádios, mapas ilustrados dos setores e ícone da aba do navegador. |

## 4. Arquivos da raiz do projeto

| Arquivo | O que faz |
|---|---|
| `README.md` | Apresenta o projeto, como instalar e executar, como sincronizar jogos e a lista de funcionalidades. É a documentação principal para quem vai instalar. |
| `funcionalidades.md` | Lista as funcionalidades. Em boa parte, repete o resumo do README; confira ambos se o projeto mudar. |
| `CORRECOES.md` | Registra correções feitas anteriormente e explica alguns problemas encontrados durante a recuperação do projeto. É um histórico técnico, não é executado pelo app. |
| `.gitignore` | Diz ao Git quais arquivos locais não devem entrar no controle de versão, como ambientes virtuais, `.env`, banco local e fotos enviadas. |
| `.git/` | Metadados e histórico de versões do Git. Não faz parte do funcionamento do site e normalmente não é editada manualmente. |
| `frontend/.gitkeep` | Arquivo vazio para o Git manter a pasta `frontend` quando ela ainda não tem conteúdo no checkout original. Não é usado pelo app. |
| `GUIA_APRESENTACAO.md` | Este documento. Explica a estrutura e oferece um roteiro de apresentação. |

## 5. Backend: arquivos principais

| Arquivo | O que faz |
|---|---|
| `backend/app.py` | Cria a aplicação Flask, carrega as configurações, conecta o SQLAlchemy, registra os controllers e serve o frontend. Ao iniciar, cria tabelas que ainda não existem, acrescenta a coluna `fase` em bancos antigos e cadastra Atlético MG e Cruzeiro caso a tabela de times esteja vazia. |
| `backend/config.py` | Carrega variáveis do arquivo `.env` e define banco, chave de sessão e limite de upload. O padrão local é SQLite. |
| `backend/requirements.txt` | Lista as bibliotecas Python necessárias, como Flask, Flask-SQLAlchemy, python-dotenv e requests. |
| `backend/sincronizar_jogos.py` | Consulta a API football-data.org para obter jogos do Brasileirão Série A, identifica partidas do Atlético e do Cruzeiro, converte horário para o fuso de São Paulo e grava/atualiza os jogos no banco. Usa o ID da partida externa para evitar duplicações. |
| `backend/registrar_jogo.py` | Script de terminal para cadastrar jogos de Copa do Brasil e Sul-Americana que não são importados pelo sincronizador. Pergunta os dados da partida e registra o jogo no banco. |
| `backend/.env.example` | Modelo das configurações locais. Deve ser copiado para `.env` e preenchido no computador de quem executa o projeto. |
| `backend/.env` | Arquivo local com configurações e tokens privados. Não é código e não deve ser incluído em apresentação pública, zip ou GitHub. O guia não reproduz seu conteúdo. |
| `backend/instance/stadium.db` | Banco SQLite local criado pelo app. Guarda registros da aplicação; não é código-fonte. O conteúdo pode variar em cada instalação. |
| `backend/repositories/.gitkeep` | Mantém no Git a pasta de repositórios, atualmente sem implementação. |
| `backend/static/fotos/.gitkeep` | Mantém criada a pasta onde o serviço de perfil salva fotos enviadas. O arquivo em si é vazio. |

## 6. Controllers: rotas da API

Um controller recebe a requisição HTTP, lê JSON ou formulário, verifica os campos básicos, chama um serviço e devolve o resultado em JSON com um código HTTP.

| Arquivo | Rotas e responsabilidade |
|---|---|
| `backend/controllers/usuario_controller.py` | Cadastro (`POST /usuarios/cadastro`), login (`POST /usuarios/login`) e logout (`POST /usuarios/logout`). |
| `backend/controllers/time_controller.py` | Lista times (`GET /times`), salva a primeira escolha (`POST /times/selecionar`) e troca o time do perfil (`PUT /times/mudar`). |
| `backend/controllers/perfil_controller.py` | Consulta o perfil (`GET /perfil`), salva endereço (`PUT /perfil/localizacao`) e recebe foto (`PUT /perfil/foto`). |
| `backend/controllers/ingresso_controller.py` | Abre o link de ingressos do time (`GET /ingressos/comprar`) e fornece jogos próximos e passados (`GET /jogos/proximos`, `GET /jogos/passados`). |
| `backend/controllers/favorito_controller.py` | Alterna o estado de favorito de um jogo (`POST /jogos/<id>/favoritar`) e lista favoritos (`GET /favoritos`). |
| `backend/controllers/avaliacao_controller.py` | Registra nota/comentário de jogo passado (`POST /jogos/<id>/avaliar`) e lista avaliações (`GET /avaliacoes`). |
| `backend/controllers/rota_controller.py` | Recebe o modo escolhido (`POST /rota`), identifica o usuário pelo token, lê o endereço salvo no perfil e solicita ao serviço um link para o estádio do time. |
| `backend/controllers/ocupacao_controller.py` | Recebe os dados do jogo (`POST /ocupacao/previsao`), identifica o estádio pelo time do usuário e devolve ocupação prevista, setores e recomendação. |

## 7. Models: dados guardados no banco

Os models descrevem as tabelas usadas pelo SQLAlchemy. Eles também oferecem operações simples para salvar, localizar e listar registros.

| Arquivo | Tabela / dados |
|---|---|
| `backend/models/usuario_model.py` | Tabela `usuarios`: nome, e-mail, hash da senha, token da sessão, time escolhido, foto e endereço. Também inicializa o objeto `db` compartilhado pelos models. |
| `backend/models/time_model.py` | Tabela `times`, com os times disponíveis. |
| `backend/models/jogo_model.py` | Tabela `jogos`: time relacionado, adversário, data/hora, mando, estádio, competição, fase e identificador da API externa. Tem consultas para jogos futuros e passados. |
| `backend/models/favorito_model.py` | Tabela `favoritos`, que relaciona usuário e jogo marcado como favorito. |
| `backend/models/avaliacao_model.py` | Tabela `avaliacoes`: usuário, jogo, nota, comentário e data da avaliação. |
| `backend/models/estadio_coordenadas.py` | Dicionário de referência com nome, endereço e coordenadas da Arena MRV e do Mineirão. Não é uma tabela do banco. |

## 8. Services: regras e integrações

Os services concentram o que o sistema precisa fazer. Por exemplo, o controller de login cuida da comunicação HTTP, enquanto `LoginService` verifica credenciais e cria o token.

| Arquivo | Regra ou integração |
|---|---|
| `services/cadastrar_usuario_service.py` | Verifica se o e-mail já existe, transforma a senha em hash e cria o usuário. |
| `services/login_service.py` | Verifica e-mail e senha usando o hash armazenado; cria um token aleatório para a sessão. |
| `services/logout_service.py` | Localiza a sessão pelo token e o remove do usuário. |
| `services/buscar_perfil_service.py` | Valida o token e devolve o usuário e, se houver, o time escolhido. |
| `services/selecionar_time_service.py` | Associa o usuário a um time na primeira seleção. |
| `services/mudar_time_service.py` | Valida e troca o time associado ao perfil. |
| `services/atualizar_foto_service.py` | Valida sessão e extensão da imagem, salva o arquivo com nome único em `backend/static/fotos/` e grava o endereço da foto no perfil. |
| `services/atualizar_localizacao_service.py` | Valida e salva rua, número, bairro, cidade e estado do usuário. |
| `services/proximos_jogos_service.py` | Busca os jogos futuros do time do usuário e converte cada jogo para um objeto JSON simples. |
| `services/listar_jogos_passados_service.py` | Lista jogos anteriores do usuário e informa se ele já avaliou cada um. |
| `services/comprar_ingresso_service.py` | Escolhe o endereço de venda de ingressos com base no time cadastrado. |
| `services/favoritar_jogo_service.py` | Alterna: cria o favorito se ainda não existir ou remove se já estiver marcado. |
| `services/listar_favoritos_service.py` | Converte os favoritos do usuário em uma lista com dados das partidas. |
| `services/avaliar_jogo_service.py` | Confere usuário, jogo, pertencimento ao time, se o jogo já ocorreu, faixa da nota e se já existe avaliação; então grava a avaliação. |
| `services/listar_minhas_avaliacoes_service.py` | Busca avaliações do usuário e acrescenta dados básicos da partida. |
| `services/calcular_rota_service.py` | Identifica o estádio pelo nome do time, valida o modo carro ou ônibus/metrô e monta um link do Google Maps com o endereço do perfil como origem. |
| `services/ocupacao_service.py` | Mantém faixas de ocupação e capacidades de referência dos setores, aplica fatores de contexto, estima público por setor, calcula cenários e escolhe um setor recomendado. Também fornece referências de localização das organizadas. |
| `services/texto_util.py` | Normaliza textos: remove acentos, converte para minúsculas e remove espaços. Ajuda a comparar nomes de times vindos de fontes diferentes. |

## 9. Frontend: o que roda no navegador

| Arquivo | O que faz |
|---|---|
| `frontend/index.html` | Estrutura as telas de login/cadastro, seleção de time e painel. Também contém os formulários, cartões, modais e regiões que o JavaScript preenche. Inclui os arquivos CSS/JS e fontes externas. |
| `frontend/css/estilo.css` | Define cores, tipografia, espaçamento, cartões e comportamento responsivo. Inclui modo claro/escuro e os temas do Cruzeiro e do Atlético no painel. |
| `frontend/js/app.js` | Controla o estado da interface, login, abas, formulários e interações. Usa `fetch` para conversar com a API; monta jogos, perfil, favoritos, avaliações, mapa de ocupação e rota. |
| `frontend/img/arena-mrv.jpg` | Foto usada como banner da Arena MRV na aba de localização. |
| `frontend/img/mineirao.jpg` | Foto usada como banner do Mineirão na aba de localização. |
| `frontend/img/mapa-arena-mrv-setores.png` | Imagem isométrica de referência da Arena MRV. O JavaScript sobrepõe cores e pontos pela ocupação estimada dos setores. |
| `frontend/img/mapa-mineirao-setores.png` | Imagem isométrica de referência do Mineirão, usada da mesma forma para mostrar a previsão por setor. |
| `frontend/img/favicon.png` | Logo transparente exibida como ícone da aba do navegador. |

### Como o JavaScript se organiza

O arquivo `app.js` é longo, mas pode ser apresentado em blocos:

1. **Estado e utilitários:** guarda token, perfil, jogos, favoritos e rota; inclui funções para buscar elementos, criar elementos de texto, formatar datas e chamar a API.
2. **Sessão e telas:** controla login, cadastro, logout, seleção de time e escolha do tema do clube.
3. **Início:** mostra o próximo jogo em casa/fora e a contagem regressiva.
4. **Ocupação:** pede previsão ao backend e desenha os cartões de setor, o mapa ilustrado e a recomendação.
5. **Jogos:** separa jogos em casa, fora e passados; permite favoritar ou avaliar partidas antigas.
6. **Localização:** chama o backend, que usa o endereço cadastrado no perfil para montar um link do Google Maps em modo carro ou ônibus/metrô. O app não pede acesso ao GPS.
7. **Perfil:** altera foto/endereço e permite trocar de time.
8. **Inicialização:** `init()` conecta os botões e formulários às funções e chama `bootstrap()` para decidir qual tela mostrar.

## 10. Scripts de jogos

Os jogos não precisam ser todos cadastrados um a um:

- `sincronizar_jogos.py` consulta o Brasileirão no football-data.org. Requer `FOOTBALL_DATA_TOKEN` no `.env`; a API pode limitar os dados conforme a temporada/plano.
- `registrar_jogo.py` serve para competições que não são importadas pelo script, como Copa do Brasil e Sul-Americana. A pessoa informa os dados no terminal.
- Ambos escrevem na tabela `jogos`, e as rotas de próximos/passados jogos leem essa tabela.

## 11. Como funciona a previsão e o mapa dos setores

O serviço escolhe os dados do Mineirão ou da Arena MRV pelo time do perfil. Para cada setor, usa a faixa informada como referência. Se receber cinco ocupações reais para aquele setor, calcula uma média ponderada com pesos `1, 1, 1, 2, 2`. Em seguida, aplica os multiplicadores de relevância e clima/data e limita o percentual a 100%. O público estimado é o percentual multiplicado pela capacidade de referência.

O resultado contém percentuais e público estimado por setor, cenários geral baixo/central/alto, referências de organizadas e uma sugestão de setor. O JavaScript pinta o mapa com base nesses percentuais.

### O que é importante explicar com precisão

- **A previsão é uma estimativa por regras**, não uma inteligência artificial treinada com uma base de vendas. Sem histórico real dos últimos cinco jogos no banco, o serviço usa o ponto médio das faixas informadas.
- A API aceita campos opcionais para histórico, capacidade disponível, clima e preços. A interface atual envia principalmente adversário, competição, fase e data; portanto, sem esses dados extras, entram as referências e padrões definidos no serviço.
- Capacidades e faixas são referências. A quantidade de setores aberta para venda pode mudar de uma partida para outra.
- A recomendação de ingresso exclui os setores marcados como referência de organizadas e combina preço com ocupação. Sem preços médios enviados para todos os candidatos, usa uma escala relativa estimada, não um preço atual em reais.
- O “mapa 3D” é uma imagem isométrica com uma camada de cores e pontos criada pelo JavaScript. Ele não é um modelo tridimensional que possa ser girado.
- A rota é calculada pelo Google Maps fora do app. O sistema mostra a origem cadastrada, o estádio e o modo escolhido, mas não calcula distância, duração nem desenha uma rota interna.
- O endereço do perfil é incluído no link do Google Maps e é enviado ao Google quando a pessoa abre esse link.

## 12. Arquivos locais e bibliotecas externas

- `backend/.env` contém credenciais/configurações da instalação e é ignorado pelo Git. Nunca projete ou compartilhe seus valores.
- `backend/instance/stadium.db` contém dados locais e pode ter usuários ou outros registros criados durante o uso.
- `backend/static/fotos/` pode conter imagens pessoais enviadas por usuários.
- O frontend carrega fontes do Google Fonts via CDN. Abrir a rota exige internet e o Google Maps.

## 13. Roteiro curto para apresentação

1. **Objetivo:** “O app organiza informações para o torcedor planejar a ida ao estádio.”
2. **Demonstração:** cadastro/login, escolha do time, painel, jogos, ocupação, mapa, recomendação, localização e perfil.
3. **Arquitetura:** “O navegador chama rotas Flask; cada controller encaminha o pedido para um service; os models leem e gravam no SQLite.”
4. **Dados externos:** explique que os jogos do Brasileirão vêm do football-data.org, as copas podem ser cadastradas pelo script e a rota abre no Google Maps com o endereço salvo no perfil.
5. **Limites:** deixe claro que ocupação, preço relativo e capacidade são estimativas e que o mapa desenha esses valores sobre imagens ilustradas.

Uma frase para resumir a arquitetura: **“A interface apresenta os dados; o backend valida e aplica as regras; o banco guarda os dados do usuário e dos jogos.”**
