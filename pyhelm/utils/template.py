# -*- coding: utf-8 -*-
"""
~~~~~~~~~~~~~~~~~~~~~~~
Generate chart template module.

like: helm create helm-test.


"""
import os
from pyhelm.utils.exceptions import CustomError


values_template = """
# Default values for %s.
# This is a YAML-formatted file.
# Declare variables to be passed into your templates.
replicaCount: 1
image:
  repository: nginx
  tag: stable
  pullPolicy: IfNotPresent
nameOverride: ""
fullnameOverride: ""
service:
  type: ClusterIP
  port: 80
ingress:
  enabled: false
  annotations: {}
    # kubernetes.io/ingress.class: nginx
    # kubernetes.io/tls-acme: "true"
  path: /
  hosts:
    - chart-example.local
  tls: []
  #  - secretName: chart-example-tls
  #    hosts:
  #      - chart-example.local
resources: {}
  # We usually recommend not to specify default resources and to leave this as a conscious
  # choice for the user. This also increases chances charts run on environments with little
  # resources, such as Minikube. If you do want to specify resources, uncomment the following
  # lines, adjust them as necessary, and remove the curly braces after 'resources:'.
  # limits:
  #  cpu: 100m
  #  memory: 128Mi
  # requests:
  #  cpu: 100m
  #  memory: 128Mi
nodeSelector: {}
tolerations: []
affinity: {}

"""


default_ignore = """
# Patterns to ignore when building packages.
# This supports shell glob matching, relative path matching, and
# negation (prefixed with !). Only one pattern per line.
.DS_Store
# Common VCS dirs
.git/
.gitignore
.bzr/
.bzrignore
.hg/
.hgignore
.svn/
# Common backup files
*.swp
*.bak
*.tmp
*~
# Various IDEs
.project
.idea/
*.tmproj
"""


ingress_template = """
{{- if .Values.ingress.enabled -}}
{{- $fullName := include "<CHARTNAME>.fullname" . -}}
{{- $ingressPath := .Values.ingress.path -}}
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: {{ $fullName }}
  labels:
    app.kubernetes.io/name: {{ include "<CHARTNAME>.name" . }}
    helm.sh/chart: {{ include "<CHARTNAME>.chart" . }}
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.ingress.annotations }}
  annotations:
{{ toYaml . | indent 4 }}
{{- end }}
spec:
{{- if .Values.ingress.tls }}
  tls:
  {{- range .Values.ingress.tls }}
    - hosts:
      {{- range .hosts }}
        - {{ . | quote }}
      {{- end }}
      secretName: {{ .secretName }}
  {{- end }}
{{- end }}
  rules:
  {{- range .Values.ingress.hosts }}
    - host: {{ . | quote }}
      http:
        paths:
          - path: {{ $ingressPath }}
            backend:
              serviceName: {{ $fullName }}
              servicePort: http
  {{- end }}
{{- end }}
"""


deployment_template = """
apiVersion: apps/v1beta2
kind: Deployment
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ include "<CHARTNAME>.name" . }}
    helm.sh/chart: {{ include "<CHARTNAME>.chart" . }}
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/managed-by: {{ .Release.Service }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ include "<CHARTNAME>.name" . }}
      app.kubernetes.io/instance: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ include "<CHARTNAME>.name" . }}
        app.kubernetes.io/instance: {{ .Release.Name }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /
              port: http
          readinessProbe:
            httpGet:
              path: /
              port: http
          resources:
{{ toYaml .Values.resources | indent 12 }}
    {{- with .Values.nodeSelector }}
      nodeSelector:
{{ toYaml . | indent 8 }}
    {{- end }}
    {{- with .Values.affinity }}
      affinity:
{{ toYaml . | indent 8 }}
    {{- end }}
    {{- with .Values.tolerations }}
      tolerations:
{{ toYaml . | indent 8 }}
    {{- end }}
"""


service_template = """
apiVersion: v1
kind: Service
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    app.kubernetes.io/name: {{ include "<CHARTNAME>.name" . }}
    helm.sh/chart: {{ include "<CHARTNAME>.chart" . }}
    app.kubernetes.io/instance: {{ .Release.Name }}
    app.kubernetes.io/managed-by: {{ .Release.Service }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    app.kubernetes.io/name: {{ include "<CHARTNAME>.name" . }}
    app.kubernetes.io/instance: {{ .Release.Name }}
"""


