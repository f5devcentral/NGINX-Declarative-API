import type {
  OutputNMS, OutputNGINXOne, LicenseConfig, Server, Location, Upstream, Origin,
  NMSCertificate, LogProfile, HttpMap, MapEntry, HttpLogFormat, HttpResolver,
  NjsFile, AcmeIssuer, NjsHookServer, NjsHookLocation, HttpAuthServer,
  AGWRateLimit, AGWAuthorization, AGWCache, AGWVisibility,
  NMSPolicyVersion, NMSPolicy, HttpRateLimit, HttpAuthClient, HttpAuthzJwtClaim,
  HttpAuthorization, HttpCache, ConfigData,
} from './types';

export const emptyNms = (): OutputNMS => ({
  url: '', username: '', password: '', instancegroup: '', synctime: 0, modules: [],
});

export const emptyNginxOne = (): OutputNGINXOne => ({
  url: '', namespace: '', token: '', configsyncgroup: '', synctime: 0, modules: [],
});

export const emptyLicense = (): LicenseConfig => ({
  endpoint: 'product.connect.nginx.com', token: '', ssl_verify: true,
  proxy: '', proxy_username: '', proxy_password: '',
});

export const emptyServer = (): Server => ({
  name: '', names: [], listen: { address: '', http2: false }, locations: [],
});

export const emptyLocation = (): Location => ({ uri: '/', urimatch: 'prefix', upstream: '' });

export const emptyUpstream = (): Upstream => ({ name: '', origin: [{ server: '', weight: 1 }] });

export const emptyOrigin = (): Origin => ({ server: '', weight: 1, max_fails: 1, fail_timeout: '10s', max_conns: 0, slow_start: '0' });

export const emptyCertificate = (): NMSCertificate => ({ type: 'certificate', name: '', contents: { content: '' } });

export const emptyLogProfile = (): LogProfile => ({ type: 'app_protect', app_protect: { name: '', format: 'default', type: 'blocked', max_request_size: 'any', max_message_size: '5k' } });

export const emptyHttpMap = (): HttpMap => ({ match: '', variable: '', entries: [] });

export const emptyMapEntry = (): MapEntry => ({ key: '', keymatch: 'exact', value: '' });

export const emptyHttpLogFormat = (): HttpLogFormat => ({ name: '', escape: 'default', format: '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent' });

export const emptyHttpResolver = (): HttpResolver => ({ name: '', address: '', valid: '', ipv4: true, ipv6: true, timeout: '30s' });

export const emptyNjsFile = (): NjsFile => ({ name: '', file: { content: '' } });

export const emptyAcmeIssuer = (): AcmeIssuer => ({ name: '', uri: 'https://acme-v02.api.letsencrypt.org/directory', accept_terms_of_service: false, ssl_verify: false });

export const emptyNjsHookServer = (): NjsHookServer => ({ hook: { type: 'js_set', js_set: { variable: '' } }, profile: '', function: '' });

export const emptyNjsHookLocation = (): NjsHookLocation => ({ hook: { type: 'js_content' }, profile: '', function: '' });

export const emptyHttpAuthServerToken = (): HttpAuthServer => ({ name: '', type: 'token', token: { token: '', type: 'bearer', location: '', username: '', password: '' } });

export const emptyHttpAuthServerMtls = (): HttpAuthServer => ({ name: '', type: 'mtls', mtls: { certificate: '', key: '' } });

export const emptyAGWRateLimit = (): AGWRateLimit => ({
  profile: '', httpcode: 429, burst: 0, delay: 0, enforceOnPaths: true, paths: [],
});

export const emptyAGWAuthorization = (): AGWAuthorization => ({
  profile: '', enforceOnPaths: true, paths: [],
});

export const emptyAGWCache = (): AGWCache => ({
  profile: '', key: '$scheme$proxy_host$request_uri', validity: [], enforceOnPaths: true, paths: [],
});

export const emptyAGWVisibility = (): AGWVisibility => ({
  enabled: true, type: 'moesif',
  moesif: { application_id: '', plugin_path: '/usr/local/share/lua/5.1/resty/moesif' },
});

export const emptyNMSPolicyVersion = (): NMSPolicyVersion => ({
  tag: '', displayName: '', description: '', contents: { content: '' },
});

export const emptyNMSPolicy = (): NMSPolicy => ({
  type: 'app_protect', name: '', active_tag: '', versions: [],
});

export const emptyHttpRateLimit = (): HttpRateLimit => ({ name: '', key: '$binary_remote_addr', size: '10m', rate: '10r/s' });

export const emptyHttpAuthClient = (): HttpAuthClient => ({ name: '', type: 'jwt', jwt: { realm: '', key: '', jwt_type: 'signed', cachetime: 0, token_location: '' } });

export const emptyHttpAuthzClaim = (): HttpAuthzJwtClaim => ({ name: '', value: [], errorcode: 403 });

export const emptyHttpAuthorization = (): HttpAuthorization => ({ name: '', type: 'jwt', jwt: { claims: [] } });

