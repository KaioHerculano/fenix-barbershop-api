# 💈 Fênix BarberShop - API

API do sistema de gestão da **Fênix BarberShop**, desenvolvido com Django, focado em agendamentos, pagamentos, fidelidade e automações.

> 🚀 Projeto em desenvolvimento — arquitetura pensada para escalar como produto (SaaS) no futuro.

---

## 📌 Sobre o Projeto

O Fênix BarberShop é um sistema completo para gestão de barbearias, incluindo:

- 👤 Autenticação de usuários
- 📅 Agendamento de serviços
- 💳 Pagamentos via Pix
- 🎯 Sistema de fidelidade
- 📩 Notificações e e-mails
- 🛠 Painel administrativo
- ⚙️ Processamento assíncrono com Celery

---

## 🧱 Tecnologias

- Python 3.13
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Poetry (gerenciamento de dependências)
- Docker / Docker Compose

---

## 🏗 Estrutura do Projeto

```
.
├── app/
├── accounts/
├── barbers/
├── services/
├── scheduling/
├── payments/
├── loyalty/
├── notifications/
├── manage.py
├── pyproject.toml
├── docker-compose.yml
└── Dockerfile
```

---

## 🔐 Autenticação

O sistema utiliza **Custom User Model** com:

- Login via email
- Estrutura preparada para expansão

---

## ⚙️ Setup do Projeto

### Clonar o repositório

```
git clone <repo-url>
cd fenix-barbershop-api
```

### Subir com Docker

```
docker-compose up --build
```

### Aplicar migrações

```
docker-compose exec web python manage.py migrate
```

### Criar superusuário

```
docker-compose exec web python manage.py createsuperuser
```

---

## 🔄 Celery

```
docker-compose up celery
```

---

## 📊 Roadmap

- [x] Custom User Model
- [x] Setup Celery + Redis
- [ ] Autenticação
- [ ] Agendamento
- [ ] Pagamentos
- [ ] Fidelidade
- [ ] Notificações

---

## 🚀 Futuro

- SaaS multi-barbearia
- Dashboard
- WhatsApp
- App mobile

---

## 🤝 Contribuição

1. Fork
2. Branch
3. Commit
4. PR

---

## 📄 Licença

MIT
