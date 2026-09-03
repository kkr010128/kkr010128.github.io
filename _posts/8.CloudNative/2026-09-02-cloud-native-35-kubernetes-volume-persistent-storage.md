---
title: Kubernetes Volume과 Persistent Storage
description: emptyDir, hostPath, Downward API와 projected Volume부터 PV·PVC 및 NFS Storage 연결까지 정리
date: 2026-09-02
updated_at: 2026-09-03
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Container의 Writable Layer에 저장한 Data는 Container가 교체될 때 유지되지 않는다. Kubernetes Volume은 Pod의 Container가 사용할 File System 영역을 제공하며, Volume 종류에 따라 Data의 수명과 실제 저장 위치가 달라진다.

## 1 ) Kubernetes Volume

---

> **Volume**
>
> Pod에 정의하고 Container의 특정 경로에 Mount하여 사용하는 File System 영역이다.

Pod는 `spec.volumes`에서 Volume을 정의하고 각 Container의 `volumeMounts`에서 Mount 경로를 지정한다. Volume은 Container와 분리되므로 같은 Pod 안의 여러 Container가 Data를 공유할 수 있다.

| 분류 | 대표 종류 | Data 수명과 위치 |
|---|---|---|
| Pod 수명에 연결 | `emptyDir` | Pod가 삭제되면 함께 삭제 |
| Node에 연결 | `hostPath` | 특정 Node의 File System 사용 |
| Kubernetes Resource를 File로 제공 | `secret`, `configMap`, `downwardAPI`, `projected` | API Resource 내용을 Pod에 투영 |
| 외부 또는 영구 Storage 연결 | `persistentVolumeClaim`, `nfs`, `iscsi`, CSI | Storage Backend의 수명 정책에 따름 |

과거에는 Cloud Disk와 Storage 제품별 In-tree Volume Plugin이 다수 포함됐지만 현재 외부 Storage 연동의 중심은 CSI(Container Storage Interface)이다. `cephfs` In-tree Driver는 Kubernetes 1.31부터 제공되지 않고 GlusterFS In-tree Driver는 1.26부터 제공되지 않는다. Ceph와 Cloud Disk 같은 Storage는 해당 CSI Driver의 지원 상태를 확인해야 한다.

## 2 ) Control Plane과 Worker의 Volume 연결

---

Master 또는 관리 Client에서 Pod Manifest를 적용하면 Control Plane은 Pod와 Volume 설정을 저장하고 실행할 Worker를 선택한다. 선택된 Worker의 kubelet이 Volume을 준비한 뒤 Container Runtime에 Container 실행을 요청한다.

```text
Master·관리 Client
  kubectl apply
       │
       ▼
Control Plane
  API Server가 Pod와 Volume 설정 저장
       │
       ▼
Scheduler가 Volume 조건을 고려하여 Worker 선택
       │
       ▼
Worker의 kubelet
  Volume Plugin 또는 CSI Driver로 Mount 준비
       │
       ▼
Container Runtime
  volumeMounts 경로를 Container에 연결
```

Pod에 직접 정의하는 Volume과 PV·PVC를 사용하는 Volume은 Control Plane에서 처리되는 과정이 다르다. `emptyDir`과 `hostPath`는 Pod Spec을 기준으로 Worker의 kubelet이 준비하고, PVC는 먼저 조건에 맞는 PV와 Binding되어야 Pod에서 사용할 수 있다.

## 3 ) emptyDir

---

`emptyDir`은 Pod가 Worker에 배치될 때 생성되는 임시 Volume이다. Container가 재시작되어도 같은 Pod가 유지되는 동안에는 Data가 남지만 Pod가 삭제되거나 다른 Pod로 교체되면 Data도 삭제된다.

`emptyDir`은 Node의 임의 경로나 기존 File을 선택하는 Volume이 아니다. Pod 전용 임시 작업 공간이나 같은 Pod 안의 Container 간 File 공유에 사용한다.

