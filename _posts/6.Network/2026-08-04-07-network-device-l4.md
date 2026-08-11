---
title: 네트워크 장비 - 4계층 장비
description: L4 장비의 핵심 개념과 Session 기반 동작, Load Balancer, Firewall, Scale Up/Out, 비대칭 경로 문제 및 해결 방법을 정리
date: 2026-08-04
series: Network
tags:
  - Network
  - AutoEverSW
---
## Device 3 ) L4 장비

### 개요

초기의 네트워크 장비는 L2 Switch, Router와 같이 OSI 계층을 기준으로 구분되었다.

이후 NAT, Firewall, Load Balancer, Proxy 등 **4계층 이상의 정보를 활용하는 장비**가 등장하면서 이러한 장비들도 네트워크 장비의 한 종류로 분류하게 되었다.

L4 장비는 **TCP/UDP의 포트 번호, Sequence Number, ACK Number** 등의 정보를 이해하고 이를 기반으로 동작한다.

또한 하나의 패킷만 처리하는 것이 아니라 **통신의 연결 상태(Session)** 를 관리해야 하므로, 세션 정보를 저장하는 **Session Table**을 유지한다.

---

### 특징

- L4(Transport Layer) 헤더 정보를 기반으로 동작한다.
- TCP/UDP의 포트 번호를 이용하여 트래픽을 제어한다.
- 연결 상태(Session)를 추적하며 통신을 관리한다.
- 대표적인 장비로 Load Balancer, Firewall 등이 있다.

이처럼 세션을 기반으로 동작하는 장비를 **Session Device**라고도 한다.

---

### Session Device의 특징

#### 1. Session Table

Session Device는 **Session Table**을 기반으로 동작한다.

Session Table에는 통신에 필요한 상태 정보가 저장되며, 패킷이 들어올 때마다 해당 정보를 조회하여 정상적인 연결인지 확인한다.

또한 Session 정보는 일정 시간이 지나면 삭제되는 **Lifetime(Session Timeout)** 을 가진다.

---

#### 2. Symmetric Routing (대칭 경로)

Session Device는 일반적으로 **대칭 경로(Symmetric Routing)** 를 요구한다.

즉,

- Request 패킷이 지나간 장비와
- Response 패킷이 지나가는 장비가

동일해야 한다.

경로가 달라지면 Session Table에 연결 정보가 존재하지 않아 정상적인 통신이 이루어지지 않을 수 있다.

---

#### 3. 정보 변경

L4 이상의 장비는 필요에 따라 패킷의 정보를 변경할 수 있다.

- NAT : IP 주소와 포트 번호 변경
- L7 Load Balancer : HTTP Header, Cookie 등 애플리케이션 계층 정보 변경

---

> **중간 정리**
>
> - L4 장비는 TCP/UDP 정보를 이해하고 동작한다.
> - Session Table을 이용하여 연결 상태를 관리한다.
> - 대칭 경로(Symmetric Routing)가 유지되어야 한다.
> - NAT, Firewall, Load Balancer는 대표적인 Session Device이다.

---

### 1. Load Balancer

#### 개요

Load Balancer는 여러 대의 서버나 네트워크 장비에 **트래픽을 분산하여 부하를 균등하게 처리**하기 위한 장비이다.

주로 **L4 또는 L7 계층**에서 동작하며 IP 주소, 포트 번호, 애플리케이션 정보를 기반으로 적절한 서버로 요청을 전달한다.

가장 대표적인 역할은 여러 서버에 트래픽을 분산하여 **성능과 가용성을 향상시키는 것**이다.

---

#### Load Balancer가 필요한 이유

대규모 서비스를 운영할 때는 성능이 매우 높은 서버 한 대를 사용하는 것보다 상대적으로 성능이 낮은 서버 여러 대를 사용하는 것이 비용과 확장성 측면에서 효율적인 경우가 많다.

이처럼 서버 수를 늘려 처리 성능을 향상시키는 방식을 **Scale Out**이라고 한다.

하지만 사용자는 서버가 여러 대인지 알 필요 없이 하나의 서비스처럼 이용해야 한다.

이를 위해 Load Balancer는 **Virtual IP(VIP)** 를 제공하고 클라이언트의 요청을 실제 서버(Real Server)로 분산하여 전달한다.

