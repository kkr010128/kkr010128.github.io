---
title: Kubernetes Resource 관리와 Autoscaling
description: Container의 Resource 제한과 Namespace별 할당량, HPA·VPA의 Metric 기반 Autoscaling 동작과 실습 정리
date: 2026-09-03
updated_at: 2026-09-04
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Kubernetes는 Container가 요청하는 Resource를 기준으로 Pod를 Worker에 배치하고, kubelet과 Container Runtime을 통해 실행 중인 Resource 사용을 제한한다. Namespace에는 LimitRange와 ResourceQuota를 적용할 수 있으며, Resource Request는 Cluster와 Pod Autoscaling 판단에도 사용된다.

## 1 ) Cluster API Resource와 관리 범위

---

Cluster를 운영할 때 자주 확인하는 Resource는 Cluster 범위와 Namespace 범위로 나뉜다.

| Resource | 범위 | 역할 |
|---|---|---|
| Node | Cluster | Worker의 상태와 Capacity·Allocatable 표시 |
| Namespace | Cluster | Namespace 범위 Resource의 논리적 구분 |
| PersistentVolume | Cluster | Cluster에 제공되는 Storage 표현 |
| ResourceQuota | Namespace | Resource 사용량과 Object 개수 제한 |
| ServiceAccount | Namespace | Pod와 Process의 API Identity 제공 |
| Role | Namespace | Namespace 안의 API 권한 정의 |
| ClusterRole | Cluster | Cluster 범위 또는 재사용 가능한 API 권한 정의 |
| RoleBinding | Namespace | Namespace 안의 주체에 Role·ClusterRole 연결 |
| ClusterRoleBinding | Cluster | Cluster 범위에서 주체에 ClusterRole 연결 |
| NetworkPolicy | Namespace | 선택한 Pod의 Ingress·Egress Traffic 제어 |

Node와 Namespace의 기본 조회는 다음 명령으로 확인한다.

```bash
# Master 또는 관리 Client에서 실행
kubectl get nodes -o wide
kubectl get node worker1 -o yaml
kubectl get namespaces
kubectl get pods -n kube-system
kubectl get pods --all-namespaces
```

Node Object는 일반 Workload처럼 사용자가 반복해서 생성·삭제하는 Resource가 아니다. kubelet 등록과 Node Bootstrap 과정에서 Cluster에 추가되며 운영 중에는 상태, Capacity, Condition과 배치된 Pod를 자주 확인한다.

`-A`는 `--all-namespaces`의 축약 Option이다. `-a`는 모든 Namespace를 조회하는 Option이 아니다.

Namespace의 구조와 생성 방법은 [Kubernetes Namespace와 kubectl 기본 사용](/cloud-native-23-kubernetes-namespace-kubectl/)에서, PV는 [Kubernetes Volume과 Persistent Storage](/cloud-native-35-kubernetes-volume-persistent-storage/)에서 설명한다.

## 2 ) Resource Request와 Limit

---

Container의 `resources.requests`와 `resources.limits`에는 CPU, Memory와 Ephemeral Storage 등을 지정할 수 있다. Device Plugin을 사용하면 GPU 같은 Extended Resource도 요청할 수 있다.

| 설정 | Control Plane과 Worker에서의 역할 |
|---|---|
| `requests` | Scheduler가 Pod를 배치할 수 있는 Node를 판단할 때 사용 |
| `limits` | kubelet과 Container Runtime이 실행 중인 Container의 사용 상한을 적용 |

CPU는 Clock Frequency가 아니라 CPU Unit으로 지정한다. `1` CPU는 물리 Core 또는 Virtual Core 하나에 해당하며 `1000m`과 같다.

| 값 | 의미 |
|---|---|
| `1000m` | 1 CPU |
| `500m` | 0.5 CPU |
| `100m` | 0.1 CPU |
| `512Mi` | 512 Mebibyte |
| `1Gi` | 1 Gibibyte |

Request는 Container가 항상 실제로 소비하는 최솟값이 아니다. Scheduler의 배치 판단 기준이며, CPU 경합 시에는 CPU Share의 가중치에도 사용된다. Node에 여유가 있으면 Container는 Request보다 많은 CPU와 Memory를 사용할 수 있다.

Limit 적용 방식은 Resource마다 다르다.

- CPU Limit을 초과하려 하면 Linux Kernel이 CPU 시간을 Throttling한다.

- Memory Limit은 반응적으로 적용되며, Memory 부족이 감지되면 OOM Killer가 Container Process를 종료할 수 있다.

## 3 ) CPU와 Memory Request·Limit 실습

---

실습 Resource가 기존 Workload에 미치는 영향을 줄이기 위해 `resource-lab` Namespace를 사용한다. Namespace가 없다면 Master 또는 관리 Client에서 생성한다.

```bash
kubectl create namespace resource-lab
kubectl get namespace resource-lab
```

다음 내용을 `sample-resource.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-resource
  namespace: resource-lab
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-resource
  template:
    metadata:
      labels:
        app: sample-resource
    spec:
      containers:
        - name: nginx-container
          image: nginx:stable
          resources:
            requests:
              memory: 512Mi
              cpu: 500m
            limits:
              memory: 1Gi
              cpu: "1"
```

Master 또는 관리 Client에서 Deployment를 생성하고 Rollout 상태를 확인한다.

