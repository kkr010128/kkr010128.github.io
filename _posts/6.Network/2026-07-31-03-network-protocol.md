---
title: Network Protocol
description: MAC 주소, IP 주소, TCP/UDP, ARP, 서브넷 등 OSI 7계층 기반 네트워크 통신 핵심 프로토콜 정리
date: 2026-07-31
series: Network
tags:
  - Network
  - AutoEverSW
---
## 1. 네트워크 통신 방식

### 개요

네트워크에서 데이터를 전송할 때는 **목적지 주소(Address)** 를 기준으로 통신 방식을 구분한다.

대표적인 통신 방식은 Unicast, Broadcast, Multicast, Anycast의 네 가지이다.

### Unicast

Unicast는 하나의 송신자가 하나의 수신자와 통신하는 **1:1 통신 방식**이다.

실제 네트워크에서 이루어지는 대부분의 통신이 Unicast 방식으로 수행된다.

#### 특징

- 1:1 통신
- 하나의 목적지만 지정
- 가장 일반적으로 사용되는 통신 방식

---

### Broadcast

Broadcast는 동일한 네트워크에 존재하는 **모든 호스트**를 대상으로 데이터를 전송하는 방식이다.

목적지 주소가 네트워크 전체를 의미하는 Broadcast Address로 설정되며, 동일한 네트워크의 모든 장비가 해당 패킷을 수신한다.

주로 Unicast 통신을 시작하기 전에 상대방의 위치를 확인하기 위해 사용된다.

#### 특징

- 1:N 통신
- 동일한 네트워크 전체가 목적지
- 상대 장비 탐색에 사용
- 라우터를 넘어 전달되지 않음

---

### Multicast

Multicast는 하나의 송신자가 특정 그룹에 속한 여러 장비와 통신하는 **1:그룹 통신 방식**이다.

Multicast Group Address를 이용하여 해당 그룹에 가입한 호스트에게만 데이터를 전달한다.

동일한 데이터를 여러 사용자에게 동시에 전송해야 하는 서비스에서 많이 사용된다.

#### 특징

- 1:그룹 통신
- Multicast Group 기반
- 동일한 데이터를 여러 사용자에게 동시에 전달

#### 활용 사례

- IPTV
- 사내 방송
- 증권 시세 전송
- 화상 회의(Zoom 등)

---

### Anycast

Anycast는 동일한 서비스를 제공하는 여러 서버 가운데 **가장 가까운 하나의 서버**와 통신하는 방식이다.

최종적으로는 1:1 통신이 이루어지지만, 동일한 Anycast Address를 사용하는 여러 서버 중 가장 효율적인 서버가 응답한다.

IPv4에서는 일부 기능만 구현되어 있으며, IPv6에서는 Anycast를 정식으로 지원한다.

#### 특징

- 최종 통신은 1:1
- 동일한 서비스를 제공하는 여러 서버 존재
- 가장 가까운 서버가 응답

대표적인 활용 사례는 DNS 서버 선택이다.

---

### Unicast와 Anycast 비교

최종 통신은 모두 1:1이지만 통신 대상의 선정 방식에는 차이가 있다.

| 구분 | Unicast | Anycast |
|------|----------|----------|
| 통신 대상 | 하나의 목적지 | 동일 서비스를 제공하는 여러 후보 중 하나 |
| 목적지 | 하나 | 여러 후보 |
| 최종 통신 | 1:1 | 1:1 |

---

### IPv4와 IPv6

현재 가장 많이 사용하는 주소 체계는 IPv4이다.

최근에는 모바일 네트워크와 IDC(Internet Data Center)를 중심으로 IPv6 도입이 확대되고 있다.

IPv6에서는 IPv4와 달리 **Broadcast가 존재하지 않는다.**

Broadcast 대신 **Link Local Multicast**를 이용하여 필요한 장비에게만 데이터를 전달한다.

---

### Link Local Multicast

Link Local Multicast는 동일한 물리적 네트워크에 연결된 특정 그룹의 장비에게만 데이터를 전달하는 방식이다.

