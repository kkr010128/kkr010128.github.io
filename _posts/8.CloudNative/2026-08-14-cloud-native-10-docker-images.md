---
title: Docker 이미지와 Union File System
description: Docker Image 검색과 다운로드, Layer 구조, Tag 및 Docker Hub 배포 방법
date: 2026-08-14
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Docker
---
## 1 ) Docker Image

---

Docker Image는 Container 형태로 Software를 배포하고 실행하는 데 필요한 코드, Runtime, Library와 설정을 담은 Package이다.

- 실행에 필요한 요소를 포함하므로 환경별 의존성 차이를 줄인다.
- 특정 시점의 Container File System을 담은 Snapshot으로 볼 수 있다.
- 하나의 Image로 동일한 환경을 가진 Container를 여러 개 생성할 수 있다.
- 여러 개의 읽기 전용 Layer로 구성된다.

### Image 이름

Image의 전체 참조 형식은 다음과 같다.

```text
REGISTRY/NAMESPACE/REPOSITORY:TAG
```

Docker Hub 공식 Image는 `docker.io/library`를 생략할 수 있고, Tag를 생략하면 기본적으로 `latest`가 사용된다.

```text
docker.io/library/debian:latest
library/debian:latest
debian:latest
debian
```

네 표현은 모두 같은 Image를 가리킨다. 다만 `latest`는 가장 최신 Version을 보장하는 의미가 아니라 이름이 `latest`인 Tag이므로, 재현 가능한 배포에는 명시적인 Version Tag나 Digest를 사용하는 것이 좋다.

## 2 ) Image 검색과 다운로드

---

### 검색

```bash
docker search [OPTIONS] KEYWORD
docker search --limit 5 httpd
```

검색 결과에는 Image 이름, 설명, Star 수, 공식 Image 여부 등이 표시된다.

### 다운로드

```bash
docker image pull NAME[:TAG]
docker image pull NAME@DIGEST
```

```bash
docker pull jenkins/jenkins:lts
docker pull debian:latest
docker pull gcr.io/google-samples/hello-app:1.0
```

주요 Option은 다음과 같다.

| Option | 설명 |
|---|---|
| `--all-tags`, `-a` | Repository의 모든 Tag 다운로드 |
| `--platform` | 대상 Platform 지정 |
| `--quiet`, `-q` | 상세 출력 생략 |

Apple Silicon Mac에서는 필요에 따라 `--platform linux/arm64` 또는 실행할 Image가 요구하는 Platform을 지정한다.

Digest는 Image Content를 식별하는 Hash 값이다. 같은 Digest를 사용하면 동일한 Image Content를 가리킨다.

## 3 ) Image 조회

---

```bash
# Local Image 목록
docker images
docker image ls

# 상세 정보
docker image inspect httpd

# 생성 시각만 출력
docker image inspect --format='{{.Created}}' httpd

# Layer 생성 이력
docker image history httpd
```

`docker image history`를 사용하면 Image를 구성한 명령과 Layer 정보를 확인할 수 있다.

## 4 ) Union File System

---

Union File System은 서로 다른 File System이나 Directory의 내용을 하나의 File System처럼 합쳐 보여주는 기술이다.

Docker Image는 변경할 수 없는 여러 읽기 전용 Layer로 구성된다. Image로 Container를 실행하면 그 위에 쓰기 가능한 Container Layer가 추가되고, 실행 중 발생한 변경 사항은 이 Layer에 기록된다.

```text
Container Layer     ← Read / Write
-----------------
Application Layer   ← Read Only
Library Layer       ← Read Only
Base Image Layer    ← Read Only
```

동일한 Image에서 만든 Container들은 읽기 전용 Image Layer를 공유하므로 Disk를 효율적으로 사용할 수 있다. Container Layer는 Container 삭제 시 함께 사라질 수 있으므로 영구 데이터는 Volume에 저장한다.

Linux Docker Engine의 데이터와 Log는 일반적으로 `/var/lib/docker` 아래에 저장되며 Storage Driver에 따라 실제 구조가 달라질 수 있다. `overlay2`를 사용하는 환경에서는 관련 Layer 데이터가 해당 영역에 관리된다.

