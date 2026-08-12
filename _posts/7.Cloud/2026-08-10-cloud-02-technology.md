---
title: Cloud에 필요한 기술
description: 클라우드 네트워크, IaC, 보안과 접근 제어, 장애 대응 및 고가용성, 재해 복구와 클라우드 플랫폼 선택 기준
date: 2026-08-10
series: Cloud
tags:
  - Cloud
  - AutoEverSW
---
## 1) Cloud에 필요한 기술
---

클라우드 환경에서는 내부 시스템과 클라우드를 연결하고, 동적으로 생성되는 리소스를 식별하며, 네트워크와 인프라를 안정적으로 운영하기 위한 여러 기술이 필요하다.

대표적으로 다음과 같은 기술이 사용된다.

- VPN (Virtual Private Network)
- Dedicated Line (전용선)
- Load Balancer
- Service Endpoint
- Naming Service와 Service Discovery
- VPC (Virtual Private Cloud) / VNet (Virtual Network)
- IaC (Infrastructure as Code)

### VPN과 클라우드 전용선

클라우드 내부 시스템을 연결하거나 On-Premise 환경에서 클라우드 리소스에 안전하게 접근해야 할 때 VPN 또는 전용선을 사용할 수 있다.

#### VPN

VPN (Virtual Private Network)은 공용 네트워크 위에 논리적인 사설 네트워크를 구성하여 데이터를 안전하게 주고받도록 하는 기술이다.

실제 통신에는 인터넷을 사용할 수 있지만, VPN 터널 내부의 데이터를 암호화하여 전송하기 때문에 외부에서 통신 내용을 쉽게 확인할 수 없도록 한다.

Public Cloud에서는 VPN을 구성하기 위한 기능을 제공하며, 클라우드 측 VPN Gateway와 회사 또는 사용자의 VPN 장비·클라이언트를 연결하여 사용할 수 있다.

VPN의 성능은 다음과 같은 요소의 영향을 받을 수 있다.

- 인터넷 회선 품질
- 네트워크 경로
- VPN Gateway의 처리 성능
- 암호화 및 복호화 처리
- 네트워크 혼잡도

따라서 VPN 자체가 무조건 느리다고 볼 수는 없다.

> **강의에서의 질문 - VPN은 암호화 때문에 느린가?**
>
> VPN에서는 암호화 및 복호화에 따른 추가 처리가 발생한다.
> 그러나 실제 성능은 인터넷 연결 상태와 네트워크 경로 등 여러 요소에 의해 결정된다.
>
> 안정적인 지연 시간이나 일정한 대역폭이 중요한 대규모 트래픽 환경에서는 인터넷 기반 VPN보다 전용 회선을 고려할 수 있다.

#### Dedicated Line

Dedicated Line (전용선)은 기업의 On-Premise 네트워크와 클라우드 사업자의 네트워크를 전용 연결을 통해 구성하는 방식이다.

공용 인터넷을 통한 VPN과 비교하면 일정한 네트워크 품질과 높은 대역폭을 확보하기 쉽다.

따라서 다음과 같이 안정적인 네트워크 성능이 중요한 환경에서 고려할 수 있다.

- 대규모 데이터 전송
- On-Premise와 Cloud 사이의 지속적인 데이터베이스 통신
- 지연 시간과 네트워크 품질이 중요한 서비스
- 대규모 기업 및 금융 환경

다만 VPN보다 구축 절차가 복잡하고 비용도 높다.

#### VPN과 전용선 비교

| 비교 | VPN | 전용선 |
|---|---|---|
| 연결 방식 | 주로 공용 인터넷망을 이용한 암호화 터널 | 클라우드와 전용 연결 구성 |
| 구축 비용 | 비교적 저렴 | 비교적 높음 |
| 구축 속도 | 빠른 편 | 회선 구성 등이 필요하여 상대적으로 느림 |
| 보안 | 암호화된 터널 사용 | 공용 인터넷을 우회할 수 있음 |
| 속도 및 품질 | 인터넷 품질 등의 영향을 받음 | 비교적 안정적인 대역폭과 품질 확보 가능 |
| 확장성 | 비교적 유연함 | 회선 용량 변경 등에 추가 작업이 필요할 수 있음 |
| 주요 활용 | 원격 접속, 관리용 접속, Site-to-Site 연결 | 대규모 서비스, 기업 네트워크와 Cloud 연동 |

> **정리**
>
> - VPN은 공용 네트워크 위에 암호화된 논리적 사설망을 구성한다.
> - 전용선은 On-Premise와 Cloud 사이에 보다 안정적인 전용 연결을 구성한다.
> - VPN은 구축이 비교적 간단하고 저렴하지만 인터넷 환경의 영향을 받을 수 있다.
> - 전용선은 안정적인 성능을 확보하기 쉽지만 구축 비용과 복잡도가 높다.

### Load Balancer와 Service Endpoint

#### Service Endpoint

Service Endpoint는 네트워크상에서 클라이언트가 특정 서비스나 애플리케이션 기능에 접근하기 위해 사용하는 접점이다.

클라이언트는 내부 서버의 실제 구조를 직접 알지 않고 Endpoint를 기준으로 서비스에 접근할 수 있다.

예를 들어 내부에서 실제 서버가 변경되더라도 외부에서 사용하는 Endpoint가 유지된다면 클라이언트의 접근 방식은 변경하지 않아도 된다.

#### 캡슐화와 추상화

Service Endpoint를 사용하면 내부 시스템의 구체적인 구조를 외부 인터페이스로부터 분리할 수 있다.

```text
Client
   │
   ▼
Service Endpoint
   │
   ├── Server A
   ├── Server B
   └── Server C
````

외부 사용자는 Endpoint만 알고 있으면 되며 내부의 서버 구성이나 위치가 변경되더라도 동일한 방식으로 서비스를 사용할 수 있다.

**강의 예시 - 소켓과 추상화**

소켓을 설명할 때 실제 NIC와 네트워크 처리 구조를 직접 다루는 대신 네트워크 통신을 위한 인터페이스로 추상화했다고 볼 수 있다.

내부 구현이 변경되더라도 사용하는 쪽에서 동일한 인터페이스를 사용할 수 있도록 만드는 것이 추상화의 중요한 목적이다.

#### **보안 제어**

Endpoint 주변에는 다음과 같은 보안 정책을 적용할 수 있다.

- 인증 (Authentication)
- 인가 (Authorization)
- 방화벽 정책
- 접근 제어
- 트래픽 제한

다만 Endpoint 자체가 이러한 보안 기능을 모두 수행하는 것은 아니며, 실제 환경에서는 API Gateway, Load Balancer, Firewall, IAM 등의 다른 구성 요소와 결합하여 구현한다.

#### **Load Balancer**

Load Balancer는 클라이언트의 요청을 여러 서버나 서비스 인스턴스로 분산한다.

```text
           Client
              │
              ▼
        Load Balancer
         /     |     \
        ▼      ▼      ▼
     Server  Server  Server
       A       B       C
