---
title: Kubernetes Namespace와 kubectl 기본 사용
description: Namespace의 분리 범위와 RBAC·NetworkPolicy의 역할부터 Kubeconfig, Context, kubectl을 이용한 Resource 생성·갱신·삭제까지 정리
date: 2026-08-26
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Kubernetes Cluster를 구축한 다음에는 `kubectl`로 API Server에 요청을 보내 Resource를 생성하고 관리한다. 여러 팀이나 Application이 하나의 Cluster를 함께 사용한다면 Namespace로 Resource의 논리적인 범위를 나누고, RBAC와 NetworkPolicy를 결합하여 접근 권한과 Network Traffic을 제어할 수 있다.

## 1 ) Namespace

---

> **Namespace**
>
> 하나의 Kubernetes Cluster 안에서 Resource Group을 논리적으로 구분하는 범위이다. 같은 종류의 Resource 이름은 하나의 Namespace 안에서 고유해야 하지만 서로 다른 Namespace에서는 같은 이름을 사용할 수 있다.

Namespace는 Cluster 자체를 여러 개로 나누는 기능이 아니다. 하나의 Control Plane과 Worker 집합을 공유하면서 Pod, Deployment, Service처럼 Namespace에 속하는 Resource를 구분한다.

```text
Kubernetes Cluster
├── Namespace: development
│   ├── Deployment: web
│   └── Service: web
│
└── Namespace: production
    ├── Deployment: web
    └── Service: web
```

두 Namespace에 같은 이름의 `web` Deployment와 Service가 존재할 수 있다. 그러나 Node, PersistentVolume과 StorageClass처럼 Cluster 전체 범위에서 관리되는 Resource에는 Namespace가 적용되지 않는다.

### 기본 Namespace

Kubernetes Cluster에는 다음 Namespace가 기본으로 존재한다.

| Namespace | 역할 |
|---|---|
| `default` | 별도 Namespace를 지정하지 않았을 때 사용하는 기본 범위 |
| `kube-system` | Control Plane Component와 Cluster Add-on 등 Kubernetes System Resource 배치 |
| `kube-public` | 모든 Client가 읽을 수 있도록 공개할 Resource를 배치하는 범위 |
| `kube-node-lease` | kubelet의 Node Heartbeat를 위한 Lease Resource 저장 |

Master에서 현재 Namespace를 확인한다.

```bash
kubectl get namespaces
```

축약 Resource 이름도 사용할 수 있다.

```bash
kubectl get ns
```

### Namespace 범위 Resource

Namespace에 속하는 Resource와 Cluster 전체 범위 Resource를 확인한다.

```bash
# Namespace에 속하는 Resource
kubectl api-resources --namespaced=true

# Cluster 전체 범위 Resource
kubectl api-resources --namespaced=false
```

Namespace 자체는 특정 Namespace 안에 속하지 않는 Cluster 범위 Resource이다. Namespace를 삭제하면 그 안에 속한 Resource도 함께 삭제되므로 삭제 전에 대상을 확인해야 한다.

## 2 ) Namespace, RBAC와 NetworkPolicy

---

Namespace만 생성했다고 해서 사용자 권한과 Pod Traffic이 자동으로 차단되는 것은 아니다. 분리 목적에 따라 RBAC, ResourceQuota와 NetworkPolicy 같은 Resource를 함께 구성해야 한다.

| 구성 | 제어 대상 | 주요 역할 |
|---|---|---|
| Namespace | Kubernetes Resource의 논리적 범위 | 이름 충돌 방지, 팀·환경·Application 단위 구분 |
| RBAC | Kubernetes API 요청 권한 | 사용자와 ServiceAccount가 조회·생성·변경할 수 있는 Resource 제한 |
| NetworkPolicy | Pod의 Network Traffic | 허용할 Ingress·Egress Traffic 정의 |
| ResourceQuota | Namespace의 Resource 총량 | CPU, Memory와 Resource 개수 제한 |

RBAC(Role-Based Access Control)는 API Server에 전달된 요청의 권한을 검사한다. Namespace 범위의 `Role`과 `RoleBinding`을 사용하면 특정 Namespace 안의 Resource만 조작하도록 권한을 제한할 수 있다.

NetworkPolicy는 Pod 사이의 Network Traffic을 제어한다. NetworkPolicy Resource를 생성하더라도 사용하는 CNI가 NetworkPolicy 적용을 지원해야 실제 Traffic이 제어된다.

```text
사용자 또는 ServiceAccount
        │
        ├── RBAC ────────── API Resource 조작 권한
        │
        ▼
Namespace의 Pod
        │
        └── NetworkPolicy ─ Pod Ingress·Egress Traffic
```

