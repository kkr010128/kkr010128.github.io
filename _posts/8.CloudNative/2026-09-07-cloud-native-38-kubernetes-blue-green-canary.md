---
title: Kubernetes Blue-Green과 Canary 배포
description: Service Selector를 이용한 Blue-Green 전환, Replica 비율과 Traffic Router를 이용한 Canary 및 Argo Rollouts 정리
date: 2026-09-07
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Rolling Update는 이전 Version과 새 Version의 Pod를 점진적으로 교체한다. Blue-Green은 두 Version을 별도 환경으로 유지한 뒤 Service의 연결 대상을 한 번에 바꾸고, Canary는 새 Version에 전달되는 Traffic을 제한하여 점진적으로 확대한다.

이 문서는 [Kubernetes ReplicaSet과 Deployment](/cloud-native-28-replicaset-deployment/)의 Rollout과 [Kubernetes Service Discovery와 외부 노출](/cloud-native-31-kubernetes-service-network/)의 Service Selector를 알고 있다고 가정한다.

## 1 ) 배포 전략 비교

---

| 전략 | Version 전환 방식 | 추가 Resource | Rollback 방식 | 주요 고려 사항 |
|---|---|---|---|---|
| Rolling Update | 이전 Pod를 줄이고 새 Pod를 늘림 | `maxSurge`만큼 추가 Pod 가능 | 이전 Revision으로 Rollout | 두 Version이 잠시 같은 Service에 존재 |
| Blue-Green | 두 환경을 모두 준비하고 Traffic 대상을 한 번에 변경 | 두 Version을 동시에 실행할 Resource 필요 | Service Selector를 이전 환경으로 복원 | 전환 전 새 환경 검증과 Data 호환성 필요 |
| Canary | 새 Version의 Traffic 비율을 조금씩 확대 | 두 Version과 Traffic 제어 수단 필요 | 새 Version Traffic을 0으로 축소 | 지표, 판정 기준과 Session 처리 필요 |

배포 전략은 Pod 교체 방식만 결정한다. Database Schema, Message Format과 외부 API가 두 Version에서 호환되는지도 별도로 검토해야 한다.

## 2 ) Blue-Green 동작 구조

---

Blue-Green에서는 현재 운영 중인 Version을 Blue, 새 Version을 Green으로 구분한다. 두 Deployment는 서로 다른 `color` Label을 사용하며 Service는 그중 하나만 선택한다.

```text
                       ┌─▶ Blue Deployment: v0.0.1
Client ─▶ Service ─────┤    color: blue
 selector.color=blue   │
                       └── Green Deployment: v0.0.2
                            color: green
                            전환 전 별도 검증
```

전환할 때 Pod를 다시 생성하는 것이 아니라 Service의 Selector를 `blue`에서 `green`으로 변경한다. EndpointSlice Controller가 새 Selector와 일치하는 Green Pod를 Endpoint로 반영하면 이후 Traffic이 Green으로 전달된다.

## 3 ) Blue와 Green Deployment 생성

---

현재 Version을 `print-version-blue.yaml`로 작성한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: print-version-blue
  labels:
    app: print-version
    color: blue
spec:
  replicas: 1
  selector:
    matchLabels:
      app: print-version
      color: blue
  template:
    metadata:
      labels:
        app: print-version
        color: blue
    spec:
      containers:
        - name: print-version
          image: ghcr.io/jpubdocker/print-version:v0.0.1
          ports:
            - containerPort: 8080
```

새 Version을 `print-version-green.yaml`로 작성한다. Resource 이름, `color` Label과 Image Version이 Blue와 다르다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: print-version-green
  labels:
    app: print-version
    color: green
spec:
  replicas: 1
  selector:
    matchLabels:
      app: print-version
      color: green
  template:
    metadata:
      labels:
        app: print-version
        color: green
    spec:
      containers:
        - name: print-version
          image: ghcr.io/jpubdocker/print-version:v0.0.2
          ports:
            - containerPort: 8080
```

