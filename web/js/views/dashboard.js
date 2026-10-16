import { html, Component } from "../vendor/htm-preact.js";
import { getJson } from "../api.js";
import { formatCount, formatDate, formatDateTime, formatQty } from "../format.js";
import { Button } from "../components/button.js";
import { Badge } from "../components/badge.js";
import { Panel } from "../components/panel.js";
import { StatList } from "../components/stat-list.js";
import { FilterChips } from "../components/filter-chips.js";
import { DataTable } from "../components/data-table.js";
import { EmptyState, ErrorState } from "../components/states.js";
import { showToast } from "../components/toast.js";

const CHIPS = [["all", "Tất cả"], ["expired", "Hết hạn"], ["near", "Cận hạn"], ["low", "Tồn thấp"]];
const TONE = { expired: "danger", near: "warning", low: "info" };
const NOT_AVAILABLE = "Chưa có trong giao diện mới";
const QUICK_ACTIONS = [
  { label: "+ Nhập kho", tone: "primary" },
  { label: "− Xuất kho", tone: "primary" },
  { label: "Tra cứu tồn", tone: "secondary" },
  { label: "Báo cáo XNT", tone: "secondary" },
];

function categoryOf(severity) {
  if (severity <= 1) return "expired";
  if (severity === 2) return "near";
  return "low";
}

const COLUMNS = [
  { key: "product", label: "Thuốc - vật tư", render: (row) => `#${row.productId}  ${row.productName}` },
  { key: "lot", label: "Lô", align: "center", render: (row) => row.lotNo },
  { key: "expiry", label: "Hạn dùng", align: "center", render: (row) => formatDate(row.expiryDate) },
  { key: "stock", label: "Tồn", align: "right", render: (row) => formatQty(row.stockBase) },
  { key: "fund", label: "Nguồn", render: (row) => row.fundSource || "(không rõ)" },
  {
    key: "status",
    label: "Trạng thái",
    align: "center",
    render: (row) => html`<${Badge} tone=${TONE[categoryOf(row.severity)]}>${row.status}<//>`,
  },
];

export class DashboardView extends Component {
  constructor(props) {
    super(props);
    this.requestId = 0;
    this.state = { filter: "all", data: null, error: null, loading: true };
    this.reload = () => this.load(this.state.filter);
    this.pickFilter = (value) => this.load(value);
  }

  componentDidMount() {
    this.load("all");
  }

  componentWillUnmount() {
    this.requestId += 1; // bỏ qua phản hồi đến muộn sau khi rời màn hình
  }

  async load(filter) {
    const requestId = ++this.requestId;
    this.setState({ filter, loading: true });
    try {
      const data = await getJson("/api/dashboard", { filter });
      if (requestId !== this.requestId) return; // đã có yêu cầu mới hơn: bỏ phản hồi cũ
      this.setState({ data, error: null, loading: false });
    } catch (error) {
      if (requestId !== this.requestId) return;
      this.setState({ error, loading: false });
      showToast(error.message, "danger");
    }
  }

  renderHeader() {
    return html`<header class="page-head">
      <div>
        <h1 class="page-head__title">Tổng quan vận hành kho</h1>
        <p class="page-head__sub">FEFO theo lô và HSD</p>
      </div>
      <div class="page-head__actions">
        ${QUICK_ACTIONS.map((action) => html`<${Button} key=${action.label} tone=${action.tone}
          disabled=${true} title=${NOT_AVAILABLE}>${action.label}<//>`)}
        <${Button} tone="secondary" title="Tải lại" testid="reload" onClick=${this.reload}>↻<//>
      </div>
    </header>`;
  }

  renderWarnings(data) {
    const { filter, loading } = this.state;
    const counts = data.warnings.counts;
    const rows = data.warnings.rows;
    const options = CHIPS.map(([value, label]) => ({ value, label, count: counts[value] }));
    const chips = html`<${FilterChips} options=${options} value=${filter} onChange=${this.pickFilter} />`;
    const empty = html`<${EmptyState} testid="warning-empty"
      title=${counts.all === 0 ? "Không có cảnh báo nào cần xử lý" : "Không có dòng nào thuộc nhóm này"} />`;
    return html`<${Panel} title="⚠ CẦN XỬ LÝ HÔM NAY" actions=${chips} testid="warnings-panel">
      <${DataTable} testid="warning-table" columns=${COLUMNS} rows=${rows} empty=${empty}
        rowKey=${(row) => `${row.productId}-${row.batchId}-${row.fundSource}`}
        rowProps=${(row) => ({ class: "row--" + categoryOf(row.severity), "data-severity": row.severity })} />
      <div class="panel__foot" data-testid="warning-foot">
        ${loading ? "Đang tải…" : `Hiển thị ${rows.length} / ${counts[filter]} dòng`}
      </div>
    <//>`;
  }

