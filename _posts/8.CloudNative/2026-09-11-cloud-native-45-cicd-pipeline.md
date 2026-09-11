---
title: CI/CD Pipeline과 Container 배포 흐름
description: CI·Continuous Delivery·Continuous Deployment의 차이와 Source 변경이 Container Image 및 Kubernetes Pod로 이어지는 과정을 정리한다
date: 2026-09-11
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - CI/CD
---

[Container Image Registry](/cloud-native-41-container-image-registry/)는 배포할 Image를 저장하고 전달하며, [GitHub Remote Repository 작업 흐름](/cloud-native-44-github-remote-workflow/)은 여러 개발자의 변경을 중앙 Repository에서 합치는 방법을 다룬다. CI/CD는 이 두 지점 사이의 Build, Test, Package와 배포 과정을 반복 가능한 Pipeline으로 연결한다.

## 1 ) 개발 변경 사항이 배포되기까지

---

자동화가 없는 개발 흐름에서도 다음 작업은 필요하다.

1. 중앙 Repository의 최신 코드를 Local로 가져온다.

2. 요구 사항을 구현하고 Local Unit Test를 반복한다.

3. 변경 사항을 중앙 Repository에 Push하고 Main Branch에 병합한다.

4. 병합된 Source를 Compile 또는 Build한다.

5. Unit Test, Integration Test, Regression Test와 Static Analysis를 수행한다.

6. 검증된 결과물을 Package하고 실행 환경에 배포한다.

Test-driven Development(TDD)를 사용한다면 작은 Test를 먼저 작성하고 구현을 반복할 수 있다. TDD는 개발 방식이고 CI는 여러 변경을 자주 통합해 자동 검증하는 방식이므로 같은 개념은 아니다.

사람이 각 단계를 수동으로 넘기면 병합 후에야 Compile 오류를 발견하거나, 배포 직전의 큰 변경에서 결함이 한꺼번에 드러날 수 있다. Hotfix처럼 시간이 촉박한 작업에서는 Test 범위가 줄어들 위험도 커진다.

| 수동 흐름에서 생기는 문제 | Pipeline이 줄이는 부분 |
|---|---|
| 긴 인도 기간 | Commit 이후 Build와 Test를 즉시 시작 |
| 느린 Feedback | 실패한 Job과 Step을 실행 Log로 빠르게 확인 |
| 반복 작업 누락 | 같은 Workflow를 같은 순서로 실행 |
| 큰 Release 위험 | 작은 변경을 자주 검증하고 배포 후보를 지속적으로 생성 |
| 역할 간 전달 지연 | Artifact와 실행 결과를 공통 Repository와 Pipeline에 남김 |
| 의사소통 부족과 책임 분산 | 단계별 담당 범위, 승인과 실행 이력을 Pipeline에 기록 |
| 긴급 Hotfix와 반복 작업의 부담 | 표준 Test와 배포 절차를 재사용해 생략 가능성을 줄임 |

반복적인 수동 전달과 긴급 배포가 줄어들면 개발과 운영 업무의 예측 가능성도 높아진다.

> **Artifact**
> Build 과정이 만들어 낸 배포 가능한 결과물이다. JAR, WAR, 실행 Binary, 압축 Package, Container Image 또는 Helm Chart 등이 될 수 있다. Artifact가 항상 하나의 압축 File인 것은 아니다.

## 2 ) CI, Continuous Delivery와 Continuous Deployment

---

CI/CD는 하나의 제품명이 아니라 개발 변경을 통합하고 검증하며 배포 가능한 상태로 전달하는 일련의 관행과 자동화된 Pipeline을 뜻한다.

| 구분 | 목적 | 자동화가 끝나는 지점 |
|---|---|---|
| Continuous Integration(CI) | 작은 변경을 자주 통합하고 Build와 Test로 검증 | 배포 가능한 Artifact 생성과 검증 |
| Continuous Delivery | 검증된 변경을 언제든 Release할 수 있는 상태로 유지 | 운영 배포 직전까지 자동화하며 최종 Release에는 승인 절차를 둘 수 있음 |
| Continuous Deployment | 검증을 통과한 변경을 운영 환경까지 계속 배포 | 운영 Release까지 자동화 |

Continuous Delivery와 Continuous Deployment는 배포 전에 사람이 승인하는 지점이 있는지로 구분할 수 있다. 조직에 따라 두 용어를 넓은 의미의 CD로 묶어서 사용하므로 Pipeline 문서에서는 자동화 경계와 승인 조건을 함께 적어야 한다.

