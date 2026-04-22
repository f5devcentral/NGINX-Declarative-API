import type { Server, HttpProfiles } from './types';
import { emptyServer } from './defaults';
import { Field, TextInput, Toggle, AddBtn, RemoveBtn, CollapseCard, ProfileSelect } from './primitives';
import { LocationsEditor } from './LocationsEditor';
import {
  LogEditor, AppProtectEditor, SnippetEditor, HeadersEditor,
  LocationAuthEditor, LocationAuthzEditor, LocationCacheEditor, NjsHooksServerEditor,
} from './LocationEditors';
import { TlsEditor } from './TlsEditor';

export function ServersSection({ servers, onChange, profiles, authServerNames, njsProfileNames, resolverNames }: {
  servers: Server[];
  onChange: (s: Server[]) => void;
  profiles?: HttpProfiles;
  authServerNames?: string[];
  njsProfileNames?: string[];
  resolverNames?: string[];
}) {
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
            <Field label="Resolver" hint='Select a resolver profile defined in the HTTP Profiles → Resolvers section.'>
              <ProfileSelect value={srv.resolver ?? ''} onChange={v => update(i, { ...srv, resolver: v || undefined })} options={resolverNames ?? []} />
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

          <LogEditor log={srv.log} onChange={v => update(i, { ...srv, log: v })} />
          <AppProtectEditor ap={srv.app_protect} onChange={v => update(i, { ...srv, app_protect: v })} />
          <LocationCacheEditor cache={srv.cache} cacheNames={profiles?.cacheNames ?? []} onChange={v => update(i, { ...srv, cache: v })} />
          <LocationAuthEditor auth={srv.authentication} authClientNames={profiles?.authClientNames ?? []} authServerNames={authServerNames ?? profiles?.authServerNames ?? []} onChange={v => update(i, { ...srv, authentication: v })} />
          <LocationAuthzEditor authz={srv.authorization} authzNames={profiles?.authzNames ?? []} onChange={v => update(i, { ...srv, authorization: v })} />
          <HeadersEditor headers={srv.headers} onChange={v => update(i, { ...srv, headers: v })} />
          <NjsHooksServerEditor hooks={srv.njs ?? []} onChange={v => update(i, { ...srv, njs: v })} njsProfileNames={njsProfileNames ?? []} />
          <SnippetEditor snippet={srv.snippet} onChange={v => update(i, { ...srv, snippet: v })} />

          <LocationsEditor
            locations={srv.locations ?? []}
            onChange={locs => update(i, { ...srv, locations: locs })}
            profiles={profiles}
            njsProfileNames={njsProfileNames}
          />
        </CollapseCard>
      ))}
    </div>
  );
}