  renderActivities(activities) {
    if (!activities.length) {
      return html`<${EmptyState} title="Chưa có hoạt động được ghi nhận" />`;
    }
    return html`<ul class="info-list">
      ${activities.map((item, index) => html`<li key=${index} class="info-list__row">
        ${formatDateTime(item.timestamp)} • ${item.action} • ${item.details}
      </li>`)}
    </ul>`;
  }

  renderSide(data) {
    const cards = data.cards;
    const stats = [
      { key: "products", label: "Tổng mặt hàng", value: formatCount(cards.productCount), tone: "neutral" },
      { key: "active", label: "Lô đang tồn", value: formatCount(cards.activeLotCount), tone: "success" },
      { key: "near", label: `Cận hạn ≤${data.warningDays} ngày`, value: formatCount(cards.nearExpiryCount), tone: "warning" },
      { key: "expired", label: "Đã hết hạn", value: formatCount(cards.expiredCount), tone: "danger" },
      { key: "low", label: `Tồn thấp ≤${data.lowStockThreshold}`, value: formatCount(cards.lowStockCount), tone: "warning" },
    ];
    const runtime = data.runtime;
    const backupOk = Boolean(runtime.lastBackup);
    const backupText = backupOk
      ? `✓ Sao lưu gần nhất: ${formatDateTime(runtime.lastBackup.created)}`
      : "! Chưa có bản sao lưu";
    const temp = runtime.latestTemperature;
    const humidity = temp && temp.humidity !== null ? ` • ${formatQty(temp.humidity)}%` : "";
    const negative = runtime.negativeStockRows;
    return html`<div class="dashboard__side">
      <${Panel} title="SỐ LIỆU KHO (theo lô)" testid="stats-panel"><${StatList} items=${stats} /><//>
      <${Panel} title="↶ HOẠT ĐỘNG GẦN ĐÂY" testid="activity-panel">${this.renderActivities(data.activities)}<//>
      <${Panel} title="✓ TRẠNG THÁI" testid="status-panel">
        <ul class="info-list">
          <li class=${"info-list__row " + (backupOk ? "is-ok" : "is-warn")}>${backupText}</li>
          <li class="info-list__row">${temp
            ? html`Nhiệt độ gần nhất: ${formatQty(temp.temperature)}°C${humidity}<br />${temp.locationName} • ${formatDate(temp.logDate)} • ${temp.session}`
            : "Nhiệt độ & độ ẩm: chưa có bản ghi"}</li>
          <li class=${"info-list__row " + (negative === 0 ? "is-ok" : "is-warn")}>${negative === 0
            ? "✓ Không có dòng tồn âm"
            : `! Phát hiện ${negative} dòng tồn âm`}</li>
        </ul>
      <//>
    </div>`;
  }

  renderBody() {
    const { data, error } = this.state;
    if (data) {
      return html`${error ? html`<p class="dashboard__error" role="alert">${error.message}</p>` : null}
        <div class="dashboard__grid">${this.renderWarnings(data)}${this.renderSide(data)}</div>
        <p class="dashboard__note">Ngưỡng tồn thấp hiện là ≤${data.lowStockThreshold} đơn vị cơ sở, không phải định mức cấu hình.</p>`;
    }
    if (error) {
      const expired = error.authRequired === true;
      return html`<${ErrorState}
        title=${expired ? "Phiên làm việc đã hết hạn" : "Không tải được Tổng quan"}
        message=${expired ? "Hãy đóng cửa sổ và mở lại ứng dụng." : error.message}
        onRetry=${expired ? null : this.reload} />`;
    }
    return html`<${EmptyState} title="Đang tải dữ liệu…" />`;
  }

  render() {
    const { data, error, loading } = this.state;
    const ready = !loading && Boolean(data || error);
    return html`<section class="dashboard" data-testid=${ready ? "dashboard-ready" : "dashboard-loading"}>
      ${this.renderHeader()}${this.renderBody()}
    </section>`;
  }
}