## 3 ) Continuous Integration

---

CI는 개발자가 작은 변경을 Version Control Repository에 자주 통합하고, 통합할 때마다 동일한 검사를 자동 실행하는 방식이다. 여러 언어, Platform과 Build Tool이 섞인 환경에서는 개발자마다 다른 Local 환경에 의존하지 않고 공통 검증 절차를 유지하는 것이 중요하다.

일반적인 CI 단계는 다음과 같다.

1. `push` 또는 Pull Request 같은 Event가 Pipeline을 시작한다.

2. Runner가 대상 Commit을 Checkout한다.

3. Dependency를 설치하고 Source를 Compile 또는 Build한다.

4. Unit Test와 Static Analysis를 수행한다.

5. 다음 단계에서 사용할 Artifact를 Package한다.

6. 결과와 Log를 저장하고 실패한 변경을 개발자에게 알린다.

CI 성공은 Workflow에 정의한 검사를 통과했다는 뜻이다. 정의하지 않은 Test, 운영 환경의 장애 조건과 Security 문제까지 모두 없다는 보장은 아니다. 따라서 Pipeline의 신뢰도는 어떤 검사를 어느 단계에 넣었는지에 달려 있다.

작은 변경을 자주 통합하면 여러 Branch가 오래 분리된 뒤 한꺼번에 충돌하는 Integration Hell을 줄일 수 있다. 실패 지점도 최근 변경 범위에 가까워져 원인을 찾기 쉬워진다.

## 4 ) Continuous Delivery와 Release

---

Continuous Delivery는 CI를 통과한 Artifact를 배포 가능한 Repository에 보관하고, Test 환경이나 Staging 환경까지 자동으로 전달한다. 운영팀은 검증된 같은 Artifact를 선택해 Production에 Release할 수 있다.

Continuous Deployment는 승인 대기 없이 정책과 Test를 모두 통과한 변경을 Production까지 자동 Release한다. 배포 횟수를 늘리는 것만으로 완성되지 않으며 자동 Test, Monitoring과 복구 절차가 함께 있어야 한다.

지속적인 전달 체계가 제공하는 효과는 다음과 같다.

- 변경부터 사용자 Feedback까지 걸리는 시간이 짧아진다.

- 한 번에 배포되는 변경 범위가 작아져 Release 위험을 줄일 수 있다.

- 검증된 Artifact를 필요한 시점에 Release할 수 있다.

- Build와 배포 절차가 Pipeline에 기록되어 재현하기 쉬워진다.

## 5 ) 자동 배포 Pipeline

---

Pipeline은 보통 다음 흐름으로 구성한다.

```text
Code Change
    ↓
Continuous Integration
    ↓
Automated Acceptance Test
    ↓
Configuration Change
    ↓
Deployment
    ↓
Monitoring and Feedback
```

| 단계 | 주요 작업 | 실패 시 확인할 대상 |
|---|---|---|
| Code Change | Commit, Push, Pull Request | Branch와 Commit, Trigger 조건 |
| CI | Checkout, Build, Unit Test, Static Analysis | Runner Log, Dependency, Test 결과 |
| Acceptance Test | 통합·인수·회귀 Test | Test 환경, 외부 Service, Test Data |
| Configuration Change | Image Tag, Manifest와 환경별 설정 갱신 | 설정 차이, Secret과 권한 |
| Deployment | 대상 환경에 원하는 상태 반영 | 배포 도구, API 응답, Rollout 상태 |
| Monitoring | Log, Metric과 사용자 Feedback 확인 | Error Rate, 응답 시간, Resource 상태 |

각 환경에서 Artifact를 다시 Build하면 같은 Version 이름이라도 Binary나 Image 내용이 달라질 수 있다. 배포할 Artifact를 한 번 만들고 식별 가능한 Version 또는 Digest로 저장한 뒤 같은 결과물을 다음 환경으로 승격하면 Build와 배포의 책임을 구분하기 쉽다.

## 6 ) Container와 Kubernetes의 CI/CD 흐름

---

Container 환경에서는 Application Artifact를 Container Image로 만들고 Registry에 저장할 수 있다. Kubernetes에 배포할 때는 Image와 함께 Deployment, StatefulSet 같은 Workload Resource의 Manifest가 필요하다.

{% include visuals/cicd-kubernetes-flow.html %}

