---
title: Kubernetes DaemonSet과 StatefulSet
description: Node별 DaemonSet 배치와 StatefulSet의 순서·고유 식별자·Persistent Storage 및 Database 운영 관점 정리
date: 2026-08-27
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

DaemonSet과 StatefulSet은 서로 다른 배치 조건을 해결하는 Workload Controller이다. DaemonSet은 조건에 맞는 각 Node에 Pod를 배치하고, StatefulSet은 순서와 고유한 Network·Storage 식별자가 필요한 Pod 집합을 관리한다.

## 1 ) DaemonSet

---

> **DaemonSet**
>
> Scheduling 조건을 만족하는 각 Node에 특정 Pod가 하나씩 실행되도록 관리하는 Workload Controller이다.

ReplicaSet은 Cluster 전체에서 지정한 Pod 수를 유지하지만 DaemonSet은 대상 Node마다 Pod를 배치한다. Node가 추가되어 Scheduling 조건을 만족하면 DaemonSet Pod도 자동으로 생성되고, Node가 제거되면 해당 Pod도 함께 정리된다.

DaemonSet은 ReplicaSet의 특수한 형태가 아니라 별도의 Controller Resource이다. 하나의 DaemonSet은 대상 Node마다 Pod 하나를 만들며 `spec.replicas`를 사용하지 않는다.

주요 사용 사례는 다음과 같다.

- Fluentd와 같은 Node별 Log 수집 Agent

- Prometheus Node Exporter와 같은 Node Metric 수집 Agent

- Datadog Agent와 같은 Monitoring Agent

- Network 또는 Storage의 Node Agent

## 2 ) DaemonSet의 배치 흐름

---

DaemonSet Pod가 배치되는 흐름은 다음과 같다.

```text
Control Plane
DaemonSet Controller
  │ 대상 Node와 기존 Pod 확인
  │ 부족한 Node의 Pod 생성
  ▼
Scheduler
  │ Pod가 실행될 Worker 결정
  ▼
Worker의 kubelet
  │ Pod Spec 확인
  ▼
Container Runtime
  │
  ▼
Node별 Agent Container 실행
```

모든 Node에 무조건 배치되는 것은 아니다. Node Label과 다음 Scheduling 조건에 따라 대상 Node를 제한할 수 있다.

| 설정 | 역할 |
|---|---|
| `nodeSelector` | 지정한 Label을 가진 Node만 선택 |
| Node Affinity | 여러 Label 조건으로 포함·제외 규칙 구성 |
| Taint와 Toleration | Taint가 설정된 Node에 배치할 수 있는지 결정 |

Control Plane Node에 일반 Workload를 막는 Taint가 있으면 해당 Taint를 허용하는 Toleration이 없는 DaemonSet Pod는 배치되지 않는다.

## 3 ) DaemonSet 생성

---

다음 내용을 `sample-daemonset.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: prometheus-daemonset
spec:
  selector:
    matchLabels:
      tier: monitoring
      name: prometheus-exporter
  template:
    metadata:
      labels:
        tier: monitoring
        name: prometheus-exporter
    spec:
      containers:
        - name: prometheus
          image: prom/node-exporter
          ports:
            - containerPort: 9100
```

Node Exporter의 기본 Metric Port는 `9100`이다. 이 예제는 DaemonSet의 Node별 배치 확인을 위한 기본 구성이다. 운영 환경에서는 Host의 Metric을 정확히 수집하기 위한 Mount, Namespace와 보안 설정을 별도로 검토해야 한다.

Master 또는 kubeconfig가 설정된 관리 Client에서 Manifest를 적용한다.

```bash
kubectl apply -f sample-daemonset.yaml
```

원하는 Pod 수와 준비된 Pod 수를 확인한다.

```bash
kubectl get daemonsets
kubectl get pods \
  -l tier=monitoring,name=prometheus-exporter \
  -o wide
```

`DESIRED`는 현재 Scheduling 조건에 맞는 Node 수이고 `READY`는 Ready 상태인 DaemonSet Pod 수이다. `-o wide` 출력의 `NODE` Column으로 Node별 배치를 확인한다.

상세 설정과 Event를 확인한다.

```bash
kubectl describe daemonset prometheus-daemonset
```

실습이 끝나면 Manifest를 기준으로 삭제한다.

