---
title: GitOps와 Argo CD Architecture·설치
description: GitOps의 선언적 Desired State와 지속적 조정을 이해하고 Argo CD 구성 요소를 Kubernetes에 Helm으로 설치한다
date: 2026-09-17
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - ArgoCD
---

[Docker로 GitLab CE 설치와 운영 준비](/cloud-native-54-gitlab-docker-installation/)에서는 Source Repository를 직접 운영하기 위한 Git Server를 구성했다. GitOps는 Git Repository에 선언한 Desired State를 기준으로 Kubernetes Cluster를 지속적으로 조정한다. 이 글에서는 일반적인 CI와 GitOps CD의 경계를 구분하고, Argo CD의 구성 요소와 설치 흐름을 Control Plane과 Worker 관점에서 연결한다.

## 1 ) GitOps

---

> **GitOps**는 Application과 Infrastructure의 원하는 상태를 선언적 File로 작성해 Git에서 Version 관리하고, 자동화된 Agent가 실제 환경을 그 상태에 맞추는 운영 방식이다.

Git을 단순한 Manifest 보관 장소로 사용하는 것만으로는 GitOps가 되지 않는다. 변경 Review, Version 이력, 자동 반영과 실제 상태의 지속적인 비교가 함께 동작해야 한다.

| 원칙 | 의미 |
|---|---|
| 선언적 구성 | 현재 실행 절차가 아니라 최종적으로 원하는 상태를 작성 |
| Version 관리와 불변 이력 | 변경 내용을 Git Commit으로 추적하고 이전 상태를 확인 |
| 자동 반영 | 승인된 Git 변경을 Agent가 대상 환경에 적용 |
| 지속적 조정 | Git의 Desired State와 Cluster의 Live State 차이를 반복 확인 |

예를 들어 “Pod를 세 개 생성하라”는 일회성 명령보다 `replicas: 3`이라는 상태를 선언한다. Pod 하나가 사라지면 Kubernetes Controller가 세 개라는 상태를 다시 맞추고, Manifest가 바뀌면 GitOps Controller가 변경된 선언을 Cluster에 반영한다.

## 2 ) GitOps를 사용하는 이유

---

- **표준 Workflow**: Branch, Pull Request, Review와 Merge라는 Git Workflow로 운영 변경을 처리한다.

- **감사 가능성**: 누가 어떤 값을 언제 변경했는지 Commit 이력으로 확인한다.

- **Rollback 기준**: 이전 Commit이나 Release의 Manifest로 돌아갈 근거가 남는다.

- **구성 Drift 탐지**: 사람이 Cluster를 직접 변경해 Git과 달라진 상태를 찾을 수 있다.

- **다중 환경 일관성**: 개발, 검증과 운영 환경의 공통 Base와 차이를 Version 관리한다.

GitOps가 모든 수동 작업을 없애는 것은 아니다. 긴급 변경, Secret 관리, Cluster Bootstrap과 Controller 장애 시 복구 절차는 별도로 설계해야 한다.

## 3 ) Kubernetes CI와 GitOps CD

---

CI는 Application Source를 Test하고 Container Image를 만든다. GitOps CD는 배포 Repository의 Manifest 변경을 감시하고 Cluster에 반영한다.

| 단계 | 기준 Repository | 주요 결과 |
|---|---|---|
| Source 변경 | Application Source Repository | Build와 Test 대상 Code |
| CI | Application Source Repository | Commit을 식별할 수 있는 Image Tag |
| Image 저장 | Container Registry | 배포 가능한 Immutable Artifact |
| 배포 변경 | Deployment Repository | 새 Image Tag가 기록된 Manifest |
| CD 조정 | Deployment Repository | Cluster의 Live State 변경 |

Application Source와 Deployment Manifest를 두 Repository로 분리하면 Image 생성 권한과 운영 배포 승인 권한을 구분할 수 있다. CI가 Registry에 Image를 Push한 뒤 Deployment Repository의 Image Tag를 Pull Request로 변경하고, Argo CD가 Merge된 Manifest를 Cluster에 반영한다.

{% include visuals/argocd-gitops-reconciliation-flow.html %}

## 4 ) Argo Project의 도구

---

Argo 생태계에는 서로 다른 역할의 Kubernetes Native 도구가 있다.

