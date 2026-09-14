---
title: Jenkins Controller-Agent 구조와 설치
description: Jenkins의 Job 실행 흐름을 Controller, Queue, Agent와 Executor 관점에서 이해하고 Docker로 설치해 초기 설정과 Plugin을 관리한다
date: 2026-09-14
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Jenkins
---

[GitHub Actions Workflow와 CI/CD 실습](/cloud-native-46-github-actions-ci/)은 GitHub가 제공하는 Runner에서 Build와 Test를 실행했다. Jenkins는 조직이 직접 설치하고 확장할 수 있는 Java 기반 Open Source 자동화 Server이다. Source Checkout, Compile, Test, 정적 분석, Package, 배포와 결과 알림을 Plugin과 Job으로 연결한다.

## 1 ) Jenkins가 담당하는 자동화

---

여러 개발자의 변경 사항이 Main Branch에 병합되면 Jenkins는 Webhook을 받거나 Repository를 주기적으로 확인해 Job을 시작할 수 있다. 일반적인 처리 과정은 다음과 같다.

1. SCM Plugin으로 대상 Commit을 Checkout한다.

2. Maven이나 Gradle 같은 Build Tool로 Source를 Compile한다.

3. Unit Test와 Integration Test를 실행한다.

4. 정적 분석 도구로 Coding Convention, 결함과 사용하지 않는 Code를 확인한다.

5. JAR, WAR 또는 Container Image 같은 Artifact로 Package한다.

6. 배포 도구를 호출해 검증된 Artifact를 대상 환경으로 전달한다.

7. 배포된 Application을 Selenium 같은 자동화 도구로 추가 검증할 수 있다.

8. 수행 결과를 Email이나 협업 도구로 알린다.

Jenkins Core가 모든 도구를 직접 구현하는 것은 아니다. Git, Maven, Email Extension처럼 외부 도구와 연결하는 기능은 주로 Plugin이 제공한다. 따라서 Jenkins Version뿐 아니라 설치한 Plugin의 Version과 호환성도 함께 관리해야 한다.

## 2 ) Controller, Agent와 Executor

---

Jenkins의 분산 구조를 이해하려면 실행을 결정하는 역할과 실제 명령을 수행하는 역할을 분리해서 봐야 한다.

> **Controller**
> Jenkins의 중앙 조정 Process이다. 설정과 Plugin을 보관하고 Web UI를 제공하며 Trigger, Build Queue와 Agent 할당을 관리한다. 과거에는 Master라고 불렀지만 현재 공식 용어는 Controller이다.

> **Agent**
> Controller에 연결되어 할당받은 Build Step을 실행하는 Machine, Virtual Machine 또는 Container이다.

| 구성 요소 | 관점 | 주요 역할 |
|---|---|---|
| Controller | 제어 | Job 설정 저장, Trigger 처리, Queue 관리, Agent 선택, UI와 결과 제공 |
| Queue | 대기 | 실행 조건을 만족했지만 Executor를 아직 배정받지 못한 Build 보관 |
| Agent | 실행 | Workspace 준비, Source Checkout, Compile, Test와 Package 실행 |
| Executor | 동시 실행 용량 | Node에서 동시에 실행할 수 있는 작업 Slot |
| Label | 작업 배치 조건 | `linux`, `docker`, `jdk21`처럼 Agent의 능력을 표시 |
| Workspace | 작업 File 영역 | Checkout한 Source와 Build 중간 결과를 저장하는 Node의 Directory |
| Artifact | 보존 결과 | Build가 만든 JAR, WAR, Report와 같은 불변 결과물 |

{% include visuals/jenkins-controller-agent-flow.html %}

Job이 시작되는 흐름은 다음과 같다.

1. 사용자의 **Build Now**, SCM 변경 또는 일정 Trigger가 Controller에 실행을 요청한다.

2. Controller가 Job 설정을 읽고 실행할 Build를 Queue에 넣는다.

3. Scheduler가 Label, Agent 연결 상태와 사용 가능한 Executor를 확인한다.

4. 조건을 만족하는 Agent의 Executor가 Build를 가져간다.

5. Agent가 자신의 Workspace에서 Checkout, Build와 Test를 실행한다.

6. Console Log, Build 상태와 보관하도록 설정한 Artifact를 Controller가 사용자에게 제공한다.

Agent 한 대에 Executor를 2개 설정하면 원칙적으로 작업 2개를 동시에 실행할 수 있다. 그러나 CPU, Memory, Disk I/O와 외부 Tool이 같은 Node를 공유하므로 Executor 수를 늘리는 것이 항상 처리량 증가로 이어지지는 않는다.

