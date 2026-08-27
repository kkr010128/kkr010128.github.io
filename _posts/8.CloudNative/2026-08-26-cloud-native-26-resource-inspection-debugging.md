---
title: Kubernetes Resource 조회와 Pod Debugging
description: kubectl get 출력 형식과 describe, Metrics Server 기반 Resource 사용량, exec·debug·cp·port-forward·logs를 이용한 Pod 확인 방법 정리
date: 2026-08-26
updated_at: 2026-08-27
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
  - kubectl
  - Debugging
---

Kubernetes Resource를 운영하려면 생성 명령뿐 아니라 현재 상태를 정확하게 조회하고 실행 중인 Container를 확인할 수 있어야 한다. `kubectl get`과 `describe`로 Control Plane에 저장된 상태를 확인하고, Metrics Server, `exec`, `debug`, `cp`, `port-forward`와 `logs`로 Worker에서 실행되는 Pod를 점검한다.

## 1 ) Resource 조회 범위

---

현재 API Server가 제공하는 Resource 종류를 확인한다.

```bash
# Master에서 실행
kubectl api-resources
```

Namespace에 속하는 Resource와 Cluster 전체 범위 Resource를 구분한다.

```bash
kubectl api-resources --namespaced=true
kubectl api-resources --namespaced=false
```

조회할 Resource의 Namespace 범위를 이해해야 원하는 결과를 얻을 수 있다.

| Resource | 범위 | 조회 예시 |
|---|---|---|
| Pod, Deployment, Service | Namespace | `kubectl get pods -n default` |
| Node, PersistentVolume | Cluster | `kubectl get nodes` |
| Namespace | Cluster | `kubectl get namespaces` |

## 2 ) kubectl get

---

> **kubectl get**
>
> API Server에서 하나 이상의 Kubernetes Resource 목록이나 현재 상태를 조회하는 명령이다.

### 기본 조회

현재 Namespace의 Pod를 조회한다.

```bash
kubectl get pods
```

특정 종류의 Resource를 조회한다.

```bash
kubectl get deployments
kubectl get services
```

특정 이름의 Resource를 조회한다.

```bash
kubectl get pod sample-pod
```

Node 목록은 Cluster 범위에서 조회한다.

```bash
kubectl get nodes
```

### get all의 범위

현재 Namespace의 대표적인 Workload와 Service Resource를 함께 조회한다.

```bash
kubectl get all
```

`all`은 Kubernetes의 모든 Resource 종류를 뜻하지 않는다. ConfigMap, Secret, Ingress, PersistentVolumeClaim 등은 출력에 포함되지 않을 수 있으므로 필요한 Resource 종류를 명시해서 조회한다.

```bash
kubectl get configmaps,secrets,ingresses,persistentvolumeclaims
```

### Namespace 지정

특정 Namespace의 Resource를 조회한다.

```bash
kubectl get pods --namespace kube-system
```

축약 Option을 사용할 수 있다.

```bash
kubectl get pods -n kube-system
```

모든 Namespace의 Pod를 조회한다.

```bash
kubectl get pods --all-namespaces
```

`-A`는 `--all-namespaces`의 축약 Option이다.

```bash
kubectl get pods -A
```

### Label Selector

특정 Label을 가진 Pod를 조회한다.

```bash
kubectl get pods -l app=sample-app
```

Label 이름과 값은 `-l` 또는 `--selector` 뒤에 지정해야 한다.

```bash
kubectl get pods --selector app=sample-app
```

Pod가 가진 Label을 함께 출력한다.

```bash
kubectl get pods --show-labels
```

## 3 ) 출력 형식

---

`--output` 또는 `-o` Option으로 JSON, YAML, Custom Columns, JSONPath와 Go Template 등 다양한 출력 형식을 선택할 수 있다.

| 형식 | 용도 |
|---|---|
| `wide` | Node, Pod IP 등 기본 표보다 많은 Column 표시 |
| `yaml` | Resource 전체 내용을 YAML로 확인 |
| `json` | Resource 전체 내용을 JSON으로 확인 |
| `custom-columns` | 필요한 Field를 표의 Column으로 구성 |
| `jsonpath` | JSONPath 표현식으로 특정 Field 추출 |
| `name` | `resource/name` 형식만 출력 |

