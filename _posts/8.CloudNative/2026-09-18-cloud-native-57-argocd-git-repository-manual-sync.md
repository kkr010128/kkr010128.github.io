---
title: Argo CD Git Repository 연동과 수동 Sync
description: Kubernetes Manifest를 GitHub Repository에 저장하고 Argo CD Application으로 등록하여 OutOfSync 상태를 수동 동기화한다
date: 2026-09-18
updated_at: 2026-09-22
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - ArgoCD
---

[Argo CD Application 배포와 CLI·Autopilot](/cloud-native-56-argocd-application-cli-autopilot/)에서는 Helm Chart를 Source로 사용하는 Application과 자동 Sync를 구성했다. 이번에는 Namespace, Deployment와 Service Manifest를 GitHub Repository에 저장하고 `syncPolicy.automated`를 설정하지 않은 Application으로 등록한다. Git의 Desired State가 `OutOfSync`로 감지된 뒤 사용자가 수동 Sync를 요청했을 때 Control Plane과 Worker에서 어떤 동작이 이어지는지 확인한다.

## 1 ) 실습 구조와 준비 사항

---

이번 실습에서는 Application Source와 Argo CD Application 선언을 다음처럼 구분한다.

```text
bgd Repository
└── manifest/
    ├── ns.yaml
    ├── deployment.yaml
    └── svc.yaml

Local 관리 File
└── bgd-app.yaml
```

`manifest/` Directory는 Argo CD가 읽는 Desired State이다. `bgd-app.yaml`은 해당 Repository와 배포 대상을 Argo CD에 등록하는 `Application` Resource이다.

작업 전에 다음 조건을 확인한다.

- Argo CD가 Kubernetes Cluster에 설치되어 있어야 한다.

- `kubectl`의 현재 Context가 배포 대상 Cluster를 가리켜야 한다.

- Argo CD CLI로 수동 Sync할 수 있도록 Login이 완료되어야 한다.

- GitHub에 Push할 `bgd` Repository가 준비되어 있어야 한다.

```bash
kubectl config current-context
kubectl get nodes
kubectl get applications -n argocd
argocd account get-user-info
```

명령은 Argo CD가 설치된 Server에서만 실행해야 하는 것이 아니다. 대상 Cluster의 Kubernetes API와 Argo CD API에 접근할 수 있고 필요한 인증 정보가 설정된 환경이면 실행할 수 있다.

## 2 ) Namespace Manifest

---

`manifest/ns.yaml`을 작성한다.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: bgd
```

Deployment와 Service는 `bgd` Namespace에 생성되는 namespaced Resource이다. Namespace Manifest를 같은 Source에 두면 Argo CD가 전체 Resource를 동기화할 때 Namespace도 Desired State로 관리한다.

## 3 ) Deployment Manifest

---

`manifest/deployment.yaml`을 작성한다. `<dockerhub-username>`은 실제 Image를 Push한 Docker Hub 계정으로 바꾼다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bgd
  namespace: bgd
  labels:
    app: bgd
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bgd
  template:
    metadata:
      labels:
        app: bgd
    spec:
      containers:
        - name: bgd
          image: docker.io/<dockerhub-username>/bgd:1.0.0
          env:
            - name: COLOR
              value: "blue"
```

`spec.selector.matchLabels`와 `spec.template.metadata.labels`는 모두 `app: bgd`로 일치해야 한다. Deployment Controller는 이 Label을 이용해 자신이 관리할 Pod를 식별한다. Selector는 Deployment를 생성한 뒤 변경할 수 없으므로 이름만 비슷하게 두지 말고 실제 Key와 Value가 일치하는지 확인한다.

Manifest 생성 도구의 출력에 나타날 수 있는 `creationTimestamp: null`, `strategy: {}`와 `resources: {}`는 이 실습에서 필요한 설정이 아니다. API Server가 관리하거나 기본값을 적용하는 Field이므로 학습용 선언에서는 제외한다.

## 4 ) Service Manifest

---

`manifest/svc.yaml`을 작성한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: bgd
  namespace: bgd
  labels:
    app: bgd
spec:
  type: NodePort
  selector:
    app: bgd
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
      nodePort: 31080
