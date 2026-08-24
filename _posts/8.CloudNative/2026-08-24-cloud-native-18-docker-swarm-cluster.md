---
title: Docker Swarm Cluster 구성과 Service 운영
description: Manager와 Worker Cluster 구성, Service 배포, Routing Mesh, 확장, Rolling Update 및 Stack 배포
date: 2026-08-24
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
  - DockerSwarm
---
## 1 ) 클러스터 실습 환경 구성

---

Ubuntu 24.04 VM 세 대를 같은 Network에 연결하고 한 대는 Manager, 두 대는 Worker로 사용한다.

```text
Windows Host
LAPTOP
192.168.0.99
       │
       ├── LAB_MASTER
       │   hostname: master
       │   192.168.0.100
       │
       ├── LAB_WORKER_1
       │   hostname: worker1
       │   192.168.0.101
       │
       └── LAB_WORKER_2
           hostname: worker2
           192.168.0.102
```

수업에서는 NAT 네트워크를 구성하여 한 네트워크로 묶어 사용하는 방향으로 진행했으나, VPN과 SSH를 이용해 홈 네트워크에 접속해 사용하고 있는 현재 환경에 맞게 각 VM은 Bridge Adapter를 사용하여 Host에서 SSH로 접속했다. 
세 VM 모두 Docker Engine과 Compose Plugin을 설치해 환경을 준비했다.


![Manager와 Worker VM에 Docker를 설치하는 화면](notes/assets/post/2026-08-24-cloud-native-18-docker-swarm-cluster/02.webp)

```bash
sudo apt-get update
sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

설치 후 Version과 Service 상태를 확인한다.

```bash
sudo docker version
sudo systemctl enable --now docker
sudo systemctl status docker
```

현재 사용자가 `sudo` 없이 Docker를 실행하려면 `docker` Group에 추가한 뒤 다시 로그인한다.

```bash
sudo usermod -aG docker "$(whoami)"
```

> Docker Socket의 권한을 `666`으로 변경하면 모든 사용자가 Docker Daemon을 제어할 수 있으므로 사용하지 않는다.


Docker Engine 설치는 모든 Node에서 수행하지만 Cluster를 생성하고 관리하는 명령은 Manager에서 수행한다. 

> Kubernetes도 Container Runtime과 Node 구성 요소는 모든 Machine에 필요하지만 Cluster 제어 명령은 Control Plane을 중심으로 수행한다.

## 2 ) Swarm Cluster 구성

---

### Manager 초기화

Manager로 사용할 `master`에서 Swarm Mode를 초기화한다.

```bash
docker swarm init

# docker swarm init --advertise-addr 192.168.0.100
```

`docker wsarm init` 으로만 실행하면 Docker가 해당 호스트의 IP 주소를 자동으로 선택해 Swarm Manager를 초기화한다.

`--advertise-addr`는 다른 Node가 Manager에 접속할 주소를 지정한다. 

다른 Swarm 노드들에게 "이 Manager에는 계속 `192.168.0.100`으로 접속해"라고 명시하는 것이다.


초기화가 끝나면 현재 Node가 Manager가 되고 Worker가 Cluster에 참여할 때 사용할 `docker swarm join` 명령이 출력된다.

> Kubernetes에서는 `kubeadm init`이 Control Plane을 초기화하고 Worker가 사용할 `kubeadm join` 명령을 출력한다. Cluster의 제어 주체를 먼저 만들고 다른 Node가 Token을 이용해 참여한다는 흐름은 비슷하다. 다만 Swarm은 Docker Engine에 Orchestrator가 내장되어 있고 Kubernetes는 API Server, Scheduler, Controller Manager 등 별도의 Control Plane 구성 요소를 사용한다.

### Worker 참여

Manager에서 출력된 명령을 `worker1`, `worker2`에서 실행한다.

```bash
docker swarm join \
  --token SWMTKN-1-WORKER_TOKEN \
  192.168.0.100:2377
