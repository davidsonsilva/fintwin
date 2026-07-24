## 1. CSS-base do FinTwin AI

Esse CSS pode ser usado com React, Next.js, Vite ou HTML tradicional. Ele utiliza classes sem dependência de Tailwind.

```css
/* =========================================================
   FINTWIN AI — DESIGN SYSTEM
   Gêmeo Financeiro Pessoal
   ========================================================= */

:root {
  /* Backgrounds */
  --ft-bg-page: #050d18;
  --ft-bg-sidebar: #07111e;
  --ft-bg-surface: #0b1726;
  --ft-bg-surface-soft: #0e1c2d;
  --ft-bg-surface-hover: #12243a;
  --ft-bg-elevated: rgba(14, 28, 45, 0.88);

  /* Brand */
  --ft-primary: #22e6b1;
  --ft-primary-strong: #00c896;
  --ft-primary-soft: rgba(34, 230, 177, 0.12);

  --ft-secondary: #44d8f3;
  --ft-secondary-soft: rgba(68, 216, 243, 0.12);

  --ft-purple: #9a5cff;
  --ft-purple-strong: #7c3aed;
  --ft-purple-soft: rgba(154, 92, 255, 0.14);

  /* Semantic */
  --ft-success: #27dd8a;
  --ft-success-soft: rgba(39, 221, 138, 0.12);

  --ft-warning: #ffb020;
  --ft-warning-soft: rgba(255, 176, 32, 0.13);

  --ft-danger: #ff525d;
  --ft-danger-soft: rgba(255, 82, 93, 0.13);

  --ft-info: #4e9cff;
  --ft-info-soft: rgba(78, 156, 255, 0.13);

  /* Text */
  --ft-text-primary: #f6f8fb;
  --ft-text-secondary: #b3bdca;
  --ft-text-muted: #7f8b9b;
  --ft-text-disabled: #536071;

  /* Borders */
  --ft-border: rgba(157, 178, 204, 0.15);
  --ft-border-hover: rgba(157, 178, 204, 0.28);
  --ft-border-primary: rgba(34, 230, 177, 0.45);

  /* Shadows */
  --ft-shadow-sm: 0 8px 24px rgba(0, 0, 0, 0.18);
  --ft-shadow-md: 0 18px 48px rgba(0, 0, 0, 0.28);
  --ft-shadow-primary: 0 0 28px rgba(34, 230, 177, 0.12);
  --ft-shadow-purple: 0 0 28px rgba(154, 92, 255, 0.14);

  /* Radius */
  --ft-radius-sm: 10px;
  --ft-radius-md: 14px;
  --ft-radius-lg: 18px;
  --ft-radius-xl: 24px;
  --ft-radius-pill: 999px;

  /* Spacing */
  --ft-space-1: 4px;
  --ft-space-2: 8px;
  --ft-space-3: 12px;
  --ft-space-4: 16px;
  --ft-space-5: 20px;
  --ft-space-6: 24px;
  --ft-space-8: 32px;
  --ft-space-10: 40px;

  /* Layout */
  --ft-sidebar-width: 270px;
  --ft-header-height: 92px;

  /* Motion */
  --ft-transition-fast: 150ms ease;
  --ft-transition-base: 240ms ease;
  --ft-transition-slow: 400ms ease;
}

/* =========================================================
   RESET
   ========================================================= */

*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  color-scheme: dark;
  scroll-behavior: smooth;
}

body {
  min-width: 320px;
  min-height: 100vh;
  margin: 0;
  overflow-x: hidden;

  font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;

  color: var(--ft-text-primary);

  background:
    radial-gradient(
      circle at 82% 12%,
      rgba(28, 106, 144, 0.16),
      transparent 30%
    ),
    radial-gradient(
      circle at 18% 92%,
      rgba(0, 200, 150, 0.08),
      transparent 30%
    ),
    var(--ft-bg-page);

  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

button,
input,
select,
textarea {
  font: inherit;
}

button,
a {
  -webkit-tap-highlight-color: transparent;
}

button {
  color: inherit;
}

a {
  color: inherit;
  text-decoration: none;
}

/* =========================================================
   APPLICATION SHELL
   ========================================================= */

.ft-app {
  display: grid;
  grid-template-columns: var(--ft-sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
}

.ft-main {
  min-width: 0;
  padding: 0 var(--ft-space-8) var(--ft-space-8);
}

.ft-content {
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
}

/* =========================================================
   SIDEBAR
   ========================================================= */

.ft-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 24px 18px;

  overflow-y: auto;

  background:
    linear-gradient(
      180deg,
      rgba(7, 17, 30, 0.98),
      rgba(4, 12, 22, 0.98)
    );

  border-right: 1px solid var(--ft-border);
}

.ft-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 4px 30px;
}

.ft-brand-logo {
  display: grid;
  width: 48px;
  height: 48px;

  place-items: center;

  color: var(--ft-primary);
  background: var(--ft-primary-soft);
  border: 1px solid var(--ft-border-primary);
  border-radius: 16px;
  box-shadow: var(--ft-shadow-primary);
}

.ft-brand-title {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.ft-brand-title span {
  color: var(--ft-primary);
}

.ft-brand-subtitle {
  margin: 4px 0 0;
  color: var(--ft-text-secondary);
  font-size: 13px;
}

.ft-nav {
  display: grid;
  gap: 6px;
}

.ft-nav-item {
  display: flex;
  align-items: center;
  gap: 13px;

  min-height: 48px;
  padding: 0 14px;

  color: var(--ft-text-secondary);

  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--ft-radius-md);

  cursor: pointer;

  transition:
    color var(--ft-transition-fast),
    background var(--ft-transition-fast),
    border-color var(--ft-transition-fast),
    transform var(--ft-transition-fast);
}

.ft-nav-item:hover {
  color: var(--ft-text-primary);
  background: rgba(255, 255, 255, 0.035);
  transform: translateX(2px);
}

.ft-nav-item.is-active {
  color: var(--ft-text-primary);
  background:
    linear-gradient(
      90deg,
      rgba(0, 200, 150, 0.18),
      rgba(0, 200, 150, 0.06)
    );

  border-color: var(--ft-border-primary);
  box-shadow: inset 3px 0 0 var(--ft-primary);
}

.ft-nav-icon {
  display: grid;
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  place-items: center;
}

.ft-sidebar-panel {
  margin-top: 22px;
  padding: 18px;

  background:
    linear-gradient(
      145deg,
      rgba(154, 92, 255, 0.16),
      rgba(69, 26, 110, 0.2)
    );

  border: 1px solid rgba(154, 92, 255, 0.48);
  border-radius: var(--ft-radius-lg);
  box-shadow: var(--ft-shadow-purple);
}

.ft-sidebar-panel--ai {
  background:
    linear-gradient(
      145deg,
      rgba(34, 230, 177, 0.08),
      rgba(68, 216, 243, 0.05)
    );

  border-color: rgba(68, 216, 243, 0.4);
}

.ft-sidebar-panel-title {
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 700;
}

.ft-sidebar-panel-text {
  margin: 0 0 16px;
  color: var(--ft-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

/* =========================================================
   HEADER
   ========================================================= */

.ft-header {
  display: flex;
  min-height: var(--ft-header-height);

  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.ft-header-left {
  display: flex;
  align-items: center;
  gap: 22px;
}

.ft-menu-button {
  display: grid;
  width: 42px;
  height: 42px;

  place-items: center;

  background: transparent;
  border: 1px solid transparent;
  border-radius: 12px;
  cursor: pointer;

  transition:
    background var(--ft-transition-fast),
    border-color var(--ft-transition-fast);
}

.ft-menu-button:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--ft-border);
}

.ft-page-title {
  margin: 0;
  font-size: clamp(24px, 2vw, 32px);
  font-weight: 800;
  letter-spacing: -0.04em;
}

.ft-page-description {
  margin: 5px 0 0;
  color: var(--ft-text-secondary);
  font-size: 14px;
}

.ft-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ft-icon-button {
  position: relative;

  display: grid;
  width: 42px;
  height: 42px;

  place-items: center;

  color: var(--ft-text-secondary);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 12px;

  cursor: pointer;
  transition: all var(--ft-transition-fast);
}

.ft-icon-button:hover {
  color: var(--ft-text-primary);
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--ft-border);
}

.ft-notification-dot {
  position: absolute;
  top: 8px;
  right: 8px;

  width: 7px;
  height: 7px;

  background: var(--ft-primary);
  border: 2px solid var(--ft-bg-page);
  border-radius: 50%;
}

/* =========================================================
   GRID
   ========================================================= */

.ft-grid {
  display: grid;
  gap: 14px;
}

.ft-grid--metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.ft-grid--indicators {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.ft-grid--analytics {
  grid-template-columns: 1.05fr 1.05fr 1fr;
}

.ft-col-span-2 {
  grid-column: span 2;
}

.ft-section {
  margin-top: 14px;
}

/* =========================================================
   CARDS
   ========================================================= */

.ft-card {
  position: relative;

  min-width: 0;
  padding: 20px;

  background:
    linear-gradient(
      145deg,
      rgba(15, 31, 49, 0.96),
      rgba(9, 23, 38, 0.98)
    );

  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-lg);
  box-shadow: var(--ft-shadow-sm);

  overflow: hidden;

  transition:
    transform var(--ft-transition-base),
    border-color var(--ft-transition-base),
    box-shadow var(--ft-transition-base);
}

.ft-card::before {
  position: absolute;
  inset: 0;

  pointer-events: none;
  content: "";

  background:
    linear-gradient(
      120deg,
      rgba(255, 255, 255, 0.025),
      transparent 30%
    );

  opacity: 0;
  transition: opacity var(--ft-transition-base);
}

.ft-card:hover {
  border-color: var(--ft-border-hover);
  box-shadow: var(--ft-shadow-md);
  transform: translateY(-2px);
}

.ft-card:hover::before {
  opacity: 1;
}

.ft-card--compact {
  padding: 16px 18px;
}

.ft-card--disabled {
  opacity: 0.62;
}

.ft-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.ft-card-title {
  margin: 0;
  font-size: 17px;
  font-weight: 750;
  letter-spacing: -0.02em;
}

.ft-card-subtitle {
  margin: 6px 0 0;
  color: var(--ft-text-secondary);
  font-size: 13px;
}

.ft-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-top: 20px;
  padding-top: 16px;

  color: #b49cff;
  border-top: 1px solid var(--ft-border);
}

/* =========================================================
   METRIC CARDS
   ========================================================= */

.ft-metric-card {
  display: flex;
  min-height: 132px;
  align-items: flex-start;
  gap: 16px;
}

.ft-metric-icon {
  display: grid;
  width: 48px;
  height: 48px;

  flex: 0 0 auto;
  place-items: center;

  border: 1px solid transparent;
  border-radius: 15px;
}

.ft-metric-icon--primary {
  color: var(--ft-primary);
  background: var(--ft-primary-soft);
  border-color: rgba(34, 230, 177, 0.16);
}

.ft-metric-icon--warning {
  color: var(--ft-warning);
  background: var(--ft-warning-soft);
}

.ft-metric-icon--purple {
  color: #c178ff;
  background: var(--ft-purple-soft);
}

.ft-metric-icon--info {
  color: var(--ft-secondary);
  background: var(--ft-secondary-soft);
}

.ft-metric-content {
  min-width: 0;
}

.ft-metric-label {
  margin: 3px 0 10px;
  color: var(--ft-text-secondary);
  font-size: 13px;
}

.ft-metric-value {
  margin: 0;
  font-size: clamp(25px, 2vw, 32px);
  font-weight: 800;
  letter-spacing: -0.035em;
}

.ft-metric-unit {
  margin-left: 5px;
  font-size: 14px;
  font-weight: 650;
}

.ft-metric-helper {
  margin: 8px 0 0;
  color: var(--ft-text-secondary);
  font-size: 13px;
}

/* =========================================================
   STATUS CARDS
   ========================================================= */

.ft-status-card {
  display: flex;
  min-height: 104px;
  align-items: flex-start;
  gap: 13px;
}

.ft-status-icon {
  display: grid;
  width: 38px;
  height: 38px;

  flex: 0 0 auto;
  place-items: center;

  border-radius: 12px;
}

.ft-status-title {
  margin: 1px 0 6px;
  font-size: 14px;
  font-weight: 700;
}

.ft-status-description {
  margin: 0;
  color: var(--ft-text-secondary);
  font-size: 13px;
}

.ft-badge {
  display: inline-flex;
  min-height: 24px;

  align-items: center;

  margin-top: 10px;
  padding: 3px 10px;

  color: var(--ft-text-secondary);
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid var(--ft-border);
  border-radius: 7px;

  font-size: 11px;
}

/* =========================================================
   BUTTONS
   ========================================================= */

.ft-button {
  display: inline-flex;
  min-height: 42px;

  align-items: center;
  justify-content: center;
  gap: 9px;

  padding: 0 16px;

  font-weight: 700;

  border: 1px solid transparent;
  border-radius: 11px;

  cursor: pointer;

  transition:
    transform var(--ft-transition-fast),
    background var(--ft-transition-fast),
    border-color var(--ft-transition-fast),
    box-shadow var(--ft-transition-fast);
}

.ft-button:hover {
  transform: translateY(-1px);
}

.ft-button:active {
  transform: translateY(0);
}

.ft-button--primary {
  color: #001d17;

  background:
    linear-gradient(
      135deg,
      var(--ft-primary),
      var(--ft-primary-strong)
    );

  box-shadow: 0 8px 24px rgba(0, 200, 150, 0.2);
}

.ft-button--primary:hover {
  box-shadow: 0 10px 30px rgba(0, 200, 150, 0.3);
}

.ft-button--secondary {
  color: var(--ft-text-primary);
  background: rgba(255, 255, 255, 0.035);
  border-color: var(--ft-border);
}

.ft-button--secondary:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: var(--ft-border-hover);
}

.ft-button--purple {
  color: white;

  background:
    linear-gradient(
      135deg,
      var(--ft-purple),
      var(--ft-purple-strong)
    );

  box-shadow: 0 9px 28px rgba(124, 58, 237, 0.24);
}

.ft-button--ghost-purple {
  color: #bda9ff;
  background: rgba(94, 71, 170, 0.1);
  border-color: rgba(130, 108, 255, 0.38);
}

.ft-button--full {
  width: 100%;
}

/* =========================================================
   FINANCIAL EVENTS
   ========================================================= */

.ft-event-list {
  display: grid;
  gap: 12px;
}

.ft-event-item {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;

  padding: 14px 16px;

  background: rgba(17, 38, 56, 0.75);
  border: 1px solid var(--ft-border);
  border-radius: 12px;
}

.ft-event-date {
  display: grid;
  width: 44px;
  height: 50px;

  place-items: center;

  color: var(--ft-primary);
  font-weight: 800;
  line-height: 1;

  background: var(--ft-primary-soft);
  border-radius: 10px;
}

.ft-event-date small {
  font-size: 10px;
  font-weight: 700;
}

.ft-event-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
}

.ft-event-description {
  margin: 5px 0 0;
  color: var(--ft-text-secondary);
  font-size: 13px;
}

.ft-event-amount {
  color: var(--ft-success);
  font-size: 14px;
  font-weight: 800;
}

/* =========================================================
   CHART AREAS
   ========================================================= */

.ft-chart-container {
  position: relative;
  min-height: 250px;
}

.ft-chart-legend {
  display: grid;
  gap: 11px;
}

.ft-legend-item {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;

  color: var(--ft-text-secondary);
  font-size: 12px;
}

.ft-legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* =========================================================
   AI INSIGHT
   ========================================================= */

.ft-ai-insight {
  display: grid;
  grid-template-columns: 94px minmax(0, 1fr) auto;
  align-items: center;
  gap: 22px;

  padding: 20px 24px;

  background:
    radial-gradient(
      circle at 10% 50%,
      rgba(34, 230, 177, 0.15),
      transparent 28%
    ),
    linear-gradient(
      100deg,
      rgba(0, 96, 73, 0.26),
      rgba(4, 44, 39, 0.72)
    );

  border: 1px solid rgba(34, 230, 177, 0.42);
  border-radius: var(--ft-radius-lg);
  box-shadow: var(--ft-shadow-primary);
}

.ft-ai-avatar {
  display: grid;
  width: 76px;
  height: 76px;

  place-items: center;

  background:
    radial-gradient(
      circle,
      rgba(34, 230, 177, 0.34),
      rgba(34, 230, 177, 0.04)
    );

  border: 1px solid rgba(34, 230, 177, 0.48);
  border-radius: 50%;
}

.ft-ai-title {
  margin: 0 0 8px;
  color: var(--ft-primary);
  font-size: 17px;
  font-weight: 800;
}

.ft-ai-text {
  max-width: 900px;
  margin: 0;

  color: var(--ft-text-primary);
  font-size: 14px;
  line-height: 1.7;
}

/* =========================================================
   FORMS / ONBOARDING
   ========================================================= */

.ft-onboarding {
  width: min(100%, 1180px);
  margin: 0 auto;
  padding: 32px 0;
}

.ft-stepper {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 24px;
}

.ft-step {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.ft-step-indicator {
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: var(--ft-radius-pill);
  overflow: hidden;
}

.ft-step.is-complete .ft-step-indicator,
.ft-step.is-active .ft-step-indicator {
  background:
    linear-gradient(
      90deg,
      var(--ft-primary),
      var(--ft-secondary)
    );
}

.ft-step-label {
  color: var(--ft-text-muted);
  font-size: 11px;
  white-space: nowrap;
}

.ft-step.is-active .ft-step-label {
  color: var(--ft-primary);
  font-weight: 700;
}

.ft-form-card {
  padding: 28px;
}

.ft-form-title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 800;
}

.ft-form-description {
  margin: 0 0 26px;
  color: var(--ft-text-secondary);
}

.ft-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.ft-field {
  display: grid;
  gap: 8px;
}

.ft-field--full {
  grid-column: 1 / -1;
}

.ft-label {
  color: var(--ft-text-secondary);
  font-size: 13px;
  font-weight: 650;
}

.ft-input,
.ft-select,
.ft-textarea {
  width: 100%;
  min-height: 46px;
  padding: 0 14px;

  color: var(--ft-text-primary);
  background: rgba(3, 12, 22, 0.58);
  border: 1px solid var(--ft-border);
  border-radius: 11px;
  outline: none;

  transition:
    border-color var(--ft-transition-fast),
    box-shadow var(--ft-transition-fast),
    background var(--ft-transition-fast);
}

.ft-textarea {
  min-height: 110px;
  padding-top: 13px;
  resize: vertical;
}

.ft-input::placeholder,
.ft-textarea::placeholder {
  color: var(--ft-text-disabled);
}

.ft-input:focus,
.ft-select:focus,
.ft-textarea:focus {
  background: rgba(3, 12, 22, 0.82);
  border-color: var(--ft-primary);
  box-shadow: 0 0 0 4px rgba(34, 230, 177, 0.1);
}

.ft-form-actions {
  display: flex;
  justify-content: space-between;
  gap: 14px;

  margin-top: 28px;
  padding-top: 22px;

  border-top: 1px solid var(--ft-border);
}

/* =========================================================
   REVIEW
   ========================================================= */

.ft-review-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.ft-review-item {
  padding: 14px 16px;

  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--ft-border);
  border-radius: 12px;
}

.ft-review-label {
  margin: 0 0 6px;
  color: var(--ft-text-muted);
  font-size: 12px;
}

.ft-review-value {
  margin: 0;
  color: var(--ft-text-primary);
  font-weight: 700;
}

/* =========================================================
   SCROLLBAR
   ========================================================= */

* {
  scrollbar-width: thin;
  scrollbar-color: rgba(113, 136, 161, 0.44) transparent;
}

*::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

*::-webkit-scrollbar-track {
  background: transparent;
}

*::-webkit-scrollbar-thumb {
  background: rgba(113, 136, 161, 0.4);
  border-radius: var(--ft-radius-pill);
}

*::-webkit-scrollbar-thumb:hover {
  background: rgba(113, 136, 161, 0.65);
}

/* =========================================================
   ACCESSIBILITY
   ========================================================= */

:focus-visible {
  outline: 2px solid var(--ft-primary);
  outline-offset: 3px;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}

/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 1280px) {
  .ft-grid--metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ft-grid--analytics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ft-grid--analytics > :last-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 1024px) {
  .ft-app {
    grid-template-columns: 1fr;
  }

  .ft-sidebar {
    position: fixed;
    z-index: 50;
    top: 0;
    left: 0;

    width: var(--ft-sidebar-width);

    transform: translateX(-102%);
    transition: transform var(--ft-transition-base);
  }

  .ft-sidebar.is-open {
    transform: translateX(0);
  }

  .ft-main {
    padding-inline: 20px;
  }

  .ft-grid--indicators {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ft-ai-insight {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .ft-ai-insight .ft-button {
    grid-column: 1 / -1;
  }
}

@media (max-width: 720px) {
  .ft-main {
    padding-inline: 14px;
    padding-bottom: 20px;
  }

  .ft-header {
    align-items: flex-start;
    padding: 18px 0;
  }

  .ft-header-actions {
    display: none;
  }

  .ft-grid--metrics,
  .ft-grid--indicators,
  .ft-grid--analytics,
  .ft-form-grid,
  .ft-review-grid {
    grid-template-columns: 1fr;
  }

  .ft-col-span-2 {
    grid-column: auto;
  }

  .ft-stepper {
    display: flex;
    overflow-x: auto;
    padding-bottom: 8px;
  }

  .ft-step {
    min-width: 100px;
  }

  .ft-form-card {
    padding: 20px;
  }

  .ft-form-actions {
    flex-direction: column-reverse;
  }

  .ft-form-actions .ft-button {
    width: 100%;
  }

  .ft-event-item {
    grid-template-columns: 48px minmax(0, 1fr);
  }

  .ft-event-amount {
    grid-column: 2;
  }

  .ft-ai-insight {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .ft-ai-avatar {
    margin: 0 auto;
  }
}
```