### Wide 출력

Pod가 어느 Worker에서 실행되는지 확인한다.

```bash
kubectl get pods -o wide
```

### YAML과 JSON

Pod 전체 정보를 YAML로 확인한다.

```bash
kubectl get pod sample-pod -o yaml
```

JSON으로 확인한다.

```bash
kubectl get pod sample-pod -o json
```

### Custom Columns

Pod 이름과 실행 중인 Worker의 Host IP를 표로 출력한다.

```bash
kubectl get pods \
  -o custom-columns='NAME:.metadata.name,NODE_IP:.status.hostIP'
```

출력 예시는 다음과 같다.

```text
NAME         NODE_IP
sample-pod   192.168.0.101
```

### JSONPath

특정 Pod의 이름만 추출한다.

```bash
kubectl get pod sample-pod -o jsonpath='{.metadata.name}'
```

줄바꿈까지 출력한다.

```bash
kubectl get pod sample-pod \
  -o jsonpath='{.metadata.name}{"\n"}'
```

Shell이 `{}`와 특수 문자를 먼저 해석하지 않도록 JSONPath 표현식은 작은따옴표로 감싼다.

## 4 ) kubectl describe

---

`kubectl describe`는 Resource의 주요 Field, 상태와 관련 Event를 사람이 읽기 쉬운 형식으로 출력한다.

```bash
kubectl describe pod sample-pod
```

Pod를 점검할 때 다음 내용을 확인한다.

| 항목 | 확인 내용 |
|---|---|
| `Node` | Pod가 배치된 Worker |
| `Status` | Pod Phase |
| `Containers` | Image, State, Ready, Restart Count |
| `Conditions` | Initialized, Ready, PodScheduled 등 |
| `Volumes` | Pod에 연결된 Volume |
| `Events` | Scheduling, Image Pull, Mount와 Probe 관련 Event |

Control Plane은 Worker의 kubelet이 보고한 Pod 상태를 API Server에 저장한다. `describe`는 이 상태와 Event를 조회하므로 Worker에서 발생한 문제를 Master의 kubectl로 확인할 수 있다.

## 5 ) Metrics Server와 kubectl top

---

> **Metrics Server**
>
> 각 Node의 kubelet에서 CPU와 Memory 사용량을 수집하고 Kubernetes Metrics API로 제공하는 Cluster Add-on이다.

`kubectl top`으로 Node와 Pod의 Resource 사용량을 조회하려면 Metrics API를 제공하는 Metrics Server가 필요하다.

```text
Worker의 Container Runtime·cAdvisor
              │
              ▼
           kubelet
              │ CPU·Memory Metric
              ▼
        Metrics Server
              │
              ▼
API Server의 metrics.k8s.io API
              │
              ▼
          kubectl top
```

Metrics Server는 장기간 Metric 저장과 상세 Monitoring을 위한 System이 아니다. Autoscaling과 `kubectl top`에 필요한 CPU·Memory 중심의 짧은 수명 Metric을 제공한다.

### Metrics Server 설치

Master에서 공식 Release Manifest를 적용한다.

