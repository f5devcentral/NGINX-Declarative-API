import { useState } from 'react';
import type { TlsConfig } from './types';
import { Field, TextInput, Toggle } from './primitives';

export function TlsEditor({ tls, onChange }: {
  tls: TlsConfig | undefined;
  onChange: (t: TlsConfig | undefined) => void;
}) {
  const enabled = !!tls?.certificate || !!tls?.key;
  const [show, setShow] = useState(enabled);
  const t = tls ?? {};

  const handleEnable = (v: boolean) => {
    setShow(v);
    if (!v) onChange(undefined);
    else onChange({ certificate: '', key: '', protocols: ['TLSv1.2', 'TLSv1.3'] });
  };

  const TLS_PROTOCOL_OPTIONS = ['TLSv1.2', 'TLSv1.3', 'TLSv1.1'];
  const toggleProto = (p: string) => {
    const protos = t.protocols ?? [];
    onChange({ ...t, protocols: protos.includes(p) ? protos.filter(x => x !== p) : [...protos, p] });
  };

  return (
    <div className="cf-subsection cf-subsection-tls">
      <div className="cf-subsection-header">
        <span className="cf-subsection-title">TLS / SSL</span>
        <Toggle checked={show} onChange={handleEnable} label={show ? 'Enabled' : 'Disabled'} />
      </div>
      {show && (
        <div className="cf-grid-3">
          <Field label="Certificate" required hint="Name of the certificate object managed by NIM or NGINX One (not a file path).">
            <TextInput value={t.certificate ?? ''} onChange={v => onChange({ ...t, certificate: v })} placeholder="my-tls-cert" />
          </Field>
          <Field label="Private key" required hint="Name of the private key object matching the certificate above.">
            <TextInput value={t.key ?? ''} onChange={v => onChange({ ...t, key: v })} placeholder="my-tls-key" />
          </Field>
          <Field label="Protocols" hint="TLS protocol versions to accept. TLSv1.3 + TLSv1.2 is the recommended baseline.">
            <div className="cf-modules">
              {TLS_PROTOCOL_OPTIONS.map(p => (
                <label key={p} className="cf-toggle">
                  <input type="checkbox" checked={(t.protocols ?? []).includes(p)} onChange={() => toggleProto(p)} />
                  <span className="cf-toggle-text">{p}</span>
                </label>
              ))}
            </div>
          </Field>
          <Field label="Ciphers" hint='OpenSSL cipher list string, e.g. "HIGH:!aNULL:!MD5". Leave empty to use the NGINX default.'>
            <TextInput value={t.ciphers ?? ''} onChange={v => onChange({ ...t, ciphers: v || undefined })} placeholder="HIGH:!aNULL:!MD5" mono />
          </Field>
        </div>
      )}
    </div>
  );
}
