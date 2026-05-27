import type { ConfigData, NMSPolicy } from './types';
import {
  emptyNms, emptyNginxOne, emptyLicense, emptyNMSPolicy, emptyNMSPolicyVersion,
} from './defaults';
import { Field, TextInput, NumberInput, SelectInput, Toggle, AddBtn, RemoveBtn, CollapseCard, ModulesField } from './primitives';

export function PoliciesEditor({ policies, onChange, outputType }: {
  policies: NMSPolicy[];
  onChange: (p: NMSPolicy[]) => void;
  outputType?: 'nim' | 'n1c';
}) {
  const update = (i: number, p: NMSPolicy) => onChange(policies.map((x, idx) => idx === i ? p : x));
  const remove = (i: number) => onChange(policies.filter((_, idx) => idx !== i));

  const destination = outputType === 'n1c' ? 'NGINX One Console' : 'NGINX Instance Manager';
  const emptyMsg = `No policies — add one to manage an App Protect WAF policy in ${destination}.`;

  return (
    <div className="cf-subsection">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">Policies</span>
        <AddBtn label="Add policy" onClick={() => onChange([...policies, emptyNMSPolicy()])} />
      </div>
      {policies.length === 0 && (
        <p className="cf-empty">{emptyMsg}</p>
      )}
      {policies.map((pol, pi) => (
        <CollapseCard
          key={pi}
          title={pol.name || <em>policy #{pi + 1}</em>}
          meta={pol.type || undefined}
          defaultOpen={!pol.name}
        >
          <div className="cf-grid-2">
            <Field label="Type" required
              error={!pol.type ? 'Required' : undefined}>
              <SelectInput
                value={pol.type}
                onChange={v => update(pi, { ...pol, type: v })}
                options={[{ value: 'app_protect', label: 'App Protect' }]}
                error={!pol.type}
              />
            </Field>
            <Field label="Name" required
              error={!pol.name.trim() ? 'Required' : undefined}>
              <TextInput
                value={pol.name}
                onChange={v => update(pi, { ...pol, name: v })}
                placeholder="production-policy"
                error={!pol.name.trim()}
              />
            </Field>
            <Field label="Active tag" required
              hint="Tag of the currently active policy version. Must match one of the version tags below."
              error={!pol.active_tag.trim() ? 'Required' : undefined}>
              <TextInput
                value={pol.active_tag}
                onChange={v => update(pi, { ...pol, active_tag: v })}
                placeholder="xss-blocked"
                error={!pol.active_tag.trim()}
              />
            </Field>
          </div>

          <div className="cf-subsection">
            <div className="cf-subsection-header">
              <span className="cf-subsection-title">Versions</span>
              <AddBtn
                label="Add version"
                onClick={() => update(pi, { ...pol, versions: [...pol.versions, emptyNMSPolicyVersion()] })}
              />
            </div>
            {pol.versions.length === 0 && (
              <p className="cf-empty cf-empty-sm">No versions — add at least one version with a tag and policy content URL.</p>
            )}
            {pol.versions.map((ver, vi) => (
              <div key={vi} className="cf-agw-item-row">
                <Field label="Tag" required
                  hint='Unique identifier for this version, e.g. "xss-blocked".'
                  error={!ver.tag.trim() ? 'Required' : undefined}>
                  <TextInput
                    value={ver.tag}
                    onChange={v => update(pi, { ...pol, versions: pol.versions.map((vx, j) => j === vi ? { ...vx, tag: v } : vx) })}
                    placeholder="xss-blocked"
                    error={!ver.tag.trim()}
                  />
                </Field>
                <Field label="Display name"
                  hint="Human-readable name shown in NGINX Instance Manager.">
                  <TextInput
                    value={ver.displayName}
                    onChange={v => update(pi, { ...pol, versions: pol.versions.map((vx, j) => j === vi ? { ...vx, displayName: v } : vx) })}
                    placeholder="Production Policy - XSS blocked"
                  />
                </Field>
                <Field label="Description"
                  hint="Short description of this policy version.">
                  <TextInput
                    value={ver.description}
                    onChange={v => update(pi, { ...pol, versions: pol.versions.map((vx, j) => j === vi ? { ...vx, description: v } : vx) })}
                    placeholder="XSS attack protection enabled"
                  />
                </Field>
                <Field label="Content" span="full" required
                  hint='URL or path to the policy JSON file. Supports {{variable}} substitution.'
                  error={!ver.contents.content.trim() ? 'Required' : undefined}>
                  <TextInput
                    value={ver.contents.content}
                    onChange={v => update(pi, { ...pol, versions: pol.versions.map((vx, j) => j === vi ? { ...vx, contents: { content: v } } : vx) })}
                    placeholder="https://example.com/policy.json"
                    mono
                    error={!ver.contents.content.trim()}
                  />
                </Field>
                <div className="cf-agw-item-remove">
                  <RemoveBtn onClick={() => update(pi, { ...pol, versions: pol.versions.filter((_, j) => j !== vi) })} />
                </div>
              </div>
            ))}
          </div>

          <div className="cf-card-actions"><RemoveBtn onClick={() => remove(pi)} /></div>
        </CollapseCard>
      ))}
    </div>
  );
}

export function OutputSection({ output, onChange }: {
  output: ConfigData['output'];
  onChange: (o: ConfigData['output']) => void;
}) {
  const nms = output.nms ?? emptyNms();
  const no = output.nginxone ?? emptyNginxOne();
  const license = output.license;

  return (
    <section className="cf-section" id="cf-sec-output">

      <div className="cf-type-row">
        <button
          type="button"
          className={`cf-type-card${output.type === 'nim' ? ' active' : ''}`}
          onClick={() => onChange({ ...output, type: 'nim' })}
        >
          <span className="cf-type-card-title">NGINX Instance Manager</span>
          <span className="cf-type-card-sub">Push to an instance group</span>
        </button>
        <button
          type="button"
          className={`cf-type-card${output.type === 'n1c' ? ' active' : ''}`}
          onClick={() => onChange({ ...output, type: 'n1c' })}
        >
          <span className="cf-type-card-title">NGINX One Console</span>
          <span className="cf-type-card-sub">Push to a config sync group</span>
        </button>
      </div>

      {/* Synchronous toggle (applies to both output types) */}
      <div className="cf-field cf-field-inline">
        <Toggle
          checked={output.synchronous ?? true}
          onChange={v => onChange({ ...output, synchronous: v })}
          label="Synchronous push"
        />
        <p className="cf-hint">When enabled the API waits for NGINX to apply the configuration before responding.</p>
      </div>

      {/* License section */}
      <div className="cf-subsection cf-subsection-tls" id="cf-sec-license">
        <div className="cf-subsection-header">
          <span className="cf-subsection-title">License (NGINX Plus)</span>
          <Toggle checked={license != null} onChange={v => onChange({ ...output, license: v ? emptyLicense() : undefined })} label={license != null ? 'Configured' : 'Not configured'} />
        </div>
        {license != null && (
          <div className="cf-grid-2">
            <Field label="Endpoint" hint="License server endpoint URL.">
              <TextInput value={license.endpoint ?? 'product.connect.nginx.com'} onChange={v => onChange({ ...output, license: { ...license, endpoint: v } })} placeholder="product.connect.nginx.com" mono />
            </Field>
            <Field label="JWT token" hint="NGINX Plus license JWT. Paste the token content or upload a .jwt file.">
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <TextInput value={license.token ?? ''} onChange={v => onChange({ ...output, license: { ...license, token: v } })} placeholder="eyJ..." mono />
                <label className="cf-btn-add" style={{ cursor: 'pointer', whiteSpace: 'nowrap', margin: 0 }} title="Upload JWT file">
                  <span className="cf-btn-add-icon">↑</span> Upload
                  <input type="file" accept=".jwt,.txt,text/plain" style={{ display: 'none' }}
                    onChange={e => {
                      const f = e.target.files?.[0];
                      if (!f) return;
                      const reader = new FileReader();
                      reader.onload = ev => onChange({ ...output, license: { ...license, token: (ev.target?.result as string ?? '').trim() } });
                      reader.readAsText(f);
                      e.target.value = '';
                    }} />
                </label>
              </div>
            </Field>
            <Field label="Enforce initial report" hint='When enabled, enforces the initial license report to the licensing server. Controls the enforce_initial_report directive.'>
              <Toggle checked={license.grace_period ?? false} onChange={v => onChange({ ...output, license: { ...license, grace_period: v } })} label={license.grace_period ? 'Enabled' : 'Disabled'} />
            </Field>
            <Field label="SSL verify">
              <Toggle checked={license.ssl_verify ?? true} onChange={v => onChange({ ...output, license: { ...license, ssl_verify: v } })} label={license.ssl_verify ?? true ? 'Yes' : 'No'} />
            </Field>
            <Field label="Proxy URL" hint="HTTP proxy for license server connectivity.">
              <TextInput value={license.proxy ?? ''} onChange={v => onChange({ ...output, license: { ...license, proxy: v || undefined } })} placeholder="http://proxy.example.com:3128" mono />
            </Field>
            <Field label="Proxy username">
              <TextInput value={license.proxy_username ?? ''} onChange={v => onChange({ ...output, license: { ...license, proxy_username: v || undefined } })} placeholder="proxyuser" />
            </Field>
            <Field label="Proxy password">
              <TextInput value={license.proxy_password ?? ''} type="password" onChange={v => onChange({ ...output, license: { ...license, proxy_password: v || undefined } })} placeholder="••••••••" />
            </Field>
          </div>
        )}
      </div>

      {output.type === 'nim' && (
        <>
          <div className="cf-grid-2">
            <Field label="URL" required
              hint="Base URL of your NGINX Instance Manager instance. Include scheme and port. Example: https://nim.example.com:443">
              <TextInput value={nms.url} onChange={v => onChange({ ...output, nms: { ...nms, url: v } })} placeholder="https://nms.example.com" mono />
            </Field>
            <Field label="Username" required hint="API username for NGINX Instance Manager. Usually 'admin' for initial setup.">
              <TextInput value={nms.username} onChange={v => onChange({ ...output, nms: { ...nms, username: v } })} placeholder="admin" />
            </Field>
            <Field label="Password" required hint="Password for the NGINX Instance Manager API user. Stored only in your local session — never sent to this UI's server.">
              <TextInput value={nms.password} onChange={v => onChange({ ...output, nms: { ...nms, password: v } })} type="password" placeholder="••••••••" />
            </Field>
            <Field label="Instance group" required hint="Name of the NGINX Instance Manager instance group to push configuration to. The group must already exist.">
              <TextInput value={nms.instancegroup} onChange={v => onChange({ ...output, nms: { ...nms, instancegroup: v } })} placeholder="production" />
            </Field>
            <Field label="Sync time (seconds)"
              hint="How often (in seconds) the API will re-push the configuration. Set to 0 to push once and stop. Use a positive integer for continuous synchronisation.">
              <NumberInput value={nms.synctime ?? 0} onChange={v => onChange({ ...output, nms: { ...nms, synctime: v } })} />
            </Field>
            <Field label="Dynamic modules"
              hint="Select any additional NGINX dynamic modules that must be loaded. These are inserted as load_module directives at the top of nginx.conf.">
              <ModulesField value={nms.modules ?? []} onChange={v => onChange({ ...output, nms: { ...nms, modules: v } })} />
            </Field>
          </div>
        </>
      )}

      {output.type === 'n1c' && (
        <>
          <div className="cf-grid-2">
            <Field label="NGINX One URL" required
              hint="Base URL of your NGINX One Console instance. Example: https://nginx-one.example.com">
              <TextInput value={no.url} onChange={v => onChange({ ...output, nginxone: { ...no, url: v } })} placeholder="https://nginx-one.example.com" mono />
            </Field>
            <Field label="Namespace" required hint="The NGINX One namespace that contains your config sync group. Case-sensitive.">
              <TextInput value={no.namespace} onChange={v => onChange({ ...output, nginxone: { ...no, namespace: v } })} placeholder="default" />
            </Field>
            <Field label="API token" required hint="Bearer token for authenticating to the NGINX One API. Generate this in the NGINX One Console under API keys.">
              <TextInput value={no.token} onChange={v => onChange({ ...output, nginxone: { ...no, token: v } })} type="password" placeholder="••••••••" />
            </Field>
            <Field label="Config sync group" required hint="Name of the config sync group to target. Instances in this group will receive the generated configuration.">
              <TextInput value={no.configsyncgroup} onChange={v => onChange({ ...output, nginxone: { ...no, configsyncgroup: v } })} placeholder="production-group" />
            </Field>
            <Field label="Sync time (seconds)"
              hint="How often (in seconds) to re-push the configuration. Set to 0 to push once and stop.">
              <NumberInput value={no.synctime ?? 0} onChange={v => onChange({ ...output, nginxone: { ...no, synctime: v } })} />
            </Field>
            <Field label="Dynamic modules"
              hint="Select any additional NGINX dynamic modules required by this configuration.">
              <ModulesField value={no.modules ?? []} onChange={v => onChange({ ...output, nginxone: { ...no, modules: v } })} />
            </Field>
          </div>
        </>
      )}
    </section>
  );
}
