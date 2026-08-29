---
title: Kubernetes Pod Lifecycle과 kubectl wait
description: Deployment 재시작과 generateName 사용법, Pod Phase와 kubectl 상태 표시의 차이, Condition 기반 작업 완료 대기 정리
date: 2026-08-26
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Kubernetes Resource를 연속해서 조작할 때는 앞에서 요청한 Resource가 의도한 상태에 도달했는지 확인해야 한다. Deployment의 Pod를 다시 생성하거나 Pod가 Ready 상태가 될 때까지 기다리려면 Controller의 역할, Pod Lifecycle과 `kubectl wait`의 Condition을 함께 이해해야 한다.

## 1 ) Deployment의 Pod 재시작

---

Pod는 직접 재부팅하는 Virtual Machine과 다르다. Deployment가 관리하는 Pod를 다시 시작하려면 Deployment의 Pod Template을 갱신하여 Controller가 기존 Pod를 교체하도록 요청한다.

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

Master에서 Deployment를 적용한다.

```bash
kubectl apply -f sample-deployment.yaml
```

Deployment와 Pod를 확인한다.

```bash
kubectl get deployment sample-deployment
kubectl get pods -l app=sample-app
```

### rollout restart

Deployment가 관리하는 Pod를 순차적으로 교체한다.

```bash
kubectl rollout restart deployment/sample-deployment
```

| 구성 | 동작 |
|---|---|
| `rollout restart` | Workload의 Pod Template을 갱신하여 새 Rollout 시작 |
| `deployment/sample-deployment` | 재시작할 Resource 종류와 이름 |

Rollout 상태를 확인한다.

```bash
kubectl rollout status deployment/sample-deployment
```

Pod 이름과 생성 시간이 바뀌는지 확인한다.

```bash
kubectl get pods -l app=sample-app
```

`rollout restart`는 다음과 같은 상황에서 활용할 수 있다.

- Application 시작 시 수행되는 초기화 처리를 다시 실행한다.

- Secret이나 ConfigMap에서 주입된 환경 변수를 새 Pod에 다시 반영한다.

- 새로운 Pod 생성 과정을 통해 일시적인 상태를 초기화한다.

Deployment Controller는 Control Plane에서 새 ReplicaSet과 Pod 상태를 조정한다. Scheduler가 새 Pod의 Worker를 선택하면 해당 Worker의 kubelet이 Container를 실행한다.

### 독립 Pod와 Controller 관리 Pod

`rollout restart`는 Deployment, StatefulSet과 DaemonSet처럼 Rollout을 지원하는 Workload에 사용한다. Controller에 연결되지 않은 독립 Pod에는 사용할 수 없다.

독립 Pod를 삭제하면 자동으로 대체 Pod를 생성할 상위 Controller가 없다.

```text
Deployment가 관리하는 Pod 삭제
    → Deployment Controller가 부족한 Replica 감지
    → 대체 Pod 생성

독립 Pod 삭제
    → 대체 Pod를 생성할 Controller 없음
```

Pod를 안정적으로 운영하려면 Pod를 직접 생성하기보다 목적에 맞는 Controller를 통해 관리한다.

## 2 ) metadata.name과 generateName

---

Kubernetes Resource는 일반적으로 `metadata.name`으로 고정된 이름을 지정한다.

```yaml
metadata:
  name: sample-pod
```

같은 종류와 Namespace에 동일한 이름의 Resource가 있으면 다시 생성할 수 없다.

### generateName

> **generateName**
>
> Resource 생성 요청마다 API Server가 고유한 접미사를 추가할 수 있도록 이름의 접두사를 지정하는 Field이다.

다음 내용을 `sample-generatename.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  generateName: sample-generatename-
spec:
  containers:
    - name: nginx-container
      image: nginx
```

`create`로 Resource를 생성한다.

```bash
kubectl create -f sample-generatename.yaml
```

생성된 이름을 확인한다.

```bash
kubectl get pods
```

출력 예시는 다음과 같다.

```text
NAME                          READY   STATUS    RESTARTS   AGE
sample-generatename-k7m2p     1/1     Running   0          10s
```

같은 File로 다시 `create`하면 다른 접미사를 가진 새 Pod가 생성된다.

```bash
kubectl create -f sample-generatename.yaml
kubectl get pods
```

`generateName`은 매 요청마다 새 Resource를 만들 때 사용한다. 동일한 Resource를 반복 갱신하는 선언형 `apply`에는 안정적인 `metadata.name`이 필요하므로 `generateName` 예제는 `create`로 실행한다.

