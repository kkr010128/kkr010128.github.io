---
title: Kubernetes Service Discovery와 외부 노출
description: Pod Network부터 Service·EndpointSlice·DNS 기반 Discovery와 ClusterIP·NodePort·LoadBalancer를 이용한 Traffic 전달 정리
date: 2026-08-28
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Pod는 생성과 교체 과정에서 IP Address가 달라질 수 있으므로 Client가 개별 Pod IP를 직접 관리하면 Backend 변화에 대응하기 어렵다. Service는 Label Selector로 Pod 집합을 찾고 안정적인 IP Address와 DNS 이름을 제공하며, Service Type에 따라 Cluster 내부 또는 외부에서 접근할 수 있게 한다.

## 1 ) Kubernetes의 통신 범위

---

Kubernetes에서 Container와 Pod가 통신하는 범위는 다음과 같다.

| 통신 대상 | 주소 | 특징 |
|---|---|---|
| 같은 Pod의 Container | `localhost:<port>` | Pod Network Namespace와 IP Address 공유 |
| 다른 Pod | `<pod-ip>:<port>` | 같은 Node와 다른 Node 모두 Pod Network를 통해 통신 |
| Service Backend | `<service-name>:<port>` | 변하는 Pod 집합을 Service가 안정적인 이름으로 연결 |
| Cluster 외부 Client | NodePort, LoadBalancer, Ingress·Gateway 등 | 외부 노출 방식과 Infrastructure 필요 |

같은 Pod의 Container는 같은 IP Address를 사용하므로 서로 다른 Port에서 Listen해야 한다. 다른 Pod와는 Cluster 전체에서 고유한 Pod IP로 통신할 수 있지만 Pod 교체 시 IP가 바뀔 수 있다.

Pod Network는 CNI(Container Network Interface) 구현이 구성한다. `kubeadm`으로 Cluster를 초기화한 것만으로 Pod 간 Network가 완성되는 것은 아니며 Calico, Flannel 등 Cluster에 맞는 CNI Plugin을 설치해야 한다.

```text
Worker 1                          Worker 2
Pod A: 10.244.1.10                Pod B: 10.244.2.20
        │                                 │
        └────── CNI가 구성한 Pod Network ─┘
```

CNI 구현에 따라 VXLAN 같은 Overlay, Native Routing 또는 다른 Data Plane 방식을 사용할 수 있다. 구현 방식은 달라도 NetworkPolicy 등 의도적인 제한이 없다면 Pod가 Node 경계를 넘어 통신할 수 있는 Kubernetes Network Model을 제공해야 한다.

## 2 ) Service와 외부 노출 Resource

---

> **Service**
>
> 하나 이상의 Backend Pod에 안정적인 Network Endpoint와 Service Discovery 기능을 제공하는 Kubernetes Resource이다.

Service와 관련 구성은 다음과 같이 구분한다.

| 종류 | 설정 | 용도 |
|---|---|---|
| ClusterIP | `type: ClusterIP` | Cluster 내부 Virtual IP와 Load Balancing |
| NodePort | `type: NodePort` | 각 Node의 IP와 지정 Port로 외부 노출 |
| LoadBalancer | `type: LoadBalancer` | 외부 Load Balancer 구현과 연동 |
| ExternalName | `type: ExternalName` | Service DNS를 외부 DNS 이름의 CNAME으로 연결 |
| Headless | `clusterIP: None` | Virtual IP 없이 Backend별 DNS Record 제공 |
| Selector가 없는 Service | Selector 생략, EndpointSlice 별도 관리 | Cluster 밖 Backend나 수동 Endpoint 연결 |
| External IP | `.spec.externalIPs` | 외부에서 Node로 Routing되는 특정 IP를 Service에 연결 |
| Ingress | 별도 Resource | HTTP·HTTPS의 Host와 Path 기반 Routing |

External IP, Headless와 Selector가 없는 Service는 별도의 `type` 값이 아니라 Service를 구성하는 방식이다. Ingress도 Service Type이 아니며 실제 Traffic 처리를 위해 Ingress Controller가 필요하다.

## 3 ) Service Backend Deployment 생성

---