다음 내용을 `sample-emptydir.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-emptydir
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      volumeMounts:
        - name: cache-volume
          mountPath: /cache
  volumes:
    - name: cache-volume
      emptyDir: {}
```

Master 또는 관리 Client에서 Pod를 생성하고 `/cache` Mount를 확인한다.

```bash
kubectl apply -f sample-emptydir.yaml
kubectl wait --for=condition=Ready pod/sample-emptydir --timeout=120s
kubectl exec sample-emptydir -- df -h /cache
```

Container가 재시작되더라도 Pod가 동일하면 `emptyDir`은 유지된다. Pod 자체를 삭제하면 Volume과 Data도 함께 삭제된다.

## 4 ) emptyDir 용량과 Memory 사용

---

`emptyDir.sizeLimit`은 Pod가 사용할 임시 Volume 크기의 상한을 지정한다. 다음 내용을 `sample-emptydir-limit.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-emptydir-limit
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      volumeMounts:
        - name: cache-volume
          mountPath: /cache
  volumes:
    - name: cache-volume
      emptyDir:
        sizeLimit: 128Mi
```

Pod를 생성하고 별도 Terminal에서 상태를 감시한다.

```bash
kubectl apply -f sample-emptydir-limit.yaml
kubectl get pod sample-emptydir-limit --watch
```

다른 Terminal에서 150MiB File 생성을 시도한다.

```bash
kubectl exec sample-emptydir-limit -- \
  dd if=/dev/zero of=/cache/dummy bs=1M count=150
```

`sizeLimit`을 초과했다고 항상 쓰기 작업이 즉시 실패하거나 Pod가 같은 시점에 종료되는 것은 아니다. kubelet은 Node의 Ephemeral Storage 사용량과 Eviction 조건을 함께 평가하므로 Pod 상태와 Event를 확인해야 한다.

```bash
kubectl describe pod sample-emptydir-limit
kubectl get events --sort-by=.lastTimestamp
```

Disk 대신 Memory 기반 `tmpfs`를 사용하려면 `medium: Memory`를 지정한다.

```yaml
volumes:
  - name: cache-volume
    emptyDir:
      medium: Memory
      sizeLimit: 128Mi
```

Memory 기반 `emptyDir`에 기록한 Data는 해당 Container의 Memory 사용량으로 계산될 수 있으므로 Container의 Memory Limit과 함께 설계해야 한다.

## 5 ) hostPath

---

`hostPath`는 Pod가 실행되는 Worker의 File이나 Directory를 Container에 Mount한다. Node별 Log 수집 Agent나 Metric 수집기처럼 Node File System 접근이 필요한 Workload에 사용할 수 있다.

대표적인 사용 사례는 다음과 같다.

- Fluentd, Promtail과 Filebeat가 `/var/log` 또는 `/var/log/pods`의 Log를 수집하는 경우

- Container Runtime 상태를 확인하기 위해 Runtime Socket에 접근하는 경우

- Node Exporter나 cAdvisor가 `/proc`, `/sys` 등 Node 정보를 읽는 경우

- 단일 Node 개발 환경에서 Local File을 연결하는 경우

`hostPath` Data는 Node에 종속된다. Pod가 다른 Worker에서 실행되면 같은 경로 이름이더라도 기존 Node의 Data를 읽을 수 없으므로 일반적인 Database 영구 저장 용도로는 적합하지 않다.

| `hostPath.type` | 동작 |
|---|---|
| `DirectoryOrCreate` | Directory가 없으면 생성 |
| `Directory` | 기존 Directory가 있어야 함 |
| `FileOrCreate` | File이 없으면 생성 |
| `File` | 기존 File이 있어야 함 |
| `Socket` | 기존 UNIX Socket이어야 함 |
| `CharDevice` | 기존 Character Device여야 함 |
| `BlockDevice` | 기존 Block Device여야 함 |

