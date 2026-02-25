import { useState, useEffect, useCallback } from 'react';
import './ConfigForm.css';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Origin {
  server: string;
  weight?: number;
  max_fails?: number;
  fail_timeout?: string;
  backup?: boolean;
}

interface Location {
  uri: string;
  urimatch?: string;
  upstream?: string;
}

interface TlsConfig {
  certificate?: string;
  key?: string;
  protocols?: string[];
}

interface Server {
  name: string;
  names?: string[];
  listen?: { address?: string; http2?: boolean; tls?: TlsConfig };
  locations?: Location[];
}

interface Upstream {
  name: string;
  origin: Origin[];
  resolver?: string;
}

interface OutputNMS {
  url: string;
  username: string;
  password: string;
  instancegroup: string;
  synctime?: number;
  modules?: string[];
}

interface OutputNGINXOne {
  url: string;
  namespace: string;
  token: string;
  configsyncgroup: string;
  synctime?: number;
  modules?: string[];
}

interface ConfigData {
  output: {
    type: 'nms' | 'nginxone';
    nms?: OutputNMS;
    nginxone?: OutputNGINXOne;
  };
  declaration: {
    http?: { servers?: Server[]; upstreams?: Upstream[] };
    layer4?: {
      servers?: Array<{ name: string; listen?: { address?: string }; upstream?: string }>;
      upstreams?: Array<{ name: string; origin?: Array<{ server: string }> }>;
    };
  };
}

// ─── Defaults ─────────────────────────────────────────────────────────────────

const emptyNms = (): OutputNMS => ({
  url: '', username: '', password: '', instancegroup: '', synctime: 0, modules: [],
});
const emptyNginxOne = (): OutputNGINXOne => ({
  url: '', namespace: '', token: '', configsyncgroup: '', synctime: 0, modules: [],
});
const emptyServer = (): Server => ({
  name: '', names: [], listen: { address: '', http2: false }, locations: [],
});
const emptyLocation = (): Location => ({ uri: '/', urimatch: 'prefix', upstream: '' });
const emptyUpstream = (): Upstream => ({ name: '', origin: [{ server: '', weight: 1 }] });
const emptyOrigin = (): Origin => ({ server: '', weight: 1, max_fails: 1, fail_timeout: '10s' });

function parseConfig(json: string): ConfigData | null {
  try {
    const p = JSON.parse(json);
    return {
      output: {
        type: p?.output?.type ?? 'nms',
        nms: { ...emptyNms(), ...(p?.output?.nms ?? {}) },
        nginxone: { ...emptyNginxOne(), ...(p?.output?.nginxone ?? {}) },
      },
      declaration: {
        http: {
          servers: p?.declaration?.http?.servers ?? [],
          upstreams: p?.declaration?.http?.upstreams ?? [],
        },
        layer4: {
          servers: p?.declaration?.layer4?.servers ?? [],
          upstreams: p?.declaration?.layer4?.upstreams ?? [],
        },
      },
    };
  } catch {
    return null;
  }
}

function toJson(cfg: ConfigData): string {
  const out: Record<string, unknown> = { type: cfg.output.type };
  if (cfg.output.type === 'nms') out.nms = cfg.output.nms;
  else out.nginxone = cfg.output.nginxone;

  const decl: Record<string, unknown> = {};
  const http = cfg.declaration.http;
  if ((http?.servers?.length ?? 0) + (http?.upstreams?.length ?? 0) > 0) {
    decl.http = {
      ...(http?.servers?.length ? { servers: http.servers } : {}),
      ...(http?.upstreams?.length ? { upstreams: http.upstreams } : {}),
    };
  }
  const l4 = cfg.declaration.layer4;
  if ((l4?.servers?.length ?? 0) + (l4?.upstreams?.length ?? 0) > 0) {
    decl.layer4 = {
      ...(l4?.servers?.length ? { servers: l4.servers } : {}),
      ...(l4?.upstreams?.length ? { upstreams: l4.upstreams } : {}),
    };
  }

  return JSON.stringify({ output: out, declaration: decl }, null, 2);
}