```bash
kubectl apply -f \
  https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

`latest` URL은 실행 시점의 최신 Release를 가리킨다. 재현 가능한 운영 배포에서는 Cluster와 호환되는 Version을 확인하고 Release Version이 포함된 URL로 고정하는 방식이 적합하다.

Metrics Server는 `kube-system` Namespace에 배포된다.

```bash
kubectl -n kube-system get deployment metrics-server
kubectl -n kube-system get pods | grep metrics-server
```

Metrics API 등록 상태를 확인한다.

```bash
kubectl get apiservice v1beta1.metrics.k8s.io
```

### kubelet 인증서 확인

일부 학습용 Cluster에서는 kubelet Serving Certificate를 Metrics Server가 검증하지 못해 Metric 수집이 실패할 수 있다. 먼저 Log를 확인한다.

```bash
kubectl -n kube-system logs deployment/metrics-server
```

인증서 검증 오류가 명확하고 학습용 Cluster에서만 우회가 필요하다면 Deployment를 편집한다.

```bash
kubectl edit deployment metrics-server -n kube-system
```

Container `args`에 다음 Option을 추가할 수 있다.

```yaml
- --kubelet-insecure-tls
```

변경 후 Deployment를 재시작하고 상태를 확인한다.

```bash
kubectl rollout restart deployment/metrics-server -n kube-system
kubectl rollout status deployment/metrics-server -n kube-system
```

`--kubelet-insecure-tls`는 kubelet이 제시하는 인증서의 CA 검증을 생략하는 Test용 Option이다. 모든 Local Kubernetes에 필요한 설정이 아니며 운영 환경에서는 올바른 CA와 kubelet Certificate를 구성하여 검증을 유지한다.

### Resource 사용량 조회

Node의 CPU와 Memory 사용량을 확인한다.

```bash
kubectl top nodes
```

현재 Namespace의 Pod 사용량을 확인한다.

```bash
kubectl top pods
```

`kube-system` Namespace의 Pod를 확인한다.

```bash
kubectl top pods -n kube-system
```

Pod 안의 Container별 사용량을 확인한다.

```bash
kubectl top pods -n kube-system --containers
```

Metrics Server를 설치한 직후에는 첫 Metric이 수집될 때까지 잠시 결과가 나오지 않을 수 있다. Pod와 APIService가 정상인데도 조회되지 않으면 Metrics Server Log와 Worker의 kubelet 연결 상태를 확인한다.

## 6 ) Container에서 명령 실행

---

> **kubectl exec**
>
> 실행 중인 Pod의 Container 안에서 Command를 실행하도록 API Server를 통해 요청하는 명령이다.

다음 내용을 `sample-pod.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-pod
spec:
  containers:
    - name: nginx-container
      image: nginx
```

Manifest를 적용하고 Ready 상태를 기다린다.

```bash
kubectl apply -f sample-pod.yaml
kubectl wait --for=condition=Ready pod/sample-pod --timeout=60s
```

Container의 Root Directory를 확인한다.

```bash
kubectl exec pod/sample-pod -- /bin/ls /
```

`--` 앞은 kubectl Option이고 뒤는 Container 안에서 실행할 Command이다.

### Interactive Shell

Container Shell에 접속한다.

```bash
kubectl exec -it pod/sample-pod -- /bin/sh
```

| Option | 역할 |
|---|---|
| `-i` | 표준 입력을 열린 상태로 유지 |
| `-t` | TTY 할당 |
| `--` | kubectl 인자와 Container Command 구분 |

모든 Container Image에 `/bin/bash`가 포함되는 것은 아니다. Nginx처럼 작은 Image에서는 `/bin/sh`를 먼저 사용하고 실제 Image에 존재하는 Shell을 확인한다.

### Container 지정

Pod에 Container가 여러 개 있으면 `-c`로 대상을 지정한다.

```bash
kubectl exec -it pod/sample-pod \
  -c nginx-container \
  -- /bin/sh
```

Shell을 열지 않고 명령을 실행할 수도 있다.

```bash
kubectl exec pod/sample-pod -- \
  /bin/sh -c 'ls -alF / | grep lib'
```

kubectl의 요청은 Control Plane의 API Server를 거쳐 대상 Pod가 실행 중인 Worker의 kubelet로 전달된다.

## 7 ) Port Forwarding

---

`kubectl port-forward`는 관리 Client의 Local Port를 Cluster 안의 Pod Port로 연결한다.

```text
관리 Client localhost:8080
            │
            │ kubectl port-forward
            ▼
      Pod Container :80
```

Pod의 `80` Port를 Master의 `8080` Port로 전달한다.

```bash
kubectl port-forward pod/sample-pod 8080:80
```

다른 Terminal에서 접속한다.

```bash
curl http://127.0.0.1:8080
```

Resource 종류별 예시는 다음과 같다.

```bash
# 특정 Pod
kubectl port-forward pod/sample-pod 8080:80

# sample-deployment가 관리하는 Pod 중 하나
kubectl port-forward deployment/sample-deployment 8080:80

