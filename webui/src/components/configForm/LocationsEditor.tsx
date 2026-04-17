import type { Location, HttpProfiles } from './types';
import { emptyLocation } from './defaults';
import { Field, TextInput, SelectInput, Toggle, AddBtn, RemoveBtn, CollapseCard, ProfileSelect } from './primitives';
import {
  LogEditor, AppProtectEditor, SnippetEditor, HeadersEditor,
  LocationAuthEditor, LocationAuthzEditor, LocationCacheEditor,
  LocationRateLimitEditor, HealthCheckEditor, NjsHooksLocationEditor,
} from './LocationEditors';
import { ApiGatewayEditor } from './ApiGatewayEditor';

export const URI_MATCH_OPTIONS = [
  { value: 'prefix',  label: 'Prefix — matches any path starting with URI' },
  { value: 'exact',   label: 'Exact — matches only this exact URI' },
  { value: 'regex',   label: 'Regex — case-sensitive regular expression' },
  { value: 'iregex',  label: 'iRegex — case-insensitive regular expression' },
  { value: 'best',    label: 'Best — longest prefix + regex priority' },
];

export function LocationsEditor({ locations, onChange, profiles, njsProfileNames }: {
  locations: Location[];
  onChange: (l: Location[]) => void;
  profiles?: HttpProfiles;
  njsProfileNames?: string[];
}) {
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
        <CollapseCard
          key={i}
          title={loc.uri || <em>location #{i + 1}</em>}
          meta={loc.apigateway != null ? 'API Gateway' : (loc.upstream || '—')}
          defaultOpen={i === 0 && locations.length === 1}
        >
          <div className="cf-card-actions"><RemoveBtn onClick={() => remove(i)} /></div>
          <div className="cf-grid-3">
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
            <Field label="Upstream" hint='Full upstream reference including scheme, e.g. "http://my-upstream". Leave empty when using API Gateway routing.'>
              <TextInput value={loc.upstream ?? ''} onChange={v => update(i, { ...loc, upstream: v })} placeholder="http://my-upstream" mono />
            </Field>
          </div>
          {/* Caching profile reference (http.caching style) */}
          <div className="cf-subsection cf-subsection-tls">
            <div className="cf-subsection-header">
              <span className="cf-subsection-title">Caching Zone</span>
              <Toggle checked={!!loc.caching} onChange={v => update(i, { ...loc, caching: v ? '' : undefined })} label={loc.caching ? 'Configured' : 'Not configured'} />
            </div>
            {loc.caching !== undefined && (
              <Field label="Caching profile name" hint="Name of a caching zone defined in the HTTP caching section.">
                <ProfileSelect value={loc.caching ?? ''} onChange={v => update(i, { ...loc, caching: v })} options={profiles?.cacheNames ?? []} />
              </Field>
            )}
          </div>
          <LocationRateLimitEditor rl={loc.rate_limit} rateLimitNames={profiles?.rateLimitNames ?? []} onChange={v => update(i, { ...loc, rate_limit: v })} />
          <HealthCheckEditor hc={loc.health_check} onChange={v => update(i, { ...loc, health_check: v })} />
          <LocationCacheEditor cache={loc.cache} cacheNames={profiles?.cacheNames ?? []} onChange={v => update(i, { ...loc, cache: v })} />
          <LocationAuthEditor auth={loc.authentication} authClientNames={profiles?.authClientNames ?? []} authServerNames={profiles?.authServerNames ?? []} onChange={v => update(i, { ...loc, authentication: v })} />
          <LocationAuthzEditor authz={loc.authorization} authzNames={profiles?.authzNames ?? []} onChange={v => update(i, { ...loc, authorization: v })} />
          <HeadersEditor headers={loc.headers} onChange={v => update(i, { ...loc, headers: v })} />
          <AppProtectEditor ap={loc.app_protect} onChange={v => update(i, { ...loc, app_protect: v })} />
          <LogEditor log={loc.log} onChange={v => update(i, { ...loc, log: v })} />
          <NjsHooksLocationEditor hooks={loc.njs ?? []} onChange={v => update(i, { ...loc, njs: v })} njsProfileNames={njsProfileNames ?? []} />
          <SnippetEditor snippet={loc.snippet} onChange={v => update(i, { ...loc, snippet: v })} />
          <ApiGatewayEditor
            agw={loc.apigateway}
            onChange={agw => update(i, { ...loc, apigateway: agw })}
            profiles={profiles}
          />
        </CollapseCard>
      ))}
    </div>
  );
}
