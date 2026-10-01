import { html } from "../vendor/htm-preact.js";
import { Button } from "./button.js";

export function EmptyState({ title, hint = null, testid = null }) {
  return html`<div class="state" data-testid=${testid}>
    <p class="state__title">${title}</p>
    ${hint ? html`<p class="state__hint">${hint}</p>` : null}
  </div>`;
}

export function ErrorState({ title, message, onRetry = null, testid = "dashboard-error" }) {
  return html`<div class="state state--error" role="alert" data-testid=${testid}>
    <p class="state__title">${title}</p>
    <p class="state__hint">${message}</p>
    ${onRetry ? html`<div class="state__retry"><${Button} tone="secondary" onClick=${onRetry} testid="retry">Thử lại<//></div>` : null}
  </div>`;
}