```

Load Balancer가 하나의 Endpoint를 제공하고 그 뒤에 여러 서버를 배치하는 구조를 사용할 수 있다.

따라서 **Endpoint는 접근 지점에 대한 개념이고, Load Balancer는 트래픽을 여러 대상으로 분산하는 역할**이라는 점을 구분해야 한다.

### **Cloud Native Naming Service**

DNS (Domain Name System)는 사람이 이해하기 쉬운 이름과 네트워크 주소를 연결하여 통신을 쉽게 만들어준다.

클라우드 환경에서는 서버와 컨테이너가 동적으로 생성되고 제거될 수 있기 때문에 특정 IP 주소를 직접 기억하고 관리하는 방식이 비효율적이다.

```text
Service A
   │
   │ "Service B로 연결"
   ▼
Naming / Service Discovery
   │
   ▼
현재 Service B의 주소
```

이러한 환경에서는 DNS를 비롯한 이름 기반의 접근 방식과 Service Discovery가 중요해진다.

#### **Service Discovery**

Service Discovery는 서비스의 이름을 이용하여 현재 해당 서비스를 제공하는 위치를 찾아갈 수 있도록 하는 방식이다.

클라우드나 컨테이너 오케스트레이션 환경에서는 서비스의 주소가 변경되더라도 등록 정보가 자동으로 갱신될 수 있다.

예를 들어 Kubernetes에서는 Service를 생성하면 클러스터 내부 DNS를 통해 Service 이름을 기반으로 접근할 수 있다.

따라서 애플리케이션은 상대 컨테이너의 실제 IP 주소를 직접 기억하지 않고 Service 이름을 기준으로 통신할 수 있다.

#### **장점**

**유연성**

서버나 컨테이너의 IP 주소가 변경되더라도 이름을 기준으로 접근할 수 있다.

**자동화**

관리자가 매번 변경된 IP 주소를 직접 확인하여 애플리케이션 설정을 수정하는 작업을 줄일 수 있다.

**서비스 간 통신 단순화**

Microservice 환경에서는 다른 서비스의 이름을 기준으로 통신할 수 있다.

```text
order-service
      │
      ▼
payment-service
```

애플리케이션 입장에서는 `payment-service`가 실제로 어떤 IP를 사용하고 있는지 직접 관리할 필요가 줄어든다.

#### **Private DNS**

클라우드에서는 외부 인터넷에 공개할 필요가 없는 내부 서비스에 대해 Private DNS 등의 내부 이름 해석 기능을 사용할 수 있다.

이를 통해 외부에 공개되지 않는 네트워크에서도 서비스 이름을 기준으로 내부 시스템끼리 통신할 수 있다.

**정리**

- 클라우드의 서버와 컨테이너는 동적으로 변경될 수 있어 고정 IP에 의존하기 어렵다.
- 이름을 기준으로 현재 서비스의 위치를 찾는 방식이 중요해진다.
- Service Discovery를 이용하면 서비스의 위치 변화와 애플리케이션을 분리할 수 있다.
- Private DNS를 이용하여 외부에 공개되지 않는 내부 서비스의 이름도 관리할 수 있다.

### **Cloud Virtual Network Architecture**

클라우드에서 서버를 구성할 때는 서버가 속할 논리적인 가상 네트워크가 필요하다.

클라우드 사업자에 따라 이러한 네트워크를 VPC (Virtual Private Cloud), VNet (Virtual Network) 등의 이름으로 부른다.

가상 네트워크 내부에는 다음과 같은 구성 요소를 배치할 수 있다.

```text
VPC / VNet
│
├── Subnet
│    ├── Server
│    └── Server
│
├── Routing Table
├── NAT Gateway
├── Security Policy
└── On-Premise / Internet 연결
```

#### **생성 과정**

1. **VPC 또는 VNet 구성**
    - 사용할 Private IP 주소 범위를 설정한다.
    - 필요한 Subnet을 구성한다.
2. **서버 생성**
    - 서버에 Private IP를 할당한다.
    - 외부에서 직접 접근할 필요가 있다면 Public IP 등의 연결 방식을 구성할 수 있다.
    - Private Subnet의 서버가 외부 인터넷으로 나가야 한다면 NAT Gateway 등을 사용할 수 있다.
3. **Routing Table 설정**
    - 목적지에 따라 트래픽이 이동할 경로를 설정한다.
    - Internet Gateway, NAT Gateway, 다른 네트워크 또는 On-Premise 환경 등으로 전달할 경로를 결정한다.
4. **보안 정책 구성**
    - Security Group
    - Network ACL (Access Control List)

이와 같은 기능을 이용하여 네트워크 접근을 제어한다.

**정리**

- VPC 또는 VNet은 클라우드에서 사용하는 논리적 가상 네트워크이다.
- 내부에는 Subnet을 구성하고 Private IP를 이용하여 서버를 배치할 수 있다.
- 외부 연결이 필요하면 Public IP, NAT 등의 방식을 사용할 수 있다.
- Routing Table은 트래픽이 이동할 경로를 결정한다.
- Security Group과 Network ACL 등을 이용하여 네트워크 접근을 제어한다.

## **2) Infrastructure as Code (IaC)**

---

### **개요**

Infrastructure as Code (IaC)는 인프라의 구성과 원하는 상태를 코드 또는 설정 파일로 정의하고, 이를 기반으로 인프라를 프로비저닝하고 관리하는 방식이다.

관리 대상에는 다음과 같은 리소스가 포함될 수 있다.

- Compute
- Virtual Machine
- Network
- Storage
- Load Balancer
- Database
- Cloud Resource
- 일부 On-Premise Infrastructure

기존에는 관리자가 콘솔이나 장비에 직접 접근하여 설정을 변경하는 경우가 많았다.

이 방식에서는 실제 환경의 변경 이력이 문서와 일치하지 않거나, 작업자가 변경 사항을 기록하지 않으면 현재 구성을 정확하게 파악하기 어려울 수 있다.

IaC에서는 인프라 구성을 파일로 관리할 수 있기 때문에 Git 등의 Version Control System과 결합할 수 있다.

```text
Infrastructure 변경
        │
        ▼
     IaC Code
        │
        ▼
      Git
        │
        ▼
