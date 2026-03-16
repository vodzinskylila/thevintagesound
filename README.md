# Clube de Assinatura de Vinil

Disciplina: Programação WEB  
Professor: Luiz Carlos Camargo, PhD.  
Alunos: William (Front-end) e Pedro Israel (Back-end)
1. Domínio do Problema (Escopo)

O projeto consiste em desenvolver uma aplicação web para um serviço de assinatura de discos de vinil. A plataforma permitirá que usuários se cadastrem, gerenciem sua assinatura e recebam mensalmente um disco de vinil selecionado.

O conceito é criar uma experiência de usuário limpa, minimalista e intuitiva, onde o foco está na descoberta musical e no colecionismo. A cada mês, um novo disco será anunciado no site, e os assinantes ativos o receberão em casa.

 1.1. Requisitos Funcionais (RF)

*   **RF01:** O sistema deve permitir que um novo usuário se cadastre na plataforma, fornecendo dados como nome, e-mail, senha e endereço de entrega.
*   **RF02:** O sistema deve permitir que um usuário autenticado gerencie os dados de sua conta (ex: alterar senha, atualizar endereço).
*   **RF03:** O sistema deve exibir o disco do mês atual na página principal.
*   **RF04:** O sistema deve permitir que um usuário realize a assinatura do serviço, fornecendo dados de pagamento.
*   **RF05:** O sistema deve ter uma área administrativa para cadastrar o "disco do mês".
*   **RF06:** O sistema deve processar a lógica de envio do disco para todos os assinantes ativos na primeira semana do mês (simulação).

 1.2. Requisitos Não-Funcionais (RNF)

*   **RNF01:** A interface do usuário deve ser limpa, minimalista e responsiva (adaptável a desktops e celulares).
*   **RNF02:** A aplicação deve ser segura, protegendo os dados dos usuários e as transações.
*   **RNF03:** O back-end deve ser construído como uma API RESTful para desacoplar a lógica do front-end.
*   **RNF04:** O sistema deve ser performático, com tempos de resposta rápidos para as requisições do usuário.

---

 2. Tecnologias Utilizadas

A escolha das tecnologias foi baseada na familiaridade da equipe e nos requisitos da disciplina, buscando ferramentas modernas e eficientes para o desenvolvimento web.

| Camada      | Tecnologia | Justificativa                                                                                                                                                                                                                                                                                       |
| :---------- | :--------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Front-end** | `HTML`, `CSS`, `JavaScript` | **HTML** será a base para estruturar o conteúdo de forma semântica e acessível. A escolha se dá pela familiaridade do desenvolvedor e por ser a tecnologia fundamental da web. **CSS** e **JavaScript** serão usados para estilização e interatividade, criando a experiência minimalista desejada. |
| **Back-end**  | `Python` com `FastAPI` | **Python** é uma linguagem versátil e de alta produtividade. O framework **FastAPI** foi escolhido por sua alta performance, documentação automática de APIs (Swagger UI) e por facilitar a criação de APIs RESTful robustas e rápidas, o que atende perfeitamente ao nosso RNF03. |
| **Banco de Dados** | `SQLite` (inicialmente) | Para a fase inicial do projeto, `SQLite` é ideal por ser simples, leve e não exigir um servidor dedicado. Ele atende às necessidades de um CRUD básico e pode ser facilmente substituído por um banco de dados mais robusto (como PostgreSQL) no futuro, se necessário. |
| **Controle de Versão** | `Git` e `GitLab` | Conforme solicitado na disciplina, `Git` será usado para o controle de versão do código-fonte, e o `GitLab` para hospedar o repositório, gerenciar o projeto e, futuramente, configurar o pipeline de CI/CD. |

---

## 3. Organização de Tarefas (Trello)

Para organizar o desenvolvimento, utilizaremos um quadro no Trello. A divisão inicial de responsabilidades está definida da seguinte forma:

**William (Front-end):**
*   [ ] Estruturar as páginas principais com HTML (Home, Login, Cadastro, Área do Assinante).
*   [ ] Estilizar as páginas com CSS para garantir o design minimalista e responsivo.
*   [ ] Implementar a lógica de front-end com JavaScript para consumir a API do back-end.

**Pedro Israel (Back-end):**
*   [ ] Modelar o banco de dados (tabelas de usuários, assinaturas, discos).
*   [ ] Desenvolver a API RESTful com FastAPI (endpoints para CRUD de usuários, autenticação, etc.).
*   [ ] Implementar a lógica de negócio para o sistema de assinaturas.