```bash
kubectl delete -f sample-daemonset.yaml
```

## 4 ) StatefulSet

---

> **StatefulSet**
>
> 순서가 있는 배포와 Scaling, 안정적인 Pod 식별자 및 Pod별 Storage 연결이 필요한 Stateful Workload를 관리하는 Controller Resource이다.

StatefulSet도 ReplicaSet의 특수한 형태가 아니라 별도의 Controller Resource이다. 같은 Pod Template을 사용하더라도 각 Pod를 서로 교환 가능한 Replica로 취급하지 않고 고유한 Ordinal과 식별자를 부여한다.

| 항목 | Deployment | StatefulSet |
|---|---|---|
| Pod 이름 | 임의 Hash와 문자열 사용 | `<statefulset-name>-0`부터 순서대로 부여 |
| Pod 관계 | 서로 교체 가능한 Replica | 각 Pod가 고유한 Identity 보유 |
| Network Identity | 주로 일반 Service로 Pod 집합에 접근 | Headless Service로 Pod별 DNS 제공 |
| Storage | Pod Template에 공통 Volume 정의 가능 | `volumeClaimTemplates`로 Pod별 PVC 생성 가능 |
| 생성·삭제 순서 | 기본적으로 병렬 처리 | 기본값은 순차 처리 |

Pod가 다른 Worker에서 다시 생성되어도 같은 Ordinal 이름과 연결된 PVC를 다시 사용할 수 있다. StatefulSet 자체가 Data를 저장하거나 복제하는 것은 아니며 실제 Data 보존 여부는 PVC가 연결된 PersistentVolume과 Storage System에 달려 있다.

## 5 ) StatefulSet의 Control Plane과 Worker 흐름

---

StatefulSet과 Storage가 연결되는 흐름은 다음과 같다.

```text
Control Plane
StatefulSet Controller
  ├── Headless Service 기반 Network Identity 사용
  ├── Ordinal Pod 생성
  └── volumeClaimTemplates로 Pod별 PVC 생성
                │
                ▼
PV Provisioner 또는 관리자가 PV 제공
                │
                ▼
Scheduler가 Storage 조건을 만족하는 Worker 선택
                │
                ▼
Worker의 kubelet
  ├── Volume Mount 요청
  └── Container Runtime에 Container 실행 요청
```

Pod를 다른 Worker로 다시 Scheduling할 수 있는지는 Storage Backend, Access Mode, Zone과 Volume 연결 조건에 따라 달라진다. PVC가 존재한다는 사실만으로 모든 Worker에서 같은 Data에 접근할 수 있는 것은 아니다.

## 6 ) StatefulSet과 Persistent Storage 생성

---

StatefulSet의 `serviceName`이 가리키는 Headless Service와 StatefulSet을 함께 정의한다. 다음 내용을 `sample-statefulset.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-statefulset
spec:
  clusterIP: None
  selector:
    app: sample-statefulset
  ports:
    - name: http
      port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: sample-statefulset
spec:
  serviceName: sample-statefulset
  replicas: 3
  selector:
    matchLabels:
      app: sample-statefulset
  template:
    metadata:
      labels:
        app: sample-statefulset
    spec:
      containers:
        - name: nginx-container
          image: nginx
          ports:
            - containerPort: 80
          volumeMounts:
            - name: www
              mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
    - metadata:
        name: www
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 1Gi
```

| Field | 역할 |
|---|---|
| Service의 `clusterIP: None` | ClusterIP 없이 Pod별 DNS Record를 제공하는 Headless Service 구성 |
| `spec.serviceName` | StatefulSet의 Network Identity를 관리할 Service 이름 |
| `spec.replicas` | 생성할 StatefulSet Pod 수 |
| `volumeClaimTemplates` | Ordinal Pod마다 별도의 PVC 생성 |
| `accessModes: ReadWriteOnce` | Volume을 하나의 Node에서 Read·Write로 Mount하도록 요청 |
| `storage: 1Gi` | Pod별 PVC가 요청할 Storage 용량 |

Master 또는 관리 Client에서 Resource를 생성한다.

```bash
kubectl apply -f sample-statefulset.yaml
```

StatefulSet, Pod와 PVC를 함께 확인한다.

