---
title: 클라우드 네이티브 - Micro Serivce
description: Cloud Native 환경에서 비즈니스 민첩성을 높이기 위한 애플리케이션 구조와 Micro Service Architecture의 핵심 원리, 운영 방식, 주요 패턴
date: 2026-08-11
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
---
## 1 ) 비즈니스 민첩성과 Cloud Native

---

### 비즈니스 민첩성 (Business Agility)

인터넷 기업의 경쟁력 중 하나는 **새로운 서비스를 얼마나 빠르게 시장에 적용하고 개선할 수 있는가**이다.

이를 비즈니스 민첩성(Business Agility)이라고 한다.

기존 비즈니스에 새로운 기술과 아이디어를 결합하여 서비스를 빠르게 출시하고, 사용자 피드백을 지속적으로 반영하면서 서비스를 개선하는 것이 핵심이다.

Amazon과 Netflix 같은 기업은 Cloud를 적극적으로 활용하면서 이러한 방식을 실제 비즈니스 성과로 연결한 대표적인 사례이다.

#### 빠른 배포가 중요한 이유

서비스를 빠르게 개선하려면 코드 작성뿐 아니라 실제 사용자에게 변경 사항을 전달하는 **배포 주기 자체가 짧아야 한다.**

강의에서는 Amazon의 배포 속도가 2011년 약 11.6초 수준이었으며, 이후에는 초당 1.5회 이상, 즉 약 0.66초마다 서비스를 업데이트할 수 있는 수준까지 향상된 사례를 설명하였다.

배포 주기가 짧아지면 다음 과정을 빠르게 반복할 수 있다.

```text
서비스 개발
↓
배포
↓
사용자 피드백
↓
서비스 개선
↓
재배포
````

결국 비즈니스 민첩성은 단순히 개발 속도가 빠르다는 의미보다 **개발 → 배포 → 피드백 → 개선의 주기를 얼마나 짧게 반복할 수 있는가**와 관련된다.

### **Cloud가 비즈니스 민첩성을 높이는 이유**

과거에는 새로운 서비스를 시작하거나 기존 서비스를 확장하려면 서버와 네트워크 등 필요한 인프라를 먼저 준비해야 했다.

장비 구매와 설치에 시간이 필요했기 때문에 애플리케이션을 개발하더라도 인프라 준비가 서비스 출시 속도를 제한할 수 있었다.

Cloud에서는 필요한 컴퓨팅 자원을 빠르게 확보하고 확장할 수 있기 때문에 이러한 인프라 준비 시간을 줄일 수 있다.

```text
[기존 환경]

서비스 기획
   ↓
장비 구매
   ↓
인프라 구축
   ↓
애플리케이션 배포
```

```text
[Cloud 환경]

서비스 기획
   ↓
Cloud 자원 생성
   ↓
애플리케이션 배포
```

하지만 **애플리케이션을 Cloud에 올리는 것만으로 Cloud의 장점을 모두 활용할 수 있는 것은 아니다.**

### **Cloud에 맞는 애플리케이션 구조**

예를 들어 하나의 시스템에 여러 기능이 존재한다고 가정한다.

```text
회원
주문
결제
검색
```

이 중 검색 기능에만 사용자가 몰린다면 이상적인 방식은 **검색 서비스만 확장하는 것**이다.

하지만 애플리케이션 전체가 하나의 큰 덩어리로 구성되어 있다면 검색 기능 하나를 확장하기 위해 전체 애플리케이션을 함께 확장해야 할 수 있다.

```text
전체 애플리케이션
├── 회원
├── 주문
├── 결제
└── 검색  ← 트래픽 증가
```

이러한 구조에서는 Cloud가 자원을 탄력적으로 제공하더라도 애플리케이션 구조 때문에 특정 기능만 독립적으로 확장하기 어렵다.

따라서 Cloud의 탄력성을 효과적으로 활용하려면 시스템을 **작은 단위의 독립적인 서비스로 분리**할 필요가 있다.

```text
회원 서비스

주문 서비스

결제 서비스

검색 서비스  ← 필요한 서비스만 확장
```

### **Cloud Friendly와 Cloud Native**

Cloud 환경에서 실행되는 애플리케이션은 구조에 따라 Cloud Friendly와 Cloud Native로 구분하여 생각할 수 있다.

#### **Cloud Friendly**

Cloud Friendly는 기존 방식으로 개발한 애플리케이션을 **Cloud 환경에서도 실행할 수 있도록 구성한 형태**이다.

```text
기존 Application
       ↓
   Cloud Infra
```

서비스를 운영하는 것 자체에는 문제가 없지만, 애플리케이션이 하나의 덩어리로 구성되어 있다면 특정 기능만 독립적으로 확장하거나 배포하기 어렵다.

즉, **Cloud를 사용할 수는 있지만 Cloud의 특성을 충분히 활용하지 못하는 구조**이다.

#### **Cloud Native**

Cloud Native Application은 애플리케이션을 **독립적으로 분리하고 배포할 수 있는 작은 서비스 단위로 구성한 형태**이다.

```text
Service A ─┐
Service B ─┼─ Cloud Infra
Service C ─┘
```

각 서비스가 독립적으로 구성되기 때문에 필요한 부분만 확장하거나 새로운 버전을 배포할 수 있다.

따라서 Cloud가 제공하는 탄력성과 빠른 자원 공급 능력을 애플리케이션 수준에서도 활용할 수 있다.

### **Cloud Friendly에서 Cloud Native로**

두 구조의 가장 중요한 차이는 단순히 **Cloud에서 실행되는가**가 아니다.

```text
Cloud Friendly
→ Cloud에서 실행 가능

