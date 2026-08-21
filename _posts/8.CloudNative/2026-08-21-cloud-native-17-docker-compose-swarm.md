---
title: Docker Compose 응용과 Docker Swarm
description: 다중 Container 실습, Nginx Load Balancing, 환경 변수 관리와 Docker Swarm의 핵심 구조
date: 2026-08-21
series: CloudNative
tags:
  - Cloud
  - AutoEverSW
---
이전 글에서는 Docker Compose의 역할과 기본 File 구조를 살펴보았다. 이번 글에서는 여러 Service를 실제로 연결하고 확장하는 방법부터 Nginx Load Balancing, 환경 변수 관리와 Docker Swarm까지 다룬다.

Docker Compose는 주로 단일 Host에서 여러 Container로 구성된 Application을 관리한다. 여러 Host를 하나의 Cluster로 묶어 Service를 배치하고 원하는 상태를 유지해야 한다면 Docker Swarm이나 Kubernetes 같은 Container Orchestration 도구가 필요하다.

## 1 ) Compose File 작성

---

### File 이름과 최상위 항목

Compose File은 다음 이름을 사용할 수 있다.

- `compose.yaml`

- `compose.yml`

- `docker-compose.yaml`

- `docker-compose.yml`

현재는 `compose.yaml`이 선호되며 `docker-compose.yaml`도 호환을 위해 사용할 수 있다.

Python 기반 Compose V1에서 사용하던 **Legacy 명령**은 현재 호환 목적으로만 남은 Obsolete 항목이므로, 현재는 Docker CLI Plugin 형태의 `docker compose`를 사용하며

Compose File의 주요 최상위 항목은 다음과 같다.

| 항목         | 역할                           |
| ---------- | ---------------------------- |
| `services` | 실행할 Container Service 정의     |
| `networks` | Service가 사용할 Network 정의      |
| `volumes`  | Service가 사용할 Named Volume 정의 |
| `configs`  | 일반 설정 정보 정의                  |
| `secrets`  | 민감한 정보 정의                    |


`services` 아래에는 함께 실행할 Container를 Service 단위로 작성한다. Service별 주요 항목은 다음과 같다.

| 항목 | 역할 |
|---|---|
| `image` | Registry에서 가져오거나 이미 Build한 Image 지정 |
| `build` | Dockerfile과 Build Context 지정 |
| `container_name` | 생성할 Container 이름 지정 |
| `ports` | Host Port와 Container Port 연결 |
| `expose` | 다른 Service에 Container Port 정보 제공 |
| `networks` | 연결할 Network 선택 |
| `volumes` | Named Volume 또는 Bind Mount 연결 |
| `environment` | Container 환경 변수 설정 |
| `command` | Image의 기본 실행 명령을 덮어쓸 명령 지정 |
| `restart` | Container 종료 후 재시작 정책 지정 |
| `depends_on` | Service 사이의 생성 및 종료 순서 지정 |

`restart`에는 `no`, `always`, `on-failure`, `unless-stopped` 등을 사용할 수 있다. YAML에서 `no`가 Boolean으로 해석될 수 있으므로 문자열인 `"no"`로 작성하는 편이 안전하다.

Docker Hub 등의 Registry에 있는 Image는 `image`로 지정한다.

```yaml
services:
  myweb:
    image: nginx
  mydb:
    image: mariadb
```

직접 개발한 Application은 Dockerfile이 있는 현재 Directory를 Build Context로 지정할 수 있다.

```yaml
services:
  myweb:
    build: .
```

Build Context와 Dockerfile 위치를 구분하려면 `build` 아래에 `context`와 `dockerfile`을 작성한다.

```yaml
services:
  myweb:
    build:
      context: .
      dockerfile: docker/Dockerfile
```

`depends_on`은 의존 Service를 먼저 생성하지만 해당 Application이 요청을 처리할 준비까지 마쳤음을 보장하지는 않는다. 준비 상태까지 기다려야 한다면 의존 Service에 `healthcheck`를 정의하고 `condition: service_healthy`를 사용한다.

