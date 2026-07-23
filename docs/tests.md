# Testes e qualidade

## Comandos principais

```bash
make lint
make test-coverage
```

## Cobertura minima

O projeto exige cobertura minima de 90%.

Na fase documentada aqui, a cobertura total esta acima desse limite.

## O que os testes cobrem hoje

- Cadastro de owner e cliente.
- Validacoes de senha.
- Login e perfil autenticado.
- Reset de senha.
- Catalogo publico de servicos.
- Listagem publica de barbeiros.
- Vinculo barbeiro-servico.
- Horarios de funcionamento.
- Disponibilidade de agenda.
- Criacao, cancelamento e reagendamento.
- Convites de barbeiro.
- E-mails transacionais e fallback sem provider.

## Qualidade antes de PR

Antes de abrir PR:

```bash
make lint
make test-coverage
```

Se a documentacao foi alterada:

```bash
mkdocs build --strict
```
