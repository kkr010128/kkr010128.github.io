---
title: Kubernetes Manifest와 Metadata 관리
description: 여러 Resource를 정의하는 Manifest 구성과 Directory 적용, Label·Annotation, prune, kubectl set과 diff를 이용한 변경 관리 정리
date: 2026-08-26
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Kubernetes Resource가 많아지면 개별 명령을 반복하는 대신 Manifest를 File과 Directory 단위로 관리해야 한다. 여러 Resource를 하나의 Manifest에 정의하거나 여러 File로 분리할 수 있으며, Label과 Annotation을 이용해 Resource를 분류하고 관리 정보를 기록할 수 있다.

## 1 ) Manifest 설계

---

> **Manifest**
>
> Kubernetes API에 생성할 Object의 원하는 상태를 YAML 또는 JSON으로 작성한 File이다.

Kubernetes Manifest의 주요 Field는 다음과 같다.

| Field | 역할 |
|---|---|
| `apiVersion` | Resource가 사용하는 Kubernetes API Version |
| `kind` | Pod, Deployment, Service 등 Resource 종류 |
| `metadata` | 이름, Namespace, Label과 Annotation 등 식별·관리 정보 |
| `spec` | 사용자가 원하는 Resource 상태 |

Control Plane은 Manifest로 전달된 `spec`을 Desired State로 저장한다. Controller와 Scheduler가 이 상태를 관찰하고, Worker의 kubelet이 할당된 Pod를 실제로 실행한다.

```text
Manifest의 spec
      │
      ▼
API Server가 Desired State 저장
      │
      ├── Controller가 Resource 상태 조정
      ├── Scheduler가 Worker 선택
      └── Worker의 kubelet이 Pod 실행
```

## 2 ) 하나의 Manifest에 여러 Resource 정의

---

YAML Document 구분자인 `---`를 사용하면 하나의 File에 여러 Resource를 정의할 수 있다.

다음 내용을 `sample-multi-resource-manifest.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order1-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
    spec:
      containers:
        - name: nginx-container
          image: nginx:1.17
---
apiVersion: v1
kind: Service
metadata:
  name: order2-service
spec:
  type: LoadBalancer
  ports:
    - name: http-port
      protocol: TCP
      port: 8080
      targetPort: 80
  selector:
    app: sample-app
```

| Resource | Control Plane의 처리 | Worker에 미치는 결과 |
|---|---|---|
| Deployment | ReplicaSet과 Pod의 Desired State 관리 | 선택된 Worker에서 Nginx Pod 실행 |
| Service | Label Selector와 Service Port 상태 관리 | 각 Node의 Service Network Rule에 반영 |

Manifest를 적용한다.

```bash
# Master에서 실행
kubectl apply -f sample-multi-resource-manifest.yaml
```

생성 결과를 확인한다.

```bash
kubectl get deployments
kubectl get services
kubectl get pods -l app=sample-app -o wide
```

하나의 File로 함께 관리하면 관련 Resource를 같은 명령으로 적용하고 삭제하기 쉽다.

```bash
kubectl delete -f sample-multi-resource-manifest.yaml
```

### Resource 적용 순서

kubectl은 File의 YAML Document를 읽어 API Server에 요청하지만 전체 File을 하나의 Transaction으로 적용하지 않는다. 앞 Resource가 생성되었다고 해서 실제 Pod가 Ready 상태가 된 후 다음 Resource를 처리하는 것도 아니다.

일부 Resource 요청이 실패하더라도 이미 API Server가 승인한 Resource는 남을 수 있다. 따라서 File에 적힌 순서를 Application 기동 의존성을 보장하는 방법으로 사용하지 않는다.

```text
Deployment 생성 요청 승인
Service 생성 요청 실패
        │
        └── 이미 생성된 Deployment는 자동 Rollback되지 않음
```

Resource 사이에 준비 완료 조건이 필요하면 Readiness Probe, Init Container 또는 `kubectl wait`처럼 상태를 확인하는 구조를 사용한다.