### Network 정의

`networks`를 생략하면 Compose가 Project 전용 기본 Network를 자동 생성한다. 같은 Network의 Service는 IP Address를 직접 확인하지 않고 Service 이름으로 통신할 수 있다.

여러 Network를 분리하려면 최상위에서 Network를 정의하고 Service별로 연결한다.

```yaml
services:
  myweb:
    image: nginx
    networks:
      - frontend-net
  mydb:
    image: mariadb
    networks:
      - backend-net

networks:
  frontend-net: {}
  backend-net: {}
```

이미 만들어 둔 Network를 사용하려면 `external: true`와 실제 이름을 지정한다.

```yaml
networks:
  default:
    external: true
    name: myapp-net
```

### Volume 정의

데이터를 Container 수명과 분리하려면 최상위에서 Named Volume을 정의하고 Service의 내부 Directory에 Mount한다.

```yaml
services:
  mydb:
    image: mysql:8.0
    volumes:
      - mydb-data:/var/lib/mysql

volumes:
  mydb-data: {}
```

Named Volume의 실제 데이터는 Docker가 관리한다. Linux의 기본 Rootless가 아닌 구성에서는 일반적으로 `/var/lib/docker/volumes` 아래에 배치되지만, Storage Driver나 실행 방식에 따라 위치가 달라질 수 있으므로 직접 경로를 조작하지 않는다.

## 2 ) MySQL과 WordPress 실행

---

MySQL 8.0과 WordPress 5.7로 구성한 Web Application을 각각의 `docker run` 명령과 Compose File로 실행해 본다. 여기서 사용하는 Image Version과 비밀번호는 강의 실습을 재현하기 위한 값이므로 실제 운영 환경에서는 지원 중인 Image와 안전한 Secret 관리 방식을 선택해야 한다.

### `docker run`으로 실행

먼저 Database 데이터를 저장할 Volume과 두 Container가 함께 사용할 Network를 만든다.

```bash
docker volume create mydb_data
docker network create myapp_net
```

MySQL Container를 실행한다.

```bash
docker run -dit \
  --name mysql_app \
  -v mydb_data:/var/lib/mysql \
  --restart=always \
  -p 3306:3306 \
  --network myapp_net \
  -e MYSQL_DATABASE=adam \
  -e MYSQL_USER=adam \
  -e MYSQL_PASSWORD=wnddkd \
  -e MYSQL_ROOT_PASSWORD=wnddkd \
  mysql:8.0
```

WordPress Container를 같은 Network에 연결하여 실행한다.

```bash
docker run -dit \
  --name wordpress_app \
  -v myweb_data:/var/www/html \
  -v "${PWD}/myweb-log:/var/log" \
  --restart=always \
  -p 8888:80 \
  --network myapp_net \
  -e WORDPRESS_DB_HOST=mysql_app:3306 \
  -e WORDPRESS_DB_NAME=adam \
  -e WORDPRESS_DB_USER=adam \
  -e WORDPRESS_DB_PASSWORD=wnddkd \
  wordpress:5.7
```

같은 사용자 정의 Network에서는 `mysql_app`이라는 Container 이름으로 MySQL에 접근할 수 있다. 과거에는 `--link mysql_app:mysql` Option을 사용하기도 했지만 `--link`는 **Legacy 기능**이므로 사용자 정의 Network와 DNS 기반 이름 조회를 사용한다.

### Docker Compose로 실행

같은 구성을 `compose.yaml` 하나로 표현하면 다음과 같다.

