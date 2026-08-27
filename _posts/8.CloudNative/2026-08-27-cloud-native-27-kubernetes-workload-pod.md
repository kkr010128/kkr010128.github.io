---
title: Kubernetes Workload Resource와 Pod
description: Kubernetes Workload Resource의 제어 관계와 Pod 구조, Multi-container Pattern, command·args 및 Network 설정 정리
date: 2026-08-27
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
  - Workload
  - Pod
---

Kubernetes는 Container를 직접 하나씩 관리하는 대신 Pod와 여러 Workload Resource에 원하는 상태를 선언한다. Control Plane의 Controller와 Scheduler는 선언된 상태를 실제 상태와 비교하고, Worker의 kubelet과 Container Runtime은 할당된 Pod의 Container를 실행한다.

## 1 ) Workload Resource

---

> **Workload**
>
> Kubernetes에서 실행되는 Application이다. Workload Resource는 Pod를 직접 또는 Controller를 통해 생성하고 원하는 실행 상태를 유지한다.

주요 Workload Resource와 관계는 다음과 같다.

```text
Pod ◀── ReplicationController
Pod ◀── ReplicaSet ◀── Deployment
Pod ◀── DaemonSet
Pod ◀── StatefulSet
Pod ◀── Job ◀── CronJob
```

| Resource              | 역할                                      | 대표 사용 사례                       |
| --------------------- | --------------------------------------- | ------------------------------ |
| Pod                   | 하나 이상의 Container를 함께 실행하는 기본 배포 단위      | 단일 실습, 밀접하게 결합된 Container      |
| ReplicationController | 지정한 수의 Pod 유지                           | Legacy 방식의 복제 관리               |
| ReplicaSet            | Label Selector와 일치하는 Pod 수 유지           | Deployment의 하위 Controller      |
| Deployment            | ReplicaSet을 이용한 배포, Update와 Rollback 관리 | Stateless Web Application      |
| DaemonSet             | 조건에 맞는 각 Node에 Pod 실행                   | Log 수집기, Node Monitoring Agent |
| StatefulSet           | 순서와 고유한 식별자가 필요한 Pod 관리                 | Database, Message Broker       |
| Job                   | 완료될 때까지 Pod 실행                          | Batch 작업                       |
| CronJob               | Schedule에 따라 Job 생성                     | 정기 Backup과 점검 작업               |

ReplicationController는 현재도 API에 남아 있는 Legacy Resource이다. 신규 Workload에서는 더 유연한 Label Selector를 지원하는 ReplicaSet을 사용하며, 일반적인 Stateless Application은 ReplicaSet을 직접 만들기보다 Deployment로 관리한다.

## 2 ) Pod

---

> **Pod**
>
> Kubernetes가 생성하고 배치할 수 있는 가장 작은 실행 단위로, 같은 Network와 Storage 자원을 공유하는 하나 이상의 Container로 구성된다.

같은 Pod의 Container는 항상 같은 Node에 함께 배치된다. Container마다 Process와 File System 영역은 구분되지만 Pod의 Network Namespace를 공유하므로 같은 IP Address를 사용하고 `localhost`로 통신할 수 있다.

여러 Container를 한 Pod에 배치하는 기준은 Lifecycle과 배치 관계이다. 서로 독립적으로 Scaling하거나 배포해야 하는 Application은 별도 Pod로 나누고, 항상 함께 실행되며 긴밀하게 협력하는 Container만 같은 Pod에 배치한다.

### Control Plane과 Worker의 동작

Pod Manifest를 적용하면 다음 순서로 실행된다.

```text
Master·관리 Client
  kubectl apply
       │
       ▼
Control Plane
  API Server에 Pod 저장
       │
       ▼
  Scheduler가 Worker 선택
       │
       ▼
Worker
  kubelet이 Pod Spec 확인
       │
       ▼
  Container Runtime이 Container 생성·실행
       │
       ▼
  kubelet이 상태를 API Server에 보고
```

Kubernetes는 Pod의 원하는 상태를 관리하고, 각 Worker의 kubelet은 CRI(Container Runtime Interface)를 통해 Container Runtime에 실행을 요청한다. 대표적인 Runtime은 `containerd`와 `CRI-O`이다. Docker Engine을 kubelet의 Runtime으로 직접 연결하던 내장 `dockershim`은 제거되었으며, Docker Engine을 사용하려면 별도의 CRI Adapter가 필요하다.

### Stateless와 Stateful Application

Stateless Application은 요청을 처리하는 Instance의 Local 상태에 사용자 Session이나 중요한 Data를 계속 보관하지 않는다. Pod가 교체되어도 다른 Replica가 같은 요청을 처리할 수 있도록 필요한 상태를 외부 Database나 Cache 등에 분리한다.

