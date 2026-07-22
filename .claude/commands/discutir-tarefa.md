# 🎯 MODO PLANEJAMENTO ATIVADO

Você entrou em **MODO DE PLANEJAMENTO** para a tarefa: $ARGUMENTS

## 📋 Suas Responsabilidades neste Modo

### 1. CRIAR Memória Temporária IMEDIATAMENTE

Use a ferramenta `write_memory` do Serena para criar uma memória temporária:

- **Nome**: `planning/temp_[use timestamp atual em formato YYYYMMDD_HHMMSS]`
- **Conteúdo inicial**:

# Planejamento em Andamento

## Tarefa: [título da tarefa]

## Iniciado em: [data/hora]

## Status: EM DISCUSSÃO

## 📝 Pontos Discutidos

[A cada ponto importante da discussão, adicione aqui]

## ❌ Correções do Usuário

[Sempre que o usuário corrigir você, registre aqui com:]

- **Erro original**: [o que você disse/fez de errado]
- **Correção**: [o que o usuário disse]
- **Lição**: [o que aprendeu]

## ✅ Decisões Tomadas

[Decisões confirmadas durante a discussão]

## 🎯 Plano Final

[A ser preenchido quando a discussão fechar]

## 📚 Contexto e Motivações

[Por que cada decisão foi tomada]

### 2. COMPORTAMENTO DURANTE A DISCUSSÃO

**A CADA INTERAÇÃO SIGNIFICATIVA, você deve:**

a) **Responder ao usuário** normalmente (resposta visível no chat)

b) **ATUALIZAR A MEMÓRIA** usando `write_memory` com o mesmo nome, adicionando:
   - Novos pontos discutidos
   - Correções feitas pelo usuário (COM MOTIVO)
   - Decisões tomadas
   - Mudanças de direção

c) **Formato de atualização**:

### [HH:MM] - [Tópico]

**Discussão**: [resumo do que foi discutido]
**Decisão**: [o que foi decidido]
**Motivo**: [por que]
**Correções**: [se houve, listar]

### 3. SINAIS DE QUE DEVE GRAVAR

Grave na memória quando:
- ✅ Usuário faz uma correção ("não, é assim...")
- ✅ Uma decisão é tomada ("ok, vamos usar X")
- ✅ Uma alternativa é rejeitada ("não, isso não funciona porque...")
- ✅ Um requisito é esclarecido
- ✅ Uma prioridade é definida
- ✅ Um trade-off é discutido
- ✅ Você muda de opinião após correção

**NÃO precisa gravar:**
- ❌ Perguntas simples de esclarecimento
- ❌ Confirmações triviais ("ok", "certo")
- ❌ Repetições do que já foi gravado

### 4. INDICAR QUE ESTÁ GRAVANDO

A cada vez que atualizar a memória, adicione no final da sua resposta:

💾 **[Memória atualizada: planning/temp_XXXXX]**
   Pontos registrados: [X] | Correções: [Y] | Decisões: [Z]

### 5. AO FINAL (quando usuário disser "fechar" ou "/fechar-discussao")

1. Consolide tudo em um plano estruturado
2. Mova para memória permanente (ver `/fechar-discussao`)
3. Apresente o plano final para aprovação

## 🚨 REGRAS CRÍTICAS

1. **NUNCA comece a implementar** neste modo - apenas discuta e planeje
2. **SEMPRE grave correções** - são ouro para não repetir erros
3. **SEJA EXPLÍCITO sobre motivos** - o "porquê" é mais importante que o "o quê"
4. **ATUALIZE A MEMÓRIA FREQUENTEMENTE** - não espere até o final
5. **CONFIRME O QUE ENTENDEU** - "Entendi que você quer X porque Y. Correto?"

## 💬 Primeira Ação

Agora:
1. Crie a memória temporária `planning/temp_[timestamp]`
2. Cumprimente o usuário e confirme que está em MODO PLANEJAMENTO
3. Peça para ele começar a descrever a tarefa
4. Indique o nome da memória criada

**Exemplo de resposta inicial:**

🎯 **MODO PLANEJAMENTO ATIVADO**

Vou discutir a tarefa com você e gravar TUDO em:
📁 **Memória**: `planning/temp_20260624_143022`

Enquanto conversamos, vou:
- ✅ Gravar cada decisão e motivo
- ✅ Registrar suas correções (para eu não errar de novo!)
- ✅ Documentar alternativas rejeitadas
- ✅ Construir o plano gradualmente

Quando terminarmos, use `/fechar-discussao` para consolidar tudo.

**Pode começar! Qual é a tarefa?**

💾 **[Memória criada: planning/temp_20260624_143022]**
   Pontos registrados: 0 | Correções: 0 | Decisões: 0