---

#### 종류

#### L4 Load Balancer

- TCP/UDP 등 4계층 정보를 기반으로 부하 분산
- IP 주소와 Port 번호를 이용하여 서버 선택
- 일반적으로 Network Load Balancer(NLB)라고도 한다.

#### L7 Load Balancer

- HTTP, HTTPS, FTP, SMTP 등 애플리케이션 프로토콜 기반으로 부하 분산
- URI, Header, Cookie 등을 기준으로 분산 가능
- Reverse Proxy 형태로 동작
- ADC(Application Delivery Controller)라고도 부른다.

> 대부분의 상용 Load Balancer는 L4와 L7 기능을 모두 지원하며, 어떤 기준으로 분산하는지에 따라 L4 / L7 Load Balancer로 구분한다.

---

#### L4 Switch

L4 Switch는 내부적으로는 L4 Load Balancer와 동일한 기능을 수행하지만, 스위치 형태의 하드웨어 장비이다.

- 부하 분산
- Redirect
- 성능 최적화
- 다수의 네트워크 포트 제공

현재는 HAProxy, Nginx와 같은 소프트웨어 Load Balancer도 많이 사용되지만 전용 장비 형태의 L4 Switch도 여전히 널리 사용된다.

---

#### 서비스 구성

Load Balancer는 다음과 같은 요소를 이용하여 서비스를 구성한다.

| 구성 요소 | 설명 |
|-----------|------|
| Virtual Server | 사용자가 접속하는 논리적인 서비스 |
| Virtual IP(VIP) | 사용자가 접속하는 대표 IP |
| Real Server | 실제 서비스를 수행하는 서버 |
| Real IP(RIP) | 실제 서버의 IP 주소 |

Load Balancer는 VIP로 들어온 요청을 적절한 Real Server의 RIP로 전달한다.

또한 필요에 따라 포트도 변경할 수 있다.

예시)

- VIP : 80
- Real Server : 8080

---

#### 부하 분산 알고리즘

 1. **Round Robin**

- 서버에 순차적으로 요청을 분산
- 가장 단순한 방식
- 작업 시간이 긴 요청이 많으면 부하가 불균형해질 수 있다.

**2. Least Connection**

- 현재 연결(Session)이 가장 적은 서버로 요청 전달
- Session Table을 이용하여 현재 연결 수를 확인
- 작업 시간이 서로 다른 서비스에서 많이 사용

3. **Hash**

- IP, Port 등의 값을 Hash하여 동일 사용자가 지속적으로 같은 서버를 이용하도록 하는 방식
- Session Persistence(Sticky Session)를 구현할 때 많이 사용
- 일반적인 환경에서는 비교적 균등하게 분산된다.

> **강사님 설명**
>
> Hash를 사용하는 대표적인 이유는 Session 유지이다.
>
> 예를 들어 장바구니 정보를 서버 메모리에 저장하는 경우 사용자가 다른 서버로 연결되면 기존 장바구니 정보를 찾지 못할 수 있다.
>
> 따라서 동일한 사용자가 항상 같은 서버로 연결되도록 Hash 기반 부하 분산을 사용하는 경우가 많다.
>
> 최근에는 Cookie, Web Storage, IndexedDB 등을 활용하여 클라이언트에서 상태를 관리하는 방식도 많이 사용된다.

---

### ADC (Application Delivery Controller)

ADC는 **L7(Application Layer)** 에서 동작하는 Load Balancer이다.

L4 장비와 달리 애플리케이션 프로토콜을 이해하고 처리할 수 있으므로 더욱 다양한 기능을 제공한다.

#### 특징

- HTTP Header와 Body를 분석
- URI 기반 분산
- Reverse Proxy 방식으로 동작
- 대부분 L4 기능도 함께 제공

#### 주요 기능

| 기능 | 설명 |
|------|------|
| Load Balancing | 부하 분산 |
| Failover | 장애 발생 시 정상 서버로 자동 전환 |
| Redirection | 요청 재전송 |
| Caching | 콘텐츠 캐싱 |
| Compression | 데이터 압축 |
| Content Rewrite | 콘텐츠 수정 및 재작성 |
| Encoding Conversion | 인코딩 변환 |
| Application Optimization | 애플리케이션 최적화 |
| WAF | Web Application Firewall |
| HTML/XML Validation | 콘텐츠 검증 |