```bash
kubectl apply -f sample-resource.yaml
kubectl rollout status deployment/sample-resource \
  -n resource-lab
kubectl get pods -n resource-lab \
  -l app=sample-resource -o wide
```

Control Plane의 Scheduler는 Container별 Request를 합산하여 배치 가능한 Worker를 선택한다. Worker의 kubelet은 Pod Spec의 Limit을 Container Runtime에 전달하고 Runtime은 Linux cgroup을 통해 CPU와 Memory 제한을 적용한다.

Pod에 저장된 Resource 설정을 확인한다.

```bash
kubectl get pods -n resource-lab \
  -l app=sample-resource -o json \
  | jq '.items[].spec.containers[].resources'
```

## 4 ) Request만 지정한 경우

---

다음 내용을 `sample-resource-only-requests.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-resource-only-requests
  namespace: resource-lab
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-resource-only-requests
  template:
    metadata:
      labels:
        app: sample-resource-only-requests
    spec:
      containers:
        - name: nginx-container
          image: nginx:stable
          resources:
            requests:
              memory: 256Mi
              cpu: 200m
```

```bash
kubectl apply -f sample-resource-only-requests.yaml
kubectl get pods -n resource-lab \
  -l app=sample-resource-only-requests
kubectl get pods -n resource-lab \
  -l app=sample-resource-only-requests -o json \
  | jq '.items[].spec.containers[].resources'
```

Request만 있고 Limit이 없으면 해당 Resource에 Container별 상한이 설정되지 않는다. CPU는 Node의 여유 Resource를 더 사용할 수 있고, Memory 사용이 증가하여 Node 전체에 Memory Pressure가 발생하면 OOM이나 Pod Eviction으로 이어질 수 있다.

## 5 ) Limit만 지정한 경우

---

Admission 단계에서 다른 기본값이 적용되지 않았다면 특정 Resource의 Limit만 지정했을 때 Kubernetes는 같은 값을 Request로 복사한다.

다음 내용을 `sample-resource-only-limits.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-resource-only-limits
  namespace: resource-lab
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      resources:
        limits:
          memory: 256Mi
          cpu: 200m
```

Pod를 생성한 뒤 API Server에 저장된 Request와 Limit을 확인한다.

```bash
kubectl apply -f sample-resource-only-limits.yaml
kubectl get pod sample-resource-only-limits \
  -n resource-lab -o json \
  | jq '.spec.containers[].resources'
```

Namespace에 LimitRange 등 Admission 단계의 기본값이 있으면 결과가 달라질 수 있다. Scheduling Resource를 명확히 관리하려면 Request와 Limit을 모두 명시한다.

## 6 ) Ephemeral Storage 제한

---

Local Ephemeral Storage는 Pod가 실행되는 Node의 임시 저장 공간이다. kubelet이 측정하는 주요 대상은 다음과 같다.

- Container Log

- Container의 Writable Layer

- Disk 기반 `emptyDir` Data

Memory 기반 `emptyDir`은 Ephemeral Storage가 아니라 Container Memory 사용량으로 계산된다.

다음 내용을 `sample-ephemeral-storage.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-ephemeral-storage
  namespace: resource-lab
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      resources:
        requests:
          ephemeral-storage: 1Gi
        limits:
          ephemeral-storage: 2Gi
```

```bash
kubectl apply -f sample-ephemeral-storage.yaml
kubectl wait --for=condition=Ready \
  pod/sample-ephemeral-storage \
  -n resource-lab --timeout=120s
```

Container의 Writable Layer에 2GiB File 생성을 시도한다.

```bash
kubectl exec -n resource-lab sample-ephemeral-storage -- \
  dd if=/dev/zero of=/dummy bs=1M count=2049
```

사용량이 Limit을 초과하면 kubelet이 Pod를 Eviction 대상으로 표시할 수 있다. File System 구성과 kubelet의 Local Storage 측정 조건에 따라 결과 시점이 달라질 수 있으므로 Pod 상태와 Event를 함께 확인한다.

```bash
kubectl get pod sample-ephemeral-storage \
  -n resource-lab --watch
kubectl describe pod sample-ephemeral-storage \
  -n resource-lab
kubectl get events -n resource-lab \
  --sort-by=.lastTimestamp
```

여러 Container가 있는 Pod의 Ephemeral Storage Limit은 Container별 Limit의 합으로 계산한다. Pod 사용량에는 Container의 Writable Layer와 Log 및 Disk 기반 `emptyDir` 사용량이 포함된다.

## 7 ) Node Capacity와 Allocatable

---

Node의 전체 Capacity가 모두 Pod에 할당되는 것은 아니다. kubelet은 OS와 Kubernetes Component가 사용할 Resource를 고려하여 `status.allocatable`에 Pod가 사용할 수 있는 양을 표시한다.

```bash
kubectl get node worker1 \
  -o custom-columns='NAME:.metadata.name,CPU:.status.capacity.cpu,ALLOCATABLE_CPU:.status.allocatable.cpu,MEMORY:.status.capacity.memory,ALLOCATABLE_MEMORY:.status.allocatable.memory'
kubectl describe node worker1
```

| 설정 | 용도 |
|---|---|
| `kubeReserved` | kubelet과 Container Runtime 등 Kubernetes 관련 Daemon Resource 예약 |
| `systemReserved` | OS와 System Daemon Resource 예약 |
| Eviction Threshold | Node Resource 고갈 전에 kubelet이 Pod를 Eviction할 기준 |

