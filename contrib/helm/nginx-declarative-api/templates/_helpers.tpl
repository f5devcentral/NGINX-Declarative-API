{{/*
Expand the name of the chart.
*/}}
{{- define "nginx-declarative-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "nginx-declarative-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Resolve the namespace.
*/}}
{{- define "nginx-declarative-api.namespace" -}}
{{- if .Values.global.namespaceOverride }}
{{- .Values.global.namespaceOverride }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}

{{/*
Chart label.
*/}}
{{- define "nginx-declarative-api.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "nginx-declarative-api.labels" -}}
helm.sh/chart: {{ include "nginx-declarative-api.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
nginx-dapi selector labels.
*/}}
{{- define "nginx-declarative-api.nginxDapi.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nginx-declarative-api.name" . }}-nginx-dapi
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
nginx-dapi full labels.
*/}}
{{- define "nginx-declarative-api.nginxDapi.labels" -}}
{{ include "nginx-declarative-api.labels" . }}
{{ include "nginx-declarative-api.nginxDapi.selectorLabels" . }}
app.kubernetes.io/component: nginx-dapi
app.kubernetes.io/version: {{ .Values.nginxDapi.image.tag | quote }}
{{- with .Values.global.podLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
redis selector labels.
*/}}
{{- define "nginx-declarative-api.redis.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nginx-declarative-api.name" . }}-redis
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
redis full labels.
*/}}
{{- define "nginx-declarative-api.redis.labels" -}}
{{ include "nginx-declarative-api.labels" . }}
{{ include "nginx-declarative-api.redis.selectorLabels" . }}
app.kubernetes.io/component: redis
app.kubernetes.io/version: {{ .Values.redis.image.tag | quote }}
{{- end }}

{{/*
devportal selector labels.
*/}}
{{- define "nginx-declarative-api.devportal.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nginx-declarative-api.name" . }}-devportal
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
devportal full labels.
*/}}
{{- define "nginx-declarative-api.devportal.labels" -}}
{{ include "nginx-declarative-api.labels" . }}
{{ include "nginx-declarative-api.devportal.selectorLabels" . }}
app.kubernetes.io/component: devportal
app.kubernetes.io/version: {{ .Values.devportal.image.tag | quote }}
{{- with .Values.global.podLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
ServiceAccount name — nginx-dapi.
*/}}
{{- define "nginx-declarative-api.nginxDapi.serviceAccountName" -}}
{{- if .Values.nginxDapi.serviceAccount.create }}
{{- default (printf "%s-nginx-dapi" (include "nginx-declarative-api.fullname" .)) .Values.nginxDapi.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.nginxDapi.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
ServiceAccount name — devportal.
*/}}
{{- define "nginx-declarative-api.devportal.serviceAccountName" -}}
{{- if .Values.devportal.serviceAccount.create }}
{{- default (printf "%s-devportal" (include "nginx-declarative-api.fullname" .)) .Values.devportal.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.devportal.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Image pull secrets block.
*/}}
{{- define "nginx-declarative-api.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Resolve the effective app version for display in NOTES.
Uses nginxDapi.image.tag as the source of truth.
*/}}
{{- define "nginx-declarative-api.appVersion" -}}
{{- .Values.nginxDapi.image.tag }}
{{- end }}

{{/*
Redis service name — always "redis" to match the hardcoded hostname in
the app's config.toml. The upstream image resolves Redis via this exact
DNS name; it does not read REDIS_HOST from the environment.
*/}}
{{- define "nginx-declarative-api.redis.serviceName" -}}
redis
{{- end }}

{{/*
Devportal service name — fixed to "devportal" to match the hardcoded hostname
used by the nginx-dapi app when communicating with the developer portal service.
*/}}
{{- define "nginx-declarative-api.devportal.serviceName" -}}
devportal
{{- end }}

{{/*
webui selector labels.
*/}}
{{- define "nginx-declarative-api.webui.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nginx-declarative-api.name" . }}-webui
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
webui full labels.
*/}}
{{- define "nginx-declarative-api.webui.labels" -}}
{{ include "nginx-declarative-api.labels" . }}
{{ include "nginx-declarative-api.webui.selectorLabels" . }}
app.kubernetes.io/component: webui
app.kubernetes.io/version: {{ .Values.webui.image.tag | quote }}
{{- with .Values.global.podLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
ServiceAccount name — webui.
*/}}
{{- define "nginx-declarative-api.webui.serviceAccountName" -}}
{{- if .Values.webui.serviceAccount.create }}
{{- default (printf "%s-webui" (include "nginx-declarative-api.fullname" .)) .Values.webui.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.webui.serviceAccount.name }}
{{- end }}
{{- end }}