**Link Local**이란 라우터를 통과하지 않는 동일한 로컬 네트워크 범위를 의미한다.

#### 특징

- 동일한 로컬 네트워크에서만 동작
- 라우터를 통과하지 않음
- 필요한 그룹에게만 데이터 전달
- Broadcast보다 불필요한 트래픽이 적음

IPv6에서는 다음과 같은 기능을 수행하기 위해 Link Local Multicast를 사용한다.

#### 주소 자동 설정(SLAAC)

SLAAC(Stateless Address Auto Configuration)는 장비가 네트워크에 연결되면 자동으로 IPv6 주소를 설정하는 기능이다.

이 과정에서 자신의 존재를 알리거나 중복 주소를 검사하기 위해 Link Local Multicast를 사용한다.

#### Neighbor Discovery

IPv6에서는 IPv4의 ARP(Address Resolution Protocol)를 사용하지 않는다.

대신 Neighbor Discovery를 이용하여 상대방의 MAC Address를 알아내며, 이 과정에서도 Link Local Multicast가 사용된다.

---

### BUM Traffic

BUM은 다음 세 가지 트래픽을 의미한다.

- Broadcast
- Unknown Unicast
- Multicast

이들은 서로 다른 트래픽이지만 네트워크에서는 매우 유사한 방식으로 처리된다.

#### Unknown Unicast

Unknown Unicast는 목적지 MAC Address는 존재하지만 스위치가 아직 해당 MAC Address를 학습하지 못한 상태의 Unicast 트래픽이다.

스위치는 목적지 포트를 알 수 없으므로 수신 포트를 제외한 모든 포트로 Frame을 전달(Flooding)한다.

동작 방식은 Broadcast와 비슷하지만 목적지 주소 자체는 Unicast라는 점이 다르다.

#### 특징

- 목적지 MAC은 존재
- Switch가 MAC Address Table을 아직 학습하지 못함
- 모든 포트로 Flooding 수행

BUM Traffic이 많아질수록 네트워크 전체의 처리량이 증가하여 성능이 저하될 수 있다.

다만 Ethernet 환경에서는 일반적으로 최초 ARP Broadcast 이후에는 MAC Address를 학습하여 Unicast로 통신하므로 BUM Traffic은 지속적으로 발생하지 않는다.

> **정리**
>
> - Unicast는 가장 일반적인 1:1 통신이다.
> - Broadcast는 동일 네트워크 전체를 대상으로 한다.
> - Multicast는 특정 그룹에게만 데이터를 전달한다.
> - Anycast는 동일 서비스를 제공하는 여러 서버 중 가장 가까운 서버와 통신한다.
> - IPv6는 Broadcast 대신 Link Local Multicast를 사용한다.
> - BUM Traffic이 증가하면 네트워크 성능이 저하될 수 있다.

---

## 2. MAC Address

### 개요

MAC(Media Access Control) Address는 네트워크 인터페이스 카드(NIC)에 부여되는 **물리적 주소(Physical Address)** 이다.

일반적으로 하드웨어가 출하될 때 제조사가 미리 할당하며, 동일한 네트워크에서 장비를 구분하기 위한 고유한 식별자로 사용된다.

강의에서는 **MAC Address는 NIC의 주민등록번호와 같다**고 설명하였다.

IP 주소를 택배를 받을 주소에 비유한다면, MAC Address는 실제로 택배를 받는 집의 위치와 같은 개념이다.

---

### MAC Address의 구조

모든 제조사가 독립적으로 MAC Address를 생성하면 중복 문제가 발생할 수 있다.

이를 방지하기 위해 IEEE가 제조사별 주소 풀을 관리하며, 각 제조사에 고유한 제조사 코드를 할당한다.

MAC Address는 총 **48비트**로 구성된다.

| 구분 | 크기 | 설명 |
|------|------|------|
| OUI (Organizationally Unique Identifier) | 24비트 | 제조사 코드 |
| UAA (Universally Administered Address) | 24비트 | 제조사가 장비별로 부여하는 주소 |