변경 이력 및 Version 관리
```

따라서 다음과 같은 정보를 추적하기 쉬워진다.

- 무엇이 변경되었는가?
- 누가 변경했는가?
- 언제 변경했는가?
- 이전 구성은 무엇이었는가?

### **등장 배경**

클라우드 환경에서는 구성해야 하는 리소스의 수가 증가하면서 사람이 직접 동일한 작업을 반복하는 방식의 한계가 커졌다.

대표적인 문제는 다음과 같다.

- 반복 작업에서 실수가 발생할 수 있다.
- 환경마다 설정이 달라질 수 있다.
- 현재 구성을 정확하게 파악하기 어렵다.
- 변경 이력을 추적하기 어렵다.
- 여러 사람이 동일한 인프라를 관리할 때 협업하기 어렵다.
- 장애 발생 시 이전 상태를 파악하기 어렵다.

IaC는 인프라 구성을 코드로 남겨 이러한 문제를 줄이기 위한 방법이다.

**강사의 실무 경험 - 문서화의 중요성**

과거에는 하드웨어를 변경하고도 변경 기록이 제대로 남지 않는 경우가 있었다.  
그래서 시스템을 구성하고 관리하는 과정에서 문서화가 매우 중요했다.

시간이 오래 지난 코드는 작성자조차 구조를 이해하기 어려워질 수 있다. 강의에서는 이를 기억하기 쉽게 “외계인 코드”에 비유하였다.

실제 프로젝트에서도 구축이 끝난 뒤 문서가 제대로 남아 있지 않으면 이후 유지보수 과정에서 추가적인 시간과 비용이 발생할 수 있다.

**강의에서의 IaC 관점**

개발이나 운영 과정에서 변경 기록이 자연스럽게 부산물로 남도록 만드는 것이 중요하다.

Git을 사용하면 코드 변경 이력이 자연스럽게 남는 것처럼, 인프라 역시 코드로 정의하면 인프라의 변경 기록을 Version Control System으로 관리할 수 있다.

코드에서 API 문서를 생성하는 도구처럼 작업의 결과물이 자동으로 문서와 기록으로 연결되는 방식도 활용할 수 있다.

강의에서는 Jira, Slack 등의 협업 도구를 실제 업무 환경에서 경험해보는 것도 도움이 된다고 언급하였다.

IaC는 단순히 명령을 자동 실행하는 것을 넘어 **인프라 관리 방식을 코드 중심으로 전환하는 것**이라고 볼 수 있다.

자동화와 표준화를 통해 반복적인 수작업을 줄일 수 있으므로 운영 비용 절감에도 도움을 줄 수 있다.

### **Terraform과 Ansible**

Terraform과 Ansible은 모두 인프라 자동화에 사용되지만 주요 목적에는 차이가 있다.

|**비교**|**Terraform**|**Ansible**|
|---|---|---|
|개발 주체|HashiCorp|Red Hat / Ansible Community|
|주요 용도|인프라 프로비저닝 및 수명 주기 관리|시스템 구성 관리 및 IT 자동화|
|대표적인 분류|IaC|Configuration Management / IT Automation|
|정의 방식|HCL 기반 구성|YAML 기반 Playbook|
|Managed Node Agent|별도 Agent 불필요|Agentless|
|확장 방식|Provider|Module, Collection, Plugin|
|주요 관리 대상|Cloud, On-Premise, SaaS 등의 Infrastructure|Server, Network, Cloud Service, Application 등|

#### **Terraform**

Terraform은 원하는 인프라의 상태를 선언적으로 정의하고 리소스를 생성·변경·삭제하는 데 사용한다.

```text
Terraform Code
      │
      ▼
   Provider
      │
      ├── AWS
      ├── Azure
      ├── GCP
      └── 기타 Infrastructure
```

Provider를 통해 각 플랫폼의 API와 연결한다.

#### **Ansible**

Ansible은 서버나 시스템의 구성 상태를 자동화하는 데 많이 사용한다.

예를 들어 다음과 같은 작업을 정의할 수 있다.

- Package 설치
- 설정 파일 배포
- Service 시작 및 중지
- Application 배포
- Server 구성
- Network 장비 구성

Managed Node에 별도의 Ansible Agent를 설치하지 않는 Agentless 방식이 특징이다.

Terraform과 Ansible의 영역은 완전히 분리되는 것은 아니며 실제 환경에서는 함께 사용할 수도 있다.

예를 들어 Terraform으로 VM과 Network를 생성한 뒤 Ansible로 VM 내부의 Package와 Application을 구성하는 식이다.

### **AWS CloudFormation**

AWS CloudFormation은 AWS에서 제공하는 IaC 서비스이다.

AWS Resource를 Template으로 정의하고 Stack 단위로 생성 및 관리할 수 있다.

Template은 JSON 또는 YAML 형식으로 작성할 수 있다.

```text
CloudFormation Template
          │
          ▼
         Stack
          │
          ├── EC2
          ├── VPC
          ├── Load Balancer
          └── 기타 AWS Resource
```

CloudFormation은 AWS 환경을 대상으로 하는 서비스이므로 일반적인 Multi-Cloud IaC 도구와는 성격이 다르다.

Template에는 조건에 따라 Resource를 생성하기 위한 Condition을 정의할 수 있으며, `AWS::LanguageExtensions`를 사용하는 경우 `Fn::ForEach`를 이용한 반복적인 Resource 정의도 사용할 수 있다.

### **IaC의 장점**

#### **환경 간 일관성**

동일한 코드를 기반으로 인프라를 생성하면 개발, 테스트, 운영 환경에서 설정 차이가 발생하는 문제를 줄일 수 있다.

#### **변경 이력 추적**

IaC 파일을 Git과 같은 Version Control System으로 관리하면 변경 이력을 확인할 수 있다.

#### **반복 작업 자동화**

동일한 인프라 구성을 여러 번 반복해서 수행해야 할 때 수작업을 줄일 수 있다.

#### **불필요한 자원 관리**

실제 구성과 코드의 상태를 비교하면서 필요한 리소스를 체계적으로 관리할 수 있다.

도구에 따라 인프라 삭제 작업도 코드와 자동화 과정에 포함할 수 있다.

#### **클라우드 환경에 대한 통제력 향상**

인프라 구성을 코드로 명시하면 현재 시스템이 어떤 형태로 구성되어야 하는지를 명확하게 표현할 수 있다.

**정리**

- IaC는 인프라의 원하는 상태를 코드로 정의하고 관리하는 방식이다.
- Git과 결합하면 인프라 변경 이력을 관리할 수 있다.
- Terraform은 인프라 프로비저닝과 수명 주기 관리에 주로 사용한다.
- Ansible은 서버 구성과 IT 자동화에 주로 사용한다.
- CloudFormation은 AWS Resource를 Template으로 정의하는 AWS의 IaC 서비스이다.
- IaC는 반복 작업, 환경 간 불일치, 변경 추적 문제를 줄이는 데 도움이 된다.

## **3) 보안과 접근 제어**

---

### **Shared Responsibility Model**

Shared Responsibility Model (공유 책임 모델)은 클라우드 보안의 모든 책임을 Cloud Service Provider가 담당하는 것이 아니라 **Cloud Provider와 Customer가 역할을 나누어 담당하는 모델**이다.

Cloud Provider는 기본적으로 데이터센터, 물리 서버, 네트워크 등 클라우드 서비스를 제공하기 위한 기반 인프라를 보호한다.

반면 사용자는 자신이 이용하는 서비스 유형에 따라 다음과 같은 영역에 책임을 가진다.

- Account
- Identity
- Data
- Application
- Operating System
- Network Configuration
- Security Configuration

서비스가 IaaS에서 PaaS, SaaS 방향으로 이동할수록 일반적으로 Cloud Provider가 관리하는 영역이 증가한다.

### **서비스 모델에 따른 책임 범위**

|**구분**|**사용자 책임의 특징**|**Cloud Provider 책임의 특징**|
|---|---|---|
|IaaS|Guest OS, Application, Data, 계정, 상당수 Network 및 Security 설정 관리|물리 Infrastructure, Virtualization 기반 관리|
|PaaS|Application, Data, Identity와 서비스 설정 중심|OS, Runtime, Platform 등의 관리 범위 증가|
|SaaS|Account, Data, 접근 권한 및 사용 설정 중심|Application을 포함한 대부분의 Platform과 Infrastructure 운영|

구체적인 책임 범위는 사용하는 Cloud Service와 제품에 따라 달라질 수 있다.

### **IAM**

IAM (Identity and Access Management)은 **누가 어떤 Resource에 어떤 조건으로 접근할 수 있는지를 통제하고 관리하는 보안 체계**이다.

클라우드 보안에서 가장 기본적인 통제 수단 중 하나이다.

#### **IAM의 핵심 구성 요소**

**Identification (식별)**

접근 주체가 누구인지를 구분하는 과정이다.

Identity는 반드시 사람만을 의미하지 않는다.

- User
- Application
- Server
- Service Account
- Workload

등도 Identity가 될 수 있다.

**Authentication (인증)**

접근하려는 주체가 주장하는 Identity가 실제로 맞는지 확인한다.

예시는 다음과 같다.

- ID / Password
- MFA
- Certificate
- 외부 Identity Provider를 이용한 로그인

**Authorization (인가)**

인증된 Identity가 특정 Resource에서 어떤 행동을 수행할 수 있는지 판단한다.

예를 들어 다음과 같은 권한을 설정할 수 있다.

- 읽기만 허용
- Resource 생성 허용
- 관리자 권한 부여
- 특정 Database만 접근 허용

**Account Lifecycle Management (계정 수명 주기 관리)**

계정은 생성 이후 계속 유지하는 것이 아니라 전체 수명 주기를 관리해야 한다.

```text
계정 생성
   ↓