// ─── Primitive field components ───────────────────────────────────────────────

function Field({
  label, required, hint, children, span,
}: {
  label: string; required?: boolean; hint?: string; children: React.ReactNode; span?: 'full';
}) {
  return (
    <div className={`cf-field${span === 'full' ? ' cf-field-full' : ''}`}>
      <label className="cf-label">
        {label}{required && <span className="cf-required">*</span>}
      </label>
      {children}
      {hint && <p className="cf-hint">{hint}</p>}
    </div>
  );
}

function TextInput({
  value, onChange, placeholder, type = 'text', mono,
}: {
  value: string; onChange: (v: string) => void; placeholder?: string; type?: string; mono?: boolean;
}) {
  return (
    <input
      className={`cf-input${mono ? ' cf-mono' : ''}`}
      type={type}
      value={value}
      placeholder={placeholder}
      autoComplete="off"
      spellCheck={false}
      onChange={e => onChange(e.target.value)}
    />
  );
}

function NumberInput({ value, onChange, min = 0 }: { value: number; onChange: (v: number) => void; min?: number }) {
  return (
    <input
      className="cf-input cf-input-sm"
      type="number"
      value={value}
      min={min}
      onChange={e => onChange(Number(e.target.value))}
    />
  );
}

function SelectInput({ value, onChange, options }: {
  value: string; onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select className="cf-input" value={value} onChange={e => onChange(e.target.value)}>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="cf-toggle">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
      <span className="cf-toggle-text">{label}</span>
    </label>
  );
}

const MODULES = [
  { value: 'ngx_http_app_protect_module', label: 'NGINX App Protect WAF' },
  { value: 'ngx_http_js_module',          label: 'NGINX JavaScript (njs) — HTTP' },
  { value: 'ngx_stream_js_module',        label: 'NGINX JavaScript (njs) — Stream' },
  { value: 'ngx_http_geoip2_module',      label: 'GeoIP2' },
];

function ModulesField({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  const toggle = (mod: string) =>
    onChange(value.includes(mod) ? value.filter(m => m !== mod) : [...value, mod]);
  return (
    <div className="cf-modules">
      {MODULES.map(m => (
        <label key={m.value} className="cf-toggle">
          <input type="checkbox" checked={value.includes(m.value)} onChange={() => toggle(m.value)} />
          <span className="cf-toggle-text">{m.label}</span>
        </label>
      ))}
    </div>
  );
}

// ─── Section chrome ───────────────────────────────────────────────────────────

function SectionTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="cf-section-head">
      <div className="cf-section-text">
        <span className="cf-section-title">{title}</span>
        {sub && <span className="cf-section-sub">{sub}</span>}
      </div>
    </div>
  );
}

function AddBtn({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" className="cf-btn-add" onClick={onClick}>
      <span className="cf-btn-add-icon">+</span> {label}
    </button>
  );
}

function RemoveBtn({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className="cf-btn-remove" title="Remove" onClick={onClick}>
      ✕
    </button>
  );
}

// ─── Collapsible card ─────────────────────────────────────────────────────────