```yaml
services:
  mydb:
    image: mysql:8.0
    container_name: mysql_app
    volumes:
      - mydb_data:/var/lib/mysql
    restart: always
    ports:
      - "3306:3306"
    networks:
      - backend-net
    environment:
      MYSQL_ROOT_PASSWORD: wnddkd
      MYSQL_DATABASE: adam
      MYSQL_USER: adam
      MYSQL_PASSWORD: wnddkd

  myweb:
    image: wordpress:5.7
    container_name: wordpress_app
    depends_on:
      - mydb
    ports:
      - "8888:80"
    networks:
      - backend-net
      - frontend-net
    volumes:
      - myweb_data:/var/www/html
      - ${PWD}/myweb-log:/var/log
    restart: always
    environment:
      WORDPRESS_DB_HOST: mydb:3306
      WORDPRESS_DB_NAME: adam
      WORDPRESS_DB_USER: adam
      WORDPRESS_DB_PASSWORD: wnddkd

networks:
  frontend-net: {}
  backend-net: {}

volumes:
  mydb_data: {}
  myweb_data: {}
```

`mydb`는 Backend Network에만 연결하고 `myweb`은 Frontend와 Backend Network에 모두 연결한다. WordPress는 MySQL Container의 IP가 아닌 Service 이름 `mydb`로 접속한다.

```bash
docker compose up -d
docker compose ps
```

> **중간 정리**
>
> - 여러 `docker run` 명령의 Image, Port, Volume, Network와 환경 변수를 하나의 Compose File로 옮길 수 있다.
>
> - 동일한 Compose Network에서는 Service 이름을 DNS 이름으로 사용한다.
>
> - `depends_on`은 실행 순서를 정의하지만 준비 완료를 보장하지 않는다.

## 3 ) Flask와 Redis의 Container 통신

---

Flask Application의 Web 접속 횟수를 Redis에 저장하는 예제로 `localhost`와 Container Network의 차이를 확인한다.

### Redis만 Container로 실행

Redis Container를 실행한다.

```bash
docker run --name myredis -d -p 6379:6379 redis
```

Host에서 Redis Server가 이미 실행 중이어서 Port가 충돌한다면 실습 전에 기존 Service를 중지한다.

```bash
sudo systemctl stop redis-server
```

Python 가상 환경을 만들고 필요한 Package를 설치한다.

```bash
python3 -m venv ./myvenv
source myvenv/bin/activate
pip install flask redis
pip freeze > requirements.txt
```

`app.py`를 작성한다.

```python
import redis
from flask import Flask

app = Flask(__name__)


def web_hit_cnt():
    with redis.Redis(host="localhost", port=6379) as conn:
        return conn.incr("hits")


@app.route("/")
def hello():
    count = web_hit_cnt()
    return f"<h1>Web Access Count: {count}</h1>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000, debug=True)
```

Host에서 Application을 실행하면 Host의 `6379` Port를 통해 Redis Container에 접근한다.

```bash
python app.py
```

### Flask도 Container로 실행

Flask Application을 Image로 Build하기 위해 `Dockerfile`을 작성한다.

```dockerfile
FROM python:3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]
```

Image를 Build하고 Container를 실행한다.

```bash
docker build -t flaskapp .
docker run -dit -p 9000:9000 --name flaskapp flaskapp
```

이 상태에서 Web Page를 호출하면 Redis 연결에 실패한다. Container 안의 `localhost`와 `127.0.0.1`은 Host나 다른 Container가 아니라 **현재 Flask Container 자신**을 가리키기 때문이다.

다음 명령으로 기본 Bridge Network와 Redis Container의 IP Address를 확인할 수 있다.

```bash
docker network inspect bridge
docker inspect myredis
```

확인한 IP Address를 `app.py`에 직접 작성하면 임시로 연결할 수 있지만 Container를 다시 만들 때 IP가 바뀔 수 있다. 지속적으로 사용할 구성에서는 두 Container를 같은 사용자 정의 Network에 연결하고 이름으로 통신하거나 Compose를 사용한다.

### Docker Compose에서 Service 이름으로 통신

`app.py`에서 Redis 접속 Host를 Compose Service 이름인 `redis`로 변경한다.