`nginx:1.17`은 고정 Tag를 보여주기 위한 오래된 Image 예시이다. 운영 환경에서는 보안 Update가 제공되는 검증된 Version Tag 또는 Image Digest를 사용한다.

## 3 ) 여러 Manifest File 적용

---

Resource 종류나 Application 구성 단위로 File을 분리할 수 있다.

```text
dir/
├── sample-pod1.yaml
└── sample-pod2.yaml
```

Directory를 생성한다.

```bash
mkdir -p dir
```

다음 내용을 `dir/sample-pod1.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod1
spec:
  containers:
    - name: nginx-container
      image: nginx:1.17
```

다음 내용을 `dir/sample-pod2.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod2
spec:
  containers:
    - name: nginx-container
      image: nginx:1.17
```

Directory 안의 Manifest를 적용한다.

```bash
kubectl apply -f ./dir
```

Pod를 확인한다.

```bash
kubectl get pods sample-pod1 sample-pod2
```

### 하위 Directory 재귀 적용

`-f`로 지정한 Directory의 하위 Directory까지 적용하려면 `-R` 또는 `--recursive`를 사용한다.

```bash
kubectl apply -f ./dir -R
```

| Option | 역할 |
|---|---|
| `-f`, `--filename` | 적용할 File 또는 Directory 지정 |
| `-R`, `--recursive` | 지정한 Directory 아래를 재귀적으로 탐색 |

File 이름의 번호를 Resource 준비 순서를 보장하는 장치로 사용하지 않는다. Kubernetes Resource는 API 요청 후 Controller가 비동기로 상태를 조정하므로 File 처리 순서와 Application 준비 완료 순서는 다를 수 있다.

### Directory 분리 기준

규모에 따라 다음 방식으로 구성할 수 있다.

- 작은 System은 관련 Manifest를 하나의 Directory에 모은다.

- 규모가 커지면 Subsystem이나 운영 Team 단위로 Directory를 나눈다.

- Microservice별 Directory를 만들고 Deployment, Service와 설정 Resource를 함께 둔다.

- 여러 Application이 공유하는 ConfigMap이나 공통 정책은 별도 Directory로 분리한다.

Directory가 지나치게 세분화되면 어떤 Resource를 함께 적용해야 하는지 파악하기 어려울 수 있다. 반대로 모든 Resource를 하나의 File에 모으면 변경 충돌과 검토 범위가 커진다. 배포·Rollback·소유권 단위를 기준으로 분리한다.

## 4 ) Label과 Annotation

---

Kubernetes Resource에는 Label과 Annotation 형태의 Metadata를 추가할 수 있다.

| 구분 | Label | Annotation |
|---|---|---|
| 목적 | Resource 분류, 선택과 검색 | 설명, 도구 설정, Build 정보 등 비식별 Metadata 저장 |
| Selector 지원 | 지원 | 지원하지 않음 |
| 값의 형태 | 길이와 문자 구성이 제한된 String | 문자열이며 공백·특수 문자와 구조화된 Text 저장 가능 |
| 대표 사용 | Application, 환경, Tier, 관리 대상 구분 | 담당자, 배포 Revision, 외부 도구 설정 |

### Label

> **Label**
>
> Resource를 분류하고 Selector로 Resource 집합을 선택하기 위한 Key-Value Metadata이다.

다음 내용을 `sample-label-pod.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-label-pod
  labels:
    app: sample-app
    environment: development
spec:
  containers:
    - name: nginx-container
      image: nginx
```

적용 후 Label을 확인한다.

```bash
kubectl apply -f sample-label-pod.yaml
kubectl get pods --show-labels
```

Label Selector로 Pod를 조회한다.

```bash
kubectl get pods -l app=sample-app
```

여러 조건을 쉼표로 연결하면 모든 조건을 만족하는 Resource를 선택한다.

```bash
kubectl get pods -l app=sample-app,environment=development
```

Label Key는 선택적인 DNS Prefix와 `/`, 필수 Name Segment로 구성할 수 있다. Name Segment와 Label Value는 각각 63자 이하이며, Prefix를 사용하면 DNS Subdomain 형식으로 최대 253자까지 사용할 수 있다.

