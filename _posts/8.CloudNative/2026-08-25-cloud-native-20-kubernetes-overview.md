---
title: Kubernetes 개요와 Architecture
description: Container Runtime과 Orchestration의 개념부터 Kubernetes Resource, Pod, Control Plane과 Worker Node 구조까지 정리
date: 2026-08-25
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Kubernetes는 여러 Node에서 Container Application을 배포하고, 확장하며, 선언한 상태로 유지하는 Container Orchestration Platform이다. Kubernetes를 이해하려면 먼저 Container Runtime이 Application을 실행하는 범위와 Orchestrator가 Cluster를 관리하는 범위를 구분해야 한다.

## 1 ) Container Runtime

---

일반적인 Virtual Machine은 Hardware Resource를 가상화하고 각 Virtual Machine에 Guest OS를 실행한다. Container는 Host OS의 Kernel을 공유하면서 Process, File System과 Network를 격리한다. Guest OS 전체를 실행하지 않으므로 상대적으로 적은 Resource로 더 많은 Application을 실행할 수 있다.

Runtime은 Program이 실행되는 환경을 의미한다. JavaScript가 Browser에서 실행된다면 Browser가 Runtime 역할을 한다. 같은 관점에서 **Container Runtime은 Container Image를 가져오고 Container를 생성·실행·감독하는 Software**이다.

### containerd

containerd는 Container 실행과 Image 관리를 담당하는 Open Source Container Runtime이다.

- Registry에서 Container Image를 내려받는다.

- Image Layer의 압축을 풀고 Local Storage에 관리한다.

- Container를 생성·시작·중지·삭제한다.

- 실행 중인 Container의 상태를 감독한다.

Docker Engine은 내부적으로 containerd를 사용하며 Kubernetes도 CRI Plugin을 갖춘 containerd를 Runtime으로 사용할 수 있다.

### Docker Engine

Docker Engine은 Image Build, Registry 전송, Network, Volume과 Container Lifecycle을 포함한 개발·운영 기능을 제공한다. containerd보다 넓은 범위를 담당하며 내부의 Container 실행 계층에서 containerd를 사용한다.

Kubernetes `v1.20`에서 Docker Engine 연동을 담당하던 Dockershim이 Deprecated되었고 `v1.24`에서 제거되었다. 이는 Docker로 만든 Image를 Kubernetes에서 사용할 수 없다는 의미는 아니다.

```text
Docker Build
    │
    ▼
OCI 호환 Container Image
    │
    ├── containerd
    ├── CRI-O
    └── Docker Engine + cri-dockerd
```

Docker로 Build한 OCI 호환 Image를 Registry에 Push하면 containerd와 CRI-O를 사용하는 Kubernetes Cluster에서도 실행할 수 있다. Docker Engine을 Kubernetes Runtime으로 연결해야 한다면 외부 CRI Adapter인 `cri-dockerd`가 필요하다.

### CRI-O

CRI-O는 Kubernetes의 CRI(Container Runtime Interface)를 구현하기 위해 만들어진 Open Source Runtime이다. Kubernetes에서 OCI 호환 Container를 실행하는 데 필요한 범위에 집중한다.

| 구분 | Docker Engine | containerd | CRI-O |
|---|---|---|---|
| 주요 범위 | Image Build·배포·Container 관리 | Image 관리·Container 실행 | Kubernetes용 Container 실행 |
| Kubernetes 연결 | `cri-dockerd` 필요 | CRI Plugin 사용 | CRI 직접 구현 |
| Image Build | 지원 | 기본 역할 아님 | 기본 역할 아님 |
| 주요 용도 | 개발과 Container Platform 운영 | Docker와 Kubernetes의 Runtime | Kubernetes Runtime |

## 2 ) Container Orchestration

---

Container 수가 많아지고 여러 Machine에 분산되면 개별 명령으로 상태를 관리하기 어렵다. Container Orchestration은 여러 Container를 배치하고 연결하며, 상태를 추적하고, 장애가 발생했을 때 원하는 상태로 복구하는 역할을 수행한다.

주요 기능은 다음과 같다.

- 여러 Node에 Workload를 배치한다.

- Container 장애를 감지하고 대체 실행 단위를 생성한다.

- Replica 수를 조정하여 Application을 확장하거나 축소한다.

- Service Discovery와 Traffic Routing을 제공한다.

- 설정, Secret과 Persistent Storage를 Application에 연결한다.

- 선언한 상태와 실제 상태가 일치하도록 지속적으로 조정한다.

### Orchestration 도구

