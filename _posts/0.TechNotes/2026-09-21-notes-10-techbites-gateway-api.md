---
title: Kubernetes Gateway API
description: Ingress의 한계와 Gateway API의 역할별 리소스 구조를 비교합니다
date: 2026-09-21
series: TechNotes
tags:
  - TechBites
  - Kubernetes
  - GatewayAPI
---

## 요약

---

> Kubernetes의 `Ingress`는 HTTP와 HTTPS 요청을 클러스터 내부의 `Service`로 전달합니다. 사용하기 단순하지만, 기능을 확장할수록 컨트롤러별 `Annotation`에 의존하고 인프라 설정과 애플리케이션 라우팅 설정이 한 리소스에 섞이기 쉽습니다. `Gateway API`는 `GatewayClass`, `Gateway`, `Route`로 책임을 나누고 프로토콜별 라우팅 규칙을 별도의 리소스로 표현합니다.

## 1. Ingress가 담당하는 역할

---

`Ingress`는 외부에서 들어온 HTTP와 HTTPS 요청을 `Host`와 `Path` 조건에 따라 클러스터 내부의 `Service`로 전달합니다.

```text
[설정 반영]
Ingress → Ingress Controller → Load Balancer 또는 Proxy 설정

[요청 전달]
Client → Load Balancer 또는 Proxy → Service → Pod
```

`Ingress` 리소스만 생성해서는 트래픽이 처리되지 않습니다. 리소스를 감시하고 실제 Load Balancer나 Proxy 설정으로 변환하는 `Ingress Controller`가 함께 필요합니다. 실제 요청은 Controller의 조정 과정에서 만들어진 Data Plane을 통과합니다.

다음 설정은 `shop.example.com`으로 들어온 요청을 경로에 따라 두 `Service`로 전달합니다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop-ingress
spec:
  tls:
    - hosts:
        - shop.example.com
      secretName: tls-secret
  rules:
    - host: shop.example.com
      http:
        paths:
          - path: /app
            pathType: Prefix
            backend:
              service:
                name: app-service
                port:
                  number: 80
          - path: /admin
            pathType: Prefix
            backend:
              service:
                name: admin-service
                port:
                  number: 8080
```

이 예제는 클러스터에 기본 `IngressClass`가 지정되어 있다고 가정합니다. 기본 Class가 없다면 `spec.ingressClassName`으로 이 리소스를 처리할 Ingress Class를 명시해야 합니다.

이 설정에는 외부 진입점의 TLS 정보와 애플리케이션의 경로별 라우팅 정보가 함께 들어 있습니다.

| 설정 | 역할 | 주로 관리하는 영역 |
| --- | --- | --- |
| `spec.tls` | HTTPS 연결에 사용할 Host와 TLS Secret을 지정합니다. | 클러스터 운영 또는 보안 |
| `spec.rules.host` | 요청의 Host 조건을 지정합니다. | 클러스터 운영과 애플리케이션의 공통 영역 |
| `spec.rules.http.paths` | URL Path에 연결할 `Service`와 Port를 지정합니다. | 애플리케이션 |

작은 환경에서는 한 리소스로 관리해도 문제가 적습니다. 여러 팀이 하나의 진입점을 공유하면 TLS, Listener, 라우팅 규칙의 변경 주체가 달라지므로 관리 경계가 불분명해질 수 있습니다.

## 2. Ingress의 한계

---

### 2.1 Controller별 Annotation에 의존합니다

`Ingress`의 기본 스펙에 없는 기능은 `Ingress Controller`가 제공하는 `Annotation`으로 설정하는 경우가 많습니다. NGINX Ingress Controller의 Rewrite 기능은 다음과 같이 지정할 수 있습니다.

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
```

이 Key는 Kubernetes 공통 스펙이 아니라 NGINX Ingress Controller의 설정입니다. AWS Load Balancer Controller와 같은 다른 구현체는 서로 다른 Key와 값을 사용합니다. Controller를 교체할 때 기존 설정을 그대로 옮길 수 없는 이유입니다.

```text
Ingress 표준 필드
        +
Controller별 Annotation
        ↓
구현체에 종속된 설정
```

### 2.2 HTTP와 HTTPS를 중심으로 설계되었습니다

Kubernetes의 표준 `Ingress` 규칙은 HTTP와 HTTPS 트래픽만 처리합니다. TCP와 UDP처럼 다른 프로토콜을 노출하려면 `NodePort` 또는 `LoadBalancer` 유형의 `Service`를 사용하거나 Controller가 제공하는 별도 기능을 사용해야 합니다.

Gateway API는 프로토콜별 라우팅 규칙을 Route 리소스로 분리합니다.

| 트래픽 | Gateway API 리소스 | 현재 채널 |
| --- | --- | --- |
| HTTP, TLS가 종료된 HTTPS | `HTTPRoute` | Standard |
| gRPC | `GRPCRoute` | Standard |
| TLS Passthrough 또는 TLS Metadata 기반 라우팅 | `TLSRoute` | Standard |
| TCP | `TCPRoute` | Experimental |
| UDP | `UDPRoute` | Experimental |