## 2. Exemplo de estrutura HTML/JSX

```jsx
<div className="ft-app">
  <aside className="ft-sidebar">
    <div className="ft-brand">
      <div className="ft-brand-logo">{/* Logo */}</div>

      <div>
        <h1 className="ft-brand-title">
          FinTwin <span>AI</span>
        </h1>

        <p className="ft-brand-subtitle">
          Gêmeo Financeiro Pessoal
        </p>
      </div>
    </div>

    <nav className="ft-nav">
      <a className="ft-nav-item is-active" href="/">
        <span className="ft-nav-icon">{/* Ícone */}</span>
        Início
      </a>

      <a className="ft-nav-item" href="/perfil">
        <span className="ft-nav-icon">{/* Ícone */}</span>
        Perfil
      </a>

      <a className="ft-nav-item" href="/contas">
        <span className="ft-nav-icon">{/* Ícone */}</span>
        Contas e saldos
      </a>
    </nav>
  </aside>

  <main className="ft-main">
    <div className="ft-content">
      <header className="ft-header">
        <div className="ft-header-left">
          <button className="ft-menu-button">
            {/* Menu */}
          </button>

          <div>
            <h2 className="ft-page-title">Olá, Davidson! 👋</h2>
            <p className="ft-page-description">
              Aqui está o panorama da sua vida financeira.
            </p>
          </div>
        </div>

        <div className="ft-header-actions">
          <button className="ft-button ft-button--secondary">
            Sincronizar dados
          </button>
        </div>
      </header>

      <section className="ft-grid ft-grid--metrics">
        <article className="ft-card ft-metric-card">
          <div className="ft-metric-icon ft-metric-icon--primary">
            {/* Ícone */}
          </div>

          <div className="ft-metric-content">
            <p className="ft-metric-label">
              Saldo líquido disponível
            </p>

            <p className="ft-metric-value">
              12.500,00
              <span className="ft-metric-unit">BRL</span>
            </p>

            <p className="ft-metric-helper">
              Atualizado hoje
            </p>
          </div>
        </article>
      </section>
    </div>
  </main>
</div>
```