Namespace는 분리의 기준을 제공하고 RBAC와 NetworkPolicy는 그 범위에 맞는 권한과 통신 정책을 적용한다.

## 3 ) kubectl과 Cluster 조작 흐름

---

> **kubectl**
>
> Kubernetes API Server에 Resource 조회·생성·변경·삭제 요청을 보내는 Command Line Client이다.

`kubectl`은 반드시 Master에서만 실행해야 하는 명령이 아니다. API Server 주소와 인증 정보가 담긴 Kubeconfig를 사용할 수 있다면 별도 관리 PC에서도 실행할 수 있다.

이 글의 명령은 앞에서 구축한 학습용 Cluster의 **Master에서 실행**한다. Master에는 `kubeadm init` 후 생성한 Kubeconfig가 설정되어 있다.

```text
Master의 kubectl
        │
        ▼
Control Plane의 kube-apiserver
        │
        ├── 인증·인가·요청 검증
        ├── Resource 상태 저장
        └── Controller·Scheduler가 상태 관찰
                    │
                    ▼
             선택된 Worker의 kubelet
                    │
                    ▼
             Container Runtime이 Pod 실행
```

`kubectl`이 Worker에서 Container를 직접 실행하는 것은 아니다. `kubectl`이 API Server에 원하는 상태를 전달하면 Control Plane Component가 상태를 조정하고, Pod가 배치된 Worker의 kubelet과 Container Runtime이 실제 Container를 실행한다.

## 4 ) Kubeconfig와 Context

---

> **Kubeconfig**
>
> kubectl이 접속할 Cluster, 사용자 인증 정보와 Context를 저장하는 YAML 형식의 설정이다.

Linux에서 kubectl은 기본적으로 다음 File을 사용한다.

```text
~/.kube/config
```

Kubeconfig의 주요 구성은 다음과 같다.

| 구성 | 내용 |
|---|---|
| `clusters` | API Server 주소와 Cluster 인증서 정보 |
| `users` | Client 인증서, Token 등 사용자 인증 정보 |
| `contexts` | Cluster, User와 기본 Namespace의 조합 |
| `current-context` | 현재 kubectl이 기본으로 사용하는 Context |

현재 Context를 확인한다.

```bash
kubectl config current-context
```

Kubeconfig에서 현재 선택된 정보만 확인한다.

```bash
kubectl config view --minify
```

특정 Context를 한 명령에만 적용할 수 있다.

```bash
kubectl get pods --context <context-name>
```

현재 Context를 변경하면 이후 명령에 새 Context가 기본으로 사용된다.

```bash
kubectl config use-context <context-name>
```

특정 Namespace를 한 요청에 지정한다.

```bash
kubectl get pods --namespace kube-system
```

`-n`은 `--namespace`의 축약 Option이다.

```bash
kubectl get pods -n kube-system
```

현재 Context의 기본 Namespace를 변경할 수도 있다.

```bash
kubectl config set-context --current --namespace=default
```

Context의 기본 Namespace를 변경하면 Namespace Option을 생략한 후속 명령에 적용된다. 현재 작업 대상이 어느 Cluster와 Namespace인지 먼저 확인하는 습관이 중요하다.

## 5 ) 명령형 Resource 생성

---

kubectl은 실행 명령에 필요한 값을 직접 전달하는 명령형 방식과 YAML Manifest에 원하는 상태를 기록하는 선언형 방식을 제공한다.

| 방식 | 예시 | 적합한 용도 |
|---|---|---|
| 명령형 Command | `kubectl run`, `kubectl create deployment` | 빠른 Test와 간단한 Resource 생성 |
| 명령형 File 관리 | `kubectl create -f` | Manifest를 이용한 최초 생성 |
| 선언형 File 관리 | `kubectl apply -f` | 반복 적용, 변경 관리와 자동화 |

### kubectl run

가장 간단하게 Pod를 생성한다.

```bash
# Master에서 실행
kubectl run nginx --image=nginx
```

| 인자 | 의미 |
|---|---|
| `nginx` | 생성할 Pod 이름 |
| `--image=nginx` | Container에 사용할 Image |

생성 결과를 확인한다.

```bash
kubectl get pods
```

`kubectl run`은 Test Pod를 빠르게 만들 때 유용하다. 실행에 사용한 Option이 별도 Manifest File로 남지 않으므로 설정이 많아지면 재현과 변경 이력 관리가 어렵다.

### kubectl create

Resource 종류를 지정하여 생성한다.

```bash
kubectl create deployment dpy-nginx --image=nginx
```