또한 L4 장비에서도 DoS 방어, TCP Session 재사용(Connection Pool) 등의 성능 향상 기능을 제공하기도 한다.

#### SSL Offloading

최근에는 HTTPS 사용이 증가하면서 SSL 암호화/복호화 작업이 웹 서버의 부담이 되고 있다.

ADC는 SSL의 Endpoint 역할을 수행하여 다음과 같이 구성할 수 있다.

```
Client  <-- HTTPS -->  ADC  <-- HTTP -->  Web Server
```

이를 **SSL Offloading**이라고 한다.

전용 ADC는 SSL 가속 카드를 탑재하여 다수의 HTTPS 연결을 효율적으로 처리할 수 있다.

---

### Health Check

Load Balancer는 Real Server의 상태를 지속적으로 확인하여 정상 서버로만 요청을 전달한다.

장애가 발생한 서버는 서비스 그룹에서 제외하고, 정상으로 복구되면 자동으로 다시 포함한다.

#### Health Check 방식

##### ICMP(Ping)

- 서버의 생존 여부만 확인

**TCP Port Check**

- 서비스 포트가 정상적으로 열려 있는지 확인
- TCP Half Open 방식을 사용하기도 한다.

**HTTP Status Check**

- HTTP 응답 코드(200 등)를 확인

**Content Check**

- 실제 콘텐츠를 요청하여 응답 내용까지 검사

#### 주요 설정

| 항목 | 설명 |
|------|------|
| Interval | 헬스 체크 주기 |
| Response Time | 응답 대기 시간 |
| Retries | 재시도 횟수 |
| Timeout | 최대 대기 시간 |
| Dead Interval | 장애 상태에서의 체크 주기 |

> **강사님 설명**
>
> Nginx는 장애 서버를 제외하는 기능은 제공하지만 전용 Load Balancer 수준의 다양한 기능을 모두 제공하는 것은 아니다.
> 따라서 일반적으로 Reverse Proxy로 분류한다.

---

### Fault-Tolerant System (고장 허용 시스템)

고장 허용 시스템은 일부 장비나 구성 요소에 장애가 발생하더라도 서비스가 중단되지 않고 계속 동작하도록 설계된 시스템이다.

이를 위해 서버, 네트워크, 스토리지 등을 이중화(Redundancy)하거나 다중화하여 SPoF를 제거한다.

대표적인 구현 방법은 다음과 같다.

- Active-Active
- Active-Standby
- Load Balancer를 이용한 서버 이중화
- RAID
- Database Replication
- STP/RSTP를 이용한 네트워크 이중화

---

#### 활용 분야

- Web Load Balancer
- Firewall Load Balancer
- VPN Load Balancer

웹 서비스뿐 아니라 다양한 네트워크 서비스에서도 사용된다.

---

> **중간 정리**
>
> - 여러 서버에 트래픽을 분산한다.
> - Scale Out 환경에서 핵심 장비이다.
> - VIP를 통해 하나의 서비스처럼 제공한다.
> - L4와 L7 방식으로 구분된다.
> - Health Check를 이용하여 정상 서버만 서비스한다.
> - Fault-Tolerant System 구현의 핵심 요소 중 하나이다.

### 시스템 확장 방법

서비스의 성능이나 처리 용량이 부족해지면 시스템을 확장해야 한다.

대표적인 확장 방식은 **Scale Up**과 **Scale Out** 두 가지이다.

---

#### (1) Scale Up (수직 확장)

기존 시스템의 성능을 높이는 방식이다.

CPU, 메모리, 디스크 등의 하드웨어를 증설하거나, 더 높은 성능의 서버로 교체하여 서비스를 이전한다.

#### 특징

- 기존 서버의 성능을 향상시키는 방식
- 애플리케이션 구조 변경이 거의 필요 없다.
- 일부 자원(디스크 등)은 비교적 쉽게 확장할 수 있지만 CPU나 메모리는 확장에 제약이 있을 수 있다.
- 일정 규모 이상에서는 성능 향상 대비 비용이 급격히 증가한다.

#### 장점

