---
title: Argo CD Application 배포와 CLI·Autopilot
description: Argo CD Application CRD로 Helm Chart를 배포하고 Sync·Health, CLI 조작과 Autopilot Bootstrap 구조를 확인한다
date: 2026-09-17
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - ArgoCD
---

[GitOps와 Argo CD Architecture·설치](/cloud-native-55-gitops-argocd-architecture-installation/)에서는 Git의 Desired State와 Kubernetes Live State를 비교하는 구성 요소를 정리했다. 이 글에서는 `Application` Resource로 Helm Chart를 배포하고 UI, `kubectl`과 Argo CD CLI에서 Sync 결과를 확인한 뒤 Autopilot의 Bootstrap 방식을 살펴본다.

## 1 ) Application CRD

---

> **Application**은 Argo CD가 어디에서 어떤 Manifest를 가져와 어느 Cluster와 Namespace에 배포할지 선언하는 Custom Resource이다.

| Field | 역할 |
|---|---|
| `spec.project` | Application이 속한 Argo CD Project |
| `spec.source` | Git, Helm 또는 OCI Source와 Revision |
| `spec.destination` | 대상 Cluster API와 Namespace |
| `spec.syncPolicy` | 자동 Sync, Prune, Self Heal과 Sync Option |

`Application` Resource 자체는 일반적으로 Argo CD가 설치된 `argocd` Namespace에 생성한다. 실제 Workload는 `spec.destination.namespace`에 배포된다.

## 2 ) Helm Chart Version 확인

---

예제는 Bitnami NGINX Chart를 사용한다. Application File에 Version을 기록하기 전에 Repository에서 존재하는 Version을 확인한다.

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo bitnami/nginx --versions | head
```

Chart Version과 Container Image Version은 같은 값이 아니다. `targetRevision`에는 `helm search` 결과의 Chart Version을 사용한다.

## 3 ) NGINX Application 선언

---

`application.yaml`을 작성한다.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx-app
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://charts.bitnami.com/bitnami
    chart: nginx
    targetRevision: <verified-chart-version>
    helm:
      parameters:
        - name: service.type
          value: NodePort
        - name: replicaCount
          value: "2"

  destination:
    server: https://kubernetes.default.svc
    namespace: nginx-deploy

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

| 설정 | 동작 |
|---|---|
| `server: https://kubernetes.default.svc` | Argo CD가 실행 중인 Cluster에 배포 |
| `replicaCount: "2"` | Helm Value를 통해 NGINX Replica 두 개 요청 |
| `automated` | OutOfSync 감지 후 자동 Sync |
| `prune: true` | Git·Chart에서 제거된 Resource를 Cluster에서도 제거 |
| `selfHeal: true` | 사람이 Cluster Resource를 직접 바꾼 Drift를 Desired State로 복원 |
| `CreateNamespace=true` | 대상 Namespace가 없으면 생성 |

`prune`과 `selfHeal`은 편리하지만 삭제와 되돌림도 자동화한다. 운영 환경에서는 Project 권한, Sync Window, 보호할 Resource와 변경 Review 절차를 함께 구성한다.

## 4 ) Application 생성과 상태 확인

---

Application을 생성한다.

```bash
kubectl apply -f application.yaml
```

Argo CD Application 상태를 확인한다.

```bash
kubectl get applications -n argocd
kubectl describe application nginx-app -n argocd
```

대상 Namespace와 Workload도 함께 확인한다.

```bash
kubectl get all -n nginx-deploy
kubectl get pods -n nginx-deploy -o wide
kubectl get service -n nginx-deploy
```

Application이 `Synced`여도 Pod가 `Pending`이나 `CrashLoopBackOff`일 수 있다. Argo CD의 Sync·Health와 Kubernetes Pod 상태를 함께 확인한다.

NodePort가 할당됐다면 실제 값을 조회한다.

```bash
kubectl get service -n nginx-deploy \
  -o custom-columns='NAME:.metadata.name,TYPE:.spec.type,NODE_PORT:.spec.ports[*].nodePort'
```

고정된 `30555` 같은 값을 가정하지 않고 조회한 NodePort와 접근 가능한 Node IP를 조합한다.

