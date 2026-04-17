import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import { ConfigForm } from '@/components/ConfigForm';

describe('ConfigForm — API Gateway: profile dropdown population', () => {
  let mockOnChange: (json: string) => void;
  beforeEach(() => { mockOnChange = vi.fn(); });

  const makeJsonWithProfiles = () => JSON.stringify({
    output: { type: 'nms' },
    declaration: {
      http: {
        rate_limit: [{ name: 'petstore_ratelimit', key: '$binary_remote_addr', size: '10m', rate: '10r/s' }],
        authentication: {
          client: [{ name: 'jwt-client-auth', type: 'jwt', jwt: { realm: 'api', key: 'secret', jwt_type: 'signed', cachetime: 0, token_location: '' } }],
          server: [],
        },
        authorization: [{ name: 'jwt-authz', type: 'jwt', jwt: { claims: [] } }],
        cache: [{ name: 'my-cache', basepath: '/tmp/cache', size: '10m', ttl: '10m' }],
        servers: [{
          name: 'test',
          locations: [{
            uri: '/',
            urimatch: 'prefix',
            apigateway: {
              rate_limit: [{ profile: '', httpcode: 429, burst: 0, delay: 0 }],
              authentication: { client: [{ profile: '' }], enforceOnPaths: true, paths: [] },
              authorization: [{ profile: '', enforceOnPaths: true, paths: [] }],
              cache: [{ profile: '', key: '$scheme$proxy_host$request_uri', paths: [], enforceOnPaths: true }],
            }
          }]
        }]
      }
    }
  });

  it('populates rate limit dropdown with HTTP-level rate_limit profile names', () => {
    const { container } = render(<ConfigForm initialJson={makeJsonWithProfiles()} onChange={mockOnChange} />);
    const selects = container.querySelectorAll('select');
    const rateLimitSelect = Array.from(selects).find(s =>
      Array.from(s.options).some(o => o.value === 'petstore_ratelimit')
    );
    expect(rateLimitSelect).toBeDefined();
  });

  it('populates auth client dropdown with HTTP-level authentication.client profile names', () => {
    const { container } = render(<ConfigForm initialJson={makeJsonWithProfiles()} onChange={mockOnChange} />);
    const selects = container.querySelectorAll('select');
    const authSelect = Array.from(selects).find(s =>
      Array.from(s.options).some(o => o.value === 'jwt-client-auth')
    );
    expect(authSelect).toBeDefined();
  });

  it('populates authorization dropdown with HTTP-level authorization profile names', () => {
    const { container } = render(<ConfigForm initialJson={makeJsonWithProfiles()} onChange={mockOnChange} />);
    const selects = container.querySelectorAll('select');
    const authzSelect = Array.from(selects).find(s =>
      Array.from(s.options).some(o => o.value === 'jwt-authz')
    );
    expect(authzSelect).toBeDefined();
  });

  it('populates cache dropdown with HTTP-level cache profile names', () => {
    const { container } = render(<ConfigForm initialJson={makeJsonWithProfiles()} onChange={mockOnChange} />);
    const selects = container.querySelectorAll('select');
    const cacheSelect = Array.from(selects).find(s =>
      Array.from(s.options).some(o => o.value === 'my-cache')
    );
    expect(cacheSelect).toBeDefined();
  });
});

describe('ConfigForm — API Gateway: live profile typing', () => {
  let mockOnChange: (json: string) => void;
  beforeEach(() => { mockOnChange = vi.fn(); });

  it('populates the rate limit dropdown after the user types a name in ProfilesSection', async () => {
    // Start with an AGW location and one rate limit rule, but NO http.rate_limit profiles yet
    const initialJson = JSON.stringify({
      output: { type: 'nms' },
      declaration: {
        http: {
          servers: [{
            name: 'test',
            locations: [{
              uri: '/', urimatch: 'prefix',
              apigateway: {
                rate_limit: [{ profile: '', httpcode: 429, burst: 0, delay: 0 }]
              }
            }]
          }]
        }
      }
    });

    const { container } = render(<ConfigForm initialJson={initialJson} onChange={mockOnChange} />);

    // Initially: no rate limit profiles defined — AGW dropdown should be disabled
    const initialSelects = container.querySelectorAll('select');
    const initialRateLimitSelect = Array.from(initialSelects).find(s =>
      Array.from(s.options).some(o => o.text.includes('no profiles defined'))
    );
    expect(initialRateLimitSelect).toBeDefined();

    // Find the "Rate Limiting" subsection header specifically inside ProfilesSection.
    // ProfilesSection is the FIRST section in HttpSection, so its "Rate Limiting" header
    // comes before the location-level "Rate Limiting" header (which has a Toggle, not AddBtn).
    const subsectionHeaders = container.querySelectorAll('.cf-subsection-header');
    const rateLimitHeader = Array.from(subsectionHeaders).find(h =>
      h.querySelector('.cf-subsection-title')?.textContent === 'Rate Limiting' &&
      h.querySelector('.cf-btn-add') != null
    );
    expect(rateLimitHeader).toBeDefined();

    const addProfileBtn = rateLimitHeader!.querySelector('.cf-btn-add') as HTMLElement;
    fireEvent.click(addProfileBtn);

    // A name input should now appear for the new rate limit profile
    const nameInputs = Array.from(container.querySelectorAll('input[placeholder="petstore_ratelimit"]'));
    expect(nameInputs.length).toBeGreaterThan(0);

    // Type a name
    fireEvent.change(nameInputs[0], { target: { value: 'my-rate-limit' } });

    // Now the AGW rate limit dropdown should be populated
    const updatedSelects = container.querySelectorAll('select');
    const populatedSelect = Array.from(updatedSelects).find(s =>
      Array.from(s.options).some(o => o.value === 'my-rate-limit')
    );
    expect(populatedSelect).toBeDefined();
  });
});
