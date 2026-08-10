---
title: Cloud Native와 DevOps
description: Cloud Native의 개념과 적용 이유, CNCF, 개발 방식의 변화, DevOps와 Agile, CI/CD, Docker와 Kubernetes를 포함한 DevOps 생태계
date: 2026-08-10
series: Cloud
tags:
  - Cloud
  - AutoEverSW
---
## 1) Cloud Native 개요
---

Cloud Native는 Public Cloud, Private Cloud, Hybrid Cloud와 같은 현대적이고 동적인 환경에서 **확장 가능하고 탄력적인 애플리케이션을 개발하고 운영하기 위한 접근 방식**이다.

대표적인 기술과 설계 방식에는 다음과 같은 것들이 있다.

- Container
- Service Mesh
- Microservices
- Immutable Infrastructure
- Declarative API

이러한 기술을 자동화와 함께 활용하면 시스템을 느슨하게 결합하고, 변경에 유연하게 대응하며, 애플리케이션의 상태와 동작을 관찰하기 쉬운 환경을 구성할 수 있다.

결과적으로 개발자는 큰 변경을 한 번에 적용하기보다 **작은 변경을 반복적이고 예측 가능한 방식으로 배포하는 구조**를 만들 수 있다.

### CNCF

CNCF (Cloud Native Computing Foundation)는 Cloud Native 기술과 관련된 오픈 소스 프로젝트 생태계를 지원하는 재단이다.

특정 Cloud Vendor에 종속되지 않는 생태계를 지원하며 Kubernetes를 비롯한 다양한 Cloud Native 프로젝트를 관리하고 육성한다.

이를 통해 Cloud Native 기술과 운영 패턴이 특정 기업에만 제한되지 않고 다양한 조직과 개발자가 활용할 수 있는 생태계를 만드는 역할을 한다.

> **정리**
>
> - Cloud Native는 단순히 Cloud에서 Application을 실행하는 것을 의미하지 않는다.
> - Container, Microservices, Declarative API, 자동화 등을 활용하여 변화에 유연한 Application과 운영 환경을 만드는 접근 방식이다.
> - CNCF는 Cloud Native 관련 오픈 소스 프로젝트와 생태계를 지원한다.

## 2) IT 서비스 개발 및 구현 방식의 변화
---

Cloud Native의 등장에는 Application 개발 방식뿐 아니라 Architecture, 배포 방식, Infrastructure의 변화가 함께 영향을 주었다.

### 개발 방식

IT Service 개발에는 다음과 같은 다양한 방법론과 운영 방식이 사용된다.

- Waterfall
- Agile
- Scrum
- Kanban
- Lean
- DevOps
- DevSecOps
- Water-Scrum-Fall

Waterfall은 과거부터 사용되어 온 전통적인 개발 방식이며, 이후 변화에 빠르게 대응하기 위한 Agile 방식과 개발·운영의 협업을 강조하는 DevOps 등이 등장하였다.

### 개발 프로세스의 변화

강의에서는 개발 및 운영 방식의 변화 흐름을 다음과 같이 정리하였다.

```text
Waterfall
   ↓
Agile
   ↓
DevOps
   ↓
DevSecOps
````

이는 이전 방식이 완전히 사라지고 새로운 방식으로 교체된다는 의미라기보다, **빠른 변화와 지속적인 Delivery를 지원하기 위한 개발·운영 방식이 발전해 온 흐름**으로 이해할 수 있다.

### **Application Architecture의 변화**

```text
Monolithic
   ↓
N-Tier
   ↓
Microservices
```

초기의 Application은 하나의 큰 단위로 구성되는 Monolithic Architecture를 많이 사용했다.

이후 Presentation, Business Logic, Data 등의 역할을 계층으로 분리하는 N-Tier Architecture가 사용되었으며, Cloud Native 환경에서는 기능을 독립적인 Service 단위로 분리하는 Microservices Architecture가 활용된다.

### **개발 및 Packaging 방식의 변화**

```text
Physical Server
      ↓
Virtual Server
      ↓
Container
```

물리 Server에 Application을 직접 설치하는 방식에서 Virtualization을 이용하는 방식으로 변화했고, 이후 Application과 실행에 필요한 환경을 함께 Packaging하는 Container가 널리 사용되기 시작했다.

Container는 Virtual Machine보다 Application 실행 단위를 작고 독립적으로 구성하기 쉬워 Cloud Native Architecture와 잘 결합된다.

### **Infrastructure의 변화**

```text
Data Center
    ↓
Hosted Infrastructure
    ↓