Cloud Native
→ Cloud의 특성을 활용하도록 설계
```

Cloud Friendly 애플리케이션도 Cloud에서 정상적으로 서비스를 제공할 수 있다.

하지만 비즈니스 민첩성을 높이기 위해서는 특정 기능을 독립적으로 확장하고 배포할 수 있어야 하므로 궁극적으로는 Cloud Native 구조로 전환하는 것을 지향한다.

|**구분**|**Cloud Friendly**|**Cloud Native**|
|---|---|---|
|Cloud 실행|가능|가능|
|서비스 구조|하나의 큰 단위로 구성될 수 있음|독립적인 작은 서비스로 구성|
|특정 기능 확장|어려움|독립적으로 가능|
|특정 기능 배포|어려움|독립적으로 가능|
|Cloud 활용|Cloud에 올려 사용하는 수준|Cloud의 탄력성을 구조적으로 활용|

> **정리**
>
> - 비즈니스 민첩성은 서비스를 빠르게 출시하고 사용자 피드백을 반영하여 지속적으로 개선하는 능력이다.
>
> - Cloud는 인프라 준비 시간을 줄여 서비스 개발과 배포 주기를 단축하는 데 유리하다.
>
> - 애플리케이션이 하나의 큰 덩어리로 구성되어 있으면 특정 기능만 독립적으로 확장하거나 배포하기 어렵다.
>
> - Cloud Friendly는 기존 애플리케이션을 Cloud 환경에서 실행할 수 있도록 구성한 형태이다.
>
> - Cloud Native는 서비스를 독립적인 단위로 분리하여 필요한 서비스만 확장하고 배포할 수 있도록 설계한 형태이다.
>
> - Cloud의 탄력성과 확장성을 효과적으로 활용하려면 Cloud Friendly에서 Cloud Native 구조로 전환하는 것이 중요하다.

## 2 ) Micro Service

---

### Monolithic과 Micro Service

#### Monolithic

Monolithic Architecture는 애플리케이션의 여러 기능을 **하나의 애플리케이션 및 배포 단위로 구성하는 일체형 구조**이다.

일반적으로 다음과 같은 3-Tier 구조로 설명할 수 있다.

```text
Client ↔ Server ↔ Storage
```

- **Client**: 사용자 인터페이스를 제공한다.
- **Server**: 비즈니스 로직을 처리한다.
- **Storage**: 애플리케이션의 데이터를 저장한다.

Monolithic은 여러 기능이 하나의 애플리케이션으로 묶여 있기 때문에 특정 기능에 변경이 발생하더라도 전체 애플리케이션을 다시 빌드하고 배포해야 하는 경우가 많다.

애플리케이션의 여러 인스턴스를 운영하는 경우에도 새로운 버전을 적용하려면 각 인스턴스에 변경된 애플리케이션을 배포해야 한다.

확장 방법으로는 서버의 CPU와 Memory 등의 사양을 높이는 **Scale-up**을 사용할 수 있으며, 동일한 Monolithic 애플리케이션 인스턴스를 여러 개 실행하는 **Scale-out**도 가능하다.

다만 특정 기능에만 부하가 집중되더라도 해당 기능만 독립적으로 확장하기 어려워 전체 애플리케이션 단위로 확장해야 할 수 있다는 한계가 있다.

#### Micro Service

Micro Service는 서버 측 애플리케이션을 여러 개의 독립적인 서비스로 분리하여 구성하는 방식이다.

```text
                    ┌─ Service A ↔ Storage A
Client ↔ Gateway ───┼─ Service B ↔ Storage B
                    └─ Service C ↔ Storage C
```

각 서비스는 별도의 프로세스나 인스턴스로 실행되며, 여러 서비스가 모여 하나의 비즈니스 애플리케이션을 구성한다.

서비스를 업무 기능 단위로 분리하고 각 서비스가 자신의 데이터를 관리하도록 구성하면 모듈의 경계를 명확하게 나눌 수 있다.

**특징**

- 필요한 서비스만 독립적으로 확장할 수 있다.
- 변경이 발생한 서비스만 빌드하고 배포할 수 있다.
- 전체 시스템을 다시 배포할 필요가 줄어 배포 주기를 단축할 수 있다.
- 서비스마다 서로 다른 언어와 데이터 저장 기술을 사용할 수 있다.
- 서비스별 소유권을 분리하여 서로 다른 팀이 개발과 운영을 담당할 수 있다.

| 구분 | Monolithic | Micro Service |
|---|---|---|
| 구성 | 하나의 애플리케이션 | 여러 개의 독립적인 서비스 |
| 배포 단위 | 전체 애플리케이션 | 개별 서비스 |
| 확장 단위 | 애플리케이션 전체 | 필요한 서비스 |
| 저장소 | 통합 저장소를 사용하는 경우가 많음 | 서비스별 데이터 소유를 지향 |
| 기술 선택 | 전체 애플리케이션의 기술 스택에 영향을 받음 | 서비스별 기술 선택 가능 |
| 팀 구성 | 기능별 조직 간 협업이 필요할 수 있음 | 비즈니스 기능 중심의 독립적인 팀 구성 가능 |

### SOA와 Micro Service

#### 모듈화의 발전

소프트웨어는 복잡성을 줄이고 재사용성과 유지보수성을 높이기 위해 지속적으로 더 작은 단위로 모듈화되어 왔다.

```text
구조적 방법론
↓
객체 지향 방법론
↓
CBD
↓
SOA
↓
Micro Service
```

**구조적 방법론**

기능을 하향식으로 분해하면서 시스템을 설계하는 방식이다.

**객체 지향 방법론**

데이터와 행위를 객체 단위로 캡슐화하여 시스템을 모듈화한다.

**CBD (Component Based Development)**

기능별로 재사용할 수 있는 컴포넌트(Component)를 조합하여 시스템을 개발하는 방식이다.

**SOA (Service Oriented Architecture)**

컴포넌트보다 더 큰 범위에서 비즈니스적으로 의미 있고 완결된 기능을 **서비스(Service)** 단위로 구성하고 연계하는 아키텍처이다.

CBD와 SOA 역시 독립적인 컴포넌트 또는 서비스를 조합하여 하나의 시스템을 만든다는 점에서 Micro Service와 공통점이 있다.

Micro Service는 이러한 서비스 지향 개념이 Cloud 인프라, 자동화된 배포, DevOps 등의 기술 및 개발 방식과 결합하면서 발전한 형태로 이해할 수 있다.

Micro Service를 기반으로 시스템을 설계하고 개발하는 아키텍처를 **MSA (Microservice Architecture)** 라고 한다.

#### MSA의 특징

Microservice라는 용어는 Amazon, Netflix와 같은 인터넷 기업이 대규모 서비스를 운영하면서 사용한 아키텍처의 공통적인 특징을 정리하는 과정에서 널리 알려졌다.

MSA의 주요 특징은 다음과 같다.

- 하나의 애플리케이션을 여러 개의 작은 서비스 집합으로 구성한다.
- 각 서비스는 독립적인 프로세스에서 실행될 수 있다.
- 서비스 간에는 HTTP API나 Messaging 등의 비교적 가벼운 통신 방식을 사용한다.
- 서비스를 비즈니스 기능 단위로 구성한다.
- 자동화된 배포 체계를 이용하여 각 서비스를 독립적으로 배포한다.
- 중앙 집중적인 관리를 최소화하고 각 서비스에 자율성을 부여한다.
- 서비스별로 서로 다른 언어와 데이터 저장 기술을 선택할 수 있다.
- 서비스가 자신의 데이터를 소유하도록 하여 다른 서비스와의 결합도를 낮춘다.
- 서비스 간에는 명시적인 API나 메시지를 통해 통신한다.

서비스가 서로 독립적이라면 다른 서비스와 약속한 API 계약을 유지하는 범위에서 내부 구현 언어나 저장 기술을 자유롭게 선택할 수 있다.

이를 다음과 같이 표현할 수 있다.

**Polyglot Programming**

서비스마다 목적에 적합한 서로 다른 프로그래밍 언어나 개발 기술을 사용하는 방식이다.

**Polyglot Persistence**

서비스마다 데이터 특성에 적합한 서로 다른 데이터 저장 기술을 사용하는 방식이다.

예를 들어 한 서비스는 RDBMS를 사용하고 다른 서비스는 NoSQL이나 Redis를 사용할 수 있다.

#### SOA와 MSA의 차이

SOA와 MSA를 단순히 완전히 다른 개념으로 구분하기는 어렵다.

둘 모두 서비스 단위로 시스템을 구성한다는 공통점이 있다.

다만 전통적인 SOA 구현에서는 여러 서비스가 공통 데이터베이스나 ESB(Enterprise Service Bus)와 같은 중앙 집중적인 통합 요소를 공유하는 형태가 많이 사용되었으며, 이 경우 서비스 간 결합도가 높아질 수 있었다.

Micro Service에서는 서비스의 독립성을 강화하기 위해 다음 원칙을 중요하게 다룬다.

**서비스의 데이터 캡슐화**

서비스가 자신의 데이터를 소유하며, 다른 서비스가 해당 저장소를 직접 접근하지 않도록 구성한다.

```text
잘못된 접근