# 3. Prompt definitivo para o agente implementar

```md
# MISSÃO

Atue como um Senior Frontend Engineer, Product Designer e especialista em aplicações financeiras.

Sua tarefa é modernizar completamente a interface Web do projeto FinTwin AI, também chamado de Gêmeo Financeiro Pessoal.

O projeto já possui um MVP funcional, onboarding financeiro e dashboard com dados reais ou demonstrativos. A implementação deve preservar integralmente o domínio, os casos de uso, as regras financeiras, os cálculos, as APIs e as Vertical Slices já existentes.

Não recrie o projeto do zero.

Primeiro, investigue o código atual, identifique a stack, as páginas, rotas, componentes, serviços, estados, testes e contratos existentes. Depois faça a modernização visual de maneira incremental e segura.

---

# OBJETIVO DO PRODUTO

O FinTwin AI é uma plataforma Web visual de simulação, prevenção e acompanhamento financeiro pessoal.

O sistema representa um gêmeo financeiro digital do usuário, capaz de:

- consolidar sua situação financeira;
- acompanhar saldo líquido;
- calcular obrigações mensais;
- analisar comprometimento da renda;
- acompanhar metas;
- projetar autonomia financeira;
- detectar déficits futuros;
- identificar fragilidades financeiras;
- exibir eventos financeiros futuros;
- gerar insights personalizados;
- futuramente simular decisões financeiras.

A experiência precisa transmitir:

- confiança;
- inteligência;
- segurança;
- clareza;
- visão de futuro;
- tecnologia;
- controle financeiro.

---

# PRINCÍPIO FUNDAMENTAL

Não alterar as regras de negócio para acomodar a interface.

A interface deve consumir os casos de uso e view models existentes.

Não duplicar cálculos financeiros no frontend.

Não adicionar valores hardcoded em componentes quando os dados já existirem no domínio, API, store ou serviços.

Não misturar lógica de domínio com componentes visuais.

---

# DIREÇÃO VISUAL

Criar uma aplicação financeira premium em dark mode.

Referências conceituais:

- dashboards financeiros SaaS;
- interfaces de fintech;
- produtos de analytics;
- visual futurista moderado;
- inteligência artificial aplicada a finanças;
- design limpo e profissional.

Evitar:

- excesso de neon;
- aparência de videogame;
- cyberpunk exagerado;
- gradientes excessivos;
- efeitos que prejudiquem a leitura;
- textos pequenos;
- cards sem hierarquia;
- botões decorativos sem ação real;
- gráficos falsos;
- animações gratuitas.

---

# IDENTIDADE VISUAL

## Cores principais

Background principal:

- #050D18

Sidebar:

- #07111E

Cards:

- #0B1726
- #0E1C2D

Verde principal:

- #22E6B1

Verde forte:

- #00C896

Azul secundário:

- #44D8F3

Roxo:

- #9A5CFF

Sucesso:

- #27DD8A

Alerta:

- #FFB020

Perigo:

- #FF525D

Texto principal:

- #F6F8FB

Texto secundário:

- #B3BDCA

Texto desabilitado:

- #536071

Bordas:

- rgba(157, 178, 204, 0.15)

## Tipografia

Preferência:

- Inter

Fallback:

- system-ui
- Segoe UI
- sans-serif

Aplicar:

- títulos com peso entre 700 e 800;
- números financeiros com forte hierarquia;
- textos auxiliares discretos;
- boa legibilidade;
- tabular numbers nos valores financeiros, quando possível.

Use:

font-variant-numeric: tabular-nums;

---

# ARQUITETURA VISUAL

Criar um App Shell composto por:

1. Sidebar lateral fixa no desktop.
2. Sidebar colapsável em tablets e dispositivos móveis.
3. Cabeçalho da página.
4. Área principal responsiva.
5. Sistema de cards.
6. Área de insights do FinTwin AI.
7. Feedback visual de carregamento, erro e ausência de dados.

---

# SIDEBAR

A sidebar deve conter:

- logo do FinTwin AI;
- subtítulo “Gêmeo Financeiro Pessoal”;
- Início;
- Perfil;
- Contas e saldos;
- Rendas;
- Obrigações e despesas;
- Dívidas;
- Metas;
- Eventos futuros;
- Revisão.

O item da rota atual deve possuir:

- fundo verde translúcido;
- borda verde discreta;
- indicador visual lateral;
- ícone;
- contraste suficiente.

Adicionar um card inferior para o agente:

Título:

“IA FinTwin”

Texto:

“Pergunte algo sobre suas finanças para o seu gêmeo.”

Botão:

“Conversar com IA”

O botão só deve ser exibido como funcional quando existir ação implementada.

Caso o recurso ainda não exista, utilizar estado “Em breve” ou desabilitado, sem criar uma funcionalidade falsa.

---

# DASHBOARD PRINCIPAL

O dashboard deverá apresentar quatro métricas principais:

1. Saldo líquido disponível.
2. Obrigações mensais.
3. Comprometimento da renda.
4. Progresso da meta principal.

Cada card deve possuir:

- ícone;
- título;
- valor principal;
- unidade;
- texto auxiliar;
- estado de carregamento;
- estado de erro;
- tooltip explicativo;
- responsividade.

Utilizar formatação monetária para BRL com Intl.NumberFormat.

Exemplo:

R$ 12.500,00

Não formatar manualmente valores monetários.

---

# INDICADORES DO GÊMEO FINANCEIRO

Exibir cards para:

- Autonomia básica.
- Autonomia provável.
- Autonomia adversa.
- Próximo déficit previsto.
- Quantidade de fragilidades.

Quando uma funcionalidade ainda não estiver disponível, exibir claramente:

- “Disponível na VS-XX”;
- badge “Em breve”;
- estado visual desabilitado.

Não inventar dados para preencher funcionalidades futuras.

Quando a Vertical Slice correspondente estiver implementada, substituir automaticamente o placeholder pelos dados reais.

---

# EVENTOS FINANCEIROS FUTUROS

Criar um card chamado:

“Próximos eventos financeiros”

Cada evento deve apresentar:

- dia;
- mês;
- título;
- descrição;
- valor;
- tipo de evento;
- natureza de entrada ou saída;
- status;
- data completa em tooltip ou detalhe.

Entradas financeiras devem usar cor semântica de sucesso.

Saídas e obrigações devem usar cor de alerta ou perigo conforme criticidade.

Adicionar ação:

“Ver todos os eventos”

Essa ação deve navegar para a rota de eventos futuros.

---

# GRÁFICOS

Utilizar a biblioteca de gráficos já existente no projeto.

Caso nenhuma biblioteca esteja instalada, preferir:

- Recharts para React;
- Chart.js apenas se já fizer parte da stack.

Não instalar várias bibliotecas com a mesma finalidade.

Criar os seguintes gráficos:

## Distribuição das despesas

Tipo:

- donut chart.

Dados:

- despesas agrupadas por categoria.

Exibir:

- total mensal no centro;
- legenda;
- percentual;
- valor monetário;
- tooltip acessível.

## Evolução do saldo líquido

Tipo:

- line chart ou area chart.

Dados:

- histórico dos últimos seis meses;
- somente dados reais ou dados retornados pelo modo de demonstração.

Exibir:

- eixo temporal;
- eixo de valores;
- tooltip;
- valor mais recente;
- estado vazio quando não houver histórico suficiente.

## Comprometimento da renda

Tipo:

- gauge ou radial progress.

Exibir:

- percentual atual;
- classificação financeira;
- limite saudável;
- limite de atenção;
- limite crítico.

Não classificar apenas pela cor.

Exibir também texto e ícone.

---

# INSIGHT DO GÊMEO FINANCEIRO

Adicionar uma área de destaque no final do dashboard.

Título:

“Insight do seu Gêmeo Financeiro”

O conteúdo deve vir de:

1. regra determinística já existente;
2. serviço de recomendação;
3. agente de IA, quando implementado.

Nunca gerar uma recomendação genérica hardcoded fingindo ser uma análise inteligente.

Enquanto a IA não estiver integrada, exibir uma mensagem claramente identificada como insight baseado em regras.

Exemplo:

“Seu comprometimento da renda está dentro do limite configurado. Considere revisar o aporte da meta principal.”

Adicionar botão:

“Ver recomendações”

Somente habilitar caso exista uma rota ou ação funcional correspondente.

---

# ONBOARDING

Modernizar as oito etapas existentes:

1. Perfil.
2. Contas e saldos.
3. Rendas.
4. Obrigações e despesas.
5. Dívidas.
6. Metas.
7. Eventos futuros.
8. Revisão.

Criar um stepper horizontal no desktop.

Em telas menores, permitir rolagem horizontal ou usar uma visualização compacta.

Cada etapa deve possuir:

- identificação visual;
- estado ativo;
- estado concluído;
- estado pendente;
- validação;
- persistência;
- navegação anterior e próxima.

Não perder dados ao navegar entre etapas.

---

# TELA DE PERFIL

Melhorar os campos:

- moeda;
- dependentes;
- capacidade de redução de despesas.

Adicionar:

- labels;
- textos auxiliares;
- validação;
- mensagens de erro;
- formatação adequada;
- indicação clara de campo opcional.

A capacidade de redução de despesas deve continuar respeitando a faixa definida pelo domínio, por exemplo de 0 a 1.

Não alterar a unidade interna sem verificar os contratos existentes.

Botões:

- “Iniciar onboarding”.
- “Carregar dados de demonstração”.

Dar maior destaque ao botão principal.

O carregamento de demonstração deve ser explicitamente identificado como dados fictícios.

---

# TELA DE REVISÃO

Substituir a lista textual simples por cards de resumo.

Exibir:

- moeda;
- dependentes;
- quantidade de contas;
- quantidade de rendas;
- quantidade de obrigações;
- quantidade de dívidas;
- quantidade de metas;
- quantidade de eventos futuros.

Adicionar ações:

- editar uma seção;
- voltar;
- concluir onboarding;
- acessar dashboard.

Não apagar os dados coletados ao voltar para uma etapa.

---

# COMPONENTES

Criar ou reutilizar componentes como:

- AppShell;
- Sidebar;
- MobileSidebar;
- TopHeader;
- PageHeader;
- MetricCard;
- StatusCard;
- FinancialEventCard;
- ChartCard;
- EmptyState;
- LoadingSkeleton;
- ErrorState;
- CurrencyValue;
- PercentageValue;
- Badge;
- Button;
- IconButton;
- Tooltip;
- FormField;
- Stepper;
- ReviewCard;
- FinTwinInsight.

Evitar componentes gigantes.

Separar composição de página e componentes reutilizáveis.

---

# ESTADOS DA INTERFACE

Todas as áreas que dependem de dados devem tratar:

- idle;
- loading;
- success;
- empty;
- error;
- unavailable;
- future feature.

Usar skeletons durante carregamento.

Não utilizar apenas spinner central para toda a aplicação.

Não bloquear o dashboard inteiro quando somente um card estiver carregando.

---

# RESPONSIVIDADE

## Desktop

- sidebar fixa;
- quatro métricas por linha;
- três cards de analytics;
- máximo aproveitamento horizontal;
- largura máxima aproximada de 1600 px.

## Tablet

- sidebar colapsável;
- duas métricas por linha;
- gráficos reorganizados;
- espaçamento reduzido.

## Mobile

- uma coluna;
- navegação via drawer;
- cards ocupando 100%;
- valores financeiros sem corte;
- tabelas transformadas em cards;
- botões principais em largura total;
- stepper adaptado.

Testar pelo menos:

- 360 px;
- 390 px;
- 768 px;
- 1024 px;
- 1366 px;
- 1440 px;
- 1920 px.

---

# ACESSIBILIDADE

Implementar:

- HTML semântico;
- contraste WCAG AA;
- foco visível;
- navegação por teclado;
- labels associados;
- aria-label em botões de ícone;
- aria-current na navegação atual;
- tooltips acessíveis;
- gráficos acompanhados de resumo textual;
- suporte a prefers-reduced-motion.

Não comunicar estados financeiros apenas por cor.

---

# ANIMAÇÕES

Usar animações discretas:

- hover dos cards;
- abertura da sidebar;
- transição entre etapas;
- atualização de métricas;
- entrada dos gráficos;
- feedback de botões.

Duração recomendada:

- 150 ms para interações rápidas;
- 240 ms para transições comuns;
- máximo de 400 ms para elementos maiores.

Respeitar prefers-reduced-motion.

Não criar animações contínuas que distraiam o usuário.

---

# REGRAS TÉCNICAS

1. Inspecionar package.json antes de instalar dependências.
2. Reutilizar a stack existente.
3. Não substituir o sistema de roteamento sem necessidade.
4. Não substituir o gerenciamento de estado sem justificativa.
5. Não alterar contratos da API sem necessidade.
6. Não duplicar lógica financeira no frontend.
7. Não remover testes existentes.
8. Não quebrar o modo de demonstração.
9. Não esconder funcionalidades atuais.
10. Não criar dados falsos fora do modo de demonstração.
11. Não criar botões sem ação.
12. Não implementar recursos futuros das VSs de forma improvisada.
13. Não misturar CSS global com estilos específicos sem organização.
14. Não utilizar estilos inline para toda a aplicação.
15. Não criar um único componente de dashboard monolítico.

---

# CSS E TOKENS

Criar um arquivo central de tokens, por exemplo:

src/styles/tokens.css

Criar estilos globais:

src/styles/global.css

Criar estilos do layout:

src/styles/layout.css

Criar estilos dos componentes conforme o padrão atual do projeto.

Utilizar as variáveis CSS fornecidas na especificação visual.

Se o projeto já utilizar CSS Modules, styled-components, Tailwind ou outro sistema consistente, adaptar os tokens sem introduzir um segundo sistema concorrente.

---

# QUALIDADE

Antes de concluir:

- executar lint;
- executar typecheck;
- executar testes;
- executar build;
- corrigir erros;
- verificar warnings relevantes;
- testar rotas;
- testar onboarding;
- testar carregamento de demonstração;
- testar dashboard;
- testar navegação mobile;
- verificar console do navegador;
- verificar layout sem dados;
- verificar layout com valores grandes;
- verificar acessibilidade básica.

---

# TESTES RECOMENDADOS

Adicionar testes para:

- formatação monetária;
- formatação percentual;
- estado loading do MetricCard;
- estado unavailable;
- navegação do onboarding;
- persistência entre etapas;
- carregamento de dados de demonstração;
- resumo da tela de revisão;
- dashboard com dados;
- dashboard vazio;
- abertura e fechamento da sidebar mobile.

Não escrever testes frágeis baseados apenas em detalhes visuais.

---

# PLANO DE EXECUÇÃO OBRIGATÓRIO

Antes de modificar o código, apresente:

1. stack detectada;
2. estrutura atual;
3. rotas existentes;
4. componentes reaproveitáveis;
5. serviços e casos de uso consumidos;
6. riscos da refatoração;
7. plano incremental;
8. arquivos que serão criados;
9. arquivos que serão alterados.

Depois implemente em fases:

## Fase 1 — Fundação visual

- tokens;
- estilos globais;
- tipografia;
- AppShell;
- sidebar;
- header;
- responsividade base.

## Fase 2 — Dashboard

- cards de métricas;
- indicadores;
- eventos futuros;
- estados loading, empty e error.

## Fase 3 — Analytics

- despesas;
- saldo líquido;
- comprometimento da renda;
- tooltips;
- acessibilidade.

## Fase 4 — Onboarding

- stepper;
- formulários;
- validações;
- navegação;
- revisão.

## Fase 5 — FinTwin AI

- painel visual do agente;
- insight baseado em dados reais;
- estados de indisponibilidade;
- preparação para integração futura.

## Fase 6 — Qualidade

- testes;
- lint;
- typecheck;
- build;
- revisão responsiva;
- revisão de acessibilidade.

---

# CRITÉRIOS DE ACEITAÇÃO

A implementação será considerada concluída quando:

- o projeto continuar funcional;
- todas as regras financeiras forem preservadas;
- o onboarding tiver oito etapas funcionais;
- os dados persistirem entre etapas;
- o dashboard consumir dados reais;
- o modo demonstração estiver claramente identificado;
- métricas tiverem estados de carregamento e erro;
- funcionalidades futuras aparecerem como indisponíveis;
- a interface for responsiva;
- a sidebar funcionar no desktop e mobile;
- os gráficos forem baseados em dados reais;
- não existirem botões decorativos sem ação;
- os testes existentes continuarem passando;
- lint, typecheck e build passarem;
- o console do navegador não apresentar erros;
- a interface seguir a identidade visual do FinTwin AI.

---

# ENTREGA FINAL

Ao concluir, apresente:

1. resumo da implementação;
2. árvore dos componentes criados;
3. arquivos alterados;
4. decisões técnicas;
5. dependências adicionadas;
6. testes executados;
7. resultados do lint;
8. resultados do typecheck;
9. resultados do build;
10. limitações mantidas;
11. funcionalidades ainda dependentes de Vertical Slices futuras;
12. screenshots das principais telas, caso o ambiente permita.

Não apenas descreva a implementação.

Implemente, valide e reporte as evidências.
```

Um ponto importante: no layout gerado apareceu **“Autonomia ativa”**, mas no seu MVP atual existe **“Autonomia adversa”**. Na implementação, mantenha **Autonomia adversa**, porque ela faz parte do modelo que vocês já definiram.