Cloud
```

기업이 직접 Data Center와 Hardware를 운영하던 방식에서 외부 Hosting Infrastructure를 이용하는 방식으로 변화했고, 이후 필요한 Resource를 API와 자동화를 통해 사용할 수 있는 Cloud Infrastructure가 널리 사용되고 있다.

**정리**

|**영역**|**변화 흐름**|
|---|---|
|개발·운영 방식|Waterfall → Agile → DevOps / DevSecOps|
|Architecture|Monolithic → N-Tier → Microservices|
|실행 환경|Physical Server → Virtual Server → Container|
|Infrastructure|Data Center → Hosted → Cloud|

## **3) Cloud Native 적용이 필요한 이유**

---

### **서비스 배포 시간 단축**

Cloud Native 환경에서는 Container, Microservices, CI/CD 등의 기술을 이용하여 Application을 작은 단위로 개발하고 배포할 수 있다.

DevOps 문화와 자동화가 함께 적용되면 개발팀과 운영팀 사이의 협업 방식도 개선할 수 있다.

- 개발팀과 운영팀의 상호 이해 확대
- DevOps 문화 정착
- 조직 내 Team 간 Hand-off 감소
- 지속적인 Delivery와 Deployment
- 변경 과정의 복잡성 감소

Application 전체를 한 번에 변경해야 하는 구조보다 작은 Service 단위로 변경하고 배포할 수 있기 때문에 Release 주기를 단축하는 데 유리하다.

### **Application 및 Service 현대화**

Container를 이용하면 Application 실행 환경을 일정한 단위로 Packaging할 수 있다.

이를 통해 Application이 특정 Server 환경에 직접 의존하는 문제를 줄일 수 있다.

기존 On-Premise Application도 구조와 요구 사항에 따라 Container화하거나 Cloud 환경으로 이전할 수 있다.

Kubernetes는 다양한 Infrastructure 환경에서 Container를 일관된 방식으로 배포하고 관리하기 위한 Platform을 제공한다.

따라서 On-Premise와 Cloud 등 서로 다른 Infrastructure 환경에서도 Container 운영 방식을 일정하게 유지하는 데 활용할 수 있다.

### **신속한 신규 서비스 개발**

Cloud Native는 대규모 Open Source 생태계를 기반으로 발전하고 있다.

대표적으로 Kubernetes와 CNCF 프로젝트에는 많은 개발자와 기업이 참여하고 있다.

#### **풍부한 기술 생태계**

- Kubernetes
- CNCF Project
- Open Source Tool
- Community
- 다양한 Vendor 및 Cloud Provider 지원

#### **Open Source 기반**

Open Source 생태계는 개발자들이 기술을 학습하고 도구를 활용하기 쉬운 환경을 제공한다.

또한 특정 기업 내부에서만 사용되는 기술보다 관련 경험을 가진 개발자를 확보하기 쉬운 경우가 있다.

### **IT 목표**

Cloud Native를 통해 추구하는 IT 측면의 목표는 다음과 같이 정리할 수 있다.

- 민첩성 (Agility)
- 생산성 (Productivity)
- 복원력 (Resilience)
- 확장성 (Scalability)
- 최적화 (Optimization)
- 효율성 (Efficiency)

### **사업 성과**

기술적인 변화는 최종적으로 다음과 같은 Business 목표와 연결될 수 있다.

- 새로운 시장 및 서비스 대응
- Business Risk 감소
- 운영 비용 최적화
- 서비스 출시 속도 향상

Cloud Native를 적용한다고 해서 이러한 결과가 자동으로 발생하는 것은 아니며, 조직의 Architecture와 운영 방식, 자동화 수준 등이 함께 변화해야 한다.

**정리**

- Cloud Native는 작은 단위의 변경과 지속적인 Delivery를 지원한다.
- Container를 이용하여 Application과 Infrastructure 사이의 종속성을 줄일 수 있다.
- Kubernetes는 다양한 Infrastructure에서 Container를 일관된 방식으로 운영할 수 있도록 한다.
- 기술 도입 자체보다 DevOps와 자동화, Architecture 변화가 함께 이루어지는 것이 중요하다.

## **4) Cloud Native 운영 흐름**

---

강의에서는 Cloud Native 환경에서 제품을 개발하고 운영하는 전체 흐름을 다음과 같이 정리하였다.

```text
Product
   ↓
Development
   ↓
Capacity Planning
   ↓
Testing + Release Procedures
   ↓
Monitoring
   ↓
Incident Response
   ↓
