/*
 * Copyright (C) 2026 Davidson Silva
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, version 3 of the License.
 */

import type { ElementType, HTMLAttributes, ReactNode } from "react";

import type { CardVariantProps } from "./cardVariants";

/*
 * Contrato da moldura. Nenhuma destas props descreve conteúdo (valor, métrica,
 * evento, gráfico): isso pertence ao componente concreto de cada card.
 */

export type CardRootProps = HTMLAttributes<HTMLElement> &
  CardVariantProps & {
    as?: ElementType;
    children: ReactNode;
    className?: string;
  };

export type CardHeaderProps = {
  icon?: ReactNode;
  title: ReactNode;
  help?: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export type CardContentProps = {
  children: ReactNode;
  className?: string;
};

export type CardFooterProps = {
  children: ReactNode;
  className?: string;
};
