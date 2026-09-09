---
title: Kubernetes Helm Chart와 Release 관리
description: Helm의 Chart·Release 구조, Repository와 OCI Chart 사용, MariaDB Storage 연결 및 사용자 Chart 작성 정리
date: 2026-09-08
updated_at: 2026-09-09
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

[Kubernetes Kustomize로 Manifest 구성 관리](/cloud-native-39-kubernetes-kustomize/)에서 다룬 Kustomize는 원본 Manifest를 조합하고 환경별 차이를 Overlay로 관리한다. Helm은 여러 Kubernetes Resource와 기본 설정을 Version이 있는 Chart로 묶고, Chart를 Cluster에 설치한 결과를 Release 단위로 관리한다.

## 1 ) Helm

---

> **Helm**
>
> Kubernetes Application을 Chart로 Packaging하고 설치, Upgrade, Rollback과 제거를 Release 단위로 관리하는 CNCF Project이다.

Helm의 주요 구성 요소는 다음과 같다.

| 구성 요소 | 역할 |
|---|---|
| Helm Client | Chart를 읽고 Template을 Rendering하여 Kubernetes API Server에 적용 |
| Chart | Kubernetes Resource Template, 기본값과 Metadata를 묶은 Package |
| Values | 같은 Chart에서 변경할 Image, Replica, Port와 Storage 등의 입력값 |
| Manifest | Chart와 Values를 Rendering한 최종 Kubernetes YAML |
| Release | 특정 Namespace에 설치한 Chart Instance와 Revision History |
| Repository·OCI Registry | Version별 Chart Package를 배포하는 저장소 |

관계는 다음과 같다.

```text
Chart Templates + Default values.yaml + 사용자 Values
                         │
                         ▼
                   Helm Rendering
                         │
                         ▼
             Kubernetes Manifest 집합
                         │ API Server에 적용
                         ▼
                    Helm Release
                         │ Revision 기록
                         ▼
Deployment·StatefulSet·Service 등의 Controller
                         │
                         ▼
              Worker의 kubelet과 Pod
```

Helm은 Application Container를 직접 실행하지 않는다. Helm이 Rendering한 Resource를 API Server에 저장하면 Control Plane의 각 Controller가 원하는 상태를 조정하고 Worker의 kubelet이 실제 Container를 실행한다.

## 2 ) Helm Version과 Kubernetes 호환성

---

2026년 9월 기준 Helm의 현재 Stable Major Version은 Helm 4이다. Helm 3은 지원 종료 단계에 있으므로 신규 환경에서는 Helm 4와 Cluster의 호환 범위를 먼저 확인한다.

```bash
helm version
kubectl version
```

Helm은 내부에 포함된 Kubernetes Client Library를 통해 API Server와 통신한다. Cluster보다 지나치게 오래된 Helm이나 Helm이 보장하지 않는 더 새로운 Kubernetes Cluster를 조합하면 API 호환 문제가 생길 수 있다.

Helm `3.13.3`을 고정하는 다음 명령은 당시 환경을 재현하기 위한 Legacy 예제이다.

```bash
asdf plugin add helm
asdf install helm 3.13.3
asdf global helm 3.13.3
```

asdf 0.16 이상에서는 `asdf global` 대신 `asdf set`을 사용한다. 실제 Version은 Cluster와 Helm의 공식 Version Skew를 확인한 뒤 선택한다.

```bash
asdf plugin add helm
asdf list all helm
asdf install helm <compatible-helm-version>
asdf set --home helm <compatible-helm-version>
helm version
```

## 3 ) Debian·Ubuntu에서 Helm 설치

---

Helm의 Debian·Ubuntu Package Repository를 이용하려면 먼저 필요한 Package를 설치한다.

```bash
sudo apt-get install curl gpg apt-transport-https --yes
```

Repository Signing Key를 내려받아 Fingerprint를 확인하고 Keyring으로 변환한다. Fingerprint 값은 실행 전에 Helm 공식 설치 문서의 현재 값과 다시 대조한다.

```bash
HELM_APT_KEY_ID='DDF78C3E6EBB2D2CC223C95C62BA89D07698DBC6'

curl -fsSL \
  https://packages.buildkite.com/helm-linux/helm-debian/gpgkey \
  -o /tmp/helm.gpg

if [ "$(gpg --show-keys --with-colons /tmp/helm.gpg | awk -F: '$1 == "fpr" {print $10}' | head -n 1)" != "${HELM_APT_KEY_ID}" ]
then
  echo 'ERROR: unexpected Helm APT signing key'
  exit 1
fi
```