```python
import redis
from flask import Flask

app = Flask(__name__)


def web_hit_cnt():
    with redis.Redis(host="redis", port=6379) as conn:
        return conn.incr("hits")


@app.route("/")
def hello():
    count = web_hit_cnt()
    return f"<h1>Web Access Count: {count}</h1>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000, debug=True)
```

`compose.yaml`을 작성한다.

```yaml
services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  flask:
    build: .
    ports:
      - "9000:9000"
    depends_on:
      redis:
        condition: service_healthy
    restart: always
```

Application을 실행한다.

```bash
docker compose up -d
```

Dockerfile만 사용하면 Image Build와 Container 실행 명령을 각각 수행해야 한다. Compose의 `build`를 사용하면 필요한 Image Build와 여러 Service 실행을 `docker compose up`으로 함께 처리할 수 있다.

## 4 ) Compose 명령과 Scale 조정

---

주요 Compose 명령은 다음과 같다.

| 명령 | 역할 |
|---|---|
| `build` | Dockerfile을 이용해 Service Image Build |
| `config` | Compose File 해석 및 검증 결과 출력 |
| `create` | Service Container 생성 |
| `up` | Service 생성 및 실행 |
| `down` | Project의 Container와 Network 중지 후 삭제 |
| `events` | Container Event 실시간 수신 |
| `exec` | 실행 중인 Service Container에서 명령 실행 |
| `images` | Service가 사용하는 Image 출력 |
| `kill` | Service Container 강제 종료 |
| `logs` | Service Log 출력 |
| `pause`, `unpause` | Service Container 일시 정지 및 재개 |
| `port` | 공개 Port 확인 |
| `ps` | Service Container 상태 출력 |
| `pull`, `push` | Service Image 가져오기 및 배포 |
| `restart`, `start`, `stop` | Service Container 재시작·시작·중지 |
| `rm` | 중지된 Service Container 삭제 |
| `run` | 특정 Service 설정으로 일회성 명령 실행 |
| `top` | 실행 중인 Process 출력 |
| `version` | Compose Version 출력 |

과거 Compose V1에는 `scale` 하위 명령이 있었지만 현재는 `docker compose up --scale`을 사용한다.

```yaml
services:
  server_web:
    image: httpd:2
  server_db:
    image: redis
```

기본 구성을 실행하고 확인한 뒤 종료한다.

```bash
docker compose up -d
docker compose ps
docker compose down
```

각 Service의 Replica 수를 3개로 조정하여 실행한다.

```bash
docker compose up \
  --scale server_db=3 \
  --scale server_web=3 \
  -d
```

Scale 대상 Service에 `container_name`을 지정하면 Container 이름이 중복되므로 Replica를 여러 개 만들 수 없다. Host의 고정 Port도 각 Replica가 동시에 사용할 수 없으므로 Scale 구성에서는 Port 충돌을 함께 고려해야 한다.

Project를 삭제할 때 사용할 수 있는 주요 Option은 다음과 같다.

```bash
docker compose [-f FILE] down [OPTIONS]
```

| Option | 역할 |
|---|---|
| `--rmi all` | Service가 사용하는 모든 Image 삭제 |
| `--rmi local` | Custom Tag가 없는 Image만 삭제 |
| `-v`, `--volumes` | Compose File에 선언한 Named Volume과 Anonymous Volume 삭제 |
| `--remove-orphans` | 현재 Compose File에 정의되지 않은 Project Container도 삭제 |

Volume 삭제는 영속 데이터를 제거할 수 있으므로 대상 데이터를 확인한 뒤 실행한다.

## 5 ) Load Balancer

---

Load Balancer는 Client와 Server Pool 사이에서 요청을 여러 Server로 분산하는 장치 또는 기술이다. 한 Server에 부하가 집중되는 것을 방지하여 Resource 활용도와 처리량을 높이고 지연 시간을 줄이며, Health Check와 결합하면 장애가 발생한 Server를 대상에서 제외할 수 있다.

