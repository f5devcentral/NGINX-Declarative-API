import type { ConfigData } from './types';
import { Field, TextInput, NumberInput, Toggle, AddBtn, RemoveBtn, CollapseCard, SectionTitle } from './primitives';
import { SnippetEditor } from './LocationEditors';

type L4Servers  = NonNullable<NonNullable<ConfigData['declaration']['layer4']>['servers']>;
type L4Server   = L4Servers[number];
type L4Upstreams = NonNullable<NonNullable<ConfigData['declaration']['layer4']>['upstreams']>;
type L4Upstream = L4Upstreams[number];
type L4Origin   = NonNullable<L4Upstream['origin']>[number];

function L4ServersSection({ servers, onChange }: { servers: L4Servers; onChange: (s: L4Servers) => void }) {
  const update = (i: number, s: L4Server) => onChange(servers.map((x, idx) => idx === i ? s : x));
  const remove = (i: number) => onChange(servers.filter((_, idx) => idx !== i));
  const emptyL4Server = (): L4Server => ({ name: '', listen: { address: '' } } as L4Server);

  return (
    <div className="cf-group">
      <div className="cf-group-header">
        <span className="cf-group-title">Layer 4 Servers</span>
        <AddBtn label="Add server" onClick={() => onChange([...servers, emptyL4Server()])} />
      </div>
      {servers.length === 0 && <p className="cf-empty">No Layer 4 servers. Add a server to handle TCP/UDP traffic.</p>}
      {servers.map((sv, i) => (
        <CollapseCard key={i} title={(sv as any).name || <em>server #{i + 1}</em>} meta={(sv as any).listen?.address || '—'} defaultOpen={i === 0 && servers.length === 1}>
          <div className="cf-card-actions"><RemoveBtn onClick={() => remove(i)} /></div>
          <div className="cf-grid-2">
            <Field label="Server name" required>
              <TextInput value={(sv as any).name ?? ''} onChange={v => update(i, { ...sv, name: v } as L4Server)} placeholder="my-l4-server" />
            </Field>
            <Field label="Listen address" required hint='IP:port to listen on. Use "udp" suffix for UDP, e.g. "0.0.0.0:5000 udp".'>
              <TextInput value={(sv as any).listen?.address ?? ''} onChange={v => update(i, { ...sv, listen: { ...(sv as any).listen, address: v } } as L4Server)} placeholder="0.0.0.0:9000" mono />
            </Field>
            <Field label="Upstream" hint="Name of the Layer 4 upstream group to proxy to.">
              <TextInput value={(sv as any).upstream ?? ''} onChange={v => update(i, { ...sv, upstream: v } as L4Server)} placeholder="my-l4-upstream" />
            </Field>
            <Field label="Resolver">
              <TextInput value={(sv as any).resolver ?? ''} onChange={v => update(i, { ...sv, resolver: v || undefined } as L4Server)} placeholder="my-resolver" />
            </Field>
          </div>
          <div className="cf-field cf-field-inline">
            <Toggle checked={!!(sv as any).listen?.ssl} onChange={v => update(i, { ...sv, listen: { ...(sv as any).listen, ssl: v } } as L4Server)} label="TLS passthrough" />
            <p className="cf-hint">Enables SSL termination on the Layer 4 listener.</p>
          </div>
          <SnippetEditor snippet={(sv as any).snippet} onChange={v => update(i, { ...sv, snippet: v } as L4Server)} />
        </CollapseCard>
      ))}
    </div>
  );
}

function L4UpstreamsSection({ upstreams, onChange }: { upstreams: L4Upstreams; onChange: (u: L4Upstreams) => void }) {
  const update = (i: number, u: L4Upstream) => onChange(upstreams.map((x, idx) => idx === i ? u : x));
  const remove = (i: number) => onChange(upstreams.filter((_, idx) => idx !== i));
  const emptyL4Upstream = (): L4Upstream => ({ name: '', origin: [] } as unknown as L4Upstream);
  const emptyL4Origin = (): L4Origin => ({ server: '' } as L4Origin);

  const addOrigin = (i: number) =>
    update(i, { ...upstreams[i], origin: [...((upstreams[i] as any).origin ?? []), emptyL4Origin()] } as L4Upstream);
  const updOrigin = (i: number, oi: number, o: L4Origin) =>
    update(i, { ...upstreams[i], origin: ((upstreams[i] as any).origin ?? []).map((x: L4Origin, oIdx: number) => oIdx === oi ? o : x) } as L4Upstream);
  const remOrigin = (i: number, oi: number) =>
    update(i, { ...upstreams[i], origin: ((upstreams[i] as any).origin ?? []).filter((_: L4Origin, oIdx: number) => oIdx !== oi) } as L4Upstream);

  return (
    <div className="cf-group">
      <div className="cf-group-header">
        <span className="cf-group-title">Layer 4 Upstreams</span>
        <AddBtn label="Add upstream" onClick={() => onChange([...upstreams, emptyL4Upstream()])} />
      </div>
      {upstreams.length === 0 && <p className="cf-empty">No Layer 4 upstreams. Add an upstream to define backend servers for TCP/UDP traffic.</p>}
      {upstreams.map((up, i) => (
        <CollapseCard key={i} title={(up as any).name || <em>upstream #{i + 1}</em>} meta={`${((up as any).origin ?? []).length} origin(s)`} defaultOpen={i === 0 && upstreams.length === 1}>
          <div className="cf-card-actions"><RemoveBtn onClick={() => remove(i)} /></div>
          <div className="cf-grid-2">
            <Field label="Upstream name" required>
              <TextInput value={(up as any).name ?? ''} onChange={v => update(i, { ...up, name: v } as L4Upstream)} placeholder="my-l4-upstream" />
            </Field>
            <Field label="Resolver">
              <TextInput value={(up as any).resolver ?? ''} onChange={v => update(i, { ...up, resolver: v || undefined } as L4Upstream)} placeholder="my-resolver" />
            </Field>
          </div>
          <div className="cf-subsection">
            <div className="cf-subsection-header">
              <span className="cf-subsection-title">Origins</span>
              <AddBtn label="Add origin" onClick={() => addOrigin(i)} />
            </div>
            {((up as any).origin ?? []).length === 0
              ? <p className="cf-hint">No origins. Add a backend server.</p>
              : ((up as any).origin ?? []).map((o: L4Origin, oi: number) => (
                <div key={oi} className="cf-origin-row">
                  <Field label="Server address" hint='"host:port"'>
                    <TextInput value={(o as any).server ?? ''} onChange={v => updOrigin(i, oi, { ...o, server: v } as L4Origin)} placeholder="10.0.0.1:9000" mono />
                  </Field>
                  <Field label="Weight">
                    <NumberInput value={(o as any).weight ?? 1} onChange={v => updOrigin(i, oi, { ...o, weight: v } as L4Origin)} min={1} />
                  </Field>
                  <Field label="Max fails">
                    <NumberInput value={(o as any).max_fails ?? 1} onChange={v => updOrigin(i, oi, { ...o, max_fails: v } as L4Origin)} min={0} />
                  </Field>
                  <Field label="Fail timeout">
                    <TextInput value={(o as any).fail_timeout ?? '10s'} onChange={v => updOrigin(i, oi, { ...o, fail_timeout: v } as L4Origin)} placeholder="10s" mono />
                  </Field>
                  <Field label="Backup">
                    <Toggle checked={(o as any).backup ?? false} onChange={v => updOrigin(i, oi, { ...o, backup: v } as L4Origin)} label="Backup only" />
                  </Field>
                  <div className="cf-origin-remove"><RemoveBtn onClick={() => remOrigin(i, oi)} /></div>
                </div>
              ))
            }
          </div>
        </CollapseCard>
      ))}
    </div>
  );
}

export { L4ServersSection, L4UpstreamsSection };

export function Layer4Section({
  servers, onServersChange, upstreams, onUpstreamsChange,
}: {
  servers: L4Servers | undefined;
  onServersChange: (s: L4Servers) => void;
  upstreams: L4Upstreams | undefined;
  onUpstreamsChange: (u: L4Upstreams) => void;
}) {
  return (
    <section className="cf-section">
      <SectionTitle title="Layer 4 (TCP/UDP)" sub="Stream proxy servers and upstream groups — optional" />
      <L4ServersSection servers={servers ?? []} onChange={onServersChange} />
      <L4UpstreamsSection upstreams={upstreams ?? []} onChange={onUpstreamsChange} />
    </section>
  );
}
