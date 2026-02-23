import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateConfigPage } from '@/pages/CreateConfigPage';
import toast from 'react-hot-toast';

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange }: { value: string; onChange?: (v: string) => void }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
    />
  ),
}));

vi.mock('@/components/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ConfigForm', () => ({
  ConfigForm: ({ onChange }: { onChange: (json: string) => void }) => (
    <button
      data-testid="form-trigger-change"
      onClick={() => onChange('{"declaration":{}}')}
    >
      Simulate Form Change
    </button>
  ),
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
  Toaster: () => null,
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

const renderPage = () => render(<CreateConfigPage />);

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('CreateConfigPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });

    global.URL.createObjectURL = vi.fn().mockReturnValue('blob:mock');
    global.URL.revokeObjectURL = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({ ok: false });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  // ── Section order ──────────────────────────────────────────────────────────

  describe('layout', () => {
    it('renders Quick Start Templates before Configuration Declaration', () => {
      renderPage();
      const headings = screen.getAllByRole('heading');
      const templateIdx = headings.findIndex((h) => h.textContent === 'Quick Start Templates');
      const configIdx = headings.findIndex((h) => h.textContent === 'Configuration Declaration');
      expect(templateIdx).toBeGreaterThanOrEqual(0);
      expect(configIdx).toBeGreaterThanOrEqual(0);
      expect(templateIdx).toBeLessThan(configIdx);
    });

    it('renders all three template cards', () => {
      renderPage();
      expect(screen.getByText('NGINX Instance Manager')).toBeInTheDocument();
      expect(screen.getByText('NGINX One Console')).toBeInTheDocument();
      expect(screen.getByText('API Gateway')).toBeInTheDocument();
    });

    it('renders Copy to Clipboard and Save to File buttons', () => {
      renderPage();
      expect(screen.getByRole('button', { name: /copy to clipboard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save to file/i })).toBeInTheDocument();
    });
  });

  // ── Mode toggle ────────────────────────────────────────────────────────────

  describe('mode toggle', () => {
    it('starts in form mode', () => {
      renderPage();
      expect(screen.getByTestId('form-trigger-change')).toBeInTheDocument();
      expect(screen.queryByTestId('monaco-editor')).not.toBeInTheDocument();
    });

    it('switches to JSON mode when JSON button is clicked', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
      expect(screen.queryByTestId('form-trigger-change')).not.toBeInTheDocument();
    });

    it('switches back to form mode', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      await userEvent.click(screen.getByRole('button', { name: /form/i }));
      expect(screen.getByTestId('form-trigger-change')).toBeInTheDocument();
    });
  });

  // ── Template loading (clean state) ────────────────────────────────────────

  describe('template loading — clean state', () => {
    it('loads a template without showing a confirm dialog', async () => {
      renderPage();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('loaded template JSON is reflected in the editor', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      const parsed = JSON.parse(editor.value);
      expect(parsed.output.type).toBe('nms');
      expect(parsed.output.nms.instancegroup).toBe('production');
    });

    it('loads the NGINX One Console template', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      await userEvent.click(screen.getByText('NGINX One Console'));
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      const parsed = JSON.parse(editor.value);
      expect(parsed.output.type).toBe('nginxone');
    });

    it('loads the API Gateway template', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      await userEvent.click(screen.getByText('API Gateway'));
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      const parsed = JSON.parse(editor.value);
      expect(parsed.output.nms.instancegroup).toBe('api-gateway');
    });
  });

  // ── Template loading (dirty state) ────────────────────────────────────────

  describe('template loading — dirty state', () => {
    const makeDirtyViaForm = async () => {
      renderPage();
      await userEvent.click(screen.getByTestId('form-trigger-change'));
    };

    const makeDirtyViaEditor = async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      fireEvent.change(screen.getByTestId('monaco-editor'), {
        target: { value: '{"declaration":{}}' },
      });
    };

    it('shows confirm dialog when form is dirty and a template is clicked', async () => {
      await makeDirtyViaForm();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Replace configuration?')).toBeInTheDocument();
    });

    it('shows confirm dialog when JSON editor is dirty and a template is clicked', async () => {
      await makeDirtyViaEditor();
      await userEvent.click(screen.getByText('NGINX One Console'));
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('dismisses dialog without loading template when Cancel is clicked', async () => {
      await makeDirtyViaForm();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      await userEvent.click(screen.getByRole('button', { name: /cancel/i }));
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      // editor still has the user's previous content, not the template
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      expect(editor.value).toBe('{"declaration":{}}');
    });

    it('loads template and dismisses dialog when Load template is clicked', async () => {
      await makeDirtyViaForm();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      await userEvent.click(screen.getByRole('button', { name: /load template/i }));
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      const parsed = JSON.parse(editor.value);
      expect(parsed.output.type).toBe('nms');
    });

    it('resets dirty flag after loading a template via confirm', async () => {
      await makeDirtyViaForm();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      await userEvent.click(screen.getByRole('button', { name: /load template/i }));
      // Clicking another template now should NOT show the dialog again
      await userEvent.click(screen.getByText('API Gateway'));
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  // ── Copy to clipboard ──────────────────────────────────────────────────────

  describe('Copy to Clipboard', () => {
    it('shows error toast when there is nothing to copy', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /copy to clipboard/i }));
      expect(toast.error).toHaveBeenCalledWith(
        'Nothing to copy — build or paste a configuration first'
      );
    });

    it('shows error toast when JSON is invalid', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      fireEvent.change(screen.getByTestId('monaco-editor'), {
        target: { value: '{ bad json' },
      });
      await userEvent.click(screen.getByRole('button', { name: /copy to clipboard/i }));
      expect(toast.error).toHaveBeenCalledWith(expect.stringMatching(/invalid json/i));
    });

    it('copies valid JSON and shows success toast', async () => {
      renderPage();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      await userEvent.click(screen.getByRole('button', { name: /copy to clipboard/i }));
      await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalledOnce());
      expect(toast.success).toHaveBeenCalledWith('Configuration copied to clipboard');
    });

    it('shows "Copied!" label briefly after copying', async () => {
      renderPage();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      await userEvent.click(screen.getByRole('button', { name: /copy to clipboard/i }));
      await waitFor(() =>
        expect(screen.getByRole('button', { name: /copied/i })).toBeInTheDocument()
      );
    });
  });

  // ── Save to File ───────────────────────────────────────────────────────────

  describe('Save to File', () => {
    it('shows error toast when there is nothing to save', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /save to file/i }));
      expect(toast.error).toHaveBeenCalledWith(
        'Nothing to save — build or paste a configuration first'
      );
    });

    it('shows error toast when JSON is invalid', async () => {
      renderPage();
      await userEvent.click(screen.getByRole('button', { name: /json/i }));
      fireEvent.change(screen.getByTestId('monaco-editor'), {
        target: { value: '{ bad json' },
      });
      await userEvent.click(screen.getByRole('button', { name: /save to file/i }));
      expect(toast.error).toHaveBeenCalledWith(expect.stringMatching(/invalid json/i));
    });

    it('triggers a download and shows "Download started" toast for valid JSON', async () => {
      const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
      renderPage();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      await userEvent.click(screen.getByRole('button', { name: /save to file/i }));
      expect(URL.createObjectURL).toHaveBeenCalledOnce();
      expect(clickSpy).toHaveBeenCalledOnce();
      expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock');
      expect(toast.success).toHaveBeenCalledWith('Download started');
    });

    it('uses "nginx-dapi-config.json" as the download filename', async () => {
      vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
      const createElementSpy = vi.spyOn(document, 'createElement');
      renderPage();
      await userEvent.click(screen.getByText('NGINX Instance Manager'));
      await userEvent.click(screen.getByRole('button', { name: /save to file/i }));
      const anchor = createElementSpy.mock.results.find(
        (r) => r.value instanceof HTMLAnchorElement
      )?.value as HTMLAnchorElement;
      expect(anchor?.download).toBe('nginx-dapi-config.json');
    });
  });
});
