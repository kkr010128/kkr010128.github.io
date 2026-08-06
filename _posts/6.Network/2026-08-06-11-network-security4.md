---
title: Network - Security 4
description: 방화벽과 연계 보안 솔루션 및 ACL 실습
date: 2026-08-06
series: Network
tags:
  - Network
  - AutoEverSW
  - GNS3
---
## Firewall
---

### 개요

방화벽(Firewall)은 신뢰할 수 없는 외부 네트워크와 신뢰할 수 있는 내부 네트워크 사이를 지나는 패킷을 미리 정의한 정책에 따라 허용하거나 차단하는 하드웨어 또는 소프트웨어이다.

네트워크 경계(Perimeter)에 위치하여 내부 시스템을 보호하는 가장 기본적인 보안 장비이며, 일반적으로 DDoS 방어 장비 뒤에 배치된다.

### 주요 기능

#### 접근 제어(Access Control)

접근 제어는 방화벽의 가장 기본적이고 중요한 기능이다.

관리자가 허용(Allow, Permit)하거나 차단(Deny)할 통신 정책(Rule Set)을 정의하면 방화벽은 해당 정책에 따라 패킷을 처리한다.

접근 제어 방식은 다음 두 가지로 구분된다.

- 패킷 필터링(Packet Filtering)
- 프록시(Proxy)

일반적으로 Rule Set은 다음 정보를 기준으로 작성한다.

- 출발지 IP 주소
- 목적지 IP 주소
- 포트 번호
- 프로토콜(TCP, UDP 등)

**Rule Set 작성 절차**

1. 허용해야 하는 서비스를 확인한다.
2. 해당 서비스가 보안상 허용 가능한지 검토한다.
3. 서비스의 동작 방식을 분석하여 필요한 정책을 결정한다.
4. 방화벽에 정책을 적용한다.
5. 적용 결과를 검증한다.

#### 로깅(Logging)과 감사 추적(Audit)

방화벽은 다음과 같은 정보를 로그로 기록한다.

- Rule Set 생성 및 변경
- 관리자 접근
- 패킷 허용
- 패킷 차단

이러한 로그는 보안 사고 발생 시 원인 분석과 공격 경로 추적에 활용된다.

#### 인증(Authentication)

방화벽은 다양한 인증 기능을 지원한다.

- **메시지 인증(Message Authentication)**
	- VPN과 같이 신뢰할 수 있는 통신 환경에서 메시지의 무결성과 신뢰성을 보장한다.



- **사용자 인증(User Authentication)**
	- ID / Password
	- OTP
	- Token 기반 인증

- **클라이언트 인증(Client Authentication)**
	- 접속하는 사용자가 아니라 접속을 시도하는 장비 자체가 정상적인 장비인지 확인하는 방식이다.

#### 데이터 암호화

방화벽은 다른 방화벽과의 통신을 암호화할 수 있다.

일반적으로 IPSec VPN이나 SSL VPN 기능을 이용한다.

### 방화벽의 한계

- 패킷 내부 데이터를 검사하지 않으므로 바이러스나 악성코드를 직접 탐지하지 못한다.
- 내부 사용자의 공격에는 대응이 제한적이다.
- 방화벽을 통과하지 않는 통신은 제어할 수 없다.
- 새로운 공격 기법이나 애플리케이션 계층 공격에는 한계가 있다.

### 방화벽 구조

#### Bastion Host

가장 강력한 보안 정책이 적용되며 외부 연결을 최초로 받아들이는 시스템이다.

```text
Internet
│
Public Subnet
│
Bastion Host
│
├── Server
├── Server
└── Server
```

#### Screening Router

일반 라우터에 패킷 필터링 기능을 추가한 형태이다.

IP 주소와 포트를 이용한 접근 제어만 수행한다.

```text
Internal Network
        │
Screening Router
        │
     Internet
```

#### Single-Homed Gateway

NIC(Network Interface Card)가 하나인 방화벽 구조이다.

일반적으로 Bastion Host 구조라고도 부른다.

특징

- 일반 사용자 계정 삭제
- 불필요한 프로그램 제거
- 대용량 로깅 지원
- IP Forwarding 제거
- Source Routing 제거

```text
Internal Network
        │
Single-Homed Gateway
        │
     Internet
```

#### Dual-Homed Gateway

NIC를 두 개 이상 사용하는 방화벽이다.

외부망과 내부망이 서로 다른 인터페이스를 사용한다.

```text
Internal Network
        │
 Internal NIC
Dual-Homed Gateway
 External NIC
        │
     Internet
```

#### Screened Host Gateway

Screening Router와 Gateway를 함께 사용하는 구조이다.

모든 트래픽은 Gateway를 거쳐 Router로 전달된다.

```text
Internal
    │
Gateway
    │
Router
    │
Internet
```

#### Screened Subnet Gateway

외부망과 내부망 사이에 DMZ를 두는 구조이다.

보안성이 가장 뛰어나지만 구축과 관리 비용이 높다.

```text
Internet
    │
Screening Router
    │
DMZ
    │
Gateway
    │
Screening Router
    │
Internal Network
```

> **정리**
>
> - Bastion Host는 가장 강력한 보안 정책이 적용된 시스템이다.
> - Dual-Homed Gateway는 내부망과 외부망을 물리적으로 분리한다.
> - Screened Subnet Gateway는 가장 높은 수준의 보안을 제공한다.

## ACL (Access Control List)
---


ACL은 라우터에서 패킷을 식별하고 필터링하기 위한 접근 제어 정책이다.

라우터는 ACL을 이용하여 다음 작업을 수행한다.

- 패킷 필터링
- 트래픽 분류
- 접근 제어

### 동작 방식

ACL은 다음 두 가지 방식으로 동작한다.