## 5 ) 자동 Sync와 Self Heal 관찰

---

Replica 수를 직접 바꿔 Drift를 만들 수 있다.

```bash
kubectl scale deployment \
  --namespace nginx-deploy \
  --replicas 1 \
  nginx-app
```

실제 Deployment 이름은 Chart Version에 따라 달라질 수 있으므로 먼저 `kubectl get deployments -n nginx-deploy`로 확인한다. `selfHeal: true`라면 Argo CD가 Helm Parameter의 Replica 두 개로 다시 맞춘다.

```bash
kubectl get deployment -n nginx-deploy --watch
```

이 실습은 Drift 복원 동작을 확인하기 위한 것이다. 운영 환경에서 `kubectl edit`나 `kubectl scale`로 영구 변경하지 않고 Deployment Repository의 선언을 수정한다.

## 6 ) Argo CD CLI 설치

---

Linux `amd64` 환경에서는 Release Version을 확인해 Binary를 설치할 수 있다.

```bash
ARGOCD_VERSION=$(curl --silent \
  https://api.github.com/repos/argoproj/argo-cd/releases/latest \
  | grep '"tag_name"' \
  | cut -d '"' -f 4)

curl --fail --location \
  --output argocd-linux-amd64 \
  "https://github.com/argoproj/argo-cd/releases/download/$ARGOCD_VERSION/argocd-linux-amd64"

chmod +x argocd-linux-amd64
sudo mv argocd-linux-amd64 /usr/local/bin/argocd
argocd version --client
```

ARM64 Machine은 `argocd-linux-arm64`, macOS는 OS와 Architecture에 맞는 Binary 또는 Homebrew Package를 사용한다. Download URL을 바꾸기 전에 `uname -s`와 `uname -m`으로 환경을 확인한다.

## 7 ) CLI Login과 Application 조작

---

Port Forward가 `localhost:8080`에서 실행 중인 상태에서 Login한다.

```bash
argocd login localhost:8080 \
  --username admin \
  --insecure
```

Password는 대화형 Prompt에 입력한다. `--insecure`는 자체 서명 인증서를 사용하는 격리된 학습 환경의 Port Forward에서만 사용한다. 운영 Endpoint에서는 신뢰할 수 있는 TLS 인증서를 구성한다.

Application 목록과 상세 상태를 확인한다.

```bash
argocd app list
argocd app get nginx-app
argocd app history nginx-app
```

수동 Sync가 필요한 Application은 다음처럼 실행한다.

```bash
argocd app sync nginx-app
argocd app wait nginx-app --health --timeout 300
```

`sync` 성공은 API 요청이 수락됐다는 의미와 구분해야 한다. `app wait --health`로 Workload가 정상 상태에 도달했는지 확인한다.

## 8 ) CLI로 Application 생성

---

Manifest 대신 CLI로 같은 종류의 Application을 만들 수 있다.

```bash
argocd app create nginx-cli \
  --repo https://charts.bitnami.com/bitnami \
  --helm-chart nginx \
  --revision <verified-chart-version> \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace nginx-cli \
  --sync-option CreateNamespace=true

argocd app sync nginx-cli
argocd app wait nginx-cli --health --timeout 300
```

CLI는 빠른 실습에 유용하지만 Command만 실행하고 기록하지 않으면 Application 생성 과정이 Git Review에 남지 않는다. 운영 구성은 `Application` YAML이나 ApplicationSet을 Deployment Repository에서 관리한다.

## 9 ) Argo CD Autopilot

---

Argo CD Autopilot은 Argo CD 설치와 GitOps Repository 구조를 정해진 방식으로 Bootstrap하는 선택 도구이다.

- GitOps Repository Directory 구조 생성

- Argo CD와 ApplicationSet 설치

- Project와 Application Manifest Commit

- 기존 또는 새 Repository를 이용한 Bootstrap

- 새 Cluster에서 Repository를 기준으로 복구할 구조 제공