```bash
kubectl get statefulsets
kubectl get pods -l app=sample-statefulset -o wide
kubectl get persistentvolumeclaims
```

Pod는 기본적으로 `sample-statefulset-0`, `sample-statefulset-1`, `sample-statefulset-2` 순서로 생성된다. 각 Pod에는 `www-sample-statefulset-0`과 같은 별도 PVC가 연결된다.

Default StorageClass나 미리 준비된 PV가 없으면 PVC는 `Pending` 상태에 머물고 Storage를 Mount해야 하는 Pod도 정상 실행되지 않을 수 있다. 이 경우 PVC Event와 StorageClass를 확인한다.

```bash
kubectl describe persistentvolumeclaim www-sample-statefulset-0
kubectl get storageclasses
```

Pod별 DNS와 Volume Mount를 확인한다.

```bash
kubectl exec pod/sample-statefulset-0 -- hostname
kubectl exec pod/sample-statefulset-0 -- \
  df -h /usr/share/nginx/html
```

같은 Namespace에서는 첫 번째 Pod를 `sample-statefulset-0.sample-statefulset`이라는 이름으로 식별할 수 있다. Pod IP가 바뀌어도 StatefulSet의 Ordinal과 Headless Service를 이용한 DNS Identity는 유지된다.

## 7 ) StatefulSet Lifecycle과 Scaling

---

기본 `podManagementPolicy`는 `OrderedReady`이다. Pod를 생성할 때 낮은 Ordinal부터 앞선 Pod가 Ready가 된 뒤 다음 Pod를 생성하고, Scaling Down에서는 높은 Ordinal부터 제거한다.

Replica 수를 5개로 늘리고 순서를 관찰한다.

```bash
kubectl scale statefulset sample-statefulset --replicas=5
kubectl get pods -l app=sample-statefulset --watch
```

Replica 수를 3개로 줄이면 `sample-statefulset-4`, `sample-statefulset-3` 순서로 Pod가 제거된다.

```bash
kubectl scale statefulset sample-statefulset --replicas=3
kubectl get pods -l app=sample-statefulset
```

StatefulSet을 줄이거나 삭제해도 연결된 PVC는 Data 보호를 위해 기본적으로 자동 삭제되지 않는다.

### Parallel Pod Management

Pod 간 순서 의존성이 없다면 `spec.podManagementPolicy: Parallel`로 생성과 종료를 병렬 처리할 수 있다. 다음 내용을 `sample-stateful-parallel.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-statefulset-parallel
spec:
  clusterIP: None
  selector:
    app: sample-statefulset-parallel
  ports:
    - name: http
      port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: sample-statefulset-parallel
spec:
  podManagementPolicy: Parallel
  serviceName: sample-statefulset-parallel
  replicas: 3
  selector:
    matchLabels:
      app: sample-statefulset-parallel
  template:
    metadata:
      labels:
        app: sample-statefulset-parallel
    spec:
      containers:
        - name: nginx-container
          image: nginx
          volumeMounts:
            - name: www
              mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
    - metadata:
        name: www
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 1Gi
```

Resource를 적용하고 Pod의 `AGE`를 비교한다.

```bash
kubectl apply -f sample-stateful-parallel.yaml
kubectl get pods -l app=sample-statefulset-parallel
```

`Parallel`은 각 Pod가 Ready가 될 때까지 순서대로 기다리지 않고 Pod를 함께 생성하므로 `AGE`가 비슷하게 나타난다. Pod 이름과 PVC Identity까지 임의로 바뀌는 설정은 아니다.

첫 번째 Pod의 Mount를 확인한다.

```bash
kubectl exec pod/sample-statefulset-parallel-0 -- \
  df -h /usr/share/nginx/html
```

## 8 ) 질의: StatefulSet으로 Database 운영 가능 여부에 대한 강사님 답변

---

StatefulSet을 이용하여 Database를 Kubernetes Cluster 안에서 실행할 수 있다. 다만 StatefulSet을 사용한다는 사실만으로 Data가 안전하게 보존되거나 Database의 고가용성이 완성되는 것은 아니다.

### Network 접근

Pod는 다시 생성될 때 IP Address가 바뀔 수 있으므로 Client가 Pod IP를 직접 저장해서 접근하면 안 된다.

- 일반 Client Traffic은 Database Service의 DNS 이름으로 연결한다.

