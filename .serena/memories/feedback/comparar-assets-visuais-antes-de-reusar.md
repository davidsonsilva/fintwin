Antes de reaproveitar um asset visual já existente no código (ícone, imagem, ilustração) para
uma nova UI, **comparar via Read a imagem real do arquivo** contra a referência do usuário —
não assumir que "já existe um X.png com esse nome, deve ser o certo".

**Why**: na sessão de 2026-07-27, reusei `public/agent-icon.png` (já usado na sidebar) para o
avatar do card de insight do dashboard, sem abrir e comparar visualmente contra a referência do
usuário. Era um robô completamente diferente (metálico/branco vs. o verde/ciano da referência em
`imagens/icone-robot.png` e `imagens/screenshots/Card-Como-deve-ser.png`). O usuário pegou o erro
("vc tem a imagem do robo na pasta imagens e me cria uma imagem nada a ver?").

**How to apply**: sempre que for usar/reaproveitar um asset de imagem para bater com uma
referência visual, usar o `Read` tool nos dois arquivos (o que vou usar + a referência) e
comparar antes de escrever o `<Image src=.../>` no código. Isso vale tanto para assets novos
quanto para assets "já existentes no projeto" — a existência prévia não é garantia de que é o
correto.