// ─── Domain interfaces for NGINX Declarative API ConfigForm ──────────────────

export interface Origin {
  server: string;
  weight?: number;
  max_fails?: number;
  fail_timeout?: string;
  max_conns?: number;
  slow_start?: string;
  backup?: boolean;
}

export interface Sticky {
  cookie: string;
  expires?: string;
  domain?: string;
  path?: string;
}

export interface SourceOfTruth {
  content: string;
  authentication?: Array<{ profile?: string }>;
}

export interface HTTPHeader {
  name: string;
  value: string;
}

export interface LocationHeaderToClient {
  add?: HTTPHeader[];
  delete?: string[];
  replace?: HTTPHeader[];
}

export interface LocationHeaderToServer {
  set?: HTTPHeader[];
  delete?: string[];
}

export interface LocationHeaders {
  to_server?: LocationHeaderToServer;
  to_client?: LocationHeaderToClient;
}

export interface LogAccess {
  destination: string;
  format?: string;
  condition?: string;
}

export interface LogError {
  destination: string;
  level?: string;
}

export interface Log {
  access?: LogAccess;
  error?: LogError;
}

export interface AppProtectLog {
  enabled?: boolean;
  profile_name?: string;
  destination?: string;
}

export interface AppProtect {
  enabled?: boolean;
  policy: string;
  log?: AppProtectLog;
}

export interface HealthCheck {
  enabled?: boolean;
  uri?: string;
  interval?: number;
  fails?: number;
  passes?: number;
}

export interface CacheItem {
  profile?: string;
  key?: string;
  validity?: Array<{ code?: string; ttl?: string }>;
}

export interface RateLimitRef {
  profile?: string;
  httpcode?: number;
  burst?: number;
  delay?: number;
}

export interface LocationAuthEntry {
  profile?: string;
}

export interface LocationAuth {
  client?: LocationAuthEntry[];
  server?: LocationAuthEntry[];
}

export interface AuthzRef {
  profile?: string;
}

export interface NjsHookDetails {
  type: string;
  js_body_filter?: { buffer_type?: string };
  js_periodic?: { interval?: string; jitter?: number; worker_affinity?: string };
  js_preload_object?: { file: string };
  js_set?: { variable: string };
}

export interface NjsHookLocation {
  hook: NjsHookDetails;
  profile: string;
  function: string;
}

export interface NjsHookServer {
  hook: { type: string; js_preload_object?: { file: string }; js_set?: { variable: string } };
  profile: string;
  function: string;
}

export interface Location {
  uri: string;
  urimatch?: string;
  upstream?: string;
  apigateway?: APIGateway;
  log?: Log;
  caching?: string;
  rate_limit?: RateLimitRef;
  health_check?: HealthCheck;
  app_protect?: AppProtect;
  snippet?: SourceOfTruth;
  authentication?: LocationAuth;
  authorization?: AuthzRef;
  headers?: LocationHeaders;
  njs?: NjsHookLocation[];
  cache?: CacheItem;
}

export interface AGWOpenAPISchema {
  content?: string;
}

export interface AGWApiGateway {
  enabled?: boolean;
  strip_uri?: boolean;
  server_url?: string;
}

export interface DevPortalRedocly {
  uri?: string;
}

export interface DevPortalBackstage {
  name?: string;
  lifecycle?: string;
  owner?: string;
  system?: string;
}

export interface AGWDeveloperPortal {
  enabled?: boolean;
  type?: string;
  redocly?: DevPortalRedocly;
  backstage?: DevPortalBackstage;
}

export interface AGWVisibilityMoesif {
  application_id?: string;
  plugin_path?: string;
}

export interface AGWVisibility {
  enabled?: boolean;
  type?: string;
  moesif?: AGWVisibilityMoesif;
}

export interface AGWRateLimit {
  profile?: string;
  httpcode?: number;
  burst?: number;
  delay?: number;
  enforceOnPaths?: boolean;
  paths?: string[];
}

export interface AGWAuthClient {
  profile?: string;
}

export interface AGWAuthentication {
  client?: AGWAuthClient[];
  enforceOnPaths?: boolean;
  paths?: string[];
}

export interface AGWAuthorization {
  profile: string;
  enforceOnPaths?: boolean;
  paths?: string[];
}

export interface AGWCacheTTL {
  code?: string;
  ttl?: string;
}

export interface AGWCache {
  profile: string;
  key?: string;
  validity?: AGWCacheTTL[];
  enforceOnPaths?: boolean;
  paths?: string[];
}

export interface APIGateway {
  openapi_schema?: AGWOpenAPISchema;
  api_gateway?: AGWApiGateway;
  developer_portal?: AGWDeveloperPortal;
  visibility?: AGWVisibility[];
  rate_limit?: AGWRateLimit[];
  authentication?: AGWAuthentication;
  authorization?: AGWAuthorization[];
  cache?: AGWCache[];
}

export interface TlsConfig {
  certificate?: string;
  key?: string;
  acme_issuer?: string;
  ciphers?: string;
  protocols?: string[];
}

export interface Server {
  name: string;
  names?: string[];
  resolver?: string;
  listen?: { address?: string; http2?: boolean; tls?: TlsConfig };
  log?: Log;
  locations?: Location[];
  app_protect?: AppProtect;
  snippet?: SourceOfTruth;
  headers?: LocationHeaders;
  njs?: NjsHookServer[];
  authentication?: LocationAuth;
  authorization?: AuthzRef;
  cache?: CacheItem;
}