Service A ──────────→ Storage B
```

```text
권장 구조

Service A → API / Message → Service B → Storage B
```

다른 서비스의 데이터가 필요한 경우 해당 서비스를 통해 접근하도록 하여 저장소의 구현을 캡슐화한다.

**가벼운 통신 방식**

서비스 간 통신에는 REST API, gRPC, Messaging 등 비교적 가벼운 통신 방식을 사용할 수 있다.

이러한 구조를 통해 서비스 간 결합도를 낮추고 각 서비스를 독립적으로 변경하거나 배포할 수 있도록 한다.

### Micro Service를 위한 변화

Micro Service는 단순히 애플리케이션을 작은 서비스로 나누는 것만으로 완성되지 않는다.

조직, 개발 방식, 배포 방식, 데이터 관리, 장애 대응 등 여러 영역이 함께 변화해야 한다.

#### 조직의 변화

기존처럼 개발, 데이터베이스, 운영 등 기술 분야별 부서를 중심으로 조직을 구성하기보다 **비즈니스 기능을 중심으로 팀을 구성**할 수 있다.

하나의 팀이 특정 서비스의 개발과 운영을 함께 담당한다.

```text
기존

개발팀
DB팀
운영팀
↓
여러 팀이 하나의 기능을 함께 처리
```

```text
Micro Service

주문팀 → 주문 서비스
결제팀 → 결제 서비스
배송팀 → 배송 서비스
```

서비스에 대한 의사결정을 하나의 팀에서 수행할 수 있으므로 다른 팀과 조율해야 하는 범위를 줄일 수 있다.

다만 Micro Service라고 해서 다른 팀과의 의사소통이 없어지는 것은 아니며, 서비스 간 API 계약이나 비즈니스 프로세스에 대한 협업은 여전히 필요하다.

#### 관리 체계의 변화

각 서비스와 팀에 일정 수준의 자율성을 부여하는 **분권형 관리 구조**를 지향한다.

서비스 특성에 따라 적절한 언어, 프레임워크, 데이터 저장 기술을 선택할 수 있으며 이를 Polyglot한 환경이라고 표현한다.

#### 개발 생명 주기의 변화

기존에는 애플리케이션 개발을 하나의 **Project**로 바라보는 경우가 많았다.

필요한 인력이 한시적으로 모여 장기간 개발한 뒤 개발이 완료되면 운영 조직에 시스템을 넘기는 방식이다.

```text
요구사항
↓
장기간 개발
↓
완료
↓
운영 조직에 인계
```

개발 조직과 운영 조직이 분리되어 있으면 프로젝트 진행 중 발생한 새로운 아이디어나 요구사항 변경을 빠르게 반영하기 어려울 수 있다.

Micro Service와 Cloud Native 환경에서는 소프트웨어를 일회성 프로젝트가 아니라 지속적으로 발전시키는 **Product**로 바라보는 방식을 지향한다.

폭포수 모델이나 한 번에 대규모 기능을 개발하는 Big Bang 방식보다는 점진적이고 반복적인 Agile 개발 방식을 사용할 수 있다.

예를 들어 2~3주 정도의 Sprint를 반복하면서 다음 과정을 수행한다.

```text
개발
 ↓
배포
 ↓
사용자 피드백
 ↓
개선
 ↓
다음 Sprint
```

소프트웨어를 고정된 요구사항을 모두 만족하면 끝나는 결과물이 아니라 **요구사항 변화에 따라 지속적으로 개선되는 제품**으로 바라본다.

#### 개발 환경의 변화

Micro Service는 각 서비스를 독립적으로 배포한다.

Monolithic 애플리케이션처럼 배포 단위가 하나라면 수동 작업으로 관리할 수 있는 범위가 상대적으로 넓지만, 서비스가 수십 또는 수백 개로 늘어나면 모든 서비스를 수동으로 관리하고 배포하기 어렵다.

소프트웨어 개발 과정은 크게 다음과 같이 나눌 수 있다.

```text
개발 환경 준비
      ↓
소프트웨어 개발
      ↓
Build / Test / Deploy
```

Cloud 인프라를 이용하면 개발 및 실행에 필요한 인프라를 빠르게 준비할 수 있다.

또한 Build, Test, Deploy 과정을 자동화함으로써 개발과 운영의 반복적인 작업을 줄일 수 있다.

이러한 자동화 환경은 개발과 운영을 함께 수행하는 DevOps를 지원하는 중요한 기반이 된다.

#### 배포 파이프라인 자동화

Micro Service 환경에서는 각 서비스가 독립적으로 변경되고 배포되므로 Build와 Deploy 과정의 자동화가 중요하다.

```text
Build
(Compile / Unit Test)
        ↓
개발 환경 배포
(기능 테스트)
        ↓