| 도구 | 특징 |
|---|---|
| Docker Swarm | Docker Engine에 내장되어 구성과 사용이 비교적 단순 |
| Apache Mesos | 분산 System Resource를 관리하며 Framework와 결합하여 사용 |
| Nomad | HashiCorp가 개발한 Orchestrator로 Consul, Vault와 연동 가능 |
| Kubernetes | Container Workload 배포·확장·상태 관리를 위한 CNCF Platform |

Docker Swarm은 작은 Cluster나 Docker 중심 환경에서 비교적 쉽게 시작할 수 있다. Mesos는 분산 Resource 관리 Framework와 다른 System을 함께 구성해야 하며, Nomad는 Consul의 Service Discovery 및 Vault의 Secret 관리와 결합할 수 있다. Kubernetes는 폭넓은 Cloud·Network·Storage 생태계를 갖추고 있다.

## 3 ) Kubernetes

---

Kubernetes는 `K8s`라고도 표기한다. `K`와 `s` 사이의 여덟 글자 `ubernete`를 숫자 `8`로 줄인 표현이다.

Kubernetes에 배포할 Application은 Container 환경에서 독립적으로 실행되고, 외부 설정을 주입받으며, Replica가 교체되어도 Service를 유지할 수 있도록 설계해야 장점을 충분히 활용할 수 있다.

Kubernetes Cluster는 한 대의 Machine으로도 구성할 수 있지만 실제 운영 환경에서는 일반적으로 여러 Node를 사용한다. 각 Node에서 여러 Pod가 실행되며 Kubernetes는 YAML Manifest에 선언한 상태를 기준으로 Pod와 관련 Resource를 생성하고 관리한다.

### Kubernetes를 사용하는 이유

#### 자동화된 Container Orchestration

Scheduler가 Resource와 조건을 확인하여 Pod를 Node에 배치하고 Controller가 선언한 Replica 수를 유지한다.

#### Service 지속성과 Self-healing

Pod나 Container에 장애가 발생하면 Controller와 kubelet이 필요한 복구 작업을 수행한다. Node가 사용할 수 없는 상태가 되면 Controller가 다른 가용 Node에 대체 Pod를 생성할 수 있다.

대체 Pod가 생성되는 것이 기존 Process나 Local Data가 그대로 이동한다는 의미는 아니다. Stateful Application은 Persistent Volume과 Application 수준의 복구 전략이 필요하다.

#### 효율적인 Resource 사용

Container별 CPU와 Memory Request·Limit을 지정할 수 있으며 Scheduler가 가용 Resource를 고려하여 Pod를 배치한다. Service는 변하는 Pod 집합에 안정적인 Endpoint를 제공하고 Ingress 또는 Gateway API는 HTTP·HTTPS Traffic Routing을 구성한다.

#### 유연한 확장

Replica 수를 직접 조정하거나 HorizontalPodAutoscaler를 사용하여 Metric에 따라 Workload를 확장·축소할 수 있다.

#### Desired State 유지

사용자는 YAML Manifest로 원하는 상태를 선언한다. Controller는 실제 Cluster 상태를 관찰하고 필요한 Resource를 생성·수정·삭제하여 두 상태를 일치시킨다.

```text
사용자가 선언한 상태
Deployment Replica: 3
          │
          ▼
Controller가 실제 상태 관찰
          │
          ├── Pod 2개 → Pod 1개 추가
          └── Pod 4개 → Pod 1개 제거
```

#### Infrastructure 선택의 유연성

Kubernetes는 On-premises, Virtual Machine과 여러 Public Cloud에서 사용할 수 있다. 다만 Kubernetes를 사용한다고 Application과 Infrastructure가 자동으로 모든 Cloud Provider에서 동일하게 동작하는 것은 아니다. Load Balancer, Storage와 IAM 같은 Provider별 연동 요소를 함께 고려해야 한다.

## 4 ) Kubernetes Resource

---

Kubernetes에서 상태를 관리하는 대상을 Resource 또는 Object라고 한다. Resource는 API Group과 역할을 기준으로 구분할 수 있다.

| 영역 | 주요 Resource | 역할 |
|---|---|---|
| Workload | Pod, ReplicaSet, Deployment, DaemonSet, StatefulSet, Job, CronJob | Container 실행과 Lifecycle 관리 |
| Service와 Network | Service, EndpointSlice, Ingress, NetworkPolicy | Service Discovery, Traffic 공개와 Network 정책 |
| Config와 Storage | ConfigMap, Secret, PersistentVolumeClaim, PersistentVolume, StorageClass | 설정·기밀 정보와 영속 Storage 관리 |
| Cluster와 접근 제어 | Node, Namespace, ServiceAccount, Role, ClusterRole, RoleBinding, ClusterRoleBinding | Cluster 구성과 RBAC 관리 |
| 정책과 확장 | ResourceQuota, LimitRange, HorizontalPodAutoscaler, PodDisruptionBudget, CustomResourceDefinition | Resource 제한·확장·가용성·API 확장 |