note_template = """
1. Get the application URL by running these commands:
{{- if .Values.ingress.enabled }}
{{- range .Values.ingress.hosts }}
  http{{ if $.Values.ingress.tls }}s{{ end }}://{{ . }}{{ $.Values.ingress.path }}
{{- end }}
{{- else if contains "NodePort" .Values.service.type }}
  export NODE_PORT=$(kubectl get --namespace {{ .Release.Namespace }} -o jsonpath="{.spec.ports[0].nodePort}" services {{ include "<CHARTNAME>.fullname" . }})
  export NODE_IP=$(kubectl get nodes --namespace {{ .Release.Namespace }} -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
{{- else if contains "LoadBalancer" .Values.service.type }}
     NOTE: It may take a few minutes for the LoadBalancer IP to be available.
           You can watch the status of by running 'kubectl get svc -w {{ include "<CHARTNAME>.fullname" . }}'
  export SERVICE_IP=$(kubectl get svc --namespace {{ .Release.Namespace }} {{ include "<CHARTNAME>.fullname" . }} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  echo http://$SERVICE_IP:{{ .Values.service.port }}
{{- else if contains "ClusterIP" .Values.service.type }}
  export POD_NAME=$(kubectl get pods --namespace {{ .Release.Namespace }} -l "app.kubernetes.io/name={{ include "<CHARTNAME>.name" . }},app.kubernetes.io/instance={{ .Release.Name }}" -o jsonpath="{.items[0].metadata.name}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl port-forward $POD_NAME 8080:80
{{- end }}
"""


helpers_template = """
{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "<CHARTNAME>.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "<CHARTNAME>.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "<CHARTNAME>.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}
"""


chart_template = """
apiVersion: {apiversion}
appVersion: {appversion}
description: {description}
name: {name}
version: {version}
"""


template_name = {
    'values.yaml': values_template,
    '_helpers.yaml': helpers_template,
    # 'Chart.yaml': chart_default,
    'deployment.yaml': deployment_template,
    'service.yaml': service_template,
    'NOTES.txt': note_template,
    '.helmignore': default_ignore,
}

# base_dir = os.path.abspath(os.path.dirname(__file__))
# print(base_dir)
chart_default = {
    'description': "A Helm chart for Kubernetes",
    'version': '0.1.0',
    'appversion': '1.0',
    'apiversion': 'v1'
}


class Chart(object):
    """ default create chart template."""
    def __init__(self, chart_name, file_path):
        """

        :param chart_name:
        :param file_path: Specify the storage path, must be Sergio absolute path
        """
        self.chart_name = chart_name
        self.file_path = file_path

    def create(self):
        if not os.path.isabs(self.file_path):
            raise CustomError("Please setting abs path, not real path.")

        chart_path = os.path.join(self.file_path, self.chart_name)
        if os.path.exists(chart_path) and os.path.isfile(chart_path):
            raise CustomError("file %s already exists and is not a directory" % chart_path)

        if os.path.exists(chart_path):
            pass
        else:
            try:
                os.mkdir(chart_path, 0755)
            except OSError as e:
                raise CustomError("create chart fail, %s" % e)

        self._save_chart_file(base_path=chart_path, name=self.chart_name)
        self._mkdir_directory(path=chart_path, name='charts')
        self._mkdir_directory(path=chart_path, name='templates')
        template_path = os.path.join(chart_path, 'templates')
        self._save_to_file(template_path)

    def _mkdir_directory(self, path, name):
        """

        :param base_path:
        :param name:
        :return:
        """
        path = os.path.join(path, name)
        if os.path.exists(path):
            pass
        else:
            try:
                os.mkdir(path, 0755)
            except OSError as e:
                raise CustomError("create chart fail, %s" % e)

    def _save_chart_file(self, base_path, name):
        """ save Chart.yaml to file.

        :param base_path:
        :param data:
        :return:
        """
        data = chart_template.format(apiversion=chart_default['apiversion'],
                                     appversion=chart_default['appversion'],
                                     description=chart_default['description'],
                                     name=name,
                                     version=chart_default['version'])
        path = os.path.join(base_path, 'Chart.yaml')
        with open(path, 'wb') as f:
            f.write(data)

    def _save_to_file(self, path):
        for name, template in template_name.items():
            if name == '.helmignore' or name == 'values.yaml':
                ignore_path = os.path.join(os.path.abspath(os.path.dirname(path)), name)
                with open(ignore_path, 'wb') as f:
                    f.write(template)
            else:
                name_path = os.path.join(path, name)
                with open(name_path, 'wb') as f:
                    f.write(template)


if __name__ == '__main__':
    path = '/Users/guoweikuang/project'
    chart = Chart('helm-test', path)
    chart.create()