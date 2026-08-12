---
title: 클라우드 네이티브의 핵심 요소 CI/CD와 Container
description: CI, Continuous Delivery, Continuous Deployment의 차이와 Container 기반 배포 흐름
date: 2026-08-11
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
---
## Pillars of Cloud Native

---

### CI/CD

#### 개요

CI/CD는 애플리케이션 개발 단계를 자동화하여 애플리케이션을 더 짧은 주기로 고객에게 제공하기 위한 방법이다.

새로운 코드를 기존 코드에 통합하는 과정에서 개발 및 운영에 발생할 수 있는 **Integration Hell** 문제를 줄이는 데 목적이 있다.

| 구분 | 의미 |
|---|---|
| CI (Continuous Integration) | 지속적 통합 |
| CD (Continuous Delivery) | 지속적 제공 |
| CD (Continuous Deployment) | 지속적 배포 |

#### 흐름

개발자가 코드를 작성한 뒤 저장소에 Push 또는 Upload하면 이후 Build, Test, Merge 등의 과정이 CI 파이프라인에서 수행된다.

| Development | CI |
|---|---|
| Coding → Push / Upload | Build → Test → Merge |
| Coding은 수동 | 대부분 자동화되며 일부 과정은 Manual일 수 있음 |

CI 이후에는 Acceptance Test와 Staging 배포를 거쳐 Production 환경에 배포한다.

**Continuous Delivery**

```text
Coding
  ↓
Push / Upload
  ↓
Build
  ↓
Test
  ↓
Merge
  ↓
Acceptance Test
  ↓
Deploy to Staging
  ↓
Deploy to Production (Manual)
  ↓
Smoke Test
````

Continuous Delivery에서는 Production에 배포할 수 있는 상태까지 자동화하지만, 실제 Production 배포는 수동으로 수행한다.

**Continuous Deployment**

```text
Coding
  ↓
Push / Upload
  ↓
Build
  ↓
Test
  ↓
Merge
  ↓
Acceptance Test
  ↓
Deploy to Staging
  ↓
Deploy to Production
  ↓
Smoke Test
```

Continuous Deployment에서는 검증을 통과한 변경 사항을 Production 환경까지 자동으로 배포한다.

#### **테스트 종류**

**CI 단계의 테스트**

CI에서 수행하는 테스트는 코드 검증과 정적 테스트를 포함한다.

예를 들어 다음 항목을 점검할 수 있다.

- 사용하지 않는 변수
- 사용하지 않는 패키지
- 코드 및 로직 문제

**Acceptance Test**

인수 테스트(Acceptance Test)는 개발된 애플리케이션이 고객의 요구사항에 부합하는지 확인하는 테스트이다.

**Smoke Test**

Smoke Test는 새로운 빌드나 배포판이 생성되었을 때 기본적인 기능이 정상적으로 동작하는지 빠르게 확인하는 테스트이다.

### **CI (Continuous Integration)**

CI는 개발팀이 작은 변경 사항을 구현하고 코드를 버전 제어 저장소(Repository)에 자주 체크인하도록 하는 코딩 철학이자 일련의 관행이다.

최신 애플리케이션은 다양한 플랫폼과 도구를 이용하여 개발되기 때문에 여러 개발자가 만든 변경 사항을 지속적으로 통합하고 검증하기 위한 메커니즘이 필요하다.

CI의 기술적 목표는 애플리케이션을 **빌드, 패키징, 테스트하는 일관되고 자동화된 방법을 구축하는 것**이다.

통합 프로세스의 일관성을 유지하면 개발자가 코드 변경을 더 자주 커밋할 수 있고, 공동 작업과 소프트웨어 품질을 향상시킬 수 있다.

소프트웨어 공학에서 지속적 통합은 품질 관리를 마지막 단계에서 한 번 수행하는 방식이 아니라, 작은 단위로 자주 통합하면서 지속적으로 품질 관리를 수행하는 프로세스이다.

이를 통해 소프트웨어의 품질을 높이고 배포에 걸리는 시간을 줄이는 데 초점을 맞춘다.

### **Continuous Delivery**

Continuous Delivery는 개발자가 애플리케이션에 적용한 변경 사항을 테스트한 뒤 Repository에 자동으로 업로드하고, 언제든 Production 환경에 배포할 수 있는 상태로 유지하는 방식이다.

Repository에는 Git 저장소나 Image Registry 등이 사용될 수 있다.

운영팀은 이 Repository에 저장된 결과물을 가져와 실제 Production 환경에 배포한다.

**목적**

- 개발팀과 비즈니스팀 간의 가시성 부족 문제 완화
- 개발팀과 운영팀 간의 커뮤니케이션 문제 감소
- 최소한의 노력으로 새로운 코드를 배포할 수 있는 상태 유지

Continuous Delivery에서는 Production 배포가 가능한 상태까지 자동화하지만 실제 배포 시점은 사람이 결정한다.

### **Continuous Deployment**

Continuous Deployment는 개발자의 변경 사항을 Repository에서 고객이 실제로 사용할 수 있는 Production 환경까지 자동으로 릴리즈하는 방식이다.

수동 배포 과정으로 인해 운영팀에 프로세스 과부하가 발생하거나, 애플리케이션 제공 속도가 늦어지는 문제를 줄이는 데 목적이 있다.

Continuous Deployment는 Continuous Delivery에서 제공하는 자동화 기반을 활용하고, 그 다음 단계인 Production 배포까지 자동화한다.

**정리**

- CI는 코드 변경 사항을 자주 통합하고 Build와 Test를 자동화하는 방식이다.
- Continuous Delivery는 Production에 배포 가능한 상태까지 자동화한다.
- Continuous Deployment는 Production 배포까지 자동화한다.
- Acceptance Test는 고객 요구사항 충족 여부를 확인한다.
- Smoke Test는 새로운 빌드나 배포 이후 기본 기능의 정상 동작 여부를 빠르게 확인한다.

### **Containers**

#### **개요**

Linux Container는 애플리케이션 실행에 필요한 파일과 실행 환경을 하나의 단위로 패키징하고, 다른 애플리케이션과 분리하여 실행할 수 있도록 하는 기술이다.

컨테이너화된 애플리케이션은 기능을 유지하면서 개발, 테스트, Production 환경 사이를 쉽게 이동할 수 있다.

또한 컨테이너 파이프라인에 보안을 적용하고 인프라를 보호함으로써 컨테이너 환경의 안정성, 확장성, 신뢰성을 확보할 수 있다.

#### **실행 구조 비교**

**가상화를 사용하지 않는 경우**

하나의 운영체제 위에 여러 애플리케이션을 직접 배치하여 실행한다.

```text
Application
Application
Application
    ↓
