---
title: Kubernetes Service Traffic Policy와 MetalLB
description: Session Affinity와 Traffic Policy, Headless·ExternalName·Selector가 없는 Service 및 Bare-metal 환경의 MetalLB 구성 정리
date: 2026-08-31
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Service는 안정적인 IP와 DNS 이름을 제공하는 것뿐 아니라 Client 고정, Local Endpoint 선택과 Topology 선호 같은 Traffic 정책도 제어한다. Cloud Load Balancer가 없는 Bare-metal Cluster에서는 MetalLB 같은 구현을 추가하여 `LoadBalancer` Service에 외부 IP를 할당할 수 있다.

## 1 ) 선행 학습과 실습 환경

---

이 문서는 ClusterIP, NodePort와 LoadBalancer의 기본 차이를 이해한 상태에서 Service의 세부 동작을 확장한다. 기본 구조는 [Kubernetes Service Discovery와 외부 노출](/cloud-native-31-kubernetes-service-network/)에서 확인할 수 있다.

실습은 Control Plane 1대와 Worker 2대 이상이 통신 가능한 kubeadm Cluster를 기준으로 한다.

| 역할 | 주요 작업 |
|---|---|
| Master 또는 관리 Client | Manifest 적용, Service와 EndpointSlice 상태 확인 |
| Control Plane | Service·EndpointSlice 상태 저장, Controller의 상태 조정 |
| Worker | kube-proxy 또는 CNI Service 구현으로 Traffic 전달 |
| MetalLB Controller | `LoadBalancer` Service에 IP Address 할당 |
| MetalLB Speaker | 각 Node에서 L2 또는 BGP 방식으로 할당된 IP Address 광고 |

먼저 Node와 Pod가 정상인지 확인한다.

```bash
# Master 또는 관리 Client에서 실행
kubectl get nodes -o wide
kubectl get pods -A
```

MetalLB에서 사용할 IP 범위는 다음 주소와 겹치지 않아야 한다.

- Node와 Gateway가 이미 사용하는 주소

- DHCP Server가 Client에 할당할 수 있는 주소

- 다른 장비나 Load Balancer가 사용하는 주소

- 다른 VLAN 또는 L2 Network에 있어 현재 Node가 광고할 수 없는 주소

예제에서는 `192.168.0.150`~`192.168.0.199`를 사용하지만 실제 환경에서는 Network 구성에 맞는 미사용 범위로 바꿔야 한다.

## 2 ) 실습 Backend Deployment

---

Traffic 정책과 LoadBalancer 동작을 함께 확인할 Backend를 생성한다. 다음 내용을 `sample-service-backend.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-service-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-service-backend
  template:
    metadata:
      labels:
        app: sample-service-backend
    spec:
      containers:
        - name: echo-nginx
          image: amsy810/echo-nginx:v2.0
          ports:
            - name: http
              containerPort: 80
```

Master 또는 관리 Client에서 적용한 뒤 Pod가 여러 Worker에 배치됐는지 확인한다.

```bash
kubectl apply -f sample-service-backend.yaml
kubectl rollout status deployment/sample-service-backend
kubectl get pods -l app=sample-service-backend -o wide
```

Pod가 하나의 Worker에만 배치되어도 Service 기능은 확인할 수 있다. 다만 `externalTrafficPolicy: Local`의 Node별 차이를 관찰하려면 여러 Worker에 Pod가 분산되어 있어야 한다.

## 3 ) Session Affinity

---

> **Session Affinity**
>
> 같은 Client에서 들어온 연결을 일정 시간 동안 같은 Backend Pod로 전달하도록 선호하는 Service 설정이다.

Service의 기본 `sessionAffinity` 값은 `None`이다. `ClientIP`로 설정하면 Service Data Plane이 식별한 Client IP를 기준으로 Backend를 고정한다.

먼저 Affinity가 없는 ClusterIP Service를 `sample-session-affinity.yaml`로 작성한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-session-affinity
spec:
  type: ClusterIP
  sessionAffinity: None
  selector:
    app: sample-service-backend
  ports:
    - name: http
      protocol: TCP
      port: 8080
      targetPort: http
