import { useState, useRef, type ReactNode } from 'react';
import type { APIGateway, HttpProfiles, AGWDeveloperPortal } from './types';
import { emptyAGWRateLimit, emptyAGWAuthorization, emptyAGWCache, emptyAGWVisibility } from './defaults';
import { Field, TextInput, NumberInput, SelectInput, ProfileSelect, Toggle, AddBtn, RemoveBtn } from './primitives';

export function PathsInput({
  value, onChange, placeholder,
}: { value: string[]; onChange: (v: string[]) => void; placeholder?: string }) {
  return (
    <textarea
      className="cf-input cf-textarea-sm cf-mono"
      rows={3}
      placeholder={placeholder ?? '/path/one\n/path/two'}
      value={value.join('\n')}
      onChange={e => onChange(e.target.value.split('\n').filter(Boolean))}
      autoComplete="off"
      spellCheck={false}
    />
  );
}

export function AgwCard({
  title, right, children,
}: { title: string; right: ReactNode; children?: ReactNode }) {
  return (
    <div className="cf-agw-card">
      <div className="cf-agw-card-header">
        <span className="cf-agw-card-title">{title}</span>
        {right}
      </div>
      {children && <div className="cf-agw-card-body">{children}</div>}
    </div>
  );
}

export function ApiGatewayEditor({
  agw, onChange, profiles = { rateLimitNames: [], authClientNames: [], authServerNames: [], authzNames: [], cacheNames: [] },
}: { agw: APIGateway | undefined; onChange: (agw: APIGateway | undefined) => void; profiles?: HttpProfiles }) {
  const enabled = agw != null;
  const g = agw ?? {};
  const [schemaInputMode, setSchemaInputMode] = useState<'url' | 'file'>('url');
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!enabled) {
    return (
      <div className="cf-subsection cf-subsection-agw">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">API Gateway</span>
          <Toggle checked={false} onChange={v => v && onChange({})} label="Disabled" />
        </div>
      </div>
    );
  }

  // — OpenAPI Schema —
  const schemaEnabled = g.openapi_schema != null;
  const schema = g.openapi_schema ?? {};

  // — API Gateway settings —
  const apiGwEnabled = g.api_gateway != null;
  const apiGw = g.api_gateway ?? {};

  // — Developer Portal —
  const devPortalEnabled = g.developer_portal != null;
  const dp = g.developer_portal ?? {};

  // — Rate Limiting —
  const rateLimits = g.rate_limit ?? [];

  // — Authentication —
  const authEnabled = g.authentication != null;
  const auth = g.authentication ?? {};

  // — Authorization —
  const authzItems = g.authorization ?? [];

  // — Cache —
  const cacheItems = g.cache ?? [];

  // — Visibility —
  const visibilityItems = g.visibility ?? [];

  return (
    <div className="cf-subsection cf-subsection-agw">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">API Gateway</span>
        <Toggle checked={true} onChange={v => !v && onChange(undefined)} label="Enabled" />
      </div>

      {/* OpenAPI Schema */}
      <AgwCard
        title="OpenAPI Schema"
        right={
          <Toggle
            checked={schemaEnabled}
            onChange={v => onChange(v ? { ...g, openapi_schema: { content: '' } } : { ...g, openapi_schema: undefined })}
            label={schemaEnabled ? 'Configured' : 'Not configured'}
          />
        }
      >
        {schemaEnabled && (
          <>
            <div className="cf-agw-schema-mode">
              <button
                className={`cf-agw-mode-btn${schemaInputMode === 'url' ? ' active' : ''}`}
                onClick={() => setSchemaInputMode('url')}
                type="button"
              >URL</button>
              <button
                className={`cf-agw-mode-btn${schemaInputMode === 'file' ? ' active' : ''}`}
                onClick={() => { setSchemaInputMode('file'); onChange({ ...g, openapi_schema: { ...schema, content: '' } }); }}
                type="button"
              >Local file</button>
            </div>
            {schemaInputMode === 'url' ? (
              <Field label="URL" span="full"
                hint="HTTP/HTTPS URL to the OpenAPI schema (JSON or YAML)."
                error={!schema.content?.trim() ? 'Required' : undefined}>
                <TextInput
                  value={schema.content ?? ''}
                  onChange={v => onChange({ ...g, openapi_schema: { ...schema, content: v } })}
                  placeholder="https://example.com/openapi.yaml"
                  mono
                  error={!schema.content?.trim()}
                />
              </Field>
            ) : (
              <Field label="File" span="full"
                hint="Select a local OpenAPI JSON or YAML file. It will be base64-encoded and stored in the declaration.">
                <div className="cf-agw-file-row">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".json,.yaml,.yml"
                    className="cf-agw-file-input"
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      const reader = new FileReader();
                      reader.onload = () => {
                        const b64 = btoa(
                          new Uint8Array(reader.result as ArrayBuffer)
                            .reduce((s, b) => s + String.fromCharCode(b), '')
                        );
                        onChange({ ...g, openapi_schema: { ...schema, content: b64 } });
                      };
                      reader.readAsArrayBuffer(file);
                    }}
                  />
                  {schema.content && (
                    <span className="cf-agw-file-ok">Encoded ({Math.ceil(schema.content.length * 3 / 4)} bytes)</span>
                  )}
                </div>
              </Field>
            )}
          </>
        )}
      </AgwCard>

      {/* API Gateway Settings */}
      <AgwCard
        title="API Gateway Settings"
        right={
          <Toggle
            checked={apiGwEnabled}
            onChange={v => onChange(v
              ? { ...g, api_gateway: { enabled: true, strip_uri: false, server_url: '' } }
              : { ...g, api_gateway: undefined })}
            label={apiGwEnabled ? 'Configured' : 'Not configured'}
          />
        }
      >
        {apiGwEnabled && (
          <div className="cf-grid-2">
            <Field label="Server URL"
              hint='Full URL of the upstream API server for proxy_pass. Example: "http://api-backend".'
              error={!apiGw.server_url?.trim() ? 'Required' : undefined}>
              <TextInput
                value={apiGw.server_url ?? ''}
                onChange={v => onChange({ ...g, api_gateway: { ...apiGw, server_url: v } })}
                placeholder="http://api-backend"
                mono
                error={!apiGw.server_url?.trim()}
              />
            </Field>
            <Field label="Options">
              <div className="cf-agw-toggles">
                <Toggle
                  checked={apiGw.enabled ?? true}
                  onChange={v => onChange({ ...g, api_gateway: { ...apiGw, enabled: v } })}
                  label="Enabled"
                />
                <Toggle
                  checked={apiGw.strip_uri ?? false}
                  onChange={v => onChange({ ...g, api_gateway: { ...apiGw, strip_uri: v } })}
                  label="Strip URI prefix"
                />
              </div>
            </Field>
          </div>
        )}
      </AgwCard>

      {/* Developer Portal */}
      <AgwCard
        title="Developer Portal"
        right={
          <Toggle
            checked={devPortalEnabled}
            onChange={v => onChange(v
              ? { ...g, developer_portal: { enabled: true, type: 'redocly', redocly: { uri: '/devportal.html' } } }
              : { ...g, developer_portal: undefined })}
            label={devPortalEnabled ? 'Configured' : 'Not configured'}
          />
        }
      >
        {devPortalEnabled && (
          <>
            <div className="cf-grid-2">
              <Field label="Type"
                hint='"redocly" serves an HTML viewer for the OpenAPI spec. "backstage" registers the API in Backstage.'
                error={!dp.type ? 'Required' : undefined}>
                <SelectInput
                  value={dp.type ?? ''}
                  onChange={v => {
                    const next: AGWDeveloperPortal = { ...dp, type: v };
                    if (v === 'redocly' && !next.redocly) next.redocly = { uri: '/devportal.html' };
                    if (v === 'backstage' && !next.backstage) next.backstage = { name: '', lifecycle: 'production', owner: '', system: '' };
                    onChange({ ...g, developer_portal: next });
                  }}
                  options={[
                    { value: '',          label: '— select type —' },
                    { value: 'redocly',   label: 'Redocly (HTML viewer)' },
                    { value: 'backstage', label: 'Backstage (catalog)' },
                  ]}
                  error={!dp.type}
                />
              </Field>
              <Field label="Enable">
                <Toggle
                  checked={dp.enabled ?? true}
                  onChange={v => onChange({ ...g, developer_portal: { ...dp, enabled: v } })}
                  label={dp.enabled ?? true ? 'Enabled' : 'Disabled'}
                />
              </Field>
            </div>
            {dp.type === 'redocly' && (
              <Field label="Redocly URI" hint='URI path that serves the Redocly HTML viewer. Example: "/devportal.html".'
                error={!dp.redocly?.uri?.trim() ? 'Required' : undefined}>
                <TextInput
                  value={dp.redocly?.uri ?? '/devportal.html'}
                  onChange={v => onChange({ ...g, developer_portal: { ...dp, redocly: { uri: v } } })}
                  placeholder="/devportal.html"
                  mono
                  error={!dp.redocly?.uri?.trim()}
                />
              </Field>
            )}
            {dp.type === 'backstage' && (
              <div className="cf-grid-2">
                <Field label="Name" hint="API name as it will appear in Backstage."
                  error={!dp.backstage?.name?.trim() ? 'Required' : undefined}>
                  <TextInput value={dp.backstage?.name ?? ''} onChange={v => onChange({ ...g, developer_portal: { ...dp, backstage: { ...(dp.backstage ?? {}), name: v } } })} placeholder="my-api" error={!dp.backstage?.name?.trim()} />
                </Field>
                <Field label="Lifecycle" hint='Backstage lifecycle stage, e.g. "production" or "experimental".'
                  error={!dp.backstage?.lifecycle?.trim() ? 'Required' : undefined}>
                  <TextInput value={dp.backstage?.lifecycle ?? 'production'} onChange={v => onChange({ ...g, developer_portal: { ...dp, backstage: { ...(dp.backstage ?? {}), lifecycle: v } } })} placeholder="production" error={!dp.backstage?.lifecycle?.trim()} />
                </Field>
                <Field label="Owner" hint="Team or user that owns this API in Backstage."
                  error={!dp.backstage?.owner?.trim() ? 'Required' : undefined}>
                  <TextInput value={dp.backstage?.owner ?? ''} onChange={v => onChange({ ...g, developer_portal: { ...dp, backstage: { ...(dp.backstage ?? {}), owner: v } } })} placeholder="team-platform" error={!dp.backstage?.owner?.trim()} />
                </Field>
                <Field label="System" hint="Optional Backstage system this API belongs to.">
                  <TextInput value={dp.backstage?.system ?? ''} onChange={v => onChange({ ...g, developer_portal: { ...dp, backstage: { ...(dp.backstage ?? {}), system: v } } })} placeholder="api-platform" />
                </Field>
              </div>
            )}
          </>
        )}
      </AgwCard>

      {/* Rate Limiting */}
      <AgwCard
        title="Rate Limiting"
        right={<AddBtn label="Add rule" onClick={() => onChange({ ...g, rate_limit: [...rateLimits, emptyAGWRateLimit()] })} />}
      >
        {rateLimits.length === 0
          ? <p className="cf-empty cf-empty-sm">No rate limiting rules. Add one to reference a pre-defined rate limit profile.</p>
          : rateLimits.map((rl, ri) => (
            <div key={ri} className="cf-agw-item-row">
              <Field label="Profile" hint="Name of the rate limit profile defined in the HTTP section."
                error={!rl.profile?.trim() ? 'Required' : undefined}>
                <ProfileSelect value={rl.profile ?? ''} onChange={v => onChange({
                  ...g,
                  rate_limit: rateLimits.map((x, idx) => idx === ri
                    ? { ...x, profile: v, enforceOnPaths: x.enforceOnPaths ?? true, paths: x.paths ?? [] }
                    : x)
                })} options={profiles.rateLimitNames} placeholder="my-rate-limit" error={!rl.profile?.trim()} />
              </Field>
              <Field label="HTTP code" hint="Status code returned when rate-limited.">
                <NumberInput value={rl.httpcode ?? 429} onChange={v => onChange({ ...g, rate_limit: rateLimits.map((x, idx) => idx === ri ? { ...x, httpcode: v } : x) })} />
              </Field>
              <Field label="Burst" hint="Extra requests to queue before rejecting. 0 = no burst.">
                <NumberInput value={rl.burst ?? 0} onChange={v => onChange({ ...g, rate_limit: rateLimits.map((x, idx) => idx === ri ? { ...x, burst: v } : x) })} />
              </Field>
              <Field label="Delay" hint="Requests to delay before the limit applies. 0 = nodelay.">
                <NumberInput value={rl.delay ?? 0} onChange={v => onChange({ ...g, rate_limit: rateLimits.map((x, idx) => idx === ri ? { ...x, delay: v } : x) })} />
              </Field>
              <Field label="Paths" hint="Paths this rule applies to, one per line. Empty = all paths.">
                <PathsInput value={rl.paths ?? []} onChange={v => onChange({ ...g, rate_limit: rateLimits.map((x, idx) => idx === ri ? { ...x, paths: v } : x) })} />
              </Field>
              <Field label="Enforce on paths">
                <Toggle checked={rl.enforceOnPaths ?? true} onChange={v => onChange({ ...g, rate_limit: rateLimits.map((x, idx) => idx === ri ? { ...x, enforceOnPaths: v } : x) })} label={rl.enforceOnPaths ?? true ? 'Yes' : 'No'} />
              </Field>
              <div className="cf-agw-item-remove"><RemoveBtn onClick={() => onChange({ ...g, rate_limit: rateLimits.filter((_, idx) => idx !== ri) })} /></div>
            </div>
          ))
        }
      </AgwCard>

      {/* Authentication */}
      <AgwCard
        title="Authentication"
        right={
          <Toggle
            checked={authEnabled}
            onChange={v => onChange(v
              ? { ...g, authentication: { client: [{ profile: '' }], enforceOnPaths: true, paths: [] } }
              : { ...g, authentication: undefined })}
            label={authEnabled ? 'Configured' : 'Not configured'}
          />
        }
      >
        {authEnabled && (
          <div className="cf-grid-2">
            <div>
              <div className="cf-subsection-header" style={{ marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>Client profiles</span>
                <AddBtn label="Add" onClick={() => onChange({
                  ...g,
                  authentication: {
                    ...auth,
                    enforceOnPaths: auth.enforceOnPaths ?? true,
                    paths: auth.paths ?? [],
                    client: [...(auth.client ?? []), { profile: '' }],
                  }
                })} />
              </div>
              {(auth.client ?? []).length === 0
                ? <p className="cf-hint">No client profiles. Add one to reference an authentication profile.</p>
                : (auth.client ?? []).map((ac, aci) => (
                  <div key={aci} className="cf-agw-item-row" style={{ marginBottom: '0.4rem' }}>
                    <Field label={`Profile ${aci + 1}`} required error={!ac.profile?.trim() ? 'Required' : undefined}>
                      <ProfileSelect
                        value={ac.profile ?? ''}
                        onChange={v => onChange({
                          ...g,
                          authentication: {
                            ...auth,
                            enforceOnPaths: auth.enforceOnPaths ?? true,
                            paths: auth.paths ?? [],
                            client: (auth.client ?? []).map((x, j) => j === aci ? { ...x, profile: v } : x),
                          }
                        })}
                        options={profiles.authClientNames}
                        placeholder="jwt-auth"
                        error={!ac.profile?.trim()}
                      />
                    </Field>
                    <div className="cf-agw-item-remove">
                      <RemoveBtn onClick={() => onChange({ ...g, authentication: { ...auth, client: (auth.client ?? []).filter((_, j) => j !== aci) } })} />
                    </div>
                  </div>
                ))
              }
            </div>
            <div>
              <Field label="Enforce on paths">
                <Toggle
                  checked={auth.enforceOnPaths ?? true}
                  onChange={v => onChange({ ...g, authentication: { ...auth, enforceOnPaths: v } })}
                  label={auth.enforceOnPaths ?? true ? 'Yes' : 'No'}
                />
              </Field>
              <Field label="Paths" hint="Paths this policy applies to, one per line. Empty = all paths.">
                <PathsInput value={auth.paths ?? []} onChange={v => onChange({ ...g, authentication: { ...auth, paths: v } })} />
              </Field>
            </div>
          </div>
        )}
      </AgwCard>

      {/* Authorization */}
      <AgwCard
        title="Authorization"
        right={<AddBtn label="Add profile" onClick={() => onChange({ ...g, authorization: [...authzItems, emptyAGWAuthorization()] })} />}
      >
        {authzItems.length === 0
          ? <p className="cf-empty cf-empty-sm">No authorization rules. Add a profile reference to enforce access control.</p>
          : authzItems.map((az, ai) => (
            <div key={ai} className="cf-agw-item-row">
              <Field label="Profile" required hint="Name of an authorization profile defined in the HTTP section."
                error={!az.profile?.trim() ? 'Required' : undefined}>
                <ProfileSelect value={az.profile} onChange={v => onChange({
                  ...g,
                  authorization: authzItems.map((x, idx) => idx === ai
                    ? { ...x, profile: v, enforceOnPaths: x.enforceOnPaths ?? true, paths: x.paths ?? [] }
                    : x)
                })} options={profiles.authzNames} placeholder="my-authz-profile" error={!az.profile?.trim()} />
              </Field>
              <Field label="Paths" hint="Paths this rule applies to, one per line. Empty = all.">
                <PathsInput value={az.paths ?? []} onChange={v => onChange({ ...g, authorization: authzItems.map((x, idx) => idx === ai ? { ...x, paths: v } : x) })} />
              </Field>
              <Field label="Enforce on paths">
                <Toggle checked={az.enforceOnPaths ?? true} onChange={v => onChange({ ...g, authorization: authzItems.map((x, idx) => idx === ai ? { ...x, enforceOnPaths: v } : x) })} label={az.enforceOnPaths ?? true ? 'Yes' : 'No'} />
              </Field>
              <div className="cf-agw-item-remove"><RemoveBtn onClick={() => onChange({ ...g, authorization: authzItems.filter((_, idx) => idx !== ai) })} /></div>
            </div>
          ))
        }
      </AgwCard>

      {/* Cache */}
      <AgwCard
        title="Cache"
        right={<AddBtn label="Add profile" onClick={() => onChange({ ...g, cache: [...cacheItems, emptyAGWCache()] })} />}
      >
        {cacheItems.length === 0
          ? <p className="cf-empty cf-empty-sm">No cache configurations. Add a profile reference to enable response caching.</p>
          : cacheItems.map((c, ci) => (
            <div key={ci} className="cf-agw-item-row">
              <Field label="Profile" required hint="Name of a cache zone profile defined in the HTTP section."
                error={!c.profile?.trim() ? 'Required' : undefined}>
                <ProfileSelect value={c.profile} onChange={v => onChange({ ...g, cache: cacheItems.map((x, idx) => idx === ci ? { ...x, profile: v } : x) })} options={profiles.cacheNames} placeholder="my-cache" error={!c.profile?.trim()} />
              </Field>
              <Field label="Cache key" hint='NGINX variable expression for the cache key.'>
                <TextInput value={c.key ?? '$scheme$proxy_host$request_uri'} onChange={v => onChange({ ...g, cache: cacheItems.map((x, idx) => idx === ci ? { ...x, key: v } : x) })} placeholder="$scheme$proxy_host$request_uri" mono />
              </Field>
              <Field label="Paths" hint="Paths this cache applies to, one per line. Empty = all.">
                <PathsInput value={c.paths ?? []} onChange={v => onChange({ ...g, cache: cacheItems.map((x, idx) => idx === ci ? { ...x, paths: v } : x) })} />
              </Field>
              <Field label="Enforce on paths">
                <Toggle checked={c.enforceOnPaths ?? true} onChange={v => onChange({ ...g, cache: cacheItems.map((x, idx) => idx === ci ? { ...x, enforceOnPaths: v } : x) })} label={c.enforceOnPaths ?? true ? 'Yes' : 'No'} />
              </Field>
              <div className="cf-agw-item-remove"><RemoveBtn onClick={() => onChange({ ...g, cache: cacheItems.filter((_, idx) => idx !== ci) })} /></div>
            </div>
          ))
        }
      </AgwCard>

      {/* Visibility */}
      <AgwCard
        title="Visibility"
        right={<AddBtn label="Add provider" onClick={() => onChange({ ...g, visibility: [...visibilityItems, emptyAGWVisibility()] })} />}
      >
        {visibilityItems.length === 0
          ? <p className="cf-empty cf-empty-sm">No visibility providers configured.</p>
          : visibilityItems.map((vis, vi) => (
            <div key={vi} className="cf-agw-item-row">
              <Field label="Type" hint='"moesif" enables API analytics via the Moesif NGINX plugin.'
                error={!vis.type ? 'Required' : undefined}>
                <SelectInput
                  value={vis.type ?? ''}
                  onChange={v => {
                    const next = { ...vis, type: v };
                    if (v === 'moesif' && !next.moesif) next.moesif = { application_id: '', plugin_path: '/usr/local/share/lua/5.1/resty/moesif' };
                    onChange({ ...g, visibility: visibilityItems.map((x, idx) => idx === vi ? next : x) });
                  }}
                  options={[
                    { value: '',       label: '— select type —' },
                    { value: 'moesif', label: 'Moesif (API analytics)' },
                  ]}
                  error={!vis.type}
                />
              </Field>
              <Field label="Enable">
                <Toggle checked={vis.enabled ?? true} onChange={v => onChange({ ...g, visibility: visibilityItems.map((x, idx) => idx === vi ? { ...x, enabled: v } : x) })} label={vis.enabled ?? true ? 'Enabled' : 'Disabled'} />
              </Field>
              {vis.type === 'moesif' && (
                <>
                  <Field label="Application ID" required hint="Your Moesif application ID from the Moesif dashboard."
                    error={!vis.moesif?.application_id?.trim() ? 'Required' : undefined}>
                    <TextInput value={vis.moesif?.application_id ?? ''} onChange={v => onChange({ ...g, visibility: visibilityItems.map((x, idx) => idx === vi ? { ...x, moesif: { ...(x.moesif ?? {}), application_id: v } } : x) })} placeholder="your-moesif-app-id" error={!vis.moesif?.application_id?.trim()} />
                  </Field>
                  <Field label="Plugin path" hint='Path to the Moesif Lua plugin. Default: "/usr/local/share/lua/5.1/resty/moesif".'>
                    <TextInput value={vis.moesif?.plugin_path ?? '/usr/local/share/lua/5.1/resty/moesif'} onChange={v => onChange({ ...g, visibility: visibilityItems.map((x, idx) => idx === vi ? { ...x, moesif: { ...(x.moesif ?? {}), plugin_path: v } } : x) })} placeholder="/usr/local/share/lua/5.1/resty/moesif" mono />
                  </Field>
                </>
              )}
              <div className="cf-agw-item-remove"><RemoveBtn onClick={() => onChange({ ...g, visibility: visibilityItems.filter((_, idx) => idx !== vi) })} /></div>
            </div>
          ))
        }
      </AgwCard>
    </div>
  );
}
