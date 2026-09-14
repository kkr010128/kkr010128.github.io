---
title: Jenkins Freestyle Job과 Credentials
description: Jenkins Freestyle Job의 설정 영역과 Build 실행 흐름을 이해하고 SCM 및 외부 서비스 인증 정보를 Credentials로 관리한다
date: 2026-09-14
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Jenkins
---

[Jenkins Controller-Agent 구조와 설치](/cloud-native-47-jenkins-architecture-installation/)에서 Controller가 Trigger와 Queue를 관리하고 Agent의 Executor가 Build를 실행하는 구조를 정리했다. 이번에는 Jenkins가 수행할 작업을 Freestyle Job으로 정의하고, 실행 결과와 외부 서비스 인증 정보를 관리한다.

## 1 ) Job, Build와 Freestyle

---

> **Job**
> Jenkins가 수행해야 할 작업의 설정이다. 언제 시작하고, 어느 Source를 가져오며, 어떤 명령을 실행하고, 완료 후 무엇을 할지 정의한다.

> **Build**
> Job을 한 번 실행한 결과이다. 실행할 때마다 고유한 Build Number가 붙고 상태, Console Log와 Artifact가 연결된다.

Freestyle Job은 화면에서 SCM, Trigger, Build Step과 Post-build Action을 조합하는 일반적인 Job 유형이다. 간단한 Test, Build, Package와 알림을 빠르게 구성하기 좋다. 복잡한 분기와 반복 가능한 Code Review가 필요하면 이후에 다룰 Pipeline과 `Jenkinsfile`이 더 적합하다.

| 설정 영역 | 답하는 질문 | 예시 |
|---|---|---|
| General | Job 자체를 어떻게 관리하는가 | 설명, Parameter, Build 보존, 동시 실행 |
| Source Code Management | 어떤 Source를 가져오는가 | Git Repository, Branch, Credential |
| Build Triggers | 언제 Build를 시작하는가 | 수동, 일정, Poll SCM, Webhook, Upstream |
| Build Environment | 실행 직전에 어떤 환경을 준비하는가 | Workspace 정리, Secret 주입, Timestamp, Timeout |
| Build Steps | 실제로 무엇을 실행하는가 | Shell, Batch, Maven, Gradle |
| Post-build Actions | 실행 후 무엇을 남기거나 알리는가 | Artifact 보관, Test Report, Email, Downstream Job |

## 2 ) Freestyle Job 생성과 첫 Build

---

Dashboard에서 **New Item**을 선택하고 이름을 입력한 뒤 **Freestyle project**를 선택한다. Description에는 이 Job이 다루는 Repository, Build 결과와 실행 목적을 적는다.

**Build Steps → Add build step → Execute shell**을 선택하고 다음 명령을 작성한다.

```bash
echo "Welcome to my first project using Jenkins"
```

저장 후 **Build Now**를 누르면 실행 요청이 Queue에 들어가고 사용 가능한 Executor가 Build를 수행한다. Build History에서 생성된 Build Number를 선택하고 **Console Output**을 열어 다음 항목을 확인한다.

- 어떤 Node와 Workspace에서 실행됐는가

- 어떤 사용자 또는 Trigger가 시작했는가

- Shell 명령과 출력은 무엇인가

- Process 종료 Code와 최종 Build 상태는 무엇인가

Job의 **Workspace** 메뉴는 현재 Source와 작업 File을 보여준다. 기본 경로 형식은 다음과 같지만 실제 경로는 Build를 실행한 Node와 Jenkins Home 설정에 따라 달라진다.

```text
/var/jenkins_home/workspace/<job-name>
```

Workspace는 작업 공간이며 보관소가 아니다. Cleanup 정책이나 Agent 교체로 사라질 수 있으므로 이후 Build나 배포에 필요한 결과는 Artifact로 보관하거나 외부 Artifact Repository에 올린다.

## 3 ) General 설정

---

| 항목 | 동작 | 적용 판단 |
|---|---|---|
| Discard old builds | 기간이나 개수를 넘은 Build Record와 Artifact 삭제 | Disk 사용량을 제어할 때 설정 |
| This project is parameterized | 실행 시 문자열, 선택 값 등 입력 수신 | 환경이나 Version을 선택해야 할 때 사용 |
| Execute concurrent builds | 같은 Job의 Build 여러 개를 동시에 실행 | Workspace와 외부 Resource 충돌이 없을 때만 사용 |
| Throttle builds | Plugin 정책으로 동시 실행 수 제한 | Agent 과부하나 외부 API 제한을 제어할 때 사용 |
| Quiet period | 요청 후 지정한 초만큼 Queue에서 대기 | 짧은 시간에 연속된 변경을 모아 실행할 때 사용 |
| Retry Count | SCM Checkout 실패 시 재시도 | 일시적인 Network 오류를 허용할 때 사용 |
| Custom workspace | 기본값이 아닌 Directory 사용 | 공유 Directory 충돌과 정리 책임을 검토한 뒤 사용 |
| Display Name | UI에 표시할 별도 이름 설정 | Job 이름과 사용자 표시 이름을 구분할 때 사용 |