HTTPS 전용 `HTTPSRoute`가 따로 존재하는 것은 아닙니다. `Gateway`의 HTTPS Listener가 인증서와 TLS 종료를 담당하고, 복호화된 HTTP 요청은 연결된 `HTTPRoute`가 처리합니다.

`TLSRoute`는 Gateway API v1.5.0부터 Standard Channel에 포함되었습니다. `TCPRoute`와 `UDPRoute`는 Experimental Channel에 포함되므로 향후 호환성이 보장되지 않습니다. 실제 사용 전에는 설치한 CRD와 Gateway Controller가 해당 Route를 지원하는지 확인해야 합니다.

### 2.3 관리 역할을 분리하기 어렵습니다

`Ingress`에는 Host, Path, TLS, Backend와 Controller별 설정이 함께 들어갑니다. 다음과 같이 운영자와 개발자가 같은 리소스를 수정하게 될 수 있습니다.

```text
Ingress
├── Host
├── Path
├── TLS
├── Backend Service
└── Controller별 Annotation
```

클러스터 운영자는 외부 Listener와 TLS를 관리하고, 애플리케이션 개발자는 `/app`과 `/admin` 같은 라우팅 규칙을 관리해야 합니다. 설정이 하나의 리소스에 모이면 변경 권한과 검토 범위를 분리하기 어렵습니다.

### 2.4 고급 라우팅의 표현 범위가 좁습니다

`Ingress`의 기본 라우팅 조건은 Host와 Path입니다. 다음 기능은 Controller별 `Annotation`이나 확장 설정을 사용해야 하는 경우가 많습니다.

- 특정 Header가 있는 요청만 전달합니다.

- 여러 Backend에 가중치를 주어 트래픽을 분할합니다.

- 다른 URL로 Redirect합니다.

- 요청을 다른 Backend로 복제해 Mirror합니다.

Gateway API는 이러한 조건과 동작을 `HTTPRoute`의 Match, Filter, `backendRefs` 같은 필드로 표현합니다. 각 필드의 지원 수준은 Core, Extended 또는 구현체별 기능으로 나뉠 수 있으므로 Controller의 Conformance 문서를 함께 확인해야 합니다.

## 3. Gateway API의 리소스 구조

---

Gateway API는 클러스터의 진입점과 애플리케이션 라우팅을 여러 리소스로 나눕니다.

```text
GatewayClass
     ↓
Gateway
     ↓
HTTPRoute / GRPCRoute / TCPRoute / UDPRoute / TLSRoute
     ↓
Service
     ↓
Pod
```

각 리소스의 책임은 다음과 같습니다.

| 역할 | 관리 리소스 | 책임 |
| --- | --- | --- |
| 인프라 제공자 | `GatewayClass` | 어떤 Gateway Controller가 Gateway를 구현할지 정의합니다. |
| 클러스터 운영자 | `Gateway` | Listener, Port, Protocol, TLS와 Route 연결 범위를 정의합니다. |
| 애플리케이션 개발자 | `HTTPRoute`, `GRPCRoute` 등의 Route | 요청 조건과 Backend `Service`를 정의합니다. |

한 사람이 모든 역할을 담당할 수도 있습니다. 리소스가 분리되어 있으므로 조직 규모가 커졌을 때 RBAC와 Namespace 경계를 이용해 책임과 변경 권한을 나눌 수 있습니다.

### 3.1 GatewayClass

`GatewayClass`는 Gateway 구현체의 종류를 정의하는 Cluster Scope 리소스입니다. `StorageClass`가 Storage Provisioner를 가리키는 것처럼 `GatewayClass`는 Gateway Controller를 가리킵니다.

```text
GatewayClass
└── controllerName: 이 Class를 처리할 Gateway Controller
```

### 3.2 Gateway

`Gateway`는 실제 트래픽을 받을 지점을 정의합니다. 어떤 `GatewayClass`를 사용할지 선택하고, Listener의 Hostname, Port, Protocol, TLS와 연결 가능한 Route 범위를 설정합니다.

```text
Gateway
├── gatewayClassName
└── listeners
    ├── hostname
    ├── port
    ├── protocol
    ├── tls
    └── allowedRoutes
```

기본 설정에서는 같은 Namespace의 Route만 Gateway에 연결할 수 있습니다. 다른 Namespace의 Route를 연결하려면 `allowedRoutes`로 허용 범위를 지정해야 합니다.

### 3.3 Route

Route는 Gateway가 받은 요청을 어느 `Service`로 전달할지 정의합니다. HTTP 요청은 `HTTPRoute`, gRPC 요청은 `GRPCRoute`처럼 프로토콜에 맞는 리소스를 사용합니다.