- 시스템 구조를 크게 변경하지 않아도 된다.
- 애플리케이션 수정이 거의 필요 없다.
- 관리 대상 서버 수가 적다.

#### 단점

- 성능이 높은 장비일수록 비용이 급격히 증가한다.
- 장비의 최대 사양에 도달하면 더 이상 확장하기 어렵다.
- 서버 교체 시 서비스 이전(Migration)이 필요할 수 있다.
- 단일 서버에 의존하므로 SPoF가 발생하기 쉽다.

---

#### (2) Scale Out (수평 확장)

동일하거나 비슷한 성능의 서버를 여러 대 추가하여 병렬로 서비스를 제공하는 방식이다.

#### 특징

- 서버 수를 늘려 전체 처리량을 증가시킨다.
- Load Balancer 등을 이용하여 요청을 여러 서버로 분산한다.
- 분산 처리를 위한 시스템 설계가 필요하다.

#### 장점

- Scale Up보다 비용 효율적으로 확장할 수 있다.
- 서버를 필요한 만큼 단계적으로 추가할 수 있다.
- 서버 일부에 장애가 발생해도 서비스 전체에는 영향이 적어 고장 허용(Fault Tolerance)을 구현하기 쉽다.

#### 단점

- 시스템 구조가 복잡해진다.
- Load Balancer, 분산 저장소 등 추가 인프라가 필요할 수 있다.
- 세션 관리, 데이터 동기화 등 고려해야 할 요소가 많다.

---

### Scale Up vs Scale Out

| 구분 | Scale Up | Scale Out |
|------|----------|-----------|
| 확장 방식 | 기존 서버의 성능 향상 | 서버 수 증가 |
| 비용 | 고성능 장비일수록 급격히 증가 | 단계적으로 확장 가능 |
| 구조 | 단순 | 상대적으로 복잡 |
| 장애 대응 | 단일 장애점(SPoF) 발생 가능 | 장애 허용(Fault Tolerance) 구현 용이 |
| 확장 한계 | 하드웨어 성능 한계 존재 | 서버를 계속 추가하여 확장 가능 |
| 대표 기술 | CPU, RAM, Storage 증설 | Load Balancer, Cluster, Distributed System |

---

> **중간 정리**
>
> - **Scale Up**은 기존 서버의 성능을 높이는 방식이다.
> - **Scale Out**은 서버 수를 늘려 병렬로 처리하는 방식이다.
> - 대규모 서비스에서는 비용 효율성과 가용성 때문에 Scale Out을 주로 사용한다.
> - Scale Out 환경에서는 일반적으로 Load Balancer를 함께 사용하여 트래픽을 분산한다.

### 2. Firewall

#### 개요

Firewall은 네트워크 중간에 위치하여 **미리 정의된 보안 정책(Policy)** 에 따라 트래픽을 허용하거나 차단하는 장비이다.

초기에는 네트워크 보안 장비 전반을 방화벽이라고 부르기도 했지만, 일반적으로는 **L3/L4 계층에서 동작하며 SPI(Stateful Packet Inspection) 기반으로 세션을 추적하는 장비**를 의미한다.

Firewall은 단순히 패킷 하나만 검사하는 것이 아니라 **Session Table**을 유지하며 통신의 상태를 관리한다.

대표적으로 다음과 같은 정보를 저장한다.

| 항목 | 예시 |
|------|------|
| 출발지 IP | 1.1.1.10 |
| 목적지 IP | 10.10.10.11 |
| 출발지 Port | 30513 |
| 목적지 Port | 80 |

Firewall은 NAT와 유사하게 세션 정보를 저장한 후, 패킷이 들어오거나 나갈 때 먼저 Session Table을 조회한다.

이를 통해 해당 패킷이 **내부에서 시작된 정상적인 연결인지**, 또는 **외부에서 임의로 들어온 연결인지**를 판단한다.

---

### Session 관리

#### Session Table

종단 장비가 통신을 시작하면 Firewall은 Session Table에 연결 정보를 기록한다.

세션이 정상적으로 종료되면 해당 정보를 삭제하지만, 종료 패킷이 오지 않는 경우를 대비하여 일정 시간 동안 세션 정보를 유지한다.

Session 정보는 메모리에 저장되므로 메모리 사용량을 고려하여 **Session Timeout**이 설정된다.

