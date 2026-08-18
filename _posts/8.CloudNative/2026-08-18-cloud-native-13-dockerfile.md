---
title: Dockerfile
description: Dockerfile의 주요 Instruction과 Image Build 방법 및 작성 시 주의 사항
date: 2026-08-18
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
---
## 1 ) Infrastructure as Code, IaC

---

Infrastructure를 CLI로 직접 구성하면 설치 순서, Package의 의존 관계, 환경 설정을 모두 사람이 관리해야 한다. APM(Apache, PHP, MySQL)처럼 여러 Software가 연동되는 환경은 작업 누락과 설정 오류가 발생하기 쉽고, 동일한 환경을 다시 만드는 데에도 많은 시간이 든다.

IaC(Infrastructure as Code)는 Infrastructure의 구성과 절차를 Code로 정의하고 Version을 관리하는 방식이다. Dockerfile 역시 Application 실행 환경과 Image 생성 과정을 Text로 기록하므로 동일한 Image를 반복해서 Build하고 배포할 수 있다.

## 2 ) Dockerfile 개요

---

Dockerfile은 Docker Image를 생성하기 위한 Instruction을 순서대로 작성한 Text File이다.

- Image를 어떤 Base Image와 명령으로 만들었는지 기록할 수 있다.

- 동일한 실행 환경을 반복해서 생성할 수 있다.

- Source Code와 함께 Version을 관리하고 배포할 수 있다.

- Container가 시작될 때 실행할 명령과 기본 설정을 정의할 수 있다.

Dockerfile의 각 Instruction은 Image Layer와 Build Cache에 영향을 준다. 변경 빈도가 낮은 작업을 앞에, Source Code처럼 자주 변경되는 작업을 뒤에 배치하면 Cache를 효율적으로 재사용할 수 있다.

## 3 ) Dockerfile 주요 Instruction

---

### FROM

Build의 기반이 되는 Base Image를 지정한다. 일반적인 Dockerfile은 `FROM`으로 시작하며 Multi-stage Build에서는 여러 번 사용할 수 있다.

```dockerfile
FROM ubuntu:24.04
FROM python:3.13-slim
```

Tag를 생략하면 기본적으로 `latest`가 사용되지만 Build 결과를 예측하기 어려워질 수 있으므로 Version Tag나 Digest를 명시하는 편이 좋다. `slim`이나 `alpine`은 Image 크기를 줄이는 데 도움이 되지만 C Library와 Package 구성이 다르므로 Application 호환성을 먼저 확인한다.

### MAINTAINER

`MAINTAINER`는 Image 작성자 정보를 기록하던 Instruction이다.

```dockerfile
MAINTAINER adam.park <itstudy@example.com>
```

현재 `MAINTAINER`는 사용이 중단된 Deprecated Instruction이다. 새 Dockerfile에서는 OCI Annotation에 해당하는 `LABEL`을 사용한다.

```dockerfile
LABEL org.opencontainers.image.authors="adam.park <itstudy@example.com>"
```

### LABEL

Image의 Version, 설명, License와 같은 Metadata를 Key-Value 형식으로 기록한다. 여러 개를 지정할 수 있다.

```dockerfile
LABEL org.opencontainers.image.version="1.0"
LABEL org.opencontainers.image.description="web service"
LABEL org.opencontainers.image.licenses="MIT"
```

### RUN

Image를 Build하는 동안 Package를 설치하거나 File을 변경하는 명령을 실행한다. Shell 형식과 Exec 형식을 사용할 수 있다.

```dockerfile
# Shell 형식
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      nginx && \
    rm -rf /var/lib/apt/lists/*

# Exec 형식
RUN ["/bin/bash", "-c", "echo build-complete > /build.txt"]
```

각 `RUN`은 Layer를 만들므로 관련 작업은 하나의 `RUN`에서 수행하고 Package 목록도 같은 Layer에서 제거한다. 

`apt autoclean`, `apt autoremove` 명령은 현재도 사용할 수 있지만 Container Image Build에서는 설치 직후 `/var/lib/apt/lists/*`를 제거하고 불필요한 Package를 처음부터 설치하지 않는 방식이 더 명확하다.

