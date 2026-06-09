# ⚡ Wattiz — Backend API

> Plataforma de Inteligência Energética para famílias brasileiras.  
> Monitore, entenda e economize energia com ajuda da IA **Lume**.

---

## 📁 Estrutura do Projeto

```
backend/
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py          # Registro, login, JWT
│   │       │   ├── users.py         # Perfil do usuário
│   │       │   ├── appliances.py    # CRUD eletrodomésticos
│   │       │   ├── tariffs.py       # Tarifa energética
│   │       │   ├── dashboard.py     # Painel de consumo
│   │       │   ├── reports.py       # Relatórios mensais
│   │       │   ├── lume.py          # IA Lume (chatbot + insights)
│   │       │   └── iot.py           # IoT (preparado, em breve)
│   │       └── router.py
│   │
│   ├── core/
│   │   ├── config.py       # Settings (Pydantic BaseSettings)
│   │   ├── security.py     # JWT + bcrypt
│   │   └── dependencies.py # Injeção de usuário autenticado
│   │
│   ├── database/
│   │   ├── base.py         # Base declarativa + imports de modelos
│   │   └── session.py      # Engine async + get_db()
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── appliance.py
│   │   ├── consumption.py
│   │   ├── tariff.py
│   │   └── report.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── appliance.py
│   │   ├── tariff.py
│   │   ├── dashboard.py
│   │   ├── lume.py
│   │   └── report.py
│   │
│   ├── services/           # Lógica de negócio (Clean Architecture)
│   │   ├── user_service.py
│   │   ├── appliance_service.py
│   │   ├── tariff_service.py
│   │   ├── dashboard_service.py
│   │   ├── report_service.py
│   │   └── lume_orchestrator.py
│   │
│   ├── analytics/
│   │   └── energy_engine.py  # Motor de cálculos energéticos
│   │
│   ├── ia/
│   │   └── lume_service.py   # Integração Ollama/llama3
│   │
│   ├── middleware/
│   │   └── logging.py
│   │
│   └── main.py              # Entrypoint FastAPI
│
├── alembic/                 # Migrations de banco de dados
│   ├── env.py
│   └── versions/
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── .env.example
```

---

## 🚀 Como Rodar Localmente

### Pré-requisitos

- Docker + Docker Compose
- (Opcional) Python 3.12+ para desenvolvimento sem Docker

### 1. Clonar e configurar

```bash
git clone https://github.com/seu-usuario/wattiz.git
cd wattiz/backend

# Criar arquivo de configuração
cp .env.example .env
# Edite o .env e troque SECRET_KEY por uma string aleatória segura
```

### 2. Subir os containers

```bash
docker compose up -d
```

Isso sobe:
- **wattiz_api** — FastAPI na porta `8000`
- **wattiz_db** — PostgreSQL na porta `5432`
- **wattiz_ollama** — Ollama na porta `11434`

### 3. Baixar o modelo da IA

```bash
docker exec -it wattiz_ollama ollama pull llama3
```

> Aguarde o download (llama3 ~4GB). Progresso visível no terminal.

### 4. Verificar

```bash
# Health check
curl http://localhost:8000/health

# Documentação interativa
open http://localhost:8000/docs
```

---

## ⚙️ Variáveis de Ambiente (`.env`)

| Variável | Descrição | Padrão |
|---|---|---|
| `DATABASE_URL` | URL completa de conexão async | — |
| `SECRET_KEY` | Chave JWT (64+ chars aleatórios) | — |
| `ALGORITHM` | Algoritmo JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do access token | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Validade do refresh token | `7` |
| `OLLAMA_BASE_URL` | URL do servidor Ollama | `http://ollama:11434` |
| `OLLAMA_MODEL` | Modelo LLM utilizado | `llama3` |
| `LUME_TEMPERATURE` | Temperatura da geração (criatividade) | `0.4` |
| `DEFAULT_TARIFF` | Tarifa padrão R$/kWh | `0.75` |
| `ALLOWED_ORIGINS` | URLs permitidas pelo CORS | `http://localhost:3000` |

Gere uma SECRET_KEY segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📡 Endpoints da API

### Autenticação
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/auth/register` | Cadastrar usuário |
| POST | `/api/v1/auth/login` | Login (retorna JWT) |
| POST | `/api/v1/auth/refresh` | Renovar access token |
| GET | `/api/v1/auth/me` | Dados do usuário logado |

### Eletrodomésticos
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/appliances/` | Cadastrar aparelho |
| GET | `/api/v1/appliances/` | Listar com kWh calculado |
| GET | `/api/v1/appliances/{id}` | Detalhe |
| PATCH | `/api/v1/appliances/{id}` | Atualizar |
| DELETE | `/api/v1/appliances/{id}` | Remover |

