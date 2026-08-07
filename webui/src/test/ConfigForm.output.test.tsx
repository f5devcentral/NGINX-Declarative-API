/**
 * Tests for OutputSection and related output-section functionality.
 *
 * Coverage:
 *  - Output type card labels (NGINX Instance Manager / NGINX One Console)
 *  - Output type switching and field visibility
 *  - License section toggle, field rendering, and grace_period as boolean
 *  - JWT token file-upload behaviour
 *  - Resolver ProfileSelect dropdown (populated vs. empty)
 *  - Copy-to-clipboard execCommand fallback (non-secure context)
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfigForm } from '@/components/ConfigForm';
import { CreateConfigPage } from '@/pages/CreateConfigPage';
import toast from 'react-hot-toast';

// ── Module-level mocks needed for CreateConfigPage ────────────────────────────

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

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
  Toaster: () => null,
}));

// ── JSON helpers ──────────────────────────────────────────────────────────────

/** Minimal NMS-type config with no license. */
const nmsJson = () => JSON.stringify({ output: { type: 'nim' } });

/** Minimal NGINX One config. */
const nginxoneJson = () => JSON.stringify({ output: { type: 'n1c' } });

/**
 * NMS config with the license block present.
 * @param gracePeriod  initial value of grace_period (undefined → field absent → Toggle defaults to false)
 */
const licensedJson = (gracePeriod?: boolean) =>
  JSON.stringify({
    output: {
      type: 'nim',
      license: {
        endpoint: 'product.connect.nginx.com',
        token: '',
        ssl_verify: true,
        ...(gracePeriod !== undefined ? { grace_period: gracePeriod } : {}),
      },
    },
  });

/**
 * NMS config with one resolver profile and one HTTP server.
 * Used to test the resolver ProfileSelect.
 */
const resolverJson = () =>
  JSON.stringify({
    output: { type: 'nim' },
    declaration: {
      resolvers: [
        { name: 'local-resolver', address: '192.168.2.13', ipv4: true, ipv6: false, timeout: '30s' },
      ],
      http: {
        servers: [{ name: 'web', listen: { address: '0.0.0.0:80' }, locations: [] }],
      },
    },
  });

// ── Helper: parse the last JSON string emitted via onChange ───────────────────

const lastOutput = (mockFn: ReturnType<typeof vi.fn>) => {
  const calls = mockFn.mock.calls;
  return JSON.parse(calls[calls.length - 1][0]);
};

// ─────────────────────────────────────────────────────────────────────────────
//  Output type card labels
// ─────────────────────────────────────────────────────────────────────────────