```text
example.com/application
─────────── ───────────
   Prefix       Name
```

### Annotation

> **Annotation**
>
> Selector로 분류할 필요는 없지만 Resource와 함께 보존해야 하는 추가 정보를 기록하는 Metadata이다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-annotation-pod
  annotations:
    description: "Nginx 학습용 Pod"
    build.example.com/revision: "2026-08-26.1"
spec:
  containers:
    - name: nginx-container
      image: nginx
```

Annotation의 Key와 Value는 문자열이어야 한다. 모든 Annotation Key와 Value를 합한 크기는 한 Object에서 256KiB를 넘을 수 없다.

Label에는 Selector에 사용할 간단한 식별값을 넣고, 긴 설명이나 도구가 사용하는 설정은 Annotation에 넣는다.

## 5 ) prune을 이용한 Resource 정리

---

Git에서 Manifest를 삭제한 뒤 `kubectl apply -f`만 다시 실행하면 Cluster의 기존 Resource가 자동으로 삭제되지는 않는다.

```text
Git Directory                         Kubernetes Cluster
├── sample-pod1.yaml                  ├── sample-pod1
└── sample-pod2.yaml                  └── sample-pod2

sample-pod2.yaml 삭제 후 apply

Git Directory                         Kubernetes Cluster
└── sample-pod1.yaml                  ├── sample-pod1
                                      └── sample-pod2  ← 그대로 남음
```

명시적으로 삭제하는 방법이 가장 이해하기 쉽다.

```bash
kubectl delete -f prune/sample-pod2.yaml
```

삭제된 Manifest가 더 이상 없어서 File 기반 삭제를 사용할 수 없다면 Resource 종류와 이름 또는 Label을 지정한다.

```bash
kubectl delete pod sample-pod2
```

### prune 실습 Manifest

Directory를 생성한다.

```bash
mkdir -p prune
```

다음 내용을 `prune/sample-pod1.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod1
  labels:
    system: a
spec:
  containers:
    - name: nginx-container
      image: nginx:1.17
```

다음 내용을 `prune/sample-pod2.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod2
  labels:
    system: a
spec:
  containers:
    - name: nginx-container
      image: nginx:1.17
```

두 Resource를 적용한다.

```bash
kubectl apply -f ./prune
kubectl get pods -l system=a
```

`sample-pod2.yaml`을 Directory에서 제거한 뒤 일반 `apply`를 실행한다.

```bash
rm prune/sample-pod2.yaml
kubectl apply -f ./prune
kubectl get pods -l system=a
```

일반 `apply`만으로는 `sample-pod2`가 삭제되지 않는다.

### apply --prune

`--prune`은 이전에 `apply`로 관리하던 Resource 중 현재 Manifest 집합에 포함되지 않은 대상을 삭제한다.

Kubernetes `v1.36` 기준 기존 Allowlist 기반 `--prune`과 ApplySet 기반 방식은 모두 Alpha 상태이다. 삭제 범위를 잘못 지정하면 예상하지 않은 Resource가 제거될 수 있으므로 운영 환경에서는 명시적인 `kubectl delete -f`를 우선한다.

실습에서 Pod와 `system=a` Label로 범위를 제한한다.

```bash
kubectl apply -f ./prune \
  --prune \
  -l system=a \
  --prune-allowlist=core/v1/Pod
