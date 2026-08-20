---
title: 애플리케이션별 Docker Multi-stage Build
description: Node.js, Spring Boot, Go, Python, React 애플리케이션의 Multi-stage Image Build 방법
date: 2026-08-20
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
---
## 1 ) 애플리케이션과 Multi-stage Build

---

애플리케이션의 언어와 Framework가 달라도 Multi-stage Build의 기본 흐름은 같다.

1. Builder Stage에서 의존성을 설치한다.

2. Source Code를 Build하거나 실행에 필요한 환경을 준비한다.

3. Runtime Stage를 별도의 Base Image로 시작한다.

4. Builder Stage에서 만든 산출물만 Runtime Stage로 복사한다.

5. 최종 Image에서 Application을 실행한다.

언어별 차이는 최종 산출물과 실행 환경에 있다.

| 애플리케이션 | Builder Stage의 작업 | Runtime Stage로 전달하는 대상 | Runtime |
|---|---|---|---|
| Node.js | Package 설치 | Source Code와 설치된 Package | Node.js |
| Spring Boot | Gradle Build | JAR | JRE |
| Go | Source Code Compile | 실행 Binary | Alpine Linux |
| Python | 가상 환경에 Package 설치 | Python 가상 환경 | Python |
| React | 정적 File Build | `dist` Directory | Nginx |

Spring Boot, Go, React는 Build 산출물이 명확하므로 Builder의 Build 도구를 최종 Image에서 제외하기 쉽다. Node.js와 Python은 Source Code를 Runtime에서 실행하므로 의존성 설치 결과를 별도 Stage로 전달한다.

## 2 ) Node.js Multi-stage Build

---

Node.js 예제는 Builder Stage에서 Package를 설치하고 Runtime Stage에서는 더 작은 Alpine 기반 Node.js Image로 Application을 실행한다.

```dockerfile
FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app ./

EXPOSE 3000

USER node

CMD ["node", "app.js"]
```

Build 과정은 다음과 같다.

1. `node:20-slim`에서 `package.json`을 먼저 복사하고 Package를 설치한다.

2. Source Code를 `/app`에 복사한다.

3. `node:20-alpine`으로 Runtime Stage를 시작한다.

4. Builder의 `/app`을 Runtime Stage로 복사한다.

5. `node` 사용자로 `app.js`를 실행한다.

```bash
docker build -t nodeapp:2.0 .
```

이 예제는 Builder의 Application Directory 전체를 복사하므로 Source Code와 `node_modules`가 모두 Runtime Stage로 전달된다. 두 Stage를 분리하는 흐름과 더 작은 Runtime Base Image를 사용하는 방법을 보여주는 예제이다.

## 3 ) Spring Boot Gradle Multi-stage Build

---

Spring Boot는 JDK와 Gradle이 필요한 Build 환경과 JAR 실행에 필요한 JRE 환경을 분리한다.

### 프로젝트 준비

```bash
git clone https://github.com/itggangpae/spring_docker.git
cd spring_docker
```

### Dockerfile

```dockerfile
FROM eclipse-temurin:21-jdk AS builder

WORKDIR /app

COPY gradlew ./
COPY gradle ./gradle
RUN chmod +x gradlew

COPY build.gradle ./
COPY settings.gradle ./
RUN ./gradlew dependencies --no-daemon

COPY src ./src
RUN ./gradlew clean build -x test --no-daemon

FROM eclipse-temurin:21-jre

WORKDIR /app

COPY --from=builder /app/build/libs/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

이전 실습에서는 Host에서 Gradle Build를 수행하고 생성된 JAR를 Docker Image에 복사했다. Multi-stage Build에서는 다음 과정이 하나의 Dockerfile 안에서 이루어진다.

1. JDK Image에서 Gradle Wrapper로 JAR를 Build한다.

2. 새로운 JRE Image를 Runtime Stage로 사용한다.

3. Builder에서 생성한 JAR만 Runtime Stage로 복사한다.

4. 최종 Image에는 Gradle, Source Code와 JDK가 남지 않는다.

```bash
docker build -t spring-docker:2.0 .
```

`build.gradle`과 `settings.gradle`을 Source Code보다 먼저 복사하여 의존성 Layer를 분리했다. 의존성 설정이 바뀌지 않았다면 Source Code 변경 시 기존 의존성 Cache를 활용할 수 있다.

## 4 ) Go Multi-stage Build

---

Go는 Builder Stage에서 Source Code를 실행 Binary로 Compile하고 최종 Image에는 Binary만 복사한다.

```dockerfile
FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY go.mod go.sum* ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root

COPY --from=builder /app/main ./main

EXPOSE 8000

