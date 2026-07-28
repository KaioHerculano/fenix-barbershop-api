# Painel administrativo e operacao

A operacao interna inicial da Fenix BarberShop acontece pelo Django Admin em `/admin/`.

Essa camada foi pensada para permitir que a equipe acompanhe e gerencie o sistema sem depender de acesso direto ao banco de dados.

## Acesso

O acesso ao Django Admin usa a regra padrao do Django:

- usuario com `is_staff=True` pode acessar o admin;
- permissoes por model continuam sendo controladas pelo sistema de permissoes do Django;
- dados financeiros e historicos sensiveis priorizam visualizacao e auditoria.

## Clientes

O admin de usuarios permite:

- buscar por nome, e-mail e telefone;
- filtrar por status ativo, staff, superuser e data de cadastro;
- visualizar datas de cadastro, ultimo login e atualizacao;
- gerenciar dados basicos da conta.

Perfis de cliente tambem ficam disponiveis para consulta e edicao operacional.

## Empresas e equipe

O admin permite operar:

- empresas;
- funcionarios vinculados a empresa;
- convites de barbeiro;
- vinculos de barbeiro com servicos.

Funcionarios podem ser ativados ou desativados em massa. Isso permite tirar um barbeiro da operacao sem remover historico.

## Catalogo

Servicos podem ser criados, editados, ativados e desativados pelo admin.

A listagem permite busca por:

- nome;
- descricao;
- empresa;
- slug da empresa.

Tambem existem filtros por empresa, status ativo, duracao e data de criacao.

## Agenda

Agendamentos podem ser acompanhados por:

- empresa;
- cliente;
- barbeiro;
- servico;
- data;
- status;
- pagamento vinculado.

Filtros operacionais incluem:

- hoje;
- proximos;
- passados;
- status;
- empresa;
- barbeiro;
- servico.

O admin tambem possui acoes para:

- cancelar agendamentos selecionados;
- marcar agendamentos selecionados como concluidos.

Ao cancelar um agendamento pelo admin, pagamentos pendentes vinculados tambem sao cancelados.

Ao concluir um agendamento pelo admin, a regra de fidelidade e reaplicada e o cliente recebe os pontos previstos quando ainda nao houve pontuacao para aquele atendimento.

## Pagamentos

Pagamentos sao tratados como area de auditoria.

O admin permite visualizar:

- cliente;
- empresa;
- agendamento;
- valor;
- status;
- provedor;
- identificador do provedor;
- data de criacao;
- data de pagamento.

Campos criticos como idempotencia, payload do provedor, codigo Pix e identificadores externos ficam somente leitura no admin.

Eventos de webhook tambem ficam disponiveis para auditoria e nao podem ser criados manualmente pelo admin.

## Fidelidade

Cartoes de fidelidade mostram saldo por cliente e empresa.

O saldo nao deve ser editado diretamente. Ajustes manuais devem ser feitos criando uma transacao de fidelidade no admin.

Ao criar uma transacao manual pelo admin, o sistema usa a regra de ajuste da camada de servico:

- ajuste positivo soma pontos;
- ajuste negativo subtrai pontos;
- ajuste que deixaria saldo negativo e rejeitado;
- toda alteracao gera historico transacional.

## Fora do escopo desta fase

Esta fase nao cria:

- dashboard grafico;
- painel frontend em Next.js;
- API administrativa customizada;
- relatorios analiticos;
- RBAC avancado.

Esses pontos seguem no roadmap para evolucao futura.