| 도구 | 역할 |
|---|---|
| Argo CD | Git Repository와 Kubernetes 상태를 조정하는 GitOps CD |
| Argo Rollouts | Blue-Green, Canary 같은 점진적 배포 Controller |
| Argo Workflows | DAG와 Step 기반 Kubernetes Workflow Engine |
| Argo Events | Event Source와 Sensor를 이용한 Event 기반 자동화 |

Argo CD는 CI Build Tool이 아니다. Source Compile과 Image Build는 GitHub Actions나 Jenkins 같은 CI가 담당하고, Argo CD는 배포 가능한 Manifest와 Cluster 상태를 다룬다.

## 5 ) Argo CD의 상태 모델

---

Argo CD는 Git Repository에서 Rendering한 Manifest와 Kubernetes API에서 읽은 Live Resource를 비교한다.

| 상태 | 확인 내용 |
|---|---|
| `Synced` | Desired State와 Live State가 일치 |
| `OutOfSync` | Git과 Cluster Resource에 차이가 있음 |
| `Healthy` | Application Resource가 정상 상태 |
| `Progressing` | 배포나 상태 전환이 진행 중 |
| `Degraded` | 일부 Resource가 실패하거나 비정상 상태 |
| `Missing` | Git에는 있지만 Cluster에 Resource가 없음 |

Sync Status와 Health Status는 다른 질문에 답한다. Git과 값이 같아도 Application이 Crash하면 `Synced`이면서 `Degraded`일 수 있다. 반대로 정상 실행 중인 Resource를 Git에서 변경하면 `Healthy`이면서 `OutOfSync`가 될 수 있다.

## 6 ) Argo CD 핵심 구성 요소

---

### API Server

Web UI, CLI와 외부 System이 Argo CD를 조작하는 진입점이다.

- Application 생성과 상태 조회

- Repository와 Cluster Credential 관리

- Login, SSO와 RBAC

- Sync와 Rollback 요청 처리

### Repository Server

Git Repository를 Local Cache로 유지하고 배포할 Manifest를 생성한다. Plain YAML뿐 아니라 Kustomize와 Helm을 Rendering한다. Argo CD에서 Helm은 Chart를 Manifest로 변환하는 역할이며 Release Lifecycle은 Argo CD가 관리한다.

### Application Controller

Application의 Desired State와 Live State를 지속적으로 비교한다. 차이가 있고 Sync가 요청되면 Kubernetes API를 통해 Resource를 생성·수정·삭제하고 Health를 관찰한다.

Controller가 매번 `kubectl` Process를 실행한다고 이해하면 안 된다. Argo CD가 Kubernetes API와 통신해 같은 목적의 Resource 변경을 수행한다.

## 7 ) Control Plane과 Worker에서 보는 조정 과정

---

Argo CD Component도 Kubernetes Pod로 실행되지만, 배포 대상 Workload를 직접 실행하지는 않는다.

1. Repository Server가 Git 또는 Helm Repository에서 Manifest를 Rendering한다.

2. Application Controller가 Rendering 결과와 API Server에서 읽은 Live State를 비교한다.

3. 차이가 있으면 Application Controller가 Kubernetes API Server에 Resource 변경을 요청한다.

4. Control Plane의 Controller가 Deployment와 ReplicaSet 상태를 맞춘다.

5. Scheduler가 새 Pod를 실행할 Worker Node를 선택한다.

6. Worker의 kubelet이 Container Runtime에 Image Pull과 Container 생성을 요청한다.

7. Application Controller가 API Server를 통해 Resource 상태를 다시 읽고 Sync와 Health를 갱신한다.

Argo CD의 조정과 Kubernetes Controller의 조정은 계층이 다르다. Argo CD는 Git과 Kubernetes Resource를 맞추고, Kubernetes Controller는 Resource Spec과 실제 Pod·Node 상태를 맞춘다.

## 8 ) 설치 전 확인

---

Argo CD를 설치할 Cluster와 현재 Context를 확인한다.

```bash
kubectl config current-context
kubectl get nodes -o wide
helm version
```

실습 환경은 단일 Argo CD Instance가 같은 Cluster를 관리하는 구성을 사용한다. 운영 환경에서는 Kubernetes와 Argo CD Version 호환성, RBAC 범위, HA 여부와 관리 대상 Cluster를 먼저 결정한다. 공식 설치 유형은 [Argo CD Installation](https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/)에서 확인할 수 있다.