Host의 `/etc`나 `/root`를 쓰기 가능한 상태로 Mount하면 Container 침해가 Node 전체의 침해로 이어질 수 있다. 실습에서는 전용 Directory만 사용한다.

다음 내용을 `sample-hostpath.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-hostpath
spec:
  nodeSelector:
    kubernetes.io/hostname: worker1
  containers:
    - name: nginx-container
      image: nginx:stable
      volumeMounts:
        - name: hostpath-sample
          mountPath: /srv
  volumes:
    - name: hostpath-sample
      hostPath:
        path: /var/local/kubernetes/hostpath-demo
        type: DirectoryOrCreate
```

Master 또는 관리 Client에서 적용한 뒤 Pod가 `worker1`에 배치됐는지 확인한다.

```bash
kubectl apply -f sample-hostpath.yaml
kubectl wait --for=condition=Ready pod/sample-hostpath --timeout=120s
kubectl get pod sample-hostpath -o wide
kubectl describe pod sample-hostpath
```

Container에서 File을 생성한다.

```bash
kubectl exec sample-hostpath -- \
  sh -c "echo 'hostPath-test' > /srv/test.txt"
```

`worker1`에서 같은 File을 확인한다.

```bash
sudo cat /var/local/kubernetes/hostpath-demo/test.txt
```

운영 환경에서 Host 정보를 읽기만 한다면 `volumeMounts[].readOnly: true`를 우선 검토하고 Mount 경로를 필요한 범위로 제한한다.

## 6 ) Downward API Volume

---

Downward API는 Application이 API Server와 직접 통신하지 않고 자신의 Pod Metadata와 Resource 정보를 확인하게 한다. 환경 변수 방식은 [Kubernetes 환경 변수와 Secret, ConfigMap](/cloud-native-34-kubernetes-env-secret-configmap/)에서 다뤘으며, Volume 방식은 정보를 File로 제공한다.

다음 내용을 `sample-downward-api.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-downward-api
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      resources:
        requests:
          cpu: 100m
      volumeMounts:
        - name: downward-api-volume
          mountPath: /srv
          readOnly: true
  volumes:
    - name: downward-api-volume
      downwardAPI:
        items:
          - path: podname
            fieldRef:
              fieldPath: metadata.name
          - path: cpu-request
            resourceFieldRef:
              containerName: nginx-container
              resource: requests.cpu
```

Master 또는 관리 Client에서 적용하고 생성된 File과 값을 확인한다.

```bash
kubectl apply -f sample-downward-api.yaml
kubectl wait --for=condition=Ready \
  pod/sample-downward-api --timeout=120s
kubectl exec sample-downward-api -- ls -l /srv
kubectl exec sample-downward-api -- cat /srv/podname
kubectl exec sample-downward-api -- cat /srv/cpu-request
```

API Server에 저장된 Pod Spec을 Worker의 kubelet이 확인하여 `podname`과 `cpu-request` File을 구성한다. Container Application에는 Pod 조회를 위한 Kubernetes Client나 별도 RBAC 권한이 필요하지 않다.

## 7 ) projected Volume

---

`projected` Volume은 여러 Volume Source를 하나의 Directory에 배치한다. Secret 인증 정보, ConfigMap 설정과 Downward API Metadata를 같은 Mount 경로에 제공해야 할 때 사용할 수 있다.

```yaml
volumes:
  - name: application-config
    projected:
      sources:
        - secret:
            name: sample-db-auth
        - configMap:
            name: sample-configmap
        - downwardAPI:
            items:
              - path: podname
                fieldRef:
                  fieldPath: metadata.name
```

`projected`에 포함하는 Secret과 ConfigMap은 Pod와 같은 Namespace에 있어야 한다. Volume Source별 Key가 같은 File 경로를 사용하지 않는지도 확인한다.

## 8 ) PersistentVolume과 PersistentVolumeClaim