일반적으로 16진수 12자리 형태로 표현한다.

예시

```text
00:1A:2B:3C:4D:5E
```

앞의 24비트는 제조사를 의미하고, 뒤의 24비트는 해당 제조사에서 장비를 구분하기 위해 사용한다.

---

### MAC Address는 항상 유일한가?

일반적으로는 고유한 주소가 부여되지만 반드시 전 세계에서 유일한 것은 아니다.

제조사의 실수나 의도적인 변경으로 동일한 MAC Address가 존재할 수도 있다.

그러나 동일한 로컬 네트워크에서만 중복되지 않으면 큰 문제가 발생하지 않는다.

그 이유는 Router를 통과할 때마다 새로운 Ethernet Frame이 생성되기 때문이다.

즉,

- MAC Address는 Hop마다 변경된다.
- IP Address는 최종 목적지까지 유지된다.

이것이 MAC Address와 IP Address의 가장 큰 차이점이다.

### MAC Address 변경

일반적으로 MAC Address는 ROM(Read Only Memory)에 저장되어 출하되므로 변경할 수 없는 주소로 알려져 있다.

그러나 실제로는 운영체제가 부팅되면서 MAC Address 정보를 메모리에 적재하여 사용하므로 소프트웨어적으로 변경하여 사용할 수도 있다.

#### 변경 방법

- **Windows**
  - 네트워크 어댑터 Driver의 속성에서 MAC Address 변경 기능 제공
- **Linux**
  - `GNU MacChanger`와 같은 도구를 사용하거나 네트워크 설정 파일에 MAC Address를 지정하여 변경 가능

---

### MAC Address의 동작

NIC(Network Interface Card)는 자신의 MAC Address를 기준으로 수신한 Frame을 처리할지 여부를 결정한다.

#### 기본 동작 과정

1. 전기 신호를 수신한다.
2. 2계층에서 Frame 형태로 변환한다.
3. 목적지 MAC Address를 확인한다.
4. 자신의 MAC Address와 비교한다.
5. 주소가 일치하면 상위 계층으로 전달한다.
6. 주소가 일치하지 않으면 NIC에서 폐기한다.

다만 다음과 같은 경우에는 자신의 MAC Address가 아니더라도 처리 대상으로 인식한다.

- Broadcast Address
- Multicast Address

이 경우 NIC는 Frame을 운영체제(OS)로 전달하며, 이후 실제 처리는 OS나 애플리케이션에서 수행한다.

---

### IPv6와 Link Local Multicast

IPv4에서는 Broadcast를 이용하여 네트워크 전체에 패킷을 전달한다.

하지만 Broadcast는 모든 장비가 패킷을 수신하고 처리 여부를 확인해야 하므로 불필요한 자원 사용이 발생한다.

IPv6에서는 이러한 문제를 해결하기 위해 Broadcast를 제거하고 **Link Local Multicast**를 사용한다.

필요한 Multicast Group에 가입한 장비만 패킷을 수신하므로 네트워크 트래픽과 시스템 자원 사용을 줄일 수 있다.

---

### 무차별 모드 (Promiscuous Mode)

무차별 모드(Promiscuous Mode)는 NIC가 자신의 MAC Address와 관계없이 **모든 패킷을 수신하여 분석**할 수 있도록 하는 동작 모드이다.

기본적으로 NIC는 자신의 MAC Address나 Broadcast, Multicast 패킷만 처리한다.

그러나 패킷 분석이나 네트워크 모니터링을 위해서는 다른 장비의 패킷도 확인해야 하는 경우가 있다.

이때 NIC를 Promiscuous Mode로 설정하면 모든 Frame을 메모리로 전달하여 분석할 수 있다.

대표적인 활용 사례는 **Wireshark**와 같은 패킷 분석 프로그램이다.

---

### 여러 개의 MAC Address

MAC Address는 장비가 아니라 **NIC에 종속되는 주소**이다.

