---
title: Docker Swarm Ingress가 요청을 Container까지 전달하는 방법
description: Published Port로 들어온 요청이 Routing Mesh와 IPVS, Ingress Overlay Network를 거쳐 Service Task에 도달하는 과정
date: 2026-08-24
series: TechNotes
tags:
  - DeepDive
  - Docker
  - DockerSwarm
  - Network
---
## 1 ) 실습에서 이상한 점을 발견했다

---

Docker Swarm에서 Nginx Container는 Worker에만 배치했다.

```bash
docker service create \
  --name web-alb \
  --replicas 2 \
  --publish published=8001,target=80 \
  --constraint 'node.role==worker' \
  nginx
```

Cluster의 상태는 다음과 같다.

```text
Manager  192.168.0.100  Nginx Container 없음
Worker 1 192.168.0.101  Nginx Container 실행
Worker 2 192.168.0.102  Nginx Container 실행
```

그런데 Manager IP로 접속해도 Nginx Page가 출력됐다.

```bash
curl http://192.168.0.100:8001
```

Worker IP로 접속한 결과도 같았다.

```bash
curl http://192.168.0.101:8001
curl http://192.168.0.102:8001
```

Manager에는 Nginx Container가 없는데 누가 요청을 받은 것일까?

## 2 ) 결론부터 확인해 보자

---

Manager가 Nginx 요청을 직접 처리한 것은 아니다. Manager는 요청을 받은 뒤 실제 Nginx Container가 있는 Worker로 전달했다.

```text
Client
  │ Manager_IP:8001로 요청
  ▼
Manager
  │ 실제 Nginx Task로 전달
  ▼
Worker 1 또는 Worker 2
  │
  ▼
Nginx Container가 응답
```

이 동작을 가능하게 만드는 기능이 Docker Swarm의 **Routing Mesh**이다.

Routing Mesh가 적용되면 모든 Swarm Node가 Service 요청의 입구가 된다. 요청을 받은 Node에 Container가 없어도 실제 Container가 실행 중인 다른 Node로 요청을 보낼 수 있다.

## 3 ) 일반 Container의 Port 연결과 무엇이 다를까

---

일반 Container의 Port를 다음과 같이 연결했다고 가정한다.

```bash
docker container run -p 8001:80 nginx
```

이 명령은 현재 Host의 8001번 Port를 현재 Host에서 실행 중인 Nginx Container의 80번 Port와 연결한다. 다른 Host의 8001번 Port까지 열리지는 않는다.

Swarm Service에서는 다음 값을 사용했다.

```text
published=8001,target=80
```

| 항목 | 의미 |
|---|---|
| `published=8001` | Swarm 외부에서 Service에 접속할 Port |
| `target=80` | Nginx Container가 실제로 요청을 받는 Port |

8001번 Port는 특정 Container에 연결된 Port가 아니라 `web-alb` Service로 들어가는 공통 입구이다.

```text
Swarm Service의 8001번 Port
          │
          ├── Worker 1의 Nginx:80
          └── Worker 2의 Nginx:80
```

Replica가 늘어나도 외부에서는 같은 8001번 Port를 사용한다.

## 4 ) 왜 모든 Node가 8001번 Port로 요청을 받을까

---

Swarm Service의 기본 Port 공개 방식은 `ingress` Mode이다.

```text
published=8001,target=80,mode=ingress
```

Ingress Mode에서는 모든 Node가 8001번 Port로 들어오는 요청을 받을 수 있도록 Routing Mesh가 구성된다.

```text
Manager:8001  ─┐
Worker1:8001  ─┼─→ web-alb Service
Worker2:8001  ─┘
```

여기서 가장 중요한 차이는 다음과 같다.

>모든 Node에 Nginx가 실행된다. → X
>
모든 Node가 Service 요청의 입구가 된다. → O

Manager는 Nginx를 실행하지 않는다. Service의 입구 역할만 하며 실제 HTTP 응답은 Worker의 Nginx가 만든다.