확인한 Key를 등록하고 Repository를 추가한다.

```bash
gpg --dearmor < /tmp/helm.gpg | \
  sudo tee /usr/share/keyrings/helm.gpg > /dev/null

echo 'deb [signed-by=/usr/share/keyrings/helm.gpg] https://packages.buildkite.com/helm-linux/helm-debian/any/ any main' | \
  sudo tee /etc/apt/sources.list.d/helm-stable-debian.list

sudo apt-get update
sudo apt-get install helm
helm version
```

Package Repository에서 최신 Major Version이 설치될 수 있으므로 운영 Cluster에 적용하기 전에 `helm version`과 Kubernetes Version 지원 범위를 확인한다.

## 4 ) Chart, Repository와 OCI Registry

---

전통적인 Helm Repository는 `index.yaml`과 Chart Package를 HTTP Server에서 제공한다. OCI Registry는 Container Image와 유사한 방식으로 Chart Artifact를 저장한다.

| 배포 위치 | 검색·사용 방식 |
|---|---|
| Helm Repository | `helm repo add`, `helm repo update`, `helm search repo` |
| Artifact Hub | Browser 또는 `helm search hub`로 여러 공급자의 Chart 검색 |
| OCI Registry | `oci://<registry>/<path>/<chart>`를 직접 참조 |

등록된 Repository를 확인한다.

```bash
helm repo list
```

Bitnami Repository를 등록하고 Index를 갱신한다.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo bitnami/nginx
helm search repo bitnami/mariadb --versions
```

Artifact Hub 전체에서 Chart를 찾을 수 있다.

```bash
helm search hub nginx
helm search hub mariadb
```

과거 Helm의 기본 Chart 모음이었던 `stable`과 `incubator` Repository는 2020년 11월부터 읽기 전용 Archive이며 신규 Chart 선택지로 사용하지 않는다. 현재 Chart는 Artifact Hub에서 공급자, 최근 Release, Source Repository와 보안 정보를 확인한 뒤 선택한다.

### OCI Registry에 사용자 Chart 배포

OCI Registry는 Container Image뿐 아니라 Helm Chart Package도 저장할 수 있다. Chart Directory를 직접 Push하지 않고 `helm package`로 만든 `.tgz` File을 업로드한다.

Registry의 Image 참조 구조, Public·Private Registry와 인증 방식은 [Container Image Registry와 Kubernetes Image Pull](/cloud-native-41-container-image-registry/)에서 다룬다.

```text
Chart Directory
      │ helm lint
      ▼
검증된 Chart
      │ helm package
      ▼
Chart Archive(.tgz)
      │ helm push
      ▼
OCI Registry
      │ helm pull·helm install
      ▼
Helm Client
```

샘플 Chart를 생성한다. 기존 `echo` Directory가 있다면 덮어쓰지 말고 내용을 먼저 확인한다.

```bash
helm create echo
helm lint ./echo
helm template echo-preview ./echo
```

`Chart.yaml`의 `name`과 `version`을 확인한 뒤 Package를 생성한다.

```bash
helm show chart ./echo
helm package ./echo
```

기본 생성값을 사용했다면 현재 Directory에 `echo-0.1.0.tgz`가 만들어진다. 실제 File 이름은 `Chart.yaml`의 Version에 따라 달라진다.

Docker Hub 같은 OCI Registry에 로그인한다. Password 또는 Personal Access Token은 명령 인자에 작성하지 않고 Prompt에 입력한다.

```bash
helm registry login registry-1.docker.io \
  -u <registry-username>
```

Package를 Registry Namespace로 Push한다.

```bash
helm push echo-0.1.0.tgz \
  oci://registry-1.docker.io/<registry-username>
```

`helm push`의 대상 경로에는 Chart 이름과 Tag를 붙이지 않는다. Helm이 `Chart.yaml`의 `name`을 OCI Repository 이름으로, `version`을 Tag로 사용하므로 위 명령의 결과 참조는 다음 형태가 된다.

```text
registry-1.docker.io/<registry-username>/echo:0.1.0
```

OCI Chart 참조는 `oci://` Prefix를 사용하며 `helm show`, `helm pull`과 `helm install`에서 Chart Version을 명시할 수 있다.

