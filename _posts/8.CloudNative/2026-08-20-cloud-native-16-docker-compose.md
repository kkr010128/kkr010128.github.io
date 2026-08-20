---
title: Docker Compose
description: Docker Compose의 역할과 Compose File 작성 방법 및 Apache와 MariaDB 실행 실습
date: 2026-08-20
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
  - DockerCompose
---
## 1 ) Docker Compose 개요

---

분산 Application은 Web Frontend, Backend API, Database처럼 여러 구성 요소로 이루어진다. Dockerfile은 각 구성 요소를 하나의 Image로 Packaging하지만 전체 Application을 실행하려면 여러 Container의 Port, Volume, 환경 변수와 Network를 함께 설정해야 한다.

각 Container를 `docker container run`으로 하나씩 실행할 수도 있지만 명령이 많아질수록 Option을 누락하거나 실행 순서를 잘못 지정하기 쉽다. Docker Compose는 공통 목적을 가진 여러 Container의 구성을 하나의 YAML File에 선언하고 함께 관리하는 도구이다.

- 각 Application 구성 요소를 `services`에 정의한다.

- Container의 Image, Port, Volume, 환경 변수와 재시작 정책을 기록한다.

- 필요한 Network와 Volume 같은 Docker Object를 생성한다.

- `docker compose up`으로 Application Stack을 생성하고 실행한다.

- `docker compose down`으로 Stack의 Container와 Network를 중지하고 삭제한다.

Compose File은 여러 Service가 실행 중일 때 갖추어야 하는 원하는 상태를 기술한다. Compose가 File을 읽으면 Docker API를 통해 Container, Network와 Volume을 구성한다.

## 2 ) Dockerfile과 Docker Compose

---

Dockerfile과 Docker Compose는 서로 다른 범위를 담당한다.

| 구분 | Dockerfile | Docker Compose |
|---|---|---|
| 목적 | 하나의 Image 생성 | 여러 Container로 구성된 Application 실행 |
| 주요 정의 | Base Image, Package, Source Code, 실행 명령 | Service, Port, Volume, 환경 변수, Network |
| 주요 명령 | `docker build` | `docker compose up` |
| 결과 | Docker Image | 실행 중인 Application Stack |

Web Frontend, Backend API와 Database가 있다면 구성 요소마다 Dockerfile을 작성할 수 있다. Compose File은 이렇게 만든 Image와 외부 Image를 조합하여 전체 Application의 실행 관계를 정의한다.

Compose로 실행한 Container도 각자 독립된 기능을 담당한다. 같은 Compose Project의 Service는 기본 Network에 연결되므로 IP 주소 대신 Service 이름으로 서로 통신할 수 있다.

Docker Compose는 개발, 테스트, CI와 운영 환경에서 사용할 수 있다. 다만 여러 Host에 걸친 자동 확장, 장애 복구와 Cluster Scheduling 같은 기능을 제공하는 Orchestrator와 역할이 같지는 않다. 그러한 운영 기능이 필요하면 Docker Swarm이나 Kubernetes 같은 별도의 Orchestration Platform을 검토한다.

## 3 ) Docker Compose 설치

---

Docker Desktop에는 Docker Compose가 포함되므로 Windows, macOS와 Docker Desktop을 사용하는 Linux에서는 별도로 설치할 필요가 없다.

Docker Engine과 Docker CLI만 설치된 Linux에서는 Docker의 Package Repository를 설정한 뒤 Compose Plugin을 설치한다.

```bash
sudo apt-get update
sudo apt-get install -y docker-compose-plugin
docker compose version
```

현재 권장 방식은 Docker CLI Plugin과 공백을 사용한 `docker compose` 명령이다.

```bash
docker compose up -d
docker compose ps
docker compose down
```

강의에서 사용한 `docker-compose` 명령과 `/usr/local/bin/docker-compose`에 실행 File을 직접 설치하는 방식은 Standalone Compose 방식이다. 현재는 하위 호환을 위해 제공되는 Legacy 설치 방식이므로 이 문서의 실행 예제에서는 Compose Plugin을 사용한다.

## 4 ) Compose File 구조

---

Compose File의 기본 이름으로 `compose.yaml` 또는 `docker-compose.yaml`을 사용할 수 있다.

```yaml
services:
  web:
    image: httpd
    ports:
      - "8080:80"
```

주요 항목은 다음과 같다.

| 항목 | 역할 |
|---|---|
| `services` | Application을 구성하는 Service 정의 |
| `image` | Container 생성에 사용할 Image |
| `build` | Dockerfile을 이용해 Image를 Build할 경로와 Option |
| `ports` | `HOST_PORT:CONTAINER_PORT` 형식의 Port 연결 |
| `volumes` | Service의 영속 데이터와 Host File 연결 |
| `environment` | Container에 전달할 환경 변수 |
| `restart` | Container 종료 후 재시작 정책 |

과거 Compose File에서는 `version: "3"` 또는 `version: "3.8"`처럼 File 형식 Version을 작성했다.

```yaml
version: "3.8"

services:
  web:
    image: httpd
```

최상위 `version` 속성은 현재 Compose Specification에서 호환을 위해 남아 있는 Obsolete 항목이다. Compose는 이 값과 관계없이 현재 Specification으로 File을 검증하므로 새로운 Compose File에서는 생략한다.

