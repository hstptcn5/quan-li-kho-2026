import { html } from "../vendor/htm-preact.js";

export function StatList({ items }) {
  return html`<ul class="stat-list">
    ${items.map((item) => html`<li class="stat-list__row" key=${item.key}>
      <span class=${"dot dot--" + item.tone} aria-hidden="true"></span>
      <span class="stat-list__label">${item.label}</span>
      <strong class="stat-list__value">${item.value}</strong>
    </li>`)}
  </ul>`;
}
