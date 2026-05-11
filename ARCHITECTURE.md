# 🏛️ Fênix BarberShop - Especificação Arquitetural & Requisitos

## 🎯 1. Visão Geral
O Fênix BarberShop é uma plataforma SaaS de gestão para barbearias, permitindo o gerenciamento completo de clientes, profissionais, serviços, agendamentos, pagamentos e fidelidade.

---

## 📊 2. Modelo de Dados (ERD)

```mermaid
erDiagram
    USER ||--o{ COMPANY_EMPLOYEE : works_at
    COMPANY ||--o{ COMPANY_EMPLOYEE : has

    COMPANY ||--o{ SERVICE : offers
    COMPANY ||--o{ BARBER_SCHEDULE : manages
    COMPANY ||--o{ APPOINTMENT : owns
    COMPANY ||--o{ LOYALTY_ACCOUNT : owns
    COMPANY ||--o{ PAYMENT : owns

    USER ||--o{ APPOINTMENT : books
    USER ||--|| CUSTOMER_PROFILE : has
    USER ||--o{ LOYALTY_ACCOUNT : has

    COMPANY_EMPLOYEE ||--o{ APPOINTMENT : performs
    COMPANY_EMPLOYEE ||--o{ BARBER_SCHEDULE : has

    SERVICE ||--o{ APPOINTMENT_SERVICE : used_in
    APPOINTMENT ||--o{ APPOINTMENT_SERVICE : contains

    APPOINTMENT ||--|| PAYMENT : generates
    PAYMENT ||--o{ PAYMENT_EVENT : has

    LOYALTY_ACCOUNT ||--o{ LOYALTY_TRANSACTION : records

    APPOINTMENT ||--o{ NOTIFICATION : triggers

    USER {
        uuid id PK
        string email UK
        string password
        string full_name
        string role
        boolean is_active
        datetime created_at
    }

    COMPANY {
        uuid id PK
        string name
        string slug UK
        string address
        boolean is_active
        datetime created_at
    }

    COMPANY_EMPLOYEE {
        uuid id PK
        fk user_id
        fk company_id
        string role
        boolean is_active
    }
```
*(Nota: Para ver o diagrama completo com todas as tabelas e relações, consulte o código DBML gerado para o dbdiagram.io)*

---

## ✅ 3. Requisitos Funcionais (RF)

### 🔐 Autenticação & Usuários
- **RF01**: Cadastro e Login via E-mail/Senha (JWT).
- **RF02**: Recuperação e redefinição de senha com confirmação de e-mail.
- **RF03**: Gerenciamento de perfil e desativação de conta.

### 🏢 Gestão de Empresas & Staff
- **RF04**: Cadastro e edição de barbearias (Tenants).
- **RF05**: Vínculo de funcionários com papéis específicos (`ADMIN`, `BARBER`, `RECEPTIONIST`).
- **RF06**: Controle de permissões e isolamento total entre empresas.

### ✂️ Serviços & Agenda
- **RF07**: Gestão de catálogo de serviços (Preço, Duração, Status).
- **RF08**: Agendamento com seleção de Barbeiro, Serviço e Horário.
- **RF09**: Controle de disponibilidade semanal e bloqueios de horários.

### 💳 Pagamentos & Fidelidade
- **RF10**: Integração com Pix e registro de eventos de pagamento.
- **RF11**: Garantia de idempotência em pagamentos e webhooks.
- **RF12**: Sistema de fidelidade (Acúmulo e resgate de pontos).

### 📢 Comunicação & Dashboards
- **RF13**: Notificações via E-mail (Lembretes, Confirmações).
- **RF14**: Painel Administrativo com métricas de faturamento e agenda.

---

## ⚙️ 4. Requisitos Não Funcionais (RNF)
- **RNF01**: **Escalabilidade**: Arquitetura Multi-tenant preparada para crescimento.
- **RNF02**: **Segurança**: Senhas criptografadas e isolamento de dados entre tenants.
- **RNF03**: **Performance**: Respostas rápidas e consultas otimizadas (< 50ms para buscas simples).
- **RNF04**: **Processamento Assíncrono**: Uso de Celery + Redis para tarefas pesadas.
- **RNF05**: **Padronização**: Ambiente Dockerizado para consistência Total.
- **RNF06**: **Observabilidade**: Logs estruturados e rastreamento de erros.

---

## 🧠 5. Requisitos Estratégicos (SaaS)
- **RES01**: Preparação para cobrança recorrente (Assinaturas).
- **RES02**: API-First: Backend pronto para Mobile e Web moderno.
- **RES03**: Monetização via planos de funcionalidades.

---

## 🎨 6. Design System (Tokens)
- **Primary**: `#D4AF37` (Gold)
- **Secondary**: `#1A1A1A` (Dark Gray)
- **Background**: `#0F0F0F` (Deep Black)
- **Text**: `#F5F5F5` (Off-White)