---

> **PersistentVolume(PV)**
>
> Cluster에 제공되는 Storage 용량과 연결 정보를 나타내는 Cluster 범위 Resource이다.

> **PersistentVolumeClaim(PVC)**
>
> Namespace 안의 Workload가 필요한 Storage 용량과 Access Mode를 요청하는 Resource이다.

Pod에 직접 정의한 Volume은 Pod Spec과 함께 관리하지만 PV와 PVC는 개별 Kubernetes Resource로 생성한다. PV의 수명은 Pod와 분리되며 PVC 삭제 후의 처리 방식은 Reclaim Policy에 따라 달라진다.

| 구성 요소 | 담당 관점 | 역할 |
|---|---|---|
| StorageClass | Cluster 관리자 | Storage 종류, Provisioner와 정책 정의 |
| PVC | Application 개발자 | 필요한 용량, Access Mode와 StorageClass 요청 |
| CSI Driver 또는 Provisioner | Storage 연동 구성 요소 | 실제 Storage 생성·연결 작업 수행 |
| PV | Control Plane에서 관리하는 Resource | 제공된 Storage를 Kubernetes Resource로 표현 |

영구 Storage에는 Local Disk, Network File System, Cloud Disk와 분산 Storage 등을 연결할 수 있다.

| Storage | 현재 연결 방식 또는 상태 |
|---|---|
| AWS Elastic Block Store | AWS EBS CSI Driver 사용. In-tree `awsElasticBlockStore` Type은 제거됨 |
| GCE Persistent Disk | GCE PD CSI Driver 사용. In-tree Type은 Deprecated 상태이며 CSI Driver로 Redirect됨 |
| Azure File | Azure File CSI Driver 사용. In-tree Type은 Deprecated 상태이며 CSI Driver로 Redirect됨 |
| NFS | 기존 NFS Export를 직접 Mount할 수 있음. Dynamic Provisioning에는 외부 Provisioner 필요 |
| iSCSI | 미리 준비한 iSCSI Volume 연결 가능 |
| Ceph RBD·CephFS | In-tree Driver는 제거됐으며 Ceph CSI Driver 사용 |
| OpenStack Cinder | In-tree Driver는 제거됐으며 Cinder CSI Driver 사용 |
| GlusterFS | In-tree Driver가 제거됨 |
| CSI | Kubernetes 외부 Storage Driver를 연결하는 표준 Interface |

In-tree Driver가 제거됐다는 것은 해당 Storage 제품 자체를 사용할 수 없다는 의미가 아니다. 지원되는 CSI Driver를 Cluster에 설치하고 StorageClass와 PV가 그 Driver를 사용하도록 구성해야 한다.

Static Provisioning에서는 관리자가 Storage와 PV를 먼저 만들고 PVC가 조건에 맞는 PV를 선택한다. Dynamic Provisioning에서는 PVC가 요청한 StorageClass의 Provisioner가 PV와 실제 Volume을 생성한다.

```text
Static Provisioning
Storage 준비 → PV 생성 → PVC 요청 → PV·PVC Binding → Pod Mount

Dynamic Provisioning
StorageClass 준비 → PVC 요청 → Provisioner가 Volume·PV 생성
                  → PV·PVC Binding → Pod Mount
```

## 9 ) Access Mode와 Reclaim Policy

---

Access Mode는 Node가 Volume을 어떤 방식으로 Mount하도록 요청하는지 나타낸다. Storage가 해당 Mode를 실제로 지원해야 한다.

| Access Mode | 약어 | 의미 |
|---|---|---|
| `ReadWriteOnce` | RWO | 하나의 Node에서 Read·Write Mount |
| `ReadOnlyMany` | ROX | 여러 Node에서 Read-only Mount |
| `ReadWriteMany` | RWX | 여러 Node에서 Read·Write Mount |