### CI 관점

개발자가 Source를 Push하면 CI Runner가 대상 Commit을 Checkout하고 Build와 Test를 수행한다. 검증을 통과하면 Container Image를 한 번 만들고 Version Tag 또는 Digest와 함께 Registry에 Push한다.

Image 생성 시점을 CI와 CD 중 어디에 둘지는 Pipeline 설계에 따라 달라질 수 있다. 다만 여러 환경에 같은 결과물을 배포하려면 Image를 한 번 생성한 뒤 Registry에서 승격하는 구성이 유리하다.

### CD와 Control Plane 관점

CD System은 배포할 Image Version을 선택하고 Manifest의 원하는 상태를 갱신한다. `kubectl apply`, GitOps Controller 또는 배포 도구가 이 변경을 Kubernetes API Server에 전달한다.

API Server가 요청을 검증하고 Cluster 상태로 저장하면 Controller가 현재 상태를 원하는 상태에 맞추려 한다. 새 Pod가 필요할 경우 Scheduler는 실행할 Worker Node를 결정한다.

### Worker 관점

선택된 Worker의 kubelet은 자신에게 배정된 Pod Spec을 확인한다. kubelet이 Container Runtime에 Container 생성을 요청하면 Runtime은 Registry에서 지정된 Image를 Pull하고 Pod의 Container를 실행한다.

따라서 CI가 성공했더라도 배포 단계에서는 별도의 문제가 생길 수 있다.

- Worker가 Registry에 인증하지 못해 `ImagePullBackOff`가 발생할 수 있다.

- Manifest의 Image Tag가 존재하지 않을 수 있다.

- Resource 요청량이나 Scheduling 조건 때문에 Pod가 `Pending`에 머물 수 있다.

- Readiness Probe를 통과하지 못해 Service Traffic을 받지 못할 수 있다.

Control Plane의 배포 상태와 Worker의 실제 실행 상태를 함께 확인해야 Pipeline 결과와 Runtime 상태를 연결할 수 있다.

## 7 ) 역할별 도구

---

모든 단계를 하나의 제품으로 구성할 필요는 없다. 팀의 Repository, 배포 대상과 운영 방식에 맞춰 역할별 도구를 조합한다.

| 역할 | 도구 예시 | 담당 범위 |
|---|---|---|
| Source Code Management | GitHub, GitLab, Bitbucket | Commit, Branch, Pull Request와 권한 관리 |
| CI | GitHub Actions, Jenkins, TeamCity, CircleCI, GitLab CI/CD, Bamboo | Build, Test, 분석과 Artifact 생성 |
| Artifact·Image 저장 | GitHub Packages, GitLab Registry, Docker Hub, Cloud Registry | Version별 Package와 Container Image 저장 |
| Configuration Management | Ansible | Server Provisioning과 설정 자동화 |
| CD·GitOps | Argo CD, Spinnaker | 환경별 배포, 원하는 상태 동기화와 Release 제어 |
| Public Cloud Pipeline | AWS CodeBuild, CodePipeline, CodeDeploy 등 | Cloud Service와 연계한 Build 및 배포 자동화 |

TeamCity는 Kotlin DSL로 Build 구성을 코드화할 수 있다. Jenkins는 UI Job과 Pipeline Code를 모두 지원하고 Plugin 생태계가 넓다. Bamboo는 Jira, Confluence와 Bitbucket 같은 Atlassian 제품군과 연계할 수 있다. GitHub Actions와 GitLab CI/CD는 Repository Event와 Workflow File을 가까이 관리할 수 있다.

무료 실행 시간, Storage와 요금은 서비스와 Plan에 따라 바뀐다. 고정된 수치를 문서에 남기기보다 도입 시점의 공식 정책과 Self-hosted Runner 운영 비용을 함께 확인한다.

> **최종 정리**
> - CI는 작은 변경을 자주 통합하고 Build, Test와 Package 과정을 자동으로 검증한다.
>
> - Continuous Delivery는 언제든 Release할 수 있는 상태를 유지하고, Continuous Deployment는 운영 Release까지 자동화한다.
>
> - Container Pipeline에서는 검증된 Image를 Registry에 저장하고 식별 가능한 Version으로 다음 환경에 전달한다.
>
> - Kubernetes 배포는 CD 요청, Control Plane의 상태 조정과 배치, Worker의 Image Pull과 Pod 실행으로 이어진다.