```

| Field | 역할 |
|---|---|
| `selector` | `app: bgd` Label을 가진 Pod를 Service Endpoint로 선택 |
| `port` | Cluster 내부에서 Service가 제공하는 Port |
| `targetPort` | 선택된 Pod의 Application으로 전달할 Port |
| `nodePort` | Node IP를 통해 외부에서 접근할 고정 Port |

`31080`은 Kubernetes의 기본 NodePort 범위인 `30000-32767` 안에 있지만 다른 Service가 이미 사용 중이면 생성이 거절된다. 고정 번호가 필요하지 않다면 `nodePort`를 생략하고 Control Plane이 할당한 값을 조회할 수 있다. NodePort의 현재 동작과 Port 범위는 [Kubernetes Service 공식 문서](https://kubernetes.io/docs/concepts/services-networking/service/#type-nodeport)에서 확인할 수 있다.

## 5 ) Manifest 검증과 GitHub Push

---

Repository Root에서 YAML 문법과 Kubernetes Resource 변환 결과를 먼저 확인한다.

```bash
kubectl apply \
  --dry-run=client \
  --filename manifest/ \
  --output yaml
```

이 명령은 Local 검증이며 Image가 Registry에 실제로 존재하는지, NodePort가 Cluster에서 사용 중인지까지 확인하지는 않는다.

검증한 Manifest를 Commit하고 GitHub에 Push한다.

```bash
git status
git add manifest/
git diff --staged
git commit -m "deploy: add bgd Kubernetes manifests"
git push origin main
```

Argo CD는 Working Tree의 File을 읽지 않는다. `repoURL`과 `targetRevision`이 가리키는 Remote Repository의 Commit을 기준으로 Desired State를 만든다.

## 6 ) Argo CD Application 작성

---

`bgd-app.yaml`을 작성한다. `<github-owner>`는 실제 Repository Owner로 바꾼다.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: bgd-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<github-owner>/bgd.git
    path: manifest
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: bgd
```

| Field | 값의 의미 |
|---|---|
| `metadata.namespace: argocd` | `Application` CRD가 저장되는 Namespace |
| `source.repoURL` | Desired State를 읽을 Git Repository |
| `source.path` | Repository 안에서 Manifest가 있는 Directory |
| `source.targetRevision` | 추적할 Branch, Tag 또는 Commit |
| `destination.server` | Argo CD와 같은 Kubernetes Cluster의 API 주소 |
| `destination.namespace` | Namespace가 없는 namespaced Manifest에 적용할 기본 대상 |