권한 부여
   ↓
권한 변경
   ↓
비활성화
   ↓
삭제
```

### **Policy**

IAM에서는 Policy를 이용하여 Identity가 수행할 수 있는 작업을 정의할 수 있다.

각 사용자에게 모든 권한을 부여하는 대신 실제 업무에 필요한 범위의 권한만 부여하는 것이 중요하다.

### **RBAC와 ABAC**

|**구분**|**RBAC (Role-Based Access Control)**|**ABAC (Attribute-Based Access Control)**|
|---|---|---|
|기준|사용자의 역할(Role)|사용자, Resource, 환경 등의 Attribute|
|예|개발자, 관리자, 감사 담당자|부서, 시간, 위치, Resource Tag 등의 조건|
|특징|구조가 비교적 단순하고 관리하기 쉬움|조건을 이용한 세밀한 정책 표현 가능|

#### **IAM이 필요한 이유**

**최소 권한 적용**

사용자에게 업무 수행에 필요한 최소한의 권한만 부여한다.

**중앙 집중식 관리**

수많은 Account와 Permission을 중앙에서 관리할 수 있다.

**Audit와 규정 준수**

누가, 언제, 어떤 Resource에 접근하고 어떤 작업을 수행했는지 기록하여 Audit과 보안 규정 준수에 활용할 수 있다.

#### **대표적인 IAM 서비스와 솔루션**

**Cloud IAM**

- AWS IAM
- Google Cloud IAM
- Microsoft Entra ID

**IAM / SSO Solution**

- Okta
- Ping Identity
- Keycloak

### **최소 권한의 원칙**

Principle of Least Privilege (최소 권한의 원칙)는 User, Process, Application 등에 **주어진 업무를 수행하는 데 필요한 최소한의 권한만 부여하는 보안 원칙**이다.

필요 이상의 정보와 기능에 접근할 수 없도록 한다.

관련 개념으로 다음과 같은 표현을 사용할 수 있다.

- Need-to-Know
- Need-to-Do

#### **필요한 이유**

- 보안 사고 발생 시 피해 범위 최소화
- 내부자 위협 감소
- 실수로 인한 Resource 변경 및 Data 손실 방지
- 규정 준수

#### **적용 사례**

**Root Account 사용 최소화**

일반 작업에서는 일반 Account를 사용하고 필요한 경우에만 `sudo` 등으로 권한을 상승한다.

**IAM Policy 세분화**

개발자에게 모든 Resource에 대한 `*` 권한을 제공하는 대신 업무에 필요한 Resource와 Operation만 허용한다.

**Smartphone Application 권한**

Application이 실제 기능에 필요한 Camera, Location 등의 권한만 요청하도록 한다.

**Database Account 분리**

Database 또는 Table 단위로 Account와 Permission을 구분한다.

#### **최소 권한 원칙 이행 방법**

**Default Deny**

명시적으로 허용하지 않은 접근은 기본적으로 거부한다.

**RBAC**

사용자의 Role을 기준으로 필요한 권한을 부여한다.

**Just-In-Time Access**

항상 높은 권한을 보유하는 대신 필요한 순간에 일정 시간 동안만 권한을 부여한다.

**Access Review**

현재 사용자에게 부여된 권한이 계속 필요한지 정기적으로 점검한다.

### **비밀번호·Key와 Secret 관리**

Password와 API Key 등의 Secret을 Source Code에 직접 작성하면 코드가 외부에 노출되었을 때 Secret도 함께 유출될 수 있다.

따라서 Secret과 Source Code를 분리하여 관리해야 한다.

대표적인 방식에는 다음이 있다.

- 환경 변수
- 접근 권한이 제한된 외부 설정
- Secret Management Service

단, 환경 변수를 사용한다는 사실만으로 Secret이 안전해지는 것은 아니며 실행 환경과 접근 권한 역시 적절하게 관리해야 한다.

#### **Secret Management Service**

Cloud Provider는 Secret을 별도로 저장하고 관리하기 위한 서비스를 제공한다.

대표적으로 다음과 같은 기능을 제공할 수 있다.

- Secret 암호화 저장
- 접근 주체 제어
- IAM과 연동
- Audit
- Secret Version 관리
- Rotation 자동화

대표적인 서비스는 다음과 같다.

|**Cloud**|**Service**|
|---|---|
|AWS|AWS Secrets Manager|
|Azure|Azure Key Vault|
|Google Cloud|Secret Manager|

#### **Key Rotation**

Key Rotation은 암호화 Key 또는 Credential을 일정 주기나 특정 Event에 따라 새로운 값으로 교체하는 과정이다.

```text
Old Key
   ↓