테스트 환경 배포
(통합 테스트)
        ↓
Staging 환경 배포
(인수 테스트 / 성능 테스트 / 비기능 테스트)
        ↓
Production 환경 배포
```

**Staging 환경**

실제 Production과 최대한 유사한 환경을 구성하고 운영 환경에 배포하기 전에 다음과 같은 요소를 검증한다.

- 기능
- Security
- 성능
- 장애 대응
- 기타 비기능 요구사항

서비스의 수가 증가하면 배포 환경과 인프라 역시 빠르게 증가한다.

따라서 인프라 설정을 사람이 반복해서 수행하기보다 소프트웨어 코드처럼 정의하여 관리하는 **IaC (Infrastructure as Code)** 를 활용할 수 있다.

IaC를 이용하면 인프라 설정을 버전 관리하고 반복적으로 동일한 환경을 구성할 수 있다.

### 분권형 데이터 관리

#### 서비스별 저장소

Monolithic 애플리케이션에서는 여러 비즈니스 기능이 하나의 통합 데이터베이스를 사용하는 경우가 많다.

```text
Service Logic A ─┐
Service Logic B ─┼─ Shared Database
Service Logic C ─┘
```

Micro Service에서는 서비스의 독립성을 높이기 위해 **Database per Service** 형태를 사용할 수 있다.

```text
Service A ↔ Database A

Service B ↔ Database B

Service C ↔ Database C
```

각 서비스는 자신의 저장소를 소유하고 다른 서비스는 해당 저장소를 직접 접근하지 않는다.

다른 서비스의 데이터가 필요하면 해당 서비스가 제공하는 API나 Event를 이용한다.

각 서비스는 데이터 특성에 따라 적합한 저장 기술을 선택할 수 있으므로 Polyglot Persistence를 적용할 수 있다.

#### RDBMS와 데이터 정규화

RDBMS에서는 정규화를 통해 불필요한 데이터 중복을 줄이고 데이터의 삽입·수정·삭제 과정에서 발생할 수 있는 이상 현상(Anomaly)을 줄일 수 있다.

> **RDBMS와 정규화**
>
> - 불필요한 데이터 중복 최소화
> - 데이터 무결성 및 일관성 관리
> - 데이터 간 종속 관계를 체계적으로 표현
> - 삽입·수정·삭제 이상 현상 감소

과거보다 Storage 비용이 낮아지고 Network 환경이 발전하면서 일부 분산 시스템에서는 성능과 독립성을 위해 데이터의 복제나 중복을 의도적으로 허용하기도 한다.

그러나 이것이 정규화가 더 이상 필요하지 않다는 의미는 아니다.

Micro Service에서는 서비스 독립성을 확보하기 위해 서비스별 저장소를 구성하면서 일부 데이터가 여러 서비스에 중복 저장될 수 있으며, 이로 인해 **분산 데이터의 일관성 문제**가 발생한다.

### 분산 트랜잭션과 데이터 일관성

#### 2단계 커밋의 한계

하나의 데이터베이스에서는 ACID Transaction을 이용하여 여러 작업을 하나의 Transaction으로 처리할 수 있다.

하지만 Micro Service에서는 저장소가 서비스별로 분리되어 있기 때문에 여러 저장소에 걸친 Transaction을 하나로 처리하기 어렵다.

분산 Transaction을 처리하는 전통적인 방법으로 **2PC (Two-Phase Commit)** 가 있다.

그러나 여러 서비스를 하나의 분산 Transaction으로 묶으면 각 서비스가 서로의 상태에 의존하게 되어 독립성과 가용성에 영향을 줄 수 있다.

또한 모든 데이터 저장 기술이 동일한 형태의 분산 Transaction을 지원하는 것도 아니다.

따라서 Micro Service에서는 2PC로 모든 서비스를 하나의 Transaction으로 묶기보다 **각 서비스의 Local Transaction을 독립적으로 처리하고 서비스 간 일관성을 별도로 관리하는 방식**을 사용할 수 있다.

#### 결과적 일관성 (Eventual Consistency)

분산 시스템에서는 모든 서비스의 데이터가 항상 같은 순간에 즉시 일치하도록 만들기 어려울 수 있다.

따라서 일정 시간 동안 일부 데이터의 상태가 서로 다를 수 있지만, 새로운 변경이 없다면 **최종적으로 시스템이 일관된 상태에 도달하도록 설계하는 방식**을 결과적 일관성(Eventual Consistency)이라고 한다.

```text
시간 T1

Order Service   → 주문 완료
Delivery Service → 아직 배송 정보 없음


시간 T2

Order Service   → 주문 완료
Delivery Service → 배송 준비


결과적으로 비즈니스 상태가 일관된 상태에 도달
```

#### Saga Pattern

Saga는 여러 Micro Service에 걸친 하나의 비즈니스 작업을 여러 개의 **Local Transaction**으로 분리하여 수행하는 패턴이다.

각 서비스는 자신의 Local Transaction만 처리한다.

```text
Transaction A
     ↓
Transaction B
     ↓
Transaction C
```

중간 단계가 실패하면 이미 수행된 작업을 되돌리기 위한 **Compensating Transaction(보상 트랜잭션)** 을 실행하여 비즈니스 정합성을 맞춘다.

```text
주문 생성
   ↓
결제 성공
   ↓
배송 실패
   ↓
결제 취소
   ↓
주문 취소
```

Saga는 크게 Choreography 방식과 Orchestration 방식으로 구현할 수 있다.

#### Queue를 이용한 주문·배송 처리 사례

주문 서비스와 배송 서비스를 분리한 경우 Message Queue를 이용하여 비동기적으로 Transaction을 연결할 수 있다.

```text
주문 서비스
    ↓
주문 처리 Local Transaction
    ↓
주문 이벤트 발행
    ↓
Message Queue
    ↓
배송 서비스
    ↓
배송 처리 Local Transaction
```

배송 처리 중 오류가 발생하면 다음과 같이 처리할 수 있다.

```text
배송 서비스
    ↓
배송 처리 실패
    ↓
배송 실패 이벤트 발행
    ↓
Message Queue
    ↓
주문 서비스
    ↓
