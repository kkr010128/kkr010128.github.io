---
title: Docker Health Check와 Config 및 Secret
description: Container 상태 검사, Compose 의존성 제어와 Swarm Config·Secret 관리 방법
date: 2026-08-24
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
  - DockerSwarm
---
## 1 ) Process 상태와 Application 상태

---

Container는 지정된 주 Process가 실행되는 동안 Running 상태를 유지한다. Process가 종료되면 Container도 종료되므로 기본적인 실행 여부는 Container 상태만으로 확인할 수 있다.

하지만 Process가 실행 중이라고 Application이 정상적으로 요청을 처리한다는 의미는 아니다. Web Application이 처리 용량을 초과하여 `503 Service Unavailable`을 반환하거나 Database 연결이 끊긴 상태에서도 주 Process는 계속 실행될 수 있다.

| 확인 대상 | 확인할 수 있는 상태 | 확인하기 어려운 상태 |
|---|---|---|
| Container Process | Process 실행 및 종료 여부 | Application이 실제 요청을 처리하는지 여부 |
| Health Check | HTTP 응답, Database 접속 등 Application 상태 | 비즈니스 기능 전체의 정상 여부 |

Dockerfile의 `HEALTHCHECK`는 Container 안에서 검사 명령을 주기적으로 실행하여 Process보다 구체적인 Application 상태를 확인한다.

## 2 ) Dockerfile Health Check

---

### Flask Application

`app.py`에 일반 요청과 상태 확인을 위한 Endpoint를 작성한다.

```python
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello Docker"


@app.route("/health")
def health_check():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Dockerfile

```dockerfile
FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app.py ./
RUN pip install --no-cache-dir flask

HEALTHCHECK \
  --interval=10s \
  --timeout=3s \
  --start-period=5s \
  --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["python", "app.py"]
```

Health Check Option은 다음과 같다.

| Option | 역할 |
|---|---|
| `--interval` | 검사 실행 간격 |
| `--timeout` | 한 번의 검사 제한 시간 |
| `--start-period` | Application 시작 후 실패를 유예할 시간 |
| `--retries` | `unhealthy`로 판단하기 전 연속 실패 횟수 |
| `CMD` | 실제 상태를 검사할 명령 |

`curl -f`는 HTTP 응답 Code가 오류이면 실패 상태로 종료하게 되므로, `|| exit 1`로 정리한다.

### Image Build와 상태 확인

```bash
docker build -t my-healthcheck-app .
docker container run \
  --name healthcheck \
  -d \
  my-healthcheck-app
```

```bash
docker container ps
docker container inspect healthcheck
```

`STATUS`에는 Health Check 결과가 다음과 같이 표시된다.

| 상태 | 의미 |
|---|---|
| `starting` | Container가 시작되어 첫 검사 결과를 기다리는 상태 |
| `healthy` | 최근 Health Check가 성공한 상태 |
| `unhealthy` | 설정한 횟수만큼 연속으로 검사에 실패한 상태 |

Health Check 결과는 Load Balancing과 Rolling Update에서 새 Task가 요청을 처리할 준비가 되었는지 판단하는 자료가 된다. Kubernetes에서는 비슷한 목적을 Startup Probe, Readiness Probe와 Liveness Probe로 나누어 설정한다.

## 3 ) Compose Health Check

---

Compose File에서는 Service의 `healthcheck`에 검사 명령과 주기를 정의한다.

```yaml
services:
  web:
    image: my-healthcheck-app
    ports:
      - "8080:8080"
    healthcheck:
      test:
        - CMD
        - curl
        - -f
        - http://localhost:8080/health
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 5s
```

Dockerfile과 Compose File에 Health Check가 모두 있으면 Compose File의 설정이 해당 Service에서 우선한다.

```bash
docker compose up -d
docker compose ps
```

## 4 ) Database 준비 후 Web Service 시작

---

`depends_on`만 지정하면 Compose는 Database Container를 먼저 시작하지만 Database가 Connection을 받을 준비까지 기다리지는 않는다. Database에 Health Check를 추가하고 Web Service에 `condition: service_healthy`를 지정한다.

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    healthcheck:
      test:
        - CMD-SHELL
        - pg_isready -U user -d mydb
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - my-network

  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      DB_HOST: db
    depends_on:
      db:
        condition: service_healthy
    networks:
      - my-network

networks:
  my-network: {}
```