새 Key 생성
   ↓
Application 전환
   ↓
Old Key 폐기
```

Secret Management Service를 사용하면 Rotation 과정을 자동화할 수 있는 기능을 활용할 수 있다.

다만 Cloud가 Secret을 암호화해준다고 해서 사용자의 보안 책임이 사라지는 것은 아니다.

다음과 같은 설정은 여전히 중요하다.

- 누가 Secret에 접근할 수 있는가?
- 어떤 Application에서 사용할 수 있는가?
- Rotation 정책은 어떻게 구성할 것인가?
- Logging과 Audit은 어떻게 관리할 것인가?

### **인증 Token**

Authentication 또는 Authorization 과정에서는 사용자가 매 요청마다 ID와 Password를 다시 전송하는 대신 Token을 사용할 수 있다.

일반적인 흐름은 다음과 같다.

```text
사용자
  │
  │ 인증
  ▼
인증 Server
  │
  │ Token 발급
  ▼
사용자
  │
  │ Token을 이용한 요청
  ▼
Resource Server
```

Token은 사용자의 Password 그 자체를 반복해서 전달하지 않고 일정한 자격 정보를 이용하여 Resource에 접근할 수 있도록 한다.

### **JWT**

JWT (JSON Web Token)는 두 주체 사이에서 Claim을 전달하기 위한 Compact하고 URL-Safe한 Token 형식이다.

JWT는 흔히 서명을 이용하여 Token이 변조되지 않았음을 검증하도록 구성한다.

중요한 점은 **JWT 자체가 항상 암호화되어 있는 것은 아니라는 것**이다.

서명된 JWT의 Payload는 Base64URL Encoding된 형태이므로 기밀 정보를 아무 생각 없이 넣어서는 안 된다.

필요한 경우 암호화된 형태의 JWT도 구성할 수 있다.

### **Access Token과 Refresh Token**

#### **Access Token**

보호된 Resource에 접근할 때 사용하는 Token이다.

보안상 일반적으로 비교적 짧은 유효 기간을 설정하는 전략을 사용할 수 있다.

Token이 탈취되어도 사용할 수 있는 시간을 제한하기 위한 것이다.

#### **Refresh Token**

Access Token이 만료된 후 새로운 Access Token을 발급받는 데 사용할 수 있다.

일반적으로 Access Token보다 오래 유지될 수 있기 때문에 더욱 주의해서 저장하고 관리해야 한다.

Refresh Token의 실제 저장 위치와 관리 방식은 인증 시스템의 설계에 따라 달라진다.

### **Token 방식의 특징**

#### **장점**

**분산 시스템과 API에서 활용하기 쉬움**

API 요청에 Token을 포함하여 인증 및 인가 정보를 전달할 수 있다.

**다양한 Client에서 사용할 수 있음**

- Web
- Mobile
- Application
- API Client

등에서 활용할 수 있다.

**Stateless 구조 구성 가능**

검증에 필요한 정보를 Token 자체에 포함하는 방식에서는 서버에 Session State를 최소화하는 구조를 만들 수 있다.

다만 모든 Token 시스템이 Stateless인 것은 아니다.

#### **고려해야 할 문제**

**Token 탈취**

Token이 탈취되면 유효 기간 동안 공격자가 이를 사용할 수 있으므로 안전한 저장과 전송이 중요하다.

**XSS (Cross-Site Scripting)**

공격자가 Web Page에서 악성 Script를 실행하도록 만드는 공격이다.

Client 측에서 접근할 수 있는 위치에 Token을 저장한 경우 XSS 공격으로 Token이 노출될 가능성을 고려해야 한다.

**CSRF (Cross-Site Request Forgery)**

사용자가 이미 인증되어 있다는 점을 악용하여 사용자가 의도하지 않은 요청을 보내도록 만드는 공격이다.

CSRF 위험은 Token을 어떤 방식으로 전달하고 저장하는지와도 관련된다.

**Token 폐기**

Self-Contained Token은 발급 이후 서버의 별도 State 없이 검증할 수 있다는 장점이 있지만, 만료 전에 즉시 폐기하려면 별도의 설계가 필요할 수 있다.

예를 들어 다음과 같은 전략을 사용할 수 있다.

- 짧은 Access Token 만료 시간
- Refresh Token 폐기
- Token Revocation 목록
- Server-side Token 상태 관리

### **MFA**

MFA (Multi-Factor Authentication)는 사용자의 신원을 확인할 때 서로 다른 종류의 인증 요소를 두 개 이상 사용하는 방식이다.

일반적으로 인증 요소를 다음과 같이 구분할 수 있다.

- 사용자가 알고 있는 것
- 사용자가 가지고 있는 것
- 사용자 자신을 나타내는 것

Password 하나만 사용하는 환경에서는 Password가 유출되면 계정을 탈취당할 수 있다.

MFA를 사용하면 Password가 노출된 상황에서도 추가 인증 요소를 요구하여 계정 침해 가능성을 크게 낮출 수 있다.

#### **MFA가 필요한 이유**

- Password 유출에 대한 추가 방어
- Account 탈취 위험 감소
- 중요 시스템에 대한 접근 통제 강화
- 보안 정책 및 규정 준수

MFA의 효과에 대한 수치는 조사 환경과 인증 방식에 따라 달라질 수 있으므로 특정 비율을 모든 시스템에 동일하게 적용해서는 안 된다.

**정리**

- Cloud Security는 Provider와 Customer가 책임을 나누는 Shared Responsibility Model을 따른다.
- IAM은 Identity의 식별, 인증, 인가 및 수명 주기를 관리한다.
- Least Privilege는 업무에 필요한 최소한의 Permission만 부여하는 원칙이다.
- Password와 API Key는 Source Code와 분리하여 관리해야 한다.
- JWT는 항상 암호화되는 것이 아니며 Claim을 전달하기 위한 Token 형식이다.
- Access Token과 Refresh Token은 목적과 수명 주기가 다르다.
- MFA는 Password가 유출된 경우에도 추가적인 인증 계층을 제공한다.

## **4) Cloud 장애 대응**

---

### **장애의 원인**

클라우드에서도 장애는 발생한다.

대표적인 원인은 다음과 같다.

- Human Error
- 서비스 간 의존성 문제
- 물리적 Resource 장애
- Network 장애
- Application 장애
- Configuration 오류

클라우드 환경은 여러 서비스와 계층이 연결되어 있기 때문에 문제가 발생했을 때 **어느 계층에서 장애가 시작되었는지 빠르게 파악하는 것**이 중요하다.

장애 자체를 완전히 제거할 수 있다고 가정하기보다 장애가 발생할 것을 전제로 다음 전체 주기를 준비해야 한다.

```text
감지
 ↓
대응
 ↓
