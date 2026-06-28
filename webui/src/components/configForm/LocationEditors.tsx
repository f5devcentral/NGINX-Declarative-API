import type {
  Log, AppProtect, SourceOfTruth, LocationHeaders, LocationAuth, AuthzRef,
  CacheItem, RateLimitRef, HealthCheck, NjsHookServer, NjsHookLocation,
} from './types';
import { emptyNjsHookServer, emptyNjsHookLocation } from './defaults';
import { Field, TextInput, NumberInput, SelectInput, ProfileSelect, Toggle, AddBtn, RemoveBtn } from './primitives';

// ─── Constants ────────────────────────────────────────────────────────────────

export const LOG_ERROR_LEVELS = [
  { value: 'debug', label: 'debug' }, { value: 'info', label: 'info' },
  { value: 'notice', label: 'notice' }, { value: 'warn', label: 'warn' },
  { value: 'error', label: 'error' }, { value: 'crit', label: 'crit' },
  { value: 'alert', label: 'alert' }, { value: 'emerg', label: 'emerg' },
];

export const NJS_SERVER_HOOK_TYPES = [
  { value: 'js_preload_object', label: 'js_preload_object' },
  { value: 'js_set', label: 'js_set' },
];

export const NJS_LOCATION_HOOK_TYPES = [
  { value: 'js_body_filter', label: 'js_body_filter' },
  { value: 'js_content', label: 'js_content' },
  { value: 'js_header_filter', label: 'js_header_filter' },
  { value: 'js_periodic', label: 'js_periodic' },
  { value: 'js_preload_object', label: 'js_preload_object' },
  { value: 'js_set', label: 'js_set' },
];

// ─── Log Editor ───────────────────────────────────────────────────────────────

export function LogEditor({ log, onChange }: { log: Log | undefined; onChange: (l: Log | undefined) => void }) {
  const enabled = log != null && (!!log.access || !!log.error);
  const l = log ?? {};

  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Logging</span>
        <Toggle
          checked={enabled}
          onChange={v => onChange(v ? { access: { destination: 'syslog:server=127.0.0.1', format: 'combined' }, error: { destination: 'syslog:server=127.0.0.1', level: 'info' } } : undefined)}
          label={enabled ? 'Configured' : 'Not configured'}
        />
      </div>
      {enabled && (
        <div className="cf-grid-2">
          <Field label="Access log destination" hint='Destination for access logs, e.g. "/var/log/nginx/access.log" or "syslog:server=...".'>
            <TextInput value={l.access?.destination ?? ''} onChange={v => onChange({ ...l, access: { ...(l.access ?? { destination: '', format: 'combined' }), destination: v } })} placeholder="/var/log/nginx/access.log" mono />
          </Field>
          <Field label="Access log format" hint='Log format name. Use "combined" for the default combined format.'>
            <TextInput value={l.access?.format ?? 'combined'} onChange={v => onChange({ ...l, access: { ...(l.access ?? { destination: '' }), format: v } })} placeholder="combined" mono />
          </Field>
          <Field label="Error log destination" hint='Destination for error logs, e.g. "/var/log/nginx/error.log" or "syslog:server=...".'>
            <TextInput value={l.error?.destination ?? ''} onChange={v => onChange({ ...l, error: { ...(l.error ?? { destination: '', level: 'info' }), destination: v } })} placeholder="/var/log/nginx/error.log" mono />
          </Field>
          <Field label="Error log level">
            <SelectInput value={l.error?.level ?? 'info'} onChange={v => onChange({ ...l, error: { ...(l.error ?? { destination: '' }), level: v } })} options={LOG_ERROR_LEVELS} />
          </Field>
        </div>
      )}
    </div>
  );
}

// ─── App Protect Editor ───────────────────────────────────────────────────────