Master 또는 kubeconfig가 설정된 관리 Client에서 두 Version을 배포한다.

```bash
kubectl apply -f print-version-blue.yaml
kubectl apply -f print-version-green.yaml
kubectl rollout status deployment/print-version-blue
kubectl rollout status deployment/print-version-green
kubectl get pods -l app=print-version --show-labels
```

두 Deployment가 모두 Ready여도 Service가 선택하지 않은 Green Pod에는 운영 Traffic이 전달되지 않는다. 전환 전에는 `kubectl port-forward`나 별도 검증용 Service를 이용하여 Green Version을 확인할 수 있다.

## 4 ) Service Selector로 Version 전환

---

Blue Version을 선택하는 Service를 `print-version-service-color.yaml`로 작성한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: print-version
  labels:
    app: print-version
spec:
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: print-version
    color: blue
```

Service를 적용하고 Endpoint가 Blue Pod를 가리키는지 확인한다.

```bash
kubectl apply -f print-version-service-color.yaml
kubectl get service print-version
kubectl get endpointslice \
  -l kubernetes.io/service-name=print-version \
  -o wide
```

지속적으로 Version을 확인할 Pod를 `update-checker.yaml`로 작성한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: update-checker
  labels:
    app: update-checker
spec:
  containers:
    - name: update-checker
      image: ghcr.io/jpubdocker/debug:v0.1.0
      command:
        - sh
        - -c
        - |
          while true
          do
            VERSION=$(curl -s http://print-version/)
            echo "[$(date)] ${VERSION}"
            sleep 1
          done
```

Pod를 생성하고 응답 Version을 확인한다.

```bash
kubectl apply -f update-checker.yaml
kubectl logs -f pod/update-checker
```

Green으로 전환하려면 `print-version-service-color.yaml`의 `color`를 다음과 같이 변경한다.

```yaml
selector:
  app: print-version
  color: green
```

변경된 Service를 적용하고 Endpoint와 Log를 다시 확인한다.

```bash
kubectl apply -f print-version-service-color.yaml
kubectl get endpointslice \
  -l kubernetes.io/service-name=print-version \
  -o wide
kubectl logs -f pod/update-checker
```

문제가 발견되면 같은 File의 `color`를 `blue`로 되돌려 다시 적용한다. 빠른 전환이 가능하려면 검증 기간 동안 Blue Deployment를 삭제하거나 축소하지 않아야 한다.

## 5 ) Blue-Green 전환 시 확인 사항

---

Service Selector 변경은 Application 내부 상태까지 전환하지 않는다. 다음 항목을 함께 확인한다.

- Green Pod가 모두 Ready인지 확인한다.

- Blue와 Green이 같은 Database나 Message Broker를 사용할 때 Schema와 Message가 양쪽 Version에서 호환되는지 확인한다.

- 기존 Connection과 처리 중인 요청이 Blue Pod에 남을 수 있음을 고려한다.

- [Kubernetes Health Check와 restartPolicy](/cloud-native-37-kubernetes-health-check-restart-policy/)의 Readiness Probe와 Graceful Shutdown을 구성한다.

- Rollback 판단 기준과 Blue 환경을 유지할 시간을 배포 전에 정한다.

## 6 ) Canary 배포

---

> **Canary 배포**
>
> 새 Version에 제한된 Traffic만 전달하여 오류율과 지연 시간 등의 지표를 확인한 뒤 Traffic 비율을 단계적으로 확대하는 방식이다.

Canary에는 다음 세 요소가 필요하다.

1. 동시에 실행되는 Stable Version과 Canary Version

2. Version별 Traffic을 구분하거나 비율을 조정할 수단

3. 다음 단계 진행 또는 Rollback을 결정할 관찰 지표와 기준

단순히 Canary Pod가 Running 상태인지만 확인해서는 사용자 요청이 정상 처리되는지 판단할 수 없다. HTTP 오류율, 응답 시간, Application 오류와 주요 업무 지표를 함께 관찰해야 한다.

## 7 ) Replica 비율을 이용한 단순 Canary

---