describe('OutputSection — type card labels', () => {
  it('renders "NGINX Instance Manager" card', () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    expect(screen.getByText('NGINX Instance Manager')).toBeInTheDocument();
  });

  it('renders "NGINX One Console" card', () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    expect(screen.getByText('NGINX One Console')).toBeInTheDocument();
  });

  it('renders subtitle "Push to an instance group" for NIM card', () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    expect(screen.getByText('Push to an instance group')).toBeInTheDocument();
  });

  it('renders subtitle "Push to a config sync group" for NGINX One card', () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    expect(screen.getByText('Push to a config sync group')).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
//  Output type switching
// ─────────────────────────────────────────────────────────────────────────────

describe('OutputSection — output type switching', () => {
  it('shows NIM-specific URL field by default (type = nms)', () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    expect(screen.getByPlaceholderText('https://nms.example.com')).toBeInTheDocument();
  });

  it('shows NGINX One fields when "NGINX One Console" card is clicked', async () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    await userEvent.click(screen.getByText('NGINX One Console'));
    expect(screen.getByPlaceholderText('https://nginx-one.example.com')).toBeInTheDocument();
  });

  it('emits type = "nginxone" in onChange when NGINX One Console is selected', async () => {
    const onChange = vi.fn();
    render(<ConfigForm initialJson={nmsJson()} onChange={onChange} />);
    await userEvent.click(screen.getByText('NGINX One Console'));
    expect(lastOutput(onChange).output.type).toBe('n1c');
  });

  it('switches back to NIM fields when "NGINX Instance Manager" is clicked', async () => {
    render(<ConfigForm initialJson={nginxoneJson()} onChange={vi.fn()} />);
    await userEvent.click(screen.getByText('NGINX Instance Manager'));
    expect(screen.getByPlaceholderText('https://nms.example.com')).toBeInTheDocument();
  });

  it('emits type = "nms" when NGINX Instance Manager is selected from nginxone', async () => {
    const onChange = vi.fn();
    render(<ConfigForm initialJson={nginxoneJson()} onChange={onChange} />);
    await userEvent.click(screen.getByText('NGINX Instance Manager'));
    expect(lastOutput(onChange).output.type).toBe('nim');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
//  License section
// ─────────────────────────────────────────────────────────────────────────────

describe('OutputSection — license section', () => {
  it('shows "Not configured" when no license is present', () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    expect(screen.getByText('Not configured')).toBeInTheDocument();
  });

  it('reveals license fields when the license toggle is enabled', async () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    await userEvent.click(screen.getByText('Not configured'));
    expect(screen.getByText('Enforce initial report')).toBeInTheDocument();
  });

  it('shows "Configured" after the license toggle is enabled', async () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    await userEvent.click(screen.getByText('Not configured'));
    expect(screen.getByText('Configured')).toBeInTheDocument();
  });

  it('hides license fields after the license toggle is disabled', async () => {
    render(<ConfigForm initialJson={licensedJson()} onChange={vi.fn()} />);
    await userEvent.click(screen.getByText('Configured'));
    expect(screen.queryByText('Enforce initial report')).not.toBeInTheDocument();
  });

  it('renders "Enforce initial report" as a checkbox, not a text input', () => {
    render(<ConfigForm initialJson={licensedJson()} onChange={vi.fn()} />);
    const field = screen.getByText('Enforce initial report').closest('.cf-field');
    expect(field?.querySelector('input[type="checkbox"]')).toBeTruthy();
    expect(field?.querySelector('input[type="text"]')).toBeNull();
  });

  it('defaults grace_period checkbox to unchecked when not set', () => {
    render(<ConfigForm initialJson={licensedJson()} onChange={vi.fn()} />);
    const field = screen.getByText('Enforce initial report').closest('.cf-field');
    const checkbox = field?.querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(checkbox.checked).toBe(false);
  });

  it('emits grace_period: true when "Enforce initial report" is toggled on', async () => {
    const onChange = vi.fn();
    render(<ConfigForm initialJson={licensedJson(false)} onChange={onChange} />);
    const field = screen.getByText('Enforce initial report').closest('.cf-field');
    const checkbox = field?.querySelector('input[type="checkbox"]') as HTMLInputElement;
    await userEvent.click(checkbox);
    expect(lastOutput(onChange).output.license.grace_period).toBe(true);
  });

  it('emits grace_period: false when "Enforce initial report" is toggled off', async () => {
    const onChange = vi.fn();
    render(<ConfigForm initialJson={licensedJson(true)} onChange={onChange} />);
    const field = screen.getByText('Enforce initial report').closest('.cf-field');
    const checkbox = field?.querySelector('input[type="checkbox"]') as HTMLInputElement;
    await userEvent.click(checkbox);
    expect(lastOutput(onChange).output.license.grace_period).toBe(false);
  });

  it('renders a file input that accepts .jwt and .txt for JWT upload', () => {
    render(<ConfigForm initialJson={licensedJson()} onChange={vi.fn()} />);
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
    expect(fileInput).toHaveAttribute('accept', '.jwt,.txt,text/plain');
  });

  it('reads and trims the JWT token from an uploaded file', async () => {
    const onChange = vi.fn();
    render(<ConfigForm initialJson={licensedJson()} onChange={onChange} />);
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const tokenContent = '  eyJhbGciOiJSUzI1NiJ9.test.signature  ';
    const file = new File([tokenContent], 'license.jwt', { type: 'text/plain' });
    await userEvent.upload(fileInput, file);
    await waitFor(() => {
      const out = lastOutput(onChange);
      expect(out.output.license.token).toBe(tokenContent.trim());
    });
  });
});

// ─────────────────────────────────────────────────────────────────────────────
//  Resolver ProfileSelect dropdown
// ─────────────────────────────────────────────────────────────────────────────

