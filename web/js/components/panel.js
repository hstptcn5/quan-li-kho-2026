import { html } from "../vendor/htm-preact.js";

export function Panel({ title, actions = null, testid = null, children }) {
  return html`<section class="panel" data-testid=${testid}>
    <header class="panel__head"><h2 class="panel__title">${title}</h2>${actions}</header>
    <div class="panel__body">${children}</div>
  </section>`;
}