## 3 ) Pod Lifecycle

---

> **Pod Phase**
>
> Pod Lifecycle의 상위 상태를 나타내는 값이다. `Pending`, `Running`, `Succeeded`, `Failed`, `Unknown` 중 하나로 기록된다.

Pod Phase는 Pod 전체의 큰 상태를 표현한다. `kubectl get pods`의 `STATUS` 열에는 Phase뿐 아니라 Container 생성과 재시작 과정에서 발생한 Reason도 표시될 수 있다.

### Pod Phase

| Phase | 의미 |
|---|---|
| `Pending` | Pod가 승인되었지만 Container가 아직 준비되지 않았으며 Scheduling이나 Image Download를 기다릴 수 있는 상태 |
| `Running` | Pod가 Node에 Binding되었고 모든 Container가 생성되었으며 하나 이상이 실행 또는 시작·재시작 중인 상태 |
| `Succeeded` | Pod의 모든 Container가 성공적으로 종료되었고 다시 시작되지 않는 상태 |
| `Failed` | 모든 Container가 종료되었고 하나 이상이 실패로 종료되었으며 다시 시작되지 않는 상태 |
| `Unknown` | 일반적으로 Node 통신 문제로 Pod 상태를 확인할 수 없는 상태 |

`Completed`는 `kubectl get pods`의 `STATUS`에서 성공적으로 끝난 Pod를 표현할 때 보이는 값이며 Pod Phase의 실제 값은 `Succeeded`이다. Job이나 CronJob이 만든 완료형 Pod에서 주로 확인할 수 있다.

### kubectl에 표시되는 상태와 Reason

| 표시 | 의미 | 확인할 내용 |
|---|---|---|
| `ContainerCreating` | Volume Mount와 Network 설정 등 Container 생성 진행 | `kubectl describe pod`의 Event |
| `CrashLoopBackOff` | Container가 반복 실패하여 재시작 대기 시간이 증가 | Application Log, Command, 환경 변수, Probe |
| `ErrImagePull` | Image를 가져오는 첫 시도가 실패 | Image 이름, Tag, Registry 인증 |
| `ImagePullBackOff` | Image Pull 실패가 반복되어 재시도 대기 | Registry 접근, ImagePullSecret |
| `OOMKilled` | Memory 제한 또는 Node Memory 상황으로 Process 종료 | Resource Limit과 사용량 |
| `Terminating` | Graceful Termination과 Resource 정리 진행 | Finalizer, Volume, Node 상태 |
| `Init:0/N` | N개 Init Container 중 완료된 수가 0개 | Init Container Log와 상태 |

이 값들을 모두 Pod Phase로 분류해서는 안 된다. 예를 들어 Pod Phase가 `Running`이어도 Container 하나가 `CrashLoopBackOff` 상태일 수 있다.

### 상태 확인

Pod 목록을 확인한다.

```bash
kubectl get pods
```

Pod의 Phase만 확인한다.

```bash
kubectl get pod sample-pod -o jsonpath='{.status.phase}'
```

Container별 상태와 Event를 확인한다.

```bash
kubectl describe pod sample-pod
```

Control Plane의 API Server에는 Pod Status와 Condition이 저장된다. Worker의 kubelet은 실제 Container 상태를 관찰하여 API Server에 보고하고, kubectl은 저장된 상태를 조회한다.

## 4 ) Pod Condition

---

Condition은 Pod가 특정 조건을 만족하는지를 나타낸다. `kubectl wait`는 이 값을 기준으로 다음 작업을 시작할 시점을 결정할 수 있다.

| Condition | 의미 |
|---|---|
| `PodScheduled` | Scheduler가 Pod를 실행할 Node에 Binding함 |
| `Initialized` | 모든 Init Container가 성공적으로 완료됨 |
| `ContainersReady` | Pod의 모든 Container가 Ready 상태임 |
| `Ready` | Pod가 Service 요청을 받을 준비가 됨 |

Pod의 Condition을 확인한다.

```bash
kubectl get pod sample-pod -o jsonpath='{.status.conditions}'
```

`Running`은 Container가 실행 중임을 나타내지만 Application이 Traffic을 받을 준비가 끝났다는 의미와 항상 같지는 않다. 후속 작업에서 Service 제공 가능 상태가 필요하면 `Ready` Condition을 기준으로 기다린다.

