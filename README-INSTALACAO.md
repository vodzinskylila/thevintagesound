# The Vintage Sound — Guia de Instalação

## Estrutura do Projeto

```
thevintagesound/
├── back-end/
│   ├── app.py                  # Servidor Flask principal
│   ├── database.py             # Modelos e inicialização do banco
│   ├── requirements.txt        # Dependências Python
│   └── routes/
│       ├── auth.py             # /api/auth
│       ├── products.py         # /api/products
│       ├── cart.py             # /api/cart
│       ├── orders.py           # /api/orders
│       └── subscriptions.py    # /api/subscriptions
└── front-end/
    ├── api.js                  # Módulo JS compartilhado
    ├── index.html              # Página inicial
    ├── loja.html               # Loja
    ├── carrinho.html           # Carrinho
    ├── login.html              # Login / Cadastro
    ├── edicoes_passadas.html   # Edições passadas
    └── sobre.html              # Sobre
```

## Instalação e Execução

### 1. Requisitos
- Python 3.10+
- Nenhuma instalação necessária para o front-end (HTML puro)

### 2. Instalar dependências do back-end
```bash
cd back-end
pip install -r requirements.txt
```

### 3. Iniciar o servidor
```bash
python app.py
```
O servidor inicia em `http://localhost:3000`

### 4. Abrir o front-end
Abra o arquivo `front-end/index.html` no navegador, ou use um servidor local:
```bash
cd front-end
python -m http.server 8080
```
Depois acesse `http://localhost:8080`

## Credenciais de Teste
- **Admin:** admin@vintagesound.com / admin123

## Endpoints da API
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /api/auth/register | Cadastro |
| POST | /api/auth/login | Login |
| GET  | /api/auth/me | Dados do usuário |
| GET  | /api/products | Listar produtos |
| GET  | /api/cart | Ver carrinho (auth) |
| POST | /api/cart/items | Adicionar ao carrinho (auth) |
| POST | /api/orders | Criar pedido (auth) |
| GET  | /api/orders/my | Meus pedidos (auth) |
| GET  | /api/subscriptions/plans | Planos disponíveis |