`ReplicationController`도 지원되지만 현재는 일반적으로 ReplicaSet과 Deployment를 사용한다.

`ClusterIP`, `NodePort`, `LoadBalancer`, `ExternalName`은 각각 별도 Resource가 아니라 Service의 `type` 값이다. External IP, Headless Service와 Selector가 없는 Service도 Service를 구성하는 방식이다. Ingress는 Service Type이 아니라 HTTP·HTTPS Routing 규칙을 표현하는 별도 Resource이다.

## 5 ) Kubernetes Architecture

---

Kubernetes Cluster는 Control Plane과 Worker Node로 구성된다. 과거에 Master Node라고 부르던 역할은 현재 문서에서 **Control Plane Node**라고 표현한다. 이 글에서는 처음 역할을 대응할 때 `Master(Control Plane)`로 함께 표기하고 이후에는 Control Plane을 사용한다.

```text
Kubernetes Cluster
├── Control Plane Node
│   ├── kube-apiserver
│   ├── etcd
│   ├── kube-scheduler
│   └── kube-controller-manager
│
├── Worker Node 1
│   ├── kubelet
│   ├── Container Runtime
│   ├── Network 구성 요소
│   └── Pod
│
└── Worker Node 2
    ├── kubelet
    ├── Container Runtime
    ├── Network 구성 요소
    └── Pod
```

### Cluster와 Node

Cluster는 Kubernetes Resource를 함께 관리하는 집합이다. Node는 Pod가 배치되는 Machine이며 물리 Server나 Virtual Machine으로 구성할 수 있다.

| 관점 | Control Plane Node | Worker Node |
|---|---|---|
| 주요 책임 | Cluster 상태와 Scheduling 관리 | 할당된 Pod 실행 |
| 주요 구성 요소 | API Server, etcd, Scheduler, Controller Manager | kubelet, Container Runtime, Network 구성 요소 |
| Application Pod | 기본 kubeadm 구성에서는 일반 Workload Scheduling 제한 | 일반적으로 Application Pod 실행 |
| 장애 영향 | API와 Cluster 관리 기능에 영향 | 해당 Node의 Workload에 영향 |

운영 Cluster에서는 Control Plane을 여러 대로 구성하여 관리 기능의 고가용성을 확보할 수 있다. 학습 환경에서는 Control Plane 한 대와 Worker 두 대로 기본 구조를 확인할 수 있다.

### Pod

Pod는 Kubernetes에서 생성하고 Scheduling할 수 있는 가장 작은 배포 단위이다. 하나 이상의 Container를 포함하며 같은 Pod의 Container는 다음 Resource를 공유한다.

- Pod IP Address와 Network Namespace

- `localhost` Network

- 연결한 Volume

- Pod Lifecycle

같은 Pod에는 Main Application과 그 Application의 동작을 직접 보조하는 Sidecar처럼 **생명주기와 Resource를 밀접하게 공유해야 하는 Container**를 배치한다. Web Application과 Database처럼 독립적으로 확장·배포·복구해야 하는 구성 요소는 일반적으로 서로 다른 Pod와 Workload로 분리한다.

### Persistent Storage

Pod는 교체될 수 있는 Resource이므로 Container Writable Layer에만 저장한 Data는 Pod와 함께 사라질 수 있다. 중요한 Data는 PersistentVolume과 PersistentVolumeClaim을 통해 Pod 외부의 Storage에 저장한다.

CSI(Container Storage Interface)는 Kubernetes가 다양한 Storage System과 연결되는 표준 Interface이다. 실제 Storage는 Local Disk, NFS, Distributed Storage 또는 Cloud Provider의 Block·File Storage가 될 수 있다.

> **최종 정리**
>
> - Container Runtime은 Image와 Container 실행을 담당하고 Kubernetes는 여러 Node의 Workload를 Orchestration한다.
>
> - Dockershim은 제거되었지만 Docker로 Build한 OCI Image는 containerd와 CRI-O 환경에서도 사용할 수 있다.
>
> - Kubernetes는 Desired State, Self-healing, Scheduling, Service Discovery와 Scaling을 제공한다.
>
> - Control Plane은 Cluster 상태와 배치를 관리하고 Worker Node는 실제 Application Pod를 실행한다.
>
> - Pod에는 독립된 Application을 무조건 함께 넣는 것이 아니라 생명주기와 Resource를 공유해야 하는 Container를 배치한다.
