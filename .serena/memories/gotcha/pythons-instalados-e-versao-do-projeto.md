# Python: qual versão o projeto usa, e por que a máquina tem seis

## O que importa saber antes de mexer

**O FinTwin roda em Python 3.12, fixado em dois lugares:**

```toml
requires-python = ">=3.12,<3.13"    # apps/api/pyproject.toml — exclui 3.13 e 3.14
```
```dockerfile
FROM python:3.12-slim                # apps/api/Dockerfile — é o que serve a API de fato
```

A venv em `apps/api/.venv` está em **3.12.10** e **funciona**: `pytest` dá 201 passed em ~10s.
Nada quebrado. Não "consertar".

O **3.14.3 é o default do sistema do Davidson**, não do projeto. `py -0` marca ele com `*`.
Isso não conflita com nada — são coisas separadas.

## ⚠️ Não confundir com o NOT_VERIFIED do Meta Harness

O Codex reporta `pytest` como NOT_VERIFIED em toda rodada. **Não é venv quebrada.** É
`"sandbox": "read-only"` no `.meta-harness/config.json`: o sandbox não alcança o interpretador
fora do diretório do projeto nem consegue escrever `.pytest_cache`. O próprio
`prompts/codex-review.md` manda reportar assim. Comportamento projetado.

Eu já errei isso uma vez nesta base de código: li o relatório e afirmei "a venv está quebrada,
Python ausente" sem rodar nada. Rodar leva 10 segundos.

## Inventário (levantado em 2026-07-31)

| Onde | Origem | Estado |
|---|---|---|
| `C:\Python314\` | instalador python.org (all users) | default do sistema (`*` no `py -0`) |
| `AppData\Local\Programs\Python\Python312\` | instalador python.org (por usuário) | **é o do FinTwin** |
| `AppData\Local\Programs\Python\Python310\` | instalador python.org (por usuário) | 👻 **fantasma**: sobraram `Lib/`, `Scripts/`, `share/`, mas o `python.exe` sumiu. Registro do launcher ficou → `py -0` anuncia um 3.10 que não existe |
| `AppData\Roaming\uv\python\cpython-3.14.3-...` | baixado pelo **uv** | ok |
| `AppData\Roaming\uv\python\cpython-3.12.13-...` | baixado pelo **uv** | ok, nem aparece no `py -0` |
| `WindowsApps\python.exe` | alias da Microsoft Store | **não é Python** — redireciona para a Store |

Causa do acúmulo: três mecanismos instalando no mesmo perfil sem saberem um do outro —
instalador do python.org (3×), uv (2 interpretadores) e o alias da Store (ligado por padrão).
O `uv` também está duplicado: `~/.local/bin/uv.exe` e
`AppData\Roaming\Python\Python314\Scripts\uv.exe`.

## Decisão do Davidson (2026-07-31)

**Deixar como está.** Palavras dele: *"deixa como está, depois resolvemos isso com calma. não
vamos misturar as coisas."* Nenhuma limpeza foi feita, e não deve ser feita junto com outra
tarefa.

Quando ele retomar, a ordem seria: (1) desinstalar o 3.10 pelo Painel de Controle — para tirar
o registro do launcher — e só então apagar a pasta órfã; (2) desligar os aliases da Store em
Configurações › Aplicativos › Configurações avançadas; (3) escolher um dono entre python.org e
uv, em vez de manter os dois gerenciando versões.

**Migrar o projeto para 3.14 seria outra coisa** — mudar `requires-python`, trocar a base do
Dockerfile e validar as 7 dependências (risco concreto em `psycopg[binary]`). Não foi pedido.