`kubeReserved`와 `systemReserved`는 kubelet에서 구성하는 값이며 모든 Cluster에 같은 값이 자동으로 적용되는 것은 아니다. 실제 Pod 배치 가능량은 Node의 `status.allocatable`에서 확인한다.

## 8 ) Node-pressure Eviction

---

Worker의 kubelet에 있는 Eviction Manager는 Memory, Disk 공간과 File System Inode 등의 상태를 주기적으로 확인한다. Threshold가 충족되면 Node 전체의 Resource 고갈을 막기 위해 Pod를 종료하고 Resource를 회수한다.

| 구분 | 동작 |
|---|---|
| Soft Threshold | 조건이 `evictionSoftGracePeriod` 동안 지속된 뒤 Eviction 시작 |
| Hard Threshold | Grace Period `0s`로 즉시 Eviction 시작 |
| `evictionMaxPodGracePeriod` | Soft Eviction에서 허용할 Pod 종료 Grace Period 상한 |

`evictionSoftGracePeriod`는 Threshold가 얼마나 지속돼야 하는지를 나타낸다. Pod 종료에 허용할 시간과 같은 설정이 아니다. Node-pressure Eviction은 Pod의 `terminationGracePeriodSeconds`나 PodDisruptionBudget을 그대로 따르지 않는다.

kubelet은 다음 순서로 Eviction 대상을 평가한다.

1. 고갈된 Resource의 실제 사용량이 Request를 초과했는지 확인한다.

2. Pod Priority가 낮은 Pod를 우선한다.

3. 실제 사용량이 Request를 얼마나 초과했는지 비교한다.

`kubectl describe node`에서 `MemoryPressure`, `DiskPressure`, `PIDPressure` Condition과 Event를 확인한다.

```bash
kubectl describe node worker1

# worker1에서 실행
sudo journalctl -u kubelet --since "10 minutes ago"
```

## 9 ) Scheduling 불가와 Overcommit

---

Resource Request를 수용할 Worker가 없으면 Pod는 `Pending` 상태에 머문다. 이는 실제 CPU·Memory 사용률이 100%라는 의미가 아니라 Scheduler가 계산한 Allocatable 대비 Request가 부족하다는 의미이다.

Resource Overcommit은 일반적으로 Node Capacity보다 큰 Limit 총량을 허용하여 Workload가 동시에 최대치를 사용하지 않는다는 전제로 Resource를 배치하는 방식이다. Request 부족으로 Pod를 배치하지 못하는 상태와 구분해야 한다.

다음 내용을 `sample-resource-scale.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-resource-scale
  namespace: resource-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sample-resource-scale
  template:
    metadata:
      labels:
        app: sample-resource-scale
    spec:
      containers:
        - name: nginx-container
          image: nginx:stable
          resources:
            requests:
              memory: 512Mi
              cpu: 500m
            limits:
              memory: 1Gi
              cpu: "1"
```

```bash
kubectl apply -f sample-resource-scale.yaml
kubectl scale deployment/sample-resource-scale \
  -n resource-lab --replicas=6
kubectl get pods -n resource-lab \
  -l app=sample-resource-scale -o wide
```

실제 Cluster에 충분한 Resource가 있으면 여섯 Pod가 모두 실행될 수 있다. `Pending` Pod가 발생한 경우 Pod Event와 Node의 할당 현황을 확인한다.

```bash
kubectl describe pod <pending-pod-name> \
  -n resource-lab
kubectl describe node worker1
```

`kubectl describe node`의 `Allocated resources`는 실제 사용량이 아니라 Pod Spec에 선언된 Request와 Limit의 합계이다. 실제 사용량은 Metrics Server가 제공하는 `kubectl top`으로 구분해 확인한다.

## 10 ) 여러 Container의 Resource 계산

---

Scheduler는 Pod 단위로 Worker를 선택하므로 Pod에 포함된 Container의 Resource를 합산한다.

- 일반 Application Container의 같은 Resource Request와 Limit은 모두 합산한다.

- 일반 Init Container는 순차 실행되므로 같은 Resource에서 가장 큰 Init Container 값을 사용한다.

- Application Container 합계와 Init Container의 최댓값 중 큰 값을 Pod의 Scheduling 기준으로 사용한다.

```text
Pod의 유효 Request
  = max(
      모든 Application Container Request의 합,
      Init Container Request 중 최댓값
    )
```

이 계산은 Init Container가 Application Container보다 큰 초기화 Resource를 요구할 때 해당 Pod가 실행 가능한 Worker를 확보하는 데 사용된다.

## 11 ) Cluster Autoscaler

---

Cluster Autoscaler는 실행할 Node가 부족한 Pod를 감지하고 연동된 Infrastructure의 Node Group 크기를 조정한다. 단순한 Node CPU·Memory 평균 사용률이 아니라 Scheduler가 배치하지 못한 Pod와 해당 Pod의 Request를 주요 판단 기준으로 사용한다.

```text
Pod 생성
  → Scheduler가 모든 Node의 Allocatable과 Request 비교
  → 적합한 Node가 없어 Pod가 Pending
  → Cluster Autoscaler가 확장 가능 여부 확인
  → Infrastructure Node Group 확장
  → 새 Worker 준비와 Cluster 등록
  → Scheduler가 Pending Pod 배치
```