## 5 ) Manager로 들어온 요청은 어떻게 Worker를 찾아갈까

---

Manager의 8001번 Port로 요청이 들어온 과정을 단계별로 살펴본다.

### 1. Manager가 Service 요청을 받는다

Client가 `192.168.0.100:8001`로 요청한다. Manager에는 8001번 Port가 `web-alb` Service에 공개됐다는 Network 규칙이 설정되어 있다.

### 2. IPVS가 Nginx Task 하나를 선택한다

Swarm Node가 Published Port의 요청을 받으면 Linux의 IPVS(커널에서 동작하는 L4 LB)가 해당 Service에서 실행 중인 Task 하나를 선택한다.

```text
web-alb Service
   │
   ├── Worker 1의 Task
   └── Worker 2의 Task
```

IPVS는 요청을 어느 Task로 보낼지 결정하는 Load Balancer 역할을 한다.

### 3. Ingress Network로 요청을 전달한다

선택된 Task가 다른 Node에 있다면 `ingress` Overlay Network를 통해 요청을 전달한다.

```text
Manager
  │ ingress Overlay Network
  ▼
Worker 2
  │
  ▼
Nginx Container:80
```

Overlay Network는 서로 다른 Docker Host의 Container가 같은 가상 Network에 연결된 것처럼 통신하게 한다.

### 4. Nginx가 응답한다

Worker의 Nginx Container가 HTTP 요청을 처리하고 응답을 반환한다. Client는 요청이 어느 Worker에서 처리됐는지 알 필요가 없다.

전체 경로를 합치면 다음과 같다.

```text
Client
  │ Manager_IP:8001
  ▼
Manager의 Routing Mesh
  │
  ▼
IPVS가 Nginx Task 선택
  │
  ▼
Ingress Overlay Network
  │
  ▼
Worker의 Nginx Container:80
```

## 6 ) `netstat`에서 Port가 보이지 않을 수도 있다

---

일반적으로 Application이 Port를 열면 `netstat`이나 `ss`에서 해당 Process가 `LISTEN` 중인 것으로 나타난다.

Swarm의 Published Port는 일반 Application Process가 직접 Socket을 열고 기다리는 구조와 다르다. Docker의 Network 규칙과 IPVS가 Traffic을 처리하므로 8001번 Port가 일반적인 Listening Socket처럼 보이지 않을 수 있다.

```bash
sudo netstat -nlp | grep 8001
```

출력이 없다는 이유만으로 Service Port가 공개되지 않았다고 판단할 수 없다. Published Port는 Manager에서 Service 설정을 직접 확인하는 편이 정확하다.

```bash
docker service inspect \
  --format '{{json .Endpoint.Spec.Ports}}' \
  web-alb
```

```json
[
  {
    "Protocol": "tcp",
    "TargetPort": 80,
    "PublishedPort": 8001,
    "PublishMode": "ingress"
  }
]
```

## 7 ) Service VIP와는 어떤 차이가 있을까

---

Routing Mesh와 Service VIP는 모두 요청을 Replica로 분산하지만 요청이 시작되는 위치가 다르다.

### Routing Mesh

Swarm 외부의 Client가 Published Port를 통해 들어올 때 사용한다.

```text
외부 Client
→ Node_IP:8001
→ Routing Mesh
→ Nginx Task
```

### Service VIP

같은 Overlay Network 안의 다른 Service가 Service 이름으로 접속할 때 사용한다.

```text
Backend Container
→ web-alb
→ Docker DNS
→ Service VIP
→ Nginx Task
```

| 구분 | Routing Mesh | Service VIP |
|---|---|---|
| 요청 출발 | Swarm 외부 | Swarm 내부 Service |
| 사용하는 주소 | `Node IP:Published Port` | Service 이름 |
| 주요 목적 | 외부 요청 전달 | Service 간 통신 |

Manager IP로 Nginx에 접속할 수 있었던 이유는 Service VIP가 아니라 Routing Mesh 때문이다.

## 8 ) 실제 사용자는 어느 Node IP로 접속할까