|구분|설명|
|---|---|
|Inbound ACL|패킷이 인터페이스로 들어올 때 검사|
|Outbound ACL|라우팅이 끝난 후 인터페이스를 나가기 전에 검사|

특징

- 여러 인터페이스에 적용 가능
- 하나의 인터페이스에는 Inbound ACL과 Outbound ACL을 각각 하나씩만 적용 가능
- 하나의 프로토콜에는 하나의 ACL만 적용 가능
- 위에서부터 순서대로 검사
- Subnet Mask 대신 Wildcard Mask를 사용

### ACL 종류

|종류|설명|
|---|---|
|표준 ACL|출발지 IP만 검사|
|확장 ACL|출발지, 목적지, 프로토콜, 포트까지 검사|
|번호 ACL|번호를 이용하여 관리|
|이름 ACL|이름을 이용하여 관리|

번호 ACL은 번호 범위에 따라 종류가 결정된다.

|번호|종류|
|---|---|
|1~99, 1300~1999|표준 ACL|
|100~199, 2000~2699|확장 ACL|

### GNS3 실습

#### 목적

3대의 라우터를 연결하고 ACL을 적용하여 특정 통신을 차단한다.

#### 토폴로지

```text
R1 -------- R2 -------- R3

E2/0      E2/0  E2/1      E2/1

192.168.1.0/24
192.168.2.0/24
```

#### 인터페이스 설정

**R1**

```bash
R1#configure terminal
R1(config)#interface ethernet2/0
R1(config-if)#ip address 192.168.1.1 255.255.255.0
R1(config-if)#no shutdown
R1(config-if)#exit
R1(config)#exit
R1#
```

**R2**

```bash
R2#configure terminal
R2(config)#interface ethernet2/0
R2(config-if)#ip address 192.168.1.254 255.255.255.0
R2(config-if)#no shutdown
R2(config-if)#exit
R2(config)#interface ethernet2/1
R2(config-if)#ip address 192.168.2.254 255.255.255.0
R2(config-if)#no shutdown
R2(config-if)#exit
R2(config)#exit
R2#
```

**R3**

```bash
R3#configure terminal
R3(config)#interface ethernet2/1
R3(config-if)#ip address 192.168.2.1 255.255.255.0
R3(config-if)#no shutdown
R3(config-if)#exit
R3(config)#exit
R3#
```

#### 연결 확인

```bash
R2#show cdp neighbors
```

#### 정적 라우팅

**R1**

```bash
R1(config)#ip route 192.168.2.0 255.255.255.0 192.168.1.254
```

**R3**

```bash
R3(config)#ip route 192.168.1.0 255.255.255.0 192.168.2.254
```

### 표준 ACL

#### 작성 형식

```bash
Router(config)#access-list <번호> permit <출발지 IP> <와일드카드 마스크>

Router(config)#access-list <번호> deny <출발지 IP> <와일드카드 마스크>
```

예시

```bash
R3(config)#access-list 1 deny 192.168.1.1 0.0.0.0
```

- `1` : 표준 ACL 번호
- `deny` : 패킷 차단
- `192.168.1.1` : 차단할 출발지 IP
- `0.0.0.0` : 해당 IP 한 대만 지정

#### 인터페이스 적용

```bash
Router(config-if)#ip access-group <번호> in

Router(config-if)#ip access-group <번호> out
```

예시

```bash
R3(config)#interface ethernet2/1
R3(config-if)#ip access-group 1 out
R3(config-if)#ip access-group 1 in
```

#### 결과 확인

```text
R3#ping 192.168.1.1

데이터가 전송되지 않습니다.
```

```text
R1#ping 192.168.2.1

UUUUU
```

`UUUUU`는 ACL에 의해 패킷이 차단되었음을 의미한다.

### 확장 ACL

#### 작성 형식

```bash
Router(config)#access-list <번호> permit|deny <프로토콜> <출발지 IP> <와일드카드 마스크> <목적지 IP> <와일드카드 마스크>
```

예시

```bash
R3(config)#access-list 101 deny ip 192.168.2.1 0.0.0.0 192.168.1.1 0.0.0.0
```

- `101` : 확장 ACL 번호
- `deny` : 패킷 차단
- `ip` : 모든 IP 프로토콜
- `192.168.2.1` : 출발지 IP
- `0.0.0.0` : 출발지 한 대 지정
- `192.168.1.1` : 목적지 IP
- `0.0.0.0` : 목적지 한 대 지정

나머지 통신 허용

```bash
R3(config)#access-list 101 permit ip any any
```

적용 방법은 표준 ACL과 동일하다.

### ACL 작성 시 주의사항

- 하나의 ACL 번호에는 여러 규칙을 작성할 수 있다.
- ACL은 위에서부터 순서대로 검사한다.
- 먼저 일치한 규칙이 적용되면 이후 규칙은 검사하지 않는다.
- ACL 마지막에는 암묵적으로 `deny ip any any`가 존재한다.
- 일부 통신만 차단하려면 마지막에 반드시 다음 규칙을 추가해야 한다.

```bash
permit ip any any
```

> **정리**
>
> - 방화벽은 네트워크 경계에서 접근 제어를 수행하는 대표적인 보안 장비이다.
> - 방화벽은 접근 제어, 인증, 로깅, 데이터 암호화 기능을 제공하지만 모든 공격을 방어할 수는 없다.
> - ACL은 라우터에서 접근 제어를 수행하는 대표적인 기능이며 표준 ACL과 확장 ACL로 구분된다.
> - ACL은 위에서부터 순차적으로 검사하며 마지막에는 암묵적인 `deny ip any any` 규칙이 적용된다.
> - GNS3 실습을 통해 ACL 정책 적용과 차단 결과를 직접 확인할 수 있다.