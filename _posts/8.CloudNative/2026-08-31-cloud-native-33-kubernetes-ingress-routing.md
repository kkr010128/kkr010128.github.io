---
title: Kubernetes Ingress Resource와 HTTP Routing
description: Ingress Resource와 Controller의 관계, Bare-metal Cluster의 외부 진입점 및 Host·Path 기반 HTTP Routing 실습 정리
date: 2026-08-31
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

LoadBalancer Service를 Application마다 만들면 외부 IP와 DNS Record도 Service별로 관리해야 한다. Ingress는 HTTP와 HTTPS 요청의 Host와 Path를 기준으로 여러 Service에 전달할 Routing 규칙을 Kubernetes Resource로 관리한다. 실제 Traffic 처리는 Cluster에 별도로 배포한 Ingress Controller가 담당한다.

## 1 ) Service와 Ingress

---

Service와 Ingress는 서로 대체하는 Resource가 아니라 다른 계층의 역할을 수행한다.

| Resource | 주요 계층 | 역할 |
|---|---|---|
| ClusterIP Service | L4 | 변하는 Backend Pod 집합에 안정적인 내부 Endpoint 제공 |
| LoadBalancer Service | L4 | 하나의 Service를 외부 Load Balancer 주소로 노출 |
| Ingress | L7 HTTP·HTTPS | Host와 Path 규칙을 Backend Service에 연결 |

Application마다 LoadBalancer Service를 만들면 다음과 같이 외부 주소가 늘어난다.

```text
api.example.com  ─▶ LoadBalancer IP 1 ─▶ api Service
web.example.com  ─▶ LoadBalancer IP 2 ─▶ web Service
admin.example.com ─▶ LoadBalancer IP 3 ─▶ admin Service
```

Ingress Controller를 공통 진입점으로 사용하면 하나의 외부 주소 뒤에서 Routing할 수 있다.

```text
                         ┌─▶ api Service
외부 Client ─▶ Ingress ──┼─▶ web Service
                         └─▶ admin Service
```

Ingress는 TCP나 UDP의 임의 Port를 일반적으로 Routing하는 Resource가 아니다. HTTP·HTTPS 외 Protocol은 NodePort, LoadBalancer Service 또는 선택한 Gateway 구현의 지원 범위를 확인한다.

## 2 ) Ingress Resource와 Ingress Controller

---

> **Ingress Resource**
>
> Host, Path와 Backend Service의 관계를 선언하는 Kubernetes API Resource이다.

> **Ingress Controller**
>
> Ingress Resource를 감시하고 선언된 규칙을 실제 Reverse Proxy나 Load Balancer 설정으로 반영하는 Controller이다.

Ingress Manifest를 API Server에 등록하는 것만으로는 Traffic이 처리되지 않는다. 해당 IngressClass를 담당하는 Controller가 Cluster에서 실행 중이어야 한다.

```text
Master·관리 Client
  kubectl apply -f ingress-test.yaml
                 │
                 ▼
Control Plane의 API Server
  Ingress Resource 저장
                 │
                 ▼
Worker에서 실행되는 Ingress Controller
  Ingress·Service·EndpointSlice 관찰
  Reverse Proxy 설정 생성
                 │
                 ▼
외부 Client → Controller 진입점 → ClusterIP Service → Backend Pod
```

Ingress Controller는 `Controller`라는 이름을 가지지만 상태 조정만 하는 것이 아니라 실제 HTTP·HTTPS Traffic을 받는 Data Plane Pod 역할도 함께 수행할 수 있다.

## 3 ) Ingress의 현재 상태

---

Ingress API는 Kubernetes 1.19부터 Stable이며 기존 환경에서 계속 사용할 수 있다. 다만 API 기능은 동결되어 새로운 기능이 추가되지 않으며 Kubernetes는 신규 구성에 Gateway API 사용을 권장한다. 이것은 Ingress가 삭제됐다는 뜻이 아니라 기존 API를 안정적으로 유지하면서 후속 기능 개발이 Gateway API에서 진행된다는 뜻이다.

이 문서의 실습 대상으로 사용되는 ingress-nginx Controller는 별도의 상태 확인이 필요하다.