가장 단순한 방식은 Stable과 Canary Deployment에 같은 `app` Label을 부여하고 하나의 Service가 두 Version을 모두 선택하게 하는 것이다.

```text
Service selector: app=print-version
        │
        ├─ Stable Deployment: 9 Pods
        └─ Canary Deployment: 1 Pod
```

Stable과 Canary의 Deployment Selector는 `track`까지 포함하여 각 Controller가 자신의 Pod만 관리하게 하고, Service Selector는 공통 `app` Label만 사용한다.

```yaml
# Stable Deployment의 핵심 Label
spec:
  replicas: 9
  selector:
    matchLabels:
      app: print-version
      track: stable
  template:
    metadata:
      labels:
        app: print-version
        track: stable
```

```yaml
# Canary Deployment의 핵심 Label
spec:
  replicas: 1
  selector:
    matchLabels:
      app: print-version
      track: canary
  template:
    metadata:
      labels:
        app: print-version
        track: canary
```

```yaml
# 두 Version을 함께 선택하는 Service
spec:
  selector:
    app: print-version
```

Pod가 9대와 1대라고 해서 모든 구간에서 요청이 정확히 90%와 10%로 분배된다고 보장되지는 않는다. Service는 요청 수를 기준으로 정밀한 가중치를 적용하는 Traffic Router가 아니며, Connection 재사용과 Client 동작도 실제 비율에 영향을 준다. 이 방식은 단순한 실습이나 낮은 정밀도의 검증에 적합하다.

## 8 ) Ingress Annotation을 이용한 가중치 분배

---

ingress-nginx는 Stable Ingress와 같은 Host·Path를 사용하는 Canary Ingress에 Annotation을 지정하여 일부 Traffic을 Canary Service로 전달할 수 있다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: print-version-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"
spec:
  ingressClassName: nginx
  rules:
    - host: print-version.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: print-version-canary
                port:
                  number: 80
```

이 Annotation은 Kubernetes Ingress의 공통 기능이 아니라 ingress-nginx 구현 전용 기능이다. ingress-nginx Controller는 2026년 3월 24일부로 유지보수가 종료되어 신규 Release와 보안 수정이 제공되지 않는다. 따라서 기존 격리 학습 환경의 동작 이해에만 사용하고 신규 운영 환경의 Canary 구성으로 선택하지 않는다. Ingress API와 Controller의 구분은 [Kubernetes Ingress Resource와 HTTP Routing](/cloud-native-33-kubernetes-ingress-routing/)에서 확인할 수 있다.

운영 환경에서는 현재 유지보수되는 Gateway API 구현, Service Mesh 또는 배포 Controller가 지원하는 Traffic Router의 기능과 제약을 확인한다.

## 9 ) Argo Rollouts를 이용한 Canary 단계 관리

---

Argo Rollouts는 Kubernetes의 기본 Deployment가 아니라 별도 Controller와 CRD가 제공하는 `Rollout` Resource이다. 다음 Manifest를 적용하려면 Cluster에 Argo Rollouts Controller와 CRD가 먼저 설치되어 있어야 한다.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: print-version-rollout
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause:
            duration: 1h
        - setWeight: 50
        - pause: {}
  selector:
    matchLabels:
      app: print-version-rollout
  template:
    metadata:
      labels:
        app: print-version-rollout
    spec:
      containers:
        - name: print-version
          image: ghcr.io/jpubdocker/print-version:v0.0.2
          ports:
            - containerPort: 8080
```

| Step | 동작 |
|---|---|
| `setWeight: 10` | Canary 비중을 10으로 설정 |
| `pause.duration: 1h` | 1시간 동안 자동으로 대기하여 지표를 관찰할 시간 확보 |
| `setWeight: 50` | 다음 단계에서 Canary 비중을 50으로 확대 |
| `pause: {}` | 사용자가 재개할 때까지 무기한 대기 |