describe('OutputSection — resolver ProfileSelect', () => {
  it('shows "— no profiles defined —" when no resolver profiles exist', () => {
    const json = JSON.stringify({
      output: { type: 'nim' },
      declaration: {
        http: { servers: [{ name: 'web', listen: { address: '0.0.0.0:80' }, locations: [] }] },
      },
    });
    render(<ConfigForm initialJson={json} onChange={vi.fn()} />);
    expect(screen.getAllByText('— no profiles defined —').length).toBeGreaterThan(0);
  });

  it('lists the resolver name as an option when a resolver profile is defined', () => {
    render(<ConfigForm initialJson={resolverJson()} onChange={vi.fn()} />);
    const options = screen.getAllByRole('option', { name: 'local-resolver' });
    expect(options.length).toBeGreaterThan(0);
  });

  it('emits the selected resolver name in server.resolver when the dropdown changes', () => {
    const onChange = vi.fn();
    render(<ConfigForm initialJson={resolverJson()} onChange={onChange} />);
    // Find the combobox (select) that contains 'local-resolver' as an option
    const resolverSelect = screen
      .getAllByRole('combobox')
      .find((s) =>
        Array.from((s as HTMLSelectElement).options).some((o) => o.value === 'local-resolver'),
      ) as HTMLSelectElement;
    fireEvent.change(resolverSelect, { target: { value: 'local-resolver' } });
    const out = lastOutput(onChange);
    expect(out.declaration.http.servers[0].resolver).toBe('local-resolver');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
//  Sidebar navigation
// ─────────────────────────────────────────────────────────────────────────────

describe('ConfigForm — sidebar navigation', () => {
  it('renders sidebar nav buttons for top-level sections', () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    const nav = document.querySelector('nav.cf-sidenav');
    expect(nav).toBeInTheDocument();
    expect(nav?.textContent).toContain('Output');
    expect(nav?.textContent).toContain('HTTP');
    expect(nav?.textContent).toContain('Layer 4');
  });

  it('renders indented sub-section links in the sidebar', () => {
    render(<ConfigForm initialJson={nmsJson()} onChange={vi.fn()} />);
    const indentedItems = document.querySelectorAll('.cf-sidenav-item.indent');
    const labels = Array.from(indentedItems).map((el) => el.textContent);
    expect(labels).toContain('License');
    expect(labels).toContain('Policies');
    expect(labels).toContain('Profiles');
    expect(labels).toContain('Servers');
    expect(labels).toContain('Upstreams');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
//  Copy-to-clipboard execCommand fallback
// ─────────────────────────────────────────────────────────────────────────────

describe('CreateConfigPage — clipboard execCommand fallback', () => {
  let originalClipboard: PropertyDescriptor | undefined;
  let execCommandMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    // Remove navigator.clipboard so the condition `navigator.clipboard && isSecureContext` is false
    originalClipboard = Object.getOwnPropertyDescriptor(navigator, 'clipboard');
    Object.defineProperty(navigator, 'clipboard', {
      value: undefined,
      configurable: true,
      writable: true,
    });
    // Define execCommand on document (absent in jsdom) and track calls
    execCommandMock = vi.fn().mockReturnValue(true);
    Object.defineProperty(document, 'execCommand', {
      value: execCommandMock,
      configurable: true,
      writable: true,
    });
  });

  afterEach(() => {
    if (originalClipboard) {
      Object.defineProperty(navigator, 'clipboard', originalClipboard);
    }
  });

  it('falls back to execCommand copy when navigator.clipboard is unavailable', async () => {
    render(<CreateConfigPage />);
    // Switch to NGINX One Console — this calls ConfigForm's onChange which populates
    // jsonValue in the page, making the copy button functional.
    // getAllByText handles the case where the label appears in both the type card and the
    // CreateConfigPage template list; index [0] is the card span rendered first in the DOM.
    await userEvent.click(screen.getAllByText('NGINX One Console')[0]);
    await userEvent.click(screen.getByRole('button', { name: /copy to clipboard/i }));
    await waitFor(() => expect(execCommandMock).toHaveBeenCalledWith('copy'));
    expect(toast.success).toHaveBeenCalledWith('Configuration copied to clipboard');
  });
});