따라서 하나의 장비에 여러 개의 NIC가 장착되어 있다면 NIC마다 각각 다른 MAC Address를 가진다.

대표적인 예는 다음과 같다.

- Router
- Multi Layer Switch
- 다중 NIC를 사용하는 서버

> **정리**
>
> - MAC Address는 제조사가 부여하는 48비트 물리 주소이다.
> - 앞의 24비트는 제조사(OUI), 뒤의 24비트는 장비 식별(UAA)에 사용된다.
> - MAC Address는 Hop마다 변경되고, IP Address는 종단 간 유지된다.
> - Promiscuous Mode에서는 모든 Frame을 분석할 수 있다.
> - MAC Address는 NIC마다 하나씩 존재한다.

---

## 3. IP Address

### 개요

OSI 7계층에서 주소를 사용하는 계층은 2계층과 3계층이다.

2계층에서는 MAC Address를 사용하고, 3계층에서는 **IP(Internet Protocol) Address**를 사용한다.

IP Address는 사용자가 환경에 맞게 변경할 수 있는 **논리적 주소(Logical Address)** 이며, 네트워크를 구분하고 호스트를 식별하기 위해 사용된다.

IP Address는 크게 두 부분으로 구성된다.

- Network Address
- Host Address

Network Address는 동일한 네트워크를 의미하며, Host Address는 해당 네트워크 안에서 개별 장비를 구분한다.

---

### 주소 체계

#### IPv4

IPv4는 32비트 주소 체계를 사용한다.

32비트는 8비트씩 네 개의 옥텟(Octet)으로 구성되며, 각 옥텟은 `.`으로 구분하여 10진수 형태로 표현한다.

예시

```text
192.168.10.1
```

IPv4는 Network Address와 Host Address를 구분하여 사용할 수 있다.

---

#### IPv6

IPv6는 128비트 주소 체계를 사용한다.

IPv4의 주소 부족 문제를 해결하기 위해 등장했으며, 현재 일부 모바일 네트워크와 IDC를 중심으로 사용이 확대되고 있다.

---

### Classful 주소 체계

초기의 IPv4는 필요한 호스트 수에 따라 네트워크를 A, B, C, D, E 다섯 개의 클래스로 구분하였다.

| Class | 주소 범위 | 용도 |
|--------|-----------|------|
| A | 0.0.0.0 ~ 127.255.255.255 | 대규모 네트워크 |
| B | 128.0.0.0 ~ 191.255.255.255 | 중규모 네트워크 |
| C | 192.0.0.0 ~ 223.255.255.255 | 소규모 네트워크 |
| D | 224.0.0.0 ~ 239.255.255.255 | Multicast |
| E | 240.0.0.0 ~ 255.255.255.255 | 예약 |

각 클래스는 고정된 네트워크 크기를 사용하였다.

예를 들어 Class C는 `/24` 네트워크를 사용하며 일반적인 사설 네트워크에서 가장 많이 볼 수 있는 형태이다.

---

### Subnet Mask

Subnet Mask는 하나의 IP Address에서 어디까지가 Network Address이고 어디부터 Host Address인지를 나타내는 값이다.

다음 두 표현은 동일한 의미이다.

```text
192.168.0.0/24
```

```text
192.168.0.0 255.255.255.0
```

`/24`는 앞의 24비트가 Network Address임을 의미한다.

즉, `192.168.0`까지 동일하면 같은 네트워크로 판단한다.

초기의 Classful 방식에서는 클래스마다 Subnet Mask 크기가 고정되어 있었다.

---

### Wildcard Mask

Wildcard Mask는 Subnet Mask의 0과 1을 반대로 표현한 형태이다.

주로 ACL(Access Control List)이나 방화벽 정책을 설정할 때 사용된다.

---

### IPv4 주소 부족

인터넷이 급속도로 보급되면서 IPv4 주소는 빠르게 부족해지기 시작했다.

기존의 Classful 주소 체계만으로는 증가하는 장비를 모두 수용하기 어려웠다.

이를 해결하기 위해 다음과 같은 기술이 등장하였다.

