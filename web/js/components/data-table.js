import { html } from "../vendor/htm-preact.js";

// columns: [{ key, label, align?, render?(row) }]; rowProps(row) trả về thuộc tính thêm cho <tr>.
export function DataTable({ columns, rows, rowKey, rowProps = null, testid = null, empty = null }) {
  if (!rows.length) {
    return empty;
  }
  return html`<div class="table-wrap">
    <table class="table" data-testid=${testid}>
      <thead><tr>
        ${columns.map((column) => html`<th key=${column.key} class=${"table__th table__th--" + (column.align || "left")}>${column.label}</th>`)}
      </tr></thead>
      <tbody>
        ${rows.map((row) => html`<tr key=${rowKey(row)} ...${rowProps ? rowProps(row) : {}}>
          ${columns.map((column) => html`<td key=${column.key} class=${"table__td table__td--" + (column.align || "left")}>${column.render ? column.render(row) : row[column.key]}</td>`)}
        </tr>`)}
      </tbody>
    </table>
  </div>`;
}
