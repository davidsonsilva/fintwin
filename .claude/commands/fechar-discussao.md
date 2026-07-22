# 🔒 FECHANDO DISCUSSÃO E CONSOLIDANDO PLANO

Você está fechando o modo de planejamento e consolidando tudo em um plano final.

## 📋 Passos Obrigatórios

### 1. IDENTIFICAR Memória Temporária Ativa

Procure a memória mais recente com prefixo `planning/temp_`:
- Use `list_memories` ou verifique o contexto da conversa
- Se houver múltiplas, use a mais recente

### 2. LER TODO O CONTEÚDO DA Memória Temporária

Use `read_memory` para obter tudo que foi discutido.

### 3. CONSOLIDAR EM Memória Permanente

Crie uma nova memória com nome: `planning/[slug-da-tarefa]_[YYYYMMDD]`

**Estrutura da memória permanente:**

# Plano: [Título Claro da Tarefa]

## 📅 Criado em: [data]

## 🎯 Status: PLANEJADO (aguardando aprovação)

---

## 📋 Resumo Executivo

[2-3 parágrafos resumindo o que será feito]

---

## 🎯 Objetivo

[Qual problema estamos resolvendo? Qual valor vamos entregar?]

---

## 🏗️ Arquitetura / Abordagem Escolhida

### Solução Final

[Descrição detalhada da solução acordada]

### Diagrama (se aplicável)

[diagrama em ASCII ou descrição]

---

## ✅ Decisões Tomadas

### Decisão 1: [Título]

- **O quê**: [decisão]
- **Por quê**: [motivo]
- **Alternativas rejeitadas**: [quais e por quê]

### Decisão 2: [Título]

...

---

## ❌ Lições das Correções (OURO!)

### Correção 1

- **Erro que eu cometi**: [descrever]
- **O que o usuário ensinou**: [descrever]
- **Como aplicar na implementação**: [ação concreta]

### Correção 2

...

⚠️ **ATENÇÃO**: Estas correções são CRÍTICAS. Durante a implementação,
REVISE esta seção antes de cada passo para NÃO repetir os mesmos erros!

---

## 🔧 Especificações Técnicas

### Requisitos Funcionais

1. [Requisito 1]
2. [Requisito 2]

### Requisitos Não-Funcionais

- Performance: [...]
- Segurança: [...]
- Escalabilidade: [...]

### Critérios de Aceite

- [ ] [Critério 1]
- [ ] [Critério 2]

---

## 🗺️ Plano de Implementação

### Fase 1: [Nome]

- [ ] Tarefa 1.1: [descrição]
- [ ] Tarefa 1.2: [descrição]
- **Arquivos afetados**: [lista]
- **Dependências**: [lista]

### Fase 2: [Nome]

- [ ] Tarefa 2.1: [descrição]
- ...

### Ordem de Execução

1. [Primeiro passo]
2. [Segundo passo]
...

---

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| [Risco 1] | Alta/Média/Baixa | Alto/Médio/Baixo | [Como mitigar] |

---

## 🧪 Estratégia de Testes

- **Testes unitários**: [o que testar]
- **Testes de integração**: [o que testar]
- **Testes manuais**: [como validar]

---

## 📚 Contexto e Referências

- Memória original: `planning/temp_XXXXX`
- Arquivos relevantes: [lista]
- Documentação relacionada: [links]

---

## 🚦 Próximo Passo

**Aguardando aprovação do usuário para iniciar implementação.**

Quando aprovado:
1. Criar memória `planning/[slug]_em_execucao`
2. Seguir o plano fase por fase
3. Consultar correções registradas ANTES de cada passo
4. Atualizar progresso na memória

### 4. APRESENTAR O PLANO FINAL

Mostre ao usuário um resumo do plano e peça aprovação:

✅ **PLANO CONSOLIDADO**

Memória criada: `planning/[slug]_20260624`

**Resumo**: [2-3 linhas]

**Principais decisões**:
1. [Decisão 1]
2. [Decisão 2]

**Correções registradas**: [X] (serão respeitadas na implementação!)

**Fases de implementação**: [N]

---

👉 **Revise a memória completa no dashboard do Serena**
👉 **Se estiver tudo certo, diga: "pode implementar"**
👉 **Se precisar ajustar, me diga o que mudar**

Aguardando sua aprovação! ✅

### 5. DELETAR Memória Temporária

Após criar a permanente, use `delete_memory` para remover a temporária
(para não acumular lixo).