export function AppProtectEditor({ ap, onChange }: { ap: AppProtect | undefined; onChange: (a: AppProtect | undefined) => void }) {
  const enabled = ap != null;
  const a = ap ?? { enabled: false, policy: '' };

  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">App Protect WAF</span>
        <Toggle
          checked={enabled}
          onChange={v => onChange(v ? { enabled: true, policy: '', log: { enabled: false, profile_name: '', destination: '' } } : undefined)}
          label={enabled ? 'Configured' : 'Not configured'}
        />
      </div>
      {enabled && (
        <div className="cf-grid-2">
          <Field label="Policy name" required hint="Name of the App Protect policy (as defined in the output policies section)."
            error={!a.policy?.trim() ? 'Required' : undefined}>
            <TextInput value={a.policy} onChange={v => onChange({ ...a, policy: v })} placeholder="production-policy" error={!a.policy?.trim()} />
          </Field>
          <Field label="Enabled">
            <Toggle checked={a.enabled ?? true} onChange={v => onChange({ ...a, enabled: v })} label={a.enabled ?? true ? 'Yes' : 'No'} />
          </Field>
          <Field label="Log profile" hint="Name of the App Protect log profile to use.">
            <TextInput value={a.log?.profile_name ?? ''} onChange={v => onChange({ ...a, log: { ...(a.log ?? { enabled: true, destination: '' }), profile_name: v } })} placeholder="log_all" mono />
          </Field>
          <Field label="Log destination" hint='Log destination, e.g. "syslog:server=127.0.0.1:5144".'>
            <TextInput value={a.log?.destination ?? ''} onChange={v => onChange({ ...a, log: { ...(a.log ?? { enabled: true, profile_name: '' }), destination: v } })} placeholder="syslog:server=127.0.0.1:5144" mono />
          </Field>
          <Field label="Log enabled">
            <Toggle checked={a.log?.enabled ?? true} onChange={v => onChange({ ...a, log: { ...(a.log ?? { profile_name: '', destination: '' }), enabled: v } })} label={a.log?.enabled ?? true ? 'Yes' : 'No'} />
          </Field>
        </div>
      )}
    </div>
  );
}

// ─── Snippet Editor ───────────────────────────────────────────────────────────

export function SnippetEditor({ snippet, onChange }: { snippet: SourceOfTruth | undefined; onChange: (s: SourceOfTruth | undefined) => void }) {
  const enabled = snippet != null;

  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Snippet</span>
        <Toggle
          checked={enabled}
          onChange={v => onChange(v ? { content: '' } : undefined)}
          label={enabled ? 'Configured' : 'Not configured'}
        />
      </div>
      {enabled && (
        <Field label="Content / URL" span="full" hint='URL or inline NGINX configuration snippet. Supports {{variable}} substitution and GitOps URLs.'>
          <TextInput value={snippet?.content ?? ''} onChange={v => onChange({ ...(snippet ?? {}), content: v })} placeholder="https://example.com/snippet.conf" mono />
        </Field>
      )}
    </div>
  );
}

// ─── Headers Editor ───────────────────────────────────────────────────────────