Operating System
    ↓
Hardware
```

각 애플리케이션이 동일한 운영체제 환경을 공유한다.

**KVM 가상화를 이용하는 경우**

운영체제 위에 Hypervisor를 배치하고, 그 위에 Guest OS를 설치한 뒤 애플리케이션을 실행한다.

```text
Application      Application
    ↓                ↓
Guest OS         Guest OS
    ↓                ↓
      Hypervisor
          ↓
    Operating System
          ↓
       Hardware
```

애플리케이션을 서로 분리하려면 여러 Guest OS를 구성해야 한다.

**Linux Container를 이용하는 경우**

운영체제 위에 여러 Container를 직접 배치하지만, 각 Container는 서로 격리된 환경에서 실행된다.

```text
Container
Container
Container
    ↓
Operating System
    ↓
Hardware
```

Guest OS를 각각 설치하지 않고도 애플리케이션을 분리할 수 있다는 점이 가상 머신 방식과의 주요 차이이다.

### **DevOps와 CI/CD에서의 Container 활용**

Container는 DevOps와 CI/CD를 구현하는 주요 기술 요소 중 하나로 활용된다.

개발자가 코드를 Push하면 다음과 같은 흐름으로 배포가 진행될 수 있다.

```text
Developer
    ↓
Push
    ↓
Code Repository
    ↓
Build Tool
    ↓
Docker Build
    ↓
Image Registry
    ↓
Kubernetes Deploy
```

개발자가 Code Repository에 코드를 Push하면 Build Tool이 애플리케이션을 빌드하고, Docker Image를 생성한다.

생성된 이미지는 Image Registry에 저장되고, 이후 Kubernetes 환경에 배포된다.


>**정리**
> - Cloud Native의 주요 요소에는 CI/CD와 Container가 포함된다.
>
> - CI는 코드 변경 사항을 지속적으로 통합하고 검증하는 과정이다.
>
> - Continuous Delivery는 Production에 배포 가능한 상태까지 자동화하고, 실제 Production 배포는 수동으로 수행한다.
>
> - Continuous Deployment는 Production 환경까지 자동으로 배포한다.
>
> - Acceptance Test는 고객 요구사항 충족 여부를 확인하고, Smoke Test는 배포 이후 기본 기능의 정상 동작 여부를 빠르게 확인한다.
>
> - Container는 애플리케이션과 실행 환경을 패키징하고 서로 격리하여 실행할 수 있도록 한다.
>
> - 가상 머신은 Guest OS를 각각 구성하지만, Container는 동일한 운영체제 환경을 공유하면서 격리된다.
>
> - CI/CD 파이프라인에서는 Code Repository, Build Tool, Docker Build, Image Registry, Kubernetes 등을 연결하여 배포 과정을 자동화할 수 있다.