```bash
helm show chart \
  oci://registry-1.docker.io/<registry-username>/echo \
  --version 0.1.0

helm pull \
  oci://registry-1.docker.io/<registry-username>/echo \
  --version 0.1.0
```

Cluster에 설치하기 전 Rendering 결과를 확인한다.

```bash
helm template echo-oci-preview \
  oci://registry-1.docker.io/<registry-username>/echo \
  --version 0.1.0
```

검증이 끝난 Chart를 별도 Namespace에 설치하고 Helm Release와 Kubernetes Resource를 함께 확인한다.

```bash
helm install echo-oci \
  oci://registry-1.docker.io/<registry-username>/echo \
  --version 0.1.0 \
  --namespace helm-lab \
  --create-namespace

helm status echo-oci --namespace helm-lab
kubectl get pods,services --namespace helm-lab
```

Chart를 Registry에 Push하는 과정은 Cluster를 변경하지 않는다. `helm install`을 실행해야 Helm Client가 Chart를 Pull하고 Manifest를 Rendering하여 API Server에 제출한다. 그 이후에는 Controller와 Worker의 kubelet이 Resource를 조정한다.

설치한 Chart가 Service를 생성했다면 외부 공개 설정을 추가하기 전에 Port Forwarding으로 응답을 확인한다.

```bash
kubectl port-forward \
  --namespace helm-lab \
  service/echo-oci 8080:80
```

Chart의 실제 Service 이름과 Port는 다음 명령으로 확인한 뒤 예제 값을 바꾼다.

```bash
kubectl get service --namespace helm-lab
kubectl describe service echo-oci --namespace helm-lab
```

Pod가 시작되지 않으면 Release 상태만 보지 않고 Event와 Container Log를 확인한다.

```bash
kubectl get events \
  --namespace helm-lab \
  --sort-by=.metadata.creationTimestamp
kubectl logs \
  --namespace helm-lab \
  deployment/echo-oci \
  --all-pods=true
```

Resource 이름과 Workload Kind는 Chart Template에 따라 다를 수 있다. `helm get manifest echo-oci --namespace helm-lab`으로 실제 생성된 Resource를 확인하고 Log 명령의 대상을 선택한다.

실습이 끝나면 Release와 Registry Login Session을 정리한다.

```bash
helm uninstall echo-oci --namespace helm-lab
helm registry logout registry-1.docker.io
```

## 5 ) Chart 설치 전 확인

---

외부 Chart를 바로 설치하지 않고 Metadata, 기본 Values와 Rendering 결과를 먼저 확인한다.

```bash
helm show chart bitnami/nginx
helm show values bitnami/nginx
helm template my-nginx bitnami/nginx
helm install my-nginx bitnami/nginx --dry-run
```

| 명령 | 확인 대상 |
|---|---|
| `helm show chart` | Chart 이름, Version, Dependency와 Metadata |
| `helm show values` | 변경 가능한 기본 설정 |
| `helm template` | Cluster에 연결하지 않고 생성되는 Manifest |
| `helm install --dry-run` | Release 이름과 Values를 적용한 설치 결과 |

Rendering 결과에서 다음 항목을 확인한다.

- 사용할 Container Image Registry와 Tag

- 생성되는 RBAC Resource와 ServiceAccount 권한

- Service Type과 외부 공개 여부

- PVC, StorageClass와 요청 용량

- Secret에 들어갈 값과 생성 방식

- Namespace와 Cluster Scope Resource

Chart Version을 생략하면 Repository 갱신 시 다른 Version이 선택될 수 있다. 재현 가능한 설치에는 검증한 Chart Version을 명시한다.

```bash
helm install my-nginx bitnami/nginx \
  --version <verified-chart-version>
```

## 6 ) Bitnami Chart의 현재 배포 상태

---

Bitnami는 2025년부터 Public Container와 Chart 배포 정책을 변경했다. Chart Source는 공개되어 있어도 Chart가 참조하는 Versioned Image가 기존 `docker.io/bitnami` Registry에 없을 수 있으며, 이 경우 설치된 Pod는 `ImagePullBackOff` 상태가 된다.

