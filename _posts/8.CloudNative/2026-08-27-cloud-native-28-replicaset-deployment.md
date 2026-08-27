---
title: Kubernetes ReplicaSet과 Deployment
description: Label Selector 기반 ReplicaSet의 Pod 수 조정과 Deployment의 Rolling Update, Rollback, Pause 및 Scaling 정리
date: 2026-08-27
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
  - ReplicaSet
  - Deployment
---

ReplicaSet은 Label Selector와 일치하는 Pod를 지정한 수만큼 유지한다. Deployment는 ReplicaSet을 한 단계 위에서 관리하여 Pod 수 유지뿐 아니라 Application의 Rolling Update와 Rollback까지 수행한다.

## 1 ) ReplicaSet

---

> **ReplicaSet**
>
> Label Selector와 일치하는 Pod가 `spec.replicas`에 지정한 수만큼 실행되도록 지속적으로 조정하는 Controller Resource이다.

Pod만 직접 생성하면 Container Process가 실패했을 때 kubelet이 Container를 재시작할 수는 있지만, Pod가 삭제되거나 Node 장애로 사라진 Pod를 대신할 새 Pod를 생성하는 상위 Controller는 없다. ReplicaSet은 현재 Pod 수가 원하는 수보다 적으면 새 Pod를 만들고, 많으면 일치하는 Pod를 줄인다.

ReplicationController도 Pod 복제 수를 관리하지만 Legacy Resource이다. 신규 구성에서는 ReplicaSet을 사용하며, 일반적인 Application은 ReplicaSet을 직접 배포하기보다 Deployment를 통해 관리한다.

### Control Plane과 Worker의 조정 흐름

ReplicaSet의 상태 조정은 다음과 같이 이루어진다.

```text
Control Plane
ReplicaSet Controller
  │ Label Selector와 일치하는 Pod 수 계산
  ├── 부족함 ──▶ Pod 생성 요청
  └── 초과함 ──▶ Pod 삭제 요청
                    │
                    ▼
               Scheduler
                    │ Worker 선택
                    ▼
Worker의 kubelet ──▶ Container Runtime ──▶ Container 실행
```

Worker나 Pod에 장애가 생기면 Control Plane은 API Server에 기록된 상태를 기준으로 부족한 Replica를 감지한다. Scheduler가 새 Pod를 실행할 Worker를 선택하고 해당 Worker의 kubelet이 Container를 실행한다.

ReplicaSet은 Application 자체의 Data 복제나 Session 복구를 수행하지 않는다. 여러 Pod가 대체 가능하도록 Application을 구성하고 필요한 Data는 외부 저장소에서 관리해야 한다.

## 2 ) ReplicaSet 생성

---

다음 내용을 `sample-rs.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: sample-rs
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

| Field | 역할 |
|---|---|
| `spec.replicas` | 유지할 Pod 수 |
| `spec.selector.matchLabels` | ReplicaSet이 관리 대상으로 계산할 Pod Label |
| `spec.template` | Pod 수가 부족할 때 새로 생성할 Pod Template |
| `template.metadata.labels` | 생성되는 Pod에 부여할 Label |

Master 또는 kubeconfig가 설정된 관리 Client에서 Manifest를 적용한다.

```bash
kubectl apply -f sample-rs.yaml
```

ReplicaSet과 생성된 Pod를 확인한다.

```bash
kubectl get replicasets
kubectl get pods -l app=sample-app -o wide
```

ReplicaSet이 생성한 Pod의 이름은 `sample-rs-<임의 문자열>` 형태이다. 각 Pod의 이름은 다르지만 같은 Pod Template과 Label을 사용한다.

상세 상태와 최근 Event를 확인한다.

```bash
kubectl describe replicaset sample-rs
```

`describe`는 장기간 증감 이력을 제공하는 명령이 아니다. 현재 Replica 수, Selector, Pod Template, Condition과 최근 Event를 확인하는 데 사용한다.

## 3 ) Label Selector와 Pod 수 조정

---

ReplicaSet의 `selector`는 `template`에 지정한 Label을 포함해야 한다. 두 값이 일치하지 않으면 API Server가 Resource 생성을 거부한다.

다음 잘못된 Manifest를 `sample-rs-fail.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: sample-rs-fail
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app-fail
    spec:
      containers:
        - name: nginx-container
          image: nginx
