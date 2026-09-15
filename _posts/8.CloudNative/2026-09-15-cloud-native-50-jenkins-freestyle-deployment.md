---
title: Jenkins Freestyle Trigger와 SSH·Docker 배포
description: Jenkins Freestyle Job에서 주기 실행과 GitHub Webhook을 구성하고 Build Artifact를 SSH Server 또는 Docker Registry를 거쳐 배포한다
date: 2026-09-15
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Jenkins
---

[Jenkins Maven·Gradle Build와 Email 알림](/cloud-native-49-jenkins-maven-gradle-build/)에서 Java Application을 Test하고 JAR로 Package하는 과정을 구성했다. 이번에는 Build를 시작하는 Trigger와 생성된 Artifact를 SSH Server에 전송하는 방법, Docker Image로 만들어 Registry와 배포 Server에 전달하는 방법을 정리한다.

## 1 ) Build Trigger 선택

---

Jenkins Freestyle Job은 정해진 시각, SCM 변경 감지 또는 GitHub Webhook으로 시작할 수 있다.

| Trigger | Build 시작 조건 | 적합한 환경 |
|---|---|---|
| Build periodically | Schedule 시간이 되면 변경 여부와 관계없이 실행 | 정기 점검, Nightly Build |
| Poll SCM | Schedule마다 SCM을 확인하고 Revision이 바뀌면 실행 | Jenkins가 외부 Webhook을 받을 수 없는 환경 |
| GitHub hook trigger for GITScm polling | GitHub가 Push Event를 Jenkins에 전달하면 SCM 변경을 확인하고 실행 | GitHub에서 Jenkins로 접근할 수 있는 환경 |

Jenkins Schedule은 공백으로 구분한 다섯 Field를 사용한다.

```text
MINUTE HOUR DAY_OF_MONTH MONTH DAY_OF_WEEK
```

5분마다 정기 Build를 실행하려면 **Build periodically**에 다음 값을 입력한다.

```text
H/5 * * * *
```

같은 값을 **Poll SCM**에 입력하면 약 5분마다 Repository를 확인하되 Revision이 변경됐을 때만 Build한다. `H`는 여러 Job이 같은 분에 몰리지 않도록 Jenkins가 시작 시각을 분산하는 값이다.

## 2 ) GitHub Webhook으로 Build 시작

---

Webhook 방식에서는 GitHub가 Event 발생 사실을 Jenkins에 HTTP Request로 전달한다. 따라서 Jenkins Base URL은 GitHub에서 접근할 수 있어야 하며, 운영 환경에서는 HTTPS와 접근 제어를 적용한다.

### Jenkins Job 설정

Freestyle Job의 **Build Triggers**에서 **GitHub hook trigger for GITScm polling**을 선택한다. **Source Code Management → Git**의 Repository URL과 Credential도 Webhook을 등록할 Repository와 일치해야 한다.

### GitHub Repository 설정

Repository의 **Settings → Webhooks → Add webhook**에서 다음 값을 구성한다.

| 항목 | 값 또는 역할 |
|---|---|
| Payload URL | `https://<jenkins-base-url>/github-webhook/` |
| Content type | `application/json` |
| Secret | 충분히 긴 무작위 Secret |
| Events | 필요한 Event만 선택하며 Push Build는 Push Event 선택 |
| Active | Webhook 활성화 |

Payload URL은 Job 이름 경로가 아니라 Jenkins GitHub Plugin의 공통 Endpoint인 `/github-webhook/`로 끝난다. 저장 후 GitHub Webhook의 **Recent Deliveries**에서 응답 Status를 확인하고, Jenkins의 Build History와 Console Output에서 같은 Commit이 Checkout됐는지 확인한다.

수동으로 Webhook을 등록하는 경우 GitHub가 Jenkins Endpoint를 호출하므로 Jenkins에 GitHub Personal Access Token을 저장할 필요가 없다. Jenkins가 GitHub API를 이용해 Webhook을 자동 생성·관리하도록 구성할 때만 해당 Repository Hook을 관리할 수 있는 Credential이 필요하다. Push Webhook 수신만을 위해 `workflow` 권한을 추가하지 않는다.

