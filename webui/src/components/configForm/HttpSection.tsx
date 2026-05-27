import type {
  ConfigData, HttpResolver, HttpProfiles, NMSCertificate,
} from './types';
import { emptyCertificate, emptyLogProfile } from './defaults';
import { SectionTitle, Field, TextInput, SelectInput, AddBtn, RemoveBtn, CollapseCard } from './primitives';
import { ProfilesSection } from './ProfilesSection';
import { ServersSection } from './ServersSection';
import { UpstreamsSection } from './UpstreamsSection';
import { PoliciesEditor } from './OutputSection';

type Http = NonNullable<ConfigData['declaration']['http']>;

export function HttpSection({ http, onChange, resolvers, onResolversChange, certificates, onCertificatesChange }: {
  http: Http;
  onChange: (h: Http) => void;
  resolvers: HttpResolver[];
  onResolversChange: (v: HttpResolver[]) => void;
  certificates: NMSCertificate[];
  onCertificatesChange: (v: NMSCertificate[]) => void;
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
  const policies       = http.policies       ?? [];
  const logProfiles    = http.log_profiles   ?? [];

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

      {/* Certificates — declaration-level, referenced by server TLS configs */}
      <div className="cf-subsection" id="cf-sec-certificates">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Certificates</span>
          <AddBtn label="Add certificate" onClick={() => onCertificatesChange([...certificates, emptyCertificate()])} />
        </div>
        {certificates.length === 0
          ? <p className="cf-empty">No certificates — add TLS certificate and key objects to include in the declaration.</p>
          : certificates.map((cert, ci) => (
            <CollapseCard key={ci} title={cert.name || <em>cert #{ci + 1}</em>} meta={cert.type} defaultOpen={!cert.name}>
              <div className="cf-grid-2">
                <Field label="Type">
                  <SelectInput
                    value={cert.type}
                    onChange={v => onCertificatesChange(certificates.map((x, idx) => idx === ci ? { ...x, type: v as NMSCertificate['type'] } : x))}
                    options={[{ value: 'certificate', label: 'Certificate' }, { value: 'key', label: 'Private key' }]}
                  />
                </Field>
                <Field label="Name" required>
                  <TextInput
                    value={cert.name}
                    onChange={v => onCertificatesChange(certificates.map((x, idx) => idx === ci ? { ...x, name: v } : x))}
                    placeholder="my-tls-cert"
                  />
                </Field>
                <Field label="Contents / URL" span="full" hint="PEM content or a URL/path to fetch it from.">
                  <TextInput
                    value={cert.contents?.content ?? ''}
                    onChange={v => onCertificatesChange(certificates.map((x, idx) => idx === ci ? { ...x, contents: { content: v } } : x))}
                    placeholder="-----BEGIN CERTIFICATE-----"
                    mono
                  />
                </Field>
              </div>
              <div className="cf-card-actions"><RemoveBtn onClick={() => onCertificatesChange(certificates.filter((_, idx) => idx !== ci))} /></div>
            </CollapseCard>
          ))
        }
      </div>

      {/* WAF Policies — declaration.http.policies */}
      <div id="cf-sec-policies">
        <PoliciesEditor
          policies={policies}
          onChange={v => onChange({ ...http, policies: v })}
        />
      </div>

      {/* Log Profiles — declaration.http.log_profiles */}
      <div className="cf-subsection" id="cf-sec-log-profiles">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Log Profiles</span>
          <AddBtn label="Add profile" onClick={() => onChange({ ...http, log_profiles: [...logProfiles, emptyLogProfile()] })} />
        </div>
        {logProfiles.length === 0
          ? <p className="cf-empty">No log profiles — add one to enable App Protect security event logging.</p>
          : logProfiles.map((lp, li) => {
            const ap = lp.app_protect ?? { name: '', format: 'default', type: 'blocked', max_request_size: '2k', max_message_size: '5k' };
            return (
              <CollapseCard key={li} title={ap.name || <em>log profile #{li + 1}</em>} meta={lp.type} defaultOpen={!ap.name}>
                <div className="cf-grid-2">
                  <Field label="Profile name" required>
                    <TextInput
                      value={ap.name}
                      onChange={v => onChange({ ...http, log_profiles: logProfiles.map((x, idx) => idx === li ? { ...x, app_protect: { ...ap, name: v } } : x) })}
                      placeholder="blocked-requests"
                    />
                  </Field>
                  <Field label="Log format">
                    <SelectInput
                      value={ap.format ?? 'default'}
                      onChange={v => onChange({ ...http, log_profiles: logProfiles.map((x, idx) => idx === li ? { ...x, app_protect: { ...ap, format: v } } : x) })}
                      options={[{ value: 'default', label: 'default' }, { value: 'grpc', label: 'grpc' }, { value: 'arcsight', label: 'arcsight' }, { value: 'splunk', label: 'splunk' }, { value: 'user-defined', label: 'user-defined' }]}
                    />
                  </Field>
                  <Field label="Log type">
                    <SelectInput
                      value={ap.type ?? 'blocked'}
                      onChange={v => onChange({ ...http, log_profiles: logProfiles.map((x, idx) => idx === li ? { ...x, app_protect: { ...ap, type: v } } : x) })}
                      options={[{ value: 'blocked', label: 'blocked' }, { value: 'illegal', label: 'illegal' }, { value: 'all', label: 'all' }]}
                    />
                  </Field>
                </div>
                <div className="cf-card-actions"><RemoveBtn onClick={() => onChange({ ...http, log_profiles: logProfiles.filter((_, idx) => idx !== li) })} /></div>
              </CollapseCard>
            );
          })
        }
      </div>
    </section>
  );
}