- Database Cluster의 Member를 개별적으로 식별해야 하면 Headless Service가 제공하는 Pod별 DNS 이름을 사용할 수 있다.

StatefulSet의 `serviceName`은 Pod마다 안정적인 Network Identity를 제공하지만 Database의 접속 권한, 암호화나 장애 조치를 대신 구성하지는 않는다.

### Node 장애와 Data 보존

Node가 고장났을 때 Data가 보존되는지는 Volume이 실제로 어디에 저장되는지에 따라 달라진다.

| Storage 구성 | Node 장애 시 고려 사항 |
|---|---|
| Container Writable Layer | Pod와 함께 Data를 잃을 수 있으므로 Database Data 저장에 부적합 |
| Node Local Volume | Disk가 남아 있어도 다른 Worker에서 바로 Mount하지 못할 수 있음 |
| NFS·Network Storage | 다른 Worker가 같은 Storage에 접근할 수 있지만 Storage Server의 가용성과 성능을 별도로 확보해야 함 |
| 분산 Storage·Cloud Volume | Backend의 복제, Zone과 Attach 조건에 따라 장애 복구 범위가 달라짐 |

NFS는 Network를 통해 File Storage를 제공하는 방식이고 RAID는 여러 Disk를 결합하여 Disk 장애 내성을 높이는 방식이다. 둘은 서로 같은 계층의 대안이 아니며 Database의 논리적 복제와 Backup을 대신하지 않는다.

### 운영 방식 선택

| 방식 | 장점 | 운영 책임 |
|---|---|---|
| Cluster 내부 StatefulSet | Application과 같은 배포 체계에서 관리 가능 | Storage, 복제, Backup, Upgrade, 장애 조치까지 직접 운영 |
| Cluster 외부 Database | Kubernetes Node 장애와 Database를 분리 가능 | 외부 Database의 연결, 보안과 가용성 관리 |
| Managed Database | Backup과 장애 조치 기능을 Service로 제공 가능 | Provider 기능과 비용, Network 연결 정책 검토 |

StatefulSet으로 Database를 운영하려면 다음 항목을 함께 설계해야 한다.

- Pod별 PVC와 실제 Storage Backend

- Database 자체 Replication과 Leader Election

- 정기 Backup과 복구 검증

- Node 및 Availability Zone 장애 시 재배치 조건

- Upgrade, Scaling과 종료 순서

따라서 StatefulSet은 Stateful Application을 배치하기 위한 기반이며 Data 보호 전략 전체를 대신하는 Resource는 아니다.

## 9 ) 실습 Resource 정리

---

순서 있는 종료가 필요하면 StatefulSet을 먼저 0개로 줄인다.

```bash
kubectl scale statefulset sample-statefulset --replicas=0
kubectl scale statefulset sample-statefulset-parallel --replicas=0
```

Pod 종료를 확인한 뒤 StatefulSet과 Headless Service를 삭제한다.

```bash
kubectl delete -f sample-statefulset.yaml
kubectl delete -f sample-stateful-parallel.yaml
```

StatefulSet을 삭제해도 PVC는 기본적으로 남을 수 있다. Data가 더 이상 필요하지 않은지 확인하기 전에는 PVC를 삭제하지 않는다.

```bash
kubectl get persistentvolumeclaims
```

## 전체 정리

---

> **최종 정리**
>
> - DaemonSet은 Scheduling 조건을 만족하는 각 Node에 Pod를 하나씩 배치하며 Node별 Agent에 적합하다.
>
> - StatefulSet은 Ordinal Pod 이름, 안정적인 Network Identity, 순서와 Pod별 PVC 연결을 관리한다.
>
> - Headless Service는 StatefulSet Pod별 DNS Identity를 제공하고 `volumeClaimTemplates`는 Pod별 PVC를 생성한다.
>
> - `OrderedReady`는 Pod를 순차 처리하고 `Parallel`은 Pod 간 순서 의존성이 없을 때 병렬로 처리한다.
>
> - StatefulSet은 Database 실행에 사용할 수 있지만 Data의 실제 내구성은 Storage Backend, Database 복제와 Backup 설계에 달려 있다.
>
> - NFS와 RAID는 서로 다른 Storage 계층의 기술이며 Database Backup과 고가용성을 대신하지 않는다.