Deployment와 Deployment가 관리하는 Pod를 확인한다.

```bash
kubectl get deployments
kubectl get pods
```

Control Plane에는 Deployment와 Pod의 원하는 상태가 저장되고 Scheduler가 Pod를 실행할 Worker를 선택한다. 선택된 Worker의 kubelet이 Container Runtime을 통해 Nginx Container를 실행한다.

## 6 ) Manifest를 이용한 생성과 갱신

---

실제 설정을 반복해서 적용하려면 Manifest File을 작성한다. 다음 내용을 `sample-pod.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod
spec:
  containers:
    - name: nginx-container
      image: nginx
```

### kubectl create -f

Manifest에 정의한 Resource를 생성한다.

```bash
kubectl create -f sample-pod.yaml
```

같은 이름의 Resource가 이미 존재하면 `AlreadyExists` 오류가 발생한다. `create`는 존재하지 않는 Resource의 최초 생성에 사용한다.

### kubectl apply -f

Manifest의 선언 상태를 Cluster에 적용한다.

```bash
kubectl apply -f sample-pod.yaml
```

| 현재 상태 | apply 결과 |
|---|---|
| Resource가 없음 | 새 Resource 생성 |
| Resource가 있고 Manifest가 변경됨 | 변경 사항 적용 |
| 선언 상태에 차이가 없음 | 변경 없이 현재 상태 유지 |

생성과 갱신을 같은 명령으로 처리할 수 있어 Script와 CI/CD에서 조건 분기를 줄일 수 있다. 하나의 Resource를 계속 선언형으로 관리하려면 처음부터 `apply`를 사용하고 Manifest를 Git에서 관리하는 방식이 적합하다.

명령형 Command와 선언형 `apply`를 혼합하면 Cluster의 실제 상태와 저장된 Manifest 사이의 변경 주체를 파악하기 어려워질 수 있다. 운영 방식은 Resource별로 일관되게 유지한다.

## 7 ) Resource 삭제

---

종류와 이름으로 삭제한다.

```bash
kubectl delete pod sample-pod
```

Manifest에 포함된 Resource를 삭제한다.

```bash
kubectl delete -f sample-pod.yaml
```

특정 종류의 모든 Resource를 현재 Namespace에서 삭제하려면 Resource 종류와 `--all`을 함께 지정한다.

```bash
kubectl delete pods --all
```

`kubectl delete --all`처럼 Resource 종류를 생략해서는 삭제 대상을 결정할 수 없다. 또한 `kubectl delete all --all`의 `all`은 일부 대표 Resource를 묶은 Category이므로 Namespace의 모든 Resource 종류를 뜻하지 않는다.

### 삭제 대기

일반적인 `kubectl delete`는 기본적으로 Resource가 삭제될 때까지 기다린다. `--wait`를 명시할 수도 있다.

```bash
kubectl delete -f sample-pod.yaml --wait=true
```

Kubernetes Resource 삭제는 API에서 삭제 요청을 받은 뒤 Graceful Termination과 Finalizer 처리를 거칠 수 있어 즉시 완료되지 않을 수 있다.

### 강제 삭제

Pod를 정상 종료할 수 없는 특별한 상황에는 Grace Period를 `0`으로 설정하고 강제로 삭제할 수 있다.

```bash
kubectl delete pod sample-pod --grace-period=0 --force
```

강제 삭제는 kubelet이 실제 Process 종료를 확인하기 전에 API에서 Pod를 제거할 수 있다. 같은 이름이나 Identity를 사용하는 Process가 동시에 실행되어 Data 불일치가 발생할 수 있으므로 일반적인 삭제 방법으로 사용하지 않는다.

## 전체 정리

---

> **최종 정리**
>
> - Namespace는 하나의 Cluster 안에서 Namespaced Resource의 논리적인 범위와 이름 공간을 구분한다.
>
> - Namespace만으로 사용자 권한과 Pod Traffic이 완전히 격리되지는 않으며 RBAC와 NetworkPolicy 같은 정책을 함께 구성한다.
>
> - kubectl은 Kubeconfig의 Cluster·사용자·Context 정보를 사용하여 API Server에 요청한다.
>
> - Control Plane이 원하는 상태를 저장하고 조정하면 선택된 Worker의 kubelet과 Container Runtime이 실제 Pod를 실행한다.
>
> - 빠른 Test에는 `run`과 `create`, 반복 가능한 선언형 관리에는 Manifest와 `apply`를 사용할 수 있다.
>
> - 강제 삭제는 정상 종료 확인을 생략할 수 있으므로 Data 불일치 위험을 이해한 뒤 제한적으로 사용한다.