`ReadWriteOnce`는 Pod 하나만 접근할 수 있다는 의미가 아니다. 같은 Node의 여러 Pod가 접근할 수 있으므로 단일 Pod 접근을 요구하면 Storage Driver의 `ReadWriteOncePod` 지원 여부를 확인해야 한다.

Reclaim Policy는 PVC가 삭제되어 PV가 해제됐을 때 Storage를 처리하는 방법이다.

| Reclaim Policy | 동작 | 현재 상태 |
|---|---|---|
| `Retain` | PV와 Data를 남기고 관리자가 수동 처리 | 사용 가능 |
| `Delete` | 지원하는 Storage에서 PV와 실제 Volume 삭제 | 사용 가능 |
| `Recycle` | 기본 정리 후 PV 재사용 | Deprecated |

`Recycle`은 Deprecated 상태이므로 신규 구성에서는 Dynamic Provisioning과 `Retain` 또는 `Delete` 정책을 사용한다.

## 10 ) Local hostPath PV와 PVC

---

다음 실습은 `worker1`의 Local Directory를 `hostPath` PV로 제공한다. `hostPath` PV는 단일 Node 테스트 용도이며 Multi-node Cluster의 일반적인 영구 Storage로 사용하지 않는다.

먼저 `worker1`에서 Directory를 생성한다.

```bash
# worker1에서 실행
sudo mkdir -p /var/local/kubernetes/local-pv
```

다음 내용을 `pv.yaml`로 저장한다. `nodeAffinity`는 이 PV가 `worker1`의 Storage라는 사실을 Scheduler에 전달한다.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - worker1
  hostPath:
    path: /var/local/kubernetes/local-pv
    type: Directory
```

| Field | 역할 |
|---|---|
| `capacity.storage: 5Gi` | PV가 제공하는 용량 |
| `ReadWriteOnce` | 하나의 Node에서 Read·Write Mount 허용 |
| `Retain` | PVC가 삭제돼도 Data를 자동 삭제하지 않음 |
| `storageClassName: manual` | 같은 Class를 요청한 PVC와 Binding |
| `nodeAffinity` | Storage가 있는 `worker1`로 Scheduling 제한 |
| `hostPath` | `worker1`의 실제 Directory 지정 |

Master 또는 관리 Client에서 PV를 생성하고 확인한다.

```bash
kubectl apply -f pv.yaml
kubectl get persistentvolumes
kubectl describe persistentvolume local-pv
```

다음 내용을 `pvc.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: local-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: manual
```

PVC를 생성하고 PV와 PVC의 `STATUS`가 `Bound`인지 확인한다.

```bash
kubectl apply -f pvc.yaml
kubectl get persistentvolumes
kubectl get persistentvolumeclaims
kubectl describe persistentvolumeclaim local-pvc
```

PVC는 요청 용량 이상이면서 `storageClassName`과 Access Mode가 호환되는 PV와 Binding된다. 요청 용량과 PV 용량이 반드시 정확히 같아야 하는 것은 아니다.

PVC가 `Pending`이면 `storageClassName`, Access Mode, 요청 용량과 PV 상태를 비교한다.

## 11 ) PVC를 Pod에 Mount

---

다음 내용을 `pod.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: local-pod
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      volumeMounts:
        - name: local-storage
          mountPath: /usr/share/nginx/html
  volumes:
    - name: local-storage
      persistentVolumeClaim:
        claimName: local-pvc
```

Master 또는 관리 Client에서 Pod를 생성한다. Scheduler는 PV의 Node Affinity를 확인하여 Pod를 `worker1`에 배치한다.

```bash
kubectl apply -f pod.yaml
kubectl wait --for=condition=Ready pod/local-pod --timeout=120s
kubectl get pod local-pod -o wide
```

`worker1`에서 File을 생성한다.

```bash
# worker1에서 실행
echo 'Hello Kubernetes Local PV' | \
  sudo tee /var/local/kubernetes/local-pv/test.txt