따라서 다음 명령이 성공적으로 Chart를 Rendering했다는 사실만으로 Container Image도 Pull할 수 있다고 판단하지 않는다.

```bash
helm show chart bitnami/mariadb
helm show values bitnami/mariadb
helm template my-mariadb bitnami/mariadb
```

Chart가 사용하는 Image를 Rendering 결과에서 확인한다.

```bash
helm template my-mariadb bitnami/mariadb | \
  grep -E '^[[:space:]]*image:'
```

설치 후 Pod가 시작되지 않으면 Event와 Image를 확인한다.

```bash
kubectl get pods
kubectl describe pod <mariadb-pod-name>
kubectl get pod <mariadb-pod-name> \
  -o jsonpath='{.spec.containers[*].image}{"\n"}'
```

`bitnamilegacy` Registry는 이전 Image를 보관하는 Migration 용도이며 신규 수정과 보안 Update가 제공되지 않는다. 단순히 Repository 이름을 Legacy로 바꿔 운영 문제를 해결했다고 판단하지 않는다.

## 7 ) nginx Chart Release 관리

---

검증한 Chart Version과 Image를 사용할 수 있을 때 nginx Chart를 설치한다.

```bash
helm install my-nginx bitnami/nginx \
  --version <verified-chart-version> \
  --namespace helm-lab \
  --create-namespace
```

Helm Release와 Kubernetes Resource를 함께 확인한다.

```bash
helm list --namespace helm-lab
helm status my-nginx --namespace helm-lab
kubectl get deployments,pods,services \
  --namespace helm-lab
```

Helm은 Release 상태를 기록하지만 Pod가 Ready인지 대신 보장하지 않는다. `helm status`와 함께 Deployment Rollout, Pod Event와 Container Log를 확인한다.

```bash
kubectl rollout status deployment/my-nginx \
  --namespace helm-lab
kubectl get events \
  --namespace helm-lab \
  --sort-by=.metadata.creationTimestamp
```

실습이 끝나면 Release를 제거한다.

```bash
helm uninstall my-nginx --namespace helm-lab
```

Release를 제거해도 Chart가 생성한 PVC가 보존 정책에 따라 남을 수 있으므로 Namespace의 Resource를 확인한다.

## 8 ) MariaDB Chart와 PVC Pending 진단

---

MariaDB 같은 Stateful Application은 기본 Values에서 Persistence가 활성화되어 있을 수 있다. Cluster에 Default StorageClass나 조건에 맞는 PV가 없으면 PVC가 `Pending` 상태로 남고 MariaDB Pod도 정상 시작하지 못한다.

설치 전에 Storage 설정을 확인한다.

```bash
helm show values bitnami/mariadb | \
  grep -A 20 'persistence:'
kubectl get storageclasses
kubectl get persistentvolumes
```

검증한 Chart와 Image를 사용할 수 있는 환경에서 MariaDB를 설치한다.

```bash
helm install my-mariadb bitnami/mariadb \
  --version <verified-chart-version> \
  --namespace helm-lab \
  --create-namespace
```

설치 상태를 Resource 계층별로 확인한다.

```bash
helm status my-mariadb --namespace helm-lab
kubectl get statefulsets,pods \
  --namespace helm-lab
kubectl get persistentvolumeclaims \
  --namespace helm-lab
kubectl get persistentvolumes
```

PVC가 `Pending`이면 Pod Log보다 PVC Event와 StorageClass를 먼저 확인한다.

```bash
kubectl describe persistentvolumeclaim \
  --namespace helm-lab \
  <mariadb-pvc-name>
kubectl get storageclasses
kubectl get events \
  --namespace helm-lab \
  --sort-by=.metadata.creationTimestamp
```

PV, PVC와 StorageClass의 연결은 [Kubernetes Volume과 Persistent Storage](/cloud-native-35-kubernetes-volume-persistent-storage/)에서 자세히 설명한다.

## 9 ) Persistence를 사용하지 않는 임시 실습

---

Storage 구성이 없는 격리 실습에서는 Persistence를 끄고 `emptyDir`를 사용하도록 Chart 값을 변경할 수 있다.

```bash
helm install my-mariadb bitnami/mariadb \
  --version <verified-chart-version> \
  --namespace helm-lab \
  --set primary.persistence.enabled=false \
  --set-string auth.rootPassword='<temporary-password>'
```

