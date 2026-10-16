import { html } from "../vendor/htm-preact.js";

export function FilterChips({ options, value, onChange }) {
  return html`<div class="chips" role="group" aria-label="Lọc cảnh báo">
    ${options.map((option) => html`<button type="button" key=${option.value}
      class=${"chip" + (option.value === value ? " chip--on" : "")}
      aria-pressed=${option.value === value ? "true" : "false"}
      data-testid=${"chip-" + option.value}
      onClick=${() => onChange(option.value)}>${option.label} ${option.count}</button>`)}
  </div>`;
}