export function HeadersEditor({ headers, onChange }: { headers: LocationHeaders | undefined; onChange: (h: LocationHeaders | undefined) => void }) {
  const enabled = headers != null;
  const h = headers ?? {};

  const addToServerSet = () => onChange({ ...h, to_server: { ...(h.to_server ?? {}), set: [...(h.to_server?.set ?? []), { name: '', value: '' }] } });
  const addToServerDel = () => onChange({ ...h, to_server: { ...(h.to_server ?? {}), delete: [...(h.to_server?.delete ?? []), ''] } });
  const addToClientAdd = () => onChange({ ...h, to_client: { ...(h.to_client ?? {}), add: [...(h.to_client?.add ?? []), { name: '', value: '' }] } });
  const addToClientDel = () => onChange({ ...h, to_client: { ...(h.to_client ?? {}), delete: [...(h.to_client?.delete ?? []), ''] } });
  const addToClientReplace = () => onChange({ ...h, to_client: { ...(h.to_client ?? {}), replace: [...(h.to_client?.replace ?? []), { name: '', value: '' }] } });

  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Headers</span>
        <Toggle
          checked={enabled}
          onChange={v => onChange(v ? {} : undefined)}
          label={enabled ? 'Configured' : 'Not configured'}
        />
      </div>
      {enabled && (
        <>
          {/* To Server */}
          <div className="cf-subsection">
            <div className="cf-subsection-header">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)' }}>To Server</span>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <AddBtn label="Set" onClick={addToServerSet} />
                <AddBtn label="Delete" onClick={addToServerDel} />
              </div>
            </div>
            {(h.to_server?.set ?? []).map((hdr, i) => (
              <div key={i} className="cf-origin-row" style={{ gridTemplateColumns: '1fr 1fr auto' }}>
                <Field label="Name"><TextInput value={hdr.name} onChange={v => onChange({ ...h, to_server: { ...(h.to_server ?? {}), set: (h.to_server?.set ?? []).map((x, j) => j === i ? { ...x, name: v } : x) } })} placeholder="X-Custom-Header" mono /></Field>
                <Field label="Value"><TextInput value={hdr.value} onChange={v => onChange({ ...h, to_server: { ...(h.to_server ?? {}), set: (h.to_server?.set ?? []).map((x, j) => j === i ? { ...x, value: v } : x) } })} placeholder="$remote_addr" mono /></Field>
                <div className="cf-origin-remove"><RemoveBtn onClick={() => onChange({ ...h, to_server: { ...(h.to_server ?? {}), set: (h.to_server?.set ?? []).filter((_, j) => j !== i) } })} /></div>
              </div>
            ))}
            {(h.to_server?.delete ?? []).map((name, i) => (
              <div key={i} className="cf-inline-row">
                <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)', flexShrink: 0 }}>Delete:</span>
                <TextInput value={name} onChange={v => onChange({ ...h, to_server: { ...(h.to_server ?? {}), delete: (h.to_server?.delete ?? []).map((x, j) => j === i ? v : x) } })} placeholder="Authorization" mono />
                <RemoveBtn onClick={() => onChange({ ...h, to_server: { ...(h.to_server ?? {}), delete: (h.to_server?.delete ?? []).filter((_, j) => j !== i) } })} />
              </div>
            ))}
          </div>
          {/* To Client */}
          <div className="cf-subsection">
            <div className="cf-subsection-header">
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)' }}>To Client</span>
              <div style={{ display: 'flex', gap: '0.35rem' }}>
                <AddBtn label="Add" onClick={addToClientAdd} />
                <AddBtn label="Delete" onClick={addToClientDel} />
                <AddBtn label="Replace" onClick={addToClientReplace} />
              </div>
            </div>
            {(h.to_client?.add ?? []).map((hdr, i) => (
              <div key={i} className="cf-origin-row" style={{ gridTemplateColumns: '1fr 1fr auto' }}>
                <Field label="Add Name"><TextInput value={hdr.name} onChange={v => onChange({ ...h, to_client: { ...(h.to_client ?? {}), add: (h.to_client?.add ?? []).map((x, j) => j === i ? { ...x, name: v } : x) } })} placeholder="X-Response-Header" mono /></Field>
                <Field label="Value"><TextInput value={hdr.value} onChange={v => onChange({ ...h, to_client: { ...(h.to_client ?? {}), add: (h.to_client?.add ?? []).map((x, j) => j === i ? { ...x, value: v } : x) } })} placeholder="my-value" mono /></Field>
                <div className="cf-origin-remove"><RemoveBtn onClick={() => onChange({ ...h, to_client: { ...(h.to_client ?? {}), add: (h.to_client?.add ?? []).filter((_, j) => j !== i) } })} /></div>
              </div>
            ))}
            {(h.to_client?.replace ?? []).map((hdr, i) => (
              <div key={i} className="cf-origin-row" style={{ gridTemplateColumns: '1fr 1fr auto' }}>
                <Field label="Replace Name"><TextInput value={hdr.name} onChange={v => onChange({ ...h, to_client: { ...(h.to_client ?? {}), replace: (h.to_client?.replace ?? []).map((x, j) => j === i ? { ...x, name: v } : x) } })} placeholder="Server" mono /></Field>
                <Field label="Value"><TextInput value={hdr.value} onChange={v => onChange({ ...h, to_client: { ...(h.to_client ?? {}), replace: (h.to_client?.replace ?? []).map((x, j) => j === i ? { ...x, value: v } : x) } })} placeholder="nginx" mono /></Field>
                <div className="cf-origin-remove"><RemoveBtn onClick={() => onChange({ ...h, to_client: { ...(h.to_client ?? {}), replace: (h.to_client?.replace ?? []).filter((_, j) => j !== i) } })} /></div>
              </div>
            ))}
            {(h.to_client?.delete ?? []).map((name, i) => (
              <div key={i} className="cf-inline-row">
                <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)', flexShrink: 0 }}>Delete:</span>
                <TextInput value={name} onChange={v => onChange({ ...h, to_client: { ...(h.to_client ?? {}), delete: (h.to_client?.delete ?? []).map((x, j) => j === i ? v : x) } })} placeholder="X-Powered-By" mono />
                <RemoveBtn onClick={() => onChange({ ...h, to_client: { ...(h.to_client ?? {}), delete: (h.to_client?.delete ?? []).filter((_, j) => j !== i) } })} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Location Auth/Authz/Cache/RL/HealthCheck editors ────────────────────────

export function LocationAuthEditor({ auth, authClientNames, authServerNames, onChange }: {
  auth: LocationAuth | undefined;
  authClientNames: string[];
  authServerNames: string[];
  onChange: (a: LocationAuth | undefined) => void;
}) {
  const enabled = auth != null;
  const a = auth ?? {};

  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Authentication</span>
        <Toggle checked={enabled} onChange={v => onChange(v ? { client: [], server: [] } : undefined)} label={enabled ? 'Configured' : 'Not configured'} />
      </div>
      {enabled && (
        <div className="cf-grid-2">
          <div>
            <div className="cf-subsection-header" style={{ marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)' }}>Client profiles</span>
              <AddBtn label="Add" onClick={() => onChange({ ...a, client: [...(a.client ?? []), { profile: '' }] })} />
            </div>
            {(a.client ?? []).length === 0
              ? <p className="cf-hint">No client auth profiles.</p>
              : (a.client ?? []).map((c, i) => (
                <div key={i} className="cf-inline-row">
                  <ProfileSelect value={c.profile ?? ''} onChange={v => onChange({ ...a, client: (a.client ?? []).map((x, j) => j === i ? { ...x, profile: v } : x) })} options={authClientNames} placeholder="jwt-auth" />
                  <RemoveBtn onClick={() => onChange({ ...a, client: (a.client ?? []).filter((_, j) => j !== i) })} />
                </div>
              ))
            }
          </div>
          <div>
            <div className="cf-subsection-header" style={{ marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)' }}>Server profiles</span>
              <AddBtn label="Add" onClick={() => onChange({ ...a, server: [...(a.server ?? []), { profile: '' }] })} />
            </div>
            {(a.server ?? []).length === 0
              ? <p className="cf-hint">No server auth profiles.</p>
              : (a.server ?? []).map((s, i) => (
                <div key={i} className="cf-inline-row">
                  <ProfileSelect value={s.profile ?? ''} onChange={v => onChange({ ...a, server: (a.server ?? []).map((x, j) => j === i ? { ...x, profile: v } : x) })} options={authServerNames} placeholder="token-auth" />
                  <RemoveBtn onClick={() => onChange({ ...a, server: (a.server ?? []).filter((_, j) => j !== i) })} />
                </div>
              ))
            }
          </div>
        </div>
      )}
    </div>
  );
}

export function LocationAuthzEditor({ authz, authzNames, onChange }: {
  authz: AuthzRef | undefined;
  authzNames: string[];
  onChange: (a: AuthzRef | undefined) => void;
}) {
  const enabled = authz != null;
  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Authorization</span>
        <Toggle checked={enabled} onChange={v => onChange(v ? { profile: '' } : undefined)} label={enabled ? 'Configured' : 'Not configured'} />
      </div>
      {enabled && (
        <Field label="Profile" hint="Name of the authorization profile from the HTTP profiles section.">
          <ProfileSelect value={authz?.profile ?? ''} onChange={v => onChange({ profile: v })} options={authzNames} placeholder="jwt-authz" />
        </Field>
      )}
    </div>
  );
}

export function LocationCacheEditor({ cache, cacheNames, onChange }: {
  cache: CacheItem | undefined;
  cacheNames: string[];
  onChange: (c: CacheItem | undefined) => void;
}) {
  const enabled = cache != null;
  const c = cache ?? {};
  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Cache</span>
        <Toggle checked={enabled} onChange={v => onChange(v ? { profile: '', key: '$scheme$proxy_host$request_uri', validity: [] } : undefined)} label={enabled ? 'Configured' : 'Not configured'} />
      </div>
      {enabled && (
        <div className="cf-grid-2">
          <Field label="Profile" hint="Cache zone profile from the HTTP profiles section.">
            <ProfileSelect value={c.profile ?? ''} onChange={v => onChange({ ...c, profile: v })} options={cacheNames} placeholder="my-cache" />
          </Field>
          <Field label="Cache key" hint='NGINX variable expression for the cache key.'>
            <TextInput value={c.key ?? '$scheme$proxy_host$request_uri'} onChange={v => onChange({ ...c, key: v })} placeholder="$scheme$proxy_host$request_uri" mono />
          </Field>
        </div>
      )}
    </div>
  );
}

export function LocationRateLimitEditor({ rl, rateLimitNames, onChange }: {
  rl: RateLimitRef | undefined;
  rateLimitNames: string[];
  onChange: (r: RateLimitRef | undefined) => void;
}) {
  const enabled = rl != null;
  const r = rl ?? {};
  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Rate Limiting</span>
        <Toggle checked={enabled} onChange={v => onChange(v ? { profile: '', httpcode: 429, burst: 0, delay: 0 } : undefined)} label={enabled ? 'Configured' : 'Not configured'} />
      </div>
      {enabled && (
        <div className="cf-grid-2">
          <Field label="Profile" hint="Rate limit zone profile from the HTTP profiles section.">
            <ProfileSelect value={r.profile ?? ''} onChange={v => onChange({ ...r, profile: v })} options={rateLimitNames} placeholder="my-rate-limit" />
          </Field>
          <Field label="HTTP code" hint="Status code returned when rate-limited.">
            <NumberInput value={r.httpcode ?? 429} onChange={v => onChange({ ...r, httpcode: v })} />
          </Field>
          <Field label="Burst" hint="Extra requests to queue before rejecting. 0 = no burst.">
            <NumberInput value={r.burst ?? 0} onChange={v => onChange({ ...r, burst: v })} />
          </Field>
          <Field label="Delay" hint="Requests to delay before the limit applies. 0 = nodelay.">
            <NumberInput value={r.delay ?? 0} onChange={v => onChange({ ...r, delay: v })} />
          </Field>
        </div>
      )}
    </div>
  );
}