```text
HTTPRoute
├── parentRefs: 연결할 Gateway
├── hostnames: 요청 Host 조건
└── rules
    ├── matches: Path, Header 등의 조건
    ├── filters: Redirect, Rewrite, Mirror 등의 동작
    └── backendRefs: 전달할 Service와 가중치
```

Gateway와 Route는 서로의 연결을 모두 허용해야 합니다. Gateway의 `allowedRoutes` 범위에 Route가 포함되어야 하고, Route의 `parentRefs`도 대상 Gateway를 가리켜야 합니다.

## 4. 요청이 전달되는 흐름

---

Ingress Controller는 `Ingress`를 감시해 Load Balancer 또는 Proxy 설정을 만듭니다. 실제 요청은 구성된 Data Plane을 통과합니다.

```text
[Control Plane]
Ingress → Ingress Controller → Data Plane 설정

[Data Plane]
Client → Load Balancer 또는 Proxy → Service → Pod
```

Gateway Controller도 `GatewayClass`, `Gateway`, Route를 함께 해석해 Data Plane을 구성합니다.

```text
[Control Plane]
GatewayClass + Gateway + Route
              ↓
      Gateway Controller
              ↓
       Data Plane 설정

[Data Plane]
Client
  ↓
Gateway Listener
  ↓
Route 조건과 일치하는 Backend Service
  ↓
Pod
```

HTTP 요청은 다음 순서로 처리됩니다.

1. Client가 DNS로 Gateway의 주소를 확인한 뒤 요청을 전송합니다.

2. Gateway Controller가 구성한 Data Plane이 Listener에서 요청을 받습니다.

3. Listener에 연결된 `HTTPRoute` 중 Host, Path, Header 등의 조건이 일치하는 규칙을 찾습니다.

4. 필요한 Filter를 적용한 뒤 `backendRefs`에 지정된 `Service`로 요청을 전달합니다.

5. `Service`가 선택한 Pod에서 요청을 처리합니다.

## 5. Ingress와 Gateway API 비교

---

| 구분 | Ingress | Gateway API |
| --- | --- | --- |
| 기본 목적 | 외부 HTTP와 HTTPS 요청을 내부 `Service`로 전달합니다. | 프로토콜을 인식하는 진입점과 고급 라우팅을 구성합니다. |
| API 제공 방식 | Kubernetes에 포함된 기본 API입니다. | CRD와 이를 구현하는 Gateway Controller를 추가해야 합니다. |
| 리소스 구조 | `Ingress`를 중심으로 구성합니다. | `GatewayClass` → `Gateway` → Route로 구성합니다. |
| 프로토콜 | HTTP와 HTTPS를 처리합니다. | Standard Route로 HTTP, HTTPS, gRPC, TLS를 처리하며 Experimental Route로 TCP와 UDP를 표현할 수 있습니다. |
| 고급 기능 | Controller별 `Annotation`에 의존하는 경우가 많습니다. | Match, Filter, `backendRefs` 등의 필드로 표현합니다. |
| 역할 분리 | 진입점과 애플리케이션 라우팅 설정이 섞이기 쉽습니다. | 인프라 제공자, 클러스터 운영자, 애플리케이션 개발자의 리소스를 분리합니다. |
| 이식성 | Controller별 Annotation과 확장 설정의 차이가 큽니다. | 공통 API로 이식성을 높이지만 구현체별 지원 범위는 확인해야 합니다. |

Gateway API가 공통 스펙을 제공해도 모든 Controller가 모든 Route와 기능을 같은 수준으로 구현하지는 않습니다. Controller를 선택할 때는 지원하는 Gateway API 버전, Release Channel, Conformance Profile과 기능별 지원 수준을 확인해야 합니다.

## 6. 현재 상태와 적용 전 확인 사항

---

Kubernetes는 `Ingress` API를 제거할 계획이 없으며 기존 리소스도 계속 사용할 수 있습니다. 다만 `Ingress` API의 신규 개발은 동결되었고, Kubernetes 프로젝트는 새로운 구성을 위해 Gateway API 사용을 권장합니다.

Gateway API를 적용하기 전에는 다음 항목을 확인합니다.

- Gateway API CRD와 Gateway Controller가 설치되어 있는지 확인합니다.

- Controller가 사용할 `GatewayClass`를 제공하는지 확인합니다.

- 필요한 Route가 Standard Channel인지 Experimental Channel인지 확인합니다.

- Header Match, Redirect, Rewrite, Mirror, Traffic Split 등 필요한 기능의 지원 수준을 확인합니다.

- Gateway와 Route를 다른 Namespace에 둘 경우 `allowedRoutes`와 권한 경계를 확인합니다.

- 기존 Ingress를 전환할 때 Controller별 Annotation을 어떤 Gateway API 필드나 구현체별 정책으로 옮길지 확인합니다.

## 참고 자료

---

- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)

- [Kubernetes Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/)

- [Gateway API 개요](https://gateway-api.sigs.k8s.io/docs/concepts/api-overview/)

- [Gateway API 구현체 목록](https://gateway-api.sigs.k8s.io/docs/implementations/list/)