Service 실습에 사용할 Echo Server Deployment를 생성한다. 다음 내용을 `sample-service-deployment.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-service-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-service-app
  template:
    metadata:
      labels:
        app: sample-service-app
    spec:
      containers:
        - name: nginx-container
          image: amsy810/echo-nginx:v2.0
          ports:
            - containerPort: 80
```

Master 또는 kubeconfig가 설정된 관리 Client에서 Deployment를 생성하고 Pod가 Ready 상태가 될 때까지 기다린다.

```bash
kubectl apply -f sample-service-deployment.yaml
kubectl rollout status deployment/sample-service-deployment
```

Pod IP와 배치된 Worker를 확인한다.

```bash
kubectl get pods \
  -l app=sample-service-app \
  -o wide
```

Pod마다 서로 다른 IP가 할당되며 Scaling, Update와 장애 복구 과정에서 Pod가 다시 생성되면 IP도 바뀔 수 있다.

## 4 ) ClusterIP Service 생성

---

> **ClusterIP**
>
> Cluster 내부에서만 접근할 수 있는 Virtual IP를 제공하는 기본 Service Type이다.

다음 내용을 `sample-clusterip.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-clusterip
spec:
  type: ClusterIP
  ports:
    - name: http-port
      protocol: TCP
      port: 8080
      targetPort: 80
  selector:
    app: sample-service-app
```

| Field | 역할 |
|---|---|
| `type: ClusterIP` | Cluster 내부 Virtual IP 사용 |
| `ports[].port` | Client가 Service에 요청할 Port |
| `ports[].targetPort` | Service가 Backend Pod에 전달할 Port |
| `selector` | Backend로 사용할 Pod Label 조건 |

`containerPort`는 Container가 사용할 Port를 문서화하는 Field이며 실제 Process가 해당 Port에서 Listen하도록 만들지는 않는다. Service의 `targetPort`는 실제 Application이 Listen하는 Port와 일치해야 한다.

Service를 생성하고 할당된 ClusterIP를 확인한다.

```bash
kubectl apply -f sample-clusterip.yaml
kubectl get service sample-clusterip
kubectl describe service sample-clusterip
```

Selector와 일치하는 Backend가 EndpointSlice에 등록되었는지 확인한다.

```bash
kubectl get endpointslices \
  -l kubernetes.io/service-name=sample-clusterip
```

Endpoint가 비어 있다면 다음 항목을 확인한다.

- Service의 `spec.selector`와 Pod Label이 일치하는가

- Pod가 Ready 상태인가

- Service의 `targetPort`와 Application의 Listen Port가 일치하는가

## 5 ) Service Traffic 전달 흐름

---

Service Manifest를 적용한 뒤 Control Plane과 Worker는 다음 역할을 수행한다.

```text
Master·관리 Client의 kubectl apply
                │
                ▼
            API Server
                │
                ├── EndpointSlice Controller가 대상 Pod 기록
                ├── CoreDNS가 Service DNS Record 제공
                └── Service Proxy가 참조할 상태 제공
                                  │
                                  ▼
                    Worker의 kube-proxy 또는
                    CNI Service 구현이 Data Plane 구성
                                  │
                                  ▼
                         Backend Pod의 targetPort
```

Kubernetes의 기본 Service Proxy 구현은 kube-proxy이지만 CNI 구현이 Service Data Plane을 대신 구성할 수도 있다. Control Plane은 Service와 EndpointSlice 상태를 관리하고 실제 Packet 전달은 Worker의 Network Data Plane에서 처리된다.

Cluster 내부 요청을 보낼 Test Pod를 생성한다.

```bash
kubectl run testpod \
  --image=amsy810/tools:v2.0 \
  --restart=Never

kubectl wait --for=condition=Ready \
  pod/testpod \
  --timeout=60s
```

Test Pod에서 Service DNS 이름으로 여러 번 요청한다.

```bash
kubectl exec pod/testpod -- \
  curl -s http://sample-clusterip:8080
```

응답에 Backend Pod 정보가 포함되어 있다면 명령을 여러 번 실행하여 서로 다른 Pod가 선택되는지 확인할 수 있다. 다만 Service는 모든 HTTP 요청을 항상 정확히 같은 비율로 분배한다고 보장하지 않는다. Connection 재사용과 Service Proxy 구현에 따라 같은 Backend가 연속해서 선택될 수 있다.