```

Master 또는 관리 Client에서 Container의 Mount 경로를 통해 같은 File을 확인한다.

```bash
kubectl exec local-pod -- \
  cat /usr/share/nginx/html/test.txt
```

## 12 ) NFS Server 준비

---

NFS(Network File System)는 여러 Node가 Network를 통해 같은 File System을 Mount할 수 있다. 다음 실습은 NFS Server의 `/nfs/k8s`를 Kubernetes의 Static PV로 연결한다.

| 대상 | 예시 | 역할 |
|---|---|---|
| NFS Server | `192.168.0.100` | 공유 Directory Export |
| Master·관리 Client | kubeconfig가 설정된 Host | PV·PVC·Pod 생성과 상태 확인 |
| Kubernetes Node | Master, `worker1`, `worker2` | NFS Client 설치와 Mount 수행 |

실제 NFS Server IP가 다르면 이후 명령과 `nfs-pv.yaml`의 `server` 값을 모두 같은 주소로 변경한다.

NFS Server에서 Package와 공유 Directory를 준비한다.

```bash
# NFS Server에서 실행
sudo apt update
sudo apt install -y nfs-kernel-server
sudo mkdir -p /nfs/k8s
sudo chmod 777 /nfs/k8s
```

`chmod 777`은 권한 문제를 줄이기 위한 실습 설정이다. 운영 환경에서는 NFS를 사용하는 UID와 GID에 맞춰 필요한 권한만 부여한다.

NFS Server의 `/etc/exports`에 다음 설정을 추가한다.

```text
/nfs/k8s *(rw,sync,no_subtree_check,no_root_squash)
```

`*`와 `no_root_squash`는 모든 Client와 Remote Root 접근을 허용하므로 운영 설정으로 적합하지 않다. 운영 환경에서는 Kubernetes Node 대역을 명시하고 Root Mapping 정책을 제한한다.

변경한 Export 설정을 적용하고 확인한다.

```bash
# NFS Server에서 실행
sudo exportfs -ra
sudo exportfs -v
```

## 13 ) Kubernetes Node의 NFS 연결 확인

---

NFS Volume을 Mount할 수 있도록 Pod가 배치될 수 있는 모든 Linux Node에 NFS Client Package를 설치한다.

```bash
# 각 Kubernetes Node에서 실행
sudo apt update
sudo apt install -y nfs-common
```

각 Node에서 NFS Server와의 연결을 직접 확인한다.

```bash
# 각 Kubernetes Node에서 실행
sudo mkdir -p /mnt/nfs-test
sudo mount -t nfs 192.168.0.100:/nfs/k8s /mnt/nfs-test
df -h /mnt/nfs-test
sudo umount /mnt/nfs-test
```

Mount가 실패하면 Kubernetes Manifest를 적용하기 전에 Server IP, 사용하는 NFS Version에 필요한 Port, Export 설정, Firewall과 `nfs-common` 설치 상태를 확인한다.

## 14 ) NFS PV와 PVC

---

다음 내용을 `nfs-pv.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 10Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs-storage
  nfs:
    server: 192.168.0.100
    path: /nfs/k8s
```

이 예제는 기존 NFS Export를 관리자가 PV로 등록하는 Static Provisioning이다. `storageClassName`은 PVC와 PV를 연결하는 Class 이름이며, 이 Manifest만으로 NFS Storage를 동적으로 생성하는 Provisioner가 설치되지는 않는다.

```bash
kubectl apply -f nfs-pv.yaml
kubectl get persistentvolume nfs-pv
```

다음 내용을 `nfs-pvc.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
  storageClassName: nfs-storage