Quiet Period는 첫 Commit을 누락시키는 기능이 아니다. 실행 요청을 잠시 대기시켜 짧은 시간에 들어온 후속 요청과 함께 처리할 기회를 제공한다. 너무 길게 설정하면 Feedback도 늦어진다.

동시 Build를 허용하면 같은 Workspace, 고정 Port, Test DB 또는 배포 대상을 동시에 수정할 수 있다. 단순히 Agent 성능이 좋다는 이유만으로 켜지 않고 작업 간 격리가 보장되는지 확인한다.

## 4 ) Upstream과 Downstream

---

한 Job의 결과를 다른 Job이 사용하면 실행 순서를 정의해야 한다.

```text
image-build (upstream) → kubernetes-deploy (downstream)
```

Image를 만드는 `image-build`가 완료되기 전에 `kubernetes-deploy`가 시작되면 존재하지 않거나 이전 Version의 Image를 배포할 수 있다.

| 설정 | 방지하려는 상황 |
|---|---|
| Block build when upstream project is building | 선행 Job이 실행 또는 대기 중인데 후속 Job이 먼저 시작되는 상황 |
| Block build when downstream project is building | 후속 Job이 사용하는 대상을 선행 Job이 동시에 변경하는 상황 |
| Build after other projects are built | 선행 Job의 결과에 따라 현재 Job을 시작해야 하는 상황 |

선행 Job의 Artifact를 사용하는 Build는 어떤 Build Number와 Artifact를 전달했는지도 함께 추적해야 한다. 단순 실행 순서만 연결하면 재실행 시 서로 다른 Version이 섞일 수 있다.

## 5 ) Build Trigger 선택

---

| Trigger | 동작 | 적합한 경우 | 주의 사항 |
|---|---|---|---|
| Build Now | 사용자가 화면에서 실행 | 설정 확인, 일회성 작업 | 반복 자동화에 부적합 |
| Trigger builds remotely | Token이 포함된 Endpoint를 외부 Script가 호출 | 제한된 외부 시스템 연동 | HTTPS, 인증과 Token 노출 방지 필요 |
| Build after other projects are built | Upstream Build 결과에 따라 실행 | Job 간 순서 연결 | Artifact Version 연결 필요 |
| Build periodically | Cron 일정에 따라 실행 | Source 변경과 무관한 정기 작업 | 변경이 없어도 실행 |
| Poll SCM | 일정마다 SCM 변경 여부를 확인하고 변경 시 실행 | Jenkins가 외부 요청을 받을 수 없는 환경 | Polling 요청과 감지 지연 발생 |
| GitHub hook trigger | GitHub Webhook Event 수신 시 실행 | 변경 직후 Build가 필요한 환경 | GitHub에서 Jenkins Endpoint로 접근 가능해야 함 |

Remote Trigger URL은 다음 형태를 사용한다.

```text
https://<jenkins-host>/job/<job-name>/build?token=<token>
```

Token을 URL에 넣으면 Browser History, Proxy와 Access Log에 남을 수 있다. 외부 호출에는 HTTPS와 별도 인증을 적용하고 권한을 최소화한다.

Cron 표현식 `H/5 * * * *`를 Poll SCM에 설정하면 Jenkins가 부하를 분산한 시작 시점을 기준으로 약 5분 간격으로 변경을 확인한다.

```text
H/5 * * * *
```

Webhook은 Event가 발생할 때 GitHub가 Jenkins에 알리므로 일반적으로 Poll SCM보다 빠르고 불필요한 조회가 적다. 그러나 외부에서 Jenkins에 접근할 수 없는 내부 실습 환경에서는 Poll SCM이 단순할 수 있다. 실제 Webhook 생성과 Network 공개는 별도 배포 범위에서 다룬다.

## 6 ) Build Environment와 Step

---

Build Environment는 Step 실행 전에 Workspace와 실행 조건을 준비한다.

| 항목 | 역할 | 필요한 Plugin 또는 조건 |
|---|---|---|
| Delete workspace before build starts | 이전 Build의 Source와 중간 File 제거 | Workspace Cleanup Plugin이 제공할 수 있음 |
| Use secret text(s) or file(s) | Credential을 환경 변수나 임시 File로 주입 | Credentials Binding Plugin |
| Add timestamps to Console Output | Log 각 줄에 시간 표시 | Timestamper Plugin |
| Terminate a build if it is stuck | 지정 시간 초과 시 Build 중단 | Build Timeout Plugin |
| Inspect build log for published build scans | Maven·Gradle Build Scan URL 수집 | 관련 Build Scan Plugin |
| With Ant | Jenkins에 설정한 Ant Tool 사용 | Ant Plugin과 Tool 설정 |

