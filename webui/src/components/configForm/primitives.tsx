import { useState, type ReactNode } from 'react';
import type { HttpProfiles } from './types';

export function Field({
  label, required, hint, error, children, span,
}: {
  label: string; required?: boolean; hint?: string; error?: string; children: ReactNode; span?: 'full';
}) {
  return (
    <div className={`cf-field${span === 'full' ? ' cf-field-full' : ''}`}>
      <label className="cf-label">
        {label}{required && <span className="cf-required">*</span>}
      </label>
      {children}
      {error && <p className="cf-field-error">{error}</p>}
      {!error && hint && <p className="cf-hint">{hint}</p>}
    </div>
  );
}

export function TextInput({
  value, onChange, placeholder, type = 'text', mono, error,
}: {
  value: string; onChange: (v: string) => void; placeholder?: string; type?: string; mono?: boolean; error?: boolean;
}) {
  return (
    <input
      className={`cf-input${mono ? ' cf-mono' : ''}${error ? ' cf-input-error' : ''}`}
      type={type}
      value={value}
      placeholder={placeholder}
      autoComplete="off"
      spellCheck={false}
      onChange={e => onChange(e.target.value)}
    />
  );
}

export function NumberInput({ value, onChange, min = 0 }: { value: number; onChange: (v: number) => void; min?: number }) {
  return (
    <input
      className="cf-input cf-input-sm"
      type="number"
      value={value}
      min={min}
      onChange={e => onChange(Number(e.target.value))}
    />
  );
}

export function SelectInput({ value, onChange, options, error }: {
  value: string; onChange: (v: string) => void;
  options: { value: string; label: string }[];
  error?: boolean;
}) {
  return (
    <select className={`cf-input${error ? ' cf-input-error' : ''}`} value={value} onChange={e => onChange(e.target.value)}>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

export function ProfileSelect({ value, onChange, options, error }: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  placeholder?: string;
  error?: boolean;
}) {
  const isEmpty = options.length === 0;
  return (
    <select
      className={`cf-input cf-input-mono${error ? ' cf-input-error' : ''}`}
      value={value}
      onChange={e => onChange(e.target.value)}
      disabled={isEmpty}
      title={isEmpty ? 'Define profiles in the HTTP section first' : undefined}
    >
      {isEmpty
        ? <option value="">— no profiles defined —</option>
        : <>
            <option value="">— select profile —</option>
            {options.map(n => <option key={n} value={n}>{n}</option>)}
          </>
      }
    </select>
  );
}

export function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="cf-toggle">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
      <span className="cf-toggle-text">{label}</span>
    </label>
  );
}

export const MODULES = [
  { value: 'ngx_http_app_protect_module', label: 'NGINX App Protect WAF' },
  { value: 'ngx_http_js_module',          label: 'NGINX JavaScript (njs) — HTTP' },
  { value: 'ngx_stream_js_module',        label: 'NGINX JavaScript (njs) — Stream' },
  { value: 'ngx_http_geoip2_module',      label: 'GeoIP2' },
];

export function ModulesField({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  const toggle = (mod: string) =>
    onChange(value.includes(mod) ? value.filter(m => m !== mod) : [...value, mod]);
  return (
    <div className="cf-modules">
      {MODULES.map(m => (
        <label key={m.value} className="cf-toggle">
          <input type="checkbox" checked={value.includes(m.value)} onChange={() => toggle(m.value)} />
          <span className="cf-toggle-text">{m.label}</span>
        </label>
      ))}
    </div>
  );
}

export function SectionTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="cf-section-head">
      <div className="cf-section-text">
        <span className="cf-section-title">{title}</span>
        {sub && <span className="cf-section-sub">{sub}</span>}
      </div>
    </div>
  );
}

export function AddBtn({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" className="cf-btn-add" onClick={onClick}>
      <span className="cf-btn-add-icon">+</span> {label}
    </button>
  );
}

export function RemoveBtn({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className="cf-btn-remove" title="Remove" onClick={onClick}>
      ✕
    </button>
  );
}

export function CollapseCard({
  title, meta, children, defaultOpen,
}: {
  title: ReactNode; meta?: string; children: ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  return (
    <div className={`cf-card${open ? ' cf-card-open' : ''}`}>
      <div className="cf-card-header" onClick={() => setOpen(o => !o)}>
        <span className="cf-card-caret">{open ? '▾' : '▸'}</span>
        <span className="cf-card-title">{title}</span>
        {meta && <span className="cf-card-meta">{meta}</span>}
      </div>
      {open && <div className="cf-card-body">{children}</div>}
    </div>
  );
}

// Re-export HttpProfiles so consumers can import it from primitives if needed
export type { HttpProfiles };
