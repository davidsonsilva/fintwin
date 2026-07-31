/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import { Card as CardSurface } from "./Card";
import { CardContent } from "./CardContent";
import { CardFooter } from "./CardFooter";
import { CardHeader } from "./CardHeader";
import { CardRoot } from "./CardRoot";

/*
 * `Card` continua chamável como antes (`<Card as="article" interactive>`), que é
 * como os cards ainda não migrados o usam — só a superfície, sem estrutura.
 *
 * `Card.Root/Header/Content/Footer` é a moldura composta, usada pelos cards já
 * migrados. Quando todos migrarem, `CardSurface` some e `Card` vira `CardRoot`.
 */
export const Card = Object.assign(CardSurface, {
  Root: CardRoot,
  Header: CardHeader,
  Content: CardContent,
  Footer: CardFooter,
});

export { CardContent, CardFooter, CardHeader, CardRoot };
export { cardVariants, type CardVariantProps } from "./cardVariants";
export type {
  CardContentProps,
  CardFooterProps,
  CardHeaderProps,
  CardRootProps,
} from "./card.types";