---

실습에서는 어느 Node IP를 사용해도 접속할 수 있다. 그러나 실제 사용자에게 여러 Node IP를 직접 알려주지는 않는다. Domain을 Node 하나에만 연결하면 해당 Node가 중단됐을 때 다른 Worker가 정상이어도 사용자가 접속하지 못하기 때문이다.

일반적으로 Swarm 앞에 외부 Load Balancer나 고가용성 VIP를 둔다.

```text
사용자
  │ service.example.com
  ▼
외부 Load Balancer
  │
  ├── Manager:8001
  ├── Worker 1:8001
  └── Worker 2:8001
          │
          ▼
    Swarm Routing Mesh
          │
          ▼
      Nginx Task
```

두 기능은 서로 다른 문제를 해결한다.

- 외부 Load Balancer는 사용자가 접속할 하나의 주소와 Node 장애 대응을 제공한다.

- Routing Mesh는 Task가 어느 Node에 있는지 외부에서 추적하지 않아도 되게 한다.

## 9 ) Reverse Proxy와 Routing Mesh는 같은 기능일까

---

둘 다 요청을 뒤쪽 Server로 전달하지만 요청을 나누는 기준이 다르다.

Routing Mesh는 Published Port로 들어온 Network Connection을 Service Task 중 하나로 전달한다.

```text
8001번 Port의 요청
→ web-alb의 Nginx Task 중 하나
```

Nginx 같은 Reverse Proxy는 HTTP 요청을 읽고 Domain이나 URL Path에 따라 Backend를 선택한다.

```text
/api     → Backend API
/images  → Image Server
```

Reverse Proxy의 목적은 단순히 Backend IP를 숨기는 것이 아니다. TLS 처리, HTTP Routing, Header 변경과 Cache 같은 Application 계층 기능도 담당한다.

Routing Mesh와 Reverse Proxy는 함께 사용할 수도 있다.

```text
외부 Load Balancer
→ Swarm Routing Mesh
→ Nginx Reverse Proxy Service
→ Backend Service
```

## 10 ) 모든 Node에서 Port를 열고 싶지 않다면

---

`mode=host`로 Port를 공개하면 Routing Mesh를 우회할 수 있다.

```bash
docker service create \
  --name web-host-mode \
  --mode global \
  --publish published=8001,target=80,mode=host \
  nginx
```

| 접속 상황 | Ingress Mode | Host Mode |
|---|---|---|
| Task가 있는 Node | 접속 가능 | 접속 가능 |
| Task가 없는 Node | 다른 Node의 Task로 전달 | 접속 불가 |
| Load Balancing | Routing Mesh가 처리 | 별도로 구성 |

Host Mode에서는 외부 Load Balancer가 Task가 실행 중인 Node를 알아야 한다. 같은 Published Port를 사용하는 Task를 한 Node에 여러 개 배치하기도 어렵다.

어느 Node로든 간편하게 요청을 받고 싶다면 Ingress Mode가 적합하다. 요청 경로와 Load Balancing을 직접 제어해야 한다면 Host Mode를 검토한다.

## 11 ) 다시 처음 질문으로 돌아가면

---

Manager에 Nginx Container가 없는데도 `Manager_IP:8001`로 접속할 수 있었던 이유는 다음과 같다.

1. `published=8001`은 특정 Container가 아니라 Swarm Service에 적용된다.

2. Ingress Mode에서는 모든 Swarm Node가 8001번 Port 요청의 입구가 된다.

3. Manager로 들어온 요청은 IPVS와 Ingress Network를 거쳐 실제 Nginx Task로 전달된다.

4. HTTP 응답은 Manager가 아니라 Worker의 Nginx Container가 생성한다.

> **Swarm에서는 Container가 없는 Node도 Service의 입구가 될 수 있다.**

이 구조 덕분에 Client는 Nginx Task가 어느 Worker에서 실행 중인지 추적하지 않고 Swarm Node의 Published Port로 요청할 수 있다.