`destination.namespace`를 적었다고 해서 존재하지 않는 Namespace가 자동으로 만들어지는 것은 아니다. 이 실습에서는 `manifest/ns.yaml`이 `bgd` Namespace를 선언한다. Argo CD Application Field의 전체 구조는 [Application Specification 공식 문서](https://argo-cd.readthedocs.io/en/stable/user-guide/application-specification/)에서 확인할 수 있다.

## 7 ) Application 등록과 초기 상태

---

`Application` Resource를 Cluster에 등록한다.

```bash
kubectl apply --filename bgd-app.yaml
```

Application과 Argo CD가 계산한 Resource 상태를 확인한다.

```bash
kubectl get applications -n argocd
argocd app list
argocd app get bgd-app
kubectl get namespace bgd
```

이 Application에는 `syncPolicy.automated`가 없다. Argo CD가 Git의 Manifest를 읽어 Cluster와 차이를 감지해도 자동으로 적용하지 않는다.

| 표시 | 의미 |
|---|---|
| `OutOfSync` | Git의 Desired State와 Cluster의 Live State가 다름 |
| `Missing` | Git에 선언된 Resource가 Cluster에 아직 없음 |
| `Manual` | 사용자가 Sync를 요청해야 Resource 변경이 적용됨 |

상태 계산에는 Repository 조회와 Reconciliation 시간이 필요하므로 Application을 만든 직후 한 번의 출력만 보고 실패로 판단하지 않는다. `argocd app get bgd-app --refresh`로 Source를 다시 조회한 뒤 상세 Condition을 확인한다.

## 8 ) 수동 Sync 실행

---

수동 Sync를 요청한다.

```bash
argocd app sync bgd-app
```

Sync 요청 후 Workload가 정상 상태에 도달할 때까지 기다린다.

```bash
argocd app wait bgd-app \
  --health \
  --timeout 300
```

수동 정책에서 Sync가 필요한 것은 최초 한 번뿐이 아니다. 이후 Git의 Manifest를 변경해 Push하면 Application은 다시 `OutOfSync`가 되며 사용자가 다시 Sync를 요청해야 한다. Git 변경을 자동 반영하려면 `syncPolicy.automated`를 별도로 선언해야 한다.

## 9 ) Control Plane과 Worker의 동작

---

수동 Sync 명령 이후에는 다음 순서로 상태가 변한다.

1. Argo CD Application Controller가 Git에서 Rendering한 Namespace, Deployment와 Service를 Kubernetes API Server에 전달한다.

2. API Server가 Resource를 검증하고 Cluster State에 저장한다.

3. Deployment Controller가 Deployment의 Desired Replica에 맞는 ReplicaSet과 Pod를 생성한다.

4. Scheduler가 Pod를 실행할 Worker Node를 선택한다.

5. 선택된 Worker의 kubelet이 Container Runtime에 `bgd:1.0.0` Image Pull과 Container 생성을 요청한다.

6. Control Plane의 EndpointSlice Controller가 `app: bgd` Pod를 Service Endpoint로 연결하고, 각 Node의 Service Data Plane이 ClusterIP와 NodePort 전달 경로를 구성한다.

7. Argo CD가 Kubernetes API에서 Live State를 다시 읽어 Sync와 Health 상태를 갱신한다.

Argo CD는 Worker에서 Container를 직접 실행하지 않는다. Argo CD는 Git과 Kubernetes Resource의 차이를 조정하고, 실제 Pod 배치와 실행은 Kubernetes Control Plane과 Worker 구성 요소가 담당한다.

## 10 ) 배포 결과 확인과 문제 진단

---

Argo CD 상태와 Kubernetes Runtime 상태를 함께 확인한다.

```bash
argocd app get bgd-app
kubectl get deployment,pods,service -n bgd -o wide
kubectl get endpointslices -n bgd \
  --label-selector kubernetes.io/service-name=bgd
```

Service Manifest가 `type: NodePort`이므로 조회 결과도 `NodePort`여야 한다. `ClusterIP`로 표시된다면 GitHub에 Push된 `svc.yaml`, Application의 Source Revision과 실제 Live Manifest를 비교한다.

```bash
kubectl get service bgd -n bgd -o yaml
argocd app manifests bgd-app
```

| 증상 | 확인할 내용 |
|---|---|
| Repository 조회 실패 | `repoURL`, Repository 공개 여부와 등록된 Credential |
| Manifest가 표시되지 않음 | `path`, `targetRevision`, Git Push 여부 |
| `OutOfSync` 유지 | Sync Operation 결과와 Application Condition |
| Pod가 `ImagePullBackOff` | Image 이름, Tag, Registry 공개 여부와 Pull Secret |
| Service Endpoint 없음 | Service Selector와 Pod Label, Pod Ready 상태 |
| NodePort 생성 실패 | `31080` 사용 여부와 Cluster NodePort 범위 |

Pod가 생성됐지만 정상 실행되지 않으면 Event와 Log를 확인한다.

```bash
kubectl describe pod -n bgd <pod-name>
kubectl logs -n bgd <pod-name>
kubectl get events -n bgd --sort-by=.lastTimestamp
```

> **최종 정리**
> - 일반 Kubernetes Manifest를 Git Repository에 저장하면 Argo CD가 해당 Directory를 Desired State로 사용한다.
>
> - `Application`은 `argocd` Namespace에 생성되고 Namespace, Deployment와 Service는 배포 대상인 `bgd` Namespace에 생성된다.
>
> - 자동 Sync를 선언하지 않은 Application은 Git 변경을 감지해도 사용자가 Sync를 요청할 때까지 Cluster를 변경하지 않는다.
>
> - `OutOfSync`와 `Missing`은 동기화 전 예상 가능한 상태이며, Sync 이후에는 Argo CD 상태와 Kubernetes Pod·Service 상태를 함께 확인한다.
>
> - Argo CD가 Kubernetes API에 Desired Resource를 전달한 뒤 Control Plane의 Controller·Scheduler와 Worker의 kubelet·Runtime이 실제 Pod 실행을 이어간다.

다음 글인 [Ansible Architecture와 Inventory 구성](/cloud-native-58-ansible-architecture-inventory/)에서는 Control Node가 Inventory와 Playbook을 읽고 SSH로 여러 Managed Node를 자동화하는 구조를 구성한다.