Request를 지나치게 크게 설정하면 실제 사용량이 낮아도 Pod가 배치되지 않아 Scale-out이 발생할 수 있다. 반대로 Request를 지나치게 낮게 설정하면 실제 부하가 높아도 Scheduler는 여유가 있다고 판단할 수 있다.

Cluster Autoscaler는 실제 Node를 생성할 수 있는 Infrastructure와 연결되어야 한다.

| 환경 | 연동 구조 예시 |
|---|---|
| AWS | Auto Scaling Group의 Desired Capacity 조정 및 Tag 기반 Node Group 탐색 |
| 직접 구축한 VM 환경 | VM 생성, OS 준비와 `kubeadm join`까지 자동화 필요 |
| Cluster API 사용 환경 | Machine Resource와 Infrastructure Provider로 Node Lifecycle 관리 |

Cluster API는 On-premise 환경에서 사용할 수 있는 선택지 중 하나이며, kubeadm Cluster에 Cluster Autoscaling을 자동으로 제공하는 기능은 아니다.

Request와 Limit은 임의의 고정 비율로 결정하지 않고 Application의 부하 Test와 관측 결과를 기준으로 조정한다. Memory Limit이 지나치게 낮으면 부하 Test 중 OOM Kill이 발생할 수 있고 Request가 실제 요구량보다 크면 Scheduling과 Node 확장 효율이 낮아질 수 있다.

## 12 ) LimitRange

---

LimitRange는 Namespace 안에서 Container, Pod 또는 PVC에 허용할 Resource 범위를 정의한다. 새 Object가 API Server의 Admission 단계를 통과할 때 적용되며 이미 실행 중인 Pod의 Resource 설정은 변경하지 않는다.

| Field | 역할 |
|---|---|
| `default` | Container에 Limit이 없을 때 적용할 기본 Limit |
| `defaultRequest` | Container에 Request가 없을 때 적용할 기본 Request |
| `max` | 허용할 최대 Resource |
| `min` | 허용할 최소 Resource |
| `maxLimitRequestRatio` | Limit과 Request 사이의 최대 비율 |

`type: Container`에서는 위 항목을 모두 사용할 수 있다. Pod 범위에서는 기본값을 주입하는 `default`, `defaultRequest`를 사용하지 않으며, PVC에는 Storage Request의 `min`과 `max`를 적용한다.

다음 내용을 `sample-limitrange-container.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: sample-limitrange-container
  namespace: resource-lab
spec:
  limits:
    - type: Container
      default:
        memory: 512Mi
        cpu: 500m
      defaultRequest:
        memory: 256Mi
        cpu: 250m
      max:
        memory: 1025Mi
        cpu: "1"
      min:
        memory: 128Mi
        cpu: 125m
      maxLimitRequestRatio:
        memory: "2"
        cpu: "2"
```

```bash
kubectl apply -f sample-limitrange-container.yaml
kubectl describe limitrange sample-limitrange-container \
  -n resource-lab
```

## 13 ) LimitRange 위반 확인

---

CPU Request와 Limit이 최소값 `125m`보다 작은 Pod를 생성한다. 다음 내용을 `sample-pod-below-min.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod-below-min
  namespace: resource-lab
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      resources:
        requests:
          cpu: 100m
        limits:
          cpu: 100m
```

```bash
kubectl apply -f sample-pod-below-min.yaml
```

API Server는 LimitRange의 최소 CPU보다 작다는 `Forbidden` 응답으로 생성을 거부한다.

다음에는 Limit과 Request 비율이 4인 Pod를 확인한다. 내용을 `sample-pod-over-ratio.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod-over-ratio
  namespace: resource-lab
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      resources:
        requests:
          cpu: 125m
        limits:
          cpu: 500m
```

```bash
kubectl apply -f sample-pod-over-ratio.yaml
```

설정된 `maxLimitRequestRatio.cpu`가 `2`이므로 비율 `4`인 요청은 `Forbidden` 응답으로 거부된다. 실패한 요청은 Pod Resource를 생성하지 않는다.

## 14 ) ResourceQuota Object 개수 제한

---

ResourceQuota는 Namespace 전체에서 사용할 수 있는 Resource 양과 생성 가능한 Object 수를 제한한다. 기존 Object를 삭제하거나 설정을 변경하지는 않지만, Quota가 생성되면 Namespace의 기존 Object도 현재 사용량에 포함된다.

다음 내용을 `sample-resourcequota-count.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: sample-resourcequota-count
  namespace: resource-lab
spec:
  hard:
    count/persistentvolumeclaims: "10"
    count/services: "10"
    count/secrets: "10"
    count/configmaps: "10"
    count/replicationcontrollers: "10"
    count/deployments.apps: "10"
    count/replicasets.apps: "10"
    count/statefulsets.apps: "10"
    count/jobs.batch: "10"
    count/cronjobs.batch: "10"
```

`count/deployments.extensions`는 제거된 `extensions` API Group을 대상으로 하므로 현재 Manifest에 사용하지 않는다.

```bash
kubectl apply -f sample-resourcequota-count.yaml
kubectl describe resourcequota sample-resourcequota-count \
  -n resource-lab
```

ConfigMap 열한 개 생성을 시도한다.

```bash
for i in $(seq 1 11); do
  kubectl create configmap "conf-${i}" \
    --from-literal=key1=val1 \
    -n resource-lab
done
```