export function HealthCheckEditor({ hc, onChange }: { hc: HealthCheck | undefined; onChange: (h: HealthCheck | undefined) => void }) {
  const enabled = hc != null;
  const h = hc ?? {};
  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Health Check (NGINX Plus)</span>
        <Toggle checked={enabled} onChange={v => onChange(v ? { enabled: true, uri: '/', interval: 5, fails: 1, passes: 1 } : undefined)} label={enabled ? 'Configured' : 'Not configured'} />
      </div>
      {enabled && (
        <div className="cf-grid-2">
          <Field label="URI" hint="URI path used for health check probes.">
            <TextInput value={h.uri ?? '/'} onChange={v => onChange({ ...h, uri: v })} placeholder="/" mono />
          </Field>
          <Field label="Enabled">
            <Toggle checked={h.enabled ?? true} onChange={v => onChange({ ...h, enabled: v })} label={h.enabled ?? true ? 'Yes' : 'No'} />
          </Field>
          <Field label="Interval (s)" hint="Seconds between health check probes.">
            <NumberInput value={h.interval ?? 5} onChange={v => onChange({ ...h, interval: v })} min={1} />
          </Field>
          <Field label="Fails" hint="Consecutive failures to mark unhealthy.">
            <NumberInput value={h.fails ?? 1} onChange={v => onChange({ ...h, fails: v })} min={1} />
          </Field>
          <Field label="Passes" hint="Consecutive passes to mark healthy again.">
            <NumberInput value={h.passes ?? 1} onChange={v => onChange({ ...h, passes: v })} min={1} />
          </Field>
        </div>
      )}
    </div>
  );
}