이 설정에서 실행 순서는 다음과 같다.

1. Compose가 `db` Container를 시작한다.

2. `pg_isready`가 PostgreSQL의 준비 상태를 검사한다.

3. `db`가 `healthy`가 되면 `web` Container를 생성한다.

4. Web Application은 `db`라는 Service 이름으로 Database에 접속한다.

Health Check가 성공했더라도 실행 중 Network 장애가 발생할 수 있으므로 Application 자체에도 Connection 재시도와 오류 처리가 필요하다.

## 5 ) Swarm Config

---

Docker Config는 Application 설정과 Image를 분리하기 위한 Swarm Resource이다. Service에 Config를 연결하면 지정한 Target 경로에서 File로 읽을 수 있다.

Config에는 다음과 같은 비민감 설정을 저장한다.

- Web Server 설정

- Application Feature 설정

- 일반적인 Database Client 설정

- 환경별 설정 File

MySQL의 일반 설정 File을 Config로 생성한다.

```ini
[mysqld]
max_connections=200
```

```bash
docker config create \
  mysql_server_config \
  ./mysql.cnf
```

```bash
docker config ls
```

Config를 MySQL Service에 연결한다.

```bash
docker service create \
  --name mysql-server \
  --config source=mysql_server_config,target=/etc/mysql/conf.d/custom.cnf \
  mysql:8.0
```

Config를 변경해야 할 때는 기존 Config 자체를 덮어쓰기보다 새로운 이름으로 생성하고 Service가 참조하는 Config를 교체한다.

## 6 ) Config에 비밀번호를 넣어도 되는가

---

강의에서는 MySQL Root 비밀번호를 Config 객체로 만들어 File 형태로 주입했다. 이어서 비밀번호를 환경 변수로 직접 전달하면 Container 설정이나 `docker inspect`를 통해 노출될 수 있으므로 Secret을 사용할 수 있다고 설명했다. 

두 실습을 비교하면서 일반 설정은 Config로, 비밀번호와 같은 민감 정보는 Secret으로 관리하는 것이 목적에 더 적합하다는 것을 알게 되었다.

Config는 민감하지 않은 설정을 배포하기 위한 Resource이다. 비밀번호, API Token, TLS Private Key처럼 노출되어서는 안 되는 값은 Secret으로 관리해야 한다.

| 구분 | Config | Secret |
|---|---|---|
| 저장 대상 | 일반 설정 | 비밀번호, Token, 인증서 Key |
| Service 전달 | Container의 File로 Mount | 권한을 받은 Task에만 전달 |
| Linux Container의 기본 경로 | 지정한 Target | `/run/secrets/SECRET_NAME` |
| 주요 보호 특성 | 설정과 Image 분리 | Swarm에서 전송 중·저장 시 암호화 |

환경 변수에 비밀번호를 직접 기록하는 방법도 Container 설정과 `docker inspect` 결과 등에 값이 나타날 수 있다. Secret을 지원하는 Image라면 `_FILE` 접미사가 붙은 환경 변수로 Secret File 경로를 전달한다.

## 7 ) Swarm Secret

---

Secret의 기본 흐름은 다음과 같다.

```text
Secret 생성
→ Swarm Secret Store에 저장
→ Service에 Secret 사용 권한 부여
→ Task의 /run/secrets에 File로 Mount
→ Task 종료 시 Mount 제거
```

### Secret 생성