복구
 ↓
사후 분석
 ↓
재발 방지
```

### **장애 대응 전략**

대표적인 전략은 다음과 같다.

- 실시간 Monitoring과 Alert
- 자동 복구 및 Self-Healing
- Region 또는 Zone 단위의 Redundancy
- 정기적인 Backup
- Restore Scenario 준비
- RPO와 RTO 설정
- Postmortem
- Root Cause Analysis
- 재발 방지 대책

### **Monitoring과 Log 수집**

Monitoring은 시스템의 상태를 지속적으로 관찰하여 이상 상태를 빠르게 발견하기 위한 방법이다.

예를 들어 다음 지표를 확인할 수 있다.

- CPU Usage
- Memory Usage
- Disk Usage
- Network Traffic
- Request Latency
- Error Rate
- Application Response Time

특정 기준을 초과하면 Alert을 발생시켜 운영자가 빠르게 확인할 수 있도록 구성한다.

### **중앙 집중식 Logging**

클라우드 환경에서는 여러 Server, Container, Application에서 Log가 발생한다.

각 Server에 직접 접속해서 Log를 확인하는 방식은 규모가 커질수록 관리하기 어렵다.

따라서 여러 위치에서 발생한 Log를 중앙 시스템으로 수집하여 분석할 수 있도록 구성한다.

```text
Server A ─┐
Server B ─┼──▶ Centralized Logging
App C    ─┘
```

### **Distributed Tracing**

Microservice처럼 하나의 요청이 여러 서비스를 거치는 시스템에서는 특정 요청이 어떤 서비스를 거쳐 처리되었는지 추적할 필요가 있다.

이를 Distributed Tracing (분산 추적)이라고 한다.

```text
Client
  ↓
Service A
  ↓
Service B
  ↓
Service C
  ↓
Database
```

Tracing을 이용하면 요청이 어느 구간에서 오래 걸렸거나 실패했는지 파악하는 데 도움을 받을 수 있다.

### **장애를 빠르게 감지하고 원인을 찾는 방법**

- 실시간 Monitoring으로 문제 발생 시 빠르게 Alert을 받는다.
- Log를 이용하여 장애 발생 전후의 상황을 추적한다.
- 여러 Server의 데이터를 중앙에 모아 분석한다.
- Distributed Tracing을 이용하여 서비스 간 요청 흐름을 추적한다.

## **5) High Availability**

---

### **개요**

High Availability (고가용성)는 Server, Network, Application 등의 일부 구성 요소에 장애가 발생하더라도 서비스를 계속 제공하거나 중단 시간을 최소화할 수 있도록 시스템을 설계하는 개념이다.

목표는 단순히 “서버를 항상 켜두는 것”이 아니라 **일부 구성 요소의 실패가 전체 서비스 중단으로 이어지지 않도록 설계하는 것**이다.

### **Availability**

Availability는 일정 기간 동안 시스템이 정상적으로 서비스를 제공한 비율을 의미한다.

대표적인 수치를 연간 Down Time으로 환산하면 다음과 같다.

|**Availability**|**연간 Down Time**|
|---|---|
|99.9%|약 8시간 46분|
|99.99%|약 52분 34초|
|99.999%|약 5분 15초|

이를 흔히 `Three Nines`, `Four Nines`, `Five Nines` 등으로 표현한다.

필요한 Availability 수준은 서비스의 중요도, 비용, SLA (Service Level Agreement) 등에 따라 결정해야 한다.

Availability가 높아질수록 일반적으로 이를 달성하기 위한 시스템 구성과 비용도 증가한다.

### **고가용성의 3가지 핵심 원칙**

#### 1. **Single Point of Failure 제거**

SPOF (Single Point of Failure)는 하나의 구성 요소가 실패했을 때 전체 시스템이 중단되는 지점을 의미한다.

```text
Client
  │
  ▼
Single Server  ← 장애
  │
  X
Service 전체 중단
```

가능하면 중요한 시스템에 SPOF가 존재하지 않도록 설계해야 한다.

#### 2. **Redundancy**

Redundancy (이중화)는 동일한 기능을 수행할 수 있는 구성 요소를 여러 개 배치하는 방식이다.

다음과 같은 대상을 이중화할 수 있다.

- Server
- Database
- Network Device
- Storage
- Power Supply
- Network Line


 **Active-Active**
여러 시스템이 동시에 요청을 처리한다.

```text
          Load Balancer
          /           \
         ▼             ▼
     Active A       Active B
```

한 시스템에 장애가 발생하면 정상 상태의 다른 시스템이 계속 요청을 처리할 수 있도록 구성한다.

**Active-Standby**
하나는 서비스를 제공하고 다른 하나는 대기한다.

```text
Active
  │
  │ 장애
  ▼
Standby
  │
  ▼
Active 전환
```

장애가 발생하면 Standby 시스템이 역할을 넘겨받는 Failover를 수행한다.

#### 3. **Health Check와 Failover**

Health Check는 Server나 Application이 정상적으로 동작하고 있는지 지속적으로 확인하는 방식이다.

```text
Load Balancer
   │
   ├─ Health Check → Server A : 정상
   └─ Health Check → Server B : 장애
