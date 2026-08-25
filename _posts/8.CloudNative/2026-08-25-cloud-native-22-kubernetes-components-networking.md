---
title: Kubernetes Component와 Service Network
description: Control Plane과 Worker Component의 동작 흐름, Controller 종류, Service와 Pod Network 및 CNI 구조
date: 2026-08-25
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
  - Network
---

Kubernetes에서 사용자가 선언한 Pod가 실행되기까지 Control Plane과 Worker의 여러 Component가 역할을 나누어 동작한다. Pod가 실행된 후에는 Service가 변하는 Pod 집합에 안정적인 Endpoint를 제공하고 CNI 기반 Pod Network가 Node를 넘어 통신할 수 있게 한다.

## 1 ) Kubernetes Component 배치

---

Control Plane은 Cluster 전체의 상태와 Scheduling을 관리하고 Worker는 할당된 Pod를 실행한다.

```text
Control Plane
├── kube-apiserver
├── etcd
├── kube-scheduler
└── kube-controller-manager

Worker Node
├── kubelet
├── Container Runtime
├── kube-proxy 또는 Service Proxy 구현
└── CNI 기반 Pod Network
```

| Component | 주요 실행 위치 | 역할 |
|---|---|---|
| kubectl | 관리 Client | API Server에 요청 전달 |
| kube-apiserver | Control Plane | Kubernetes API 제공, 요청 인증·인가·검증 |
| etcd | Control Plane | Cluster 상태 저장 |
| kube-scheduler | Control Plane | Scheduling되지 않은 Pod의 실행 Node 선택 |
| kube-controller-manager | Control Plane | 여러 Controller의 Reconciliation Loop 실행 |
| kubelet | 모든 Node | 자신에게 할당된 Pod 실행 상태 유지 |
| Container Runtime | 모든 Node | Image와 Container 실행 관리 |
| kube-proxy | 일반적으로 각 Node | Service용 Network Rule 관리 |

## 2 ) kubectl과 API Server

---

### kubectl

`kubectl`은 Kubernetes API를 호출하는 Command Line Client이다. 독립된 Binary이므로 반드시 Control Plane Node에서 실행할 필요는 없다.

다음 정보가 담긴 Kubeconfig가 있으면 별도 관리 PC나 다른 Node에서도 사용할 수 있다.

- API Server 주소

- Cluster 인증서 정보

- 사용자 인증 정보

- Namespace와 Context

```bash
kubectl config current-context
kubectl cluster-info
kubectl get nodes
```

### kube-apiserver

API Server는 Kubernetes Control Plane의 Frontend이다. kubectl, Controller, Scheduler, kubelet과 외부 Client는 API Server를 통해 Cluster 상태를 조회하거나 변경한다.

주요 역할은 다음과 같다.

- 요청한 사용자를 인증한다.

- RBAC 등으로 요청 권한을 확인한다.

- Resource 형식과 정책을 검증한다.

- Admission Control을 적용한다.

- 유효한 Resource 상태를 etcd에 저장하고 Client에 응답한다.

API Server가 Worker의 kubelet에 Container 생성 명령을 직접 전달하는 구조는 아니다. 각 Component가 API Server를 중심으로 원하는 상태와 현재 상태를 관찰하고 자신의 역할을 수행한다.

## 3 ) etcd, Scheduler와 Controller Manager

---

### etcd

etcd는 Kubernetes Cluster의 상태 정보를 저장하는 분산 Key-value Database이다.

- Pod, Deployment, Service와 Node 같은 Resource의 선언 상태를 저장한다.

- Control Plane Component는 API Server를 통해 Cluster 상태를 읽고 갱신한다.

- 운영 환경에서는 etcd Backup과 복구 절차가 Cluster 복구의 핵심이 된다.

API Server가 Pod Object를 etcd에 저장했다고 해서 Container가 이미 실행된 것은 아니다. 저장된 PodSpec을 Scheduler와 kubelet이 관찰하고 후속 작업을 수행해야 실제 Container가 실행된다.

### kube-scheduler

Scheduler는 아직 Node가 정해지지 않은 Pod를 관찰하고 실행할 Node를 선택한다.

주요 판단 요소는 다음과 같다.

- Node의 가용 CPU와 Memory

- Pod의 Resource Request

- Node Selector와 Node Affinity

- Taint와 Toleration

- Pod Affinity와 Anti-affinity

