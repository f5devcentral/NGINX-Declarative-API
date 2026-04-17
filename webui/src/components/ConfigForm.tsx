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

export function ConfigForm({ initialJson, onChange }: ConfigFormProps) {
  const [cfg, setCfg] = useState<ConfigData>(() => parseConfig(initialJson) ?? DEFAULT_CFG);

  useEffect(() => {
    const parsed = parseConfig(initialJson);
    if (parsed) setCfg(parsed);
  }, [initialJson]);

  const update = useCallback((next: ConfigData) => {
    setCfg(next);
    onChange(toJson(next));
  }, [onChange]);

  const http = cfg.declaration.http ?? {};

  return (
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
  );
}
