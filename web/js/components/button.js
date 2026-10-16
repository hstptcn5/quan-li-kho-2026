import { html } from "../vendor/htm-preact.js";

export function Button({ tone = "secondary", disabled = false, title = null, onClick = null, testid = null, children }) {
  return html`<button type="button" class=${"btn btn--" + tone} disabled=${disabled} title=${title}
    onClick=${onClick} data-testid=${testid}>${children}</button>`;
}