---

#### Session Timeout

Session Timeout은 세션 정보를 유지하는 시간이다.

Timeout이 너무 길면 메모리를 많이 사용하고,

너무 짧으면 아직 통신 중인 세션이 삭제되어 정상적인 통신이 끊길 수 있다.

일부 애플리케이션은 오랜 시간 연결을 유지하므로 장비의 Timeout 값보다 애플리케이션의 세션 유지 시간이 길면 문제가 발생할 수 있다.

---

### Session 동기화 문제

세션 장비의 Timeout이 먼저 만료되어 Session Table의 정보가 삭제되었지만,

양쪽 단말은 아직 연결이 유지되고 있다고 판단하는 경우가 있다.

이 상태에서 다시 데이터를 전송하면 Firewall은 해당 세션을 알지 못한다.

특히 Session Table에 없는 상태에서 **SYN이 아닌 ACK 패킷**이 들어오면 정상적인 연결 과정이 아니라고 판단하여 패킷을 폐기한다.

이로 인해 사용자는 연결이 갑자기 끊긴 것처럼 느낄 수 있다.

---

### 해결 방법

#### 네트워크 장비 측

- Session Timeout을 증가시킨다.
- 중간 패킷(ACK 등)을 허용하도록 방화벽 정책을 조정한다.
- Session Timeout 시 양쪽 단말에 세션 종료를 통보한다.

#### 애플리케이션 측

- Keep Alive 기능을 추가하여 일정 주기로 패킷을 전송한다.
- 이를 통해 Session Timeout 이전에 세션을 갱신하여 연결이 유지되도록 한다.

---

> **중간 정리**
>
> - Firewall은 SPI 기반으로 Session Table을 유지한다.
> - Session Timeout은 메모리 사용량과 안정성을 고려하여 설정한다.
> - Timeout이 서로 맞지 않으면 Session 동기화 문제가 발생할 수 있다.
> - Keep Alive 또는 Timeout 조정을 통해 문제를 해결할 수 있다.

### 비대칭 경로(Asymmetric Routing)

네트워크의 가용성을 높이기 위해 회선과 장비를 이중화하면 패킷이 이동할 수 있는 경로가 두 개 이상 존재하게 된다.

이때 요청(Request)과 응답(Response)이 동일한 장비를 통과하는 경우를 **대칭 경로(Symmetric Routing)**, 서로 다른 장비를 통과하는 경우를 **비대칭 경로(Asymmetric Routing)** 라고 한다.

- **대칭 경로** : 요청과 응답이 동일한 세션 장비를 통과
- **비대칭 경로** : 요청과 응답이 서로 다른 세션 장비를 통과

대칭 경로에서는 하나의 세션 장비가 요청과 응답을 모두 확인하므로 세션 정보를 정상적으로 관리할 수 있다.

반면 비대칭 경로에서는 요청을 처리한 장비와 응답을 처리하는 장비가 다르므로, 응답을 받은 장비의 Session Table에 해당 세션 정보가 존재하지 않을 수 있다.

이 경우 방화벽이나 L4 Load Balancer와 같은 Session Device는 이를 **비정상적인 패킷**으로 판단하여 폐기(Drop)할 수 있다.

---

#### 비대칭 경로가 발생하는 이유

네트워크를 설계할 때 경로의 효율성과 이중화만 고려하고, Session Device의 동작 특성을 고려하지 않으면 비대칭 경로가 발생할 수 있다.

즉, 네트워크 관점에서는 정상적인 경로라도 세션 관점에서는 문제가 될 수 있다.

---

#### 해결 방법

1. **대칭 경로가 되도록 네트워크를 설계**
   - 가장 근본적인 해결 방법
   - 요청과 응답이 동일한 Session Device를 통과하도록 구성

2. **Session Table 동기화**
   - 여러 Session Device가 서로 Session Table을 공유
   - 어느 장비로 패킷이 들어와도 동일한 세션 정보를 확인 가능

3. **Session Device에서 경로 보정**
   - 세션 정보가 없는 패킷을 수신하면 해당 세션을 관리하는 다른 장비로 전달하여 처리
   - 일부 상용 방화벽이나 Load Balancer에서 제공하는 기능