```

적용하면 Selector가 Pod Template Label과 일치하지 않는다는 오류가 발생한다.

```bash
kubectl apply -f sample-rs-fail.yaml
```

```text
The ReplicaSet "sample-rs-fail" is invalid:
spec.template.metadata.labels: Invalid value:
selector does not match template labels
```

오류를 해결하려면 `spec.selector.matchLabels`와 `spec.template.metadata.labels`의 `app` 값을 같게 설정한다.

### 같은 Label의 독립 Pod 생성

다음 내용을 `sample-rs-pod.yaml`로 저장한다. 이 Pod는 ReplicaSet과 같은 `app: sample-app` Label을 사용하지만 `ownerReferences`는 없는 독립 Pod로 요청된다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-rs-pod
  labels:
    app: sample-app
spec:
  containers:
    - name: nginx-container
      image: nginx
```

Pod를 생성하고 즉시 상태 변화를 관찰한다.

```bash
kubectl apply -f sample-rs-pod.yaml
kubectl get pods -l app=sample-app --watch
```

API Server는 Pod 생성 요청을 정상적으로 처리한다. 그 결과 일치하는 Pod가 `replicas: 3`보다 많아지면 ReplicaSet Controller가 Selector와 일치하는 Pod 중 하나를 삭제하여 총수를 다시 3개로 맞춘다. 반드시 새로 생성한 `sample-rs-pod`가 삭제된다고 보장되지는 않는다.

최종 Pod 수를 확인한다.

```bash
kubectl get pods -l app=sample-app
```

## 4 ) ReplicaSet Scaling

---

Replica 수는 Manifest의 `spec.replicas`를 수정한 뒤 다시 적용하거나 `kubectl scale`로 변경한다.

```bash
kubectl scale replicaset sample-rs --replicas=5
```

변경된 원하는 수와 현재 실행 수를 확인한다.

```bash
kubectl get replicaset sample-rs
kubectl get pods -l app=sample-app
```

`kubectl scale`은 Cluster의 Live Object를 직접 변경한다. Manifest를 기준으로 지속적으로 관리한다면 File의 `spec.replicas`도 같은 값으로 수정하여 다음 `apply`에서 원래 값으로 되돌아가지 않게 한다.

## 5 ) Deployment

---

> **Deployment**
>
> ReplicaSet을 생성하고 전환하여 Stateless Application의 배포, Scaling, Rolling Update와 Rollback을 관리하는 Controller Resource이다.

Deployment의 제어 관계는 다음과 같다.

```text
Deployment Controller
        │ ReplicaSet 생성·전환
        ▼
    ReplicaSet
        │ Pod 수 유지
        ▼
       Pods
```

직접 생성한 단독 Pod는 삭제된 뒤 자동으로 대체되지 않는다. ReplicaSet은 Pod 수를 유지하지만 Pod Template 변경에 대한 Rollout과 Rollback을 관리하지 않는다. 일반적인 Stateless Application은 Deployment로 배포한다.

## 6 ) Deployment 생성

---

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
      app: sample-deployment
  template:
    metadata:
      labels:
        app: sample-deployment
    spec:
      containers:
        - name: nginx-container
          image: nginx:1.26
```

Manifest를 적용하고 Deployment가 사용 가능한 상태가 될 때까지 기다린다.

```bash
kubectl apply -f sample-deployment.yaml
kubectl rollout status deployment/sample-deployment
```

Deployment, ReplicaSet과 Pod의 관계를 Label과 함께 확인한다.

```bash
kubectl get deployments
kubectl get replicasets
kubectl get pods -l app=sample-deployment --show-labels
```

Manifest 없이 간단한 Deployment를 생성할 수도 있다.

```bash
kubectl create deployment sample-deployment-by-cli --image=nginx
```

명령형 생성은 빠른 확인에는 편리하지만 설정을 반복하고 변경 이력을 관리하려면 Manifest를 저장하여 `kubectl apply`로 관리하는 편이 적합하다.

## 7 ) Image Update와 ReplicaSet 전환

---

Deployment의 Pod Template에 있는 Image를 변경한다.

```bash
kubectl set image deployment/sample-deployment \
  nginx-container=nginx:1.27