Docker 환경에서도 HAProxy, Nginx, Apache HTTP Server 같은 외부 Service를 Container와 결합하여 Load Balancing을 구성할 수 있다.

### Load Balancing Algorithm

| Algorithm | 동작 |
|---|---|
| Round Robin | 요청을 Server에 순서대로 분배하며 Weight 적용 가능 |
| Least Connections | 현재 연결 수가 가장 적은 Server에 요청 전달 |
| IP Hash | Client IP의 Hash로 Server를 선택하여 같은 IP의 경로 유지 |
| Generic Hash | URI 등 사용자가 정한 Key로 Server 선택 |
| Least Time | 응답 시간과 연결 수를 고려하여 Server 선택 |
| Random | Server를 무작위로 선택 |

IP Hash는 같은 Client를 같은 Server로 보내는 데 유용하지만 Server 장애나 구성 변경 시 경로가 달라질 수 있고 균등 분배를 항상 보장하지 않는다.

`least_time`은 측정 기준에 따라 첫 Byte를 받는 시간인 `header`, 전체 응답을 받는 시간인 `last_byte`, 처리 중 요청까지 고려하는 `last_byte inflight` 방식을 사용할 수 있다. 이 지시어는 과거에는 Commercial Subscription에서만 제공되었지만 Nginx `1.31.0`부터 Open Source에서도 사용할 수 있다. Algorithm과 지시어의 지원 범위는 Nginx Version과 Edition에 따라 확인해야 한다.

### Nginx Upstream Parameter

| Parameter | 역할 |
|---|---|
| `weight` | Server 선택 가중치이며 기본값은 1 |
| `max_conns` | Server의 최대 동시 연결 수 제한 |
| `queue` | 즉시 전달할 Server가 없을 때 요청 대기열 설정 |
| `max_fails` | 지정 횟수 이상 실패한 Server를 일정 시간 대상에서 제외 |
| `backup` | Primary Server를 사용할 수 없을 때 요청을 받을 Backup 지정 |
| `down` | 해당 Server를 일시적으로 분배 대상에서 제외 |

원문의 `max_connes`는 Nginx Parameter 이름에 맞게 `max_conns`로 바로잡았다. `queue` 등 일부 기능은 Nginx Plus에서만 제공될 수 있으므로 사용하는 Edition의 공식 문서를 확인해야 한다.

## 6 ) Nginx Container Load Balancing 실습

---

Flask Application 세 개와 Nginx Load Balancer를 Compose로 실행한다.

### Directory 구성

```bash
mkdir alb
cd alb
mkdir nginx_alb pyfla_app1 pyfla_app2 pyfla_app3
```

완성되는 Directory 구조는 다음과 같다.

```text
alb/
├── compose.yaml
├── nginx_alb/
│   ├── Dockerfile
│   └── nginx.conf
├── pyfla_app1/
│   ├── Dockerfile
│   └── pyfla_app.py
├── pyfla_app2/
│   ├── Dockerfile
│   └── pyfla_app.py
└── pyfla_app3/
    ├── Dockerfile
    └── pyfla_app.py
```

### Nginx 구성

`nginx_alb/Dockerfile`을 작성한다.

```dockerfile
FROM nginx

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

`nginx_alb/nginx.conf`에는 세 Flask Service를 Upstream으로 지정한다.

```nginx
upstream web-alb {
    server pyfla_app1:5000;
    server pyfla_app2:5000;
    server pyfla_app3:5000;
}

