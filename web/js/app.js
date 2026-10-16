import { html, render, Component } from "./vendor/htm-preact.js";
import { NAV_ITEMS } from "./nav.js";
import { AppShell } from "./components/app-shell.js";
import { ToastHost, showToast } from "./components/toast.js";
import { DashboardView } from "./views/dashboard.js";

// Chẩn đoán cho smoke test đóng gói (quanly_web.py --smoke đọc window.__qlk).
window.__qlk = { cspViolations: [], errors: [] };
document.addEventListener("securitypolicyviolation", (event) => {
  window.__qlk.cspViolations.push(`${event.violatedDirective} ${event.blockedURI}`);
});
window.addEventListener("error", (event) => {
  window.__qlk.errors.push(String(event.message));
});
window.addEventListener("unhandledrejection", (event) => {
  window.__qlk.errors.push(String(event.reason));
});

const VIEWS = { dashboard: DashboardView };

function routeFromHash() {
  const id = String(window.location.hash || "").replace(/^#\//, "");
  const item = NAV_ITEMS.find((entry) => entry.id === id);
  return item && item.live ? item.id : "dashboard"; // mục chưa có bản web vẫn giữ Tổng quan
}

class App extends Component {
  constructor(props) {
    super(props);
    this.state = { route: routeFromHash() };
    this.onHashChange = () => this.setState({ route: routeFromHash() });
    this.onKeyDown = (event) => {
      const item = NAV_ITEMS.find((entry) => entry.hotkey === event.key);
      if (!item) return;
      event.preventDefault(); // chặn F5 (tải lại) và F12 (devtools) mặc định
      if (item.live) {
        window.location.hash = `#/${item.id}`;
      } else {
        showToast("Màn hình này chưa có trong giao diện mới. Hãy mở bằng bản Tkinter.", "info");
      }
    };
  }

  componentDidMount() {
    window.addEventListener("hashchange", this.onHashChange);
    window.addEventListener("keydown", this.onKeyDown);
  }

  componentWillUnmount() {
    window.removeEventListener("hashchange", this.onHashChange);
    window.removeEventListener("keydown", this.onKeyDown);
  }

  render() {
    const View = VIEWS[this.state.route];
    return html`<${AppShell} items=${NAV_ITEMS} activeId=${this.state.route}>
        <${View} key=${this.state.route} />
      <//>
      <${ToastHost} />`;
  }
}

render(html`<${App} />`, document.getElementById("app"));
