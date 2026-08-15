---
title: Docker 명령어와 Registry
description: Docker Registry와 Container 개발 흐름, Image·Container·Volume·Network 관리 명령어
date: 2026-08-14
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
---
## 1 ) Docker Registry

---

Docker Registry는 Image를 저장하고 배포하는 장소이다. Docker Hub는 Docker가 운영하는 공식 Public Registry이며 Apache, MySQL, Ubuntu 등의 공식 Image를 제공한다.

Registry는 여러 **Repository**로 구성된다. 직접 Private Registry를 구축하거나 Cloud Service Provider가 제공하는 Registry를 사용할 수도 있다.

```text
Registry
  ├─ Repository A
  │    ├─ Image:1.0
  │    └─ Image:2.0
  └─ Repository B
```

## 2 ) Container Application 개발 흐름

---

```text
Application Code 작성
        ↓
Dockerfile 작성
        ↓
Image Build
        ↓
Container 생성 및 실행
        ↓
Application Test
        ↓
Registry에 Image Push
```

Dockerfile은 Git으로 관리하며 코드 변경 후 같은 과정을 반복한다. 여러 Container가 필요한 Application은 Docker Compose로 함께 실행하고 각각의 Container와 전체 Application을 테스트한다.

## 3 ) Docker 명령 구조

---

모든 Docker 명령은 `docker`로 시작한다.

```text
docker [상위 명령] [하위 명령] [Option] [대상] [인자]
```

```bash
docker image pull penguin
docker container run penguin
docker container run -d penguin
```

일부 명령은 상위 명령을 생략한 이전 형식도 지원하지만, 동작 대상을 명확히 나타내려면 `docker image ...`, `docker container ...` 형식을 사용하는 것이 좋다.

### Image 명령

| 명령 | 설명 |
|---|---|
| `docker image pull IMAGE` | Registry에서 Image 다운로드 |
| `docker image ls` | Local Image 목록 출력 |
| `docker image build -t NAME .` | Dockerfile로 Image Build 및 Tag 지정 |
| `docker image rm IMAGE` | Image 삭제 |

### Container 명령

| 명령 | 설명 |
|---|---|
| `docker container create IMAGE` | Container 생성 |
| `docker container start CONTAINER` | 정지된 Container 시작 |
| `docker container run IMAGE` | Image Pull, Container 생성과 시작 수행 |
| `docker container stop CONTAINER` | 실행 중인 Container 정지 |
| `docker container rm CONTAINER` | 정지된 Container 삭제 |
| `docker container ls` | 실행 중인 Container 목록 출력 |
| `docker container exec -it CONTAINER CMD` | 실행 중인 Container에서 명령 수행 |
| `docker container cp SRC DEST` | Host와 Container 사이에서 File 복사 |
| `docker container commit CONTAINER IMAGE` | Container 상태를 Image로 저장 |

자주 사용하는 `run` Option은 다음과 같다.

| Option | 의미 |
|---|---|
| `--name` | Container 이름 지정 |
| `-d` | Background 실행 |
| `-i` | 표준 입력 유지 |
| `-t` | 가상 Terminal 할당 |
| `-e` | 환경 변수 설정 |
| `-p` | Host와 Container Port 연결 |
| `-v` | Volume 또는 Directory Mount |

## 4 ) Volume과 Network 명령

---

### Volume

```bash
docker volume create VOLUME_NAME
docker volume inspect VOLUME_NAME
docker volume ls
docker volume rm VOLUME_NAME
docker volume prune
```

`prune`은 사용하지 않는 Resource를 일괄 삭제하므로 삭제 대상을 확인한 후 실행한다.

### Network

```bash
docker network create NETWORK_NAME
docker network inspect NETWORK_NAME
docker network ls
docker network connect NETWORK_NAME CONTAINER_NAME
docker network rm NETWORK_NAME
docker network prune
```

## 5 ) 그 밖의 명령

---

| 명령 | 역할 |
|---|---|
| `docker login` / `logout` | Registry 인증과 해제 |
| `docker search` | Registry의 Image 검색 |
| `docker version` | Client와 Server Version 확인 |
| `docker info` | Docker Engine 정보 확인 |
| `docker system` | Docker System 정보와 Resource 관리 |
| `docker swarm` | Docker Swarm 관리 |
| `docker node` | Swarm Node 관리 |
| `docker service` | Swarm Service 관리 |
| `docker stack` | 여러 Swarm Service로 구성한 Stack 관리 |
| `docker secret` | Swarm의 비밀 정보 관리 |
| `docker plugin` | Docker Plugin 관리 |

명령의 자세한 사용법은 `--help`로 확인할 수 있다.

```bash
docker container run --help
```