| 대상 | 현재 상태 |
|---|---|
| Kubernetes Ingress API | Stable, 기능 동결, 제거 예정 없음 |
| ingress-nginx Controller | 2026년 3월 이후 Retirement, 신규 Release와 보안 수정 없음 |
| Gateway API | Ingress의 후속 API 계열, 별도 구현과 CRD 필요 |

따라서 ingress-nginx 실습은 Ingress Resource와 Controller 관계를 확인하는 격리된 학습 환경으로 제한한다. Internet에 공개되는 운영 환경이나 신규 장기 운영 Cluster에는 그대로 적용하지 않고 유지보수 중인 Controller 또는 Gateway API 구현을 선택해야 한다.

## 4 ) Bare-metal Cluster의 Ingress 진입점

---

Public Cloud에서는 Ingress Controller의 `LoadBalancer` Service가 Cloud Load Balancer와 연결될 수 있다. 직접 구축한 Cluster에서는 MetalLB 같은 Load Balancer 구현이나 NodePort, Host Network 등 별도의 외부 진입 방식이 필요하다.

이 실습은 앞에서 구성한 MetalLB L2 Mode를 사용한다.

```text
외부 Client
  └─▶ MetalLB가 할당한 External IP
        └─▶ ingress-nginx-controller LoadBalancer Service
              └─▶ Ingress Controller Pod
                    └─▶ Backend ClusterIP Service
                          └─▶ Application Pod
```

MetalLB 구성은 [Kubernetes Service Traffic Policy와 MetalLB](/cloud-native-32-kubernetes-service-traffic-policy-metallb/)에서 확인할 수 있다.

Master 또는 관리 Client에서 사전 상태를 확인한다.

```bash
kubectl get nodes -o wide
kubectl get pods -n metallb-system
kubectl get ipaddresspools,l2advertisements -n metallb-system
kubectl get services -A \
  -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,TYPE:.spec.type,EXTERNAL_IP:.status.loadBalancer.ingress[*].ip'
```

## 5 ) ingress-nginx Controller 설치

---

다음 Manifest는 Retirement 이전 최종 계열인 `controller-v1.15.1`을 사용하는 격리 실습 예제이다. 이전 `controller-v1.6.4`는 오래된 Release이므로 사용하지 않는다. ingress-nginx 자체가 더 이상 유지보수되지 않으므로 Version 번호만 갱신했다고 운영 환경에 적합해지는 것은 아니다.

Master 또는 관리 Client에서 Controller를 설치한다.

```bash
kubectl apply -f \
  https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/cloud/deploy.yaml
```

Manifest는 `ingress-nginx` Namespace와 Controller Deployment, Admission 관련 Resource 및 LoadBalancer Service를 생성한다.

```bash
kubectl get all -n ingress-nginx
kubectl wait --namespace ingress-nginx \
  --for=condition=Ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s
kubectl get ingressclasses
```

MetalLB가 정상이라면 `ingress-nginx-controller` Service의 `EXTERNAL-IP`가 할당된다.

```bash
kubectl get service ingress-nginx-controller -n ingress-nginx
kubectl describe service ingress-nginx-controller -n ingress-nginx
```

`EXTERNAL-IP`가 `<pending>`이면 Ingress Manifest부터 수정하지 말고 MetalLB Controller, IPAddressPool과 Service Event를 먼저 확인한다.

```bash
kubectl logs -n metallb-system deployment/controller --tail=100
kubectl get ipaddresspools,l2advertisements -n metallb-system
kubectl describe service ingress-nginx-controller -n ingress-nginx
```

## 6 ) Backend Deployment 생성

---

Ingress가 전달할 Web Application을 `deploy-test.yaml`로 작성한다. Python 2.7의 SimpleHTTPServer는 지원이 종료된 Runtime이므로 사용하지 않고 응답한 Pod를 확인할 수 있는 Echo Image를 사용한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-test
spec:
  replicas: 3
  selector:
    matchLabels:
      app: service-test
  template:
    metadata:
      labels:
        app: service-test
    spec:
      containers:
        - name: echo-nginx
          image: amsy810/echo-nginx:v2.0
          ports:
            - name: http
              containerPort: 80