- CIDR(Classless Inter-Domain Routing)
- NAT(Network Address Translation)
- Private IP
- IPv6

> **정리**
>
> - IP Address는 사용자가 변경 가능한 논리 주소이다.
> - IP는 Network Address와 Host Address로 구성된다.
> - IPv4는 32비트, IPv6는 128비트 주소 체계를 사용한다.
> - IPv4 주소 부족 문제를 해결하기 위해 CIDR, NAT, IPv6 등이 등장하였다.

### CIDR (Classless Inter-Domain Routing)

CIDR(Classless Inter-Domain Routing)은 IPv4 주소 부족 문제를 해결하기 위해 등장한 주소 체계이다.

기존 Classful 방식은 클래스별로 네트워크 크기가 고정되어 있어 많은 IP 주소가 낭비되는 문제가 있었다.

CIDR은 서브넷 마스크의 크기를 자유롭게 지정하여 필요한 만큼만 네트워크를 할당할 수 있도록 한다.

#### 서브네팅과 슈퍼네팅

CIDR에서는 네트워크를 분할하거나 병합하여 사용할 수 있다.

- **서브네팅(Subnetting)**
  - 하나의 큰 네트워크를 여러 개의 작은 네트워크로 분할하는 방식
- **슈퍼네팅(Supernetting, Route Summarization)**
  - 여러 개의 네트워크를 하나의 큰 네트워크로 묶는 방식
  - 라우터에서 여러 경로를 하나의 경로로 광고할 때 주로 사용한다.

#### 실무에서 고려하는 사항

**사용자 관점**

- 사용할 수 있는 IP 범위를 확인한다.
- 기본 게이트웨이(Default Gateway)와 Subnet Mask가 올바르게 설정되어 있는지 확인한다.

**네트워크 설계자 관점**

- 네트워크에 연결될 단말 수를 고려하여 적절한 네트워크 크기를 설계한다.

---

### Public IP와 Private IP

인터넷에서 통신하려면 전 세계에서 유일한 IP Address가 필요하다.

그러나 내부 네트워크에서는 전 세계적으로 유일한 주소가 필요하지 않으므로 Private IP를 사용할 수 있다.

#### Public IP

- 인터넷에서 유일한 주소
- 외부 네트워크와 직접 통신 가능

#### Private IP

- 내부 네트워크에서만 사용하는 주소
- NAT(Network Address Translation)를 통해 인터넷에 접속할 수 있다.

Private IP 대역은 다음과 같다.

| 주소 대역 | 범위 |
|-----------|------|
| `10.0.0.0/8` | `10.0.0.0 ~ 10.255.255.255` |
| `172.16.0.0/12` | `172.16.0.0 ~ 172.31.255.255` |
| `192.168.0.0/16` | `192.168.0.0 ~ 192.168.255.255` |

일반적인 가정용 공유기는 `192.168.0.0/24` 대역을 많이 사용하며, 모바일 네트워크에서는 `10.x.x.x` 또는 `172.16.x.x` 대역을 사용하는 경우가 많다.

---

### Bogon IP

Bogon IP는 IANA(Internet Assigned Numbers Authority)가 예약하여 일반적인 Public IP로 할당되지 않는 주소 대역이다.

인터넷 라우터에는 이러한 주소에 대한 경로가 존재하지 않는다.

따라서 외부에서 Bogon IP를 이용한 통신이 발생하면 다음과 같은 가능성을 의심할 수 있다.

- IP Spoofing
- 잘못된 주소 설정

실무에서는 이러한 주소를 방화벽 등에서 필터링하는 경우가 많다.

| IP 대역 | 용도 |
|---------|------|
| `0.0.0.0/8` | This Network |
| `10.0.0.0/8` | Private Network |
| `100.64.0.0/10` | 통신사업자 CGNAT |
| `127.0.0.0/8` | Loopback |
| `127.0.53.53` | Name Collision |
| `169.254.0.0/16` | Link Local |
| `172.16.0.0/12` | Private Network |
| `192.0.0.0/24` | IETF 예약 |
| `192.0.2.0/24` | 테스트용 |
| `192.168.0.0/16` | Private Network |
| `198.51.100.0/24` | 테스트용 |
| `203.0.113.0/24` | 테스트용 |
| `224.0.0.0/4` | Multicast |
| `240.0.0.0/4` | 예약 |
| `255.255.255.255/32` | Broadcast |