Build Step은 작성 순서대로 실행된다. 앞 Step이 실패하면 기본적으로 뒤 Step으로 진행하지 않는다. Linux와 macOS Agent에서는 **Execute shell**, Windows Agent에서는 **Execute Windows batch command** 또는 PowerShell 관련 Step을 사용한다.

Ant는 Java Build 자동화 도구이며 Compile, Test와 Package를 명시적인 Target으로 구성한다. Maven과 Gradle을 사용하는 Project도 많으므로 Build Tool은 Project의 실제 설정 File에 맞춰 선택한다.

Post-build Action은 Build Step이 끝난 뒤 Report 발행, Artifact 보관, Email 알림이나 Downstream Job 실행 같은 후속 처리를 수행한다. Post-build Action 자체의 결과에 따라 Build가 `Unstable`로 바뀔 수도 있으므로 Console Log와 상태 원인을 함께 확인한다.

## 7 ) Credentials가 필요한 이유

---

Jenkins Job은 Private Git Repository, Artifact Repository, Cloud API와 배포 Server 같은 외부 시스템에 접속한다. 인증 값을 Job 설정이나 Shell Script에 직접 넣으면 다음 문제가 생긴다.

- Job 설정을 볼 수 있는 사용자에게 Secret이 노출된다.

- Script를 Git에 Commit하면 이력에 Secret이 남는다.

- 값이 바뀔 때마다 여러 Job을 수정해야 한다.

- 동일한 계정을 여러 곳에 복사해 사용 범위와 폐기 지점을 추적하기 어렵다.

Credentials Store에 값을 등록하면 식별자인 Credential ID로 필요한 Job에 연결하고, 접근 범위와 교체 지점을 중앙에서 관리할 수 있다. Jenkins가 값을 저장한다고 해서 모든 노출을 자동으로 막는 것은 아니다. Job이 Secret을 출력하거나 외부로 전송할 권한은 여전히 가지므로 Script와 Plugin을 신뢰할 수 있어야 한다.

## 8 ) Credential 종류, Scope와 Domain

---

| 종류 | 사용 예 |
|---|---|
| Username with password | HTTP Basic 인증, Username과 Token 조합 |
| SSH Username with private key | SSH 방식 Git Checkout, 원격 Server 접속 |
| Secret text | API Token, 단일 Password |
| Secret file | Service Account JSON, 인증서 File |
| Certificate | PKCS#12 인증서와 Password |

| Scope | 사용 범위 |
|---|---|
| Global | 일반적인 Job과 Item에서 사용할 수 있는 Credential |
| System | Agent 연결이나 System Email 같은 Jenkins 내부 기능 전용 Credential |

Domain은 Hostname, Port 또는 Protocol 같은 조건으로 Credential을 그룹화하고 선택 후보를 좁힌다. Domain은 강한 보안 경계 자체가 아니므로 Folder 권한, Role과 Credential Scope도 함께 설계해야 한다.

Credential은 **Manage Jenkins → Credentials**에서 Store와 Domain을 선택한 뒤 추가한다. Job에서 Credential을 참조할 때는 의미가 드러나는 ID를 사용한다.

```text
github-readonly
dockerhub-push
production-ssh
```

Private Git Repository를 연결할 때 **Source Code Management → Git**에 Repository URL과 Branch를 입력하고, URL 방식에 맞는 Credential을 선택한다.

| Repository URL | 적합한 Credential |
|---|---|
| `https://github.com/<owner>/<repo>.git` | Username과 Personal Access Token |
| `git@github.com:<owner>/<repo>.git` | SSH Username과 Private Key |

Public Repository는 읽기만 할 경우 Credential이 없어도 Checkout할 수 있다. Private Repository는 Repository 읽기 범위만 가진 Credential을 우선 사용하고, Build에 Push 권한까지 불필요하게 주지 않는다.

> **최종 정리**
> - Job은 작업 정의이고 Build는 Job을 한 번 실행한 이력이며 Build Number, 상태와 Log를 가진다.
>
> - Freestyle Job은 General, SCM, Trigger, Environment, Build Step과 Post-build Action 순으로 실행 조건과 작업을 구성한다.
>
> - Poll SCM은 Jenkins가 변경을 조회하고 Webhook은 GitHub가 변경 Event를 전달한다.
>
> - Workspace는 일시적인 작업 공간이므로 필요한 결과는 Artifact로 별도 보관한다.
>
> - Credential은 ID로 참조하고 Job에 필요한 최소 권한과 범위만 제공한다.