`--set`에 입력한 Password는 Shell History와 Process 정보에 노출될 수 있다. 위 명령은 Option 구조를 설명하기 위한 임시 실습이며 실제 Credential은 별도 Secret이나 보호된 Values 전달 방식을 사용한다.

Persistence를 끄면 Pod가 교체될 때 Database Data를 잃을 수 있으므로 운영 Database 구성으로 사용하지 않는다.

```bash
kubectl get pods --namespace helm-lab
kubectl exec -it \
  --namespace helm-lab \
  statefulset/my-mariadb -- bash
```

실습 Release를 제거한다.

```bash
helm uninstall my-mariadb --namespace helm-lab
```

## 10 ) Node Local PV와 PVC 준비

---

직접 구축한 Cluster에서 Dynamic Provisioner가 없다면 특정 Worker의 Directory를 사용하는 정적 PV를 만들 수 있다. 이 방식은 Node 장애 시 다른 Worker로 자동 이동하는 공유 Storage가 아니므로 실습 범위로 제한한다.

먼저 MariaDB Pod를 배치할 Worker 이름을 확인한다.

```bash
kubectl get nodes
```

다음 명령은 선택한 `worker1`에서 실행한다. UID와 GID `1001`은 Bitnami MariaDB Image 계열에서 사용하는 값이므로 실제 선택한 Image의 실행 사용자를 먼저 확인한다.

```bash
sudo mkdir -p /data/mariadb
sudo chown 1001:1001 /data/mariadb
sudo chmod 0750 /data/mariadb
```

모든 사용자에게 쓰기 권한을 주는 `chmod 777`은 사용하지 않는다. 다음 내용을 `mariadb-pv.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mariadb-local-pv
spec:
  storageClassName: manual
  persistentVolumeReclaimPolicy: Retain
  capacity:
    storage: 1Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  local:
    path: /data/mariadb
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - worker1
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mariadb-pvc
  namespace: helm-lab
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

`hostPath`도 Node Directory를 직접 사용하지만 PV와 Pod의 Node 관계를 자동으로 표현하지 않는다. 이 예제는 `local` Volume과 `nodeAffinity`를 사용해 PV가 `worker1`에 종속됨을 Scheduler가 알 수 있게 한다.

Master 또는 관리 Client에서 PV와 PVC를 생성한다.

```bash
kubectl create namespace helm-lab \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f mariadb-pv.yaml
kubectl get persistentvolume
kubectl get persistentvolumeclaim \
  --namespace helm-lab
```

## 11 ) 기존 PVC와 Secret을 MariaDB Chart에 연결

---

MariaDB Credential을 별도 Secret으로 준비하고 Chart에는 Secret 이름만 전달한다. 현재 Bitnami MariaDB Chart를 기준으로 Secret Key 요구 사항은 선택한 Chart Version의 README와 `values.yaml`에서 다시 확인한다.

다음 내용을 `mariadb-auth-secret.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mariadb-auth
  namespace: helm-lab
type: Opaque
stringData:
  mariadb-root-password: REPLACE_WITH_ROOT_PASSWORD
  mariadb-password: REPLACE_WITH_USER_PASSWORD
  mariadb-replication-password: REPLACE_WITH_REPLICATION_PASSWORD
```

실제 Password가 채워진 File은 공개 Repository에 Commit하지 않는다. Secret을 적용한다.

```bash
kubectl apply -f mariadb-auth-secret.yaml
```

다음 내용을 `mariadb-values.yaml`로 저장한다.

```yaml
architecture: standalone

auth:
  existingSecret: mariadb-auth
  database: testdb
  username: dbuser

primary:
  persistence:
    enabled: true
    existingClaim: mariadb-pvc
  nodeSelector:
    kubernetes.io/hostname: worker1
```

PVC와 Pod 모두 `worker1`에 고정되는지 Rendering 결과를 확인한다.

```bash
helm template my-mariadb bitnami/mariadb \
  --version <verified-chart-version> \
  --namespace helm-lab \
  --values mariadb-values.yaml
```

Chart와 Image를 검증한 환경에서 설치한다.

```bash
helm install my-mariadb bitnami/mariadb \
  --version <verified-chart-version> \
  --namespace helm-lab \
  --values mariadb-values.yaml
