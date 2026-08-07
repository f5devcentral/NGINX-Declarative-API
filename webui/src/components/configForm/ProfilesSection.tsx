import type {
  HttpRateLimit, HttpAuthentication, HttpAuthorization, HttpCache, HttpMap,
  HttpLogFormat, NjsHookServer, NjsFile, AcmeIssuer, NginxPlusApi, HttpResolver,
} from './types';
import {
  emptyHttpRateLimit, emptyHttpAuthClient, emptyHttpAuthServerToken, emptyHttpAuthServerMtls,
  emptyHttpAuthorization, emptyHttpAuthzClaim, emptyHttpCache, emptyHttpMap, emptyMapEntry,
  emptyHttpLogFormat, emptyNjsFile, emptyAcmeIssuer, emptyHttpResolver,
} from './defaults';
import { Field, TextInput, NumberInput, SelectInput, Toggle, AddBtn, RemoveBtn, CollapseCard } from './primitives';
import { NjsHooksServerEditor } from './LocationEditors';
import { PathsInput } from './ApiGatewayEditor';

export const AUTH_CLIENT_TYPE_OPTIONS = [
  { value: 'jwt',   label: 'JWT' },
  { value: 'mtls',  label: 'mTLS' },
  { value: 'oidc',  label: 'OIDC' },
];

export const AUTH_SERVER_TYPE_OPTIONS = [
  { value: 'token', label: 'Token' },
  { value: 'mtls',  label: 'mTLS' },
];

export const AUTH_TYPE_OPTIONS = [
  { value: 'jwt', label: 'JWT' },
];