주문 취소 보상 Transaction
```

이 방식에서는 하나의 거대한 분산 Transaction으로 모든 서비스를 묶지 않고 각 서비스의 Local Transaction과 Event를 이용하여 전체 비즈니스 정합성을 관리한다.

### 실패를 고려한 설계

분산 시스템에서는 Network, Server, Application, 외부 API 등 다양한 요소에서 장애가 발생할 수 있다.

따라서 **장애가 절대로 발생하지 않는 시스템**을 목표로 하기보다 장애가 발생하더라도 전체 시스템으로 확산되지 않고 복구할 수 있도록 설계할 필요가 있다.

이를 **내결함성(Fault Tolerance)** 관점에서 생각할 수 있다.

이를 위해서는 다음과 같은 환경이 필요하다.

- 다양한 장애 상황을 검증하는 테스트
- 장애 발생 여부를 확인할 수 있는 Monitoring
- 장애를 빠르게 탐지하는 체계
- 장애가 다른 서비스로 전파되지 않도록 하는 격리 구조
- 장애 발생 후 정상 상태로 회복할 수 있는 복구 전략

#### Circuit Breaker Pattern

Circuit Breaker는 전기 회로의 차단기처럼 장애가 발생하는 외부 서비스에 대한 요청을 일정 시간 차단하여 **연쇄 장애(Cascading Failure)** 를 방지하는 패턴이다.

예를 들어 다음 구조가 있다고 가정한다.

```text
주문 서비스
    ↓
결제 서비스
    ↓
카드사 API
```

결제 서비스에 장애가 발생했는데 주문 서비스가 계속 요청을 보내면 다음과 같은 자원이 누적되어 고갈될 수 있다.

- Thread
- Connection
- CPU
- Memory

Circuit Breaker는 일정한 실패 조건을 감지하면 더 이상 장애 서비스로 요청을 보내지 않고 빠르게 실패를 반환한다.

일반적인 상태는 다음과 같이 표현한다.

```text
Closed
  ↓ 실패 누적
Open
  ↓ 일정 시간 후
Half-Open
  ↓
성공 → Closed
실패 → Open
```

핵심은 **장애가 발생한 서비스를 계속 호출하지 않고 일시적으로 호출을 차단하여 장애가 전체 시스템으로 전파되는 것을 막는 것**이다.

**구현 기술**

- Resilience4j
- Spring Cloud CircuitBreaker
- Istio / Envoy 등의 Traffic Management 기능

**사용할 수 있는 환경**

- AWS Lambda → 외부 API
- EKS / Kubernetes → 다른 Micro Service
- API Gateway → Backend Service
- MSA 서비스 간 REST / gRPC 호출
- 외부 결제·인증·배송 API
- Database / Redis 등 외부 의존 서비스

#### Chaos Monkey

Netflix는 장애 상황에서도 시스템이 정상적으로 대응할 수 있는지 검증하기 위해 **Chaos Monkey**를 개발하였다.

Chaos Monkey는 Production 환경의 VM이나 Container Instance를 의도적으로 종료하여 실제 장애 상황을 발생시키고 시스템의 Resilience를 검증하는 Chaos Engineering 도구이다.

```text
정상 시스템
   ↓
의도적인 Instance 장애 발생
   ↓
자동 복구 / 우회 / 확장 확인
```

### Reactive System

현대적인 분산 애플리케이션이 갖추어야 할 특성을 정리한 문서 중 하나가 **Reactive Manifesto(리액티브 선언문)** 이다.

Reactive Manifesto는 다음 네 가지 특성을 강조한다.

| 요소 | 의미 |
|---|---|
| Responsive | 응답성 |
| Resilient | 탄력성·회복성 |
| Elastic | 유연성 |
| Message Driven | 메시지 구동 |

#### Responsive

사용자에게 빠르고 일관된 응답을 제공하는 특성이다.

단순히 평균 응답 시간이 빠른 것뿐 아니라 문제가 발생했을 때 이를 신속하게 탐지하고 적절하게 대응할 수 있어야 한다.

#### Resilient

일부 구성 요소에 장애가 발생하더라도 전체 시스템이 함께 중단되지 않고 정상적인 서비스를 지속하거나 빠르게 회복할 수 있는 특성이다.

장애 격리, 복제, 복구 등의 방법을 이용할 수 있다.

#### Elastic

서비스 사용량 변화에 따라 필요한 자원을 증가시키거나 감소시켜 일정한 수준의 응답성을 유지하는 특성이다.

```text
트래픽 증가 → 자원 증가

트래픽 감소 → 자원 감소
```

#### Message Driven

구성 요소 사이에서 **비동기 메시지 전달**을 사용하여 느슨한 결합, 장애 격리, 위치 투명성을 확보하는 특성이다.

즉, 논블로킹 통신을 지양하는 것이 아니라 **비동기적이고 느슨하게 결합된 통신 구조를 지향**한다.

네 가지 요소는 서로 독립적인 특징이 아니라 상호 보완적으로 Reactive System을 구성한다.

### 강결합에서 느슨한 결합으로

과거에는 애플리케이션의 구성 요소를 특정 Vendor의 제품군에 강하게 의존하여 구축하는 경우가 많았다.

```text
Application
    ↓
Vendor Framework
    ↓
Vendor Middleware
    ↓
Vendor Infrastructure
```

검증된 Vendor의 제품군을 사용함으로써 품질과 지원을 확보할 수 있다는 장점이 있지만 특정 기술에 대한 의존도가 높아질 수 있다.

특정 기술이나 Vendor에 지나치게 종속되면 다른 기술로 변경하기 어려워지는 **Vendor Lock-in** 문제가 발생할 수 있다.

Cloud 환경에서는 다양한 Open Source 및 Open Source 기반 상용 제품을 조합하여 아키텍처를 구성할 수 있다.

따라서 최근 아키텍처 설계에서는 특정 하나의 Vendor 제품군만 사용하는 것보다 요구사항에 맞는 여러 솔루션을 선택하고 조합하는 경우도 많다.

이는 아키텍처가 다음과 같이 변화하는 과정으로 이해할 수 있다.

```text
강하게 결합된 Monolithic Architecture
               ↓
교체 가능한 구성 요소
               ↓