```

Pod가 선택한 Worker에서 실행되고 PVC가 연결됐는지 확인한다.

```bash
kubectl get pod \
  --namespace helm-lab \
  -o wide
kubectl get persistentvolume
kubectl get persistentvolumeclaim \
  --namespace helm-lab
kubectl describe pod \
  --namespace helm-lab \
  <mariadb-pod-name>
```

## 12 ) 사용자 Helm Chart 구조

---

`helm create`는 기본 Chart Directory를 자동으로 생성한다.

```bash
helm create custom-mariadb
```

기본 Sample을 목적에 맞게 정리하면 다음 구조가 된다.

```text
custom-mariadb/
├── Chart.yaml
├── values.yaml
├── .helmignore
└── templates/
    ├── secret.yaml
    ├── service.yaml
    ├── statefulset.yaml
    └── pvc.yaml
```

| File | 역할 |
|---|---|
| `Chart.yaml` | Chart 이름, Type, Chart Version과 Application Version 정의 |
| `values.yaml` | Template에서 사용할 기본값 정의 |
| `templates/` | Rendering할 Kubernetes Resource Template 저장 |
| `.helmignore` | Chart Package에서 제외할 File Pattern 정의 |

Helm은 `templates/` 아래의 Template을 Rendering하므로 Directory 이름을 정확하게 사용해야 한다.

## 13 ) Chart Metadata와 Values

---

다음 내용을 `custom-mariadb/Chart.yaml`로 저장한다.

```yaml
apiVersion: v2
name: custom-mariadb
description: A custom MariaDB Helm chart
type: application
version: 0.1.0
appVersion: "11.4"
```

`version`은 Chart Package Version이고 `appVersion`은 Chart가 배포하는 Application Version을 설명하는 값이다. 둘은 같은 의미가 아니다.

다음 내용을 `custom-mariadb/values.yaml`로 저장한다.

```yaml
replicaCount: 1

image:
  repository: mariadb
  tag: "11.4"
  pullPolicy: IfNotPresent

mariadb:
  existingSecret: ""
  rootPassword: REPLACE_WITH_ROOT_PASSWORD
  database: appdb
  user: appuser
  password: REPLACE_WITH_USER_PASSWORD

persistence:
  enabled: true
  existingClaim: ""
  storageClassName: ""
  storageSize: 1Gi

service:
  type: ClusterIP
  port: 3306

nodeSelector: {}
```

`mariadb.rootPassword`는 Secret Template이 참조하는 Field이고 `service.type`은 Kubernetes가 인식하는 `ClusterIP` 값을 사용한다. 실제 운영용 Values에는 평문 Password를 저장하지 않고 `mariadb.existingSecret`으로 이미 생성한 Secret을 참조한다.

## 14 ) Secret Template

---

Helm Template의 `{% raw %}{{ ... }}{% endraw %}` 표현은 Jekyll Liquid와 충돌하므로 Code Block 전체를 Raw Tag로 감싼다.

다음 내용을 `custom-mariadb/templates/secret.yaml`로 저장한다.

{% raw %}
```yaml
{{- if not .Values.mariadb.existingSecret }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Release.Name }}-secret
  labels:
    app.kubernetes.io/name: custom-mariadb
    app.kubernetes.io/instance: {{ .Release.Name }}
type: Opaque
stringData:
  mariadb-root-password: {{ .Values.mariadb.rootPassword | quote }}
  mariadb-password: {{ .Values.mariadb.password | quote }}
{{- end }}
```
{% endraw %}

`mariadb.existingSecret`이 비어 있을 때만 Chart가 Secret을 생성한다. 외부 Secret 이름을 지정하면 이 Template은 Resource를 만들지 않는다.

## 15 ) Service와 PVC Template

---

다음 내용을 `custom-mariadb/templates/service.yaml`로 저장한다.

{% raw %}
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}
  labels:
    app.kubernetes.io/name: custom-mariadb
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  type: {{ .Values.service.type }}
  selector:
    app.kubernetes.io/name: custom-mariadb
    app.kubernetes.io/instance: {{ .Release.Name }}
  ports:
    - name: mariadb
      port: {{ .Values.service.port }}
      targetPort: mariadb
```
{% endraw %}

다음 내용을 `custom-mariadb/templates/pvc.yaml`로 저장한다.