export function ProfilesSection({
  rateLimits, onRateLimitsChange,
  authentication, onAuthenticationChange,
  authorization, onAuthorizationChange,
  cache, onCacheChange,
  maps, onMapsChange,
  logformats, onLogFormatsChange,
  njs, onNjsChange,
  njsProfiles, onNjsProfilesChange,
  acmeIssuers, onAcmeIssuersChange,
  nginxPlusApi, onNginxPlusApiChange,
  resolvers, onResolversChange,
}: {
  rateLimits: HttpRateLimit[];            onRateLimitsChange: (v: HttpRateLimit[]) => void;
  authentication: HttpAuthentication;     onAuthenticationChange: (v: HttpAuthentication) => void;
  authorization: HttpAuthorization[];     onAuthorizationChange: (v: HttpAuthorization[]) => void;
  cache: HttpCache[];                     onCacheChange: (v: HttpCache[]) => void;
  maps: HttpMap[];                        onMapsChange: (v: HttpMap[]) => void;
  logformats: HttpLogFormat[];            onLogFormatsChange: (v: HttpLogFormat[]) => void;
  njs: NjsHookServer[];                   onNjsChange: (v: NjsHookServer[]) => void;
  njsProfiles: NjsFile[];                 onNjsProfilesChange: (v: NjsFile[]) => void;
  acmeIssuers: AcmeIssuer[];              onAcmeIssuersChange: (v: AcmeIssuer[]) => void;
  nginxPlusApi: NginxPlusApi | undefined; onNginxPlusApiChange: (v: NginxPlusApi | undefined) => void;
  resolvers: HttpResolver[];              onResolversChange: (v: HttpResolver[]) => void;
}) {
  const clients = authentication.client ?? [];
  const servers = authentication.server ?? [];
  const njsProfileNames = njsProfiles.map(p => p.name).filter(Boolean);

  return (
    <div className="cf-subsection">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Profiles</span>
      </div>

      {/* ── Rate Limiting ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Rate Limiting</span>
          <AddBtn label="Add profile" onClick={() => onRateLimitsChange([...rateLimits, emptyHttpRateLimit()])} />
        </div>
        {rateLimits.length === 0
          ? <p className="cf-empty cf-empty-sm">No rate limit profiles. Add one to define a named zone for use in API Gateway configurations.</p>
          : rateLimits.map((rl, i) => (
            <CollapseCard key={i} title={rl.name || <em>rate limit #{i + 1}</em>} meta={rl.rate || undefined} defaultOpen={!rl.name}>
              <div className="cf-grid-2">
                <Field label="Name" required error={!rl.name.trim() ? 'Required' : undefined}
                  hint="Zone name — referenced by API Gateway rate limit rules.">
                  <TextInput value={rl.name}
                    onChange={v => onRateLimitsChange(rateLimits.map((x, idx) => idx === i ? { ...x, name: v } : x))}
                    placeholder="petstore_ratelimit"
                    error={!rl.name.trim()} />
                </Field>
                <Field label="Rate" required error={!rl.rate.trim() ? 'Required' : undefined}
                  hint='Requests per second or minute, e.g. "10r/s" or "100r/m".'>
                  <TextInput value={rl.rate}
                    onChange={v => onRateLimitsChange(rateLimits.map((x, idx) => idx === i ? { ...x, rate: v } : x))}
                    placeholder="10r/s" mono
                    error={!rl.rate.trim()} />
                </Field>
                <Field label="Key" required error={!rl.key.trim() ? 'Required' : undefined}
                  hint='NGINX variable used to differentiate clients, e.g. "$binary_remote_addr".'>
                  <TextInput value={rl.key}
                    onChange={v => onRateLimitsChange(rateLimits.map((x, idx) => idx === i ? { ...x, key: v } : x))}
                    placeholder="$binary_remote_addr" mono
                    error={!rl.key.trim()} />
                </Field>
                <Field label="Zone size" required error={!rl.size.trim() ? 'Required' : undefined}
                  hint='Shared memory zone size, e.g. "10m".'>
                  <TextInput value={rl.size}
                    onChange={v => onRateLimitsChange(rateLimits.map((x, idx) => idx === i ? { ...x, size: v } : x))}
                    placeholder="10m" mono
                    error={!rl.size.trim()} />
                </Field>
              </div>
              <div className="cf-card-actions"><RemoveBtn onClick={() => onRateLimitsChange(rateLimits.filter((_, idx) => idx !== i))} /></div>
            </CollapseCard>
          ))
        }
      </div>

      {/* ── Authentication Client ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Authentication — Client Profiles</span>
          <AddBtn label="Add profile" onClick={() => onAuthenticationChange({ ...authentication, client: [...clients, emptyHttpAuthClient()] })} />
        </div>
        {clients.length === 0
          ? <p className="cf-empty cf-empty-sm">No client authentication profiles. Add one to define a named client authentication policy.</p>
          : clients.map((c, i) => {
            const jwt = c.jwt ?? { realm: '', key: '', jwt_type: 'signed', cachetime: 0, token_location: '' };
            const mtls = c.mtls ?? { enabled: 'on', client_certificates: '', trusted_ca_certificates: '' };
            const oidc = c.oidc ?? { issuer: '', client_id: '', client_secret: '', redirect_uri: '/oidc_callback', scope: 'openid', session_timeout: '8h' };
            return (
              <CollapseCard key={i} title={c.name || <em>client #{i + 1}</em>} meta={c.type || undefined} defaultOpen={!c.name}>
                <div className="cf-grid-2">
                  <Field label="Name" required error={!c.name.trim() ? 'Required' : undefined}
                    hint="Profile name — referenced by server/location authentication rules.">
                    <TextInput value={c.name}
                      onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, name: v } : x) })}
                      placeholder="Petstore JWT Authentication"
                      error={!c.name.trim()} />
                  </Field>
                  <Field label="Type" required>
                    <SelectInput value={c.type}
                      onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, type: v } : x) })}
                      options={AUTH_CLIENT_TYPE_OPTIONS} />
                  </Field>
                </div>
                {c.type === 'jwt' && (
                  <div className="cf-grid-2">
                    <Field label="Realm" hint='JWT realm string shown in WWW-Authenticate challenges.'>
                      <TextInput value={jwt.realm}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, jwt: { ...jwt, realm: v } } : x) })}
                        placeholder="My API" />
                    </Field>
                    <Field label="JWT type">
                      <SelectInput value={jwt.jwt_type ?? 'signed'}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, jwt: { ...jwt, jwt_type: v } } : x) })}
                        options={[{ value: 'signed', label: 'Signed' }, { value: 'encrypted', label: 'Encrypted' }, { value: 'nested', label: 'Nested' }]} />
                    </Field>
                    <Field label="Cache time (s)" hint="Seconds to cache JWT validation results. 0 disables caching.">
                      <NumberInput value={jwt.cachetime ?? 0}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, jwt: { ...jwt, cachetime: v } } : x) })} />
                    </Field>
                    <Field label="Token location" hint='Optional variable holding the JWT, e.g. "$arg_token". Leave empty to use Authorization header.'>
                      <TextInput value={jwt.token_location ?? ''}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, jwt: { ...jwt, token_location: v } } : x) })}
                        placeholder="$arg_token" mono />
                    </Field>
                    <Field label="Key / JWKS" span="full" required
                      error={!jwt.key.trim() ? 'Required' : undefined}
                      hint="Inline JWKS JSON, a JWKS URL, or a symmetric secret key.">
                      <TextInput value={jwt.key}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, jwt: { ...jwt, key: v } } : x) })}
                        placeholder='{"keys":[{"k":"...","kty":"oct","kid":"0001"}]}'
                        mono
                        error={!jwt.key.trim()} />
                    </Field>
                  </div>
                )}
                {c.type === 'mtls' && (
                  <div className="cf-grid-2">
                    <Field label="Enabled" hint='"on", "off", "optional", "optional_no_ca".'>
                      <SelectInput value={mtls.enabled ?? 'on'}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, mtls: { ...mtls, enabled: v } } : x) })}
                        options={[{ value: 'on', label: 'on' }, { value: 'off', label: 'off' }, { value: 'optional', label: 'optional' }, { value: 'optional_no_ca', label: 'optional_no_ca' }]} />
                    </Field>
                    <Field label="Client certificates" required hint="Name of the certificate bundle (from certificates section).">
                      <TextInput value={mtls.client_certificates}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, mtls: { ...mtls, client_certificates: v } } : x) })}
                        placeholder="client-ca-bundle" />
                    </Field>
                    <Field label="Trusted CA certificates" hint="Name of the trusted CA bundle for verification.">
                      <TextInput value={mtls.trusted_ca_certificates ?? ''}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, mtls: { ...mtls, trusted_ca_certificates: v } } : x) })}
                        placeholder="trusted-ca" />
                    </Field>
                  </div>
                )}
                {c.type === 'oidc' && (
                  <div className="cf-grid-2">
                    <Field label="Issuer" required hint="OIDC provider issuer URL.">
                      <TextInput value={oidc.issuer}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, oidc: { ...oidc, issuer: v } } : x) })}
                        placeholder="https://idp.example.com" mono />
                    </Field>
                    <Field label="Client ID" required>
                      <TextInput value={oidc.client_id}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, oidc: { ...oidc, client_id: v } } : x) })}
                        placeholder="my-client-id" />
                    </Field>
                    <Field label="Client secret" required>
                      <TextInput value={oidc.client_secret} type="password"
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, oidc: { ...oidc, client_secret: v } } : x) })}
                        placeholder="••••••••" />
                    </Field>
                    <Field label="Config URL" hint="Optional OIDC discovery URL override.">
                      <TextInput value={oidc.config_url ?? ''}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, oidc: { ...oidc, config_url: v } } : x) })}
                        placeholder="https://idp.example.com/.well-known/openid-configuration" mono />
                    </Field>
                    <Field label="Redirect URI" hint='Callback URI registered in the IdP, e.g. "/oidc_callback".'>
                      <TextInput value={oidc.redirect_uri ?? '/oidc_callback'}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, oidc: { ...oidc, redirect_uri: v } } : x) })}
                        placeholder="/oidc_callback" mono />
                    </Field>
                    <Field label="Scope">
                      <TextInput value={oidc.scope ?? 'openid'}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, oidc: { ...oidc, scope: v } } : x) })}
                        placeholder="openid profile email" mono />
                    </Field>
                    <Field label="Session timeout">
                      <TextInput value={oidc.session_timeout ?? '8h'}
                        onChange={v => onAuthenticationChange({ ...authentication, client: clients.map((x, idx) => idx === i ? { ...x, oidc: { ...oidc, session_timeout: v } } : x) })}
                        placeholder="8h" mono />
                    </Field>
                  </div>
                )}
                <div className="cf-card-actions"><RemoveBtn onClick={() => onAuthenticationChange({ ...authentication, client: clients.filter((_, idx) => idx !== i) })} /></div>
              </CollapseCard>
            );
          })
        }
      </div>

      {/* ── Authentication Server ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Authentication — Server Profiles</span>
          <div style={{ display: 'flex', gap: '0.35rem' }}>
            <AddBtn label="Add token" onClick={() => onAuthenticationChange({ ...authentication, server: [...servers, emptyHttpAuthServerToken()] })} />
            <AddBtn label="Add mTLS" onClick={() => onAuthenticationChange({ ...authentication, server: [...servers, emptyHttpAuthServerMtls()] })} />
          </div>
        </div>
        {servers.length === 0
          ? <p className="cf-empty cf-empty-sm">No server authentication profiles. Add one to define outbound authentication to upstream servers.</p>
          : servers.map((s, i) => {
            const tok = s.token ?? { token: '', type: 'bearer' };
            const smtls = s.mtls ?? { certificate: '', key: '' };
            return (
              <CollapseCard key={i} title={s.name || <em>server #{i + 1}</em>} meta={s.type || undefined} defaultOpen={!s.name}>
                <div className="cf-grid-2">
                  <Field label="Name" required error={!s.name.trim() ? 'Required' : undefined}>
                    <TextInput value={s.name}
                      onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, name: v } : x) })}
                      placeholder="upstream-auth"
                      error={!s.name.trim()} />
                  </Field>
                  <Field label="Type" required>
                    <SelectInput value={s.type}
                      onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, type: v } : x) })}
                      options={AUTH_SERVER_TYPE_OPTIONS} />
                  </Field>
                </div>
                {s.type === 'token' && (
                  <div className="cf-grid-2">
                    <Field label="Token type" hint='"bearer", "header", or "basic"'>
                      <SelectInput value={tok.type ?? 'bearer'}
                        onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, token: { ...tok, type: v } } : x) })}
                        options={[{ value: 'bearer', label: 'Bearer' }, { value: 'header', label: 'Header' }, { value: 'basic', label: 'Basic' }]} />
                    </Field>
                    {(tok.type === 'bearer' || tok.type === '' || tok.type === undefined) && (
                      <Field label="Token value" required>
                        <TextInput value={tok.token}
                          onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, token: { ...tok, token: v } } : x) })}
                          placeholder="eyJ..." mono />
                      </Field>
                    )}
                    {tok.type === 'header' && (
                      <>
                        <Field label="Token value" required>
                          <TextInput value={tok.token}
                            onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, token: { ...tok, token: v } } : x) })}
                            placeholder="my-token-value" mono />
                        </Field>
                        <Field label="Header name" required hint="Name of the request header to set.">
                          <TextInput value={tok.location ?? ''}
                            onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, token: { ...tok, location: v } } : x) })}
                            placeholder="X-Api-Key" mono />
                        </Field>
                      </>
                    )}
                    {tok.type === 'basic' && (
                      <>
                        <Field label="Username" required>
                          <TextInput value={tok.username ?? ''}
                            onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, token: { ...tok, username: v } } : x) })}
                            placeholder="user" />
                        </Field>
                        <Field label="Password" required>
                          <TextInput value={tok.password ?? ''} type="password"
                            onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, token: { ...tok, password: v } } : x) })}
                            placeholder="••••••••" />
                        </Field>
                      </>
                    )}
                  </div>
                )}
                {s.type === 'mtls' && (
                  <div className="cf-grid-2">
                    <Field label="Client certificate" required hint="Name of the certificate from the certificates section.">
                      <TextInput value={smtls.certificate}
                        onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, mtls: { ...smtls, certificate: v } } : x) })}
                        placeholder="client-cert" />
                    </Field>
                    <Field label="Client key" required>
                      <TextInput value={smtls.key}
                        onChange={v => onAuthenticationChange({ ...authentication, server: servers.map((x, idx) => idx === i ? { ...x, mtls: { ...smtls, key: v } } : x) })}
                        placeholder="client-key" />
                    </Field>
                  </div>
                )}
                <div className="cf-card-actions"><RemoveBtn onClick={() => onAuthenticationChange({ ...authentication, server: servers.filter((_, idx) => idx !== i) })} /></div>
              </CollapseCard>
            );
          })
        }
      </div>

      {/* ── Authorization ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Authorization</span>
          <AddBtn label="Add profile" onClick={() => onAuthorizationChange([...authorization, emptyHttpAuthorization()])} />
        </div>
        {authorization.length === 0
          ? <p className="cf-empty cf-empty-sm">No authorization profiles. Add one to define JWT claim-based access control policies.</p>
          : authorization.map((az, i) => {
            const claims = az.jwt?.claims ?? [];
            return (
              <CollapseCard key={i} title={az.name || <em>authz #{i + 1}</em>} meta={az.type || undefined} defaultOpen={!az.name}>
                <div className="cf-grid-2">
                  <Field label="Name" required error={!az.name.trim() ? 'Required' : undefined}
                    hint="Profile name — referenced by API Gateway authorization rules.">
                    <TextInput value={az.name}
                      onChange={v => onAuthorizationChange(authorization.map((x, idx) => idx === i ? { ...x, name: v } : x))}
                      placeholder="JWT role based authorization"
                      error={!az.name.trim()} />
                  </Field>
                  <Field label="Type" required>
                    <SelectInput value={az.type}
                      onChange={v => onAuthorizationChange(authorization.map((x, idx) => idx === i ? { ...x, type: v } : x))}
                      options={AUTH_TYPE_OPTIONS} />
                  </Field>
                </div>
                {az.type === 'jwt' && (
                  <div className="cf-subsection">
                    <div className="cf-subsection-header">
                      <span className="cf-subsection-title">Claims</span>
                      <AddBtn label="Add claim" onClick={() => onAuthorizationChange(authorization.map((x, idx) => idx === i
                        ? { ...x, jwt: { claims: [...claims, emptyHttpAuthzClaim()] } }
                        : x))} />
                    </div>
                    {claims.length === 0
                      ? <p className="cf-empty cf-empty-sm">No claims. Add a claim to restrict access based on JWT payload values.</p>
                      : claims.map((cl, ci) => (
                        <div key={ci} className="cf-agw-item-row">
                          <Field label="Claim name" required error={!cl.name.trim() ? 'Required' : undefined}
                            hint='JWT claim key to check, e.g. "roles".'>
                            <TextInput value={cl.name}
                              onChange={v => onAuthorizationChange(authorization.map((x, idx) => idx === i
                                ? { ...x, jwt: { claims: claims.map((c, j) => j === ci ? { ...c, name: v } : c) } }
                                : x))}
                              placeholder="roles"
                              error={!cl.name.trim()} />
                          </Field>
                          <Field label="Allowed values" hint="One value per line. Regex patterns are supported (prefix with ~).">
                            <PathsInput
                              value={cl.value}
                              onChange={v => onAuthorizationChange(authorization.map((x, idx) => idx === i
                                ? { ...x, jwt: { claims: claims.map((c, j) => j === ci ? { ...c, value: v } : c) } }
                                : x))}
                              placeholder="~(devops)&#10;admin" />
                          </Field>
                          <Field label="Error code" hint="HTTP status code returned when the claim check fails.">
                            <NumberInput value={cl.errorcode ?? 403}
                              onChange={v => onAuthorizationChange(authorization.map((x, idx) => idx === i
                                ? { ...x, jwt: { claims: claims.map((c, j) => j === ci ? { ...c, errorcode: v } : c) } }
                                : x))} />
                          </Field>
                          <div className="cf-agw-item-remove">
                            <RemoveBtn onClick={() => onAuthorizationChange(authorization.map((x, idx) => idx === i
                              ? { ...x, jwt: { claims: claims.filter((_, j) => j !== ci) } }
                              : x))} />
                          </div>
                        </div>
                      ))
                    }
                  </div>
                )}
                <div className="cf-card-actions"><RemoveBtn onClick={() => onAuthorizationChange(authorization.filter((_, idx) => idx !== i))} /></div>
              </CollapseCard>
            );
          })
        }
      </div>

      {/* ── Cache ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Cache</span>
          <AddBtn label="Add profile" onClick={() => onCacheChange([...cache, emptyHttpCache()])} />
        </div>
        {cache.length === 0
          ? <p className="cf-empty cf-empty-sm">No cache profiles. Add one to define a named proxy cache zone.</p>
          : cache.map((c, i) => (
            <CollapseCard key={i} title={c.name || <em>cache #{i + 1}</em>} meta={c.size || undefined} defaultOpen={!c.name}>
              <div className="cf-grid-2">
                <Field label="Name" required error={!c.name.trim() ? 'Required' : undefined}
                  hint="Zone name — referenced by API Gateway and server/location cache rules.">
                  <TextInput value={c.name}
                    onChange={v => onCacheChange(cache.map((x, idx) => idx === i ? { ...x, name: v } : x))}
                    placeholder="10m cache"
                    error={!c.name.trim()} />
                </Field>
                <Field label="Zone size" required error={!c.size.trim() ? 'Required' : undefined}
                  hint='Shared memory zone size, e.g. "10m".'>
                  <TextInput value={c.size}
                    onChange={v => onCacheChange(cache.map((x, idx) => idx === i ? { ...x, size: v } : x))}
                    placeholder="10m" mono
                    error={!c.size.trim()} />
                </Field>
                <Field label="Base path" required error={!c.basepath.trim() ? 'Required' : undefined}
                  hint="Filesystem directory where cache files are stored.">
                  <TextInput value={c.basepath}
                    onChange={v => onCacheChange(cache.map((x, idx) => idx === i ? { ...x, basepath: v } : x))}
                    placeholder="/var/cache/nginx/api" mono
                    error={!c.basepath.trim()} />
                </Field>
                <Field label="Default TTL" required error={!c.ttl.trim() ? 'Required' : undefined}
                  hint='Time to live for cached responses with no explicit Expires/Cache-Control, e.g. "10m".'>
                  <TextInput value={c.ttl}
                    onChange={v => onCacheChange(cache.map((x, idx) => idx === i ? { ...x, ttl: v } : x))}
                    placeholder="10m" mono
                    error={!c.ttl.trim()} />
                </Field>
                <Field label="Max size" hint='Maximum size of the cache on disk, e.g. "1g". Leave empty for no limit.'>
                  <TextInput value={c.max_size ?? ''}
                    onChange={v => onCacheChange(cache.map((x, idx) => idx === i ? { ...x, max_size: v } : x))}
                    placeholder="1g" mono />
                </Field>
                <Field label="Min free" hint='Minimum free space to maintain on the filesystem, e.g. "512m".'>
                  <TextInput value={c.min_free ?? ''}
                    onChange={v => onCacheChange(cache.map((x, idx) => idx === i ? { ...x, min_free: v } : x))}
                    placeholder="512m" mono />
                </Field>
              </div>
              <div className="cf-card-actions"><RemoveBtn onClick={() => onCacheChange(cache.filter((_, idx) => idx !== i))} /></div>
            </CollapseCard>
          ))
        }
      </div>

      {/* ── Maps ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Maps</span>
          <AddBtn label="Add map" onClick={() => onMapsChange([...maps, emptyHttpMap()])} />
        </div>
        {maps.length === 0
          ? <p className="cf-empty cf-empty-sm">No maps. Add one to define variable mappings using NGINX map blocks.</p>
          : maps.map((m, i) => (
            <CollapseCard key={i} title={m.variable || <em>map #{i + 1}</em>} meta={m.match || undefined} defaultOpen={!m.variable}>
              <div className="cf-grid-2">
                <Field label="Source variable" required hint='NGINX variable to match against, e.g. "$uri" or "$http_host".'>
                  <TextInput value={m.match}
                    onChange={v => onMapsChange(maps.map((x, idx) => idx === i ? { ...x, match: v } : x))}
                    placeholder="$uri" mono />
                </Field>
                <Field label="Destination variable" required hint='Variable to set, e.g. "$target_uri". Must include the $ prefix.'>
                  <TextInput value={m.variable}
                    onChange={v => onMapsChange(maps.map((x, idx) => idx === i ? { ...x, variable: v } : x))}
                    placeholder="$target_uri" mono />
                </Field>
              </div>
              <div className="cf-subsection">
                <div className="cf-subsection-header">
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)' }}>Entries</span>
                  <AddBtn label="Add entry" onClick={() => onMapsChange(maps.map((x, idx) => idx === i ? { ...x, entries: [...(x.entries ?? []), emptyMapEntry()] } : x))} />
                </div>
                {(m.entries ?? []).length === 0
                  ? <p className="cf-hint">No entries — add key/value pairs to define the map.</p>
                  : (m.entries ?? []).map((e, ei) => (
                    <div key={ei} className="cf-agw-item-row">
                      <Field label="Key">
                        <TextInput value={e.key} onChange={v => onMapsChange(maps.map((x, idx) => idx === i ? { ...x, entries: (x.entries ?? []).map((en, j) => j === ei ? { ...en, key: v } : en) } : x))} placeholder="default" mono />
                      </Field>
                      <Field label="Match type">
                        <SelectInput value={e.keymatch} onChange={v => onMapsChange(maps.map((x, idx) => idx === i ? { ...x, entries: (x.entries ?? []).map((en, j) => j === ei ? { ...en, keymatch: v } : en) } : x))}
                          options={[{ value: 'exact', label: 'Exact' }, { value: 'regex', label: 'Regex' }, { value: 'iregex', label: 'iRegex' }]} />
                      </Field>
                      <Field label="Value">
                        <TextInput value={e.value} onChange={v => onMapsChange(maps.map((x, idx) => idx === i ? { ...x, entries: (x.entries ?? []).map((en, j) => j === ei ? { ...en, value: v } : en) } : x))} placeholder="/api/v1" mono />
                      </Field>
                      <div className="cf-agw-item-remove"><RemoveBtn onClick={() => onMapsChange(maps.map((x, idx) => idx === i ? { ...x, entries: (x.entries ?? []).filter((_, j) => j !== ei) } : x))} /></div>
                    </div>
                  ))
                }
              </div>
              <div className="cf-card-actions"><RemoveBtn onClick={() => onMapsChange(maps.filter((_, idx) => idx !== i))} /></div>
            </CollapseCard>
          ))
        }
      </div>

      {/* ── Log Formats ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Log Formats</span>
          <AddBtn label="Add format" onClick={() => onLogFormatsChange([...logformats, emptyHttpLogFormat()])} />
        </div>
        {logformats.length === 0
          ? <p className="cf-empty cf-empty-sm">No log formats. Add one to define custom NGINX access log formats.</p>
          : logformats.map((lf, i) => (
            <CollapseCard key={i} title={lf.name || <em>logformat #{i + 1}</em>} meta={lf.escape || undefined} defaultOpen={!lf.name}>
              <div className="cf-grid-2">
                <Field label="Name" required>
                  <TextInput value={lf.name}
                    onChange={v => onLogFormatsChange(logformats.map((x, idx) => idx === i ? { ...x, name: v } : x))}
                    placeholder="custom_json" />
                </Field>
                <Field label="Escape" hint='Escape mode for special characters in log values.'>
                  <SelectInput value={lf.escape}
                    onChange={v => onLogFormatsChange(logformats.map((x, idx) => idx === i ? { ...x, escape: v } : x))}
                    options={[{ value: 'default', label: 'default' }, { value: 'json', label: 'json' }, { value: 'none', label: 'none' }]} />
                </Field>
                <Field label="Format string" span="full" required hint='NGINX log format string. Use NGINX variables like $remote_addr, $request, $status, etc.'>
                  <textarea
                    className="cf-input cf-textarea-sm cf-mono"
                    rows={3}
                    value={lf.format}
                    onChange={e => onLogFormatsChange(logformats.map((x, idx) => idx === i ? { ...x, format: e.target.value } : x))}
                    placeholder='$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent'
                    spellCheck={false}
                  />
                </Field>
              </div>
              <div className="cf-card-actions"><RemoveBtn onClick={() => onLogFormatsChange(logformats.filter((_, idx) => idx !== i))} /></div>
            </CollapseCard>
          ))
        }
      </div>

      {/* ── NJS Profiles ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">NJS Profiles</span>
          <AddBtn label="Add profile" onClick={() => onNjsProfilesChange([...njsProfiles, emptyNjsFile()])} />
        </div>
        {njsProfiles.length === 0
          ? <p className="cf-empty cf-empty-sm">No NJS profiles. Add one to reference an NJS JavaScript file.</p>
          : njsProfiles.map((np, i) => (
            <CollapseCard key={i} title={np.name || <em>profile #{i + 1}</em>} defaultOpen={!np.name}>
              <div className="cf-grid-2">
                <Field label="Name" required hint="Profile name referenced by NJS hooks.">
                  <TextInput value={np.name}
                    onChange={v => onNjsProfilesChange(njsProfiles.map((x, idx) => idx === i ? { ...x, name: v } : x))}
                    placeholder="myProfile" />
                </Field>
                <Field label="File / URL" span="full" required hint="URL or path to the NJS JavaScript file.">
                  <TextInput value={np.file.content}
                    onChange={v => onNjsProfilesChange(njsProfiles.map((x, idx) => idx === i ? { ...x, file: { ...x.file, content: v } } : x))}
                    placeholder="https://example.com/myProfile.js" mono />
                </Field>
              </div>
              <div className="cf-card-actions"><RemoveBtn onClick={() => onNjsProfilesChange(njsProfiles.filter((_, idx) => idx !== i))} /></div>
            </CollapseCard>
          ))
        }
      </div>

      {/* ── HTTP-level NJS Hooks ── */}
      <NjsHooksServerEditor hooks={njs} onChange={onNjsChange} njsProfileNames={njsProfileNames} />

      {/* ── ACME Issuers ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">ACME Issuers</span>
          <AddBtn label="Add issuer" onClick={() => onAcmeIssuersChange([...acmeIssuers, emptyAcmeIssuer()])} />
        </div>
        {acmeIssuers.length === 0
          ? <p className="cf-empty cf-empty-sm">No ACME issuers. Add one to enable automatic certificate provisioning via Let's Encrypt or other ACME servers.</p>
          : acmeIssuers.map((ai, i) => (
            <CollapseCard key={i} title={ai.name || <em>issuer #{i + 1}</em>} meta={ai.uri || undefined} defaultOpen={!ai.name}>
              <div className="cf-grid-2">
                <Field label="Name" required>
                  <TextInput value={ai.name}
                    onChange={v => onAcmeIssuersChange(acmeIssuers.map((x, idx) => idx === i ? { ...x, name: v } : x))}
                    placeholder="lets-encrypt" />
                </Field>
                <Field label="ACME server URI" required hint="ACME directory URL, e.g. the Let's Encrypt production or staging endpoint.">
                  <TextInput value={ai.uri}
                    onChange={v => onAcmeIssuersChange(acmeIssuers.map((x, idx) => idx === i ? { ...x, uri: v } : x))}
                    placeholder="https://acme-v02.api.letsencrypt.org/directory" mono />
                </Field>
                <Field label="Account key" hint="Path or URL to the ACME account private key file.">
                  <TextInput value={ai.account_key ?? ''}
                    onChange={v => onAcmeIssuersChange(acmeIssuers.map((x, idx) => idx === i ? { ...x, account_key: v } : x))}
                    placeholder="/etc/nginx/acme/account.key" mono />
                </Field>
                <Field label="Contact email" hint="Email address for ACME account registration.">
                  <TextInput value={ai.contact ?? ''}
                    onChange={v => onAcmeIssuersChange(acmeIssuers.map((x, idx) => idx === i ? { ...x, contact: v } : x))}
                    placeholder="admin@example.com" />
                </Field>
                <Field label="State path" hint="Directory for ACME state and challenge files.">
                  <TextInput value={ai.state_path ?? ''}
                    onChange={v => onAcmeIssuersChange(acmeIssuers.map((x, idx) => idx === i ? { ...x, state_path: v } : x))}
                    placeholder="/etc/nginx/acme" mono />
                </Field>
                <Field label="Trusted CA certificate" hint="Path to trusted CA bundle for verifying the ACME server's TLS certificate.">
                  <TextInput value={ai.ssl_trusted_certificate ?? ''}
                    onChange={v => onAcmeIssuersChange(acmeIssuers.map((x, idx) => idx === i ? { ...x, ssl_trusted_certificate: v } : x))}
                    placeholder="/etc/ssl/ca-bundle.crt" mono />
                </Field>
                <Field label="SSL verify">
                  <Toggle checked={ai.ssl_verify ?? false} onChange={v => onAcmeIssuersChange(acmeIssuers.map((x, idx) => idx === i ? { ...x, ssl_verify: v } : x))} label={ai.ssl_verify ? 'Yes' : 'No'} />
                </Field>
                <Field label="Accept terms of service">
                  <Toggle checked={ai.accept_terms_of_service ?? false} onChange={v => onAcmeIssuersChange(acmeIssuers.map((x, idx) => idx === i ? { ...x, accept_terms_of_service: v } : x))} label={ai.accept_terms_of_service ? 'Accepted' : 'Not accepted'} />
                </Field>
              </div>
              <div className="cf-card-actions"><RemoveBtn onClick={() => onAcmeIssuersChange(acmeIssuers.filter((_, idx) => idx !== i))} /></div>
            </CollapseCard>
          ))
        }
      </div>

      {/* ── NGINX Plus API ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">NGINX Plus API</span>
          <Toggle checked={nginxPlusApi != null} onChange={v => onNginxPlusApiChange(v ? { write: false, listen: '127.0.0.1:8080', allow_acl: '127.0.0.1' } : undefined)} label={nginxPlusApi != null ? 'Enabled' : 'Disabled'} />
        </div>
        {nginxPlusApi != null && (
          <div className="cf-grid-2">
            <Field label="Listen address" hint='Address and port for the NGINX Plus API listener, e.g. "127.0.0.1:8080".'>
              <TextInput value={nginxPlusApi.listen ?? '127.0.0.1:8080'} onChange={v => onNginxPlusApiChange({ ...nginxPlusApi, listen: v })} placeholder="127.0.0.1:8080" mono />
            </Field>
            <Field label="Allow ACL" hint='CIDR or IP address allowed to access the API, e.g. "127.0.0.1".'>
              <TextInput value={nginxPlusApi.allow_acl ?? ''} onChange={v => onNginxPlusApiChange({ ...nginxPlusApi, allow_acl: v })} placeholder="127.0.0.1" mono />
            </Field>
            <Field label="Write access">
              <Toggle checked={nginxPlusApi.write ?? false} onChange={v => onNginxPlusApiChange({ ...nginxPlusApi, write: v })} label={nginxPlusApi.write ? 'Enabled' : 'Disabled'} />
            </Field>
          </div>
        )}
      </div>

      {/* ── Resolvers ── */}
      <div className="cf-subsection">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">Resolvers</span>
          <AddBtn label="Add resolver" onClick={() => onResolversChange([...resolvers, emptyHttpResolver()])} />
        </div>
        {resolvers.length === 0
          ? <p className="cf-empty cf-empty-sm">No resolvers. Add one to configure DNS resolver addresses for dynamic upstream resolution.</p>
          : resolvers.map((r, i) => (
            <CollapseCard key={i} title={r.name || <em>resolver #{i + 1}</em>} meta={r.address || undefined} defaultOpen={!r.name}>
              <div className="cf-grid-2">
                <Field label="Name" required hint="Profile name — referenced by server/upstream resolver fields.">
                  <TextInput value={r.name} onChange={v => onResolversChange(resolvers.map((x, idx) => idx === i ? { ...x, name: v } : x))} placeholder="my-resolver" />
                </Field>
                <Field label="Address" required hint='DNS server address and optional port, e.g. "8.8.8.8" or "1.1.1.1:53".'>
                  <TextInput value={r.address} onChange={v => onResolversChange(resolvers.map((x, idx) => idx === i ? { ...x, address: v } : x))} placeholder="8.8.8.8" mono />
                </Field>
                <Field label="Valid TTL" hint='Override DNS TTL for resolved addresses, e.g. "30s".'>
                  <TextInput value={r.valid ?? ''} onChange={v => onResolversChange(resolvers.map((x, idx) => idx === i ? { ...x, valid: v || undefined } : x))} placeholder="30s" mono />
                </Field>
                <Field label="Timeout" hint='Resolver response timeout, e.g. "5s".'>
                  <TextInput value={r.timeout ?? ''} onChange={v => onResolversChange(resolvers.map((x, idx) => idx === i ? { ...x, timeout: v || undefined } : x))} placeholder="5s" mono />
                </Field>
                <Field label="IPv4">
                  <Toggle checked={r.ipv4 ?? true} onChange={v => onResolversChange(resolvers.map((x, idx) => idx === i ? { ...x, ipv4: v } : x))} label={r.ipv4 ?? true ? 'Enabled' : 'Disabled'} />
                </Field>
                <Field label="IPv6">
                  <Toggle checked={r.ipv6 ?? true} onChange={v => onResolversChange(resolvers.map((x, idx) => idx === i ? { ...x, ipv6: v } : x))} label={r.ipv6 ?? true ? 'Enabled' : 'Disabled'} />
                </Field>
              </div>
              <div className="cf-card-actions"><RemoveBtn onClick={() => onResolversChange(resolvers.filter((_, idx) => idx !== i))} /></div>
            </CollapseCard>
          ))
        }
      </div>
    </div>
  );
}