Controller도 Node이므로 Executor를 가질 수 있지만, 운영 환경에서는 중앙 조정 Process와 Build Process를 격리하기 위해 Controller의 Executor를 `0`으로 두고 전용 Agent에서 작업을 실행하는 구성이 일반적이다. 실습처럼 단일 Container에서 시작할 때는 Built-In Node가 Build를 실행할 수 있으나 이 차이를 알고 사용해야 한다.

## 3 ) 확장 방식

---

| 방식 | 변경 대상 | 장점 | 주의 사항 |
|---|---|---|---|
| 수직 확장 | Controller 또는 Agent의 CPU, Memory, Disk 증설 | 구성과 운영 지점이 적음 | 한 Node의 한계와 장애 영향 범위가 큼 |
| Agent 수평 확장 | 같은 Controller에 Agent 추가 | Build 실행 용량과 환경 격리 확장 | Queue 정책, Label과 Tool Version 관리 필요 |
| Controller 분리 | 목적별 Jenkins Instance 운영 | 팀·보안 영역·환경별 독립 설정 가능 | Plugin, Credential, Job과 Upgrade를 각각 관리해야 함 |

서로 독립된 Controller 여러 대를 운영한다고 해서 자동 Failover가 구성되는 것은 아니다. 한 Controller의 장애 시 다른 Controller가 Build를 자동 인계하려면 별도의 Job 동기화, Shared Storage, Backup과 복구 설계가 필요하다.

Test용과 Production용 Controller를 분리하면 실험적인 Plugin이나 설정 변경이 운영 자동화에 미치는 영향을 줄일 수 있다. 대규모 조직이 Public Cloud와 On-Premises를 함께 사용하며 많은 Build를 처리한 사례는 Jenkins를 역할별로 분리할 수 있음을 보여주는 역사적 사례로 이해한다. 실제 분리 기준은 Build 수보다 보안 경계, 장애 범위와 유지보수 비용으로 결정한다.

## 4 ) 설치 방법과 요구 사항

---

Jenkins는 여러 방식으로 설치할 수 있다.

| 설치 방식 | 특징 | 관리 대상 |
|---|---|---|
| Standalone WAR | Java로 `jenkins.war` 직접 실행 | Java, Service와 Jenkins Home |
| OS Package | Windows MSI, Debian·Ubuntu Package, Homebrew 등 사용 | OS Package와 Service 설정 |
| Docker | 공식 Image와 Volume으로 실행 | Image Tag, Container와 Volume |
| Kubernetes | Pod와 Persistent Volume으로 실행 | Kubernetes Resource와 Storage |
| Cloud Service | 공급자가 제공하는 관리형 환경 사용 | 공급자 정책과 연결 설정 |

Jenkins WAR에는 Winstone/Jetty 기반 실행 환경이 포함되어 있어 일반적으로 별도 Tomcat 없이 Standalone Application으로 실행한다. 외부 Servlet Container에 WAR를 배포하는 방식도 존재하지만 지원 범위와 호환성 제약을 먼저 확인해야 한다.

공식 Docker 설치 문서의 최소 요구 사항은 Memory 256 MB와 Disk 1 GB이며, Docker 환경은 Disk 10 GB 이상을 권장한다. 작은 팀에는 이보다 넉넉한 Memory와 Disk가 필요하다. 실제 용량은 Build 수, Workspace, Artifact 보존 기간과 Plugin 수를 기준으로 산정한다. 직접 설치할 때는 현재 Jenkins가 지원하는 Java Version도 확인해야 한다.

## 5 ) Docker Compose로 설치

---

다음 구성은 Jenkins Web UI와 향후 Inbound Agent 연결을 위한 Port를 열고 Jenkins Home을 Named Volume에 저장한다.

```yaml
services:
  jenkins:
    image: jenkins/jenkins:lts-jdk21
    container_name: jenkins
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home

volumes:
  jenkins_home:
```

| 설정 | 역할 |
|---|---|
| `jenkins/jenkins:lts-jdk21` | Java 21이 포함된 Jenkins LTS Image |
| `8080:8080` | Browser가 Jenkins Web UI에 접속하는 HTTP Port |
| `50000:50000` | 외부 Inbound Agent가 Controller에 연결할 때 사용하는 기본 TCP Port |
| `jenkins_home` | Job, Plugin, Credential Metadata와 Build 이력을 Container 교체 후에도 유지 |