## 6 ) 여러 Port를 제공하는 Service

---

하나의 Service에 여러 Port를 정의할 수 있다. 여러 Port를 사용하면 각 항목을 구분할 수 있도록 `name`을 지정한다.

다음 내용을 `sample-clusterip-multi.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-clusterip-multi
spec:
  type: ClusterIP
  ports:
    - name: http-port
      protocol: TCP
      port: 8080
      targetPort: 80
    - name: https-port
      protocol: TCP
      port: 8443
      targetPort: 443
  selector:
    app: sample-service-app
```

Service를 적용하고 Port 목록을 확인한다.

```bash
kubectl apply -f sample-clusterip-multi.yaml
kubectl describe service sample-clusterip-multi
```

이 예제의 Backend Image는 `80` Port에서만 Listen하므로 `8080` 요청은 처리할 수 있지만 `8443`에서 `443`으로 전달한 요청은 응답하지 않는다. Service에 Port를 정의했다는 사실만으로 Container Process가 해당 Port에서 실행되는 것은 아니다.

## 7 ) Named Port로 서로 다른 Container Port 연결

---

Service의 `targetPort`에는 숫자 대신 Pod의 Port 이름을 사용할 수 있다. Pod마다 실제 Port 번호가 달라도 같은 이름을 부여하면 하나의 Service가 해당 이름을 기준으로 연결한다.

다음 내용을 `sample-named-port-pods.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-named-port-pod-80
  labels:
    app: sample-named-port-app
spec:
  containers:
    - name: nginx-container
      image: amsy810/echo-nginx:v2.0
      ports:
        - name: http
          containerPort: 80
---
apiVersion: v1
kind: Pod
metadata:
  name: sample-named-port-pod-81
  labels:
    app: sample-named-port-app
spec:
  containers:
    - name: nginx-container
      image: amsy810/echo-nginx:v2.0
      env:
        - name: NGINX_PORT
          value: "81"
      ports:
        - name: http
          containerPort: 81
```

두 Pod의 Port 이름은 모두 `http`이지만 실제 Port는 `80`과 `81`이다.

다음 내용을 `sample-named-port-service.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-named-port-service
spec:
  type: ClusterIP
  ports:
    - name: http-port
      protocol: TCP
      port: 8080
      targetPort: http
  selector:
    app: sample-named-port-app
```

Pod와 Service를 생성한다.

```bash
kubectl apply -f sample-named-port-pods.yaml
kubectl apply -f sample-named-port-service.yaml
```

Pod 상태와 EndpointSlice의 Port를 확인한다.

```bash
kubectl get pods -l app=sample-named-port-app
kubectl get endpointslices \
  -l kubernetes.io/service-name=sample-named-port-service \
  -o yaml
```

Service는 각 Pod에서 `http`라는 이름에 대응하는 실제 Port로 Traffic을 전달한다.

## 8 ) Service Discovery

---

> **Service Discovery**
>
> Client가 직접 Backend Pod 목록을 관리하지 않고 Service 이름이나 Cluster 상태를 이용해 접근 대상을 찾는 기능이다.

Cluster 내부 Pod는 주로 다음 두 방식으로 Service를 찾는다.

| 방식 | 특징 |
|---|---|
| 환경 변수 | Pod 생성 시점에 존재하는 Service 정보를 kubelet이 주입 |
| DNS | CoreDNS가 Service 이름을 ClusterIP 또는 Backend DNS Record로 해석 |

Kubernetes API를 직접 사용하는 Application은 EndpointSlice를 조회할 수도 있지만 일반적인 Application은 Service DNS를 사용하는 방식이 적합하다.

### 환경 변수를 이용한 Discovery

Service 이름의 `-`는 `_`로 바뀌고 대문자로 변환되어 환경 변수 이름에 사용된다. `sample-clusterip` Service는 다음과 같은 변수를 제공할 수 있다.

```text
SAMPLE_CLUSTERIP_SERVICE_HOST=<CLUSTER_IP>
SAMPLE_CLUSTERIP_SERVICE_PORT=8080
```