{% raw %}
```yaml
{{- if and .Values.persistence.enabled (not .Values.persistence.existingClaim) }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Release.Name }}-data
  labels:
    app.kubernetes.io/name: custom-mariadb
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  accessModes:
    - ReadWriteOnce
  {{- if .Values.persistence.storageClassName }}
  storageClassName: {{ .Values.persistence.storageClassName | quote }}
  {{- end }}
  resources:
    requests:
      storage: {{ .Values.persistence.storageSize }}
{{- end }}
```
{% endraw %}

Persistence가 활성화되고 `existingClaim`이 비어 있을 때만 PVC를 생성한다. `storageClassName`을 비워 두면 Cluster의 Default StorageClass 선택 규칙이 적용된다.

## 16 ) StatefulSet Template

---

다음 내용을 `custom-mariadb/templates/statefulset.yaml`로 저장한다.

{% raw %}
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ .Release.Name }}
  labels:
    app.kubernetes.io/name: custom-mariadb
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  serviceName: {{ .Release.Name }}
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: custom-mariadb
      app.kubernetes.io/instance: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: custom-mariadb
        app.kubernetes.io/instance: {{ .Release.Name }}
    spec:
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: mariadb
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          env:
            - name: MARIADB_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: {{ default (printf "%s-secret" .Release.Name) .Values.mariadb.existingSecret }}
                  key: mariadb-root-password
            - name: MARIADB_DATABASE
              value: {{ .Values.mariadb.database | quote }}
            - name: MARIADB_USER
              value: {{ .Values.mariadb.user | quote }}
            - name: MARIADB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: {{ default (printf "%s-secret" .Release.Name) .Values.mariadb.existingSecret }}
                  key: mariadb-password
          ports:
            - name: mariadb
              containerPort: 3306
          {{- if .Values.persistence.enabled }}
          volumeMounts:
            - name: data
              mountPath: /var/lib/mysql
          {{- end }}
      {{- if .Values.persistence.enabled }}
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: {{ default (printf "%s-data" .Release.Name) .Values.persistence.existingClaim }}
      {{- end }}
```
{% endraw %}

StatefulSet의 Selector와 Pod Label은 Chart의 Release 이름까지 포함하여 다른 Release의 Pod를 관리하지 않게 한다. `existingSecret`과 `existingClaim`이 있으면 외부 Resource를 사용하고, 비어 있으면 Chart가 만든 Secret과 PVC 이름을 참조한다.

이 Chart는 하나의 MariaDB Instance를 위한 학습 예제이다. `replicaCount`를 1보다 크게 설정하면 여러 MariaDB Process가 같은 PVC를 사용하게 되므로 복제 구성이 되지 않으며 Data가 손상될 수 있다. MariaDB 복제는 Database의 복제 설정과 Pod별 Volume을 함께 제공하는 별도 Chart 구조가 필요하다.

## 17 ) Chart 검증과 설치

---

Chart를 Cluster에 적용하기 전에 구조와 Rendering 결과를 검사한다.

```bash
helm lint ./custom-mariadb
helm template my-custom-mariadb ./custom-mariadb \
  --namespace helm-lab
```

앞에서 만든 `mariadb-auth` Secret과 `mariadb-pvc`를 사용하려면 다음 내용을 `custom-mariadb-lab-values.yaml`로 저장한다.

```yaml
mariadb:
  existingSecret: mariadb-auth

persistence:
  enabled: true
  existingClaim: mariadb-pvc

nodeSelector:
  kubernetes.io/hostname: worker1
```

외부 Secret, PVC와 Worker 배치 조건을 적용한 결과도 확인한다.

```bash
helm template my-custom-mariadb ./custom-mariadb \
  --namespace helm-lab \
  --values custom-mariadb-lab-values.yaml
```

Server 측 API 검증까지 수행하려면 Rendering 결과를 `kubectl apply --dry-run=server`에 전달한다.

```bash
helm template my-custom-mariadb ./custom-mariadb \
  --namespace helm-lab \
  --values custom-mariadb-lab-values.yaml | \
  kubectl apply \
    --namespace helm-lab \
    --dry-run=server \
    -f -
```

검증 후 Chart를 설치한다.

```bash
helm install my-custom-mariadb ./custom-mariadb \
  --namespace helm-lab \
  --create-namespace \
  --values custom-mariadb-lab-values.yaml
