import { html } from "../vendor/htm-preact.js";

export function AppShell({ items, activeId, children }) {
  return html`<div class="shell">
    <aside class="shell__side" aria-label="Điều hướng chính">
      <div class="shell__brand">QUẢN LÝ KHO 2026</div>
      <nav class="shell__nav">
        ${items.map((item) => item.live
          ? html`<a key=${item.id} class=${"nav" + (item.id === activeId ? " nav--active" : "")}
              href=${"#/" + item.id} aria-current=${item.id === activeId ? "page" : null}
              data-testid=${"nav-" + item.id}><span>${item.label}</span><kbd>${item.hotkey}</kbd></a>`
          : html`<span key=${item.id} class="nav nav--off" aria-disabled="true"
              title="Chưa có trong giao diện mới" data-testid=${"nav-" + item.id}><span>${item.label}</span><small>sắp có</small></span>`)}
      </nav>
    </aside>
    <main class="shell__main">${children}</main>
  </div>`;
}