function CollapseCard({
  title, meta, children, defaultOpen,
}: {
  title: React.ReactNode; meta?: string; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  return (
    <div className={`cf-card${open ? ' cf-card-open' : ''}`}>
      <div className="cf-card-header" onClick={() => setOpen(o => !o)}>
        <span className="cf-card-caret">{open ? '▾' : '▸'}</span>
        <span className="cf-card-title">{title}</span>
        {meta && <span className="cf-card-meta">{meta}</span>}
      </div>
      {open && <div className="cf-card-body">{children}</div>}
    </div>
  );
}

// ─── Locations sub-editor ─────────────────────────────────────────────────────

const URI_MATCH_OPTIONS = [
  { value: 'prefix',  label: 'Prefix — matches any path starting with URI' },
  { value: 'exact',   label: 'Exact — matches only this exact URI' },
  { value: 'regex',   label: 'Regex — case-sensitive regular expression' },
  { value: 'iregex',  label: 'iRegex — case-insensitive regular expression' },
  { value: 'best',    label: 'Best — longest prefix + regex priority' },
];

function LocationsEditor({ locations, onChange }: { locations: Location[]; onChange: (l: Location[]) => void }) {
  const update = (i: number, l: Location) => onChange(locations.map((x, idx) => idx === i ? l : x));
  const remove = (i: number) => onChange(locations.filter((_, idx) => idx !== i));

  return (
    <div className="cf-subsection">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Locations</span>
        <AddBtn label="Add location" onClick={() => onChange([...locations, emptyLocation()])} />
      </div>
      {locations.length === 0 && (
        <p className="cf-empty">No locations — add one to route traffic to an upstream.</p>
      )}
      {locations.map((loc, i) => (
        <div key={i} className="cf-row-card">
          <div className="cf-row-num">#{i + 1}</div>
          <div className="cf-row-fields">
            <Field label="URI" required hint="Request path this location handles. Interpreted according to the match type.">
              <TextInput value={loc.uri} onChange={v => update(i, { ...loc, uri: v })} placeholder="/" mono />
            </Field>
            <Field label="Match type" hint="How NGINX matches the incoming request URI against this location.">
              <SelectInput
                value={loc.urimatch ?? 'prefix'}
                onChange={v => update(i, { ...loc, urimatch: v })}
                options={URI_MATCH_OPTIONS}
              />
            </Field>
            <Field label="Upstream" hint='Full upstream reference including scheme, e.g. "http://my-upstream". Leave empty to use directives from a snippet.'>
              <TextInput value={loc.upstream ?? ''} onChange={v => update(i, { ...loc, upstream: v })} placeholder="http://my-upstream" mono />
            </Field>
          </div>
          <RemoveBtn onClick={() => remove(i)} />
        </div>
      ))}
    </div>
  );
}

// ─── TLS sub-editor ───────────────────────────────────────────────────────────

function TlsEditor({ tls, onChange }: {
  tls: TlsConfig | undefined;
  onChange: (t: TlsConfig | undefined) => void;
}) {
  const enabled = !!tls?.certificate || !!tls?.key;
  const [show, setShow] = useState(enabled);
  const t = tls ?? {};

  const handleEnable = (v: boolean) => {
    setShow(v);
    if (!v) onChange(undefined);
    else onChange({ certificate: '', key: '', protocols: ['TLSv1.2', 'TLSv1.3'] });
  };

  const TLS_PROTOCOL_OPTIONS = ['TLSv1.2', 'TLSv1.3', 'TLSv1.1'];
  const toggleProto = (p: string) => {
    const protos = t.protocols ?? [];
    onChange({ ...t, protocols: protos.includes(p) ? protos.filter(x => x !== p) : [...protos, p] });
  };

  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">TLS / SSL</span>
        <Toggle checked={show} onChange={handleEnable} label={show ? 'Enabled' : 'Disabled'} />
      </div>
      {show && (
        <div className="cf-grid-3">
          <Field label="Certificate" required hint="Name of the certificate object managed by NMS or NGINX One (not a file path).">
            <TextInput value={t.certificate ?? ''} onChange={v => onChange({ ...t, certificate: v })} placeholder="my-tls-cert" />
          </Field>
          <Field label="Private key" required hint="Name of the private key object matching the certificate above.">
            <TextInput value={t.key ?? ''} onChange={v => onChange({ ...t, key: v })} placeholder="my-tls-key" />
          </Field>
          <Field label="Protocols" hint="TLS protocol versions to accept. TLSv1.3 + TLSv1.2 is the recommended baseline.">
            <div className="cf-modules">
              {TLS_PROTOCOL_OPTIONS.map(p => (
                <label key={p} className="cf-toggle">
                  <input type="checkbox" checked={(t.protocols ?? []).includes(p)} onChange={() => toggleProto(p)} />
                  <span className="cf-toggle-text">{p}</span>
                </label>
              ))}
            </div>
          </Field>
        </div>
      )}
    </div>
  );
}

// ─── HTTP Servers ─────────────────────────────────────────────────────────────