### Dashboard
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/dashboard/?month=6&year=2025` | Painel completo |

### IA Lume
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/lume/chat` | Conversar com a Lume |
| POST | `/api/v1/lume/insights` | Gerar análise mensal |
| GET | `/api/v1/lume/health` | Status do Ollama |

### Relatórios
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/reports/generate` | Gerar relatório mensal |
| GET | `/api/v1/reports/` | Listar relatórios |
| GET | `/api/v1/reports/period?month=6&year=2025` | Buscar por período |

---

## 🤖 Fluxo da IA Lume

```
Usuário faz pergunta
        │
        ▼
[LumeOrchestrator]
  Busca aparelhos do usuário
  Obtém tarifa ativa
        │
        ▼
[EnergyEngine]
  Calcula kWh, custos,
  percentuais, insights
        │
        ▼
[LumeService]
  Monta prompt com contexto
  real dos dados calculados
        │
        ▼
[Ollama / llama3]
  Gera resposta em linguagem
  natural baseada nos dados
        │
        ▼
Resposta contextualizada
ao usuário
```

**Garantia de contexto**: A Lume **nunca** recebe uma pergunta sem os dados energéticos do usuário injetados no prompt. Isso evita alucinações e garante respostas baseadas em fatos reais.

---

## 🏗️ Decisões Arquiteturais

### Clean Architecture
Cada camada tem responsabilidade única:
- **Endpoints** → apenas receber requisição e retornar resposta
- **Services** → lógica de negócio
- **Analytics** → cálculos matemáticos isolados
- **IA** → integração com modelo de linguagem
- **Models** → mapeamento ORM
- **Schemas** → validação e serialização

### Async por padrão
FastAPI + asyncpg + SQLAlchemy async permitem centenas de requisições simultâneas sem bloquear threads.

### Separação Analytics ↔ IA
O `EnergyEngine` é completamente determinístico (sem IA). A Lume recebe os dados prontos. Isso permite:
- Testar cálculos de forma isolada
- Usar a IA apenas onde ela agrega valor (linguagem natural)
- Trocar o modelo LLM sem impactar os cálculos

---

## 🔗 Integração com Front-End React

```typescript
// Exemplo de autenticação
const login = async (email: string, password: string) => {
  const form = new FormData();
  form.append('username', email);  // OAuth2 usa 'username'
  form.append('password', password);

  const res = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    body: form,
  });
  const { access_token } = await res.json();
  localStorage.setItem('token', access_token);
};

// Exemplo de chamada autenticada
const getDashboard = async () => {
  const res = await fetch('http://localhost:8000/api/v1/dashboard/', {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
  });
  return res.json();
};

// Chat com a Lume
const chatLume = async (message: string) => {
  const res = await fetch('http://localhost:8000/api/v1/lume/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
    body: JSON.stringify({ message }),
  });
  const { response } = await res.json();
  return response;
};
```

---

## 📈 Como Escalar no Futuro

### Curto prazo
- Adicionar **Redis** para cache de dashboards (evitar recalcular a cada request)
- Implementar **rate limiting** nos endpoints da Lume (chamadas ao Ollama são custosas)
- Adicionar **Celery + Redis** para geração de relatórios em background

### Médio prazo
- **Múltiplos workers Uvicorn** atrás de Nginx
- **Réplicas de leitura** do PostgreSQL para queries analíticas pesadas
- **Streaming de respostas** da Lume via SSE (Server-Sent Events)

### Integração IoT (futuro)
```
Dispositivo IoT
      │  MQTT / HTTP
      ▼
[IoT Gateway Service]     ← novo serviço
      │
      ▼
[Message Broker: RabbitMQ/Kafka]
      │
      ▼
[Consumer Service]        ← processa leituras em background
  grava ConsumptionRecord
  com timestamp real
      │
      ▼
[WebSocket Hub]           ← dashboard em tempo real
      │
      ▼
Front-end React
```

A tabela `consumption_records` já está preparada para receber dados de IoT — basta adicionar o campo `device_id` e a origem da leitura.

---

## 🔧 Migrations (Alembic)

```bash
# Criar nova migration
docker exec wattiz_api alembic revision --autogenerate -m "descricao"

# Aplicar migrations
docker exec wattiz_api alembic upgrade head

# Reverter última migration
docker exec wattiz_api alembic downgrade -1
```

---

## 🧪 Testando a API

Acesse `http://localhost:8000/docs` para a interface Swagger interativa.

Fluxo de teste manual:
1. `POST /api/v1/auth/register` — criar conta
2. `POST /api/v1/auth/login` — obter token
3. Clicar em **Authorize** no Swagger e inserir o token
4. `POST /api/v1/tariffs/` — cadastrar tarifa (ex: `0.75`)
5. `POST /api/v1/appliances/` — cadastrar aparelhos
6. `GET /api/v1/dashboard/` — ver painel
7. `POST /api/v1/lume/chat` — conversar com a Lume

---

## 📄 Licença

MIT — Wattiz © 2025