CMD ["./main"]
```

각 Stage의 역할은 다음과 같다.

- Builder Stage는 Go Compiler와 Module 의존성을 사용한다.

- `CGO_ENABLED=0`으로 C Library에 대한 동적 의존성을 사용하지 않는 Binary를 Build한다.

- Runtime Stage는 `alpine:latest`를 사용하고 HTTPS 인증에 필요한 CA 인증서를 설치한다.

- 최종 Image에는 Go Compiler와 Source Code 대신 `main` Binary만 포함한다.

```bash
docker build -t goapp:2.0 .
```

## 5 ) Python Multi-stage Build

---

Python은 Compile된 단일 실행 File보다 Source Code와 Package가 설치된 환경이 필요하다. Builder Stage에서 가상 환경을 만들고 Runtime Stage로 해당 가상 환경을 복사한다.

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY . .

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

주요 설정은 다음과 같다.

| 설정 | 역할 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1` | `.pyc` File 생성 방지 |
| `PYTHONUNBUFFERED=1` | 표준 출력과 오류의 Buffering 비활성화 |
| `/opt/venv` | Builder와 Runtime에서 공통으로 사용하는 가상 환경 경로 |
| `appuser` | Application을 실행할 일반 사용자 |

```bash
docker build -t fastapiapp:2.0 .
```

강의에서는 처음에 일반 `python` Image를 사용한 뒤 `python:3.12-slim`으로 변경했다. Python은 Compiler를 완전히 제거하는 방식보다 작은 Base Image를 선택하고 가상 환경만 복사하는 방식으로 최종 Image를 줄인다.

## 6 ) React 정적 File Multi-stage Build

---

React Source Code는 Browser가 직접 실행할 수 있는 정적 HTML, JavaScript와 CSS File로 Build한다. Docker 환경에서는 Nginx나 Apache로 정적 File을 제공할 수 있고, Cloud 환경에서는 Web Endpoint를 제공하는 Object Storage에 배포할 수도 있다.

### 프로젝트 생성과 확인

```bash
npm create vite@latest my-react-app -- --template react
cd my-react-app
npm install
npm run dev -- --host 0.0.0.0
```

```bash
curl http://localhost:5173
```

### Dockerfile

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:stable-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

Builder Stage에서는 Vite가 React Source Code를 `/app/dist`의 정적 File로 변환한다. Runtime Stage에는 Node.js, npm, Source Code를 복사하지 않고 `dist`만 Nginx의 기본 Document Root에 복사한다.

### `.dockerignore`

```text
node_modules/
dist/
.git/
.DS_Store
```

### Image Build와 Container 실행

```bash
docker build -t my-react-app .
docker container run \
  --name my-react-app \
  -d \
  -p 8000:80 \
  my-react-app
```

```bash
curl http://localhost:8000
```

## 7 ) 언어별 차이 비교

---

반복된 실습의 핵심은 Dockerfile의 형태가 아니라 Builder에서 Runtime으로 무엇을 전달하는지에 있다.

| 구분 | Node.js | Spring Boot | Go | Python | React |
|---|---|---|---|---|---|
| 실행 형태 | Source Code | JAR | Native Binary | Source Code | 정적 File |
| Build 도구 | npm | Gradle·JDK | Go Compiler | pip·가상 환경 | npm·Vite |
| Runtime | Node.js | JRE | Alpine | Python | Nginx |
| 전달 대상 | Application Directory | `app.jar` | `main` | `/opt/venv` | `/app/dist` |
| 주요 절감 대상 | Builder Base Image | JDK·Gradle·Source | Compiler·Source | Build Cache | Node.js·Source |

Multi-stage Build가 모든 언어에서 동일한 크기 절감 효과를 만드는 것은 아니다. Compile 결과만 전달할 수 있는 Spring Boot, Go, React에서는 Build 환경과 Runtime 환경의 구분이 명확하다. Node.js와 Python은 Runtime에도 언어 실행 환경과 Package가 필요하므로 필요한 의존성을 선별하고 작은 Base Image를 사용하는 것이 중요하다.

## 8 ) 종합 실습

---

강의의 종합 실습은 Database와 Web Application을 Container로 구성하는 과정이다.

1. MySQL, MariaDB, PostgreSQL, MongoDB, Redis 중 하나를 선택한다.

2. 외부에서 접속할 수 있도록 Database Container를 생성한다.

3. 프로그래밍 언어로 Database에 접속하는 Web Application을 작성한다.

4. Table에 데이터 한 건을 삽입하고 전체 데이터를 조회하는 기능을 구현한다.

5. Web Application을 Multi-stage Build로 Docker Image로 만든다.

6. Image로 Container를 실행하고 외부에서 접속되는지 확인한다.

Kafka를 이용한 CQRS 구현은 별도의 Kafka·CQRS 실습 범위에 해당하므로 이 문서에서는 다루지 않는다.

> **최종 정리**
>
> - Multi-stage Build는 Build 환경과 Runtime 환경을 서로 다른 Stage로 분리한다.
>
> - `COPY --from`으로 Builder에서 생성한 실행 산출물이나 의존성 환경만 Runtime Stage에 전달한다.
>
> - Spring Boot는 JAR, Go는 실행 Binary, React는 정적 File을 최종 Image에 복사한다.
>
> - Node.js와 Python은 Runtime에도 언어 실행 환경과 Package가 필요하다.
>
> - 의존성 File을 Source Code보다 먼저 복사하면 Build Cache를 효율적으로 사용할 수 있다.
>
> - 최종 Stage에서 작은 Base Image와 일반 사용자를 사용하면 Image 크기와 실행 권한을 함께 관리할 수 있다.