느슨하게 결합된 Micro Service Architecture
```

각 구성 요소는 명확한 인터페이스를 기준으로 연결하고 필요한 경우 다른 구현체로 대체할 수 있도록 구성하는 것을 지향한다.

### MSA 구성 요소

MSA는 Micro Service 코드만으로 구성되지 않는다.

서비스를 실행하고 배포하며 관찰하기 위한 다양한 인프라와 플랫폼 요소가 필요하다.

#### 인프라

Micro Service를 어떤 환경에서 실행할 것인지 결정한다.

- Public Cloud
- Private Cloud
- Bare Metal
- Virtual Machine
- Container
- Container Orchestration

#### Backing Service

Backing Service는 애플리케이션이 Network를 통해 사용하는 외부 의존 서비스를 의미한다.

**Persistence**

데이터를 영구적으로 저장한다.

- RDBMS
- NoSQL

**Cache**

자주 사용하는 데이터를 빠르게 제공하기 위한 Cache를 구성한다.

- Redis

**Message Broker**

서비스 사이에서 Message 또는 Event를 전달한다.

- Kafka
- RabbitMQ
- Queue

### Telemetry와 Observability

Micro Service는 서비스가 여러 개로 분산되어 있기 때문에 하나의 시스템에서 다음 문제가 발생한다.

- 여러 서비스에 분산된 Log를 어떻게 모을 것인가?
- 하나의 요청이 어떤 서비스를 거쳤는지 어떻게 확인할 것인가?
- 각 서비스와 Node의 상태를 어떻게 Monitoring할 것인가?

따라서 **Log, Trace, Metric**을 통합적으로 관리할 필요가 있다.

#### Logging

각 서비스에서 생성되는 Log를 중앙에서 수집하고 검색할 수 있도록 구성한다.

대표적인 구성은 다음과 같다.

**ELK**

```text
Elasticsearch
+ Logstash
+ Kibana
```

**EFK**

```text
Elasticsearch
+ Fluentd
+ Kibana
```

#### Distributed Tracing

Client의 하나의 요청이 여러 Micro Service를 순차적으로 호출하는 경우 전체 요청의 흐름을 추적해야 한다.

```text
Client
  ↓
Service A
  ↓
Service B
  ↓
Service C
```

각 서비스 호출에 대한 Trace와 Span을 연결하여 어떤 구간에서 지연이나 장애가 발생했는지 확인한다.

관련 기술은 다음과 같다.

- Micrometer Tracing
- OpenTelemetry
- Zipkin
- Jaeger

Spring Cloud Sleuth는 과거 Spring 기반 분산 추적에 사용되었으나 Spring Boot 3.x 이후에는 핵심 기능이 Micrometer Tracing으로 이전되었다.

#### Monitoring

서비스와 인프라의 상태를 지속적으로 수집하고 확인한다.

예를 들어 다음 항목을 Monitoring할 수 있다.

- CPU
- Memory
- Application 상태
- Node 상태
- Network I/O
- Disk 사용량
- HPA 동작 상태
- Request 처리량
- Error Rate

대표적으로 Prometheus와 Grafana를 함께 사용할 수 있다.

Cloud Native 환경에서는 다음과 같은 구성을 조합할 수도 있다.

```text
Prometheus + Grafana
OpenTelemetry
EFK
Jaeger
```

각 도구가 동일한 역할을 수행하는 것은 아니며 Metric, Log, Trace 등의 역할을 나누어 Observability 환경을 구성한다.

### CI/CD 구성 요소

Micro Service는 독립적인 Build와 Deploy가 반복적으로 발생하기 때문에 CI/CD 자동화가 중요하다.

관련 기술의 예는 다음과 같다.

| 도구 | 역할 |
|---|---|
| Git | 분산 버전 관리 시스템 |
| Jenkins | CI/CD 자동화 |
| Gradle | Build Tool |
| Maven | Build Tool |
| JUnit | Unit Test |
| SonarQube | 정적 코드 및 품질 분석 |
| JaCoCo | Java Code Coverage 측정 |
| Harbor | Container Image Registry |
| Nexus Repository | Package 및 Build Artifact 저장소 |
| Helm | Kubernetes Package Manager |

### Cloud 인프라 서비스

#### IaaS

IaaS(Infrastructure as a Service)는 Compute, Network, Storage 등의 인프라 자원을 서비스 형태로 제공한다.

**예시**

- AWS EC2
- Google Cloud Compute Engine
- Azure Virtual Machines

#### Container 관련 Managed Service

Container 또는 Kubernetes 기반 애플리케이션을 운영할 수 있도록 관리형 환경을 제공한다.

**예시**

- AWS ECS
- AWS EKS
- Google Kubernetes Engine(GKE)
- Azure Kubernetes Service(AKS)

이러한 서비스를 넓은 의미에서 CaaS(Container as a Service) 범주로 설명하기도 하지만, 각 Cloud Provider가 모든 서비스를 공식적으로 CaaS라는 동일한 제품 분류로 정의하는 것은 아니다.

#### PaaS

PaaS(Platform as a Service)는 인프라뿐 아니라 애플리케이션을 개발하고 실행하기 위한 Runtime과 관리 환경까지 제공하는 서비스 모델이다.

**예시**

- Azure App Service
- Google App Engine
- AWS Elastic Beanstalk
- Cloud Foundry
- Heroku

### MSA 플랫폼 패턴

인프라를 준비한 이후에는 여러 Micro Service를 운영하고 관리하기 위한 플랫폼 구조가 필요하다.

#### DevOps 환경과 배포 Pipeline

서비스의 Build, Test, Packaging, Deployment 과정을 자동화하는 환경을 구성한다.

```text
Source
  ↓
Build
  ↓
Test
  ↓
Package
  ↓
Registry
  ↓
Deploy
```

#### Service Registry와 Service Discovery

Cloud와 Container 환경에서는 서비스 Instance가 Scale-out되거나 재시작되면서 IP 주소가 동적으로 변경될 수 있다.

```text
Service A

10.0.0.10
      ↓ 재시작
10.0.1.27
```

Client가 각 Instance의 IP를 직접 알고 호출하는 방식은 관리하기 어렵다.

**Service Registry**

Service 이름과 현재 접근 가능한 Instance 정보를 관리한다.

```text
order-service
 ├─ 10.0.1.10
 ├─ 10.0.1.11
 └─ 10.0.1.12
```

**Service Discovery**

호출하려는 Service의 위치를 Registry 등에서 찾아 실제 Instance에 연결하는 과정이다.

Instance가 여러 개이면 Load Balancing과 함께 사용하여 요청을 적절하게 분산할 수 있다.

과거 Netflix OSS에서는 다음과 같은 기술이 사용되었다.

- Zuul: Gateway 및 Routing
- Ribbon: Client-side Load Balancing

Ribbon은 현재 Maintenance Mode이므로 현대적인 구현을 설명할 때에는 역사적인 Netflix OSS 사례로 이해하는 것이 적절하다.

Kubernetes에서는 **Service와 DNS(CoreDNS)** 를 통해 Service Discovery를 제공할 수 있다.

#### API Gateway Pattern

Client가 여러 Micro Service를 각각 직접 호출하면 복잡한 호출 관계가 형성될 수 있다.

```text
Client ─→ Service A
      ├─→ Service B
      ├─→ Service C
      └─→ Service D