## 5 ) kubectl wait

---

> **kubectl wait**
>
> 하나 이상의 Resource가 지정한 Condition, 생성 또는 삭제 상태에 도달할 때까지 기다리는 명령이다.

기본 Timeout은 30초이다. Image Download나 Application 초기화 시간이 더 필요한 실습에서는 `--timeout`을 명시한다.

### Ready 상태 대기

`sample-pod`가 Ready 상태가 될 때까지 최대 60초 동안 기다린다.

```bash
kubectl apply -f sample-pod.yaml
kubectl wait --for=condition=Ready pod/sample-pod --timeout=60s
```

성공하면 다음과 같은 결과가 출력된다.

```text
pod/sample-pod condition met
```

### Scheduling 완료 대기

현재 Namespace의 모든 Pod가 Node에 Scheduling될 때까지 기다린다.

```bash
kubectl wait --for=condition=PodScheduled pods --all --timeout=60s
```

`--all`은 지정한 Resource 종류의 모든 대상을 선택한다. 다른 Namespace의 Pod까지 포함하려면 `--all-namespaces`를 추가해야 한다.

### Phase 값 대기

Pod Phase가 `Running`이 될 때까지 기다린다.

```bash
kubectl wait pod/sample-pod \
  --for=jsonpath='{.status.phase}'=Running \
  --timeout=60s
```

Application 사용 가능 여부가 목적이라면 Phase보다 `Ready` Condition이 더 적절할 수 있다.

### 삭제 완료 대기

일반적인 `kubectl delete`는 기본적으로 삭제 완료를 기다린다.

```bash
kubectl delete pod sample-pod
```

삭제 요청과 대기를 분리해야 한다면 먼저 기다리지 않고 삭제를 요청한다.

```bash
kubectl delete pod sample-pod --wait=false
```

이후 Resource가 사라질 때까지 기다린다.

```bash
kubectl wait --for=delete pod/sample-pod --timeout=60s
```

현재 Namespace의 모든 Pod에 삭제를 요청하고 완료 대기를 분리할 수도 있다.

```bash
kubectl delete pods --all --wait=false
kubectl wait --for=delete pods --all --timeout=60s
```

두 번째 명령은 실행 시점에 남아 있는 Pod를 대상으로 기다린다. 이미 모든 Pod가 삭제되어 일치하는 Resource가 없다면 별도의 대기가 필요하지 않다.

여러 Pod를 대상으로 할 때도 Timeout은 명령 전체의 대기 한도를 나타낸다. Pod마다 정해진 시간을 순서대로 더해 기다린다는 의미가 아니다.

### Timeout 처리

지정한 시간 안에 상태가 충족되지 않으면 명령은 실패 상태로 종료된다.

```text
error: timed out waiting for the condition on pods/sample-pod
```

Timeout을 무조건 늘리기 전에 `kubectl get pods`와 `kubectl describe pod`로 Scheduling, Image Pull, Container 실행과 Probe 상태를 확인한다.

## 6 ) 실습 Resource 정리

---

`generateName`으로 만든 Pod를 이름 Prefix와 Label 없이 한꺼번에 선택하기는 어렵다. 목록을 확인한 뒤 생성된 이름을 지정하여 삭제한다.

```bash
kubectl get pods
kubectl delete pod <generated-pod-name>
```

Deployment를 삭제한다.

```bash
kubectl delete -f sample-deployment.yaml
```

Deployment를 삭제하면 Deployment가 관리하던 ReplicaSet과 Pod도 함께 정리된다.

## 전체 정리

---

> **최종 정리**
>
> - `rollout restart`는 Deployment 같은 Workload의 Pod Template을 갱신하여 Controller가 Pod를 교체하도록 한다.
>
> - 독립 Pod는 상위 Controller가 없으므로 삭제 후 자동으로 대체되지 않는다.
>
> - `generateName`은 생성 요청마다 고유한 이름이 필요한 Resource에 사용하며 `create`와 결합한다.
>
> - Pod Phase와 `CrashLoopBackOff`, `ContainerCreating` 같은 kubectl 상태 표시는 구분해서 해석한다.
>
> - Worker의 kubelet이 Container 상태를 API Server에 보고하면 kubectl이 Control Plane에 저장된 Status와 Condition을 조회한다.
>
> - `kubectl wait`는 Ready, Scheduling, Phase 또는 삭제 완료를 후속 작업의 조건으로 사용할 수 있다.