# sample-replicaset이 관리하는 Pod 중 하나
kubectl port-forward replicaset/sample-replicaset 8080:80

# sample-service가 선택한 Pod 중 하나
kubectl port-forward service/sample-service 8080:80
```

Deployment, ReplicaSet과 Service 예시는 Cluster에 해당 이름의 Resource가 존재할 때 실행할 수 있다. Service를 지정할 때 두 번째 Port에는 Service의 `port` 값을 사용한다.

| 값 | 의미 |
|---|---|
| 첫 번째 Port | kubectl을 실행한 Machine의 Local Port |
| 두 번째 Port | 대상 Pod 또는 Service의 Port |

Deployment나 Service를 지정하면 일치하는 Pod 하나가 선택된다. 선택된 Pod가 종료되면 Port Forwarding Session도 끝날 수 있다. 이 기능은 TCP Port에 사용하며 Debugging과 임시 접근에 적합하다.

## 8 ) Pod Log 확인

---

> **kubectl logs**
>
> Pod Container가 표준 출력과 표준 오류로 기록한 Log를 조회하는 명령이다.

Pod의 기본 Container Log를 확인한다.

```bash
kubectl logs pod/sample-pod
```

Pod에 Container가 여러 개 있으면 이름을 지정한다.

```bash
kubectl logs pod/sample-pod -c nginx-container
```

새 Log를 실시간으로 이어서 출력한다.

```bash
kubectl logs -f pod/sample-pod -c nginx-container
```

| Option | 역할 |
|---|---|
| `-c`, `--container` | 조회할 Container 지정 |
| `-f`, `--follow` | 새 Log를 계속 출력 |

`kubectl logs`도 API Server를 통해 대상 Worker의 kubelet과 연결된다. Application이 File에만 Log를 기록하면 기본 `kubectl logs`로 확인되지 않을 수 있으므로 Container Application은 표준 출력과 표준 오류를 사용하는 방식이 적합하다.

## 9 ) Ephemeral Container로 Pod Debugging

---

> **Ephemeral Container**
>
> 실행 중인 Pod의 기존 Container를 재시작하지 않고 문제 분석 도구를 추가하기 위한 임시 Container이다. 일반 Application Container와 달리 주로 Troubleshooting에 사용한다.

Application Image에 Shell이나 `curl` 같은 분석 도구가 없으면 `kubectl exec`만으로 문제를 확인하기 어렵다. `kubectl debug`는 이러한 Pod에 Ephemeral Container를 추가하여 Network와 Process 상태를 점검하게 한다.

다음 내용을 `myapp.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  containers:
    - name: hello-server
      image: blux2/hello-server:1.0
      ports:
        - containerPort: 8080
```

Master 또는 kubeconfig가 설정된 관리 Client에서 Pod를 생성하고 Ready 상태를 확인한다.

```bash
kubectl apply -f myapp.yaml
kubectl wait --for=condition=Ready pod/myapp --timeout=60s
```

`curl`이 포함된 Image를 Ephemeral Container로 추가하고 같은 Pod의 `localhost:8080`에 접근한다.

```bash
kubectl debug --stdin --tty pod/myapp \
  --image=curlimages/curl:8.4.0 \
  --target=hello-server \
  -- sh
```

Debug Container의 Shell에서 Web Server 응답을 확인한다.

```bash
curl http://127.0.0.1:8080
```

| Option | 역할 |
|---|---|
| `--stdin`, `-i` | Debug Container의 표준 입력 유지 |
| `--tty`, `-t` | Interactive Terminal 할당 |
| `--image` | 분석 도구가 포함된 Container Image 지정 |
| `--target` | Process Namespace 확인 대상으로 삼을 기존 Container 지정 |
| `--` | kubectl 인자와 Debug Container에서 실행할 Command 구분 |

Debug Image는 목적에 맞는 Command와 도구를 포함해야 한다. Web 요청 확인에는 `curl` Image가 적합하고, Process나 Network 진단에는 해당 명령이 포함된 Image가 필요하다. `--target`을 통한 Process 확인 범위는 Worker의 Container Runtime 지원 여부에 따라 달라질 수 있다.

요청이 처리되는 흐름은 다음과 같다.

```text
Master·관리 Client의 kubectl debug
              │
              ▼
          API Server
              │ Pod의 Ephemeral Container 정보 전달
              ▼
