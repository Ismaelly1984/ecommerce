# 🛍️ E-commerce

Um sistema de e-commerce completo construído com Flask para o backend e um frontend responsivo em HTML, CSS e JavaScript. Este projeto visa fornecer uma plataforma robusta para vendas online, com funcionalidades essenciais como gerenciamento de produtos, carrinho de compras, autenticação de usuários e um painel administrativo.

## ✨ Recursos Principais

* **Autenticação de Usuários:** Cadastro, Login e Logout seguros.
* **Gerenciamento de Produtos:** Listagem, detalhes de produtos.
* **Carrinho de Compras:** Adicionar, remover e atualizar itens no carrinho.
* **Checkout Simplificado:** Processo de finalização de compra.
* **Painel Administrativo:** (Em desenvolvimento/Planejado) Gestão de produtos e usuários.
* **Estrutura Modular:** Código organizado com Flask Blueprints para fácil manutenção e escalabilidade.
* **Banco de Dados Leve:** Utiliza SQLite para armazenamento de dados.

## 🚀 Tecnologias Utilizadas

**Backend:**
* **Python 3:** Linguagem de programação principal.
* **Flask:** Micro-framework web para o desenvolvimento do backend.
* **SQLite3:** Banco de dados relacional leve (embutido).
* **Werkzeug:** Biblioteca de utilitários WSGI.
* **Jinja2:** Motor de templates para renderização de páginas HTML.

**Frontend:**
* **HTML5:** Estrutura das páginas web.
* **CSS3:** Estilização e responsividade.
* **JavaScript:** Interatividade do lado do cliente.
* **Font Awesome:** Biblioteca de ícones.
* **Google Fonts (Poppins):** Fonte para tipografia.

## 📦 Primeiros Passos

Siga estas instruções para configurar e rodar o projeto em sua máquina local para desenvolvimento e testes.

### Pré-requisitos

Certifique-se de ter o Python 3 e o `pip` (gerenciador de pacotes do Python) instalados em seu sistema.

* [Python.org](https://www.python.org/downloads/)
* `pip` geralmente é instalado junto com o Python.

### ⬇️ Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/Ismaelly1984/ecommerce](https://github.com/Ismaelly1984/ecommerce)
    cd seu-ecommerce
    ```
    (Substitua `https://github.com/Ismaelly1984/ecommerce` pelo URL real do seu repositório).

2.  **Crie e ative um ambiente virtual:**
    É altamente recomendável usar um ambiente virtual para isolar as dependências do projeto.
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # No Linux/macOS
    # .\venv\Scripts\activate  # No Windows PowerShell
    # venv\Scripts\activate.bat # No Windows CMD
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicialize o banco de dados:**
    O projeto irá criar o arquivo `ecommerce.db` e as tabelas necessárias na primeira execução.

### ▶️ Como Rodar a Aplicação

1.  **Certifique-se de que seu ambiente virtual está ativado.** (Você deve ver `(venv)` no início do seu prompt do terminal).
2.  **Defina a variável de ambiente `FLASK_APP`** para apontar para sua fábrica de aplicativos (`create_app`):
    ```bash
    export FLASK_APP=app:create_app  # No Linux/macOS
    # $env:FLASK_APP="app:create_app" # No Windows PowerShell
    # set FLASK_APP=app:create_app   # No Windows CMD
    ```
3.  **Ative o modo de depuração (opcional, para desenvolvimento):**
    ```bash
    export FLASK_DEBUG=1  # No Linux/macOS
    # $env:FLASK_DEBUG="1" # No Windows PowerShell
    # set FLASK_DEBUG=1   # No Windows CMD
    ```
4.  **Inicie o servidor Flask:**
    ```bash
    flask run --port 5001
    ```

    Você verá uma mensagem no terminal indicando que o servidor está rodando, geralmente em `http://127.0.0.1:5001`.

## 📂 Estrutura do Projeto

A estrutura do projeto é modular e segue as boas práticas do Flask:

seu_ecommerce/
├── venv/                   # Ambiente virtual Python
├── app.py                  # Ponto de entrada principal da aplicação (fábrica de apps)
├── config.py               # Configurações da aplicação (chaves secretas, DB URI, etc.)
├── database.py             # Lógica de conexão e operações com SQLite3
├── ecommerce.db            # Arquivo do banco de dados SQLite
├── requirements.txt        # Lista de dependências Python
├── routes/                 # Contém os Blueprints para modularizar as rotas
│   ├── auth.py             # Rotas de autenticação (login, cadastro)
│   ├── main.py             # Rotas principais (home, produtos, detalhes)
│   ├── cart.py             # Rotas do carrinho de compras
│   ├── checkout.py         # Rotas de finalização de compra
│   ├── user.py             # Rotas do perfil do usuário
│   └── admin.py            # Rotas para funcionalidades de administração
├── static/                 # Arquivos estáticos (CSS, JS, imagens, uploads de usuários)
│   ├── css/                # Arquivos CSS
│   ├── js/                 # Arquivos JavaScript
│   ├── images/             # Imagens gerais da UI
│   └── uploads/            # Pasta para arquivos enviados por usuários (ignorada pelo Git)
├── templates/              # Arquivos HTML (templates Jinja2)
│   ├── base.html           # Layout base para todas as páginas
│   └── ...                 # Outros templates HTML
├── utils/                  # Funções de ajuda e utilitários
├── .gitignore              # Arquivos e pastas ignorados pelo Git
└── README.md               # Este arquivo!

## 🌐 Uso

Após iniciar o servidor, abra seu navegador e acesse:

* **Página Inicial:** `http://127.0.0.1:5001/`
* **Login:** `http://127.0.0.1:5001/login`
* **Cadastro:** `http://127.0.0.1:5001/cadastro`

Navegue pelas páginas, adicione produtos ao carrinho e explore as funcionalidades!

## 🤝 Contribuindo

Contribuições são sempre bem-vindas! Se você deseja contribuir com este projeto:

1.  Faça um fork do repositório.
2.  Crie uma nova branch para sua feature (`git checkout -b feature/nome-da-feature`).
3.  Faça suas alterações e commit (`git commit -m 'feat: Adiciona nova funcionalidade'`).
4.  Envie suas alterações para o fork (`git push origin feature/nome-da-feature`).
5.  Abra um Pull Request detalhando suas mudanças.

## 📝 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo `LICENSE` (se você tiver um) para mais detalhes.

## 📧 Contato

Se tiver alguma dúvida ou sugestão, sinta-se à vontade para entrar em contato:

* **Seu Nome:** Ismael Nunes dos Santos
* **Email:** ismaelnunes1984@gmail.com
* **GitHub:** [ismaelly1984](https://github.com/ismaelly1984)