Namespace에 이미 존재하는 ConfigMap을 포함하여 총수가 `10`에 도달하면 다음 생성 요청이 거부된다. Kubernetes가 자동으로 만든 `kube-root-ca.crt` ConfigMap 등이 있을 수 있으므로 실패 순서를 고정하지 않고 ResourceQuota의 현재 사용량을 확인한다.

```bash
kubectl describe resourcequota sample-resourcequota-count \
  -n resource-lab
kubectl get configmaps -n resource-lab
```

## 15 ) ResourceQuota Key 종류

---

`count/<resource>[.<group>]` 형식 외에도 Kubernetes가 정의한 Object별 Quota Key와 StorageClass별 Key를 사용할 수 있다. 두 형식은 단순히 옛날 방식과 최근 방식으로 나뉘지 않는다.

다음 내용을 `sample-resourcequota-special.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: sample-resourcequota-special
  namespace: resource-lab
spec:
  hard:
    sample-storageclass.storageclass.storage.k8s.io/persistentvolumeclaims: "10"
    services.loadbalancers: "10"
    services.nodeports: "10"
    pods: "10"
    persistentvolumeclaims: "10"
    replicationcontrollers: "10"
    secrets: "10"
    configmaps: "10"
    services: "10"
    resourcequotas: "10"
```

| Key | 제한 대상 |
|---|---|
| `services.loadbalancers` | `type: LoadBalancer` Service 수 |
| `services.nodeports` | Service가 사용하는 NodePort 수 |
| `pods` | Terminal 상태가 아닌 Pod 수 |
| `<storage-class>.storageclass.storage.k8s.io/persistentvolumeclaims` | 해당 StorageClass를 요청하는 PVC 수 |

```bash
kubectl apply -f sample-resourcequota-special.yaml
kubectl describe resourcequota sample-resourcequota-special \
  -n resource-lab
```

## 16 ) ResourceQuota 사용량 제한

---

ResourceQuota는 CPU, Memory, Storage와 Extended Resource의 Namespace 전체 합계도 제한할 수 있다.

다음 내용을 `sample-resourcequota-usable.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: sample-resourcequota-usable
  namespace: resource-lab
spec:
  hard:
    requests.memory: 2Gi
    requests.storage: 5Gi
    sample-storageclass.storageclass.storage.k8s.io/requests.storage: 5Gi
    requests.ephemeral-storage: 5Gi
    requests.nvidia.com/gpu: "2"
    limits.cpu: "4"
    limits.ephemeral-storage: 10Gi
```

GPU 같은 Extended Resource는 Overcommit을 지원하지 않으므로 Quota에는 `requests.<extended-resource>` 형식만 사용한다. `limits.nvidia.com/gpu`는 유효한 Extended Resource Quota Key가 아니다.

```bash
kubectl apply -f sample-resourcequota-usable.yaml
kubectl describe resourcequota sample-resourcequota-usable \
  -n resource-lab
```

같은 Namespace에 ResourceQuota가 여러 개 있으면 새 Object는 모든 Quota 조건을 만족해야 한다.

## 17 ) Horizontal Pod Autoscaler

---

> **Horizontal Pod Autoscaler(HPA)**
>
> Metric 값을 기준으로 Deployment나 StatefulSet 같은 확장 가능한 Workload의 Replica 수를 자동 조정하는 API Resource와 Controller이다.

HPA는 Deployment, StatefulSet, ReplicaSet과 ReplicationController처럼 Scale Subresource를 제공하는 대상의 Replica를 조정할 수 있다. 부하가 높으면 Replica를 늘리고 낮으면 줄인다. CPU 사용률처럼 Request 대비 비율을 사용하는 Resource Metric은 대상 Pod의 Container에 해당 Resource Request가 정의돼 있어야 계산할 수 있다.

HPA Controller의 기본 동기화 주기는 `30초`가 아니라 `15초`이다. 실제 값은 kube-controller-manager의 `horizontalPodAutoscalerSyncPeriod` 설정에 따라 달라질 수 있다.

기본 Replica 계산식은 다음과 같다.

```text
desiredReplicas
  = ceil(
      currentReplicas
      × currentMetricValue
      ÷ desiredMetricValue
    )
```

두 Pod의 CPU 사용률이 각각 `100%`, `90%`라면 평균은 `95%`이다. 목표 평균 사용률이 `50%`일 때 계산 결과는 다음과 같다.

```text
ceil(2 × 95 ÷ 50)
= ceil(3.8)
= 4
```

따라서 허용 범위와 Stabilization 동작 등 다른 조건을 제외한 기본 계산 결과는 Replica 네 개이다. Metric 수집 상태는 [Kubernetes Resource 조회와 Pod Debugging](/cloud-native-26-resource-inspection-debugging/)의 Metrics Server와 `kubectl top` 절에서 확인할 수 있다.

## 18 ) HPA 동작 구조와 준비 상태 확인

---

HPA는 Control Plane에서 실행되는 Controller와 Worker에서 수집되는 Metric을 연결하여 동작한다.

1. Worker의 kubelet이 Container의 CPU·Memory 사용량을 수집한다.

2. Metrics Server가 각 Node의 kubelet에서 Metric을 수집하여 Metrics API로 제공한다.

3. Control Plane의 HPA Controller가 Metrics API에서 대상 Pod의 Metric을 조회한다.