```

Master 또는 관리 Client에서 적용하고 Rollout과 Worker 배치를 확인한다.

```bash
kubectl apply -f deploy-test.yaml
kubectl rollout status deployment/service-test
kubectl get pods -l app=service-test -o wide
```

Control Plane의 Deployment Controller와 Scheduler가 Pod 생성과 Node 선택을 조정하고, 선택된 Worker의 kubelet과 Container Runtime이 실제 Container를 실행한다.

## 7 ) Backend Service 생성

---

Ingress는 Pod를 직접 Backend로 지정하지 않고 Service 이름과 Port를 사용한다. 다음 내용을 `svc-test.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: service-test
spec:
  type: ClusterIP
  selector:
    app: service-test
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: http
```

```bash
kubectl apply -f svc-test.yaml
kubectl get service service-test
kubectl get endpointslices \
  -l kubernetes.io/service-name=service-test -o wide
```

EndpointSlice에 세 Pod의 IP가 Ready Endpoint로 나타나야 한다. Endpoint가 비어 있으면 Ingress가 정상이어도 Backend로 요청을 전달할 수 없으므로 Service Selector와 Pod Label부터 비교한다.

## 8 ) Ingress Resource 생성

---

다음 내용을 `ingress-test.yaml`로 저장한다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-test
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: ingress.test.com
      http:
        paths:
          - path: /test
            pathType: Prefix
            backend:
              service:
                name: service-test
                port:
                  number: 80
```

| Field | 역할 |
|---|---|
| `spec.ingressClassName: nginx` | 이 Resource를 처리할 IngressClass 선택 |
| `rules[].host` | HTTP Host Header가 일치할 Domain |
| `paths[].path: /test` | Routing에 사용할 요청 Path |
| `pathType: Prefix` | `/test` Prefix와 일치하는 요청 처리 |
| `backend.service.name` | 요청을 전달할 ClusterIP Service |
| `backend.service.port.number` | Backend Service의 `port` |
| `rewrite-target: /` | Backend에 전달할 때 요청 Path를 `/`로 Rewrite |

Legacy `kubernetes.io/ingress.class: nginx` Annotation은 기존 Manifest에서 볼 수 있지만 신규 예제에는 `spec.ingressClassName`을 사용한다.

```bash
kubectl apply -f ingress-test.yaml
kubectl get ingress ingress-test
kubectl describe ingress ingress-test
```

Ingress Event에 Class나 Admission 오류가 있으면 Controller Pod와 Admission Job 상태를 함께 확인한다.

```bash
kubectl get pods,jobs -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=100
```

## 9 ) Domain 등록과 요청 확인

---

DNS Server를 사용하지 않는 실습에서는 요청을 보내는 외부 Client의 `/etc/hosts`에 Domain을 등록한다. Worker IP가 아니라 `ingress-nginx-controller` Service에 MetalLB가 할당한 `EXTERNAL-IP`를 사용한다.

먼저 IP를 확인한다.

```bash
# Master 또는 관리 Client에서 실행
kubectl get service ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}{"\n"}'
```

외부 Linux Client에서 `/etc/hosts`를 수정한다.

```bash
# 외부 Client에서 실행
sudo nano /etc/hosts
```

다음 형식으로 등록한다.

```text
192.168.0.150 ingress.test.com
```

`192.168.0.150`은 예시이며 실제 할당된 `EXTERNAL-IP`로 바꾼다. DNS 등록 없이 일회성으로 확인하려면 `curl --resolve`를 사용할 수 있다.

```bash
# 외부 Client에서 실행
curl --resolve ingress.test.com:80:<ingress-external-ip> \
  http://ingress.test.com/test
```

`/etc/hosts`를 등록했다면 일반 URL로 요청한다.

```bash
curl http://ingress.test.com/test
```

요청은 다음 순서로 처리된다.

1. Client가 `ingress.test.com`을 Ingress External IP로 해석한다.

2. MetalLB L2 Speaker가 해당 IP로 들어오는 Traffic을 Node에 도달시킨다.

3. `ingress-nginx-controller` Service가 Controller Pod로 전달한다.

4. Controller가 Host와 `/test` Prefix 규칙을 찾는다.

5. Rewrite 규칙에 따라 Backend Path를 `/`로 바꾼다.