---

### IP 주소 발신지 확인

IP Address를 이용하면 해당 주소를 할당받은 기관이나 조직을 확인할 수 있다.

대표적으로 다음 서비스를 사용한다.

- Whois
- KISA WHOIS

> **정리**
>
> - CIDR은 Classful 주소 체계의 비효율성을 해결하기 위해 등장하였다.
> - CIDR에서는 서브네팅과 슈퍼네팅을 이용해 주소 공간을 효율적으로 관리한다.
> - Public IP는 인터넷에서 사용되고 Private IP는 내부 네트워크에서 사용된다.
> - Bogon IP는 일반적인 인터넷 통신에 사용되지 않는 예약 주소이다.

---

## 4. TCP & UDP

### 개요

TCP(Transmission Control Protocol)와 UDP(User Datagram Protocol)는 OSI 7계층의 **전송 계층(Transport Layer)** 에서 동작하는 대표적인 프로토콜이다.

전송 계층은 목적지 장비를 찾는 것이 아니라 **장비 내부의 애플리케이션(프로세스)** 을 정확하게 찾아 데이터를 전달하는 역할을 수행한다.

또한 데이터를 여러 개의 패킷으로 분할하여 전송하고, 수신 측에서 올바르게 재조립할 수 있도록 관리한다.

---

### 서비스 포트

TCP/IP 스택에서는 계층마다 상위 프로토콜을 구분하기 위한 식별자를 사용한다.

| 계층 | 식별 정보 |
|------|-----------|
| 2계층 | Ether Type |
| 3계층 | Protocol Number |
| 4계층 | Port Number |

실제 통신에서는 출발지와 목적지 모두 포트 번호를 사용하지만, 일반적으로 포트 번호라고 하면 목적지 포트를 의미한다.

---

### Port Range

포트 번호는 크게 세 가지 범위로 구분된다.

| 구분 | 범위 | 설명 |
|------|------|------|
| Well Known Port | `0 ~ 1023` | IANA가 예약한 표준 서비스 |
| Registered Port | `1024 ~ 49151` | 일반 애플리케이션 등록용 |
| Dynamic / Private Port | `49152 ~ 65535` | 임시 포트, 클라이언트에서 주로 사용 |

대표적인 Well Known Port는 다음과 같다.

- HTTP : TCP 80
- HTTPS : TCP 443
- SMTP : TCP 25

쿠버네티스(Kubernetes)는 `30000 ~ 32767` 범위를 NodePort 용도로 사용한다.

---

### TCP

TCP는 **연결 지향(Connection-Oriented)** 전송 프로토콜이다.

데이터가 정확하게 전달되는 것이 중요한 대부분의 서비스에서 사용된다.

대표적인 예는 다음과 같다.

- HTTP
- HTTPS
- SSH
- SMTP
- FTP
- Database 연결

#### 3-Way Handshake

TCP는 통신을 시작하기 전에 연결을 먼저 설정한다.

연결 과정은 다음과 같다.

```text
Client               Server

SYN ------------->

      <------------- SYN + ACK

ACK -------------->
```

총 세 번의 메시지를 교환하므로 **3-Way Handshake**라고 한다.

---

### Sequence Number와 ACK

데이터를 여러 개의 패킷으로 나누어 전송하면 순서가 바뀌거나 일부가 유실될 수 있다.

이를 해결하기 위해 TCP는 다음 정보를 사용한다.

- Sequence Number
- ACK(Acknowledgement Number)

Sequence Number는 패킷의 순서를 나타내고, ACK는 정상적으로 수신한 패킷을 확인하는 번호이다.