> **주의**
> - GitHub Personal Access Token, Docker Hub Access Token, SSH Private Key와 Webhook Secret은 문서, Shell Script와 Repository에 직접 기록하지 않는다.
>
> - 이미 노출된 Token은 값을 지우는 것만으로 끝내지 않고 발급한 서비스에서 즉시 폐기한 뒤 새 Token을 발급한다.

자세한 설정 항목은 [Jenkins GitHub Plugin](https://plugins.jenkins.io/github/)과 [GitHub Webhook 생성 문서](https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks)를 참고한다.

## 3 ) SSH 배포 Server 준비

---

Jenkins가 JAR를 원격 Server로 배포하려면 Build 결과를 전송할 계정, Application을 실행할 Java Runtime과 배포 Directory가 필요하다.

### 배포 Server에서 실행

Ubuntu Server에 Application이 요구하는 Java Version을 설치한다. 다음 예시는 Java 21 Application을 실행하는 환경이다.

```bash
sudo apt update
sudo apt install -y openjdk-21-jre-headless
java --version
mkdir -p "$HOME/deploy"
```

Compile에 사용한 JDK와 실행 Server의 Java Major Version이 호환되어야 한다. `UnsupportedClassVersionError`가 발생하면 Jenkins Build의 Toolchain Version과 배포 Server의 `java --version`을 비교한다.

### Jenkins 실행 계정에서 SSH Key 생성

Jenkins가 Container에서 실행 중이라면 Key는 임시 Shell 사용자가 아니라 Jenkins Home을 소유한 `jenkins` 계정에 생성한다.

```bash
docker exec -it -u jenkins jenkins bash
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -C "jenkins-deploy" -f "$HOME/.ssh/id_ed25519"
```

`ssh-keygen`의 Passphrase를 설정하면 Private Key가 유출되더라도 바로 사용하기 어렵다. Jenkins Credential에서 Passphrase를 함께 관리할 수 있다. 대상 환경이 Ed25519를 지원하지 않을 때는 RSA 4096 Bit Key를 사용한다.

```bash
ssh-keygen -t rsa -b 4096 -C "jenkins-deploy" -f "$HOME/.ssh/id_rsa"
```

생성되는 File의 역할은 다음과 같다.

| File | 역할 | 배치 위치 |
|---|---|---|
| `id_ed25519` | Jenkins가 신원을 증명하는 Private Key | Jenkins Credential 또는 제한된 Jenkins Home |
| `id_ed25519.pub` | 배포 Server가 허용할 Public Key | 배포 계정의 `~/.ssh/authorized_keys` |

Private Key는 Jenkins 밖으로 복사하거나 Console에 출력하지 않는다. Public Key만 확인해 배포 Server 계정에 등록한다.

```bash
cat "$HOME/.ssh/id_ed25519.pub"
```

### 배포 Server에서 Public Key 등록

Jenkins가 접속할 배포 계정으로 실행한다.

```bash
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
nano "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"
```

`authorized_keys`에 Jenkins Public Key 한 줄을 추가한다. 배포 Server에서 SSH Password 인증을 끄기 전에 별도 Terminal에서 Key 인증이 성공하는지 먼저 확인한다.

Jenkins 실행 환경에서 최초 접속 전에 Server Host Key를 검증해 `known_hosts`에 등록한다. 아래 출력의 Fingerprint가 배포 Server의 실제 Fingerprint와 일치하는지 별도 경로로 확인한 뒤 저장한다.

```bash
ssh-keyscan -H <deploy-server-host> >> "$HOME/.ssh/known_hosts"
chmod 600 "$HOME/.ssh/known_hosts"
ssh <deploy-user>@<deploy-server-host>
```

`StrictHostKeyChecking=no`는 접속 대상의 신원을 검사하지 않으므로 자동 배포 Script에 사용하지 않는다.

## 4 ) Publish Over SSH로 JAR 전송

---

**Manage Jenkins → Plugins**에서 Publish Over SSH Plugin을 설치한 뒤 **Manage Jenkins → System → Publish over SSH → SSH Servers**에 배포 Server를 등록한다.

| 항목 | 예시 | 역할 |
|---|---|---|
| Name | `deploy-server` | Job에서 선택할 연결 이름 |
| Hostname | 배포 Server IP 또는 DNS | SSH 접속 대상 |
| Username | 배포 전용 계정 | File 전송과 실행 주체 |
| Remote Directory | `/home/<deploy-user>` | 상대 경로의 기준 Directory |
| Key 또는 Path to key | Jenkins 실행 계정의 Private Key | Public Key와 짝을 이루는 인증 정보 |

Plugin의 Global Key를 모든 Server에 공유할지, Server별 **Use a different key** 설정을 사용할지는 배포 계정 분리 기준에 따라 결정한다. 가능하면 Server와 환경별 Key를 분리하고 Jenkins Home의 Key File 권한을 제한한다. 자세한 항목은 [Publish Over SSH Plugin](https://plugins.jenkins.io/publish-over-ssh/)에서 확인한다.

**Test Configuration**으로 연결을 확인한다. Test가 실패하면 Network와 SSH Port, Username, `authorized_keys` 권한, Host Key와 Private Key 짝을 순서대로 점검한다.

Freestyle Job의 **Post-build Actions → Send build artifacts over SSH**에서 다음 값을 구성한다.

| 항목 | 예시 | 결과 |
|---|---|---|
| Source files | `build/libs/*.jar` | Workspace에서 전송할 JAR 선택 |
| Remove prefix | `build/libs` | 원격 경로에서 Build Directory 제거 |
| Remote directory | `deploy` | `<Remote Directory>/deploy`로 전송 |
| Exec command | `bash start_server.sh` | 전송 후 원격 실행 Script 시작 |

Spring Boot가 일반 JAR와 `-plain.jar`를 함께 만들면 실행 가능한 `bootJar`만 전송하도록 Pattern 또는 Artifact 이름을 고정한다.

```groovy
tasks.named('bootJar') {
    archiveFileName = 'calculator.jar'
}
```

배포 Server의 `~/deploy/start_server.sh`를 다음과 같이 작성한다.

```bash
#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="$HOME/deploy"
APP_JAR="$DEPLOY_DIR/calculator.jar"
PID_FILE="$DEPLOY_DIR/calculator.pid"
LOG_FILE="$DEPLOY_DIR/calculator.log"

java --version
test -f "$APP_JAR"

if [[ -f "$PID_FILE" ]]; then
    CURRENT_PID="$(cat "$PID_FILE")"
    if kill -0 "$CURRENT_PID" 2>/dev/null; then
        kill -15 "$CURRENT_PID"
        for _ in {1..30}; do
            kill -0 "$CURRENT_PID" 2>/dev/null || break
            sleep 1
        done
    fi
    rm -f "$PID_FILE"
fi

nohup java -jar "$APP_JAR" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
```

실행 권한을 부여하고 Script 문법을 확인한다.

```bash
chmod 750 "$HOME/deploy/start_server.sh"
bash -n "$HOME/deploy/start_server.sh"
```

`ps | grep` 결과를 잘라 PID를 찾는 방식은 `grep` Process나 다른 Application을 잘못 선택할 수 있다. PID File과 `kill -0`을 사용하면 이 Job이 시작한 Process인지 더 명확하게 추적할 수 있다. `nohup`에는 표준 출력·오류 Redirection과 Background 실행을 나타내는 `&`가 함께 필요하다.

배포 후 다음을 확인한다.

```bash
cat "$HOME/deploy/calculator.pid"
ps -p "$(cat "$HOME/deploy/calculator.pid")" -o pid,cmd
tail -n 100 "$HOME/deploy/calculator.log"
curl --fail "http://localhost:9000/"
```

## 5 ) Docker Image Build와 Registry Push

---

JAR를 직접 전송하는 대신 Jenkins가 Docker Image를 만들고 Registry에 Push할 수 있다. 다음 Dockerfile은 Gradle Build가 이미 생성한 JAR를 Runtime Image에 넣는다.

```dockerfile
FROM amazoncorretto:21-alpine

WORKDIR /app
COPY build/libs/calculator.jar app.jar

EXPOSE 9000
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

Dockerfile 안에서 `./mvnw`를 `CMD`로 실행하면 Image Build 시점이 아니라 Container 시작 시점에 Build가 실행된다. Source와 Wrapper를 Image에 복사하지 않았다면 명령 자체도 실행할 수 없다. 이 구성에서는 Jenkins가 먼저 `./gradlew clean build`를 실행하고 Dockerfile은 완성된 JAR만 복사한다.

Docker Hub Username과 Access Token을 Jenkins의 **Username with password** Credential로 저장한다. Freestyle Job에서는 Credentials Binding을 통해 환경 변수로 주입한 뒤 Shell에서 사용한다.

```bash
set -eu

./gradlew clean build

IMAGE_NAME="<dockerhub-username>/calculator"
IMAGE_TAG="${BUILD_NUMBER}"

printf '%s' "$DOCKERHUB_TOKEN" | docker login \
  --username "$DOCKERHUB_USERNAME" \
  --password-stdin

docker build --tag "$IMAGE_NAME:$IMAGE_TAG" .
docker push "$IMAGE_NAME:$IMAGE_TAG"
docker logout
```

Credential Binding에서 Username Variable은 `DOCKERHUB_USERNAME`, Password Variable은 `DOCKERHUB_TOKEN`으로 지정한다. Token 값을 Shell에 직접 쓰거나 `docker login -p <token>`처럼 Command Argument로 전달하지 않는다.

`latest` Tag만 사용하면 어떤 Build가 배포됐는지 추적하기 어렵다. Jenkins `BUILD_NUMBER`나 Commit SHA처럼 변경되지 않는 Tag를 Push하고, 필요할 때 같은 Image에 `latest`를 추가한다.

## 6 ) Jenkins에서 Docker를 실행하는 환경

---

Jenkins Container에서 Docker 명령을 실행하려면 Docker CLI만이 아니라 명령을 처리할 Docker Daemon Endpoint가 필요하다. 이 권한은 Build Script가 Host의 Container와 File System에 영향을 줄 수 있으므로 Controller에 직접 부여하지 않고 별도 Docker Build Agent를 사용하는 것이 기본 방향이다.

선택 가능한 구성은 다음과 같다.

| 구성 | 특징 | 주의 사항 |
|---|---|---|
| 전용 Docker Agent | Build Node에 Docker Engine과 제한된 Job을 배치 | Agent 접근 권한과 격리 필요 |
| Docker-in-Docker Agent | 별도 Daemon을 Build 환경 안에서 실행 | TLS, Storage와 Container 권한 설정 필요 |
| Remote BuildKit 또는 Image Builder | Docker Socket 없이 원격 Builder 사용 | Builder 인증과 Cache 관리 필요 |
| Host Docker Socket Mount | 구성이 단순함 | Socket 접근이 사실상 Host Root 수준 권한을 제공 |

실행 중인 Jenkins Controller Container 안에 Docker Engine을 임시 설치하면 Container 재생성 시 설정이 사라지고 Controller와 Build 환경도 결합된다. `/var/run/docker.sock`에 `chmod 666`을 적용하면 모든 Local 사용자가 Docker Daemon을 제어할 수 있으므로 사용하지 않는다. Socket을 Mount해야 하는 제한된 실습 환경이라도 전용 Agent와 Group 권한을 사용하고, 신뢰할 수 없는 Pull Request Job을 같은 Agent에서 실행하지 않는다.

Docker Daemon 권한의 영향은 [Docker Engine Security](https://docs.docker.com/engine/security/)와 [Linux Post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/)를 참고한다.

> **최종 정리**
> - Build periodically는 변경 여부와 관계없이 실행하고, Poll SCM은 Revision 변경 시 실행하며, GitHub Webhook은 Event를 Jenkins에 즉시 전달한다.
>
> - GitHub Webhook의 Jenkins Endpoint는 `/github-webhook/`이며 Secret과 필요한 Event만 설정한다.
>
> - SSH 배포에서는 Jenkins Private Key, 배포 Server의 `authorized_keys`와 검증된 `known_hosts`가 연결된다.
>
> - Publish Over SSH는 Build Artifact 전송과 원격 Script 실행을 연결하며, PID File로 이전 Application Process를 안전하게 종료한다.
>
> - Docker Credential은 Jenkins에서 주입하고 변경되지 않는 Image Tag를 Push한다.
>
> - Docker Socket은 높은 권한을 제공하므로 Controller가 아니라 격리된 Build Agent에서 다룬다.