```

API Gateway는 외부 요청을 위한 단일 진입점을 제공한다.

```text
                  ┌→ Service A
Client → Gateway ─┼→ Service B
                  └→ Service C
```

Gateway에서는 다음과 같은 기능을 수행할 수 있다.

- Routing
- 인증 및 인가
- Rate Limiting
- Monitoring
- Trace 연계
- 장애 대응
- Backend Service 선택

관련 기술에는 다음이 있다.

- Spring Cloud Gateway
- Cloud Provider의 API Gateway 서비스
- Kubernetes Gateway / Ingress 기반 구성
- Istio Gateway

Kubernetes의 Service와 Ingress 자체를 일반적인 API Gateway와 완전히 동일한 개념으로 보기는 어렵고, 외부 Traffic Routing을 구성하는 기반 요소로 이해하는 것이 적절하다.

#### BFF Pattern

최근에는 Web, Mobile, IoT 등 Client의 종류가 다양하다.

각 Client가 필요로 하는 데이터와 API 형태가 다를 수 있기 때문에 하나의 Backend API를 모든 Client에 동일하게 제공하면 불필요한 데이터나 복잡한 Client Logic이 발생할 수 있다.

BFF(Backend For Frontend)는 **Client 종류마다 최적화된 Backend 또는 Gateway 계층을 구성하는 패턴**이다.

```text
Web Client    → Web BFF    ─┐
Mobile Client → Mobile BFF ─┼→ Micro Services
Other Client  → Other BFF  ─┘
```

### 외부 구성 저장소 패턴

Cloud 환경에서는 다음과 같은 설정값이 자주 변경될 수 있다.

- Database 연결 정보
- 외부 API 주소
- File Storage 정보
- Service Endpoint
- Application 설정

이러한 정보를 애플리케이션 코드나 Image에 직접 포함하면 설정을 변경할 때 애플리케이션을 다시 Build 또는 Deploy해야 할 수 있다.

여러 Micro Service가 동일한 설정을 사용한다면 서비스별 설정이 서로 달라지는 문제도 발생할 수 있다.

따라서 **환경별 설정을 애플리케이션 코드에서 분리하여 외부에서 관리**할 수 있다.

```text
Configuration Repository
          ↓
 ┌────────┼────────┐
 ↓        ↓        ↓
Service A Service B Service C
```

구현 방법의 예는 다음과 같다.

- Git Repository + Spring Cloud Config
- Kubernetes ConfigMap
- 외부 Configuration Service

Kubernetes의 ConfigMap은 환경별 설정을 Container Image에서 분리하는 데 사용할 수 있다.

### 인증과 인가 패턴

각 Micro Service가 동일한 인증 및 인가 기능을 반복해서 구현하면 중복이 발생한다.

이를 줄이기 위해 인증 정보를 중앙에서 관리하거나 Gateway 계층에서 공통 처리를 수행할 수 있다.

#### 중앙 집중식 Session 관리

각 서비스의 Local Memory에 Session을 저장하는 대신 여러 Instance가 공유할 수 있는 저장소에 Session을 보관한다.

```text
Service A ─┐
Service B ─┼→ Redis / Shared Session Store
Service C ─┘
```

Session Store의 예는 다음과 같다.

- Redis
- Memcached

#### Token 기반 인증

Token 기반 방식에서는 Client가 인증 결과로 발급받은 Token을 보관하고 요청마다 서버에 전달한다.

```text
Client
  ↓ Token
API Gateway / Service
```

JWT(JSON Web Token)는 Token을 표현하는 방법 중 하나이다.

JWT 자체가 Session을 중앙 서버에 저장하는 방식과 반드시 함께 사용되는 것은 아니며, **Session 기반 인증과 Token 기반 인증은 별개의 접근 방식**으로 이해해야 한다.

#### API Gateway와 인증

API Gateway에서 공통적인 인증을 수행한 뒤 내부 Service로 인증 정보를 전달하는 구조를 사용할 수 있다.

```text
Client
  ↓
API Gateway
  ↓ 인증/인가
Micro Service
```

### Service Mesh Pattern

Micro Service가 증가하면 각 서비스에 다음과 같은 공통 Network 기능을 반복해서 구현해야 하는 문제가 발생할 수 있다.

- Service Discovery
- Routing
- Load Balancing
- Retry
- Circuit Breaking
- Security
- Telemetry
- Trace

Service Mesh는 이러한 **Service-to-Service 통신의 공통 기능을 애플리케이션 비즈니스 로직과 분리하여 Infrastructure 계층에서 처리하는 방식**이다.

대표적인 구현체로 Istio가 있다.

#### Istio Sidecar Mode

Istio의 Sidecar Mode에서는 애플리케이션 Container와 별도로 Envoy Proxy를 함께 배치한다.

```text
Pod
├─ Application Container
└─ Envoy Sidecar Proxy
```

Service 간 Traffic은 Proxy를 통해 전달되며 다음과 같은 기능을 적용할 수 있다.

- Service-to-Service Traffic 관리
- Routing
- Load Balancing
- Circuit Breaking
- Security
- Telemetry

Istio는 Sidecar Mode뿐 아니라 Sidecar Proxy를 각 Pod에 삽입하지 않는 Ambient Mode도 지원하므로 **Istio = 반드시 Sidecar 구조**라고 이해해서는 안 된다.

### MSA 애플리케이션 패턴

#### Frontend 구성

Frontend 역시 하나의 거대한 애플리케이션으로 구성할 수 있다.

**Monolithic Frontend**

Frontend 전체를 하나의 Application으로 구성한다.

Micro Service와 유사하게 Frontend를 기능별로 분리하는 방법도 있다.

**UI Composition / Micro Frontend**

Frontend를 업무 기능 또는 화면 단위로 분리하고 조합하여 하나의 사용자 화면을 구성하는 방식이다.

### 통신 패턴

Micro Service 간 통신 방식은 크게 동기와 비동기로 구분할 수 있다.

#### 동기 통신

요청을 보낸 서비스가 상대방의 응답을 기다리는 방식이다.

대표적으로 REST API나 gRPC 호출을 사용할 수 있다.

```text
Service A → Request → Service B
Service A ← Response ← Service B
```

#### 비동기 통신

Message Broker 등을 이용하여 메시지를 전달하고 즉시 응답을 기다리지 않는 방식이다.

```text
Service A
    ↓
Message Queue
    ↓
