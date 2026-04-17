import type { Upstream, Origin } from './types';
import { emptyUpstream, emptyOrigin } from './defaults';
import { Field, TextInput, NumberInput, Toggle, AddBtn, RemoveBtn, CollapseCard } from './primitives';
import { SnippetEditor } from './LocationEditors';

export function UpstreamsSection({ upstreams, onChange }: { upstreams: Upstream[]; onChange: (u: Upstream[]) => void }) {
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

          {/* Sticky cookie session persistence */}
          <div className="cf-subsection cf-subsection-tls">
            <div className="cf-subsection-header">
              <span className="cf-subsection-title">Sticky Session (NGINX Plus)</span>
              <Toggle checked={up.sticky != null} onChange={v => update(i, { ...up, sticky: v ? { cookie: 'srv_id' } : undefined })} label={up.sticky != null ? 'Enabled' : 'Disabled'} />
            </div>
            {up.sticky != null && (
              <div className="cf-grid-2">
                <Field label="Cookie name" required hint="Name of the sticky session cookie.">
                  <TextInput value={up.sticky.cookie} onChange={v => update(i, { ...up, sticky: { ...up.sticky!, cookie: v } })} placeholder="srv_id" mono />
                </Field>
                <Field label="Expires" hint='Cookie max-age, e.g. "1h". Leave empty for session cookie.'>
                  <TextInput value={up.sticky.expires ?? ''} onChange={v => update(i, { ...up, sticky: { ...up.sticky!, expires: v || undefined } })} placeholder="1h" mono />
                </Field>
                <Field label="Domain" hint='Cookie domain attribute, e.g. ".example.com".'>
                  <TextInput value={up.sticky.domain ?? ''} onChange={v => update(i, { ...up, sticky: { ...up.sticky!, domain: v || undefined } })} placeholder=".example.com" mono />
                </Field>
                <Field label="Path" hint='Cookie path attribute. Default is "/".'>
                  <TextInput value={up.sticky.path ?? ''} onChange={v => update(i, { ...up, sticky: { ...up.sticky!, path: v || undefined } })} placeholder="/" mono />
                </Field>
              </div>
            )}
          </div>

          <SnippetEditor snippet={up.snippet} onChange={v => update(i, { ...up, snippet: v })} />

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
                <Field label="Max connections" hint="Maximum concurrent connections to this origin. 0 means unlimited (NGINX Plus only).">
                  <NumberInput value={o.max_conns ?? 0} onChange={v => updOrigin(i, oi, { ...o, max_conns: v })} min={0} />
                </Field>
                <Field label="Slow start" hint='Gradually ramp up connections after recovery, e.g. "30s". Leave empty to disable (NGINX Plus only).'>
                  <TextInput value={o.slow_start ?? ''} onChange={v => updOrigin(i, oi, { ...o, slow_start: v || undefined })} placeholder="30s" mono />
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
