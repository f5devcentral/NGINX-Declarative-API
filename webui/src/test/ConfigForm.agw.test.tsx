import { describe, it, expect, vi, beforeEach, afterEach, type MockedFunction } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfigForm } from '@/components/ConfigForm';

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Build a minimal initialJson with one server / one location, apigateway.openapi_schema enabled. */
const makeJson = (schemaContent = '') =>
  JSON.stringify({
    output: { type: 'nim' },
    declaration: {
      http: {
        servers: [
          {
            name: 'test-server',
            locations: [
              {
                uri: '/test',
                urimatch: 'prefix',
                apigateway: {
                  openapi_schema: { content: schemaContent },
                },
              },
            ],
          },
        ],
      },
    },
  });

/** Build a minimal initialJson with one server / one location and NO apigateway block. */
const makeJsonNoAgw = () =>
  JSON.stringify({
    output: { type: 'nim' },
    declaration: {
      http: {
        servers: [
          {
            name: 'test-server',
            locations: [{ uri: '/test', urimatch: 'prefix' }],
          },
        ],
      },
    },
  });

/** Extract openapi_schema.content from onChange's last JSON argument. */
const lastSchemaContent = (mockFn: ReturnType<typeof vi.fn>): string => {
  const calls = mockFn.mock.calls;
  const lastJson = JSON.parse((calls[calls.length - 1] as [string])[0]);
  return lastJson.declaration.http.servers[0].locations[0].apigateway.openapi_schema.content;
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('ConfigForm — API Gateway: section toggle', () => {
  let mockOnChange: MockedFunction<(json: string) => void>;

  beforeEach(() => {
    mockOnChange = vi.fn();
  });

  /** Find the checkbox inside the API Gateway subsection. */
  const getAgwToggle = (container: HTMLElement) =>
    container
      .querySelector('.cf-subsection-agw .cf-subsection-header input[type="checkbox"]') as HTMLInputElement;

  it('shows a disabled toggle when apigateway is absent from the location', () => {
    const { container } = render(<ConfigForm initialJson={makeJsonNoAgw()} onChange={mockOnChange} />);
    expect(getAgwToggle(container).checked).toBe(false);
  });

  it('shows an enabled toggle when apigateway is present', () => {
    const { container } = render(<ConfigForm initialJson={makeJson()} onChange={mockOnChange} />);
    expect(getAgwToggle(container).checked).toBe(true);
  });

  it('enabling the toggle adds the apigateway key to the JSON output', () => {
    const { container } = render(<ConfigForm initialJson={makeJsonNoAgw()} onChange={mockOnChange} />);
    fireEvent.click(getAgwToggle(container));

    expect(mockOnChange).toHaveBeenCalled();
    const lastJson = JSON.parse(mockOnChange.mock.calls[mockOnChange.mock.calls.length - 1][0]);
    expect(lastJson.declaration.http.servers[0].locations[0]).toHaveProperty('apigateway');
  });

  it('disabling the toggle removes the apigateway key from the JSON output', () => {
    const { container } = render(<ConfigForm initialJson={makeJson()} onChange={mockOnChange} />);
    fireEvent.click(getAgwToggle(container));

    expect(mockOnChange).toHaveBeenCalled();
    const lastJson = JSON.parse(mockOnChange.mock.calls[mockOnChange.mock.calls.length - 1][0]);
    expect(lastJson.declaration.http.servers[0].locations[0]).not.toHaveProperty('apigateway');
  });

  it('hides all API Gateway sub-sections when the toggle is disabled', () => {
    render(<ConfigForm initialJson={makeJsonNoAgw()} onChange={mockOnChange} />);
    expect(screen.queryByText('OpenAPI Schema')).not.toBeInTheDocument();
    expect(screen.queryByText('API Gateway Settings')).not.toBeInTheDocument();
  });

  it('shows all API Gateway sub-sections when the toggle is enabled', () => {
    render(<ConfigForm initialJson={makeJson()} onChange={mockOnChange} />);
    expect(screen.getByText('OpenAPI Schema')).toBeInTheDocument();
    expect(screen.getByText('API Gateway Settings')).toBeInTheDocument();
  });
});

describe('ConfigForm — API Gateway: OpenAPI Schema', () => {
  let mockOnChange: MockedFunction<(json: string) => void>;

  beforeEach(() => {
    mockOnChange = vi.fn();
  });

  // ── Mode switcher visibility ───────────────────────────────────────────────

  describe('mode switcher', () => {
    it('shows URL and Local file mode buttons when openapi_schema is configured', () => {
      render(<ConfigForm initialJson={makeJson()} onChange={mockOnChange} />);
      expect(screen.getByRole('button', { name: 'URL' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Local file' })).toBeInTheDocument();
    });

    it('does not show mode buttons when openapi_schema is absent', () => {
      const json = JSON.stringify({
        output: { type: 'nim' },
        declaration: {
          http: {
            servers: [
              {
                name: 'test-server',
                locations: [{ uri: '/test', urimatch: 'prefix', apigateway: {} }],
              },
            ],
          },
        },
      });
      render(<ConfigForm initialJson={json} onChange={mockOnChange} />);
      expect(screen.queryByRole('button', { name: 'URL' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Local file' })).not.toBeInTheDocument();
    });
  });

  // ── URL mode (default) ─────────────────────────────────────────────────────

  describe('URL mode (default)', () => {
    it('shows a URL text input with the expected placeholder', () => {
      const { container } = render(
        <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
      );
      expect(
        container.querySelector('input[placeholder="https://example.com/openapi.yaml"]')
      ).toBeInTheDocument();
    });

    it('does not show a file input in URL mode', () => {
      const { container } = render(
        <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
      );
      expect(container.querySelector('input[type="file"]')).not.toBeInTheDocument();
    });

    it('calls onChange with the typed URL in schema.content', async () => {
      const { container } = render(
        <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
      );
      const urlInput = container.querySelector(
        'input[placeholder="https://example.com/openapi.yaml"]'
      ) as HTMLInputElement;
      fireEvent.change(urlInput, { target: { value: 'https://example.com/spec.json' } });
      expect(lastSchemaContent(mockOnChange)).toBe('https://example.com/spec.json');
    });
  });

  // ── File mode ─────────────────────────────────────────────────────────────

  describe('Local file mode', () => {
    it('shows a file input after switching to Local file mode', async () => {
      const { container } = render(
        <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
      );
      await userEvent.click(screen.getByRole('button', { name: 'Local file' }));
      expect(container.querySelector('input[type="file"]')).toBeInTheDocument();
    });

    it('hides the URL text input after switching to Local file mode', async () => {
      const { container } = render(
        <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
      );
      await userEvent.click(screen.getByRole('button', { name: 'Local file' }));
      expect(
        container.querySelector('input[placeholder="https://example.com/openapi.yaml"]')
      ).not.toBeInTheDocument();
    });

    it('restores the URL text input when switching back to URL mode', async () => {
      const { container } = render(
        <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
      );
      await userEvent.click(screen.getByRole('button', { name: 'Local file' }));
      await userEvent.click(screen.getByRole('button', { name: 'URL' }));
      expect(
        container.querySelector('input[placeholder="https://example.com/openapi.yaml"]')
      ).toBeInTheDocument();
      expect(container.querySelector('input[type="file"]')).not.toBeInTheDocument();
    });

    it('accepts .json, .yaml, .yml files only', async () => {
      const { container } = render(
        <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
      );
      await userEvent.click(screen.getByRole('button', { name: 'Local file' }));
      const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
      expect(fileInput.accept).toBe('.json,.yaml,.yml');
    });

    // ── File reading + base64 encoding ───────────────────────────────────────

    describe('file reading', () => {
      // Capture the FileReader instance created by the component so we can
      // simulate readAsArrayBuffer completing inside the test.
      let capturedReader: { result: ArrayBuffer | null; onload: (() => void) | null };

      beforeEach(() => {
        capturedReader = { result: null, onload: null };

        class MockFileReader {
          result: ArrayBuffer | null = null;
          onload: (() => void) | null = null;

          readAsArrayBuffer(_file: Blob) {
            // Store a reference to `this` so the test can set result + fire onload
            capturedReader = this as unknown as typeof capturedReader;
          }
        }
        vi.stubGlobal('FileReader', MockFileReader);
      });

      afterEach(() => {
        vi.unstubAllGlobals();
      });

      it('base64-encodes the file content and passes it to onChange', async () => {
        const { container } = render(
          <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
        );
        await userEvent.click(screen.getByRole('button', { name: 'Local file' }));

        const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
        const fileContent = 'openapi: 3.0.0\ninfo:\n  title: Test';
        const file = new File([fileContent], 'api.yaml', { type: 'application/yaml' });
        Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
        fireEvent.change(fileInput);

        // Simulate FileReader finishing
        const arrayBuffer = new TextEncoder().encode(fileContent).buffer;
        act(() => {
          capturedReader.result = arrayBuffer;
          capturedReader.onload?.();
        });

        expect(mockOnChange).toHaveBeenCalled();
        expect(lastSchemaContent(mockOnChange)).toBe(btoa(fileContent));
      });

      it('shows an "Encoded (N bytes)" label after a file is read', async () => {
        const { container } = render(
          <ConfigForm initialJson={makeJson()} onChange={mockOnChange} />
        );
        await userEvent.click(screen.getByRole('button', { name: 'Local file' }));

        const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
        const fileContent = '{"openapi":"3.0.0"}';
        const file = new File([fileContent], 'api.json', { type: 'application/json' });
        Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
        fireEvent.change(fileInput);

        const arrayBuffer = new TextEncoder().encode(fileContent).buffer;
        act(() => {
          capturedReader.result = arrayBuffer;
          capturedReader.onload?.();
        });

        // After the file reader fires, ConfigForm re-renders with the encoded content,
        // which makes schema.content truthy and the label visible.
        expect(screen.getByText(/^Encoded \(\d+ bytes\)$/)).toBeInTheDocument();
      });
    });
  });
});