4. HPA Controller가 계산한 Replica 수를 Deployment의 Scale Subresource에 반영한다.

5. Deployment Controller가 변경된 Replica 수에 맞춰 Pod를 생성하거나 제거한다.

6. 새 Pod가 필요하면 Scheduler가 Worker를 선택하고, 해당 Worker의 kubelet과 Container Runtime이 Container를 실행한다.

HPA를 사용하기 전에 [Kubernetes Resource 조회와 Pod Debugging](/cloud-native-26-resource-inspection-debugging/)에서 설치한 Metrics Server와 Metric 수집 상태를 확인한다.

```bash
kubectl get pods -n kube-system \
  -l k8s-app=metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top nodes
kubectl top pods -A
```

`kubectl top` 결과가 나오지 않는 상태에서는 Resource Metric 기반 HPA 실습을 진행할 수 없다. 먼저 Metrics Server Pod, APIService와 kubelet 통신 상태를 확인해야 한다.

## 19 ) HPA 실습

---

HPA가 CPU 사용률을 계산할 수 있도록 CPU Request를 지정한 Deployment를 생성한다. 다음 내용을 `nginx-hpa.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-hpa
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-hpa
  template:
    metadata:
      labels:
        app: nginx-hpa
    spec:
      containers:
        - name: nginx
          image: nginx:stable
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
          ports:
            - containerPort: 80
```

Cluster 안에서 부하 발생 Pod가 nginx에 접근할 수 있도록 다음 내용을 `nginx-hpa-service.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-hpa-service
spec:
  selector:
    app: nginx-hpa
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
```

CPU 평균 사용률이 Request의 `50%`를 넘으면 Replica를 늘리도록 다음 내용을 `nginx-hpa-autoscaler.yaml`로 저장한다.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx-hpa
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50
```

세 Resource를 생성하고 연결 상태를 확인한다.

```bash
kubectl apply -f nginx-hpa.yaml
kubectl apply -f nginx-hpa-service.yaml
kubectl apply -f nginx-hpa-autoscaler.yaml

kubectl get deployment,service,hpa
kubectl describe hpa nginx-hpa
```

`TARGETS`가 `<unknown>/50%`로 계속 표시되면 CPU Request와 Metrics Server 상태를 함께 확인한다.

### 부하에 따른 Replica 변화 확인

두 터미널에서 HPA와 Pod의 변화를 각각 관찰한다.

```bash
kubectl get hpa nginx-hpa --watch
```

```bash
kubectl get pods -l app=nginx-hpa --watch
```

다른 터미널에서 Service로 요청을 반복 전송하는 Pod 세 개를 실행한다.

```bash
kubectl run load-generator \
  --image=busybox:1.36 \
  --restart=Never \
  -- /bin/sh -c \
  "while true; do wget -q -O- http://nginx-hpa-service; done"

kubectl run load-generator1 \
  --image=busybox:1.36 \
  --restart=Never \
  -- /bin/sh -c \
  "while true; do wget -q -O- http://nginx-hpa-service; done"

kubectl run load-generator2 \
  --image=busybox:1.36 \
  --restart=Never \
  -- /bin/sh -c \
  "while true; do wget -q -O- http://nginx-hpa-service; done"
```

HPA가 즉시 반응하지 않을 수 있다. Metric 수집과 HPA 동기화가 진행된 뒤 CPU 사용률, `DESIRED` Replica와 Pod 수가 변하는지 확인한다.

```bash
kubectl top pods -l app=nginx-hpa
kubectl get hpa nginx-hpa
kubectl get deployment nginx-hpa
```

부하 발생 Pod를 삭제하면 CPU 사용률이 낮아지고 Stabilization 조건에 따라 Replica가 다시 줄어든다.

```bash
kubectl delete pod \
  load-generator load-generator1 load-generator2