6. `service-test:80`을 거쳐 Ready Backend Pod에 요청을 전달한다.

## 10 ) 문제 확인 순서

---

Ingress 요청이 실패할 때는 외부에서 내부 방향으로 확인한다.

| 단계 | 확인 대상 | 명령 |
|---|---|---|
| 1 | Domain 해석 | `getent hosts ingress.test.com` |
| 2 | Controller External IP | `kubectl get svc -n ingress-nginx` |
| 3 | Ingress 규칙과 Event | `kubectl describe ingress ingress-test` |
| 4 | IngressClass | `kubectl get ingressclasses` |
| 5 | Controller 상태와 Log | `kubectl get pods -n ingress-nginx`, `kubectl logs` |
| 6 | Backend Service | `kubectl get service service-test` |
| 7 | Ready Endpoint | `kubectl get endpointslices` |
| 8 | Backend Pod | `kubectl get pods -l app=service-test` |

Ingress Address가 없더라도 Controller 진입점이 별도로 준비되어 있으면 요청이 처리될 수 있다. 반대로 Address가 표시돼도 Network Route, Firewall 또는 MetalLB 광고가 잘못되면 외부 Client는 접근할 수 없다.

## 11 ) Host Routing과 Path Routing

---

Ingress는 하나의 진입점에서 Host와 Path를 조합할 수 있다.

```text
api.example.com/       ─▶ api-service
web.example.com/       ─▶ web-service
ingress.test.com/test  ─▶ service-test
```

Host 기반 Routing은 Client가 보내는 HTTP `Host` Header를 사용한다. IP 주소로만 요청하면 Manifest의 Host 규칙과 일치하지 않을 수 있으므로 Domain 등록이나 `curl --resolve`가 필요하다.

Path 기반 Routing에서는 `Exact`, `Prefix`와 `ImplementationSpecific`의 의미가 다르다. 이 문서는 하위 Path까지 포함하는 `Prefix`를 사용하며 Controller 전용 Annotation의 동작은 해당 구현 문서를 확인한다.

## 12 ) 실습 Resource 정리

---

Master 또는 관리 Client에서 Ingress부터 Backend 순서로 정리한다.

```bash
kubectl delete -f ingress-test.yaml --ignore-not-found
kubectl delete -f svc-test.yaml --ignore-not-found
kubectl delete -f deploy-test.yaml --ignore-not-found
```

다른 Ingress가 Controller를 사용 중인지 확인한다.

```bash
kubectl get ingress -A
kubectl get service ingress-nginx-controller -n ingress-nginx
```

격리 실습이 끝났고 다른 Ingress가 없다면 설치에 사용한 같은 Version의 Manifest로 Controller를 제거할 수 있다.

```bash
kubectl delete -f \
  https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.15.1/deploy/static/provider/cloud/deploy.yaml
```

MetalLB는 다른 LoadBalancer Service가 사용할 수 있으므로 Ingress Controller와 함께 자동으로 제거하지 않는다. 외부 Client의 `/etc/hosts`에 추가한 실습 Domain도 더 이상 사용하지 않으면 삭제한다.

## 전체 정리

---

> **최종 정리**
>
> - Service는 Backend Pod 집합에 L4 Endpoint를 제공하고 Ingress는 HTTP·HTTPS의 Host와 Path를 Service에 연결한다.
>
> - Ingress Resource는 Routing 규칙이며 실제 Traffic 처리를 위해 해당 IngressClass를 담당하는 Controller가 필요하다.
>
> - Control Plane은 Ingress 선언 상태를 저장하고 Worker의 Ingress Controller Pod가 규칙을 Reverse Proxy 설정과 Data Plane에 반영한다.
>
> - Bare-metal Cluster에서는 MetalLB의 LoadBalancer IP를 Ingress Controller의 외부 진입점으로 사용할 수 있다.
>
> - Ingress API는 Stable이지만 기능이 동결됐으며, ingress-nginx Controller는 Retirement 상태이므로 운영 환경의 신규 선택으로 사용하지 않는다.
>
> - 문제를 확인할 때는 DNS와 External IP부터 IngressClass, Controller, Service, EndpointSlice와 Backend Pod 순서로 추적한다.