비밀번호 File을 생성하고 Swarm Secret으로 등록한다.

```bash
printf '%s' 'MyStrongPassword123!' > mysql_root_pw.txt
docker secret create \
  mysql_root_password_v1 \
  ./mysql_root_pw.txt
```

```bash
docker secret ls
```

또는 표준 입력으로 값을 전달할 수 있다.

```bash
printf '%s' 'initial_db_password_111' | \
  docker secret create db_password_v1 -
```

Shell History와 Terminal 출력에 Secret을 남길 수 있으므로 실제 환경에서는 Secret 값을 명령행에 직접 작성하지 않는다.

### MySQL Service에 Secret 연결

MySQL 공식 Image는 `MYSQL_ROOT_PASSWORD_FILE`에 지정한 File의 내용을 Root 비밀번호로 읽을 수 있다.

```bash
docker service create \
  --name mysql-server \
  --publish published=3306,target=3306 \
  --secret source=mysql_root_password_v1,target=mysql_root_password \
  --env MYSQL_ROOT_PASSWORD_FILE=/run/secrets/mysql_root_password \
  mysql:8.0
```

Service Task에서는 다음 경로로 Secret을 읽는다.

```text
/run/secrets/mysql_root_password
```

Secret 값은 `docker secret inspect`로 조회되지 않는다. Manager와 사용 권한이 부여된 Service Task만 Secret에 접근하며 Linux Container에서는 Memory File System에 Mount된다.

### Stack File에서 Config와 Secret 사용

```yaml
version: "3.9"

services:
  db:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD_FILE: /run/secrets/db_root_password
      MYSQL_DATABASE: myapp_db
    configs:
      - source: db_config
        target: /etc/mysql/conf.d/custom.cnf
        mode: 0444
    secrets:
      - source: db_root_password
        target: db_root_password
        mode: 0400

configs:
  db_config:
    file: ./mysql.cnf

secrets:
  db_root_password:
    file: ./mysql_root_pw.txt
```

```bash
docker stack deploy \
  --compose-file docker-compose.yaml \
  mysql-app
```

`mysql.cnf`와 비밀번호 File은 용도가 다르므로 Config와 Secret으로 분리한다. 

## 8 ) Secret Version 교체

---

Swarm Secret의 값은 직접 수정할 수 없다. 새 Version의 Secret을 생성한 뒤 Service가 참조하는 Secret을 교체한다.

```bash
docker secret create \
  mysql_root_password_v2 \
  ./mysql_root_pw_v2.txt
```

```bash
docker service update \
  --secret-rm mysql_root_password_v1 \
  --secret-add source=mysql_root_password_v2,target=mysql_root_password \
  mysql-server
```

기존 Secret을 사용하는 Service가 없다면 삭제한다.

```bash
docker secret rm mysql_root_password_v1
```

Secret 이름에 Version을 포함하면 새 값으로 교체하고 이전 값을 제거하는 과정을 구분하기 쉽다.

> **최종 정리**
>
> - Container Process가 실행 중이어도 Application은 요청을 처리하지 못할 수 있으므로 별도의 Health Check가 필요하다.
>
> - Dockerfile과 Compose의 Health Check는 HTTP 요청이나 Database 접속처럼 실제 Application 상태를 검사한다.
>
> - `depends_on`과 `condition: service_healthy`를 함께 사용하면 의존 Service가 준비된 뒤 다음 Service를 시작할 수 있다.
>
> - Config는 일반 설정을 Image와 분리하고 Secret은 비밀번호와 Token 같은 민감 정보를 보호한다.
>
> - 환경 변수에 비밀번호를 직접 넣으면 Container 설정에서 노출될 수 있으므로 `_FILE` 환경 변수와 Secret File을 사용한다.
>
> - Swarm Secret은 권한이 부여된 Service Task의 `/run/secrets`에 Mount되며 새 Version을 생성하는 방식으로 교체한다.