```

장애가 감지되면 비정상 Server로의 Traffic을 차단하거나 Standby 시스템으로 전환할 수 있다.

이 과정을 자동화하면 사람의 개입 없이 장애에 대응할 수 있다.

### **고가용성 관련 구성**

#### **Server와 Database 이중화**

서비스에 따라 다음과 같은 구성을 사용할 수 있다.

- Primary / Replica
- Read Replica
- Cluster
- Multi-Zone 구성
- Multi-Region Deployment

`Master-Slave`라는 용어도 기존 시스템에서 사용되어 왔지만, 최근 제품과 문서에서는 `Primary-Replica` 등 다른 용어를 사용하는 경우가 많다.

#### **Load Balancer**

Load Balancer는 여러 Server에 Traffic을 분산하며 Health Check와 결합하여 비정상 Server를 Traffic 대상에서 제외할 수 있다.

#### **Multi-Region Deployment**

서로 다른 Region에 시스템을 구성하여 특정 지역 또는 Region 단위의 장애에 대응할 수 있다.

다만 Multi-Region을 구성했다고 해서 자동으로 완전한 재해 복구가 이루어지는 것은 아니며 다음 요소를 함께 설계해야 한다.

- Data Replication
- Traffic 전환
- DNS
- Failover
- 데이터 정합성
- 운영 절차

## **6) Disaster Recovery**

---

Disaster Recovery (DR)는 대규모 장애나 재해로 서비스가 정상적으로 운영되지 못하는 상황에서 시스템과 데이터를 복구하기 위한 전체 전략이다.

단순히 장애가 발생한 Server를 자동으로 교체하는 것보다 넓은 개념이다.

DR에서는 다음과 같은 요소를 고려할 수 있다.

- Backup
- Replication
- Standby System
- Region 장애 대응
- Network 복구
- Traffic 전환
- Recovery Procedure
- Recovery Test

### **RPO**

RPO (Recovery Point Objective, 복구 시점 목표)는 장애가 발생했을 때 **최대 어느 시점까지의 데이터 손실을 허용할 것인가**를 나타내는 목표이다.

질문으로 표현하면 다음과 같다.

어느 시점의 데이터까지 복구할 수 있어야 하는가?

최대 얼마만큼의 데이터를 잃는 것을 허용할 수 있는가?

예를 들어 RPO가 24시간이면 장애 상황에서 최대 24시간 범위의 데이터 손실을 허용한다는 목표이다.

Backup 주기와 Replication 전략은 이러한 RPO를 만족하도록 설계해야 한다.

RPO를 매우 작게 만들기 위해서는 보다 빈번한 Backup 또는 Replication이 필요할 수 있다.

### **RTO**

RTO (Recovery Time Objective, 복구 시간 목표)는 장애가 발생한 이후 서비스를 복구하는 데 허용할 수 있는 최대 목표 시간을 의미한다.

질문으로 표현하면 다음과 같다.

서비스가 중단된 후 얼마 이내에 정상화되어야 하는가?

예를 들어 RTO가 4시간이라면 장애를 감지한 후 정해진 복구 과정을 수행하여 목표상 4시간 이내에 서비스를 정상화할 수 있도록 시스템과 절차를 설계한다.

### **RPO와 RTO**

|**구분**|**RPO**|**RTO**|
|---|---|---|
|의미|허용 가능한 데이터 손실 범위|허용 가능한 서비스 복구 시간|
|핵심 질문|얼마나 이전 데이터까지 돌아가도 되는가?|얼마나 빨리 다시 서비스해야 하는가?|
|관련 요소|Backup, Replication|Failover, 복구 자동화, 운영 절차|

쉽게 구분하면 다음과 같다.

```text
RPO → 데이터
RTO → 시간
```

### **Backup 정책**

Backup 정책을 설계할 때는 다음 사항을 고려해야 한다.

- 어떤 데이터를 Backup할 것인가?
- 얼마나 자주 Backup할 것인가?
- Backup 데이터를 어디에 저장할 것인가?
- Backup 데이터를 어떻게 암호화하고 보호할 것인가?
- Backup을 얼마나 오래 보관할 것인가?
- 실제로 Restore가 가능한지 어떻게 검증할 것인가?

중요한 데이터는 운영 시스템과 동일한 장애 영역에만 Backup을 보관하지 않는 것이 중요하다.

필요에 따라 다른 Zone 또는 Region에 Backup을 보관하여 동일한 장애로 원본과 Backup이 동시에 손실되는 위험을 줄일 수 있다.

Backup 파일이 존재한다는 것만으로 복구 가능성이 보장되는 것은 아니다.

따라서 **정기적인 Restore Test를 통해 실제 복구가 가능한지 확인해야 한다.**

**정리**

- 장애는 발생하지 않도록 하는 것뿐 아니라 발생했을 때 빠르게 감지하고 복구하도록 준비해야 한다.
- Monitoring, Logging, Distributed Tracing을 이용하여 장애의 위치와 원인을 파악한다.
- High Availability는 일부 구성 요소가 실패해도 서비스를 지속하도록 설계하는 것이다.
- SPOF 제거, Redundancy, Health Check, Failover가 중요한 구성 원칙이다.
- DR은 대규모 장애 이후 서비스와 데이터를 복구하기 위한 전략이다.
- RPO는 허용 가능한 데이터 손실, RTO는 허용 가능한 복구 시간을 의미한다.
- Backup은 생성하는 것뿐 아니라 실제 Restore Test까지 수행해야 한다.

## **7) 주요 Cloud Platform 비교**

---

대표적인 Public Cloud Platform으로 AWS, Microsoft Azure, Google Cloud가 있다.

세 Platform 모두 Compute, Storage, Network, Database, Container, Serverless, AI/ML 등 다양한 Cloud Service를 제공하지만 서비스 구성 방식과 생태계에는 차이가 있다.

### **공통점**

#### **다양한 Cloud Service Model**

다음과 같은 광범위한 Cloud Resource와 Managed Service를 제공한다.

- Compute
- Storage
- Network
- Database
- Container
- Serverless
- AI / ML
- Security

#### **Shared Responsibility Model**

Cloud Provider와 사용자가 보안 책임을 나누어 가진다.

책임 범위는 사용하는 서비스 유형과 제품에 따라 달라진다.

#### **다양한 요금 모델**

대표적으로 사용량에 기반한 과금 방식과 일정 사용량 또는 기간을 약정하여 비용을 절감하는 방식 등을 제공한다.

#### **Global Infrastructure**

여러 Region과 Availability Zone 등의 Infrastructure를 이용하여 지리적으로 분산된 시스템을 설계할 수 있다.

### **AWS · Azure · Google Cloud 비교**

다음 표는 강의에서 각 Platform의 특징을 비교하기 위한 **대표적인 경향**을 정리한 것이다.

|**구분**|**AWS**|**Azure**|**Google Cloud**|
|---|---|---|---|
|주요 특징|폭넓은 Cloud Service와 생태계|Microsoft 생태계 및 Hybrid 환경과의 연계|Data, Kubernetes, AI 분야의 강점|
|Compute|EC2|Azure Virtual Machines|Compute Engine|
|Object Storage|Amazon S3|Azure Blob Storage|Cloud Storage|
|관계형 Database|Amazon RDS|Azure SQL 계열|Cloud SQL|
|Serverless|AWS Lambda|Azure Functions|Cloud Run / Cloud Functions 계열|
|Kubernetes|Amazon EKS|Azure Kubernetes Service (AKS)|Google Kubernetes Engine (GKE)|
|AI Platform|Amazon SageMaker, Amazon Bedrock|Azure AI 및 Azure OpenAI|Vertex AI|
|Data 분석|다양한 분석 서비스|Azure Data Platform|BigQuery 등|

특정 서비스의 우열은 고정되어 있지 않으며 새로운 서비스가 지속적으로 추가되므로 실제 도입 시점의 요구 사항을 기준으로 비교해야 한다.

### **AWS**

AWS는 다양한 분야의 Cloud Service와 광범위한 생태계를 제공한다.

다양한 Resource를 세밀하게 조합하여 Infrastructure를 구성할 수 있다는 장점이 있지만, 사용할 수 있는 서비스와 옵션이 많기 때문에 처음 학습할 때 복잡하게 느껴질 수 있다.

다음과 같은 상황에서 검토할 수 있다.

- 다양한 Cloud Service를 조합해야 하는 환경
- 광범위한 Reference와 Ecosystem이 필요한 환경
- 여러 유형의 Workload를 하나의 Cloud에서 운영해야 하는 환경

### **Azure**

Azure는 Microsoft의 Enterprise Product와 연계하여 활용할 수 있다.

다음과 같은 환경에서 검토하기 쉽다.

- Windows Server 기반 Infrastructure
- Microsoft Identity 환경
- Microsoft 365를 사용하는 조직
- .NET 기반 Application
- On-Premise Microsoft 환경과 Cloud를 연결하는 Hybrid 환경

### **Google Cloud**

Google Cloud는 Data Analytics, Kubernetes, AI 등의 영역과 연결하여 활용할 수 있다.

대표적인 서비스로 다음이 있다.

- BigQuery
- Google Kubernetes Engine (GKE)
- Vertex AI
- Cloud Spanner
- Compute Engine
- Cloud Storage

다음과 같은 환경에서 검토할 수 있다.

- 대규모 Data 분석
- Kubernetes 중심의 Container Platform
- AI / ML Workload
- Google Cloud의 Data Platform을 적극적으로 활용하는 환경

**정리**

Cloud Platform은 단순히 “어느 회사가 가장 좋은가”로 선택하기 어렵다.

현재 조직에서 사용하는 기술, Data 특성, Network 구조, Security 요구 사항, 운영 인력 등을 함께 고려해야 한다.

### **국내 Cloud Platform**

국내에서도 여러 Cloud Service Provider가 서비스를 제공한다.

강의에서는 다음 네 Platform의 특징을 중심으로 다루었다.

#### **NAVER Cloud**

강의에서는 다음 영역을 주요 특징으로 다루었다.

- AI Ecosystem
- 국내 기업 및 공공 환경을 고려한 Cloud Service
- Sovereign Cloud
- HyperCLOVA X와 연계된 AI Service
- IaaS / PaaS / SaaS
- 금융·의료·공공 분야를 고려한 Cloud 환경

#### **NHN Cloud**

강의에서는 다음 영역을 주요 특징으로 다루었다.

- Game Infrastructure
- 공공 Cloud
- AI Data Center
- SaaS 연계
- 게임 서비스 운영 경험을 활용한 Infrastructure
- Dooray 등의 업무 서비스

#### **KT Cloud**

강의에서는 다음 영역을 주요 특징으로 다루었다.

- IDC (Internet Data Center)
- 공공 Cloud
- 통신 Infrastructure 연계
- Edge Computing
- Enterprise Infrastructure

#### **Kakao Cloud**

강의에서는 다음 영역을 주요 특징으로 다루었다.

- 개발자 중심의 Cloud 환경
- Kubernetes
- Cloud Native Infrastructure
- AI Service
- Mobile 및 Kakao Ecosystem과의 연계

국내 Cloud 역시 특정 산업에 무조건 하나의 Provider가 적합하다고 단정하기보다는 실제 요구 사항과 인증, 규제, 서비스 지원 범위를 확인하여 선택해야 한다.

### **Cloud 선택 기준**

Cloud Platform을 선택할 때는 단순히 서비스 수나 가격만 비교해서는 안 된다.

#### **기술적 적합성**

현재 Application과 Infrastructure에서 필요한 기술을 지원하는지 확인한다.

#### **비용**

다음 비용을 함께 고려해야 한다.

- Compute
- Storage
- Network Traffic
- Managed Service
- 운영 인력
- Migration

#### **지역성과 법적 요구 사항**

Data가 저장되는 Region과 해당 산업에서 요구하는 법률·규제·인증 조건을 확인한다.

#### **기업의 전략 방향**

현재 기업이 사용하는 기술 Stack과 장기적인 Cloud 전략을 고려한다.

#### **조직의 Cloud 성숙도**

Cloud Platform 자체의 기능뿐 아니라 해당 Platform을 실제로 운영할 수 있는 인력이 있는지도 중요하다.

#### **내부 Security Policy**

조직의 Security Policy와 Cloud Provider가 제공하는 Security 기능이 맞는지 검토한다.

#### **SLA**

SLA (Service Level Agreement)에서 보장하는 Availability와 보상 조건 등을 확인한다.

#### **Migration 난이도**

기존 On-Premise 또는 다른 Cloud 환경에서 Application과 Data를 이전하는 데 필요한 비용과 난이도를 고려한다.

```text
Cloud 선택