kubectl get hpa nginx-hpa --watch
```

## 20 ) HPA Metric과 Target

---

`autoscaling/v2` HPA는 다음 Metric Source를 사용할 수 있다.

| Metric Type | 판단 대상 | 예시 |
|---|---|---|
| `Resource` | Pod의 CPU·Memory 같은 Resource 사용량 | CPU Request 대비 평균 사용률 |
| `ContainerResource` | Pod 안의 특정 Container Resource 사용량 | Application Container의 CPU 사용률 |
| `Pods` | 각 Pod에서 수집한 Custom Metric | Pod별 Connection 수 |
| `Object` | 하나의 Kubernetes Object와 연결된 Metric | Ingress의 초당 요청 수 |
| `External` | Kubernetes Object와 직접 연결되지 않은 외부 Metric | Load Balancer QPS, Queue 길이 |

Resource Metric의 Target은 다음과 같이 구분한다.

| Target Type | 의미 | 예시 |
|---|---|---|
| `Utilization` | Resource Request 대비 평균 사용률 | CPU Request의 `50%` |
| `AverageValue` | Pod 하나당 Metric의 평균값 | Pod당 Memory `500Mi` |
| `Value` | Object·External Metric의 전체 목표값 | Queue 전체 길이 |

여러 Metric을 지정하면 HPA는 각 Metric으로 필요한 Replica 수를 계산한 뒤 가장 큰 값을 사용한다. 따라서 CPU와 Memory 중 하나만 목표치를 초과해도 Scale Out이 발생할 수 있다.

## 21 ) 다중 Metric과 Scaling Behavior

---

앞서 만든 `nginx-hpa-autoscaler.yaml`을 다음 내용으로 변경한다. CPU 사용률과 평균 Memory 사용량을 함께 확인하고, Replica 증감 속도를 제한하는 설정이다. `autoscaling/v2beta2`는 Kubernetes 1.26부터 제공되지 않으므로 현재 API인 `autoscaling/v2`를 사용한다.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx-hpa
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50
    - type: Resource
      resource:
        name: memory
        target:
          type: AverageValue
          averageValue: 500Mi
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

`behavior`의 주요 항목은 다음과 같다.

| 항목 | 역할 |
|---|---|
| `scaleUp` | Replica를 늘릴 때 적용할 정책 |
| `scaleDown` | Replica를 줄일 때 적용할 정책 |
| `policies.type: Percent` | 현재 Replica 수를 기준으로 허용할 변화 비율 |
| `policies.type: Pods` | 일정 시간 동안 변경할 수 있는 Pod 개수 |
| `periodSeconds` | 정책이 허용하는 변화량을 계산할 기간 |
| `selectPolicy` | 여러 Policy 중 사용할 Policy 선택 |
| `stabilizationWindowSeconds` | 이전 권장값을 고려하여 급격한 변동을 줄이는 시간 |

Scale Up의 `selectPolicy: Max`는 `100%` 증가와 Pod 네 개 증가 중 더 큰 변화량을 허용한다. `selectPolicy: Disabled`를 해당 방향에 지정하면 그 방향의 Scaling을 비활성화할 수 있다.

변경된 HPA를 적용하고 실제 설정을 확인한다.

```bash
kubectl apply -f nginx-hpa-autoscaler.yaml
kubectl get hpa nginx-hpa -o yaml
```

## 22 ) Vertical Pod Autoscaler

---

> **Vertical Pod Autoscaler(VPA)**
>
> Container의 실제 Resource 사용량을 분석하여 CPU·Memory Request 권장값을 계산하고, Update Mode에 따라 이를 Pod에 적용하는 Autoscaler이다.

HPA는 주로 Replica 수를 늘리거나 줄이는 Horizontal Scaling을 담당한다. VPA는 Container 하나에 필요한 CPU·Memory Request를 조정하는 Vertical Scaling을 담당한다. Request가 실제 사용량보다 지나치게 작으면 성능과 Scheduling이 불안정해질 수 있고, 지나치게 크면 Worker의 Resource가 낭비될 수 있다.

VPA는 Kubernetes 기본 구성 요소가 아니므로 별도로 설치해야 한다. 설치 후에는 다음 구성 요소가 협력한다.

| 구성 요소 | 역할 |
|---|---|
| Recommender | Resource 사용 이력을 바탕으로 Request 권장값 계산 |
| Updater | Update Mode에 따라 기존 Pod를 교체할지 판단 |
| Admission Controller | 새 Pod 생성 시 VPA 권장값을 Pod Request에 반영 |

VPA 설치가 필요한 환경에서는 공식 Autoscaler 저장소를 내려받아 설치 스크립트를 실행한다.

```bash
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh
```

TLS 인증서 오류가 발생하면 원인을 해결해야 한다. 전역 Git 설정에서 TLS 검증을 비활성화하면 이후 모든 Repository 연결의 검증이 생략되므로 사용하지 않는다.

CRD와 VPA 구성 요소를 확인한다.

```bash
kubectl get crd verticalpodautoscalers.autoscaling.k8s.io
kubectl get pods -n kube-system | grep vpa
kubectl api-resources | grep -i verticalpodautoscaler
```

VPA 설치 방식과 지원하는 Update Mode는 사용하는 VPA Release와 Kubernetes Version에 따라 확인해야 한다.

## 23 ) VPA Recommendation 실습

---

작은 Request를 지정한 Deployment를 생성한다. 다음 내용을 `vpa-deployment.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-vpa
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-vpa
  template:
    metadata:
      labels:
        app: nginx-vpa
    spec:
      containers:
        - name: nginx
          image: nginx:stable
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 500m
              memory: 512Mi
          ports:
            - containerPort: 80
```

기존 Pod를 변경하지 않고 Recommendation만 확인하도록 다음 내용을 `nginx-vpa-autoscaler.yaml`로 저장한다.

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: nginx-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx-vpa
  updatePolicy:
    updateMode: "Off"
```

두 파일을 적용한다.

```bash
kubectl apply -f vpa-deployment.yaml
kubectl apply -f nginx-vpa-autoscaler.yaml
kubectl get deployment,pods,vpa
```

VPA가 사용량을 관찰하고 Recommendation을 계산할 시간이 필요하다. 일정 시간 뒤 결과를 확인한다.

```bash
kubectl describe vpa nginx-vpa
kubectl get vpa nginx-vpa \
  -o jsonpath='{.status.recommendation}'
```

Recommendation의 주요 값은 다음과 같다.

| 항목 | 의미 |
|---|---|
| `Lower Bound` | 안정적인 동작을 위해 권장되는 Resource 범위의 하한 |
| `Upper Bound` | 권장되는 Resource 범위의 상한 |
| `Target` | VPA의 Container Resource Policy를 반영한 Request 권장값 |
| `Uncapped Target` | Container Resource Policy를 적용하기 전 사용량 기반 권장값 |