Postmortem + Root Cause Analysis
```

### **Product**

어떤 Service와 기능을 제공할 것인지 정의한다.

### **Development**

Application과 Service를 개발한다.

### **Capacity Planning**

Service가 처리해야 하는 Traffic과 Resource 규모를 예측하고 필요한 Infrastructure Capacity를 계획한다.

### **Testing & Release Procedures**

Application을 검증하고 Production 환경에 Release하기 위한 절차를 구성한다.

### **Monitoring**

Application과 Infrastructure의 상태를 지속적으로 관찰한다.

### **Incident Response**

장애가 발생하면 문제를 감지하고 대응한다.

### **Postmortem & Root Cause Analysis**

장애가 해결된 후 원인을 분석하고 재발 방지 대책을 마련한다.

단순히 장애를 복구하는 데서 끝내지 않고 이후 동일한 문제가 다시 발생하지 않도록 개선하는 과정이 중요하다.

## **5) Pillars of Cloud Native**

---

강의에서는 Cloud Native를 구성하는 주요 요소를 다음 네 가지로 정리하였다.

- DevOps
- Microservices
- Containers
- Continuous Delivery

각 요소는 독립적인 기술이라기보다 Cloud Native Application을 빠르고 안정적으로 개발하고 운영하기 위해 서로 연결된다.

```text
           Cloud Native
               │
     ┌─────────┼─────────┐
     │         │         │
   DevOps  Microservices Container
     │
Continuous Delivery
```

### **DevOps**

DevOps를 이해하기 위해서는 먼저 Agile과 IT Service Management의 변화 과정을 이해할 필요가 있다.

### **Agile 방법론**

Waterfall은 Software Project를 요구 사항 분석부터 설계, 개발, 테스트, 배포까지 순차적으로 진행하는 방식이다.

초기 계획을 기반으로 순서대로 진행하기 때문에 개발 중 요구 사항이 변경될 경우 대응하기 어렵다는 문제가 발생할 수 있다.

Agile은 이러한 문제를 보완하기 위해 **짧은 개발 주기와 반복적인 개선, Team의 협업과 변화 대응**을 강조한다.

#### **Agile Manifesto**

Agile Manifesto에서는 다음 네 가지 가치를 강조한다.

프로세스와 도구보다 **개인과 상호 작용**

포괄적인 문서보다 **작동하는 Software**

계약 협상보다 **고객과의 협업**

계획을 따르는 것보다 **변화에 대응하는 것**

오른쪽의 요소도 가치가 있지만 왼쪽의 요소를 더 중요하게 본다는 의미이다.

즉, Agile이 문서나 계획을 없애자는 의미는 아니다.

변화하는 요구 사항에 맞춰 실제 동작하는 Software와 사람 사이의 협업을 더 중요하게 다루는 방식이다.

### **ITIL**

ITIL (Information Technology Infrastructure Library)은 IT Service Management (ITSM)를 위한 Best Practice 체계이다.

IT Service를 계획하고 제공하며 지속적으로 개선하기 위한 다양한 Practice를 제공한다.

ITIL은 오랫동안 기업의 IT Service Management에 활용되어 왔다.

ITIL 4에서는 기존의 절차 중심 접근을 확장하여 Agile, Lean, DevOps 등의 방식과 함께 사용할 수 있도록 Service Value System을 중심으로 체계가 구성되어 있다.

### **DevOps 개요**

DevOps는 **Development와 Operations를 결합한 개념**이다.

Software 개발자와 운영 담당자가 서로 분리된 조직으로 동작하는 대신 Application의 개발부터 Release, Production 운영까지 전체 Life Cycle에서 협력하는 방식과 문화를 의미한다.

```text
Plan
 ↓
Code
 ↓
Build
 ↓
Test
 ↓
Release
 ↓
Operate
 ↓
Monitor
 └──────────────→ 다시 Plan
```

DevOps에서는 하나의 Team이 Application 개발부터 Production 운영까지 더 넓은 범위를 책임지는 방향을 추구한다.

단순히 특정 CI/CD Tool을 도입하는 것이 아니라 **조직 문화, 개발 방식, 운영 Process를 함께 변화시키는 것**이 중요하다.

#### **Hand-off 감소**

전통적인 조직에서는 다음과 같이 역할이 분리될 수 있다.

```text
Developer
    ↓
Build Team
    ↓
QA
    ↓
Deployment Team
    ↓