export interface Upstream {
  name: string;
  origin: Origin[];
  resolver?: string;
  sticky?: Sticky;
  snippet?: SourceOfTruth;
}

// ─── HTTP-level profile interfaces ────────────────────────────────────────────

export interface HttpRateLimit {
  name: string;
  key: string;
  size: string;
  rate: string;
}

export interface HttpAuthJwt {
  realm: string;
  key: string;
  cachetime?: number;
  jwt_type?: string;
  token_location?: string;
}

export interface HttpAuthMtls {
  enabled?: string;
  client_certificates: string;
  trusted_ca_certificates?: string;
}

export interface HttpAuthOidc {
  issuer: string;
  client_id: string;
  client_secret: string;
  config_url?: string;
  redirect_uri?: string;
  scope?: string;
  session_timeout?: string;
}

export interface HttpAuthClient {
  name: string;
  type: string;
  jwt?: HttpAuthJwt;
  mtls?: HttpAuthMtls;
  oidc?: HttpAuthOidc;
}

export interface HttpAuthServerToken {
  token: string;
  type?: string;
  location?: string;
  username?: string;
  password?: string;
}

export interface HttpAuthServerMtls {
  certificate: string;
  key: string;
}

export interface HttpAuthServer {
  name: string;
  type: string;
  token?: HttpAuthServerToken;
  mtls?: HttpAuthServerMtls;
}

export interface HttpAuthentication {
  client: HttpAuthClient[];
  server?: HttpAuthServer[];
}

export interface HttpAuthzJwtClaim {
  name: string;
  value: string[];
  errorcode?: number;
}

export interface HttpAuthzJwt {
  claims: HttpAuthzJwtClaim[];
}

export interface HttpAuthorization {
  name: string;
  type: string;
  jwt?: HttpAuthzJwt;
}

export interface HttpCache {
  name: string;
  basepath: string;
  size: string;
  ttl: string;
  max_size?: string;
  min_free?: string;
}

export interface MapEntry {
  key: string;
  keymatch: string;
  value: string;
}

export interface HttpMap {
  match: string;
  variable: string;
  entries?: MapEntry[];
}

export interface HttpLogFormat {
  name: string;
  escape: string;
  format: string;
}

export interface HttpResolver {
  name: string;
  address: string;
  valid?: string;
  ipv4?: boolean;
  ipv6?: boolean;
  timeout?: string;
}

export interface NginxPlusApi {
  write?: boolean;
  listen?: string;
  allow_acl?: string;
}

export interface NjsFile {
  name: string;
  file: SourceOfTruth;
}

export interface AcmeIssuer {
  name: string;
  uri: string;
  account_key?: string;
  contact?: string;
  ssl_trusted_certificate?: string;
  ssl_verify?: boolean;
  state_path?: string;
  accept_terms_of_service?: boolean;
}

export interface AppProtectLogProfile {
  name: string;
  format?: string;
  format_string?: string;
  type?: string;
  max_request_size?: string;
  max_message_size?: string;
}

export interface LogProfile {
  type: string;
  app_protect?: AppProtectLogProfile;
}

export interface NMSCertificate {
  type: 'certificate' | 'key';
  name: string;
  contents?: SourceOfTruth;
}

export interface LicenseConfig {
  endpoint?: string;
  token?: string;
  ssl_verify?: boolean;
  grace_period?: boolean;
  proxy?: string;
  proxy_username?: string;
  proxy_password?: string;
}

export interface NMSPolicyContents {
  content: string;
}

export interface NMSPolicyVersion {
  tag: string;
  displayName: string;
  description: string;
  contents: NMSPolicyContents;
}

export interface NMSPolicy {
  type: string;
  name: string;
  active_tag: string;
  versions: NMSPolicyVersion[];
}

export interface OutputNMS {
  url: string;
  username: string;
  password: string;
  instancegroup: string;
  synctime?: number;
  modules?: string[];
}

export interface OutputNGINXOne {
  url: string;
  namespace: string;
  token: string;
  configsyncgroup: string;
  synctime?: number;
  modules?: string[];
}

export interface ConfigData {
  output: {
    type: 'nim' | 'n1c';
    synchronous?: boolean;
    license?: LicenseConfig;
    nms?: OutputNMS;
    nginxone?: OutputNGINXOne;
  };
  declaration: {
    certificates?: NMSCertificate[];
    http?: {
      servers?: Server[];
      upstreams?: Upstream[];
      rate_limit?: HttpRateLimit[];
      authentication?: HttpAuthentication;
      authorization?: HttpAuthorization[];
      cache?: HttpCache[];
      maps?: HttpMap[];
      logformats?: HttpLogFormat[];
      njs?: NjsHookServer[];
      njs_profiles?: NjsFile[];
      acme_issuers?: AcmeIssuer[];
      nginx_plus_api?: NginxPlusApi;
      policies?: NMSPolicy[];
      log_profiles?: LogProfile[];
    };
    layer4?: {
      servers?: Array<{ name: string; resolver?: string; listen?: { address?: string }; upstream?: string; snippet?: SourceOfTruth }>;
      upstreams?: Array<{ name: string; resolver?: string; origin?: Array<{ server: string; weight?: number; max_fails?: number; fail_timeout?: string; backup?: boolean }>; snippet?: SourceOfTruth }>;
    };
    resolvers?: HttpResolver[];
  };
}

export interface HttpProfiles {
  rateLimitNames: string[];
  authClientNames: string[];
  authServerNames: string[];
  authzNames: string[];
  cacheNames: string[];
}