```

Service를 적용하고 EndpointSlice를 확인한다.

```bash
# Master 또는 관리 Client에서 실행
kubectl apply -f sample-session-affinity.yaml
kubectl get service sample-session-affinity
kubectl get endpointslices -l kubernetes.io/service-name=sample-session-affinity
```

요청용 Pod를 `sample-tools-pod.yaml`로 생성한다. Cluster DNS를 그대로 사용하기 위해 `hostNetwork`는 사용하지 않는다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-tools
spec:
  containers:
    - name: tools
      image: amsy810/tools:v2.0
```

```bash
kubectl apply -f sample-tools-pod.yaml
kubectl wait --for=condition=Ready pod/sample-tools --timeout=120s
kubectl exec sample-tools -- curl -s http://sample-session-affinity:8080
```

여러 번 새 연결을 만들면 Service가 선택한 Backend 이름이 달라질 수 있다.

```bash
kubectl exec sample-tools -- /bin/bash -c \
  'for i in {1..10}; do curl -s http://sample-session-affinity:8080; done'
```

같은 Manifest에서 `sessionAffinity`와 Timeout을 다음과 같이 변경한다.

```yaml
spec:
  type: ClusterIP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10000
```

다시 적용한 뒤 같은 Client Pod에서 요청을 반복한다.

```bash
kubectl apply -f sample-session-affinity.yaml
kubectl get service sample-session-affinity \
  -o jsonpath='{.spec.sessionAffinity}{"\n"}{.spec.sessionAffinityConfig.clientIP.timeoutSeconds}{"\n"}'
kubectl exec sample-tools -- /bin/bash -c \
  'for i in {1..10}; do curl -s http://sample-session-affinity:8080; done'
```

Session Affinity는 Application Session 자체를 복제하거나 보존하는 기능이 아니다. Client IP가 NAT나 Proxy를 거치며 같아지거나 바뀌면 기대한 분산과 다르게 동작할 수 있으므로 Stateful Session의 유일한 보장 수단으로 사용하지 않는다.

NodePort와 LoadBalancer Service에도 `ClientIP`를 설정할 수 있다. 다만 외부 Traffic 경로의 NAT와 Proxy 때문에 Service Data Plane이 관찰하는 Client IP가 실제 사용자 주소와 다를 수 있으므로 `externalTrafficPolicy`와 함께 확인해야 한다.

## 4 ) externalTrafficPolicy

---

NodePort와 LoadBalancer처럼 외부에서 들어오는 Traffic은 어느 Node에 도착한 뒤 Service Backend로 전달된다. `spec.externalTrafficPolicy`는 외부 Traffic을 Cluster 전체 Endpoint로 보낼지, Traffic을 받은 Node의 Local Endpoint로만 보낼지 결정한다.

| 설정 | Backend 범위 | Source IP | 주의 사항 |
|---|---|---|---|
| `Cluster` | 다른 Node의 Ready Endpoint 포함 | 전달 과정의 SNAT로 변경될 수 있음 | Node 간 추가 Hop이 발생할 수 있음 |
| `Local` | Traffic이 도착한 Node의 Local Ready Endpoint | 보존할 수 있음 | Local Endpoint가 없는 Node는 요청을 처리하지 못함 |

기본값인 `Cluster`의 흐름은 다음과 같다.

```text
외부 Client
  └─▶ Worker 1의 NodePort
        └─▶ Service Data Plane
              └─▶ Worker 2의 Backend Pod도 선택 가능
```

`Local`은 Node 간 재전송을 제한한다.

```text
외부 Client
  └─▶ Worker 1의 NodePort
        └─▶ Worker 1의 Local Backend Pod만 선택
```

다음 내용을 `sample-nodeport-local.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-nodeport-local
spec:
  type: NodePort
  externalTrafficPolicy: Local
  selector:
    app: sample-service-backend
  ports:
    - name: http
      protocol: TCP
      port: 8080
      targetPort: http
      nodePort: 30082
```

적용한 뒤 Pod가 배치된 Node와 Service 설정을 함께 확인한다.

```bash
# Master 또는 관리 Client에서 실행
kubectl apply -f sample-nodeport-local.yaml
kubectl get pods -l app=sample-service-backend \
  -o custom-columns='NAME:.metadata.name,NODE:.spec.nodeName,NODE_IP:.status.hostIP,POD_IP:.status.podIP'
kubectl get service sample-nodeport-local \
  -o jsonpath='{.spec.externalTrafficPolicy}{"\n"}'
```