Autopilot은 Bootstrap 단계에서 Kubernetes Cluster에 직접 접근해 Argo CD를 설치한다. 이후 일반적인 Project와 Application 작업은 GitOps Repository에 Manifest를 Commit하고 Argo CD가 이를 조정하는 방식으로 이어진다.

Autopilot Repository는 Archived 상태는 아니지만 독립적인 Version과 Release 주기를 가진다. 사용 전 [공식 Repository](https://github.com/argoproj-labs/argocd-autopilot)에서 최신 Release, Issue와 지원 상태를 확인한다. Argo CD 핵심 기능과 Autopilot 사용 여부를 분리해 결정한다.

## 10 ) Autopilot 설치

---

Linux `amd64` 예제이다.

```bash
AUTOPILOT_VERSION=$(curl --silent \
  https://api.github.com/repos/argoproj-labs/argocd-autopilot/releases/latest \
  | grep '"tag_name"' \
  | cut -d '"' -f 4)

curl --fail --location --output - \
  "https://github.com/argoproj-labs/argocd-autopilot/releases/download/$AUTOPILOT_VERSION/argocd-autopilot-linux-amd64.tar.gz" \
  | tar xz

sudo mv argocd-autopilot-* /usr/local/bin/argocd-autopilot
argocd-autopilot version
```

Pipeline에서 매번 Latest Release를 자동 설치하기보다 검증한 Version을 고정한다. 다른 OS와 Architecture에서는 Release Asset 이름을 확인해 변경한다.

## 11 ) GitOps Repository Bootstrap

---

Autopilot이 사용할 Git Repository와 Token을 준비한다.

```bash
export GIT_REPO='https://github.com/<github-owner>/autopilot-nginx.git'
read -s -p 'Git token: ' GIT_TOKEN
export GIT_TOKEN
echo
```

Token에는 Repository 생성 또는 Push에 실제로 필요한 최소 권한과 만료 기간만 부여한다. Token을 Shell Script, Blog, Screenshot과 Shell History에 기록하지 않는다.

현재 `kubectl` Context가 설치 대상 Cluster를 가리키는지 확인한 뒤 Bootstrap한다.

```bash
kubectl config current-context
argocd-autopilot repo bootstrap
```

Project와 Application을 생성한다.

```bash
argocd-autopilot project create testing

argocd-autopilot app create nginx \
  --app github.com/<github-owner>/autopilot-nginx/apps/nginx \
  --project testing
```

명령 실행 후 GitOps Repository의 Commit과 Directory 구조를 먼저 확인한다. Cluster Resource만 확인하면 어떤 선언이 배포를 만들었는지 놓칠 수 있다.

```text
gitops-repo/
├── bootstrap/
├── projects/
└── apps/
```

실제 Directory는 Autopilot Version과 Option에 따라 달라질 수 있으므로 생성 결과를 기준으로 설명한다. Autopilot 소개 문서에 남아 있는 일부 예정 기능은 구현된 기능으로 단정하지 않고 Release와 공식 문서를 확인한다.

## 12 ) 실습 Resource 정리

---

CLI로 만든 Application을 삭제한다.

```bash
argocd app delete nginx-cli
```

Manifest로 만든 Application과 Workload를 정리한다.

```bash
kubectl delete -f application.yaml
kubectl get all -n nginx-deploy
```

`prune`과 Application 삭제 정책에 따라 대상 Resource가 함께 삭제되는지 확인한다. Namespace가 남아 있고 더 이상 사용하지 않으면 별도로 삭제한다.

```bash
kubectl delete namespace nginx-deploy nginx-cli
```

> **최종 정리**
> - `Application`은 Source, Destination과 Sync Policy를 선언하는 Argo CD CRD이다.
>
> - `Synced`와 `Healthy`를 함께 확인해 선언 일치와 Runtime 상태를 구분한다.
>
> - `selfHeal`은 직접 수정한 Drift를 되돌리고 `prune`은 선언에서 사라진 Resource를 삭제한다.
>
> - CLI는 조회와 실습에 유용하지만 운영 선언은 Git Repository에서 관리한다.
>
> - Autopilot은 Argo CD 핵심 기능과 별개인 선택 도구이며 Version과 유지보수 상태를 확인한 뒤 도입한다.
