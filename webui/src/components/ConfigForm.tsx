import { useState, useEffect, useCallback } from 'react';
import './ConfigForm.css';
import type { ConfigData } from './configForm/types';
import { parseConfig, toJson, emptyNms, emptyNginxOne } from './configForm/defaults';
import { OutputSection } from './configForm/OutputSection';
import { HttpSection } from './configForm/HttpSection';
import { Layer4Section } from './configForm/Layer4Section';

const DEFAULT_CFG: ConfigData = {
  output: { type: 'nms', synchronous: true, nms: emptyNms(), nginxone: emptyNginxOne() },
  declaration: {
    http: { servers: [], upstreams: [], rate_limit: [], authentication: { client: [] }, authorization: [], cache: [], maps: [], logformats: [], njs: [], njs_profiles: [], acme_issuers: [] },
    layer4: { servers: [], upstreams: [] },
    resolvers: [],
  },
};

interface ConfigFormProps {
  initialJson: string;
  onChange: (json: string) => void;
}

function scrollToSection(id: string) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

interface NavItem {
  id: string;
  label: string;
  indent?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'cf-sec-output',         label: 'Output' },
  { id: 'cf-sec-license',        label: 'License',        indent: true },
  { id: 'cf-sec-policies',       label: 'Policies',       indent: true },
  { id: 'cf-sec-certificates',   label: 'Certificates',   indent: true },
  { id: 'cf-sec-log-profiles',   label: 'Log Profiles',   indent: true },
  { id: 'cf-sec-http',           label: 'HTTP' },
  { id: 'cf-sec-http-profiles',  label: 'Profiles',       indent: true },
  { id: 'cf-sec-http-servers',   label: 'Servers',        indent: true },
  { id: 'cf-sec-http-upstreams', label: 'Upstreams',      indent: true },
  { id: 'cf-sec-layer4',         label: 'Layer 4' },
];

export function ConfigForm({ initialJson, onChange }: ConfigFormProps) {
  const [cfg, setCfg] = useState<ConfigData>(() => parseConfig(initialJson) ?? DEFAULT_CFG);
  const [activeSection, setActiveSection] = useState('cf-sec-output');

  useEffect(() => {
    const parsed = parseConfig(initialJson);
    if (parsed) setCfg(parsed);
  }, [initialJson]);

  // Track active section via IntersectionObserver
  useEffect(() => {
    const ids = NAV_ITEMS.map(n => n.id);
    const observers: IntersectionObserver[] = [];
    const visible = new Set<string>();

    ids.forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      const obs = new IntersectionObserver(
        entries => {
          entries.forEach(e => {
            if (e.isIntersecting) visible.add(id); else visible.delete(id);
          });
          // Pick the topmost visible section
          const first = ids.find(i => visible.has(i));
          if (first) setActiveSection(first);
        },
        { rootMargin: '-10% 0px -80% 0px' }
      );
      obs.observe(el);
      observers.push(obs);
    });
    return () => observers.forEach(o => o.disconnect());
  }, []);

  const update = useCallback((next: ConfigData) => {
    setCfg(next);
    onChange(toJson(next));
  }, [onChange]);

  const http = cfg.declaration.http ?? {};

  return (
    <div className="cf-layout">
      <nav className="cf-sidenav">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            type="button"
            className={`cf-sidenav-item${item.indent ? ' indent' : ''}${activeSection === item.id ? ' active' : ''}`}
            onClick={() => scrollToSection(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div className="config-form">
        <OutputSection output={cfg.output} onChange={o => update({ ...cfg, output: o })} />
        <HttpSection
          http={http}
          onChange={h => update({ ...cfg, declaration: { ...cfg.declaration, http: h } })}
          resolvers={cfg.declaration.resolvers ?? []}
          onResolversChange={v => update({ ...cfg, declaration: { ...cfg.declaration, resolvers: v } })}
        />
        <Layer4Section
          servers={cfg.declaration.layer4?.servers}
          onServersChange={s => update({ ...cfg, declaration: { ...cfg.declaration, layer4: { ...cfg.declaration.layer4, servers: s } } })}
          upstreams={cfg.declaration.layer4?.upstreams}
          onUpstreamsChange={u => update({ ...cfg, declaration: { ...cfg.declaration, layer4: { ...cfg.declaration.layer4, upstreams: u } } })}
        />
      </div>
    </div>
  );
}