Traffic Router를 연결하지 않은 기본 Canary에서는 Argo Rollouts도 Replica 수로 Weight를 근사한다. 정밀한 Traffic 비율이 필요하면 선택한 Gateway API, Ingress 또는 Service Mesh Provider와 연동해야 한다.

Controller와 CRD가 준비된 환경에서는 다음과 같이 Resource 상태를 확인한다.

```bash
kubectl apply -f print-version-rollout.yaml
kubectl get rollouts.argoproj.io print-version-rollout
kubectl describe rollouts.argoproj.io print-version-rollout
```

`pause: {}` 단계에서는 관찰 지표를 확인한 뒤 수동으로 진행하거나 중단한다. 자동화된 배포에서는 AnalysisTemplate 등 별도의 판정 구성을 연결하여 다음 단계 진행 여부를 결정할 수 있다.

## 10 ) Session과 Canary Traffic

---

여러 Version이 동시에 요청을 처리할 때 Server Memory에 Session을 저장하면 사용자가 요청마다 다른 Version에 연결되어 상태가 끊길 수 있다. Sticky Session으로 같은 Backend 연결을 유지할 수 있지만 장기적으로는 다음 항목을 함께 검토한다.

- 공유 Session Store 사용 여부

- Version 간 Cookie와 Session Format 호환성

- Sticky Session 때문에 Canary Traffic 비율과 사용자 표본이 왜곡되는지 여부

- Canary Pod 장애 시 Session Failover 방식

Sticky Session은 Canary의 필수 조건이 아니라 Application의 Session 저장 방식에 따라 선택하는 기능이다.

## 11 ) 전략 선택 기준

---

| 조건 | 적합한 출발점 |
|---|---|
| Kubernetes 기본 Rollout으로 가용성을 유지하며 교체 | Deployment Rolling Update |
| 두 Version의 혼재를 피하고 즉시 전환·복원이 필요 | Blue-Green과 Service Selector 전환 |
| 간단한 환경에서 대략적인 소수 사용자 검증 | Replica 비율 기반 Canary |
| 정밀한 Weight, 자동 분석과 단계 승격 필요 | Argo Rollouts와 유지보수되는 Traffic Router 연동 |

어떤 전략을 선택하더라도 Readiness Probe, Graceful Shutdown, 관찰 지표, Rollback 조건과 Data 호환성을 먼저 준비해야 한다.

## 12 ) 실습 Resource 정리

---

Blue-Green 실습 Resource를 삭제한다.

```bash
kubectl delete -f update-checker.yaml --ignore-not-found
kubectl delete -f print-version-service-color.yaml --ignore-not-found
kubectl delete -f print-version-green.yaml --ignore-not-found
kubectl delete -f print-version-blue.yaml --ignore-not-found
```

Argo Rollouts 실습을 수행했다면 Rollout Resource도 삭제한다. Controller와 CRD는 다른 Rollout에서 사용할 수 있으므로 함께 제거하지 않는다.

```bash
kubectl delete -f print-version-rollout.yaml --ignore-not-found
```

## 전체 정리

---

> **최종 정리**
>
> - Rolling Update는 두 ReplicaSet을 점진적으로 조정하고 Blue-Green은 Service Selector로 운영 대상을 한 번에 전환한다.
>
> - Blue-Green의 빠른 Rollback을 위해서는 이전 환경을 유지하고 두 Version의 Data 호환성을 확인해야 한다.
>
> - Canary는 새 Version의 Traffic을 제한하여 지표를 확인한 뒤 비율을 확대한다.
>
> - Replica 수를 이용한 Canary 비율은 근사치이며 정밀한 제어에는 별도 Traffic Router가 필요하다.
>
> - ingress-nginx Canary Annotation은 해당 Controller 전용이며 Controller의 유지보수가 종료되어 신규 운영 구성에 사용하지 않는다.
>
> - Argo Rollouts는 별도 CRD와 Controller가 필요한 확장 Resource이며 단계별 Weight와 Pause를 관리한다.
>
> - Readiness Probe, Graceful Shutdown, Session, 관찰 지표와 Rollback 조건이 배포 전략의 안전성을 결정한다.