Operations
```

업무가 Team 사이를 이동할 때 Context가 손실되거나 책임 소재가 불명확해지는 문제가 발생할 수 있다.

DevOps에서는 개발과 운영 Team의 협업과 자동화를 통해 이러한 Hand-off를 줄이는 것을 중요하게 본다.

### **DevOps Tool Chain**

DevOps는 Application의 전체 Life Cycle을 하나의 반복적인 흐름으로 관리한다.

|**단계**|**주요 역할**|
|---|---|
|Plan|목표, 요구 사항, 개발 계획 수립|
|Code|Source Code 개발, Review, Version Control, Merge|
|Build|Source Code Build 및 Artifact 생성|
|Test|Application 기능과 품질 검증|
|Package|배포 가능한 Application Artifact 또는 Image 생성|
|Release / Deploy|변경 사항 승인 및 Production 환경 배포|
|Operate|실제 Service 운영|
|Monitoring|Application 및 Infrastructure 상태와 사용자 경험 확인|

#### **Plan**

목표를 수행하기 위한 방법과 절차를 계획한다.

#### **Code**

- Source Code 작성
- Code Review
- Version Control
- Branch 및 Merge 관리

#### **Build**

Application을 실행 가능한 형태로 Build한다.

CI (Continuous Integration)를 통해 Code 변경 시 자동으로 Build와 검증을 수행할 수 있다.

#### **Test**

Application이 요구 사항에 맞게 동작하는지 검증한다.

#### **Package**

배포할 Application을 Package 형태로 생성한다.

예를 들어 Container 환경에서는 Docker Image가 배포 단위가 될 수 있다.

#### **Release / Deploy**

검증된 변경 사항을 실제 환경에 Release한다.

- Release 승인
- 변경 관리
- 자동 Deployment
- Rollback

#### **Operate**

Production 환경에서 Application과 Infrastructure를 운영한다.

#### **Monitoring**

Application과 Infrastructure의 상태를 지속적으로 확인한다.

- Performance
- Error
- Resource 사용량
- 최종 사용자 경험

### **DevOps로의 변화**

강의에서는 DevOps로의 변화 흐름을 다음과 같이 제시하였다.

```text
Service Oriented Architecture
            ↓
       Microservices
            ↓
Functional Microservices
```

```text
Agile Teams
     ↓
Mode 2 / DevOps / Agile Mindset
     ↓
Enterprise DevOps
```

```text
Cloud Infrastructure Automation
              ↓
             CI/CD
              ↓
       DevOps Automation
```

이는 모든 조직이 반드시 동일한 단계를 거친다는 의미라기보다, Architecture와 조직 문화, 자동화 방식이 함께 변화하는 흐름을 설명한 것이다.

### **DevOps의 이점**

|**이점**|**관련 개념**|
|---|---|
|개발 속도 향상|Agile, Microservices, Time to Market|
|신속한 배포|CI/CD|
|안정성 향상|Monitoring, Logging|
|Infrastructure 확장 및 표준화|IaC|
|협업 강화|개발·운영 협업 문화|
|Security 자동화|Policy as Code|

#### **속도**

작은 단위로 개발하고 Release하여 새로운 기능을 빠르게 제공할 수 있다.

#### **신속한 배포**

CI/CD Pipeline을 통해 Build, Test, Deployment 과정을 자동화할 수 있다.

#### **안정성**

Monitoring과 Logging을 이용하여 Application의 상태를 지속적으로 관찰하고 문제를 빠르게 확인할 수 있다.

#### **확장성**

IaC를 이용하여 Infrastructure를 Code로 관리하고 반복적으로 구성할 수 있다.

#### **협업 강화**

개발, 운영, 보안 등 서로 다른 역할을 가진 Team이 하나의 Service Life Cycle에 함께 참여한다.

#### **Security**

Policy as Code 등의 방법을 이용하여 Security Policy 역시 자동화 과정에 포함할 수 있다.

## **6) DevOps 생태계**

---

DevOps에서는 하나의 Tool이 모든 과정을 담당하는 것이 아니라 각 단계의 목적에 맞는 여러 Tool을 결합하여 Tool Chain을 구성한다.

### **Source Code와 Version Control**

- Git
- GitHub
- GitLab

Git을 이용하여 Source Code와 변경 이력을 관리하고 GitHub 또는 GitLab 등의 Platform을 이용하여 협업할 수 있다.

### **CI/CD**

- GitHub Actions
- GitLab CI/CD
- Jenkins
- Argo CD

GitHub Actions, GitLab CI/CD, Jenkins 등은 Build와 Test, Deployment Pipeline을 구성할 때 사용할 수 있다.

Argo CD는 Kubernetes 환경에서 Git을 기준으로 Application 상태를 동기화하는 GitOps 기반 Continuous Delivery Tool로 사용된다.

### **Test**

#### **Unit Test**

- JUnit
- pytest

#### **API Test**

- Postman

#### **Web UI Test**

- Selenium

#### **Performance / Load Test**

- JMeter
- k6

#### **Mobile Test**

- Appium

#### **Integration Test**

- Testcontainers

#### **Test Management**

- Jira + Xray

#### **Static Code Analysis**

- SonarQube

#### **Code Coverage**

- JaCoCo

### **Package 및 Container**

- Docker

Docker를 이용하여 Application과 실행에 필요한 환경을 Container Image로 Packaging할 수 있다.

### **Deploy 및 Orchestration**

- Docker
- Kubernetes
- Argo CD

Kubernetes는 Container Application의 배포, 확장, 상태 관리 등을 자동화하는 Orchestration Platform이다.

### **Issue 및 Project Management**

- Jira
- Mantis

Issue와 Bug, 작업 진행 상태 등을 관리할 수 있다.

### **DevOps Tool Chain 예시**

```text
Plan
 │
 ├─ Jira
 │
 ▼