대상 Worker의 kubelet ──▶ Container Runtime
                              │
                              ▼
                 기존 Pod 안에 Debug Container 실행
```

추가된 Ephemeral Container는 다음 명령으로 확인한다.

```bash
kubectl describe pod myapp
```

Ephemeral Container는 실행 중인 Pod에서 제거하거나 다시 변경하는 일반 Container가 아니다. Debugging이 끝난 뒤 실습 Pod를 삭제하면 함께 정리된다.

```bash
kubectl delete pod myapp
```

## 10 ) Container와 File 복사

---

> **kubectl cp**
>
> 관리 Client의 File이나 Directory를 Pod의 Container로 복사하거나 Container의 File을 관리 Client로 가져오는 명령이다.

기본 형식은 Source와 Target 중 어느 쪽에 `pod-name:path`가 포함되는지에 따라 복사 방향이 결정된다.

```bash
kubectl cp <source> <target>
```

26번 문서 앞에서 작성한 `sample-pod.yaml`을 적용하고 Pod 상태를 확인한다.

```bash
kubectl apply -f sample-pod.yaml
kubectl wait --for=condition=Ready pod/sample-pod --timeout=60s
```

Container의 `/etc/hostname`을 현재 Directory의 `hostname` File로 복사한다.

```bash
kubectl cp sample-pod:/etc/hostname ./hostname
```

복사한 File을 다시 Container의 `/tmp/newfile`로 전송한다.

```bash
kubectl cp ./hostname sample-pod:/tmp/newfile
```

Container 안에 File이 생성되었는지 확인한다.

```bash
kubectl exec pod/sample-pod -- ls -l /tmp/newfile
kubectl exec pod/sample-pod -- cat /tmp/newfile
```

| 형식·Option | 역할 |
|---|---|
| `pod-name:/path` | 현재 Namespace에 있는 Pod의 경로 지정 |
| `namespace/pod-name:/path` | 특정 Namespace의 Pod 경로 지정 |
| `-c <container>` | 다중 Container Pod에서 복사 대상 지정 |

`kubectl cp`는 복사 과정에서 Container 내부의 `tar` 명령을 사용한다. Container Image에 `tar`가 없으면 명령이 실패하므로 먼저 존재 여부를 확인한다.

```bash
kubectl exec pod/sample-pod -- /bin/sh -c 'command -v tar'
```

Symbolic Link, Wildcard 또는 세부 권한을 다루는 복잡한 복사는 `kubectl exec`와 `tar`를 직접 조합하는 방법을 검토한다.

## 전체 정리

---

> **최종 정리**
>
> - `kubectl get`은 Resource 종류, 이름, Namespace와 Label Selector를 조합하여 API Server의 상태를 조회한다.
>
> - `all`은 모든 Kubernetes Resource를 의미하지 않으며 필요한 종류를 명시해서 조회해야 한다.
>
> - Custom Columns와 JSONPath를 사용하면 Script에 필요한 Field만 추출할 수 있다.
>
> - `describe`는 Pod의 Worker 배치, Container 상태, Condition과 Event를 함께 확인할 때 사용한다.
>
> - Metrics Server는 Worker kubelet의 CPU·Memory Metric을 Metrics API로 제공하며 `kubectl top`이 이를 조회한다.
>
> - `exec`, `port-forward`와 `logs` 요청은 API Server를 거쳐 대상 Pod가 실행 중인 Worker로 전달된다.
>
> - `kubectl debug`는 기존 Pod에 분석 도구가 없을 때 Ephemeral Container를 추가하여 문제를 확인한다.
>
> - `kubectl cp`는 관리 Client와 Container 사이에서 File을 복사하며 Container Image에 `tar`가 필요하다.
>
> - `--kubelet-insecure-tls`는 인증서 검증을 생략하므로 학습용 문제 확인에만 제한적으로 사용한다.