Multi-stage Build는 Compiler와 Build 도구가 들어 있는 Stage에서 결과물을 만든 뒤 실행에 필요한 File만 최종 Stage로 복사하여 Image 크기와 공격 표면을 줄이는 방식이다.

### CMD

Container가 시작될 때 실행할 기본 명령 또는 `ENTRYPOINT`의 기본 인자를 지정한다. 여러 번 작성해도 마지막 `CMD`만 적용된다.

```dockerfile
CMD ["nginx", "-g", "daemon off;"]
CMD ["python", "app.py"]
```

Exec 형식은 불필요한 Shell을 거치지 않아 Signal 전달을 예측하기 쉬우므로 일반적으로 권장된다. `docker run IMAGE COMMAND`처럼 Image 뒤에 명령을 전달하면 `CMD`를 대체할 수 있다.

### ENTRYPOINT

Container의 주 실행 명령을 지정한다. `ENTRYPOINT`를 실행 파일로, `CMD`를 기본 인자로 조합할 수 있다.

```dockerfile
ENTRYPOINT ["python"]
CMD ["runapp.py"]
```

이 Image를 인자 없이 실행하면 `python runapp.py`가 실행된다. `docker run IMAGE other.py`로 실행하면 `CMD`만 바뀌어 `python other.py`가 실행된다. `ENTRYPOINT`도 `docker run --entrypoint`로 변경할 수 있으므로 절대 변경할 수 없는 명령이라는 의미는 아니다.

초기화 Script를 사용하는 예시는 다음과 같다.