// ─── NJS hooks editors ────────────────────────────────────────────────────────

export function NjsHooksServerEditor({ hooks, onChange, njsProfileNames }: {
  hooks: NjsHookServer[];
  onChange: (h: NjsHookServer[]) => void;
  njsProfileNames: string[];
}) {
  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">NJS Hooks</span>
        <AddBtn label="Add hook" onClick={() => onChange([...hooks, emptyNjsHookServer()])} />
      </div>
      {hooks.length === 0 ? <p className="cf-hint">No NJS hooks configured.</p> : hooks.map((hook, i) => (
        <div key={i} className="cf-agw-item-row">
          <Field label="Hook type">
            <SelectInput value={hook.hook.type} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, type: v } } : x))} options={NJS_SERVER_HOOK_TYPES} />
          </Field>
          <Field label="NJS profile" hint="Name of the NJS profile (njs_profiles section).">
            <ProfileSelect value={hook.profile} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, profile: v } : x))} options={njsProfileNames} placeholder="myProfile" />
          </Field>
          <Field label="Function" hint="NJS function name to invoke.">
            <TextInput value={hook.function} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, function: v } : x))} placeholder="myFunction" mono />
          </Field>
          {hook.hook.type === 'js_set' && (
            <Field label="Variable">
              <TextInput value={hook.hook.js_set?.variable ?? ''} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, js_set: { variable: v } } } : x))} placeholder="$myVar" mono />
            </Field>
          )}
          {hook.hook.type === 'js_preload_object' && (
            <Field label="File">
              <TextInput value={hook.hook.js_preload_object?.file ?? ''} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, js_preload_object: { file: v } } } : x))} placeholder="/etc/nginx/mydata.json" mono />
            </Field>
          )}
          <div className="cf-agw-item-remove"><RemoveBtn onClick={() => onChange(hooks.filter((_, j) => j !== i))} /></div>
        </div>
      ))}
    </div>
  );
}