이를 통해 패킷 유실이나 순서 변경을 감지할 수 있다.

---

### Window Size와 Sliding Window

패킷을 하나씩 보내고 응답을 기다리면 전송 효율이 매우 떨어진다.

TCP는 여러 개의 패킷을 한 번에 전송한 후 ACK를 받는 방식을 사용한다.

- 한 번에 전송 가능한 패킷 수 → **Window Size**
- 여러 패킷을 연속으로 전송하는 방식 → **Sliding Window**

Sliding Window는 네트워크 상태에 따라 크기를 고정하거나 동적으로 조절할 수 있다.


### UDP

UDP(User Datagram Protocol)는 TCP와 달리 신뢰성 보장을 위한 기능을 최소화한 전송 계층 프로토콜이다.

연결을 설정하지 않고 데이터를 전송하므로 처리 과정이 단순하며 지연 시간이 짧다.

#### 특징

- 연결 설정 과정(3-Way Handshake)이 없다.
- Sequence Number를 사용하지 않는다.
- ACK를 사용하지 않는다.
- 재전송 기능이 없다.
- 흐름 제어 및 오류 제어 기능이 없다.

즉, 데이터가 손실되거나 순서가 바뀌어도 이를 복구하지 않는다.

#### 사용되는 환경

UDP는 신뢰성보다 **실시간성**이 중요한 서비스에서 사용된다.

대표적인 예는 다음과 같다.

- 음성 통화
- 실시간 스트리밍
- IPTV
- 사내 방송
- 증권 시세 전송
- Multicast 기반 서비스

이러한 서비스는 일부 패킷이 손실되더라도 재전송으로 인해 지연이 발생하는 것이 더 큰 문제가 된다.

반대로 넷플릭스나 유튜브와 같은 일반적인 동영상 서비스는 일정량의 데이터를 미리 버퍼링할 수 있으므로 TCP를 사용한다.

---

### TCP와 UDP 비교

| 구분 | TCP | UDP |
|------|-----|-----|
| 연결 방식 | 연결 지향형 | 비연결형 |
| 오류 제어 | 지원 | 지원하지 않음 |
| 흐름 제어 | 지원 | 지원하지 않음 |
| 전송 방식 | Unicast | Unicast, Broadcast, Multicast |
| 통신 방식 | Full Duplex | Half Duplex |
| 주요 사용처 | 일반 데이터 통신 | 실시간 데이터 전송 |

> **정리**
>
> - TCP는 신뢰성을 우선하는 전송 프로토콜이다.
> - UDP는 실시간성을 우선하는 전송 프로토콜이다.
> - 전송 계층은 포트 번호를 이용해 목적지 애플리케이션을 식별한다.

---

## 5. ARP (Address Resolution Protocol)

### 개요

ARP(Address Resolution Protocol)는 **IP Address를 이용해 목적지의 MAC Address를 알아내는 프로토콜**이다.

네트워크에서는 IP 주소를 이용해 통신을 시작하지만 실제 프레임을 전송하기 위해서는 목적지의 MAC 주소가 반드시 필요하다.

즉, ARP는 **3계층(IP)** 과 **2계층(MAC)** 을 연결하는 역할을 수행한다.

> IP 주소는 목적지를 나타내는 논리 주소이고, MAC 주소는 실제 데이터를 전달하기 위한 물리 주소이다.

---

### ARP가 필요한 이유

출발지는 목적지의 IP 주소는 알고 있지만 MAC 주소는 알지 못하는 경우가 많다.

이 상태에서는 2계층 프레임을 만들 수 없어 데이터를 전송할 수 없다.

이를 해결하기 위해 ARP를 사용한다.

동작 과정은 다음과 같다.

1. 목적지 IP를 확인한다.
2. ARP Broadcast를 전송한다.
3. 목적지 장비가 자신의 MAC Address를 응답한다.
4. 응답받은 MAC Address를 이용해 캡슐화를 수행한다.
5. 데이터를 전송한다.

비유하면,