## 5 ) Apache Service

---

### `docker container run`으로 실행

Apache HTTP Server Container 하나를 직접 실행한다.

```bash
docker container run \
  --name apache_1 \
  -d \
  -p 8080:80 \
  httpd
```

### Compose File로 실행

동일한 설정을 `compose.yaml`에 선언한다. 앞의 Container와 동시에 비교할 수 있도록 Host의 8081번 Port를 사용한다.

```yaml
services:
  apache_1:
    image: httpd
    ports:
      - "8081:80"
    restart: always
```

Compose File이 있는 Directory에서 Service를 실행하고 상태를 확인한다.

```bash
docker compose up -d
docker compose ps
curl http://localhost:8081
```

`docker container run`의 `--name`, `-p`, `--restart` Option이 Compose File의 Service 이름, `ports`, `restart` 항목에 대응한다.

## 6 ) MariaDB Service

---

### `docker container run`으로 실행

강의에서는 다음 명령으로 MariaDB 10.4.6 Container를 실행했다.

```bash
docker container run \
  --name mariadb-server \
  -d \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -v ~/mariadb/data:/var/lib/mysql \
  --restart always \
  mariadb:10.4.6
```

MariaDB 10.4 계열은 유지 관리가 종료된 Legacy Version이다. 명령의 Option 대응 관계를 이해하기 위한 강의 예제로 보존하며, 새 환경의 실행 예제에는 지원 중인 10.11 계열을 사용한다.

### Compose File로 실행

```yaml
services:
  mariadb:
    image: mariadb:10.11
    container_name: mariadb-server
    restart: always
    ports:
      - "3307:3306"
    volumes:
      - ./data:/var/lib/mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${MARIADB_ROOT_PASSWORD}
```

Compose File과 같은 Directory에 `.env`를 만들고 실습용 비밀번호를 지정한다.

```dotenv
MARIADB_ROOT_PASSWORD=your_password
```

`.env`에는 비밀번호가 포함되므로 Version Control에 Commit하지 않는다.

```text
.env
```

Service를 실행하고 상태를 확인한다.

```bash
docker compose up -d
docker compose ps
```

두 실행 방식의 Option은 다음과 같이 대응한다.

| `docker container run` | Compose File | 역할 |
|---|---|---|
| `--name mariadb-server` | `container_name` | Container 이름 |
| `-p 3306:3306` | `ports` | Host와 Container Port 연결 |
| `-v PATH:/var/lib/mysql` | `volumes` | Database 데이터 영속화 |
| `-e MYSQL_ROOT_PASSWORD=...` | `environment` | 초기 Root 비밀번호 전달 |
| `--restart always` | `restart: always` | Container 재시작 정책 |

`~/mariadb/data`는 사용자의 Home Directory를 기준으로 하고 `./data`는 Compose File이 있는 Project Directory를 기준으로 한다. 상대 경로를 사용하면 Project File과 Database 데이터를 같은 Directory 구조 안에서 관리하기 쉽다.

## 7 ) Compose Network

---

Compose는 별도의 Network를 지정하지 않아도 Project 전용 기본 Network를 생성한다.

```bash
docker network ls
```

같은 Compose Network에 연결된 Service는 Container IP가 아니라 Service 이름으로 통신할 수 있다. 예를 들어 Backend Service에서 MariaDB에 접속할 때 Host를 `localhost`로 지정하지 않고 `mariadb`로 지정한다.

```text
Host: mariadb
Port: 3306
```

Container 내부에서 `localhost`는 해당 Container 자신을 가리킨다. Host에 공개한 3307번 Port는 Host에서 MariaDB에 접속할 때 사용하고, Compose Network 안의 다른 Container는 `mariadb:3306`으로 접속한다.

## 8 ) Compose 생명주기 관리

---

주요 명령은 다음과 같다.

| 명령 | 역할 |
|---|---|
| `docker compose up -d` | Service 생성 및 Background 실행 |
| `docker compose ps` | Project의 Container 상태 확인 |
| `docker compose logs` | Service Log 확인 |
| `docker compose stop` | Container를 삭제하지 않고 중지 |
| `docker compose start` | 중지한 Container 시작 |
| `docker compose down` | Container와 기본 Network 중지 및 삭제 |

```bash
docker compose logs apache_1
docker compose stop
docker compose start
docker compose down
```

`docker compose down`은 기본적으로 Container와 Compose가 만든 Network를 삭제한다. 위 MariaDB 예제의 `./data`는 Host Bind Mount이므로 Container를 삭제해도 Host Directory의 데이터는 유지된다.

> **최종 정리**
>
> - Dockerfile은 하나의 Image를 만들고 Docker Compose는 여러 Container로 구성된 Application을 실행한다.
>
> - Compose File에는 Service별 Image, Port, Volume, 환경 변수와 재시작 정책을 YAML로 선언한다.
>
> - 현재는 Standalone `docker-compose`보다 Docker CLI Plugin의 `docker compose` 명령을 사용한다.
>
> - 최상위 `version` 속성은 현재 Obsolete이므로 새로운 Compose File에서는 생략한다.
>
> - 같은 Compose Project의 Service는 기본 Network에서 Service 이름으로 통신한다.
>
> - `docker compose up`으로 Stack을 생성하고 `docker compose down`으로 Container와 기본 Network를 정리한다.
