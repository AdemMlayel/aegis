import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  children: ReactNode;
  /** Optional label so a per-section boundary can name what failed. */
  section?: string;
};

type State = {
  error: Error | null;
};

/**
 * W11: catches render-time exceptions so a single bad component can't
 * white-screen the whole cockpit. Wrap the app at the root and individual
 * high-risk panels (e.g. the workspace) so one broken view degrades to a
 * dismissible message instead of unmounting everything.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Surface to the console for debugging; the UI shows a safe fallback.
    console.error("AegisQA UI error boundary caught:", error, info);
  }

  private reset = () => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    const { error } = this.state;
    if (!error) {
      return this.props.children;
    }
    const where = this.props.section ? ` in ${this.props.section}` : "";
    return (
      <div className="error-boundary" role="alert">
        <strong>Something went wrong{where}.</strong>
        <p>{error.message || "An unexpected error occurred while rendering."}</p>
        <div className="error-boundary-actions">
          <button type="button" onClick={this.reset}>
            Try again
          </button>
          <button type="button" onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      </div>
    );
  }
}
