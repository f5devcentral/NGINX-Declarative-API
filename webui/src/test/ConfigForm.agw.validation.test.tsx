import { describe, it, expect, vi, beforeEach, type MockedFunction } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfigForm } from '@/components/ConfigForm';

/** Build a minimal initialJson that has an apigateway with the given extra keys. */
const makeAgwJson = (agwExtra: Record<string, unknown> = {}) =>
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
                apigateway: { ...agwExtra },
              },
            ],
          },
        ],
      },
    },
  });

describe('ConfigForm — API Gateway: validation', () => {
  let mockOnChange: MockedFunction<(json: string) => void>;
  beforeEach(() => { mockOnChange = vi.fn(); });

  // ── OpenAPI Schema URL ────────────────────────────────────────────────────

  describe('OpenAPI Schema URL field', () => {
    it('shows a Required error when schema content is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ openapi_schema: { content: '' } })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show a Required error when schema content is set', () => {
      render(<ConfigForm initialJson={makeAgwJson({ openapi_schema: { content: 'https://example.com/spec.json' } })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  // ── API Gateway Settings ──────────────────────────────────────────────────

  describe('API Gateway Settings: Server URL', () => {
    it('shows a Required error when server_url is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ api_gateway: { enabled: true, strip_uri: false, server_url: '' } })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show a Required error when server_url is filled', () => {
      render(<ConfigForm initialJson={makeAgwJson({ api_gateway: { enabled: true, strip_uri: false, server_url: 'http://backend' } })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  // ── Developer Portal ──────────────────────────────────────────────────────

  describe('Developer Portal: Type', () => {
    it('shows a Required error when type is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ developer_portal: { enabled: true, type: '' } })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show a Required error when type is selected', () => {
      render(<ConfigForm initialJson={makeAgwJson({ developer_portal: { enabled: true, type: 'redocly', redocly: { uri: '/devportal.html' } } })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  describe('Developer Portal: Redocly URI', () => {
    it('shows a Required error when redocly URI is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ developer_portal: { enabled: true, type: 'redocly', redocly: { uri: '' } } })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });
  });

  describe('Developer Portal: Backstage fields', () => {
    it('shows Required errors for empty name, lifecycle, and owner', () => {
      render(<ConfigForm initialJson={makeAgwJson({ developer_portal: { enabled: true, type: 'backstage', backstage: { name: '', lifecycle: '', owner: '', system: '' } } })} onChange={mockOnChange} />);
      const errors = screen.getAllByText('Required');
      expect(errors.length).toBeGreaterThanOrEqual(3);
    });

    it('does not show Required error for fields that are filled', () => {
      render(<ConfigForm initialJson={makeAgwJson({ developer_portal: { enabled: true, type: 'backstage', backstage: { name: 'my-api', lifecycle: 'production', owner: 'team', system: '' } } })} onChange={mockOnChange} />);
      // name, lifecycle, owner are filled — only system is empty but it's not required
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  // ── Rate Limiting ─────────────────────────────────────────────────────────

  describe('Rate Limiting: Profile', () => {
    it('shows a Required error when profile is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ rate_limit: [{ profile: '', httpcode: 429, burst: 0, delay: 0 }] })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show a Required error when profile is filled', () => {
      render(<ConfigForm initialJson={makeAgwJson({ rate_limit: [{ profile: 'my-limit', httpcode: 429, burst: 0, delay: 0 }] })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  // ── Authentication ────────────────────────────────────────────────────────

  describe('Authentication: Client profiles', () => {
    it('shows an error when all client profiles are empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ authentication: { client: [{ profile: '' }], enforceOnPaths: true, paths: [] } })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show an error when a client profile is filled', () => {
      render(<ConfigForm initialJson={makeAgwJson({ authentication: { client: [{ profile: 'jwt-auth' }], enforceOnPaths: true, paths: [] } })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  // ── Authorization ─────────────────────────────────────────────────────────

  describe('Authorization: Profile', () => {
    it('shows a Required error when profile is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ authorization: [{ profile: '', enforceOnPaths: true, paths: [] }] })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show a Required error when profile is filled', () => {
      render(<ConfigForm initialJson={makeAgwJson({ authorization: [{ profile: 'my-authz', enforceOnPaths: true, paths: [] }] })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  // ── Cache ─────────────────────────────────────────────────────────────────

  describe('Cache: Profile', () => {
    it('shows a Required error when profile is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ cache: [{ profile: '' }] })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show a Required error when profile is filled', () => {
      render(<ConfigForm initialJson={makeAgwJson({ cache: [{ profile: 'my-cache' }] })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  // ── Visibility ────────────────────────────────────────────────────────────

  describe('Visibility: Type', () => {
    it('shows a Required error when type is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ visibility: [{ enabled: true, type: '' }] })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show a Required error when type is selected', () => {
      render(<ConfigForm initialJson={makeAgwJson({ visibility: [{ enabled: true, type: 'moesif', moesif: { application_id: 'abc123', plugin_path: '/path' } }] })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });

  describe('Visibility: Moesif Application ID', () => {
    it('shows a Required error when application_id is empty', () => {
      render(<ConfigForm initialJson={makeAgwJson({ visibility: [{ enabled: true, type: 'moesif', moesif: { application_id: '', plugin_path: '/path' } }] })} onChange={mockOnChange} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('does not show a Required error when application_id is filled', () => {
      render(<ConfigForm initialJson={makeAgwJson({ visibility: [{ enabled: true, type: 'moesif', moesif: { application_id: 'my-app-id', plugin_path: '/path' } }] })} onChange={mockOnChange} />);
      expect(screen.queryByText('Required')).not.toBeInTheDocument();
    });
  });
});