`testpod`가 `sample-clusterip` Service보다 나중에 만들어졌다면 환경 변수를 확인할 수 있다.

```bash
kubectl exec pod/testpod -- \
  env | grep SAMPLE_CLUSTERIP
```

환경 변수는 Pod가 생성될 때 주입된다. Service보다 먼저 만들어진 Pod에는 나중에 생성된 Service 환경 변수가 자동으로 추가되지 않으므로 환경 변수 방식을 사용할 때는 Service를 먼저 생성해야 한다.

### DNS를 이용한 Discovery

Service의 기본 FQDN은 다음 형식이다.

```text
<service-name>.<namespace>.svc.cluster.local
```

`default` Namespace의 `sample-clusterip` Service는 다음 이름으로 조회한다.

```bash
kubectl exec pod/testpod -- \
  dig sample-clusterip.default.svc.cluster.local
```

같은 Namespace에서는 Service 이름만으로 접근할 수 있다.

```bash
kubectl exec pod/testpod -- \
  curl -s http://sample-clusterip:8080
```

다른 Namespace에서는 `<service-name>.<namespace>` 또는 FQDN을 사용한다. DNS는 Service가 먼저 만들어졌는지와 관계없이 현재 Service 정보를 조회할 수 있어 환경 변수 방식보다 일반적으로 사용하기 편하다.

## 9 ) ClusterIP의 Port와 고정 IP

---

ClusterIP Service의 Port 관계는 다음과 같다.

```text
Client
  │ sample-clusterip:8080
  ▼
Service port: 8080
  │
  ▼
Pod targetPort: 80
```

Service를 생성할 때 `.spec.clusterIP`를 직접 지정할 수 있다. 지정할 주소는 API Server에 설정된 Service CIDR 안에 있어야 하고 다른 Service가 사용하지 않는 주소여야 한다.

Master에서 Service CIDR을 확인한다.

```bash
sudo grep service-cluster-ip-range \
  /etc/kubernetes/manifests/kube-apiserver.yaml

kubectl get services -A -o wide
```

실습 Cluster의 Service CIDR과 사용 현황을 확인한 뒤 다음 내용을 `sample-clusterip-vip.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-clusterip-vip
spec:
  type: ClusterIP
  clusterIP: 10.101.106.108
  ports:
    - name: http-port
      protocol: TCP
      port: 8080
      targetPort: 80
  selector:
    app: sample-service-app
```

`10.101.106.108`은 예시 주소이다. 실제 Service CIDR 밖에 있거나 이미 할당된 주소이면 API Server가 생성을 거부하므로 환경에 맞는 미사용 주소로 바꾼다.

```bash
kubectl apply -f sample-clusterip-vip.yaml
kubectl get service sample-clusterip-vip
```

`.spec.clusterIP`는 Service 생성 후 변경할 수 없는 Field이다. 변경하려면 Service를 삭제하고 다시 생성해야 하므로 Client 설정에는 고정 IP보다 Service DNS 이름을 사용하는 편이 적합하다.

ClusterIP 직접 접근은 DNS 문제와 Service Data Plane을 구분하여 확인하는 진단 과정에서 사용할 수 있다. DNS 조회 비용을 피하기 위해 Application 설정에 ClusterIP를 고정하는 방식은 Pod와 Service 운영의 유연성을 떨어뜨린다.

## 10 ) externalIPs 설정

---

> **현재 상태: Deprecated**
>
> `.spec.externalIPs`는 Kubernetes v1.36부터 Deprecated 상태이다. 수업에서 진행한 방식은 학습 기록을 위해 내용을 유지하지만, 신규 구성에서는 External Load Balancer Controller나 Gateway API 를 고려해야 한다.

`.spec.externalIPs`는 외부에서 하나 이상의 Cluster Node로 Routing되는 IP Address와 Service Port로 들어온 Traffic을 Backend에 전달한다. Kubernetes는 해당 외부 IP를 할당하거나 Network Route를 만들어 주지 않으며 Cluster 관리자가 Infrastructure를 준비해야 한다.

Worker 주소를 확인한다.

