import type {
  ConfigData, HttpResolver, HttpProfiles,
} from './types';
import { SectionTitle } from './primitives';
import { ProfilesSection } from './ProfilesSection';
import { ServersSection } from './ServersSection';
import { UpstreamsSection } from './UpstreamsSection';

type Http = NonNullable<ConfigData['declaration']['http']>;

export function HttpSection({ http, onChange, resolvers, onResolversChange }: {
  http: Http;
  onChange: (h: Http) => void;
  resolvers: HttpResolver[];
  onResolversChange: (v: HttpResolver[]) => void;
}) {
  const servers      = http.servers      ?? [];
  const upstreams    = http.upstreams    ?? [];
  const rateLimits   = http.rate_limit   ?? [];
  const authentication = http.authentication ?? { client: [] };
  const authorization  = http.authorization  ?? [];
  const cache          = http.cache          ?? [];
  const maps           = http.maps           ?? [];
  const logformats     = http.logformats     ?? [];
  const njs            = http.njs            ?? [];
  const njsProfiles    = http.njs_profiles   ?? [];
  const acmeIssuers    = http.acme_issuers   ?? [];
  const nginxPlusApi   = http.nginx_plus_api;

  const njsProfileNames = njsProfiles.map(p => p.name).filter(Boolean);
  const authServerNames = (authentication.server ?? []).map(s => s.name).filter(Boolean);
  const resolverNames   = resolvers.map(r => r.name).filter(Boolean);

  const profiles: HttpProfiles = {
    rateLimitNames:  rateLimits.map(r => r.name).filter(Boolean),
    authClientNames: (authentication.client ?? []).map(c => c.name).filter(Boolean),
    authServerNames,
    authzNames:      authorization.map(a => a.name).filter(Boolean),
    cacheNames:      cache.map(c => c.name).filter(Boolean),
  };

  return (
    <section className="cf-section" id="cf-sec-http">
      <SectionTitle title="HTTP" sub="Virtual servers and upstream groups for HTTP/S traffic" />

      <div id="cf-sec-http-profiles">
      <ProfilesSection
        rateLimits={rateLimits}
        onRateLimitsChange={v => onChange({ ...http, rate_limit: v })}
        authentication={authentication}
        onAuthenticationChange={v => onChange({ ...http, authentication: v })}
        authorization={authorization}
        onAuthorizationChange={v => onChange({ ...http, authorization: v })}
        cache={cache}
        onCacheChange={v => onChange({ ...http, cache: v })}
        maps={maps}
        onMapsChange={v => onChange({ ...http, maps: v })}
        logformats={logformats}
        onLogFormatsChange={v => onChange({ ...http, logformats: v })}
        njs={njs}
        onNjsChange={v => onChange({ ...http, njs: v })}
        njsProfiles={njsProfiles}
        onNjsProfilesChange={v => onChange({ ...http, njs_profiles: v })}
        acmeIssuers={acmeIssuers}
        onAcmeIssuersChange={v => onChange({ ...http, acme_issuers: v })}
        nginxPlusApi={nginxPlusApi}
        onNginxPlusApiChange={v => onChange({ ...http, nginx_plus_api: v })}
        resolvers={resolvers}
        onResolversChange={onResolversChange}
      />
      </div>

      <div id="cf-sec-http-servers">
      <ServersSection
        servers={servers}
        onChange={v => onChange({ ...http, servers: v })}
        profiles={profiles}
        authServerNames={authServerNames}
        njsProfileNames={njsProfileNames}
        resolverNames={resolverNames}
      />
      </div>

      <div id="cf-sec-http-upstreams">
      <UpstreamsSection
        upstreams={upstreams}
        onChange={v => onChange({ ...http, upstreams: v })}
        resolverNames={resolverNames}
      />
      </div>
    </section>
  );
}