```

| Option | 역할 |
|---|---|
| `--prune` | 현재 Manifest 집합에 없는 기존 관리 Resource 삭제 |
| `-l system=a` | 삭제 검토 대상을 해당 Label Resource로 제한 |
| `--prune-allowlist=core/v1/Pod` | Prune할 Group, Version과 Kind를 Pod로 제한 |

`--prune`은 관리 대상 전체가 들어 있는 Root Directory에서 실행한다. 일부 Subdirectory만 대상으로 실행하면 다른 Directory에 있는 정상 Resource가 누락된 것으로 판단될 수 있다.

실습 결과를 확인한다.

```bash
kubectl get pods -l system=a
```

실습 Resource를 명시적으로 정리한다.

```bash
kubectl delete pods -l system=a
```

## 6 ) Resource 일부 정보 변경

---

`kubectl set`은 Resource의 특정 Field를 명령형으로 변경한다.

| 하위 명령 | 변경 대상 |
|---|---|
| `set env` | 환경 변수 |
| `set image` | Container Image |
| `set resources` | Resource Request와 Limit |
| `set selector` | Resource Selector |
| `set serviceaccount` | Pod Template의 ServiceAccount |
| `set subject` | RoleBinding과 ClusterRoleBinding의 Subject |

다음 내용을 `sample-deployment.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
    spec:
      containers:
        - name: nginx-container
          image: nginx
```

Manifest를 적용한다.

```bash
kubectl apply -f sample-deployment.yaml
```

독립 Pod의 Image도 Container 이름을 지정하여 변경할 수 있다.

```bash
kubectl set image pod/sample-label-pod \
  nginx-container=nginx:stable
```

독립 Pod는 Rollout과 Replica 유지 기능이 없으므로 Application Workload는 일반적으로 Deployment 같은 Controller로 관리한다.

Deployment가 사용하는 Image를 변경한다.

```bash
kubectl set image deployment/sample-deployment \
  nginx-container=nginx:stable
```

Image 변경으로 Deployment Rollout이 시작된다. Control Plane의 Deployment Controller가 새 ReplicaSet을 만들고 Worker에서는 새 Image를 사용하는 Pod가 실행된다.

```bash
kubectl rollout status deployment/sample-deployment
```

### Manifest와 실제 상태 차이 확인

명령형으로 변경한 Cluster 상태와 Local Manifest의 차이를 확인한다.

```bash
kubectl diff -f sample-deployment.yaml
```

`kubectl diff`는 실제 변경을 적용하지 않고 `apply` 시 변경될 내용을 미리 보여준다. 운영 환경에서는 변경 전 Diff를 검토하고 Manifest에 의도한 값을 반영한 뒤 `apply`하는 방식이 적합하다.

```bash
kubectl apply -f sample-deployment.yaml
```

명령형 `set`으로 긴급 변경한 뒤 Manifest를 갱신하지 않으면 다음 `apply`에서 값이 이전 선언으로 돌아갈 수 있다.

## 7 ) 사용 가능한 Resource 종류 확인

---

현재 API Server가 제공하는 Resource 종류를 확인한다.

```bash
kubectl api-resources
```

Namespace에 속하는 Resource만 확인한다.

```bash
kubectl api-resources --namespaced=true
```

Cluster 전체 범위 Resource만 확인한다.

```bash
kubectl api-resources --namespaced=false
```

출력에는 Resource 이름, 축약 이름, API Version, Namespace 적용 여부와 Kind가 포함된다. Manifest의 `apiVersion`과 `kind`를 확인하거나 `kubectl get`에 사용할 Resource 이름을 찾을 때 활용한다.

## 전체 정리

---

> **최종 정리**
>
> - Manifest는 Kubernetes Object의 Desired State를 기록하며 여러 Resource를 `---`로 구분해 한 File에 작성할 수 있다.
>
> - 여러 Resource 적용은 하나의 Transaction이 아니며 File 순서가 Application 준비 완료 순서를 보장하지 않는다.
>
> - 여러 Manifest는 Directory 단위로 적용할 수 있고 `-R`을 사용하면 하위 Directory까지 재귀적으로 처리한다.
>
> - Label은 Resource 선택과 분류에 사용하고 Annotation은 Selector가 필요 없는 추가 Metadata를 저장한다.
>
> - `apply --prune`은 삭제 범위에 따라 정상 Resource를 제거할 수 있는 Alpha 기능이므로 Label과 Allowlist로 범위를 제한하고 명시적 삭제를 우선한다.
>
> - `kubectl set`으로 변경한 값은 Manifest에도 반영하고 `kubectl diff`로 실제 상태와 선언 상태를 비교한다.