export function NjsHooksLocationEditor({ hooks, onChange, njsProfileNames }: {
  hooks: NjsHookLocation[];
  onChange: (h: NjsHookLocation[]) => void;
  njsProfileNames: string[];
}) {
  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">NJS Hooks</span>
        <AddBtn label="Add hook" onClick={() => onChange([...hooks, emptyNjsHookLocation()])} />
      </div>
      {hooks.length === 0 ? <p className="cf-hint">No NJS hooks configured.</p> : hooks.map((hook, i) => (
        <div key={i} className="cf-agw-item-row">
          <Field label="Hook type">
            <SelectInput value={hook.hook.type} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, type: v } } : x))} options={NJS_LOCATION_HOOK_TYPES} />
          </Field>
          <Field label="NJS profile">
            <ProfileSelect value={hook.profile} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, profile: v } : x))} options={njsProfileNames} placeholder="myProfile" />
          </Field>
          <Field label="Function">
            <TextInput value={hook.function} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, function: v } : x))} placeholder="myFunction" mono />
          </Field>
          {hook.hook.type === 'js_set' && (
            <Field label="Variable">
              <TextInput value={hook.hook.js_set?.variable ?? ''} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, js_set: { variable: v } } } : x))} placeholder="$myVar" mono />
            </Field>
          )}
          {hook.hook.type === 'js_preload_object' && (
            <Field label="File">
              <TextInput value={hook.hook.js_preload_object?.file ?? ''} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, js_preload_object: { file: v } } } : x))} placeholder="/etc/nginx/mydata.json" mono />
            </Field>
          )}
          {hook.hook.type === 'js_body_filter' && (
            <Field label="Buffer type" hint='e.g. "string" or "buffer"'>
              <TextInput value={hook.hook.js_body_filter?.buffer_type ?? ''} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, js_body_filter: { buffer_type: v } } } : x))} placeholder="string" mono />
            </Field>
          )}
          {hook.hook.type === 'js_periodic' && (
            <>
              <Field label="Interval"><TextInput value={hook.hook.js_periodic?.interval ?? ''} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, js_periodic: { ...(x.hook.js_periodic ?? {}), interval: v } } } : x))} placeholder="1h" mono /></Field>
              <Field label="Jitter (ms)"><NumberInput value={hook.hook.js_periodic?.jitter ?? 0} onChange={v => onChange(hooks.map((x, j) => j === i ? { ...x, hook: { ...x.hook, js_periodic: { ...(x.hook.js_periodic ?? {}), jitter: v } } } : x))} /></Field>
            </>
          )}
          <div className="cf-agw-item-remove"><RemoveBtn onClick={() => onChange(hooks.filter((_, j) => j !== i))} /></div>
        </div>
      ))}
    </div>
  );
}