- Volume과 Topology 조건

Scheduler는 Container를 직접 실행하지 않는다. 선택한 Node 정보를 Pod에 Binding하면 해당 Worker의 kubelet이 Pod 실행을 담당한다.

### kube-controller-manager

Controller Manager는 여러 Controller를 하나의 Process에서 실행한다. Controller는 선언된 상태와 실제 상태를 반복해서 비교하고 필요한 변경을 수행한다.

```text
선언 상태: Replica 3개
실제 상태: Pod 2개
        │
        ▼
Controller가 차이 감지
        │
        ▼
새 Pod Object 생성
```

Controller는 Resource를 지속적으로 관찰하고 장애나 변경으로 상태 차이가 생기면 Reconciliation을 수행한다.

## 4 ) Worker의 kubelet과 Container Runtime

---

### kubelet

kubelet은 각 Node에서 실행되는 Agent이다. API Server를 통해 자신에게 할당된 PodSpec을 확인하고 Container Runtime을 사용하여 Pod의 Container가 실행되도록 한다.

주요 역할은 다음과 같다.

- Pod에 필요한 Image와 Container 실행 요청

- Volume Mount

- Liveness, Readiness와 Startup Probe 실행

- Pod와 Node 상태를 API Server에 보고

- 실패한 Container의 Restart Policy 적용

kubelet은 자신이 관리하도록 할당된 Pod를 대상으로 동작하며 Kubernetes 밖에서 별도로 실행한 Container를 일반적인 Pod처럼 관리하지 않는다.

### Container Runtime

Container Runtime은 kubelet의 요청을 CRI를 통해 받아 Image를 준비하고 Container를 실행한다. containerd와 CRI-O가 대표적인 CRI Runtime이다.

### Pod 생성 흐름

Deployment를 생성했을 때 Master와 Worker의 동작을 순서대로 보면 다음과 같다.

```text
1. kubectl이 Deployment Manifest를 API Server에 전달
2. API Server가 인증·인가·검증 후 상태 저장
3. Deployment Controller가 ReplicaSet 생성
4. ReplicaSet Controller가 필요한 Pod Object 생성
5. Scheduler가 Pod를 실행할 Worker 선택
6. 선택된 Worker의 kubelet이 PodSpec 확인
7. Container Runtime이 Image를 준비하고 Container 실행
8. CNI Plugin이 Pod Network 구성
9. kubelet이 Pod 상태를 API Server에 보고
```

Control Plane은 상태를 저장하고 배치를 결정하며 Worker는 실제 Container와 Network를 구성한다.

## 5 ) kube-proxy와 Service 구현

---

kube-proxy는 Kubernetes Service 개념의 일부를 구현하는 Network Proxy이다. 일반적으로 각 Node에서 실행되며 Service의 Virtual IP와 Port로 들어온 Traffic을 Backend Pod로 전달할 수 있도록 Network Rule을 관리한다.

구현 방식에는 iptables, IPVS와 nftables 기반 Mode가 사용될 수 있다. 일부 CNI는 자체 Service Proxy 기능으로 kube-proxy를 대체할 수 있으므로 kube-proxy는 모든 Cluster에 반드시 존재하는 Component는 아니다.

kubeadm 기반 Cluster에서는 일반적으로 kube-proxy가 DaemonSet으로 배포된다.

```bash
kubectl get daemonsets -n kube-system
kubectl get pods -n kube-system -o wide
```

## 6 ) Kubernetes Controller

---

Controller는 Pod를 직접 나열하여 수동 관리하는 대신 Workload의 원하는 상태를 선언하게 한다.

### ReplicaSet

ReplicaSet은 Label Selector와 일치하는 Pod가 지정한 수만큼 실행되도록 유지한다. ReplicaSet이 관리하는 동일 구성의 Pod를 Replica라고 한다.

일반적으로 ReplicaSet을 직접 만들기보다 Deployment를 통해 관리한다.

### Deployment

Deployment는 Stateless Application을 배포할 때 가장 일반적으로 사용하는 Workload Resource이다.

- ReplicaSet과 Pod를 관리한다.

- Rolling Update와 Rollback을 제공한다.

- Replica 수를 변경하여 Scaling할 수 있다.

### DaemonSet

DaemonSet은 조건에 맞는 각 Node에 Pod가 하나씩 실행되도록 관리한다. Node가 추가되면 해당 Node에도 Pod를 배치한다.