server {
    listen 80;

    location / {
        proxy_pass http://web-alb;
    }
}
```

원문은 Host Bridge Address인 `172.17.0.1`과 Host에 공개한 `5001`~`5003` Port를 Upstream으로 사용했다. Compose의 같은 Network에서는 Service 이름과 Container Port로 직접 통신할 수 있으므로 변경될 수 있는 Bridge Address에 의존하지 않도록 구성했다.

### Flask Application 구성

`pyfla_app1/pyfla_app.py`를 작성한다.

```python
from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Web Application 1\n"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
```

`pyfla_app1/Dockerfile`을 작성한다.

```dockerfile
FROM python:3

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir flask

ENTRYPOINT ["python3"]
CMD ["pyfla_app.py"]
```

두 File을 나머지 Application Directory에 복사한다.

```bash
cp pyfla_app1/pyfla_app.py pyfla_app2/
cp pyfla_app1/pyfla_app.py pyfla_app3/
cp pyfla_app1/Dockerfile pyfla_app2/
cp pyfla_app1/Dockerfile pyfla_app3/
```

`pyfla_app2/pyfla_app.py`와 `pyfla_app3/pyfla_app.py`의 응답 숫자를 각각 `2`, `3`으로 변경한다.

```bash
nano pyfla_app2/pyfla_app.py
nano pyfla_app3/pyfla_app.py
```

### Compose File과 실행

`alb/compose.yaml`을 작성한다.

```yaml
services:
  pyfla_app1:
    build: ./pyfla_app1

  pyfla_app2:
    build: ./pyfla_app2

  pyfla_app3:
    build: ./pyfla_app3

  nginx:
    build: ./nginx_alb
    ports:
      - "8000:80"
    depends_on:
      - pyfla_app1
      - pyfla_app2
      - pyfla_app3
```

세 Flask Service는 Nginx를 통해 접근하므로 Host Port를 별도로 공개하지 않았다. Stack을 Build하고 Background에서 실행한다.

```bash
docker compose up --build -d
```

`http://localhost:8000`을 반복해서 호출하면 기본 Round Robin 방식으로 세 Application의 응답을 확인할 수 있다.

### Weight 변경

첫 번째 Application에 더 많은 요청을 전달하려면 `nginx.conf`의 Weight를 변경한다.

```nginx
upstream web-alb {
    server pyfla_app1:5000 weight=3;
    server pyfla_app2:5000 weight=1;
    server pyfla_app3:5000 weight=1;
}

server {
    listen 80;

    location / {
        proxy_pass http://web-alb;
    }
}
```

설정을 Image에 반영하려면 Nginx Service를 다시 Build한다.

```bash
docker compose up --build -d nginx
```

## 7 ) 환경 변수 삽입 및 관리

---

Container에 환경 변수를 전달하는 방법은 다음과 같다.

- Compose File에 직접 작성한다.

- Shell 환경 변수를 사용한다.

- `.env` 또는 별도의 환경 변수 File을 사용한다.

- Dockerfile의 `ENV`로 Image에 포함한다.

Compose File에 비밀번호를 직접 작성할 수 있다.

```yaml
services:
  mysql:
    image: mysql:8
    restart: unless-stopped
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: password
```

이 File을 Git Repository에 Commit하면 비밀번호가 노출된다. Shell 환경 변수로 분리하려면 먼저 값을 등록한다.

```bash
export MYSQL_ROOT_PASSWORD=password
```

Compose File에서는 변수 치환 문법을 사용한다.

```yaml
services:
  mysql:
    image: mysql:8
    restart: unless-stopped
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
```

값을 Compose File에서 분리해도 실행 중인 Container의 환경 변수나 Host 설정을 읽을 권한이 있으면 노출될 수 있다. `.env` 같은 File은 Version Control에서 제외하고 접근 권한을 관리해야 한다. 보안을 더 강화해야 하는 환경에서는 Docker Secret이나 HashiCorp Vault 같은 Secret 관리 방식을 사용한다.

## 8 ) Docker Swarm

---