Code
 │
 ├─ Git
 ├─ GitHub
 └─ GitLab
 │
 ▼
Build / CI
 │
 ├─ GitHub Actions
 ├─ GitLab CI/CD
 └─ Jenkins
 │
 ▼
Test
 │
 ├─ JUnit
 ├─ pytest
 ├─ Postman
 ├─ Selenium
 ├─ JMeter
 ├─ k6
 ├─ SonarQube
 └─ JaCoCo
 │
 ▼
Package
 │
 └─ Docker
 │
 ▼
Deploy
 │
 ├─ Kubernetes
 └─ Argo CD
 │
 ▼
Operate / Monitor
```

어떤 Tool을 사용하는지가 DevOps의 본질은 아니다.

중요한 것은 개발부터 운영까지의 전체 과정을 연결하고 반복 가능한 자동화 Process를 구성하는 것이다.

**정리**

- DevOps는 Development와 Operations의 협업을 강조하는 문화이자 업무 방식이다.
- 단순히 CI/CD Tool을 도입하는 것만으로 DevOps가 되는 것은 아니다.
- Plan → Code → Build → Test → Package → Release → Operate → Monitoring의 전체 Life Cycle을 지속적으로 반복한다.
- Git, Jenkins, GitHub Actions, Docker, Kubernetes 등은 이러한 Process를 구현하기 위한 도구이다.
- Tool 자체보다 조직 문화, 자동화, Feedback Cycle을 연결하는 것이 중요하다.

## **전체 정리**

---

> - Cloud Native는 현대적인 Cloud 환경에서 확장 가능하고 변화에 유연한 Application을 개발하고 운영하기 위한 접근 방식이다.
>
>- Container, Microservices, Service Mesh, Immutable Infrastructure, Declarative API 등이 Cloud Native를 구성하는 대표적인 기술과 설계 방식이다.
>
> - CNCF는 Cloud Native 관련 Open Source Project와 생태계를 지원한다.
> 
>- IT Service는 개발 방식, Application Architecture, Packaging 방식, Infrastructure가 함께 변화해 왔다.
>
>- Cloud Native 환경에서는 Container와 자동화를 이용하여 Infrastructure에 대한 종속성을 줄이고 지속적인 Delivery를 구현할 수 있다.
>
>- Kubernetes는 다양한 Infrastructure에서 Container를 일관된 방식으로 운영하기 위한 Platform을 제공한다.
>
>- Cloud Native의 주요 요소로 DevOps, Microservices, Containers, Continuous Delivery를 볼 수 있다.
>
>- Agile은 짧은 개발 주기, 협업, 변화 대응을 중요하게 생각한다.
>
>- ITIL은 IT Service Management를 위한 Best Practice 체계이며 ITIL 4에서는 Agile, Lean, DevOps와의 연계를 강화하였다.
>
>- DevOps는 개발과 운영을 하나의 Service Life Cycle로 연결하고 Hand-off와 반복적인 수작업을 줄이는 것을 목표로 한다.
>
>- DevOps Tool Chain은 Plan → Code → Build → Test → Package → Release → Operate → Monitoring의 반복적인 Cycle로 구성할 수 있다.
>
>- Git, CI/CD, Testing Tool, Docker, Kubernetes 등의 Tool은 DevOps Process를 구현하기 위한 수단이며 Tool 자체가 DevOps를 의미하는 것은 아니다.