```

![Manager 초기화 후 두 Worker가 Swarm에 참여한 화면](notes/assets/post/2026-08-24-cloud-native-18-docker-swarm-cluster/04.webp)

Manager에서는 Worker Token을 다시 확인할 수 있다.

```bash
docker swarm join-token worker
```

![Manager에서 Worker 참여 Token을 확인한 화면](notes/assets/post/2026-08-24-cloud-native-18-docker-swarm-cluster/08.webp)

`docker swarm join-token`은 Manager가 가진 Cluster 상태를 조회해야 하므로 Worker에서는 실행할 수 없다. 
>Kubernetes의 Join Token도 Control Plane에서 `kubeadm token create --print-join-command`로 다시 만들거나 조회한다.

Join Token은 Node를 Cluster에 참여시킬 수 있는 인증 정보이므로 공개 저장소나 게시물에 실제 값을 남기지 않는다. 노출되었다면 Token을 교체해야 한다.

물론 참여하기 위해서는 Manager와 네트워크 통신이 가능해야 한다. 하지만 토큰이 공개되어 있으면 공격자가 내부에 접근했을 때 필요한 인증 정보를 이미 확보한 상태가 되기에 인증 정보를 담고 있는 토큰은 비밀 정보로 취급해야 한다.

### Swarm Port 확인

Manager에서 Docker Daemon이 사용하는 Port를 확인한다.

```bash
sudo netstat -nlp | grep dockerd
```

![Manager에서 Docker Swarm 통신 Port를 확인한 화면](notes/assets/post/2026-08-24-cloud-native-18-docker-swarm-cluster/06.webp)

Swarm Node 사이에는 다음 Port가 필요하다.

| Port | Protocol | 역할 |
|---|---|---|
| `2377` | TCP | Manager의 Cluster 관리 통신 |
| `7946` | TCP/UDP | Node Discovery와 통신 |
| `4789` | UDP | Overlay Network Traffic |

> Kubernetes도 Control Plane API, kubelet, Service Network 등에 별도의 Port가 필요하지만 Swarm과 Port 번호 및 구성 요소는 다르다.

### Node 상태 확인

Manager에서 Node 목록을 조회한다.

```bash
docker node ls
```

![Manager와 Worker에서 docker node ls를 실행한 결과](notes/assets/post/2026-08-24-cloud-native-18-docker-swarm-cluster/10.webp)

같은 명령을 Worker에서 실행하면 `This node is not a swarm manager` 오류가 발생한다. `docker node ls`는 Cluster 전체 상태를 조회하는 관리 명령이므로 Manager에서만 사용할 수 있다.

> Kubernetes의 `kubectl get nodes`도 API Server를 통해 Cluster 상태를 조회한다. 명령 자체가 Control Plane Machine에서만 실행되어야 하는 것은 아니지만, 외부 Machine이나 Worker에서 실행하려면 API Server 주소와 인증 정보가 담긴 Kubeconfig가 필요하다. Swarm Worker가 관리 API를 제공하지 않는 것과 달리 Kubernetes Client는 인증 설정이 있으면 어느 Machine에서도 API Server에 요청할 수 있다.

```bash
docker info
docker network ls
```

`docker info`의 `Swarm: active`와 Network 목록의 `ingress`를 확인한다.

### Node 제거

Worker를 정상적으로 제거할 때는 제거할 Worker에서 Swarm을 떠난 뒤 Manager에서 Node 정보를 정리한다.

```bash
# 제거할 Worker에서 실행
docker swarm leave
```

```bash
# Manager에서 실행
docker node rm worker1
```

Manager가 Swarm을 떠나면 Manager Quorum에 영향을 줄 수 있다. 특히 마지막 Manager에서 `--force`로 떠나면 Cluster를 더 이상 관리할 수 없으므로 실습 종료 외에는 신중하게 사용한다.

## 3 ) Service 생성과 조회

---

Manager에서 반복적으로 Message를 출력하는 Service를 생성한다.

```bash
docker service create \
  --name swarm-start \
  alpine:3 \
  /bin/sh -c "while true; do echo 'Docker Swarm Start'; sleep 3; done"