function ServersSection({ servers, onChange }: { servers: Server[]; onChange: (s: Server[]) => void }) {
  const update = (i: number, s: Server) => onChange(servers.map((x, idx) => idx === i ? s : x));
  const remove = (i: number) => onChange(servers.filter((_, idx) => idx !== i));

  return (
    <div className="cf-group">
      <div className="cf-group-header">
        <span className="cf-group-title">Servers</span>
        <AddBtn label="Add server" onClick={() => onChange([...servers, emptyServer()])} />
      </div>

      {servers.length === 0 && (
        <p className="cf-empty">No HTTP servers defined. Add a server to start routing traffic.</p>
      )}

      {servers.map((srv, i) => (
        <CollapseCard
          key={i}
          title={srv.name || <em>server #{i + 1}</em>}
          meta={srv.listen?.address || '—'}
          defaultOpen={i === 0 && servers.length === 1}
        >
          <div className="cf-card-actions">
            <RemoveBtn onClick={() => remove(i)} />
          </div>

          <div className="cf-grid-2">
            <Field label="Server name" required
              hint='Unique identifier for this server. Alphanumeric, hyphens, underscores. Referenced as the "name" key in the declaration.'>
              <TextInput value={srv.name} onChange={v => update(i, { ...srv, name: v })} placeholder="my-server" />
            </Field>
            <Field label="Listen address"
              hint='IP address and port to bind to. Use 0.0.0.0 to listen on all interfaces. Examples: "0.0.0.0:80", "0.0.0.0:443", "[::]:8080".'>
              <TextInput
                value={srv.listen?.address ?? ''}
                onChange={v => update(i, { ...srv, listen: { ...(srv.listen ?? {}), address: v } })}
                placeholder="0.0.0.0:80"
                mono
              />
            </Field>
            <Field label="Server names" span="full"
              hint='Space-separated list of hostnames this server responds to (HTTP Host header matching). Example: "example.com www.example.com".'>
              <TextInput
                value={(srv.names ?? []).join(' ')}
                onChange={v => update(i, { ...srv, names: v.split(/\s+/).filter(Boolean) })}
                placeholder="example.com www.example.com"
                mono
              />
            </Field>
          </div>

          <div className="cf-field cf-field-inline">
            <Toggle
              checked={srv.listen?.http2 ?? false}
              onChange={v => update(i, { ...srv, listen: { ...(srv.listen ?? {}), http2: v } })}
              label="Enable HTTP/2"
            />
            <p className="cf-hint">Enables HTTP/2 protocol support on this listener via the http2 directive.</p>
          </div>

          <TlsEditor
            tls={srv.listen?.tls}
            onChange={t => update(i, { ...srv, listen: { ...(srv.listen ?? {}), tls: t } })}
          />

          <LocationsEditor
            locations={srv.locations ?? []}
            onChange={locs => update(i, { ...srv, locations: locs })}
          />
        </CollapseCard>
      ))}
    </div>
  );
}

// ─── HTTP Upstreams ───────────────────────────────────────────────────────────

function UpstreamsSection({ upstreams, onChange }: { upstreams: Upstream[]; onChange: (u: Upstream[]) => void }) {
  const update = (i: number, u: Upstream) => onChange(upstreams.map((x, idx) => idx === i ? u : x));
  const remove = (i: number) => onChange(upstreams.filter((_, idx) => idx !== i));
  const updOrigin = (i: number, oi: number, o: Origin) =>
    update(i, { ...upstreams[i], origin: (upstreams[i].origin ?? []).map((x, oIdx) => oIdx === oi ? o : x) });
  const remOrigin = (i: number, oi: number) =>
    update(i, { ...upstreams[i], origin: (upstreams[i].origin ?? []).filter((_, oIdx) => oIdx !== oi) });
  const addOrigin = (i: number) =>
    update(i, { ...upstreams[i], origin: [...(upstreams[i].origin ?? []), emptyOrigin()] });

  return (
    <div className="cf-group">
      <div className="cf-group-header">
        <span className="cf-group-title">Upstreams</span>
        <AddBtn label="Add upstream" onClick={() => onChange([...upstreams, emptyUpstream()])} />
      </div>

      {upstreams.length === 0 && (
        <p className="cf-empty">No upstreams defined. Add an upstream to reference from your server locations.</p>
      )}

      {upstreams.map((up, i) => (
        <CollapseCard
          key={i}
          title={up.name || <em>upstream #{i + 1}</em>}
          meta={`${up.origin?.length ?? 0} origin${(up.origin?.length ?? 0) !== 1 ? 's' : ''}`}
          defaultOpen={i === 0 && upstreams.length === 1}
        >
          <div className="cf-card-actions"><RemoveBtn onClick={() => remove(i)} /></div>

          <div className="cf-grid-2">
            <Field label="Upstream name" required
              hint='Identifier for this upstream group. Reference it from a location as "http://&lt;name&gt;". Alphanumeric, hyphens, underscores.'>
              <TextInput value={up.name} onChange={v => update(i, { ...up, name: v })} placeholder="backend" />
            </Field>
            <Field label="Resolver"
              hint="Optional DNS resolver name (from the resolvers section) for dynamic upstream addresses. Leave empty for static IPs.">
              <TextInput value={up.resolver ?? ''} onChange={v => update(i, { ...up, resolver: v })} placeholder="my-resolver" />
            </Field>
          </div>

          <div className="cf-subsection">
            <div className="cf-subsection-header">
              <span className="cf-subsection-title">Origins</span>
              <AddBtn label="Add origin" onClick={() => addOrigin(i)} />
            </div>
            <p className="cf-hint cf-hint-top">Each origin is a backend server. NGINX will load-balance requests across all non-backup origins.</p>
            {(up.origin ?? []).map((o, oi) => (
              <div key={oi} className="cf-origin-row">
                <Field label="Server address" hint='Format: "host:port" or IP. Example: "10.0.0.1:8080" or "backend.internal:443".'>
                  <TextInput value={o.server} onChange={v => updOrigin(i, oi, { ...o, server: v })} placeholder="10.0.0.1:8080" mono />
                </Field>
                <Field label="Weight" hint="Relative weight for weighted round-robin. Higher = more requests. Default: 1.">
                  <NumberInput value={o.weight ?? 1} onChange={v => updOrigin(i, oi, { ...o, weight: v })} min={1} />
                </Field>
                <Field label="Max fails" hint="Failures before marking server as unavailable. 0 disables fail tracking.">
                  <NumberInput value={o.max_fails ?? 1} onChange={v => updOrigin(i, oi, { ...o, max_fails: v })} min={0} />
                </Field>
                <Field label="Fail timeout" hint='Time window for max_fails counting, and recovery time. Example: "10s", "30s".'>
                  <TextInput value={o.fail_timeout ?? '10s'} onChange={v => updOrigin(i, oi, { ...o, fail_timeout: v })} placeholder="10s" mono />
                </Field>
                <Field label="Backup">
                  <Toggle checked={o.backup ?? false} onChange={v => updOrigin(i, oi, { ...o, backup: v })} label="Backup only" />
                </Field>
                <div className="cf-origin-remove"><RemoveBtn onClick={() => remOrigin(i, oi)} /></div>
              </div>
            ))}
          </div>
        </CollapseCard>
      ))}
    </div>
  );
}

// ─── HTTP wrapper ────────────────────────────────────────────────────────────

function HttpSection({ servers, onServersChange, upstreams, onUpstreamsChange }: {
  servers: Server[];
  onServersChange: (s: Server[]) => void;
  upstreams: Upstream[];
  onUpstreamsChange: (u: Upstream[]) => void;
}) {
  return (
    <section className="cf-section">
      <SectionTitle title="HTTP" sub="Virtual servers and upstream groups for HTTP/S traffic" />
      <ServersSection servers={servers} onChange={onServersChange} />
      <UpstreamsSection upstreams={upstreams} onChange={onUpstreamsChange} />
    </section>
  );
}

// ─── Output Section ───────────────────────────────────────────────────────────

function OutputSection({ output, onChange }: {
  output: ConfigData['output'];
  onChange: (o: ConfigData['output']) => void;
}) {
  const nms = output.nms ?? emptyNms();
  const no = output.nginxone ?? emptyNginxOne();

  return (
    <section className="cf-section">
      <SectionTitle title="Output" sub="Where to push the generated NGINX configuration" />

      <div className="cf-type-row">
        <button
          type="button"
          className={`cf-type-card${output.type === 'nms' ? ' active' : ''}`}
          onClick={() => onChange({ ...output, type: 'nms' })}
        >
          <span className="cf-type-card-title">NGINX Instance Manager</span>
          <span className="cf-type-card-sub">Push to an NMS instance group</span>
        </button>
        <button
          type="button"
          className={`cf-type-card${output.type === 'nginxone' ? ' active' : ''}`}
          onClick={() => onChange({ ...output, type: 'nginxone' })}
        >
          <span className="cf-type-card-title">NGINX One Console</span>
          <span className="cf-type-card-sub">Push to a config sync group</span>
        </button>
      </div>

      {output.type === 'nms' && (
        <div className="cf-grid-2">
          <Field label="NMS URL" required
            hint="Base URL of your NGINX Instance Manager instance. Include scheme and port. Example: https://nms.example.com:443">
            <TextInput value={nms.url} onChange={v => onChange({ ...output, nms: { ...nms, url: v } })} placeholder="https://nms.example.com" mono />
          </Field>
          <Field label="Username" required hint="API username for the NGINX Instance Manager. Usually 'admin' for initial setup.">
            <TextInput value={nms.username} onChange={v => onChange({ ...output, nms: { ...nms, username: v } })} placeholder="admin" />
          </Field>
          <Field label="Password" required hint="Password for the NMS API user. Stored only in your local session — never sent to this UI's server.">
            <TextInput value={nms.password} onChange={v => onChange({ ...output, nms: { ...nms, password: v } })} type="password" placeholder="••••••••" />
          </Field>
          <Field label="Instance group" required hint="Name of the NMS instance group to push configuration to. The group must already exist in NMS.">
            <TextInput value={nms.instancegroup} onChange={v => onChange({ ...output, nms: { ...nms, instancegroup: v } })} placeholder="production" />
          </Field>
          <Field label="Sync time (seconds)"
            hint="How often (in seconds) the API will re-push the configuration. Set to 0 to push once and stop. Use a positive integer for continuous synchronisation.">
            <NumberInput value={nms.synctime ?? 0} onChange={v => onChange({ ...output, nms: { ...nms, synctime: v } })} />
          </Field>
          <Field label="Dynamic modules"
            hint="Select any additional NGINX dynamic modules that must be loaded. These are inserted as load_module directives at the top of nginx.conf.">
            <ModulesField value={nms.modules ?? []} onChange={v => onChange({ ...output, nms: { ...nms, modules: v } })} />
          </Field>
        </div>
      )}

      {output.type === 'nginxone' && (
        <div className="cf-grid-2">
          <Field label="NGINX One URL" required
            hint="Base URL of your NGINX One Console instance. Example: https://nginx-one.example.com">
            <TextInput value={no.url} onChange={v => onChange({ ...output, nginxone: { ...no, url: v } })} placeholder="https://nginx-one.example.com" mono />
          </Field>
          <Field label="Namespace" required hint="The NGINX One namespace that contains your config sync group. Case-sensitive.">
            <TextInput value={no.namespace} onChange={v => onChange({ ...output, nginxone: { ...no, namespace: v } })} placeholder="default" />
          </Field>
          <Field label="API token" required hint="Bearer token for authenticating to the NGINX One API. Generate this in the NGINX One Console under API keys.">
            <TextInput value={no.token} onChange={v => onChange({ ...output, nginxone: { ...no, token: v } })} type="password" placeholder="••••••••" />
          </Field>
          <Field label="Config sync group" required hint="Name of the config sync group to target. Instances in this group will receive the generated configuration.">
            <TextInput value={no.configsyncgroup} onChange={v => onChange({ ...output, nginxone: { ...no, configsyncgroup: v } })} placeholder="production-group" />
          </Field>
          <Field label="Sync time (seconds)"
            hint="How often (in seconds) to re-push the configuration. Set to 0 to push once and stop.">
            <NumberInput value={no.synctime ?? 0} onChange={v => onChange({ ...output, nginxone: { ...no, synctime: v } })} />
          </Field>
          <Field label="Dynamic modules"
            hint="Select any additional NGINX dynamic modules required by this configuration.">
            <ModulesField value={no.modules ?? []} onChange={v => onChange({ ...output, nginxone: { ...no, modules: v } })} />
          </Field>
        </div>
      )}
    </section>
  );
}

// ─── Layer 4 Section ──────────────────────────────────────────────────────────

function L4ServersSection({ servers, onChange }: {
  servers: NonNullable<ConfigData['declaration']['layer4']>['servers'];
  onChange: (s: NonNullable<ConfigData['declaration']['layer4']>['servers']) => void;
}) {
  const items = servers ?? [];
  const update = (i: number, s: typeof items[0]) => onChange(items.map((x, idx) => idx === i ? s : x));
  const remove = (i: number) => onChange(items.filter((_, idx) => idx !== i));

  return (
    <div className="cf-group">
      <div className="cf-group-header">
        <span className="cf-group-title">Servers</span>
        <AddBtn label="Add server" onClick={() => onChange([...items, { name: '', listen: { address: '' }, upstream: '' }])} />
      </div>
      {items.length === 0 && (
        <p className="cf-empty">No L4 servers defined. Add one to proxy TCP/UDP connections.</p>
      )}
      {items.map((sv, i) => (
        <CollapseCard key={i} title={sv.name || <em>server #{i + 1}</em>} meta={sv.listen?.address || '—'}>
          <div className="cf-card-actions"><RemoveBtn onClick={() => remove(i)} /></div>
          <Field label="Name" required hint="Alphanumeric identifier for this stream server.">
            <TextInput value={sv.name} onChange={v => update(i, { ...sv, name: v })} placeholder="l4-server" />
          </Field>
          <Field label="Listen address" hint='TCP/UDP address and port to bind to. Example: "0.0.0.0:5432".'>
            <TextInput value={sv.listen?.address ?? ''} onChange={v => update(i, { ...sv, listen: { address: v } })} placeholder="0.0.0.0:5432" mono />
          </Field>
          <Field label="Upstream" hint="Name of the L4 upstream group that connections will be proxied to.">
            <TextInput value={sv.upstream ?? ''} onChange={v => update(i, { ...sv, upstream: v })} placeholder="l4-backend" />
          </Field>
        </CollapseCard>
      ))}
    </div>
  );
}

function L4UpstreamsSection({ upstreams, onChange }: {
  upstreams: NonNullable<ConfigData['declaration']['layer4']>['upstreams'];
  onChange: (u: NonNullable<ConfigData['declaration']['layer4']>['upstreams']) => void;
}) {
  const items = upstreams ?? [];
  const update = (i: number, u: typeof items[0]) => onChange(items.map((x, idx) => idx === i ? u : x));
  const remove = (i: number) => onChange(items.filter((_, idx) => idx !== i));

  return (
    <div className="cf-group">
      <div className="cf-group-header">
        <span className="cf-group-title">Upstreams</span>
        <AddBtn label="Add upstream" onClick={() => onChange([...items, { name: '', origin: [{ server: '' }] }])} />
      </div>
      {items.length === 0 && (
        <p className="cf-empty">No L4 upstreams defined. Add one to reference from an L4 server.</p>
      )}
      {items.map((up, i) => (
        <CollapseCard key={i} title={up.name || <em>upstream #{i + 1}</em>} meta={`${up.origin?.length ?? 0} origin${(up.origin?.length ?? 0) !== 1 ? 's' : ''}`}>
          <div className="cf-card-actions"><RemoveBtn onClick={() => remove(i)} /></div>
          <Field label="Name" required hint="Alphanumeric identifier for this stream upstream group.">
            <TextInput value={up.name} onChange={v => update(i, { ...up, name: v })} placeholder="l4-backend" />
          </Field>
          <div className="cf-subsection">
            <div className="cf-subsection-header">
              <span className="cf-subsection-title">Origins</span>
              <AddBtn label="Add origin" onClick={() => update(i, { ...up, origin: [...(up.origin ?? []), { server: '' }] })} />
            </div>
            <p className="cf-hint cf-hint-top">Backend server addresses for this upstream group.</p>
            {(up.origin ?? []).map((o, oi) => (
              <div key={oi} className="cf-inline-row">
                <TextInput
                  value={o.server}
                  onChange={v => update(i, { ...up, origin: (up.origin ?? []).map((x, xIdx) => xIdx === oi ? { ...x, server: v } : x) })}
                  placeholder="10.0.0.1:5432"
                  mono
                />
                <RemoveBtn onClick={() => update(i, { ...up, origin: (up.origin ?? []).filter((_, xIdx) => xIdx !== oi) })} />
              </div>
            ))}
          </div>
        </CollapseCard>
      ))}
    </div>
  );
}

// ─── Layer 4 wrapper ──────────────────────────────────────────────────────────

function Layer4Section({ servers, onServersChange, upstreams, onUpstreamsChange }: {
  servers: NonNullable<ConfigData['declaration']['layer4']>['servers'];
  onServersChange: (s: NonNullable<ConfigData['declaration']['layer4']>['servers']) => void;
  upstreams: NonNullable<ConfigData['declaration']['layer4']>['upstreams'];
  onUpstreamsChange: (u: NonNullable<ConfigData['declaration']['layer4']>['upstreams']) => void;
}) {
  return (
    <section className="cf-section">
      <SectionTitle title="Layer 4 (TCP/UDP)" sub="Stream proxy servers and upstream groups — optional" />
      <L4ServersSection servers={servers} onChange={onServersChange} />
      <L4UpstreamsSection upstreams={upstreams} onChange={onUpstreamsChange} />
    </section>
  );
}

// ─── Root component ───────────────────────────────────────────────────────────

interface ConfigFormProps {
  initialJson: string;
  onChange: (json: string) => void;
}

const DEFAULT_CFG: ConfigData = {
  output: { type: 'nms', nms: emptyNms(), nginxone: emptyNginxOne() },
  declaration: { http: { servers: [], upstreams: [] }, layer4: { servers: [], upstreams: [] } },
};

export function ConfigForm({ initialJson, onChange }: ConfigFormProps) {
  const [cfg, setCfg] = useState<ConfigData>(() => parseConfig(initialJson) ?? DEFAULT_CFG);

  useEffect(() => {
    const parsed = parseConfig(initialJson);
    if (parsed) setCfg(parsed);
  }, [initialJson]);

  const update = useCallback((next: ConfigData) => {
    setCfg(next);
    onChange(toJson(next));
  }, [onChange]);

  return (
    <div className="config-form">
      <OutputSection output={cfg.output} onChange={o => update({ ...cfg, output: o })} />
      <HttpSection
        servers={cfg.declaration.http?.servers ?? []}
        onServersChange={s => update({ ...cfg, declaration: { ...cfg.declaration, http: { ...cfg.declaration.http, servers: s } } })}
        upstreams={cfg.declaration.http?.upstreams ?? []}
        onUpstreamsChange={u => update({ ...cfg, declaration: { ...cfg.declaration, http: { ...cfg.declaration.http, upstreams: u } } })}
      />
      <Layer4Section
        servers={cfg.declaration.layer4?.servers}
        onServersChange={s => update({ ...cfg, declaration: { ...cfg.declaration, layer4: { ...cfg.declaration.layer4, servers: s } } })}
        upstreams={cfg.declaration.layer4?.upstreams}
        onUpstreamsChange={u => update({ ...cfg, declaration: { ...cfg.declaration, layer4: { ...cfg.declaration.layer4, upstreams: u } } })}
      />
    </div>
  );
}