실습의 `Off` Mode에서는 Recommendation이 표시되더라도 기존 Pod의 Request는 자동으로 바뀌지 않는다.

## 24 ) VPA Update Mode와 HPA 조합

---

VPA의 Update Mode는 Resource 권장값을 언제 적용할지 결정한다.

| Update Mode | 동작 |
|---|---|
| `Off` | 권장값만 계산하고 Pod Resource를 변경하지 않음 |
| `Initial` | 새 Pod가 생성될 때만 권장값 적용 |
| `Recreate` | 권장값 적용이 필요하면 기존 Pod를 제거하고 새 Pod에 반영 |
| `InPlaceOrRecreate` | 가능한 경우 실행 중인 Pod를 변경하고, 불가능하면 Pod를 교체 |
| `InPlace` | 지원되는 Resource를 실행 중인 Pod에 직접 변경 |

`Auto`는 Deprecated 상태이며 현재는 `Recreate`와 같은 방식으로 동작한다. 새 설정에는 의도를 명확히 나타내는 Mode를 사용한다. In-place Mode는 Kubernetes와 VPA가 해당 기능을 지원하는지 먼저 확인해야 한다.

VPA와 HPA가 같은 CPU Resource를 동시에 조정하면 서로의 판단에 영향을 줄 수 있다. CPU 사용률 기반 HPA는 현재 사용량을 CPU Request와 비교하는데, VPA가 그 Request를 변경하면 HPA의 계산 기준도 변하기 때문이다.

| HPA 기준 | VPA 대상 | 판단 |
|---|---|---|
| CPU 사용률 | CPU Request | 계산 기준이 변하므로 충돌 가능성이 있음 |
| CPU 사용률 | Memory Request | 서로 다른 Resource를 조정하므로 역할 분리가 가능함 |
| Request 수·Queue 길이 같은 외부 Metric | CPU·Memory Request | Replica 수와 개별 Pod Resource의 판단 기준을 분리할 수 있음 |
| CPU 사용률 | `Off` Mode의 CPU·Memory Recommendation | 자동 변경 없이 권장값을 검토할 수 있음 |

운영 환경에서는 Application 특성, Pod 교체 영향과 HPA Metric을 확인한 뒤 Mode와 조정 대상을 결정한다.

> **중간 정리**
>
> - HPA Controller는 Metric을 기준으로 Workload Replica 수를 조정한다.
>
> - VPA는 Container의 Resource 사용량을 분석하여 CPU·Memory Request 권장값을 계산한다.
>
> - 같은 Resource를 기준으로 HPA와 VPA를 함께 사용하면 계산 기준이 서로 영향을 줄 수 있다.

## 25 ) 실습 Resource 정리

---

HPA와 VPA 실습 Resource를 확인한다.

```bash
kubectl get deployment,service,hpa,vpa
kubectl get pods
```

HPA 실습 Resource를 삭제한다.

```bash
kubectl delete -f nginx-hpa-autoscaler.yaml
kubectl delete -f nginx-hpa-service.yaml
kubectl delete -f nginx-hpa.yaml
kubectl delete pod \
  load-generator load-generator1 load-generator2 \
  --ignore-not-found
```

VPA 실습 Resource를 삭제한다.

```bash
kubectl delete -f nginx-vpa-autoscaler.yaml
kubectl delete -f vpa-deployment.yaml
```

VPA 자체는 다른 Workload에서도 사용할 수 있으므로 이 실습만을 이유로 설치 구성 요소까지 제거하지 않는다.

Resource 관리 실습용 Namespace 안의 Resource도 확인한다.

```bash
kubectl get all -n resource-lab
kubectl get limitranges,resourcequotas \
  -n resource-lab
kubectl get configmaps -n resource-lab
```

`resource-lab`이 이 실습에만 사용됐는지 확인한 뒤 Namespace를 삭제한다. Namespace를 삭제하면 그 안의 Resource도 함께 삭제된다.

```bash
kubectl delete namespace resource-lab
```

## 전체 정리

---

> **최종 정리**
>
> - Request는 Scheduler의 Pod 배치 기준이고 Limit은 실행 중인 Container에 적용할 Resource 상한이다.
>
> - CPU Limit은 Throttling으로 적용되고 Memory Limit은 OOM Kill로 이어질 수 있다.
>
> - kubelet은 Memory와 Disk 등의 Node-pressure를 감지하여 Threshold와 Pod 우선순위에 따라 Eviction한다.
>
> - LimitRange는 개별 Object의 기본값과 허용 범위를 제어하고 ResourceQuota는 Namespace 전체 사용량과 Object 수를 제한한다.
>
> - Cluster Autoscaler는 배치되지 못한 Pod의 Request를 기준으로 Node 확장을 판단하고 HPA는 Metric을 기준으로 Workload Replica를 조정한다.
>
> - HPA는 Metric을 기준으로 Replica 수를 조정하고 VPA는 CPU·Memory Request 권장값을 계산하거나 적용한다.
>
> - HPA와 VPA를 함께 사용할 때는 같은 Resource가 양쪽의 판단 기준이 되지 않도록 Metric과 조정 대상을 구분한다.
>
> - 다음 글인 [Kubernetes Health Check와 restartPolicy](/cloud-native-37-kubernetes-health-check-restart-policy/)에서는 kubelet이 Container 상태를 점검하고 실패에 대응하는 과정을 다룬다.