```

Service 상태와 Task 배치를 확인한다.

```bash
docker service ls
docker service ps swarm-start
docker service logs -f swarm-start
```

`docker service ls`, `docker service ps`, `docker service logs`는 Cluster Service를 관리하는 명령이므로 Manager에서 실행한다. Worker에서는 자신에게 배치된 Container를 `docker container ls`로 확인할 수 있지만 Service의 전체 Replica 상태는 조회할 수 없다.

> Kubernetes에서는 Deployment를 생성한 뒤 `kubectl get deployments`, `kubectl get pods`, `kubectl logs`로 비슷한 정보를 확인한다. Swarm의 Service는 원하는 Replica 상태를 선언하는 단위이며 Kubernetes에서는 주로 Deployment가 이 역할을 담당한다.

Service를 삭제한다.

```bash
docker service rm swarm-start
```

## 4 ) Nginx Service와 Routing Mesh

---

Worker에만 Nginx Task가 배치되도록 Constraint를 지정하고 Service Port를 공개한다.

```bash
docker service create \
  --name web-alb \
  --replicas 2 \
  --publish published=8001,target=80 \
  --constraint 'node.role==worker' \
  nginx
```

```bash
docker service ps web-alb
```

`node.role==worker` Constraint 때문에 Nginx Task는 Manager에 배치되지 않는다. 그러나 Service의 8001번 Port를 공개하면 Manager와 두 Worker를 포함한 모든 Node가 동일한 8001번 Port로 들어오는 Traffic을 받는다.

```bash
curl http://192.168.0.100:8001
curl http://192.168.0.101:8001
curl http://192.168.0.102:8001
```

세 주소 모두 같은 Service에 연결된다. 이것은 모든 Node가 공개 Port를 감시하는 Swarm Routing Mesh의 동작이다. 요청을 받은 Node에 Nginx Task가 없더라도 Ingress Network가 실제 Task가 실행 중인 Node로 Traffic을 전달한다.

> Kubernetes에서는 Deployment만 생성해도 모든 Node에 같은 외부 Port가 자동으로 열리지 않는다. 외부 접근에는 NodePort, LoadBalancer 또는 Ingress 같은 별도의 Service 노출 방식이 필요하다. NodePort를 사용하면 여러 Node의 동일 Port로 접근할 수 있다는 점은 Swarm Routing Mesh와 비슷하지만, Kubernetes Service와 kube-proxy 또는 CNI가 Traffic 전달을 담당한다는 차이가 있다.

### 임시 Page 변경

Task가 배치된 Worker에서 테스트용 `index.html`을 만든 뒤 특정 Container에 복사할 수 있다.

```html
<h1>Swarm Worker 1</h1>
```

```bash
docker container ls
docker cp index.html CONTAINER_ID:/usr/share/nginx/html/index.html
```

이 방법은 특정 Task의 쓰기 Layer만 변경한다. 다른 Replica에는 적용되지 않고 Task가 재생성되면 변경 내용도 사라지므로 Load Balancing을 눈으로 확인하는 임시 실습에만 사용한다. 실제 배포에서는 Page를 포함한 새로운 Image를 Build하여 Service를 Update한다.

## 5 ) Overlay Network와 Service Discovery

---

Swarm의 Overlay Network는 여러 Docker Host에 걸쳐 있는 Service를 하나의 가상 Network로 연결한다. 같은 Overlay Network의 Service는 IP를 직접 관리하지 않고 Service 이름으로 통신한다.

```bash
docker network create \
  --driver overlay \
  dailylog-net
```

Service에는 Virtual IP가 할당되며 내장 DNS가 Service 이름을 이 주소로 해석한다. Client가 Virtual IP로 요청하면 Swarm이 실행 중인 Replica 중 하나로 전달한다. Replica가 늘거나 다른 Node로 이동해도 Application은 같은 Service 이름을 사용한다.

> Kubernetes도 Service 이름을 Cluster DNS로 조회하고 고정된 ClusterIP를 통해 여러 Pod로 요청을 전달한다. Service Discovery 관점은 비슷하지만 Swarm은 Service와 Overlay Network를 Docker Engine이 직접 관리하고 Kubernetes는 Service, EndpointSlice, kube-proxy 또는 Network Plugin이 역할을 나누어 담당한다.

## 6 ) Service 확장과 배포 Mode

---

### Replicated Mode

실행 중인 Service의 Replica 수를 변경한다.

```bash
docker service scale web-alb=5
```

Node 수보다 Replica가 많으면 한 Node에 여러 Task가 배치될 수 있다. Swarm은 Node 수와 Replica 수를 일치시키는 것이 아니라 가용 Resource와 Constraint를 기준으로 Task를 배치한다.

> Kubernetes의 `kubectl scale deployment ... --replicas=5`도 원하는 Pod 수를 변경한다. 두 도구 모두 선언한 수와 실제 실행 수가 같아지도록 조정한다.

### Global Mode

조건에 맞는 모든 Node에 Task를 하나씩 배치한다.

```bash
docker service create \
  --name global-nginx \
  --mode global \
  nginx