주요 사용 사례는 다음과 같다.

- Log Collector

- Node Monitoring Agent

- CNI와 Storage의 Node Agent

### StatefulSet

StatefulSet은 순서와 고유한 식별자가 필요한 Stateful Application을 관리한다.

- `pod-name-0`, `pod-name-1`과 같은 안정적인 Pod 이름을 유지한다.

- 순서가 있는 배포와 Scaling을 제공한다.

- VolumeClaimTemplate으로 Pod별 PersistentVolumeClaim을 생성할 수 있다.

Pod가 다시 Scheduling되어도 논리적 식별자는 유지되지만 Data 보존 여부는 연결한 Persistent Storage에 달려 있다.

### Job과 CronJob

Job은 지정한 작업이 성공적으로 완료되도록 하나 이상의 Pod를 실행한다. CronJob은 Schedule에 따라 Job을 반복 생성한다.

| Controller | 목적 | 대표 사례 |
|---|---|---|
| ReplicaSet | 지정한 Pod 수 유지 | Deployment의 하위 Controller |
| Deployment | Stateless Application 배포 | Web API, Frontend |
| DaemonSet | 각 Node에 Pod 실행 | Log·Monitoring Agent |
| StatefulSet | 식별자와 Storage가 필요한 Workload | Database, Message Broker |
| Job | 완료형 작업 | Batch, Migration |
| CronJob | 예약된 Job 실행 | Backup, 정기 Report |

## 7 ) Kubernetes Service

---

Pod는 장애 복구, Scaling과 Update 과정에서 생성되고 삭제되며 IP Address도 변경될 수 있다. Service는 Label Selector로 Pod 집합을 선택하고 Client가 사용할 안정적인 IP Address와 DNS 이름을 제공한다.

```text
Client
  │
  ▼
Service: web
  ├── Pod: web-a  10.244.1.10
  ├── Pod: web-b  10.244.2.11
  └── Pod: web-c  10.244.2.12
```

Pod가 여러 Worker에 나뉘어 있어도 하나의 Service가 같은 Label의 Pod를 Backend로 관리할 수 있다. EndpointSlice에는 Service가 전달할 Pod Endpoint가 기록된다.

### Service Type

| Type | 접근 범위 | 특징 |
|---|---|---|
| `ClusterIP` | Cluster 내부 | 기본 Type, Cluster 내부 Virtual IP 제공 |
| `NodePort` | Cluster 외부 | 각 Node의 지정 Port로 Service 공개 |
| `LoadBalancer` | 외부 Load Balancer | Cloud Provider 또는 Load Balancer 구현과 연동 |
| `ExternalName` | 외부 DNS 이름 | DNS CNAME으로 외부 FQDN 연결 |

#### ClusterIP

Cluster 내부 Client가 Service 이름이나 ClusterIP를 사용하여 Backend Pod에 접근한다.

#### NodePort

각 Node의 IP Address와 할당된 Port를 통해 Service를 외부에 공개한다. 기본 NodePort 범위는 `30000`~`32767`이다.

#### LoadBalancer

Cloud Provider나 Load Balancer Controller가 외부 Load Balancer를 구성하고 Service에 External IP 또는 Hostname을 제공한다. 지원 여부와 동작은 Cluster 환경에 따라 달라진다.

#### ExternalName

Service DNS 이름을 외부 FQDN의 CNAME으로 연결한다. Pod Proxy나 ClusterIP를 생성하는 방식과 다르다.

### 그 밖의 Service 구성

- External IP는 Cluster 관리자가 지정한 외부 IP로 들어온 Traffic을 Service에 연결하는 설정이다.

- Headless Service는 `clusterIP: None`으로 설정하여 단일 Virtual IP 대신 개별 Endpoint의 DNS 정보를 제공한다.

- Selector가 없는 Service는 Kubernetes 밖의 Backend나 수동으로 관리하는 EndpointSlice와 연결할 수 있다.

## 8 ) Ingress

---

Ingress는 HTTP와 HTTPS의 Hostname 및 Path 기반 Routing 규칙을 정의하는 Resource이다. Ingress Object만 생성해서는 Traffic이 처리되지 않으며 Cluster에 Ingress Controller가 필요하다.

```text
Client
  │
  ▼
Ingress Controller
  ├── app.example.com/api  → api Service
  └── app.example.com/web  → web Service
```