```

Rollout 진행 상태를 확인한다.

```bash
kubectl rollout status deployment/sample-deployment
kubectl get replicasets
kubectl get pods -l app=sample-deployment
```

Pod Template이 변경되면 Deployment는 새 ReplicaSet을 만들거나 동일한 Template의 기존 ReplicaSet을 재사용하여 전환한다. 기본 Rolling Update에서는 새 Pod를 늘리고 이전 Pod를 줄이며, 준비 상태를 확인하면서 전환한다.

Rolling Update 중 유지할 Pod 수는 다음 Field로 조정할 수 있다.

| Field | 역할 |
|---|---|
| `spec.strategy.rollingUpdate.maxSurge` | 원하는 Replica 수보다 추가로 만들 수 있는 최대 Pod 수 |
| `spec.strategy.rollingUpdate.maxUnavailable` | Update 중 사용할 수 없어도 되는 최대 Pod 수 |

`spec.replicas`만 변경하는 Scaling은 Pod Template 변경이 아니므로 새로운 ReplicaSet을 만들지 않는다.

과거 `kubectl set image`의 `--record` Option은 실행 Command를 변경 원인으로 기록하는 데 사용되었지만 Deprecated되어 현재 명령에서는 사용하지 않는다. 변경 목적은 배포 절차나 Annotation 등 별도의 관리 방식으로 기록한다.

## 8 ) Rollout History와 Rollback

---

Deployment의 Revision 목록을 확인한다.

```bash
kubectl rollout history deployment/sample-deployment
```

특정 Revision의 Pod Template을 확인한다.

```bash
kubectl rollout history deployment/sample-deployment --revision=2
```

특정 Revision으로 되돌린다.

```bash
kubectl rollout undo deployment/sample-deployment --to-revision=2
kubectl rollout status deployment/sample-deployment
```

바로 이전 Revision으로 되돌릴 때는 Revision 번호를 생략한다.

```bash
kubectl rollout undo deployment/sample-deployment
kubectl rollout status deployment/sample-deployment
```

Rollback은 과거 Pod를 그대로 다시 실행하는 방식이 아니다. Deployment가 이전 Pod Template을 원하는 상태로 선택하고 ReplicaSet의 Replica 수를 조정하여 Pod를 다시 전환한다.

## 9 ) Rollout Pause와 Resume

---

여러 Pod Template 변경을 하나의 Rollout으로 묶어 적용하려면 진행을 일시 중지할 수 있다.

```bash
kubectl rollout pause deployment/sample-deployment
```

Image를 변경한다.

```bash
kubectl set image deployment/sample-deployment \
  nginx-container=nginx:1.28
```

Pause 상태에서도 Deployment의 Pod Template 변경은 저장되지만 새 ReplicaSet으로 전환하는 Rollout은 진행되지 않는다. `kubectl rollout status`는 Rollback 명령이 아니며 배포 완료 여부를 기다리는 명령이므로, Pause 상태에서는 완료를 기다리며 종료되지 않을 수 있다.

현재 Image와 Pause Condition을 확인한다.

```bash
kubectl get deployment sample-deployment \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'

kubectl describe deployment sample-deployment
```

변경을 적용하려면 Rollout을 재개하고 상태를 확인한다.

```bash
kubectl rollout resume deployment/sample-deployment
kubectl rollout status deployment/sample-deployment
```

## 10 ) Deployment Scaling

---

Manifest의 `spec.replicas`를 수정해서 적용하거나 `kubectl scale`로 Replica 수를 변경할 수 있다.

```bash
kubectl scale deployment/sample-deployment --replicas=5
```

Deployment가 원하는 Replica 수와 사용 가능한 Replica 수를 확인한다.

```bash
kubectl get deployment sample-deployment
kubectl get pods -l app=sample-deployment
```

`kubectl scale` 역시 Live Object를 변경하므로 Manifest를 지속적인 기준으로 사용한다면 File의 `replicas` 값도 함께 맞춘다.

## 11 ) 실습 Resource 정리

---

Master 또는 관리 Client에서 생성한 Resource를 정리한다.

```bash
kubectl delete -f sample-rs-pod.yaml --ignore-not-found
kubectl delete -f sample-rs.yaml --ignore-not-found
kubectl delete -f sample-deployment.yaml --ignore-not-found
kubectl delete deployment sample-deployment-by-cli --ignore-not-found
```

삭제 결과를 확인한다.

```bash
kubectl get replicasets,deployments,pods
```

## 전체 정리

---

> **최종 정리**
>
> - ReplicaSet은 Label Selector와 일치하는 Pod를 `spec.replicas` 수만큼 유지한다.
>
> - Selector와 Pod Template Label은 일치해야 하며 같은 Label의 독립 Pod도 Replica 수 계산에 포함된다.
>
> - Deployment는 ReplicaSet을 관리하여 Stateless Application의 Rolling Update와 Rollback을 제공한다.
>
> - Pod Template 변경은 ReplicaSet 전환을 일으키지만 Replica 수만 변경하는 Scaling은 새 ReplicaSet을 만들지 않는다.
>
> - `rollout history`는 Revision을 확인하고 `rollout undo`는 이전 Pod Template으로 전환하며 `rollout status`는 진행 상태를 기다린다.
>
> - Control Plane의 Controller가 원하는 상태를 조정하고 Worker의 kubelet과 Container Runtime이 실제 Pod를 실행한다.
