import { useState, useCallback } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
import { Layout } from '@/components/Layout';
import { Copy, Check, Code2, LayoutList, Download } from 'lucide-react';
import type { ConfigDeclaration } from '@/types';
import toast from 'react-hot-toast';
import { ConfigForm } from '@/components/ConfigForm';
import './CreateConfigPage.css';


const nimTemplate: ConfigDeclaration = {
  output: {
    type: 'nms',
    nms: {
      url: 'https://nginx-instance-manager.example.com',
      username: 'admin',
      password: 'your-password',
      instancegroup: 'production',
      synctime: 0,
      modules: ['ngx_http_app_protect_module', 'ngx_http_js_module']
    }
  },
  declaration: {
    http: {
      servers: [
        {
          name: 'example-server',
          names: ['example.com', 'www.example.com'],
          listen: {
            address: '0.0.0.0:80'
          },
          locations: [
            {
              uri: '/',
              upstream: 'http://backend'
            }
          ]
        }
      ],
      upstreams: [
        {
          name: 'backend',
          origin: [
            { server: '10.0.0.10:8080' },
            { server: '10.0.0.11:8080' }
          ]
        }
      ]
    }
  }
};

const nginxOneTemplate: ConfigDeclaration = {
  output: {
    type: 'nginxone',
    nginxone: {
      url: 'https://nginx-one.example.com',
      namespace: 'default',
      token: 'your-api-token',
      configsyncgroup: 'production-group',
      synctime: 0,
      modules: ['ngx_http_app_protect_module']
    }
  },
  declaration: {
    http: {
      servers: [
        {
          name: 'api-server',
          names: ['api.example.com'],
          listen: {
            address: '0.0.0.0:443',
            tls: {
              certificate: 'server-cert',
              key: 'server-key'
            }
          },
          locations: [
            {
              uri: '/api',
              upstream: 'http://api-backend'
            }
          ]
        }
      ],
      upstreams: [
        {
          name: 'api-backend',
          origin: [
            { server: 'api-server-1.internal:8080' },
            { server: 'api-server-2.internal:8080' }
          ]
        }
      ]
    }
  }
};

const apiGatewayTemplate: ConfigDeclaration = {
  output: {
    type: 'nms',
    nms: {
      url: 'https://nginx-instance-manager.example.com',
      username: 'admin',
      password: 'your-password',
      instancegroup: 'api-gateway',
      synctime: 0
    }
  },
  declaration: {
    http: {
      servers: [
        {
          name: 'api-gateway-server',
          names: ['gateway.example.com'],
          listen: {
            address: '0.0.0.0:80',
            http2: false
          },
          locations: [
            {
              uri: '/_docs',
              urimatch: 'exact',
              apigateway: {
                developer_portal: {
                  enabled: true,
                  type: 'redocly',
                  redocly: {
                    uri: '/devportal.html'
                  }
                }
              }
            },
            {
              uri: '/api',
              upstream: 'http://api-backend',
              apigateway: {
                openapi_schema: {
                  content: ''
                },
                api_gateway: {
                  enabled: true,
                  server_url: 'http://api-backend'
                }
              }
            }
          ]
        }
      ],
      upstreams: [
        {
          name: 'api-backend',
          origin: [
            { server: 'api-server.internal:8080' }
          ]
        }
      ]
    }
  }
};

type EditorMode = 'json' | 'form';

