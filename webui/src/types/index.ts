// API types based on OpenAPI spec
export interface ConfigDeclaration {
  output?: {
    type?: 'nms' | 'nginxone';
    license?: LicenseConfig;
    nms?: NMSConfig;
    nginxone?: NginxOneConfig;
  };
  declaration?: {
    http?: HttpConfig;
    layer4?: Layer4Config;
    resolvers?: ResolverConfig[];
  };
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

export interface NMSConfig {
  url: string;
  username: string;
  password: string;
  instancegroup: string;
  synctime?: number;
  synchronous?: boolean;
  modules?: string[];
  certificates?: Certificate[];
  policies?: Policy[];
}

export interface NginxOneConfig {
  url: string;
  namespace: string;
  token: string;
  configsyncgroup: string;
  synctime?: number;
  synchronous?: boolean;
  modules?: string[];
  certificates?: Certificate[];
}

export interface Certificate {
  type: 'certificate' | 'key' | 'chain';
  name: string;
  contents: string;
}

export interface Policy {
  type: string;
  name: string;
  active_tag: string;
  versions: PolicyVersion[];
}

export interface PolicyVersion {
  tag: string;
  displayName: string;
  description: string;
  contents: string;
}

export interface HttpConfig {
  servers?: Record<string, unknown>[];
  upstreams?: Record<string, unknown>[];
  caching?: Record<string, unknown>[];
  rate_limit?: Record<string, unknown>[];
  maps?: Record<string, unknown>[];
  njs?: Record<string, unknown>[];
  njs_profiles?: Record<string, unknown>[];
  cache?: Record<string, unknown>[];
  logformats?: Record<string, unknown>[];
  authorization?: Record<string, unknown>[];
  authentication?: Record<string, unknown>;
  nginx_plus_api?: Record<string, unknown>;
  snippet?: Record<string, unknown>;
  acme_issuers?: Record<string, unknown>[];
  resolver?: string;
}

export interface Layer4Config {
  servers?: Record<string, unknown>[];
  upstreams?: Record<string, unknown>[];
}

export interface ResolverConfig {
  [key: string]: unknown;
}

export interface ConfigurationItem {
  configUid: string;
  declaration: ConfigDeclaration;
  createdAt: string;
  updatedAt: string;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface SubmissionStatus {
  configUid: string;
  submissionUid: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message?: string;
}
