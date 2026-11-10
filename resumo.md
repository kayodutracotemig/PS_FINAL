Guia resumido — Stadium Guide BH
O que é
O Stadium Guide BH é uma aplicação web para torcedores do Atlético-MG e do Cruzeiro planejarem a ida ao Mineirão ou à Arena MRV. Reúne calendário de jogos, estimativa de ocupação por setor, sugestão de setor e informações para chegar ao estádio.
Funcionalidades principais
- Consultar próximos jogos e calendário.
- Ver uma estimativa de público por setor e sua visualização no mapa ilustrado do estádio.
- Consultar uma sugestão de setor, considerando ocupação e preço relativo.
- Ver referências de torcidas organizadas, que podem variar conforme o evento.
- Acessar o link de compra de ingresso do time.
- Abrir no Google Maps uma rota a partir do endereço salvo no perfil, escolhendo carro ou transporte público.
- Usar cadastro, login, perfil, favoritos e avaliações de jogos passados.
Como funciona por dentro
O navegador envia requisições à API Flask, que valida os dados e encaminha as operações pelas camadas Controller, Service e Model. Os Models consultam e gravam os dados no SQLite usando SQLAlchemy. O navegador não acessa o banco diretamente.

Recuperação de dados: o frontend pede os próximos jogos; o controller encaminha a solicitação ao service, que consulta o Model. O resultado volta em JSON para a interface.

Entrada de dados: para registrar uma avaliação, o controller valida os dados e o token; o service aplica as regras; o Model grava a avaliação no banco.

A pasta backend/repositories/ está reservada para essa camada, mas atualmente contém apenas .gitkeep. As consultas são feitas diretamente pelos Models e Services.
Dados externos e limites
- O script sincronizar_jogos.py importa jogos do Brasileirão usando football-data.org.
- Jogos de competições como Copa do Brasil e Sul-Americana podem ser cadastrados pelo script registrar_jogo.py.
- A previsão de ocupação usa regras e referências de capacidade. É uma estimativa, não uma previsão produzida por IA treinada com vendas reais.
- O mapa é uma imagem ilustrada com cores e pontos sobrepostos; não é um modelo 3D giratório.
- A rota abre no Google Maps. O app não calcula a distância nem a duração internamente.
Frase para apresentar a arquitetura
“A interface mostra os dados; o backend valida as solicitações e aplica as regras; os Models consultam e atualizam o banco SQLite.”