Cluster 외부 Client에서 각 Worker 주소로 요청한다.

```bash
curl -s http://<backend-pod가-있는-worker-ip>:30082
curl -s --connect-timeout 3 http://<backend-pod가-없는-worker-ip>:30082
```

두 번째 Node에 Local Endpoint가 없다면 응답하지 못할 수 있다. DaemonSet처럼 각 Node에 Backend가 하나씩 존재하는 Workload는 `Local` 정책과 결합하기 쉽지만, 이 설정이 DaemonSet 전용인 것은 아니다.

`healthCheckNodePort`는 `type: LoadBalancer`이면서 `externalTrafficPolicy: Local`인 Service에서 Load Balancer가 Local Endpoint 보유 여부를 확인할 때 사용할 수 있다. 구현에 따라 Health Check 방식은 달라질 수 있으며 일반 ClusterIP나 NodePort의 공통 설정이 아니다.

```yaml
spec:
  type: LoadBalancer
  externalTrafficPolicy: Local
  healthCheckNodePort: 30083
```

값을 생략하면 조건을 지원하는 구현에서 사용 가능한 Health Check용 NodePort를 할당할 수 있다. 고정 Port가 반드시 필요한 경우에만 충돌 여부를 확인하고 직접 지정한다.

## 5 ) Topology를 고려한 전송

---

Cluster가 여러 Zone에 걸쳐 있으면 모든 Endpoint를 같은 우선순위로 선택할 때 불필요한 Zone 간 Traffic, 지연과 비용이 발생할 수 있다. Service의 Traffic Distribution은 가능한 경우 가까운 Endpoint를 선호하도록 의도를 전달한다.

Kubernetes 1.36에서 사용하는 대표 값은 다음과 같다.

| 값 | 의미 | 상태 |
|---|---|---|
| `PreferSameZone` | 같은 Zone의 Endpoint 선호 | 현재 사용 가능 |
| `PreferSameNode` | 같은 Node의 Endpoint 선호 | 현재 사용 가능 |
| `PreferClose` | 같은 Zone 선호의 이전 이름 | Deprecated |

다음 예제는 같은 Zone을 선호한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-topology-service
spec:
  selector:
    app: sample-service-backend
  trafficDistribution: PreferSameZone
  ports:
    - name: http
      port: 8080
      targetPort: http
```

이 설정은 `externalTrafficPolicy: Local`처럼 다른 Node를 엄격히 제외하는 정책이 아니라 선호도이다. Node의 Zone Label, Endpoint 수와 Service Proxy 구현 조건을 충족하지 못하면 Cluster 전체 Endpoint를 사용하는 동작으로 돌아갈 수 있다.

```bash
kubectl apply -f sample-topology-service.yaml
kubectl get nodes -L topology.kubernetes.io/zone
kubectl get service sample-topology-service \
  -o jsonpath='{.spec.trafficDistribution}{"\n"}'
kubectl get endpointslices -l kubernetes.io/service-name=sample-topology-service -o yaml
```

단일 L2 Network의 소규모 VM Cluster처럼 Zone Label이 없는 환경에서는 Manifest 구조만 확인하고 실제 Zone 선호 효과를 단정하지 않는다.

## 6 ) Headless Service와 개별 Pod Discovery

---

Headless Service는 `clusterIP: None`으로 설정하여 Service Virtual IP를 만들지 않는다. DNS는 하나의 ClusterIP 대신 Selector와 연결된 개별 Endpoint 주소를 반환한다.

다음 내용을 `sample-headless-statefulset.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-headless
spec:
  type: ClusterIP
  clusterIP: None
  selector:
    app: sample-statefulset-headless
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: sample-statefulset-headless
spec:
  serviceName: sample-headless
  replicas: 3
  selector:
    matchLabels:
      app: sample-statefulset-headless
  template:
    metadata:
      labels:
        app: sample-statefulset-headless
    spec:
      containers:
        - name: echo-nginx
          image: amsy810/echo-nginx:v2.0
          ports:
            - name: http
              containerPort: 80