```dockerfile
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

### COPY

Build Context의 File이나 Directory를 Image에 복사한다. Build Context 밖의 경로는 복사할 수 없다.

```dockerfile
COPY index.html /usr/share/nginx/html/index.html
COPY runapp.py /app/runapp.py
```

단순한 Local File 복사에는 동작이 명확한 `COPY`를 우선 사용한다.

### ADD

`COPY`처럼 File을 복사하며 Local Tar Archive의 자동 압축 해제와 Remote URL 등의 추가 기능을 제공한다.

```dockerfile
ADD application.tar.gz /app/
ADD https://example.com/data.json /app/data.json
```

`ADD`는 현재도 사용되는 Instruction이지만 자동 압축 해제 같은 동작이 필요할 때만 사용한다. Remote File은 `RUN curl` 또는 `RUN wget`으로 내려받으면 검증과 권한 설정 과정을 더 명시적으로 작성할 수 있다.

### ENV

Build 과정과 실행될 Container에서 사용할 환경 변수를 설정한다.

```dockerfile
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"
```

### EXPOSE

Container가 어떤 Port와 Protocol에서 요청을 받을지 문서화한다.

```dockerfile
EXPOSE 80
EXPOSE 8080/tcp
```

`EXPOSE`만으로 Host Port가 공개되지는 않는다. 외부에서 접근하려면 Container 실행 시 `-p HOST_PORT:CONTAINER_PORT` 또는 `-P`를 사용해야 한다.

| 구분 | 역할 | 실제 Listen 여부 | Host 외부 접근 |
|---|---|---|---|
| 애플리케이션 | Nginx, Spring Boot 등이 Container 내부 Port에서 요청을 대기한다. | O | X |
| `EXPOSE 80` | Container가 `80` Port를 사용한다는 것을 명시하는 메타데이터이다. | X | X |
| `-p 8080:80` | Host의 `8080` Port를 Container의 `80` Port에 직접 연결한다. | X | O |
| `-P` | `EXPOSE`로 명시된 Port를 Host의 임의 Port에 자동으로 연결한다. | X | O |

> **중간 정리**
>
> - `EXPOSE`는 Port를 실제로 열거나 Listen 상태로 만드는 명령이 아니다.
>
> - 실제 Listen은 Container 내부의 Application이 수행한다.
>
> - `-p`는 `EXPOSE` 여부와 관계없이 Host와 Container의 Port를 직접 연결한다.
>
> - `-P`는 `EXPOSE`에 명시된 Port를 기준으로 Host의 임의 Port에 연결한다.

### VOLUME

Container에서 Volume으로 사용할 Mount Point를 지정한다.

```dockerfile
VOLUME ["/var/log"]
VOLUME ["/var/www/html"]
```

`VOLUME`은 해당 경로를 Host의 `/var/lib/docker`와 문자 그대로 Bind Mount하는 명령이 아니다. Container 실행 시 Docker가 관리하는 Anonymous Volume의 Mount Point를 선언한다. Volume 이름, Host Bind Mount 경로 등 구체적인 연결은 `docker run --mount`나 Compose File에서 지정하는 편이 관리하기 쉽다.

### USER

이후의 `RUN`과 Container 실행 시 사용할 사용자 또는 Group을 지정한다. 기본 사용자는 `root`이므로 Application에 관리자 권한이 필요하지 않다면 별도 사용자를 만드는 것이 안전하다.

```dockerfile
RUN useradd --create-home appuser
USER appuser
```

### WORKDIR

이후 `RUN`, `CMD`, `ENTRYPOINT`, `COPY`, `ADD`의 기준 Directory를 지정한다. 경로가 없으면 자동으로 생성된다.

```dockerfile
WORKDIR /workspace
COPY . .
```

### ARG

Build할 때만 사용할 변수를 선언하고 `--build-arg`로 값을 전달한다.

```dockerfile
ARG DB_NAME=itstudy
RUN echo "database=${DB_NAME}"
```

```bash
docker build --build-arg DB_NAME=production -t my-app:1.0 .
```

`ARG`는 비밀번호나 Secret을 안전하게 숨기는 기능이 아니다. 값이 Image History나 Build Cache에 남을 수 있으므로 민감 정보를 전달하는 용도로 사용하지 않는다.

### ONBUILD

현재 Image가 다른 Dockerfile의 Base Image로 사용될 때 실행할 Trigger Instruction을 등록한다.

```dockerfile
ONBUILD COPY . /app/src
```

`ONBUILD`는 현재도 지원되지만 상속된 동작이 눈에 잘 드러나지 않아 예상하지 못한 Build 실패를 만들 수 있다. 전용 Base Image처럼 사용 목적이 명확한 경우에 제한적으로 사용한다.

### STOPSIGNAL

Container를 중지할 때 주 Process에 전달할 System Call Signal을 지정한다. 기본값은 일반적으로 `SIGTERM`이다.

```dockerfile
STOPSIGNAL SIGTERM
```

`STOPSIGNAL SIGKILL`도 문법상 지정할 수 있지만 Process가 종료 작업을 수행할 기회를 잃으므로 일반적인 설정으로는 권장하지 않는다.

### SHELL

Shell 형식의 `RUN`, `CMD`, `ENTRYPOINT`에 사용할 기본 Shell을 변경한다.

```dockerfile
SHELL ["/bin/bash", "-c"]
```

### HEALTHCHECK

Container 내부에서 명령을 주기적으로 실행하여 Application의 상태를 확인한다. 여러 번 작성하면 마지막 하나만 적용된다.

```dockerfile
HEALTHCHECK --interval=1m --timeout=3s --retries=5 \
  CMD curl --fail http://localhost/ || exit 1
```

| 종료 Code | 의미 |
|---|---|
| `0` | 정상 상태 |
| `1` | 비정상 상태 |
| `2` | 예약된 값이므로 사용하지 않음 |

기본 `interval`과 `timeout`은 각각 30초이며 기본 `retries`는 3회이다.

## 4 ) Dockerfile 작성 방법

---

Dockerfile은 보통 다음 원칙으로 작성한다.

- 필요한 Application이나 Runtime이 이미 설치된 신뢰할 수 있는 Base Image를 선택한다.

- Version Tag를 명시하여 Build 결과를 일정하게 유지한다.

- 변경 빈도가 낮은 Instruction을 먼저 배치하여 Build Cache를 활용한다.

- Package 설치와 Cache 삭제를 같은 `RUN`에서 처리한다.

- 가능한 경우 권한이 제한된 사용자로 Application을 실행한다.

- Compiler가 필요한 Application은 Multi-stage Build를 고려한다.

## 5 ) Image Build

---

기본 형식은 다음과 같다.

```text
docker build [OPTIONS] PATH | URL | -
```

```bash
# 현재 Directory를 Build Context로 사용하고 이름과 Tag 지정
docker build -t apache-example:1.0 .