기술 적합성
    +
비용
    +
Security
    +
법적 요구 사항
    +
조직 역량
    +
SLA
    +
Migration 난이도
```

## **전체 정리**

---

> - VPN은 인터넷 등의 네트워크 위에 암호화된 사설 통신 경로를 구성하며, 전용선은 보다 안정적인 Cloud 연결을 구성할 때 사용할 수 있다.
> 
>- Service Endpoint는 Client가 Service에 접근하는 접점이고 Load Balancer는 여러 Server에 Traffic을 분산하는 역할을 한다.
> 
>- Cloud에서는 Server와 Container의 주소가 동적으로 변경될 수 있으므로 DNS와 Service Discovery 같은 이름 기반 접근 방식이 중요하다.
>
>- VPC와 VNet은 Cloud Resource를 배치하기 위한 논리적인 Network이며 Subnet, Routing, NAT, Security Policy 등을 구성할 수 있다.
> 
>- IaC는 Infrastructure의 원하는 상태를 코드로 정의하여 반복적인 작업을 자동화하고 변경 이력을 관리하는 방식이다.
>
>- Terraform은 Infrastructure Provisioning에, Ansible은 Configuration Management와 IT Automation에 주로 사용하며 두 도구를 함께 사용할 수도 있다.
> 
>- Shared Responsibility Model에서는 Cloud Provider와 Customer가 사용하는 서비스에 따라 Security 책임을 나누어 가진다.
> 
>- IAM은 Identification, Authentication, Authorization과 Account Lifecycle을 관리하며 Least Privilege를 적용하는 기반이 된다.
> 
>- Secret은 Source Code와 분리하여 관리하고 접근 권한, Rotation, Audit까지 함께 고려해야 한다.
> 
>- JWT는 항상 암호화된 Token이 아니며 Claim을 전달하기 위해 서명 또는 암호화할 수 있는 Token 형식이다.
> 
>- 장애 대응에서는 Monitoring, Logging, Distributed Tracing을 통해 문제를 빠르게 발견하고 원인을 추적해야 한다.
> 
>- High Availability는 SPOF를 제거하고 Redundancy, Health Check, Failover 등을 이용하여 서비스 중단을 최소화하는 방식이다.
> 
>- RPO는 허용 가능한 데이터 손실 범위를, RTO는 허용 가능한 복구 시간을 의미한다.
>
>- Backup은 생성뿐 아니라 실제 Restore Test까지 수행해야 한다.
> 
>- AWS, Azure, Google Cloud와 국내 Cloud Platform은 각각 다른 Ecosystem과 특성을 가지므로 기술, 비용, Security, 법적 요구 사항, 조직 역량, SLA, Migration 난이도를 종합하여 선택해야 한다.