```

Service의 `metadata.name`과 StatefulSet의 `spec.serviceName`이 일치해야 StatefulSet Pod의 안정적인 DNS Domain을 구성할 수 있다.

```bash
kubectl apply -f sample-headless-statefulset.yaml
kubectl rollout status statefulset/sample-statefulset-headless
kubectl get pods -l app=sample-statefulset-headless -o wide
kubectl get service sample-headless
```

Tools Pod에서 Service와 개별 Pod의 FQDN을 조회한다.

```bash
kubectl exec sample-tools -- \
  dig sample-headless.default.svc.cluster.local
kubectl exec sample-tools -- \
  dig sample-statefulset-headless-0.sample-headless.default.svc.cluster.local
kubectl exec sample-tools -- cat /etc/resolv.conf
```

Service 이름 조회는 개별 Pod IP 목록을 반환할 수 있지만 DNS 응답 순서만으로 균등한 Load Balancing이 보장되지는 않는다. 개별 StatefulSet Pod를 직접 식별해야 하면 Pod FQDN을 사용한다. Storage까지 포함한 StatefulSet 동작은 [Kubernetes DaemonSet과 StatefulSet](/cloud-native-29-daemonset-statefulset/)에서 확인할 수 있다.

## 7 ) 일반 Pod의 hostname과 subdomain

---

StatefulSet이 아닌 Pod도 `hostname`과 `subdomain`을 지정하여 Headless Service Domain 아래의 이름을 가질 수 있다. 다음 내용을 `sample-subdomain.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-subdomain
spec:
  clusterIP: None
  selector:
    app: sample-subdomain
  ports:
    - name: http
      port: 80
      targetPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  name: sample-subdomain-pod
  labels:
    app: sample-subdomain
spec:
  hostname: sample-hostname
  subdomain: sample-subdomain
  containers:
    - name: echo-nginx
      image: amsy810/echo-nginx:v2.0
      ports:
        - name: http
          containerPort: 80
```

```bash
kubectl apply -f sample-subdomain.yaml
kubectl wait --for=condition=Ready pod/sample-subdomain-pod --timeout=120s
kubectl exec sample-tools -- \
  dig sample-hostname.sample-subdomain.default.svc.cluster.local
```

기본적으로 Ready Endpoint를 기준으로 DNS Record가 게시된다. Ready 이전부터 주소를 노출해야 하는 특수한 Discovery 구조에서는 Service의 `publishNotReadyAddresses` 여부도 함께 검토해야 한다.

## 8 ) ExternalName Service

---

ExternalName Service는 Cluster 내부 Service 이름을 외부 FQDN의 DNS 별칭으로 만든다. Service Proxy가 Traffic을 중계하거나 ClusterIP에서 Load Balancing하는 방식이 아니다.

다음 내용을 `sample-externalname.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-externalname
  namespace: default
spec:
  type: ExternalName
  externalName: external.example.com
```

```bash
kubectl apply -f sample-externalname.yaml
kubectl get service sample-externalname
kubectl exec sample-tools -- \
  dig sample-externalname.default.svc.cluster.local
```

Application은 `sample-externalname.default.svc.cluster.local`을 사용하고 Cluster 관리자는 외부 목적지가 바뀔 때 `externalName`을 변경할 수 있다. 다만 HTTP 요청의 `Host` Header와 TLS 인증서 검증 대상은 실제 외부 Domain과 다를 수 있으므로 Protocol 수준의 호환성을 확인해야 한다.

ClusterIP Service와 ExternalName Service는 필드 제약이 다르다. 운영 중인 Service Type을 억지로 전환하기보다 기존 Client 영향과 Immutable Field를 확인하고 필요하면 Service를 재생성한다.

## 9 ) Selector가 없는 Service

---

Selector가 없는 Service는 Kubernetes가 Backend Pod를 자동 선택하지 않는다. 관리자가 EndpointSlice를 별도로 정의하여 Cluster 외부 Server나 수동 관리 Backend를 Service 주소 뒤에 연결한다.

```text
Client Pod
  └─▶ Service DNS와 ClusterIP
        └─▶ Worker의 Service Data Plane
              └─▶ 수동 EndpointSlice의 Backend IP