WebSocket으로 Agent를 연결하거나 외부 Agent를 사용하지 않는다면 `50000` Port 공개는 필요하지 않다. Host의 `/var/run/docker.sock`을 Mount하고 Container를 `root`로 실행하면 Jenkins Job이 Host Docker Daemon을 사실상 제어할 수 있다. 단순한 실습에는 편리하지만 Host 권한 탈취로 이어질 수 있으므로 위 기본 설치에는 포함하지 않는다.

Compose File이 있는 Directory에서 실행한다.

```bash
docker compose up -d
docker compose ps
docker compose logs jenkins
```

`docker compose ps`에서 Container가 실행 중인지 확인하고, `docker compose logs jenkins`에서 초기화 진행과 오류를 확인한다. Jenkins는 `http://localhost:8080`으로 접속한다.

## 6 ) 초기 잠금 해제와 관리자 생성

---

최초 실행 시 Jenkins가 생성한 초기 관리자 Password로 Setup Wizard의 잠금을 해제한다.

```bash
docker exec jenkins \
  cat /var/jenkins_home/secrets/initialAdminPassword
```

이 값은 현재 Instance의 인증 정보이므로 문서, Source Repository 또는 화면 캡처에 남기지 않는다. 화면에 입력한 뒤 추천 Plugin을 설치하거나 필요한 Plugin을 선택하고, 실제로 사용할 관리자 계정을 생성한다.

초기 설정 순서는 다음과 같다.

1. `http://localhost:8080`에 접속한다.

2. 명령으로 확인한 초기 Password를 입력한다.

3. 추천 Plugin 설치 또는 Plugin 선택 설치를 진행한다.

4. 관리자 계정과 Jenkins URL을 설정한다.

5. Dashboard가 표시되는지 확인한다.

## 7 ) Plugin 관리

---

**Manage Jenkins → Plugins**에서 설치 가능, 설치됨과 Update 대상 Plugin을 확인한다.

| Plugin | 역할 |
|---|---|
| Git | Git Repository Checkout과 SCM 변경 확인 |
| Maven Integration | Maven Project 유형과 Maven Build 연동 |
| Email Extension | Build 결과에 따른 확장 Email 알림 |
| Credentials Binding | Credential을 Build 환경 변수나 File로 제한적으로 주입 |
| Throttle Concurrent Builds | Job 또는 Category별 동시 Build 수 제한 |

Plugin이 많아질수록 기능뿐 아니라 의존성, Upgrade와 보안 관리 범위도 커진다. Job에 필요한 Plugin만 설치하고 Jenkins Core를 Upgrade하기 전에 Plugin 호환성을 확인한다.

Update Center 오류가 발생하면 다음을 점검한다.

1. Jenkins Container의 DNS와 외부 Network 연결을 확인한다.

2. Host와 Container의 날짜와 시간이 올바른지 확인한다.

3. Proxy 환경이면 **Manage Jenkins → Plugins → Advanced settings**에서 Proxy를 설정한다.

4. 사설 CA를 사용한다면 인증서를 Java Truststore에 올바르게 등록한다.

5. Update Center Metadata를 다시 불러오고 Jenkins Log의 원인을 확인한다.

`SSLHandshakeException`을 피하려고 Update Center URL을 HTTPS에서 HTTP로 바꾸면 Plugin과 Metadata 전송의 기밀성과 무결성을 잃는다. 인증서 Chain, CA Truststore와 Proxy의 TLS Inspection 여부를 수정해야 한다.

현재 명칭과 설치 요구 사항은 [Jenkins 용어집](https://www.jenkins.io/doc/book/glossary/), [Jenkins 설치 문서](https://www.jenkins.io/doc/book/installing/)와 [Docker 설치 문서](https://www.jenkins.io/doc/book/installing/docker/)에서 확인할 수 있다.

> **최종 정리**
> - Controller는 Trigger, Queue, 설정과 결과를 관리하고 Agent의 Executor가 실제 Build Step을 실행한다.
>
> - Agent Label과 Executor 수는 작업의 실행 위치와 동시 실행 용량을 결정한다.
>
> - 독립된 Controller를 늘리는 것은 자동 Failover가 아니며 관리 대상도 함께 늘어난다.
>
> - Docker 설치에서는 `/var/jenkins_home`을 영속화하고 외부 Agent 사용 여부에 따라 `50000` Port를 결정한다.
>
> - 초기 Password와 Credential은 문서나 Repository에 남기지 않고, TLS 오류는 HTTP 전환이 아니라 인증서와 Network 원인을 수정한다.