```bash
kubectl get nodes -o wide
```

다음 내용은 `192.168.0.201`과 `192.168.0.202`가 실제 Worker 주소이고 외부 Client에서 해당 주소로 Routing할 수 있는 실습 환경을 가정한다. `sample-externalip.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-externalip
spec:
  type: ClusterIP
  externalIPs:
    - 192.168.0.201
    - 192.168.0.202
  ports:
    - name: http-port
      protocol: TCP
      port: 8080
      targetPort: 80
  selector:
    app: sample-service-app
```

환경의 실제 Routing 가능한 IP로 바꾼 뒤 Service를 적용한다.

```bash
kubectl apply -f sample-externalip.yaml
kubectl get service sample-externalip
```

Cluster 외부 Linux Client에서 접근한다.

```bash
curl -s http://192.168.0.201:8080
curl -s http://192.168.0.202:8080
```

Node IP를 `externalIPs`에 넣는 동작은 Network 구성에 따라 달라질 수 있다. 해당 IP가 외부에서 Node까지 Routing되고 방화벽과 Service Data Plane이 Traffic을 허용해야 한다.

## 11 ) NodePort Service

---

> **NodePort**
>
> 각 Node의 접근 가능한 IP Address와 지정된 Port를 통해 Service를 외부에 노출하는 Type이다.

NodePort Service는 ClusterIP 기능을 기반으로 하고 각 Node에 동일한 NodePort를 제공한다. 기본 할당 범위는 `30000`~`32767`이며 값을 생략하면 Control Plane이 사용 가능한 Port를 할당한다.

다음 내용을 `sample-nodeport.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-nodeport
spec:
  type: NodePort
  ports:
    - name: http-port
      protocol: TCP
      port: 8080
      targetPort: 80
      nodePort: 30080
  selector:
    app: sample-service-app
```

Service를 생성하고 ClusterIP와 NodePort를 확인한다.

```bash
kubectl apply -f sample-nodeport.yaml
kubectl get service sample-nodeport
```

외부 Client에서 접근 가능한 Node IP로 요청한다.

```bash
curl -s http://<NODE_IP>:30080
```

NodePort가 모든 Network Interface에 일반 Process처럼 `0.0.0.0`으로 Listen한다고 단정할 수는 없다. kube-proxy 또는 CNI Service 구현이 Packet 처리 규칙을 구성하며 NodePort Address 설정, 방화벽과 Network Route에 따라 접근 가능한 Node IP가 달라질 수 있다.

Control Plane Node를 포함한 모든 Node IP로 항상 접근할 수 있는 것도 아니다. 해당 Node에서 Service Data Plane이 동작하고 방화벽과 외부 Routing이 허용되는지 확인해야 한다.

## 12 ) LoadBalancer Service

---

> **LoadBalancer**
>
> Cloud Provider 또는 별도의 Load Balancer Controller와 연동하여 Cluster 외부 주소를 Service에 제공하는 Type이다.

LoadBalancer Service는 기본적으로 ClusterIP 기능을 포함하고 구현에 따라 NodePort를 통해 Node로 Traffic을 전달할 수 있다. 환경에 따라 NodePort 할당을 사용하지 않는 LoadBalancer 구성도 가능하다.

다음 내용을 `sample-loadbalancer.yaml`로 저장한다. 앞서 사용한 `30080`과 충돌하지 않도록 이 예제에서는 `30081`을 사용한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sample-loadbalancer
spec:
  type: LoadBalancer
  ports:
    - name: http-port
      protocol: TCP
      port: 8080
      targetPort: 80
      nodePort: 30081
  selector:
    app: sample-service-app
