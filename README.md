# Stadium Guide

App web para torcedores de **Atlético MG** e **Cruzeiro**: próximos jogos, ingresso, previsão de ocupação do estádio, rota até a arena, favoritos e avaliações.

- **Backend:** Python + Flask + SQLite (arquitetura em camadas: Controller → Service → Model)
- **Frontend:** HTML + CSS + JavaScript puro (servido pelo próprio Flask)

## Como rodar

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```

Abra **http://127.0.0.1:5000** no navegador (não abra o `index.html` com duplo clique: o app precisa do servidor).

O banco (`backend/instance/stadium.db`) e os dois times são criados na primeira execução. Os jogos reais são importados pelo comando abaixo.

### Sincronizar jogos reais

1. Crie uma conta gratuita e obtenha um token em [football-data.org](https://www.football-data.org/client/register).
2. Copie `backend/.env.example` para `backend/.env` e preencha `FOOTBALL_DATA_TOKEN`.
3. Com o ambiente virtual e dependências instalados, execute:

```bash
cd backend
python sincronizar_jogos.py
```

O script importa os jogos da temporada atual do Brasileirão Série A para Atlético-MG e Cruzeiro. O football-data.org oferece o calendário do Brasileirão no plano gratuito, com limite de chamadas; uma execução faz uma chamada e atualiza as partidas pelo identificador da API, sem duplicá-las. Rode novamente para buscar mudanças de data e horário. Também é possível informar uma temporada pelo ano, por exemplo `python sincronizar_jogos.py 2026`.

### Cadastrar manualmente jogos de Copa

Para jogos da Copa do Brasil ou da Sul-Americana, execute `python registrar_jogo.py` na pasta `backend` e responda às perguntas do terminal. Informe o time, adversário, data e hora local, mando (casa/fora), estádio e competição. O jogo aparecerá no app e o script avisa se ele já estiver cadastrado. Exemplo de data: `2026-10-29 19:00`.

Configuração opcional: copie `backend/.env.example` para `backend/.env`. Sem ele o app usa valores padrão de desenvolvimento.

## Funcionalidades Implementadas

1. **Cadastro** de usuário (senha com hash)
2. **Login** com token de sessão
3. **Seleção de time** (time do coração)
4. **Mudar de time** (com confirmação)
5. **Tela de perfil** (nome, e-mail, time, favoritos, avaliações)
6. **Compra de ingresso** (abre o site oficial de ingressos do clube)
7. **Próximos jogos** (abas Em Casa / Fora, com contagem regressiva do próximo)
8. **Adicionar foto** de perfil (PNG/JPG, até 5 MB)
9. **Adicionar localização** (endereço do usuário)
10. **Logout**
11. **Favoritar jogo**
12. **Avaliar jogo antigo** (1 a 5 estrelas + comentário)
13. **Modo claro/escuro**
14. **Guia para locomoção até o estádio** (abre a rota no Google Maps usando o endereço salvo no perfil)
15. **Modos de rota**: carro ou ônibus/metrô, calculados pelo Google Maps
16. **Previsão de público** (média de temporada, fatores de contexto e cenários baixo/central/alto)
17. **Previsão de ocupação por setor** (percentual e público estimado a partir das faixas históricas informadas e do contexto da partida)
18. **Mapa isométrico de ocupação** da Arena MRV e do Mineirão, com densidade visual por setor para o jogo selecionado
19. **Sincronização dos jogos do Brasileirão** (football-data.org; executada por comando)
20. **Cadastro manual** de jogos da Copa do Brasil e da Sul-Americana
21. **Referências de setores de torcidas organizadas** na Arena MRV e no Mineirão, com aviso para confirmar o mapa do evento
22. **Tema do clube** após a seleção: azul e branco para o Cruzeiro, preto e branco para o Atlético; cadastro e seleção de time permanecem neutros
23.**Mapa 3D do estadio com marcas de ocupação**

### Ainda não implementado

Mapa 3D interativo com câmera livre.
As faixas históricas por setor usadas na previsão foram fornecidas pelo usuário. Sem histórico real recente de ocupação salvo por setor, a previsão parte do ponto médio dessas faixas; capacidades são referências e podem variar conforme o mapa e a liberação de ingressos de cada evento. O fator de chuva/sol pode ser informado à API de previsão; sem esse dado, usa-se 1,0. Jogos em dias úteis após 19h recebem fator 0,8.

A sugestão de setor atribui 40% do peso ao preço e 60% à menor ocupação prevista, excluindo setores com referência de torcida organizada. A API aceita preços médios em reais por setor (`precos_setores`). Enquanto não forem informados para todos os setores elegíveis, usa faixas de preço relativas estimadas, que não representam preços atuais de ingressos.

## Estrutura

```
backend/
  app.py            cria o Flask, registra as rotas e inicializa os times
  sincronizar_jogos.py  sincroniza o Brasileirão via football-data.org
  registrar_jogo.py    cadastra manualmente jogos das copas
  config.py         configurações (lê o .env)
  controllers/      recebem a requisição HTTP e devolvem JSON
  services/         uma classe por caso de uso (regras de negócio)
  models/           tabelas (SQLAlchemy) e operações de banco
  repositories/     reservado para consultas complexas
frontend/
  index.html  css/estilo.css  js/app.js  img/
```
