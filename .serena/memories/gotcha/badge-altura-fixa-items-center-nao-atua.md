# Badge com altura fixa: `items-center` não centraliza nada

`badgeVariants` (`apps/web/src/design-system/components/Badge/badgeVariants.ts`) combina
`min-h-[22px]`, `py-[2px]`, `border` e `leading-4` sobre fonte de 12px. A soma fecha exata:
16px de line-box + 4 de padding + 2 de borda = 22px. Como o elemento já tem a altura mínima,
**`items-center` fica sem folga para atuar** — a posição vertical do texto passa a ser
determinada só pelo padding.

O padding é simétrico, mas a métrica da fonte não: o espaço reservado para a descendente
fica vazio em rótulos que não têm nenhuma. No Registro de recomendações, nenhum dos seis
rótulos tem descendente (Pendente, Aprovada, Rejeitada, Expirada, Substituída,
Desatualizada), então sobra espaço embaixo e o texto sobe visivelmente.

Corrigido em `716ff9f` com `pt-[3px] pb-px` **no ponto de chamada**, não em `badgeVariants`:
o primitivo é compartilhado e alterá-lo mexeria em toda tela que usa Badge. A causa
continua no primitivo — se for corrigir lá, revisar as outras telas junto.

## Como medir sem ficar garimpando pixel em captura de página

Screenshot da página inteira força adivinhar onde a pílula começa e termina, e o resultado
oscila conforme o limiar de luminância escolhido. O caminho confiável:

1. `locator.screenshot()` no **próprio elemento** — a imagem já é exatamente a border-box.
2. `test.use({ deviceScaleFactor: 8 })` para o antialiasing não dominar a medida.
3. Para escolher entre candidatos de padding, injetar o estilo no elemento com
   `locator.evaluate((el, css) => el.setAttribute("style", css), css)` e tirar um screenshot
   por candidato **na mesma execução** — evita um rebuild do container por tentativa.

Ver também `mem:gotcha/container-query-mede-content-box`.