export const CreateConfigPage = () => {
  const [jsonValue, setJsonValue] = useState('');
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState<EditorMode>('form');
  const [isDirty, setIsDirty] = useState(false);
  const [confirmPending, setConfirmPending] = useState<ConfigDeclaration | null>(null);

  const handleEditorMount: OnMount = useCallback(async (_editor, monaco) => {
    try {
      const res = await fetch('/v5.5/schema');
      if (res.ok) {
        const schema = await res.json();
        monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
          validate: true,
          allowComments: false,
          schemas: [{
            uri: 'https://nginx-dapi/config-declaration.json',
            fileMatch: ['nginx-dapi-config.json'],
            schema,
          }],
        });
      }
    } catch {
      // Schema IntelliSense unavailable; editor still works
    }
  }, []);

  const handleCopy = async () => {
    if (!jsonValue.trim()) {
      toast.error('Nothing to copy — build or paste a configuration first');
      return;
    }
    try {
      JSON.parse(jsonValue); // validate JSON before copying
      await navigator.clipboard.writeText(jsonValue);
      setCopied(true);
      toast.success('Configuration copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      if (error instanceof SyntaxError) {
        toast.error('Invalid JSON: ' + error.message);
      } else {
        toast.error('Failed to copy to clipboard');
      }
    }
  };

  const loadTemplate = (template: ConfigDeclaration) => {
    if (isDirty) {
      setConfirmPending(template);
      return;
    }
    setJsonValue(JSON.stringify(template, null, 2));
    setIsDirty(false);
  };

  const handleConfirmLoad = () => {
    if (confirmPending) {
      setJsonValue(JSON.stringify(confirmPending, null, 2));
      setIsDirty(false);
      setConfirmPending(null);
    }
  };

  const handleCancelLoad = () => {
    setConfirmPending(null);
  };

  const handleSave = () => {
    if (!jsonValue.trim()) {
      toast.error('Nothing to save — build or paste a configuration first');
      return;
    }
    try {
      JSON.parse(jsonValue); // validate before saving
    } catch (error) {
      if (error instanceof SyntaxError) {
        toast.error('Invalid JSON: ' + error.message);
      }
      return;
    }
    const blob = new Blob([jsonValue], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nginx-dapi-config.json';
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Download started');
  };

  const handleFormChange = useCallback((json: string) => {
    setJsonValue(json);
    setIsDirty(true);
  }, []);

  return (
    <Layout>
      {confirmPending && (
        <div className="confirm-overlay" role="dialog" aria-modal="true">
          <div className="confirm-dialog">
            <h3 className="confirm-title">Replace configuration?</h3>
            <p className="confirm-body">
              Loading this template will overwrite your current configuration. This action cannot be undone.
            </p>
            <div className="confirm-actions">
              <button className="btn btn-secondary" onClick={handleCancelLoad}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleConfirmLoad}>
                Load template
              </button>
            </div>
          </div>
        </div>
      )}
      <div className="create-config">
        <div className="card">
          <h3 className="card-title">Quick Start Templates</h3>
          <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.875rem', marginBottom: '1rem' }}>
            Click a template to load it into the editor as a starting point.
          </p>
          <div className="templates-grid">
            <div className="template-card" onClick={() => loadTemplate(nimTemplate)}>
              <h4>NGINX Instance Manager</h4>
              <p>HTTP configuration for a NIM instance group</p>
            </div>
            <div className="template-card" onClick={() => loadTemplate(nginxOneTemplate)}>
              <h4>NGINX One Console</h4>
              <p>HTTP configuration for a config sync group</p>
            </div>
            <div className="template-card" onClick={() => loadTemplate(apiGatewayTemplate)}>
              <h4>API Gateway</h4>
              <p>API gateway with OpenAPI spec and developer portal</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="editor-header">
            <h2 className="card-title">Configuration Declaration</h2>
            <div className="mode-toggle">
              <button
                className={`mode-btn${mode === 'form' ? ' active' : ''}`}
                onClick={() => setMode('form')}
              >
                <LayoutList size={15} />
                <span>Form</span>
              </button>
              <button
                className={`mode-btn${mode === 'json' ? ' active' : ''}`}
                onClick={() => setMode('json')}
              >
                <Code2 size={15} />
                <span>JSON</span>
              </button>
            </div>
          </div>
          <p className="info-message" style={{ marginBottom: '0.75rem', color: 'rgba(255,255,255,0.6)', fontSize: '0.875rem' }}>
            Build your configuration below. Use the templates to get started, then copy the result to use with the NGINX Declarative API.
          </p>

          {mode === 'form' ? (
            <ConfigForm initialJson={jsonValue} onChange={handleFormChange} />
          ) : (
            <div className="json-editor">
              <Editor
                height="560px"
                language="json"
                theme="vs-dark"
                value={jsonValue}
                path="nginx-dapi-config.json"
                onMount={handleEditorMount}
                onChange={(val) => { setJsonValue(val ?? ''); setIsDirty(true); }}
                options={{
                  fontSize: 13,
                  tabSize: 2,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  formatOnPaste: true,
                  formatOnType: false,
                  automaticLayout: true,
                  suggestOnTriggerCharacters: true,
                  quickSuggestions: { other: true, comments: false, strings: true },
                  fixedOverflowWidgets: true,
                }}
              />
            </div>
          )}

          <div className="btn-group">
            <button
              onClick={handleCopy}
              className="btn btn-primary"
            >
              {copied ? <Check size={18} /> : <Copy size={18} />}
              <span>{copied ? 'Copied!' : 'Copy to Clipboard'}</span>
            </button>
            <button
              onClick={handleSave}
              className="btn btn-secondary"
            >
              <Download size={18} />
              <span>Save to File</span>
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};
