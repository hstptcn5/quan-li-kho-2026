import { html } from "../vendor/htm-preact.js";

export function Badge({ tone = "info", children }) {
  return html`<span class=${"badge badge--" + tone}>${children}</span>`;
}
