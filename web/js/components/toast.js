import { html, Component } from "../vendor/htm-preact.js";

const listeners = new Set();
let nextId = 1;

export function showToast(message, tone = "info") {
  const toast = { id: nextId++, message: String(message), tone };
  listeners.forEach((listener) => listener(toast));
}

export class ToastHost extends Component {
  constructor(props) {
    super(props);
    this.state = { toasts: [] };
    this.onToast = (toast) => {
      this.setState((state) => ({ toasts: [...state.toasts, toast] }));
      window.setTimeout(() => this.dismiss(toast.id), 5000);
    };
  }

  dismiss(id) {
    this.setState((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
  }

  componentDidMount() {
    listeners.add(this.onToast);
  }

  componentWillUnmount() {
    listeners.delete(this.onToast);
  }

  render() {
    return html`<div class="toasts" role="status" aria-live="polite">
      ${this.state.toasts.map((toast) => html`<div key=${toast.id} class=${"toast toast--" + toast.tone}>${toast.message}</div>`)}
    </div>`;
  }
}