## 5 ) Docker Hub 로그인과 Image 배포

---

### 로그인

```bash
docker login
docker login -u USERNAME
docker logout
```

비밀번호를 Command에 직접 작성하지 않는다. Docker Hub가 요구하는 경우 Password 대신 Access Token을 사용하고, Token은 문서나 Git Repository에 저장하지 않는다.

### Tag 지정

```bash
docker image tag SOURCE_IMAGE TARGET_IMAGE
docker image tag httpd:latest USERNAME/myapache:1.0
```

Tag는 같은 Image에 Registry에 업로드할 참조 이름과 Version을 부여한다.

### Push

Docker Hub에서 Repository를 만든 뒤 계정 Namespace가 포함된 이름으로 Push한다.

```bash
docker push USERNAME/myapache:1.0
```

새 Version은 다른 Tag를 붙여 같은 Repository에 추가할 수 있다.

```bash
docker image tag httpd:latest USERNAME/myapache:2.0
docker push USERNAME/myapache:2.0
```

## 6 ) Docker Image를 파일로 관리

---

Docker Image는 Registry를 거치지 않고 `tar` Archive로 저장하고 다른 Docker 환경에서 다시 불러올 수 있다. `docker image save`는 Image의 Layer와 Tag 정보를 함께 보존하므로, Network를 사용할 수 없는 환경으로 Image를 옮기거나 특정 Image를 보관할 때 유용하다.

### Image 저장

```txt
docker image save [OPTIONS] IMAGE [IMAGE...]
```

`-o` 또는 `--output` Option을 사용하면 출력 파일을 직접 지정할 수 있다.

```bash
# Image 다운로드
docker image pull eclipse-mosquitto:latest

# Local Image 확인
docker image ls

# tar Archive로 저장
docker image save -o eclipse-mosquitto.tar eclipse-mosquitto:latest
```

Shell의 출력 Redirection을 사용해도 같은 방식으로 저장할 수 있다.

```bash
docker image save eclipse-mosquitto:latest > eclipse-mosquitto.tar
```

### Image 불러오기

`docker image load`는 `save`로 만든 Archive에서 Image와 Tag 정보를 복원한다.

```bash
docker image load -i eclipse-mosquitto.tar
docker image ls
```

입력 Redirection을 사용할 수도 있다.

```bash
docker image load < eclipse-mosquitto.tar
```

Container의 File System을 `docker export`와 `docker import`로 옮기는 방식과 달리, `save`와 `load`는 Image Layer와 Metadata를 유지한다.

### Image 삭제와 정리

Image 이름과 Tag 또는 Image ID를 지정해 Local Image를 삭제할 수 있다. `docker rmi`는 `docker image rm`의 단축 명령이다.

```bash
docker image rm IMAGE[:TAG]
docker image rm IMAGE_ID
docker rmi IMAGE[:TAG]
```

주요 Option은 다음과 같다.

| Option | 설명 |
|---|---|
| `--force`, `-f` | 충돌이 발생해도 Image를 강제로 삭제 |
| `--no-prune` | 기본적으로 함께 정리되는 Tag가 없는 Parent Image를 보존 |

Local Image ID 전체를 명령 치환으로 전달하면 모든 Local Image의 삭제를 시도한다.

```bash
docker image rm $(docker image ls -q)
```

실행 중인 Container가 사용하거나 다른 Image가 참조하는 Image는 삭제되지 않을 수 있다. `-f`를 사용하기 전에 Container와 Image의 사용 관계를 먼저 확인한다.

사용하지 않는 Image만 정리하려면 `prune`을 사용한다.

```bash
# Dangling Image만 제거
docker image prune

# Container가 사용하지 않는 모든 Image 제거
docker image prune -a
```

`docker image prune -a`는 다시 필요할 수 있는 Local Image도 삭제할 수 있으므로, 표시되는 삭제 대상을 확인한 뒤 실행한다.