```

Service를 적용하고 외부 주소 할당 상태를 확인한다.

```bash
kubectl apply -f sample-loadbalancer.yaml
kubectl get service sample-loadbalancer --watch
```

Public Cloud처럼 LoadBalancer 연동을 제공하는 환경에서는 Controller가 외부 IP Address 또는 Hostname을 할당한다. 외부 Load Balancer는 정상 Node로 Traffic을 전달하며 Node 장애를 감지하고 대상에서 제외하기까지 일시적인 지연이 발생할 수 있다.

외부 Load Balancer 구현이 없는 직접 구축 Cluster에서는 `EXTERNAL-IP`가 `<pending>` 상태로 유지될 수 있다. 이는 Service Object가 잘못되었다는 뜻이 아니라 외부 주소를 할당할 Controller가 없거나 아직 처리를 완료하지 않았다는 뜻이다.

Bare Metal 환경에서는 MetalLB와 같은 Load Balancer 구현을 별도로 구성할 수 있다. 이 문서에서는 외부 Package 설치나 MetalLB 배포를 진행하지 않는다.

## 13 ) Service 유형 비교

---

| 구성 | 접근 범위 | Infrastructure 요구 사항 | 현재 사용 판단 |
|---|---|---|---|
| ClusterIP | Cluster 내부 | CNI와 Service Data Plane | 내부 Service의 기본 선택 |
| NodePort | Node IP와 Port | 외부 Route와 방화벽 | Test 또는 외부 Load Balancer의 Backend |
| LoadBalancer | 외부 Load Balancer 주소 | Cloud 연동 또는 Load Balancer Controller | 외부 L4 Service 노출 |
| `externalIPs` | 외부에서 Routing되는 지정 IP | IP 할당과 Route를 관리자가 구성 | Deprecated, 기존 구성 이해용 |
| ExternalName | Cluster DNS를 외부 FQDN에 연결 | CoreDNS와 외부 DNS | DNS 수준 외부 Service 연결 |
| Headless | 개별 Backend DNS | CoreDNS | StatefulSet과 개별 Pod Discovery |
| Ingress | 외부 HTTP·HTTPS | Ingress Controller | Host·Path 기반 L7 Routing |

실습에서는 NodePort로 간단히 외부 접근을 확인할 수 있다. 운영 환경에서는 직접 Node IP를 Client에 고정하기보다 Infrastructure에 맞는 Load Balancer, Ingress 또는 Gateway API를 이용하여 장애 처리와 주소 관리를 분리한다.

## 14 ) 실습 Resource 정리

---

Master 또는 관리 Client에서 외부 노출 Service부터 삭제한다.

```bash
kubectl delete -f sample-loadbalancer.yaml --ignore-not-found
kubectl delete -f sample-nodeport.yaml --ignore-not-found
kubectl delete -f sample-externalip.yaml --ignore-not-found
kubectl delete -f sample-clusterip-vip.yaml --ignore-not-found
```

나머지 Service, Pod와 Deployment를 정리한다.

```bash
kubectl delete -f sample-named-port-service.yaml --ignore-not-found
kubectl delete -f sample-named-port-pods.yaml --ignore-not-found
kubectl delete -f sample-clusterip-multi.yaml --ignore-not-found
kubectl delete -f sample-clusterip.yaml --ignore-not-found
kubectl delete pod testpod --ignore-not-found
kubectl delete -f sample-service-deployment.yaml --ignore-not-found
```

남아 있는 Resource를 확인한다.

```bash
kubectl get services,deployments,pods
```

## 전체 정리

---

> **최종 정리**
>
> - 같은 Pod의 Container는 `localhost`로 통신하고 서로 다른 Pod는 CNI가 구성한 Pod Network를 사용한다.
>
> - Service는 변하는 Pod 집합에 안정적인 ClusterIP와 DNS 이름을 제공하고 EndpointSlice가 Backend 정보를 기록한다.
>
> - `port`는 Client가 Service에 접근할 Port이고 `targetPort`는 Backend Application이 Listen하는 Port이다.
>
> - Service Discovery에는 환경 변수와 DNS를 사용할 수 있으며 일반적인 Application 연결에는 DNS가 적합하다.
>
> - ClusterIP는 내부 통신, NodePort는 Node 주소를 통한 외부 접근, LoadBalancer는 외부 Load Balancer 구현과의 연동에 사용한다.
>
> - `.spec.externalIPs`는 Kubernetes가 IP나 Route를 제공하지 않으며 현재 Deprecated 상태이다.
>
> - Control Plane은 Service와 EndpointSlice 상태를 관리하고 Worker의 kube-proxy 또는 CNI Service 구현이 실제 Traffic 경로를 구성한다.