```

다음 내용을 `sample-no-selector.yaml`로 저장한다. 예제 주소는 문서용 대역이므로 실제 접근 가능한 Backend IP로 바꿔야 한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-no-selector
spec:
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8080
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: sample-no-selector-1
  labels:
    kubernetes.io/service-name: sample-no-selector
addressType: IPv4
ports:
  - name: http
    protocol: TCP
    port: 8080
endpoints:
  - addresses:
      - 192.0.2.10
    conditions:
      ready: true
  - addresses:
      - 192.0.2.11
    conditions:
      ready: true
```

```bash
kubectl apply -f sample-no-selector.yaml
kubectl get service sample-no-selector
kubectl get endpointslices \
  -l kubernetes.io/service-name=sample-no-selector -o wide
```

Legacy `Endpoints` API는 Kubernetes 1.33부터 Deprecated 상태이므로 신규 수동 Backend 구성에는 EndpointSlice를 사용한다.

| 항목 | ExternalName | Selector가 없는 Service |
|---|---|---|
| DNS 응답 | 외부 이름의 CNAME | Service ClusterIP |
| Traffic 경로 | Client가 해석한 외부 이름으로 연결 | Service Data Plane을 거쳐 Endpoint로 전달 |
| Backend 정의 | `spec.externalName` | 별도 EndpointSlice |
| 대표 목적 | 외부 DNS 이름에 내부 별칭 제공 | 외부·수동 Backend에 Service Load Balancing 제공 |

## 10 ) Bare-metal LoadBalancer와 MetalLB

---

Public Cloud에서는 `type: LoadBalancer` Service를 Cloud Provider의 Load Balancer 구현이 관찰하고 외부 주소와 Data Plane을 준비한다. 생성되는 장비나 Service가 항상 Application Load Balancer인 것은 아니며 Provider와 설정에 따라 Network Load Balancer 등 구현이 달라진다.

직접 구축한 kubeadm Cluster나 VMware, VirtualBox, UTM, Proxmox 같은 가상화 환경에는 이 연동이 기본으로 존재하지 않는다. 이 경우 Service의 `EXTERNAL-IP`가 `<pending>`에 머물 수 있다.

MetalLB는 표준 Network Protocol을 이용하여 Cloud Load Balancer가 없는 환경에 Kubernetes `LoadBalancer` Service 구현을 제공한다. 대부분의 Public Cloud는 MetalLB의 주 사용 환경이 아니며 Network 제약으로 호환되지 않을 수 있으므로 Cloud에서는 Provider 기본 연동을 우선 검토한다.

MetalLB의 주요 Component는 다음과 같다.

| Component | 배포 형태 | 역할 |
|---|---|---|
| Controller | Deployment | LoadBalancer Service를 관찰하고 IPAddressPool에서 IP 할당 |
| Speaker | DaemonSet | Node에서 Service IP를 L2 또는 BGP 방식으로 외부 Network에 광고 |

L2 Mode에서는 Speaker가 IPv4의 ARP와 IPv6의 NDP에 응답하여 특정 Node가 Service IP를 가진 것처럼 알린다. BGP Mode는 외부 Router와 경로 정보를 교환한다. 이 실습은 동일 Subnet에서 구성하기 쉬운 L2 Mode만 사용한다.

```text
Master·관리 Client
  └─▶ API Server에 IPAddressPool과 L2Advertisement 등록
        ├─▶ MetalLB Controller가 Service에 IP 할당
        └─▶ Worker의 Speaker가 L2에서 IP 광고

외부 Client
  └─▶ LoadBalancer IP
        └─▶ 광고를 담당하는 Worker
              └─▶ Service Data Plane
                    └─▶ Backend Pod
```

## 11 ) MetalLB 설치

---

2026-08-31 기준 공식 문서의 안정 Release인 `v0.16.1` Native Manifest를 사용한다. Native Mode는 L2 전용 또는 단순 BGP 구성에 적합하다. Version을 무조건 최신 문자열로 바꾸지 말고 Cluster의 Kubernetes Version과 MetalLB Release 호환성을 먼저 확인한다.

Master 또는 관리 Client에서 설치한다.

```bash
kubectl apply -f \
  https://raw.githubusercontent.com/metallb/metallb/v0.16.1/config/manifests/metallb-native.yaml
```

설치 Manifest는 `metallb-system` Namespace, Controller Deployment, Speaker DaemonSet과 필요한 RBAC Resource를 생성한다. IP Pool 설정은 포함하지 않으므로 설치 직후에는 LoadBalancer IP를 할당하지 않는다.