```

PVC를 생성한 뒤 `nfs-pv`와 `nfs-pvc`가 Binding됐는지 확인한다.

```bash
kubectl apply -f nfs-pvc.yaml
kubectl get persistentvolumes
kubectl get persistentvolumeclaims
kubectl describe persistentvolumeclaim nfs-pvc
```

## 15 ) NFS PVC를 Pod에 Mount

---

다음 내용을 `nfs-pod.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nfs-test-pod
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      volumeMounts:
        - name: nfs-volume
          mountPath: /usr/share/nginx/html
  volumes:
    - name: nfs-volume
      persistentVolumeClaim:
        claimName: nfs-pvc
```

Master 또는 관리 Client에서 Pod를 생성하고 Mount 상태를 확인한다.

```bash
kubectl apply -f nfs-pod.yaml
kubectl wait --for=condition=Ready pod/nfs-test-pod --timeout=120s
kubectl get pod nfs-test-pod -o wide
kubectl describe pod nfs-test-pod
```

Pod에서 NFS Volume에 File을 생성한다.

```bash
kubectl exec nfs-test-pod -- \
  sh -c "echo 'Hello Kubernetes NFS' > /usr/share/nginx/html/index.html"
```

NFS Server에서 같은 File을 확인한다.

```bash
# NFS Server에서 실행
cat /nfs/k8s/index.html
```

NFS Mount 문제는 Pod Event와 Worker의 kubelet 상태를 함께 확인한다.

```bash
kubectl describe pod nfs-test-pod

# 해당 Worker에서 실행
sudo journalctl -u kubelet --since "10 minutes ago"
```

## 16 ) 실습 Resource 정리

---

Master 또는 관리 Client에서 Pod를 먼저 제거한다.

```bash
kubectl delete pod nfs-test-pod --ignore-not-found
kubectl delete pod local-pod --ignore-not-found
kubectl delete pod sample-downward-api --ignore-not-found
kubectl delete pod sample-hostpath --ignore-not-found
kubectl delete pod sample-emptydir-limit --ignore-not-found
kubectl delete pod sample-emptydir --ignore-not-found
```

PVC가 더 이상 사용되지 않는지 확인한 뒤 PVC와 PV를 제거한다.

```bash
kubectl delete persistentvolumeclaim nfs-pvc --ignore-not-found
kubectl delete persistentvolume nfs-pv --ignore-not-found
kubectl delete persistentvolumeclaim local-pvc --ignore-not-found
kubectl delete persistentvolume local-pv --ignore-not-found
```

두 PV의 Reclaim Policy가 `Retain`이므로 Kubernetes Resource를 삭제해도 `worker1`과 NFS Server의 실제 File은 자동 삭제되지 않는다. Data가 필요하지 않은지 확인한 뒤 각 Machine에서 별도로 관리한다.

## 전체 정리

---

> **최종 정리**
>
> - `emptyDir`은 Pod 수명에 연결된 임시 Volume이며 Disk 또는 Memory를 사용할 수 있다.
>
> - `hostPath`는 특정 Worker의 File System에 직접 연결되므로 Node 종속성과 Host 침해 위험을 함께 고려해야 한다.
>
> - Downward API Volume은 Pod와 Container 정보를 File로 제공하고 `projected` Volume은 Secret, ConfigMap과 Downward API 등을 하나의 Directory에 배치한다.
>
> - PV는 Cluster가 제공하는 Storage이고 PVC는 Namespace의 Workload가 필요한 Storage를 요청하는 Resource이다.
>
> - Static Provisioning은 관리자가 PV를 미리 만들고 Dynamic Provisioning은 StorageClass와 Provisioner가 PVC 요청에 따라 Volume을 생성한다.
>
> - Local `hostPath` PV는 단일 Node 테스트에 적합하고 NFS PV는 여러 Node에서 같은 Network File System을 사용할 수 있다.

다음 단계에서는 [Kubernetes Resource 관리와 Autoscaling](/cloud-native-36-kubernetes-resource-management-autoscaling/)에서 Container와 Namespace의 Resource 제한, Eviction과 Autoscaling을 다룬다.