Stateful Application은 Instance별 Data, 순서 또는 고유한 식별자를 유지해야 한다. Database처럼 Data 자체를 관리하는 Application이 대표적이며, Kubernetes에서는 StatefulSet과 Persistent Storage를 조합할 수 있다. 

[StatefulSet의 구체적인 Storage 동작](/cloud-native-29-daemonset-statefulset/)

## 3 ) Multi-container Pod Pattern

---

Pod에 Container가 여러 개 있다는 사실만으로 Sidecar Pattern이 되는 것은 아니다. 보조 Container가 Main Container의 기능을 어떤 방식으로 확장하는지에 따라 Pattern을 구분한다.

| Pattern | 역할 | 통신·공유 방식 | 예시 |
|---|---|---|---|
| Sidecar | Main Container에 보조 기능 추가 | 공유 Volume, `localhost` | Log 수집, 설정 동기화 |
| Ambassador | 외부 System 연결을 대신 중계 | Main Container가 `localhost`로 접근 | Database Proxy, Service Proxy |
| Adapter | Main Container의 Data 형식 변환 | 공유 Volume 또는 Local Network | Metric 형식 표준화 |

### Sidecar Pattern

Sidecar Container는 Main Container 옆에서 보조 기능을 제공한다. 같은 Pod의 Volume을 공유할 수 있으므로 Main Container가 기록한 Data나 설정을 읽어 처리하는 구조에 적합하다.

### Ambassador Pattern

Ambassador Container는 Main Container와 외부 System 사이의 연결을 중계한다. Main Container는 특정 Database 주소에 직접 결합하는 대신 `localhost`의 Ambassador에 접근하고, Ambassador가 실제 목적지 선택이나 연결 처리를 담당한다.

### Adapter Pattern

Adapter Container는 Main Container가 생성한 Data를 외부 System이 요구하는 형식으로 변환한다. Application마다 다른 Metric 형식을 Monitoring System이 수집할 수 있는 공통 형식으로 바꾸는 경우가 대표적이다.

## 4 ) 단일 Container Pod 생성

---

Pod의 기본 구조는 `spec.containers`에 실행할 Container를 배열로 정의하는 형태이다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: <pod-name>
spec:
  containers:
    - name: <container-name>
      image: <container-image>
```

다음 내용을 `sample-pod.yaml`로 저장한다.

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

Master 또는 kubeconfig가 설정된 관리 Client에서 Manifest를 적용한다.

```bash
kubectl apply -f sample-pod.yaml
```

Pod 상태와 배치된 Worker를 확인한다.

```bash
kubectl get pods
kubectl get pod sample-pod -o wide
```

`-o wide`는 Pod IP와 Node 등 기본 출력보다 상세한 Column을 보여 준다.

## 5 ) 두 Container를 포함한 Pod

---

다음 내용을 `sample-2pod.yaml`로 저장하여 Nginx와 Redis Container를 같은 Pod에 배치한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-2pod
spec:
  containers:
    - name: nginx-container
      image: nginx
    - name: redis-container
      image: redis
```

Manifest를 적용하고 Container별 상태를 확인한다.

```bash
kubectl apply -f sample-2pod.yaml
kubectl get pod sample-2pod
kubectl describe pod sample-2pod
```

`READY`가 `2/2`이면 두 Container가 모두 Ready 상태이다. 특정 Container에서 명령을 실행할 때는 `-c` Option을 사용한다.

```bash
kubectl exec pod/sample-2pod \
  -c nginx-container \
  -- /bin/ls /

kubectl exec pod/sample-2pod \
  -c redis-container \
  -- /bin/ls /
```

### 기존 Pod의 Container 구성 변경

다음 `sample-2pod-fail.yaml`은 `sample-2pod`와 같은 이름을 사용하지만 Container의 이름과 구성을 바꾼다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-2pod
spec:
  containers:
    - name: nginx-container1
      image: nginx
    - name: redis-container2
      image: nginx
```

이 Manifest 자체는 유효하므로 `sample-2pod`가 없는 상태에서는 생성된다. 그러나 앞서 만든 Pod에 적용하면 Pod의 Container 구성을 제자리에서 바꿀 수 없기 때문에 변경 불가능한 Field 오류가 발생한다.

```bash
kubectl apply -f sample-2pod-fail.yaml
```

Container 구성을 변경하려면 기존 Pod를 삭제한 뒤 다시 생성하거나, 일반적인 Application에서는 Deployment의 Pod Template을 변경하여 새 Pod로 교체한다.

## 6 ) Container Command 실행

---

Master 또는 관리 Client에서 `kubectl exec`를 실행하면 요청이 API Server와 대상 Worker의 kubelet을 거쳐 Container Runtime에 전달된다.

Nginx Container의 Shell을 연다.

```bash
kubectl exec -it pod/sample-pod -- /bin/sh
```

Container 내부에서 Network와 Process 확인 도구를 설치한다.

```bash
apt update
apt -y install iproute2 procps
ip a
ss -napt | grep LISTEN
```

실행 중인 Container에 Package를 설치한 변경은 Pod가 교체되면 사라진다. 이 방법은 학습과 임시 진단에만 사용하고, 반복해서 필요한 도구는 별도 Debug Image에 포함한다.

Shell에 접속하지 않고 외부에서 단일 Command를 실행할 수 있다.

```bash
kubectl exec pod/sample-pod -- /bin/ls /
kubectl exec pod/sample-2pod -c nginx-container -- /bin/ls /
```

Pipe, Redirection과 Wildcard처럼 Shell 해석이 필요한 문자는 Container의 Shell에 문자열로 전달한다.

```bash
kubectl exec pod/sample-pod -- \
  /bin/sh -c 'ss -napt | grep LISTEN'