```

Global Mode는 각 Node에서 동작해야 하는 Monitoring Agent나 Log Collector에 적합하다. Kubernetes의 DaemonSet이 같은 목적을 담당한다.

## 7 ) 장애 복구와 Desired State

---

Replica가 세 개인 Service를 생성한다.

```bash
docker service create \
  --name recovery-test \
  --replicas 3 \
  nginx
```

Task가 배치된 Worker에서 Container 하나를 강제로 삭제한다.

```bash
docker container rm -f CONTAINER_ID
```

Manager에서 일정 시간 뒤 Task 상태를 다시 확인한다.

```bash
docker service ps recovery-test
```

실행 중인 Replica가 세 개보다 적어졌으므로 Swarm은 새로운 Task를 생성한다. 사용자가 선언한 Desired State와 실제 상태를 지속적으로 비교하고 차이를 복구하는 동작이다.

> Kubernetes의 Deployment Controller도 Pod가 삭제되면 ReplicaSet을 통해 새로운 Pod를 생성한다. 자동 복구의 기본 원리는 같지만 Swarm은 Service Task를, Kubernetes는 Pod와 Controller Resource를 중심으로 상태를 관리한다.

## 8 ) Rolling Update와 Rollback

---

Redis 6.0 Service를 생성한 뒤 Image Version을 변경한다.

```bash
docker service create \
  --name my-database \
  --replicas 3 \
  redis:6.0-alpine
```

```bash
docker service update \
  --image redis:6.2.5-alpine \
  my-database
```

```bash
docker service ps my-database
```

Rolling Update는 기존 Task를 한꺼번에 교체하지 않고 정해진 단위와 간격으로 교체한다.

| Option | 역할 |
|---|---|
| `--update-parallelism` | 동시에 Update할 Task 수, 기본값 `1` |
| `--update-delay` | 한 Update Group이 끝난 뒤 다음 Group까지 대기 시간 |
| `--update-order` | `stop-first` 또는 `start-first` |
| `--update-failure-action` | 실패 시 `pause`, `rollback`, `continue` |
| `--update-max-failure-ratio` | 허용할 Update 실패 비율 |

기본 Update 순서는 기존 Task를 먼저 중지하는 `stop-first`이다. 새 Task를 먼저 실행하여 중단 시간을 줄이려면 `start-first`를 명시한다.

```bash
docker service update \
  --image redis:6.2.5-alpine \
  --update-parallelism 1 \
  --update-delay 10s \
  --update-order start-first \
  --update-failure-action rollback \
  my-database
```

실패한 Update를 이전 Service Spec으로 되돌린다.

```bash
docker service rollback my-database
```

```bash
docker info
docker swarm update --task-history-limit 10
```

Task History Limit은 이전 Task 기록의 보존 수를 조정한다. Rollback 자체가 여러 Version의 Image 이력을 원하는 만큼 보관하는 기능이라는 의미는 아니다.

> Kubernetes Deployment도 RollingUpdate Strategy, `maxUnavailable`, `maxSurge`와 `kubectl rollout undo`를 제공한다. 두 도구 모두 단계적 교체와 Rollback을 지원하지만 Option 이름과 상태를 기록하는 Resource 구조는 다르다.

### Resource와 Service 설정 변경

실행 중인 Service의 설정을 변경할 수 있다.

```bash
docker service update \
  --limit-cpu 0.5 \
  --limit-memory 512M \
  --env-add MY_VAR=value \
  --env-rm OLD_VAR \
  --publish-add published=8002,target=80 \
  --replicas 5 \
  web-alb