Ingress Controller는 일반적으로 Cluster의 Pod와 Service로 배포되지만 환경에 따라 외부 Load Balancer와 연동할 수 있다. 별도의 전용 Hardware나 Cluster 밖 Node에서만 실행되는 것은 아니다.

Ingress는 주로 HTTP·HTTPS Routing을 담당한다. 더 다양한 Protocol과 Traffic 관리 기능에는 Service Type과 Gateway API 등을 함께 검토한다.

## 9 ) Pod Network

---

Kubernetes Network Model의 기본 원칙은 다음과 같다.

- 각 Pod는 Cluster 전체에서 고유한 IP Address를 가진다.

- 같은 Pod의 Container는 하나의 Network Namespace와 Pod IP를 공유한다.

- 같은 Pod의 Container는 서로 다른 Port를 사용하며 `localhost:PORT`로 통신할 수 있다.

- Network Policy로 제한하지 않았다면 같은 Node와 다른 Node의 Pod가 서로 직접 통신할 수 있어야 한다.

- Node의 Agent는 해당 Node의 Pod와 통신할 수 있어야 한다.

### Pod 내부 통신

하나의 Pod에 Application Container와 Sidecar Container가 있으면 두 Container의 IP Address는 같다. 같은 Port를 동시에 사용할 수 없으므로 서로 다른 Port를 열고 `localhost`로 통신한다.

```text
Pod 10.244.1.10
├── Application :8080
└── Sidecar     :15000

Application → localhost:15000
```

### Node와 Pod Network

Node는 Host Network의 IP Address를 사용하고 Pod는 CNI가 구성한 Pod Network의 IP Address를 사용한다. Pod CIDR은 Cluster와 CNI 설정에 따라 달라지며 항상 특정 `172.x.x.x` 대역을 사용하는 것은 아니다.

```text
Physical or VM Network
├── Worker 1: 192.168.0.101
│   └── Pod Network: 10.244.1.0/24
└── Worker 2: 192.168.0.102
    └── Pod Network: 10.244.2.0/24
```

Kubernetes Network Model은 다른 Node에 있는 Pod 사이의 통신도 요구한다. 실제 Packet 전달 경로는 설치한 CNI 기반 Network 구현이 구성한다.

## 10 ) CNI와 Overlay Network

---

CNI(Container Network Interface)는 Container Runtime이 Network Plugin을 호출하는 Interface 규격이다. Kubernetes Node의 Runtime은 CNI Plugin을 이용하여 다음 작업을 수행한다.

- Pod Network Interface 생성과 삭제

- Pod IP Address 할당과 회수

- Route와 Overlay Network 구성

- Network Namespace 연결

- Plugin에 따라 NetworkPolicy 적용

Overlay Network는 Node의 물리 Network 위에 논리적인 Pod Network를 구성한다. 각 Node의 Pod CIDR가 겹치지 않도록 관리하고 다른 Node의 Pod로 Packet을 전달한다.

### 주요 CNI 기반 Network 구현

| 구현 | 특징 |
|---|---|
| Flannel | 비교적 단순한 Pod Network 구성, VXLAN 등 Backend 제공 |
| Calico | Routing과 NetworkPolicy 기능 제공 |
| Cilium | eBPF 기반 Network, Security와 Observability 제공 |
| Multus | 하나의 Pod에 여러 Network Interface 연결 |

Kubernetes 자체는 하나의 특정 CNI 구현을 강제하지 않는다. Cluster 요구 사항에 따라 NetworkPolicy, 암호화, 성능, 운영 복잡도와 Cloud 연동을 고려하여 선택한다.

## 전체 정리

---

> **최종 정리**
>
> - API Server를 중심으로 Control Plane Component와 Worker Component가 Cluster 상태를 관찰하고 역할을 수행한다.
>
> - Scheduler는 Pod의 Worker를 선택하고 해당 Worker의 kubelet과 Container Runtime이 실제 Container를 실행한다.
>
> - Deployment, DaemonSet, StatefulSet, Job과 CronJob은 목적에 맞는 Pod 상태를 관리한다.
>
> - Service는 변하는 Pod 집합에 안정적인 IP와 DNS Endpoint를 제공하며 Ingress는 HTTP·HTTPS Routing 규칙을 정의한다.
>
> - 같은 Pod의 Container는 Network Namespace를 공유하고 다른 Node의 Pod 통신은 CNI 기반 Pod Network가 구현한다.