## 9 ) Helm으로 Argo CD 설치

---

Community에서 관리하는 Argo Helm Repository를 추가하고 Index를 갱신한다.

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm search repo argo/argo-cd --versions | head
```

Namespace를 만들고 사용할 Chart Version을 명시해 설치한다.

```bash
kubectl create namespace argocd

helm install argocd argo/argo-cd \
  --namespace argocd \
  --version <verified-chart-version>
```

`<verified-chart-version>`에는 `helm search`로 확인하고 Kubernetes Version과 검증한 값을 사용한다. Version을 생략하면 실행 시점의 최신 Chart가 선택되어 같은 명령의 결과가 달라질 수 있다.

Manifest 방식이 필요한 경우 공식 Stable Manifest를 적용할 수 있다.

```bash
kubectl apply \
  --namespace argocd \
  --filename https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

평가용 Non-HA Manifest와 운영용 HA 구성은 목적이 다르다. 설치 방식을 혼합하기보다 Helm 또는 Manifest 중 하나를 선택해 Release와 Upgrade 경로를 일관되게 관리한다.

## 10 ) 설치 상태 확인

---

Argo CD Pod와 Service를 확인한다.

```bash
kubectl get pods -n argocd -o wide
kubectl get services -n argocd
kubectl get deployments,statefulsets -n argocd
```

Pod가 준비될 때까지 기다린다.

```bash
kubectl wait \
  --for=condition=Available \
  deployment/argocd-server \
  --namespace argocd \
  --timeout=300s
```

문제가 있으면 상태와 Event를 함께 확인한다.

```bash
kubectl describe pod -n argocd <pod-name>
kubectl logs -n argocd <pod-name> --all-containers
kubectl get events -n argocd --sort-by=.lastTimestamp
```

## 11 ) Web UI 접근 방식

---

`argocd-server` Service는 기본적으로 Cluster 외부에 공개되지 않는다. 학습 환경에서는 Port Forward로 Local Computer에서만 연결한다.

```bash
kubectl port-forward \
  service/argocd-server \
  --namespace argocd \
  8080:443
```

다른 Terminal에서 `https://localhost:8080`에 접속한다. 기본 인증서는 자체 서명 인증서이므로 운영 환경에서는 신뢰할 수 있는 인증서를 적용한 Ingress나 LoadBalancer를 구성한다.

NodePort로 바꾸면 모든 Node IP와 할당된 Port를 통해 접근할 수 있다.

```bash
kubectl patch service argocd-server \
  --namespace argocd \
  --type merge \
  --patch '{"spec":{"type":"NodePort"}}'

kubectl get service argocd-server -n argocd
```

NodePort 번호는 Cluster가 할당하므로 예제의 고정 번호를 가정하지 않고 조회 결과를 사용한다. 방화벽과 접근 가능한 Source 대역도 함께 제한한다.

## 12 ) 초기 Admin Password

---

초기 계정 이름은 `admin`이다. Password는 Secret에서 확인한다.

```bash
kubectl get secret argocd-initial-admin-secret \
  --namespace argocd \
  --output jsonpath='{.data.password}' \
  | base64 --decode
echo
```

Password 값을 Blog, Screenshot이나 Shell Script에 저장하지 않는다. 첫 Login 직후 Password를 변경하고 초기 Secret의 보관 필요성을 검토한다.

> **최종 정리**
> - GitOps는 Git의 선언과 실제 환경을 자동으로 지속해서 비교·조정한다.
>
> - CI는 Test와 Image 생성을, Argo CD는 Manifest 기반 CD를 담당한다.
>
> - Repository Server가 Manifest를 만들고 Application Controller가 Kubernetes API를 통해 상태를 맞춘다.
>
> - Argo CD 조정 뒤에는 Control Plane의 Controller·Scheduler와 Worker의 kubelet·Runtime 동작이 이어진다.
>
> - 학습 환경에서는 Port Forward, 운영 환경에서는 TLS와 접근 제어를 갖춘 Ingress나 LoadBalancer를 사용한다.

다음 글인 [Argo CD Application 배포와 CLI·Autopilot](/cloud-native-56-argocd-application-cli-autopilot/)에서는 실제 `Application` Resource를 생성하고 Sync 결과를 확인한다.