Docker Swarm Mode는 여러 Docker Host를 하나의 Cluster로 묶어 Service를 배포하고 관리하는 Docker Engine 내장 Orchestration 기능이다. Orchestration 도구가 없다면 여러 Host 중 어디에 Container를 배치할지, 서로 다른 Host의 Container를 어떻게 연결할지, 장애가 발생했을 때 어떻게 복구할지를 직접 조정해야 한다.

### 주요 용어

| 용어 | 의미 |
|---|---|
| Docker Compose | 주로 단일 Host에서 여러 Container Application 관리 |
| Swarm | 여러 Docker Engine이 참여하는 Cluster |
| Node | Swarm에 참여한 Docker Host |
| Service | Swarm에서 유지할 Container 실행 상태 정의 |
| Task | Node에 배치되는 Service의 실행 단위 |
| Stack | 여러 Swarm Service로 구성된 전체 Application |

### Node 역할과 분산 설계

Swarm Node는 Manager와 Worker 역할로 구분한다.

- Manager Node는 Cluster 상태, Service Scheduling과 원하는 상태 유지를 담당한다.

- 여러 Manager 중 하나가 Raft 합의의 Leader가 되어 관리 명령을 조정한다.

- Worker Node는 Manager가 할당한 Task를 실행한다.

Manager Node도 기본적으로 Task를 실행할 수 있다. 관리 부하와 Application 부하를 분리하려면 Service에 다음 Placement Constraint를 지정한다.

```bash
docker service create \
  --name my-service \
  --constraint 'node.role!=manager' \
  nginx
```

Kubernetes의 Control Plane Node도 일반적으로 Taint를 통해 일반 Workload 배치를 막지만, 설정에 따라 Workload를 실행할 수 있다. 따라서 “Kubernetes Master는 Container Service를 절대로 실행하지 않는다”라고 구분하기보다 기본 Scheduling 정책과 역할 분리 관점에서 이해해야 한다.

### Service 확장과 원하는 상태

Replica 수를 지정하면 Swarm Manager가 그 수만큼 Task를 유지한다.

```bash
docker service create --name web --replicas 3 nginx
```

실행 중인 Task에 장애가 발생하여 실제 상태가 사용자가 요청한 상태와 달라지면 Manager는 대체 Task를 생성한다. 이처럼 선언한 상태와 실제 상태가 일치하도록 지속적으로 조정하는 것을 **Desired State Management**라고 한다.

### Service Scheduling

Manager는 Node의 가용성, Resource와 Placement 조건을 확인하여 Task를 배치한다. 원문의 `swarm manage --strategy`와 `spread`, `binpack`, `random` Option은 별도 Classic Swarm 시기의 방식으로 현재 Docker Engine의 Swarm Mode 명령이 아니다.

현재 Swarm Mode에서는 다음 기능으로 배치를 제어한다.

- `--constraint`로 Task가 배치될 수 있는 Node를 제한한다.

- `--placement-pref 'spread=...'`로 Label 값을 기준으로 Replica를 분산한다.

- CPU와 Memory 제한 또는 예약으로 Resource 조건을 설정한다.

Placement Preference는 강제 조건이 아니며 현재는 `spread`만 지원한다. 엄격한 배치 조건이 필요하면 Constraint를 함께 사용한다.

### Ingress Network와 Routing Mesh

Swarm을 초기화하거나 참여하면 Service Load Balancing을 위한 특별한 Overlay Network인 `ingress`가 생성된다. Service의 Port를 공개하면 모든 Swarm Node가 Routing Mesh에 참여한다.

```bash
docker service create \
  --name web \
  --replicas 1 \
  --publish published=8080,target=80 \
  nginx
```

위 Service의 Task가 Worker Node 1에만 배치되어 있어도 Worker Node 2의 `8080` Port로 들어온 요청을 실행 중인 Task로 전달할 수 있다. Client는 실제 Task가 어느 Node에 있는지 알 필요가 없다.