# 다른 이름의 Dockerfile 지정
docker build -f Dockerfile.dev -t apache-example:dev .

# Git Repository를 Build Context로 사용
docker build -t php-server:2.0 \
  https://github.com/example/docker-phpserver.git

# 표준 입력으로 전달한 Tar Archive를 Build Context로 사용
docker build - < context.tar.gz
```

`-t`는 Image의 이름과 Tag를 지정하고 `-f`는 Dockerfile의 경로 또는 이름을 지정한다. 마지막 인자인 `PATH`, `URL`, `-`는 Dockerfile 자체가 아니라 Build Context를 뜻한다. 압축된 Build Context는 `-f`가 아니라 표준 입력으로 전달한다.

## 6 ) Apache Main Page Image

---

### index.html

```html
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <title>Docker Image Build</title>
  </head>
  <body>
    <h1>Apache Web Server</h1>
  </body>
</html>
```

### Dockerfile

```dockerfile
FROM httpd:2.4
COPY index.html /usr/local/apache2/htdocs/index.html
```

### Build 및 실행

```bash
docker build -t apache-example:1.0 .
docker container run \
  --name apache-example \
  -d \
  -p 8000:80 \
  apache-example:1.0
```

Browser 또는 `curl http://localhost:8000`으로 변경된 Page를 확인한다.

## 7 ) Nginx Main Page Image

---

Nginx 공식 Image의 기본 문서 경로는 `/usr/share/nginx/html`이다.

본 실습의 `/var/www/html`은 Ubuntu 등에 Package로 설치한 Nginx에서 자주 사용하는 경로이며 공식 Docker Image의 기본 경로와 다르다.

### Dockerfile

```dockerfile
FROM nginx
COPY index.html /usr/share/nginx/html/index.html
```

### Build 및 실행

```bash
docker build -t nginx-example:1.0 .
docker container run \
  --name nginx-example \
  -d \
  -p 9000:80 \
  nginx-example:1.0
```

> **중간 정리**
>
> - Dockerfile과 `index.html`을 같은 Build Context에 두고 Image를 Build한다.
>
> - Apache 공식 Image의 기본 문서 경로는 `/usr/local/apache2/htdocs`이다.
>
> - Nginx 공식 Image의 기본 문서 경로는 `/usr/share/nginx/html`이다.
>
> - Build한 Image를 Container로 실행하고 Host Port를 연결하여 Page를 확인한다.

## 8 ) Dockerfile을 사용하는 이유

---

Host에 Apache와 PHP를 직접 설치하려면 Package 설치, Service 시작, 설정 변경, Web Page 배치 과정을 순서대로 반복해야 한다.

```bash
sudo apt update
sudo apt install -y apache2 php
sudo service apache2 start
sudo service apache2 status
curl http://localhost:80
```

이러한 명령을 수동으로 실행하면 환경이 커질수록 누락과 차이가 누적된다. Dockerfile로 필요한 Package, 설정, Source Code, 실행 명령을 정의하면 변경 이력을 Version Control로 관리하고 동일한 Image를 반복해서 만들 수 있다.

다만 Dockerfile만으로 Database와 Web Application처럼 여러 Container의 실행 관계까지 모두 정의하지는 않는다. 여러 Service의 Network, Volume, 환경 변수와 실행 순서는 Docker Compose 같은 도구로 함께 관리한다.

> **최종 정리**
>
> - Dockerfile은 Image 생성 과정을 Code로 기록하여 동일한 환경을 반복해서 Build할 수 있게 한다.
>
> - `FROM`으로 Base Image를 지정하고 `RUN`, `COPY`, `ENV` 등으로 실행 환경을 구성한다.
>
> - `ENTRYPOINT`는 주 실행 명령을, `CMD`는 기본 명령이나 기본 인자를 정의한다.
>
> - Dockerfile의 Instruction 순서는 Image Layer와 Build Cache에 영향을 준다.
>
> - `docker build`는 Dockerfile과 Build Context를 사용하여 새로운 Image를 생성한다.
>
> - `MAINTAINER`처럼 현재 Deprecated된 Instruction은 그대로 이해하되 새 Dockerfile에서는 대체 방법을 사용한다.