```bash
kubectl get namespaces metallb-system
kubectl get deployments,daemonsets,pods -n metallb-system -o wide
kubectl rollout status deployment/controller -n metallb-system
kubectl rollout status daemonset/speaker -n metallb-system
```

kube-proxy가 IPVS Mode라면 MetalLB 설치 전 `strictARP: true` 요구 사항을 확인해야 한다. 현재 Mode와 설정을 먼저 조회하며 확인 없이 ConfigMap을 변경하지 않는다.

```bash
kubectl get configmap kube-proxy -n kube-system -o yaml
```

## 12 ) IPAddressPool과 L2Advertisement

---

다음 내용을 `sample-metallb-l2.yaml`로 저장한다. 주소 범위는 반드시 현재 Network의 미사용 범위로 변경한다.

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: sample-l2-pool
  namespace: metallb-system
spec:
  addresses:
    - 192.168.0.150-192.168.0.199
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: sample-l2-advertisement
  namespace: metallb-system
spec:
  ipAddressPools:
    - sample-l2-pool
```

Controller가 할당할 범위와 Speaker가 L2로 광고할 Pool을 등록한다.

```bash
kubectl apply -f sample-metallb-l2.yaml
kubectl get ipaddresspools,l2advertisements -n metallb-system
kubectl describe ipaddresspool sample-l2-pool -n metallb-system
```

`IPAddressPool`이 존재해도 `L2Advertisement`나 BGP 설정이 없으면 IP가 할당되더라도 외부 Network에서 접근할 경로가 만들어지지 않는다.

## 13 ) LoadBalancer Service 생성

---

다음 내용을 `sample-loadbalancer-metallb.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-loadbalancer-metallb
spec:
  type: LoadBalancer
  selector:
    app: sample-service-backend
  ports:
    - name: http
      protocol: TCP
      port: 8080
      targetPort: http
      nodePort: 30080
```

`nodePort`를 생략하면 기본 동작에서는 Kubernetes가 사용 가능한 Port를 할당한다. 고정값은 방화벽이나 실습 조건상 필요할 때만 지정한다.

```bash
kubectl apply -f sample-loadbalancer-metallb.yaml
kubectl get service sample-loadbalancer-metallb --watch
```

다른 Terminal에서 `EXTERNAL-IP`가 Pool 범위에서 할당됐는지 확인한다.

```bash
kubectl describe service sample-loadbalancer-metallb
kubectl get service sample-loadbalancer-metallb \
  -o jsonpath='{.status.loadBalancer.ingress[*].ip}{"\n"}'
```

Cluster와 같은 Network에 있는 외부 Client에서 요청한다.

```bash
curl -s http://<할당된-external-ip>:8080
```

접근되지 않으면 다음 순서로 확인한다.

1. Service의 Event와 `EXTERNAL-IP`를 확인한다.

2. EndpointSlice에 Ready Backend가 있는지 확인한다.

3. Controller와 Speaker Log를 확인한다.

4. IP Pool이 Node와 같은 L2 Network인지 확인한다.

5. Host Firewall과 VM Network Mode가 ARP Traffic을 허용하는지 확인한다.

```bash
kubectl get endpointslices \
  -l kubernetes.io/service-name=sample-loadbalancer-metallb
kubectl logs -n metallb-system deployment/controller
kubectl logs -n metallb-system daemonset/speaker --tail=100
```

## 14 ) 특정 LoadBalancer IP 요청

---

`spec.loadBalancerIP`는 Kubernetes 1.24부터 Deprecated 상태이다. 구현별 의미가 불명확하고 Dual-stack 주소를 표현할 수 없으므로 신규 MetalLB 예제에서는 `metallb.io/loadBalancerIPs` Annotation을 사용한다.

다음 내용을 `sample-loadbalancer-fixed-ip.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-loadbalancer-fixed-ip
  annotations:
    metallb.io/loadBalancerIPs: 192.168.0.199
spec:
  type: LoadBalancer
  selector:
    app: sample-service-backend
  ports:
    - name: http
      protocol: TCP
      port: 8081
      targetPort: http
      nodePort: 30081