Service B
```

Cloud 환경에서는 AWS SQS나 SNS 등의 서비스를 이용하여 비동기 통신을 구현할 수 있다.

### 저장소 분리 패턴

각 Micro Service가 자신의 데이터를 직접 소유하도록 구성한다.

```text
Service A ↔ DB A

Service B ↔ DB B
```

다른 Service가 DB를 직접 접근하지 않도록 하여 서비스의 내부 구현과 데이터 Schema를 캡슐화한다.

### 분산 Transaction Pattern

여러 Service에 걸친 비즈니스 Transaction을 처리할 때 하나의 Global Transaction 대신 Local Transaction과 Messaging을 조합할 수 있다.

#### Saga Pattern

Saga는 여러 개의 분산 Service를 하나의 ACID Transaction으로 묶지 않고 여러 Local Transaction으로 나누어 처리한다.

각 Local Transaction은 자신의 저장소를 갱신한 뒤 다음 작업을 Trigger하기 위한 Message 또는 Event를 발행할 수 있다.

```text
Local Transaction A
        ↓ Event
Local Transaction B
        ↓ Event
Local Transaction C
```

도중에 실패하면 필요한 경우 보상 Transaction을 수행한다.

```text
A 성공
 ↓
B 성공
 ↓
C 실패
 ↓
B 보상
 ↓
A 보상
```

이를 통해 분산 환경에서 비즈니스 정합성을 관리한다.

### 데이터 일관성에 대한 관점 변화

서비스별 저장소 구조에서는 모든 데이터가 항상 동일한 순간에 일치하도록 강제하는 대신 일부 업무에서는 결과적 일관성을 허용할 수 있다.

```text
즉각적 강한 일관성

→ 모든 상태가 즉시 일치
```

```text
결과적 일관성

→ 일시적인 불일치 허용
→ 최종적으로 일관된 상태 도달
```

어떤 일관성 모델을 사용할지는 비즈니스 요구사항에 따라 결정해야 한다.

### CQRS Pattern

CQRS(Command Query Responsibility Segregation)는 **명령(Command)과 조회(Query)의 책임을 분리하는 패턴**이다.

- Command: 상태를 변경하는 작업
- Query: 데이터를 조회하는 작업

기존 방식에서는 하나의 Model과 저장소를 이용하여 Create, Read, Update, Delete를 모두 처리하는 경우가 많다.

```text
Application
     ↓
Single Model
     ↓
Database
```

CQRS에서는 읽기와 쓰기의 책임을 분리한다.

```text
          ┌→ Command Model → Write
Client ───┤
          └→ Query Model   → Read
```

논리적으로 Model만 분리할 수도 있으며, 필요한 경우 다음과 같이 저장소까지 물리적으로 분리할 수 있다.

```text
Command Service → Write Database

Query Service   → Read Database
```

CQRS의 핵심은 반드시 Database를 두 개 사용한다는 것이 아니라 **읽기와 쓰기의 책임 및 Model을 분리하는 것**이다.

### MSA 전체 구조

앞에서 설명한 요소를 하나의 흐름으로 정리하면 다음과 같다.

```text
                         Client
                            ↓
                     API Gateway / BFF
                            ↓
              ┌─────────────┼─────────────┐
              ↓             ↓             ↓
          Service A     Service B     Service C
              ↓             ↓             ↓
          Storage A     Storage B     Storage C
              │             │             │
              └────── Message Broker ─────┘

                       Service Mesh
                            │
             Routing / Security / Telemetry
                            │

                Observability Platform
             Log / Metric / Distributed Trace

                            │
                        CI / CD
                            │
                     Cloud / Kubernetes
```

MSA의 핵심은 서비스를 단순히 작은 크기로 나누는 것이 아니다.

독립적인 서비스가 실제 운영 환경에서 유지될 수 있도록 **조직 구조, 배포 자동화, 데이터 관리, 통신, 장애 대응, Observability와 인프라까지 함께 변화해야 한다.**



> **정리**
> 
>- Monolithic은 여러 기능을 하나의 애플리케이션과 배포 단위로 구성하며, Micro Service는 비즈니스 기능을 중심으로 독립적인 서비스로 분리한다.
>
> - Monolithic도 Scale-out이 가능하지만 특정 기능만 독립적으로 확장하기 어렵다는 점에서 Micro Service와 차이가 있다.
>
> - MSA는 서비스의 독립적인 배포, 느슨한 결합, 비즈니스 기능 중심의 구성과 분권적인 데이터 관리를 중요하게 다룬다.
>
> - 서비스마다 목적에 적합한 언어와 저장 기술을 선택하는 Polyglot Programming과 Polyglot Persistence를 적용할 수 있다.
>
> - Micro Service를 효과적으로 운영하려면 비즈니스 기능 중심의 팀, Product 중심의 개발, DevOps, CI/CD, IaC 등의 변화가 함께 필요하다.
>
> - 서비스별 저장소를 사용하면 서비스 독립성은 높아지지만 분산 Transaction과 데이터 일관성이라는 새로운 문제가 발생한다.
>
> - Saga는 여러 서비스를 하나의 Global Transaction으로 묶는 대신 Local Transaction과 보상 Transaction을 이용하여 분산 데이터의 정합성을 관리한다.
>
> - 결과적 일관성은 일시적인 데이터 불일치를 허용하되 최종적으로 일관된 상태에 도달하도록 하는 모델이다.
>
> - Circuit Breaker는 장애가 발생한 서비스를 계속 호출하지 않고 요청을 일시적으로 차단하여 연쇄 장애를 방지한다.
>
> - Reactive System은 Responsive, Resilient, Elastic, Message Driven이라는 네 가지 특성을 강조한다.
>
> - Micro Service 환경에서는 Service Discovery, API Gateway, BFF, 외부 Configuration, 인증·인가, Service Mesh 등의 플랫폼 패턴을 활용할 수 있다.
>
> - 분산된 서비스를 운영하기 위해 Logging, Metric, Distributed Tracing을 포함한 Observability 체계가 중요하다.
>
> - Service Mesh는 Routing, Load Balancing, Security, Circuit Breaking, Telemetry 등의 공통 Network 기능을 비즈니스 로직과 분리하는 데 사용한다.
>
> - CQRS는 Command와 Query의 책임을 분리하는 패턴이며, 필요에 따라 읽기와 쓰기의 저장소까지 분리할 수 있다.
>
> - MSA는 단순히 애플리케이션을 작은 서비스로 나누는 기술이 아니라 조직, 개발, 배포, 데이터, 통신, 장애 대응 및 운영 체계 전체를 함께 고려하는 아키텍처이다.