```

Release와 StatefulSet, Pod, Service와 PVC를 확인한다.

```bash
helm status my-custom-mariadb \
  --namespace helm-lab
kubectl get statefulsets,pods,services,persistentvolumeclaims \
  --namespace helm-lab
```

## 18 ) Upgrade와 Rollback

---

Values를 변경한 뒤 Upgrade하면 Release Revision이 증가한다.

```bash
helm upgrade my-custom-mariadb ./custom-mariadb \
  --namespace helm-lab \
  --values custom-mariadb-lab-values.yaml \
  --set image.tag='<verified-mariadb-version>'
```

History와 적용된 Values를 확인한다.

```bash
helm history my-custom-mariadb \
  --namespace helm-lab
helm get values my-custom-mariadb \
  --namespace helm-lab
helm get manifest my-custom-mariadb \
  --namespace helm-lab
```

문제가 있으면 이전 Revision으로 Rollback한다.

```bash
helm rollback my-custom-mariadb <revision> \
  --namespace helm-lab
```

Helm Rollback은 Kubernetes Resource Spec을 과거 Release Revision으로 되돌린다. Database File Format이나 이미 변경된 Data를 자동으로 복구하지 않으므로 Stateful Application은 Backup과 Migration 호환성을 별도로 확인해야 한다.

## 19 ) 실습 Resource 정리

---

Helm으로 설치한 Release를 확인하고 제거한다.

```bash
helm list --all-namespaces
helm uninstall my-custom-mariadb \
  --namespace helm-lab
helm uninstall my-mariadb \
  --namespace helm-lab
helm uninstall my-nginx \
  --namespace helm-lab
```

`helm list --namespace helm-lab`에서 존재하는 Release만 제거한다. 생성하지 않은 Release를 `helm uninstall`하면 찾을 수 없다는 오류가 발생한다.

정적 PV와 PVC는 Data 보존 여부를 확인한 뒤 별도로 처리한다.

```bash
kubectl get persistentvolume
kubectl get persistentvolumeclaim \
  --namespace helm-lab
kubectl delete -f mariadb-pv.yaml
kubectl delete -f mariadb-auth-secret.yaml \
  --ignore-not-found
```

`persistentVolumeReclaimPolicy: Retain`인 PV를 삭제해도 Worker의 `/data/mariadb` Data는 자동으로 삭제되지 않는다. Data가 더 이상 필요하지 않은지 확인한 뒤 해당 Worker에서 별도로 정리한다.

`helm-lab`이 이 실습에만 사용됐는지 확인한 뒤 Namespace를 삭제한다.

```bash
kubectl get all,secret,persistentvolumeclaim \
  --namespace helm-lab
kubectl delete namespace helm-lab
```

## 전체 정리

---

> **최종 정리**
>
> - Helm은 여러 Kubernetes Resource를 Chart로 Packaging하고 설치 결과를 Release와 Revision으로 관리한다.
>
> - Chart와 Values를 Rendering한 결과가 Manifest이며 Control Plane은 이 최종 Resource만 처리한다.
>
> - 외부 Chart는 Version, Image Registry, RBAC, Service와 Storage 설정을 확인한 뒤 설치한다.
>
> - `stable`과 `incubator` Repository는 Archive이며 현재 Chart는 Artifact Hub와 유지보수되는 Repository·OCI Registry에서 찾는다.
>
> - 사용자 Chart는 `helm package`로 `.tgz` Archive를 만든 뒤 `helm push`로 OCI Registry에 배포하며 Chart 이름과 Version은 `Chart.yaml`에서 결정된다.
>
> - Bitnami Chart Source와 기존 Image의 제공 상태는 같지 않으므로 Rendering된 Image를 실제로 Pull할 수 있는지 확인해야 한다.
>
> - MariaDB PVC가 Pending이면 Pod Log보다 PVC Event, PV와 StorageClass를 먼저 확인한다.
>
> - Node Local Storage는 PV Node Affinity와 Pod 배치 조건을 같은 Worker에 맞춰야 한다.
>
> - Helm Template은 Jekyll Liquid와 충돌하지 않도록 Raw Tag로 감싸고 `helm lint`와 `helm template`로 검증한다.
>
> - Helm Rollback은 Resource Spec을 되돌리며 Database Data와 Schema를 자동으로 복원하지 않는다.