export const emptyHttpCache = (): HttpCache => ({ name: '', basepath: '/tmp', size: '10m', ttl: '10m' });

export function parseConfig(json: string): ConfigData | null {
  try {
    const p = JSON.parse(json);
    return {
      output: {
        type: p?.output?.type ?? 'nms',
        synchronous: p?.output?.synchronous ?? true,
        license: p?.output?.license ?? undefined,
        nms: { ...emptyNms(), ...(p?.output?.nms ?? {}) },
        nginxone: { ...emptyNginxOne(), ...(p?.output?.nginxone ?? {}) },
      },
      declaration: {
        certificates: p?.declaration?.certificates ?? [],
        http: {
          servers: p?.declaration?.http?.servers ?? [],
          upstreams: p?.declaration?.http?.upstreams ?? [],
          rate_limit: p?.declaration?.http?.rate_limit ?? [],
          authentication: p?.declaration?.http?.authentication ?? { client: [] },
          authorization: p?.declaration?.http?.authorization ?? [],
          cache: p?.declaration?.http?.cache ?? [],
          maps: p?.declaration?.http?.maps ?? [],
          logformats: p?.declaration?.http?.logformats ?? [],
          njs: p?.declaration?.http?.njs ?? [],
          njs_profiles: p?.declaration?.http?.njs_profiles ?? [],
          acme_issuers: p?.declaration?.http?.acme_issuers ?? [],
          nginx_plus_api: p?.declaration?.http?.nginx_plus_api ?? undefined,
          policies: p?.declaration?.http?.policies ?? [],
          log_profiles: p?.declaration?.http?.log_profiles ?? [],
        },
        layer4: {
          servers: p?.declaration?.layer4?.servers ?? [],
          upstreams: p?.declaration?.layer4?.upstreams ?? [],
        },
        resolvers: p?.declaration?.resolvers ?? [],
      },
    };
  } catch {
    return null;
  }
}

export function toJson(cfg: ConfigData): string {
  const out: Record<string, unknown> = { type: cfg.output.type, synchronous: cfg.output.synchronous ?? true };
  if (cfg.output.license) out.license = cfg.output.license;
  if (cfg.output.type === 'nms') out.nms = cfg.output.nms;
  else out.nginxone = cfg.output.nginxone;

  const decl: Record<string, unknown> = {};
  if (cfg.declaration.certificates?.length) {
    decl.certificates = cfg.declaration.certificates;
  }
  const http = cfg.declaration.http;
  const httpHasContent = (
    (http?.servers?.length ?? 0) +
    (http?.upstreams?.length ?? 0) +
    (http?.rate_limit?.length ?? 0) +
    (http?.authentication?.client?.length ?? 0) +
    (http?.authorization?.length ?? 0) +
    (http?.cache?.length ?? 0) +
    (http?.maps?.length ?? 0) +
    (http?.logformats?.length ?? 0) +
    (http?.njs?.length ?? 0) +
    (http?.njs_profiles?.length ?? 0) +
    (http?.acme_issuers?.length ?? 0) +
    (http?.nginx_plus_api ? 1 : 0) +
    (http?.policies?.length ?? 0) +
    (http?.log_profiles?.length ?? 0)
  ) > 0;
  if (httpHasContent) {
    decl.http = {
      ...(http?.rate_limit?.length           ? { rate_limit:     http.rate_limit }     : {}),
      ...(http?.authentication?.client?.length || http?.authentication?.server?.length ? { authentication: http.authentication } : {}),
      ...(http?.authorization?.length        ? { authorization:  http.authorization }  : {}),
      ...(http?.cache?.length                ? { cache:          http.cache }          : {}),
      ...(http?.maps?.length                 ? { maps:           http.maps }           : {}),
      ...(http?.logformats?.length           ? { logformats:     http.logformats }     : {}),
      ...(http?.njs?.length                  ? { njs:            http.njs }            : {}),
      ...(http?.njs_profiles?.length         ? { njs_profiles:   http.njs_profiles }   : {}),
      ...(http?.acme_issuers?.length         ? { acme_issuers:   http.acme_issuers }   : {}),
      ...(http?.nginx_plus_api               ? { nginx_plus_api: http.nginx_plus_api } : {}),
      ...(http?.policies?.length             ? { policies:       http.policies }       : {}),
      ...(http?.log_profiles?.length         ? { log_profiles:   http.log_profiles }   : {}),
      ...(http?.servers?.length              ? { servers:        http.servers }        : {}),
      ...(http?.upstreams?.length            ? { upstreams:      http.upstreams }      : {}),
    };
  }
  const l4 = cfg.declaration.layer4;
  if ((l4?.servers?.length ?? 0) + (l4?.upstreams?.length ?? 0) > 0) {
    decl.layer4 = {
      ...(l4?.servers?.length ? { servers: l4.servers } : {}),
      ...(l4?.upstreams?.length ? { upstreams: l4.upstreams } : {}),
    };
  }
  if (cfg.declaration.resolvers?.length) {
    decl.resolvers = cfg.declaration.resolvers;
  }

  return JSON.stringify({ output: out, declaration: decl }, null, 2);
}