```

```bash
docker service inspect --pretty web-alb
```

## 9 ) Node Drain과 유지 보수

---

Node를 유지 보수할 때 `Drain`으로 변경하면 기존 Task를 다른 Active Node로 옮기고 새로운 Task도 배치하지 않는다.

```bash
docker node update \
  --availability drain \
  worker1
```

```bash
docker service ps web-alb
```

유지 보수가 끝나면 다시 `Active`로 변경한다.

```bash
docker node update \
  --availability active \
  worker1
```

`docker node update`는 Manager에서 실행한다. Worker는 자신의 Availability를 직접 변경할 수 없다.

> Kubernetes에서는 `kubectl cordon NODE`로 새로운 Pod Scheduling을 막고 `kubectl drain NODE`로 기존 Workload를 다른 Node로 이동시킨다. Swarm의 `Drain`은 이 두 작업을 하나의 Availability 상태 변경으로 처리한다.

## 10 ) Docker Stack 배포

---

Swarm에서는 여러 Service, Network와 Volume을 하나의 Stack으로 배포할 수 있다. `docker stack` 명령은 Manager에서 실행한다.

### Overlay Network 생성

```bash
docker network create \
  --driver overlay \
  dailylog-net
```

### Stack File 작성

`docker stack deploy`는 현재도 Legacy Compose v3 형식을 사용하므로 Stack File에는 `version`을 유지한다.

```yaml
version: "3.9"

services:
  mongodb:
    image: dbgurum/dailylog:db_1.0
    ports:
      - "27017:27017"
    networks:
      - dailylog-net
    deploy:
      placement:
        constraints:
          - node.role != manager
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3
        window: 120s

  backend:
    image: dbgurum/dailylog:back_1.0
    ports:
      - "8000:8000"
    networks:
      - dailylog-net
    environment:
      MONGO_URL: mongodb://mongodb:27017
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role != manager
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3
        window: 120s

  frontend:
    image: dbgurum/dailylog:front_1.0
    ports:
      - "3000:8000"
    networks:
      - dailylog-net
    environment:
      PORT: "8000"
      DAILYLOG_API_ADDR: backend:8000
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role != manager
      restart_policy:
        condition: on-failure
        delay: 10s
        max_attempts: 3
        window: 120s

networks:
  dailylog-net:
    external: true
```

Stack 배포에서는 각 Node가 Image를 내려받을 수 있어야 하므로 Image를 Registry에 Push한 상태여야 한다. `depends_on`은 Stack Service의 준비 순서를 제어하는 기능으로 의존하지 않고, Backend가 Database 연결 실패를 재시도하도록 Application과 Restart Policy를 구성한다.

### 배포와 확인

```bash
docker stack deploy \
  --compose-file docker-compose.yaml \
  dailylog
```

```bash
docker stack ls
docker stack services dailylog
docker stack ps dailylog
```

Stack을 삭제한다.

```bash
docker stack rm dailylog
```

> Kubernetes에서는 여러 Resource가 작성된 YAML을 `kubectl apply`로 배포한다. Swarm Stack과 마찬가지로 선언형 File로 여러 구성 요소를 배포하지만 Kubernetes는 Deployment, Service, ConfigMap, Secret 등 Resource 종류를 각각 정의한다.


---

> **최종 정리**
>
> - Manager에서 Swarm을 초기화하고 Worker는 Join Token으로 Cluster에 참여한다.
>
> - Cluster 전체의 Node와 Service 관리 명령은 Manager에서 실행하며 Worker는 할당된 Task를 실행한다.
>
> - Service Port를 공개하면 Task 배치 여부와 관계없이 모든 Node가 같은 Port로 Traffic을 받는다.
>
> - Overlay Network와 내장 DNS를 통해 Service 이름으로 통신하며 Routing Mesh가 실행 중인 Task로 요청을 전달한다.
>
> - Replicated Mode는 지정한 수의 Task를 유지하고 Global Mode는 조건에 맞는 모든 Node에 Task를 배치한다.
>
> - Swarm은 Desired State, Rolling Update, Rollback과 Node Drain으로 Service 운영을 지원한다.
>
> - `docker stack deploy`는 여러 Service와 Network를 하나의 Application Stack으로 배포한다.