```

요청한 IP는 MetalLB Pool에 포함되고 다른 Service가 사용하지 않아야 한다.

```bash
kubectl apply -f sample-loadbalancer-fixed-ip.yaml
kubectl get service sample-loadbalancer-fixed-ip
kubectl describe service sample-loadbalancer-fixed-ip
curl -s http://192.168.0.199:8081
```

기존 환경과의 호환을 위해 MetalLB가 `spec.loadBalancerIP`를 처리할 수는 있지만 신규 Manifest의 기본 선택으로 사용하지 않는다.

## 15 ) LoadBalancer 접근 범위 제한

---

`spec.loadBalancerSourceRanges`는 LoadBalancer Service에 접근을 허용할 Client Network를 CIDR로 지정한다.

```yaml
spec:
  type: LoadBalancer
  loadBalancerSourceRanges:
    - 192.168.0.0/24
```

설정하지 않으면 Service 수준에서 Source Network를 제한하지 않는다. API가 실제로 `0.0.0.0/0` 값을 자동 기록한다는 의미는 아니다. 필드 적용 방식은 Load Balancer Controller, Service Proxy와 Network 구현에 따라 달라질 수 있으므로 실제 Firewall Rule과 외부 접근 결과를 확인해야 한다.

## 16 ) 실습 Resource 정리

---

Master 또는 관리 Client에서 Application과 Service Resource를 먼저 정리한다.

```bash
kubectl delete -f sample-loadbalancer-fixed-ip.yaml --ignore-not-found
kubectl delete -f sample-loadbalancer-metallb.yaml --ignore-not-found
kubectl delete -f sample-no-selector.yaml --ignore-not-found
kubectl delete -f sample-externalname.yaml --ignore-not-found
kubectl delete -f sample-subdomain.yaml --ignore-not-found
kubectl delete -f sample-headless-statefulset.yaml --ignore-not-found
kubectl delete -f sample-topology-service.yaml --ignore-not-found
kubectl delete -f sample-nodeport-local.yaml --ignore-not-found
kubectl delete -f sample-session-affinity.yaml --ignore-not-found
kubectl delete -f sample-tools-pod.yaml --ignore-not-found
kubectl delete -f sample-service-backend.yaml --ignore-not-found
```

Ingress 실습에서 MetalLB를 이어서 사용할 예정이면 IP Pool과 MetalLB 설치는 유지한다. 더 이상 사용하지 않을 때만 Pool 설정을 정리한다.

```bash
kubectl delete -f sample-metallb-l2.yaml --ignore-not-found
kubectl get all -n metallb-system
```

MetalLB 자체 삭제는 다른 `LoadBalancer` Service가 사용 중이지 않은지 확인한 뒤 별도로 수행한다.

```bash
kubectl get services -A \
  -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,TYPE:.spec.type,EXTERNAL_IP:.status.loadBalancer.ingress[*].ip'
```

## 전체 정리

---

> **최종 정리**
>
> - Session Affinity의 `ClientIP`는 같은 Client를 일정 시간 같은 Backend로 보내지만 Application Session을 저장하거나 복제하지 않는다.
>
> - `externalTrafficPolicy: Cluster`는 Cluster 전체 Endpoint를 사용하고 `Local`은 Traffic이 도착한 Node의 Local Endpoint만 사용한다.
>
> - Traffic Distribution은 같은 Zone이나 Node의 Endpoint를 선호할 수 있지만 엄격한 Local 정책과는 다르다.
>
> - Headless Service는 ClusterIP 없이 개별 Endpoint DNS를 제공하고 ExternalName은 외부 FQDN의 CNAME을 제공한다.
>
> - Selector가 없는 Service는 관리자가 만든 EndpointSlice를 통해 외부 또는 수동 Backend를 Service 뒤에 연결한다.
>
> - MetalLB Controller는 LoadBalancer IP를 할당하고 Worker의 Speaker는 L2 또는 BGP 방식으로 해당 IP를 Network에 광고한다.
>
> - `spec.loadBalancerIP`는 Deprecated 상태이므로 신규 MetalLB 구성에서는 구현이 제공하는 Annotation을 사용한다.

다음 단계에서는 [Kubernetes Ingress Resource와 HTTP Routing](/cloud-native-33-kubernetes-ingress-routing/)에서 하나의 외부 진입점을 여러 HTTP Service로 연결하는 방법을 다룬다.