Published Port를 생략하면 Swarm이 사용 가능한 높은 번호의 Port를 할당한다. 과거 문서에서는 자동 할당 범위를 `30000`~`32767`로 설명하며, 현재 Docker 문서의 핵심 개념에도 이 범위가 안내되어 있다. 다만 실제 배포에서는 자동 할당 결과를 `docker service inspect`로 확인해야 한다.

Routing Mesh를 사용하려면 Node 사이에 다음 Port가 열려 있어야 한다.

| Port | Protocol | 역할 |
|---|---|---|
| `7946` | TCP/UDP | Container Network Discovery |
| `4789` | UDP | Ingress Network Traffic |

Cluster 관리에는 별도로 Manager 통신용 TCP `2377`도 필요하다. 외부 Load Balancer나 Client가 Service에 접근한다면 공개한 Service Port도 허용해야 한다.

### Service Discovery

Swarm은 내장 DNS를 통해 Service Discovery를 제공한다. 같은 Overlay Network의 Service는 각 Task의 IP를 직접 관리하지 않고 Service 이름으로 접근할 수 있으며, Swarm이 요청을 실행 중인 Task로 분산한다.

### Rolling Update와 Rollback

Swarm Service는 Replica를 단계적으로 교체하는 Rolling Update를 지원한다.

```bash
docker service update \
  --image nginx:stable \
  --update-parallelism 1 \
  --update-order start-first \
  --update-failure-action rollback \
  web
```

- `--update-parallelism`은 한 번에 Update할 Task 수를 정한다.

- 기본 Update 순서는 기존 Task를 먼저 중지하는 `stop-first`이다. 새 Task를 먼저 실행하려면 `start-first`를 지정한다.

- Update 실패 시 기본 동작은 일시 중지이며, 자동 복구가 필요하면 `--update-failure-action rollback`을 명시한다.

따라서 “항상 새 Container를 먼저 만들며 실패하면 자동 Rollback한다”는 동작은 기본값이 아니라 Service Update 정책으로 구성해야 하는 동작이다.

## 9 ) Docker Swarm과 Kubernetes

---

두 도구 모두 여러 Node에 Container Workload를 배치하고 원하는 상태를 유지하지만 적용 환경과 기능 범위가 다르다.

| 기준 | Docker Swarm | Kubernetes |
|---|---|---|
| 구성 | Docker Engine에 내장되어 비교적 단순 | 별도의 Cluster 구성 요소와 Resource Model 사용 |
| 학습 곡선 | Docker를 익혔다면 시작하기 쉬움 | 개념과 구성 요소가 더 많음 |
| 생태계와 확장성 | 기본 Orchestration 기능 중심 | Network, Storage, Policy와 확장 생태계가 큼 |
| Cloud 연동 | Cluster를 직접 구성하는 형태가 일반적 | 주요 Cloud에서 Managed Kubernetes 제공 |
| 적합한 경우 | 단순한 Docker 기반 Cluster와 학습 | 복잡한 운영 요구와 Cloud Native Platform |

Docker Compose에서 익힌 Service와 Network 개념은 Swarm으로 이어지며, Swarm의 Desired State, Scheduling, Service Discovery, Rolling Update와 Ingress는 Kubernetes를 학습할 때도 연결되는 핵심 개념이다.

## 전체 정리

---

> **최종 정리**
>
> - Compose File의 `services`, `networks`, `volumes`로 여러 Container Application을 선언한다.
>
> - 같은 Network의 Container는 변경될 수 있는 IP 대신 Service 이름으로 통신한다.
>
> - Nginx Upstream과 Compose Service를 결합하여 여러 Flask Application에 요청을 분산할 수 있다.
>
> - 환경 변수를 File 밖으로 분리해도 자동으로 안전해지는 것은 아니므로 접근 권한과 Secret 관리 방식을 함께 고려한다.
>
> - Docker Swarm은 여러 Docker Host에서 Desired State, Scheduling, Service Discovery, Rolling Update와 Ingress Routing Mesh를 제공한다.