```

## 7 ) ENTRYPOINT와 CMD 변경

---

Container Image의 기본 실행 명령을 Pod Manifest에서 덮어쓸 수 있다.

| Dockerfile | Kubernetes Manifest | 역할 |
|---|---|---|
| `ENTRYPOINT` | `spec.containers[].command` | 실행할 Program 지정 |
| `CMD` | `spec.containers[].args` | Program에 전달할 기본 인자 지정 |

다음 내용을 `sample-entrypoint.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-entrypoint
spec:
  containers:
    - name: nginx-container
      image: nginx
      command: ["/bin/sleep"]
      args: ["3600"]
```

Pod를 배포하고 실행 중인 Process를 확인한다.

```bash
kubectl apply -f sample-entrypoint.yaml
kubectl exec -it pod/sample-entrypoint -- /bin/sh
```

Container Shell에서 다음 명령을 실행한다.

```bash
apt update
apt -y install procps
ps aux
```

`nginx` 대신 `/bin/sleep 3600`이 PID 1의 실행 Command로 사용된 것을 확인할 수 있다.

## 8 ) Pod 이름 규칙

---

일반적인 Pod 이름은 DNS Subdomain 규칙을 따른다.

- 영문 소문자와 숫자를 사용할 수 있다.

- `-`와 `.`을 구분 문자로 사용할 수 있다.

- 이름의 시작과 끝은 영문 소문자 또는 숫자여야 한다.

대문자, `_` 또는 구분 문자로 시작하거나 끝나는 이름은 사용할 수 없다.

## 9 ) Host Network 사용

---

기본 Pod는 Worker와 분리된 Network Namespace 및 Cluster 내부 Pod IP를 사용한다. `spec.hostNetwork: true`를 설정하면 Pod가 배치된 Worker의 Network Namespace와 IP Address를 사용한다.

다음 내용을 `sample-hostnetwork.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-hostnetwork
spec:
  hostNetwork: true
  dnsPolicy: ClusterFirstWithHostNet
  containers:
    - name: nginx-container
      image: nginx
```

Pod를 생성하고 Pod IP와 Worker IP를 비교한다.

```bash
kubectl apply -f sample-hostnetwork.yaml
kubectl get pod sample-hostnetwork -o wide
kubectl get nodes -o wide
```

Host Network Pod가 여는 Port는 Worker의 Port를 직접 사용하므로 같은 Worker에서 동일한 Port를 사용하는 다른 Process나 Host Network Pod와 충돌할 수 있다. 운영 환경에서는 반드시 필요한 System Workload에 한해 제한적으로 사용한다.

## 10 ) Working Directory 설정

---

Dockerfile의 `WORKDIR`에 해당하는 Container 작업 Directory는 `spec.containers[].workingDir`로 덮어쓸 수 있다.

다음 내용을 `sample-working-dir.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-working-dir
spec:
  containers:
    - name: nginx-container
      image: nginx
      workingDir: /usr/share/nginx/html
```

Pod를 생성하고 현재 Directory를 확인한다.

```bash
kubectl apply -f sample-working-dir.yaml
kubectl exec pod/sample-working-dir -- pwd
```

## 전체 정리

---

> **최종 정리**
>
> - Kubernetes Workload Resource는 Pod를 직접 또는 Controller 계층을 통해 생성하고 원하는 상태를 유지한다.
>
> - Pod의 Container는 같은 Worker에 배치되고 Network Namespace를 공유하므로 `localhost`로 통신할 수 있다.
>
> - 여러 Container가 있다는 사실만으로 Sidecar가 되는 것은 아니며 보조 기능에 따라 Sidecar, Ambassador와 Adapter Pattern을 구분한다.
>
> - Control Plane은 Pod의 상태와 배치를 결정하고 Worker의 kubelet과 Container Runtime이 실제 Container를 실행한다.
>
> - Pod의 Container 구성은 제자리에서 자유롭게 변경할 수 없으므로 일반적인 Application Update에는 Deployment를 사용한다.
>
> - `command`, `args`, `hostNetwork`와 `workingDir`는 Image의 기본 실행 및 Network 설정을 Pod 수준에서 조정한다.