- IP 주소 → 집 주소
- MAC 주소 → 집 안의 실제 수신인
- ARP → "이 주소에 계신 분 누구인가요?"라고 네트워크 전체에 묻는 과정이다.

---

### ARP Table

매번 ARP Broadcast를 수행하면 네트워크 효율이 크게 떨어진다.

이를 방지하기 위해 운영체제는 메모리에 ARP 정보를 저장한다.

이를 **ARP Table**이라고 한다.

ARP Table은 다음 명령으로 확인할 수 있다.

```bash
arp -a
```

ARP Table은 일정 시간 동안만 유지된다.

논리 주소(IP)는 언제든 변경될 수 있으므로 일정 시간 통신이 없으면 해당 정보를 삭제한다.

네트워크 장비는 CPU 부담을 줄이기 위해 일반 PC보다 ARP 정보를 더 오래 유지하거나 ARP 요청을 제한하는 경우가 많다.

---

### Gratuitous ARP (GARP)

GARP(Gratuitous ARP)는 자신의 IP 주소를 대상 IP에도 넣어 ARP 요청을 보내는 방식이다.

상대방의 MAC 주소를 알아내기 위한 것이 아니라 **자신의 IP와 MAC 정보를 알리는 것**이 목적이다.

주요 사용 목적은 다음과 같다.

- IP 주소 중복 확인
- 다른 장비의 ARP Table 갱신
- HA(High Availability) 환경에서 장애 조치

---

### Reverse ARP (RARP)

RARP(Reverse ARP)는 자신의 MAC Address는 알고 있지만 IP Address를 모르는 장비가 IP 주소를 요청하는 프로토콜이다.

과거에는 디스크가 없는 워크스테이션 등에서 사용되었지만 기능이 제한적이어서 현재는 대부분 BOOTP와 DHCP가 대신 사용한다.

현재는 거의 사용되지 않는다.

> **정리**
>
> - ARP는 IP 주소를 MAC 주소로 변환하는 프로토콜이다.
> - ARP Broadcast를 줄이기 위해 ARP Table을 사용한다.
> - GARP는 자신의 정보를 알리기 위한 ARP이며, RARP는 과거 IP 주소 할당에 사용되었다.

---

## 6. Subnet & Gateway

### Gateway

Gateway는 서로 다른 네트워크를 연결하는 출입구 역할을 하는 장비이다.

같은 네트워크 내부에서는 직접 통신이 가능하지만, 다른 네트워크와 통신하려면 반드시 Gateway를 거쳐야 한다.

따라서 PC에는 목적지를 찾지 못했을 때 사용할 **Default Gateway**를 설정한다.

> 아파트 단지 안에서는 자유롭게 이동할 수 있지만, 다른 단지로 이동하려면 정문을 반드시 지나야 하는 것과 같은 개념이다.

---

### Proxy ARP

Proxy ARP는 Gateway가 대신 ARP 응답을 수행하는 기능이다.

원격 네트워크에 있는 장비라도 Gateway가 자신의 MAC 주소를 응답하여 통신을 가능하게 만든다.

Cisco Router에서는 기본적으로 활성화되어 있는 경우가 많으며, 사용자는 이를 인식하지 못한 채 사용하는 경우도 있다.

---

### Subnet

Subnet은 목적지가 **같은 네트워크인지, 다른 네트워크인지**를 판단하기 위한 기준이다.

호스트는 자신의 IP 주소와 Subnet Mask를 이용해 목적지가 같은 네트워크인지 계산한다.

- 같은 네트워크이면 직접 통신한다.
- 다른 네트워크이면 Default Gateway로 패킷을 전송한다.

Subnet은 단순히 네트워크를 나누는 개념이 아니라 **로컬 통신과 원격 통신을 구분하는 기준**이 된다.

> **정리**
>
> - Gateway는 서로 다른 네트워크를 연결하는 출입구 역할을 한다.
> - Proxy ARP는 Gateway가 대신 ARP 응답을 수행하는 기능이다.
> - Subnet은 로컬 통신과 원격 통신을 구분하는 기준이다.