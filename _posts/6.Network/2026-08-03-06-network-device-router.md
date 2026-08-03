---
title: Network Device 2 - Router
description: L3 라우팅 핵심 - 라우팅 테이블, Next Hop, TTL, Static / Dynamic Routing
date: 2026-08-03
series: Network
tags:
  - Network
  - AutoEverSW
---

# Device 2 ) Router / L3 Switch

---

## 개요

라우터(Router)는 **OSI 7계층의 3계층(Network Layer)** 에서 동작하는 장비이다.

패킷의 목적지 IP 주소를 확인하고, 라우팅 테이블(Routing Table)을 조회하여 최적의 경로로 패킷을 전달(Forwarding)한다.

원격 네트워크 간 통신을 위해 반드시 필요한 장비이며, 서로 다른 네트워크를 연결하는 핵심 장비이다.

---

## L3 Switch

L3 Switch는 스위치 기능(L2)과 라우터 기능(L3)을 함께 제공하는 장비이다.

일반적으로

- 스위칭은 ASIC(Hardware)
- 라우팅은 Hardware 또는 Software

로 처리하며 최근에는 라우터와 L3 Switch의 기능 차이가 많이 줄어들었다.

---

# 라우터의 역할

라우터의 역할은 크게 세 가지이다.

1. 경로 지정(Path Determination)
2. 브로드캐스트 컨트롤(Broadcast Control)
3. 프로토콜 변환(Protocol Conversion)

---

## 경로 지정 (Path Determination)

라우터는 다양한 경로 정보를 수집하여 **라우팅 테이블(Routing Table)** 을 만든다.

패킷이 들어오면 목적지 IP 주소와 라우팅 테이블을 비교하여 가장 적절한 경로로 패킷을 전달한다.

> **Switch와 Router의 차이**
>
> - Switch : 목적지를 모르면 Flooding
> - Router : 목적지를 모르면 Drop

라우터는 패킷을 전달할 때 기존 L2 헤더를 제거한 뒤 다음 네트워크에 맞는 새로운 L2 헤더를 생성한다.

경로 지정은 두 과정으로 나뉜다.

1. 경로 정보를 학습
2. 학습한 정보를 이용해 패킷 포워딩

---

## 경로 정보를 얻는 방법

라우터는 다음 세 가지 방법으로 경로를 학습한다.

### 1. Direct Connected

직접 연결된 네트워크이다.

인터페이스에 IP를 설정하면 자동으로 생성된다.

- 자동 생성
- 삭제 불가
- 인터페이스 Down 시 자동 제거

---

### 2. Static Routing

관리자가 직접 목적지와 Next Hop을 입력하는 방식이다.

#### 특징

- 설정이 간단하다.
- 관리가 쉽다.
- 작은 네트워크에 적합하다.
- 장애를 자동으로 우회하지 못한다.

---

### 3. Dynamic Routing

라우터끼리 경로 정보를 교환하여 자동으로 경로를 학습한다.

#### 특징

- 경로를 자동 학습
- 장애 발생 시 우회 가능
- 대규모 네트워크에 적합

---

## 경로 정보의 규모

인터넷의 경로 정보는 지속적으로 증가하고 있다.

CIDR(Classless Inter-Domain Routing)이 도입되면서 다양한 Prefix 길이의 네트워크가 사용되고, 라우팅 테이블도 매우 커졌다.

이를 줄이기 위해 라우터는 **Route Summarization(경로 요약)** 을 사용하여 여러 Prefix를 하나로 묶는다.

또한 목적지와 일치하는 경로가 여러 개라면 **Longest Prefix Match** 를 이용하여 가장 구체적인 경로를 선택한다.

---

## 브로드캐스트 컨트롤

라우터는 서로 다른 네트워크를 연결하지만 브로드캐스트 패킷은 전달하지 않는다.

따라서 브로드캐스트 도메인을 분리하여 불필요한 Broadcast Traffic을 차단한다.

---

## Hop by Hop 라우팅

인터넷에서는 하나의 라우터가 목적지까지의 전체 경로를 결정하지 않는다.

각 라우터는 자신의 라우팅 테이블만 조회하여 **Next Hop** 만 결정한다.

다음 라우터 역시 같은 과정을 반복하여 최종 목적지까지 패킷을 전달한다.

이를 **Hop by Hop Routing** 이라고 한다.

> **비유**
>
> 네비게이션은 현재 위치에서 다음 길만 계속 안내한다.
>
> 라우터도 목적지까지 모든 경로를 결정하지 않고 다음 라우터만 결정한다.

---

## Next Hop 지정 방법

| 방법 | 설명 |
|------|------|
| Next Hop IP | 가장 일반적인 방식 |
| Interface | 출구 인터페이스 지정 |
| Interface + Next Hop | 두 정보를 함께 지정 |

---

## TTL (Time To Live)

라우터는 패킷을 전달할 때마다 TTL 값을 1 감소시킨다.

TTL이 0이 되면 패킷을 폐기한다.

따라서 라우팅 루프가 발생하더라도 패킷이 영구적으로 순환하지 않는다.

---

## 프로토콜 변환

과거에는 LAN과 WAN이 서로 다른 2계층 프로토콜을 사용하였다.

예를 들어

- LAN : Ethernet
- WAN : PPP

라우터는 Ethernet Frame을 제거하고 PPP Frame으로 다시 캡슐화하여 WAN으로 전달하였다.

현재는 대부분 Ethernet 기반이므로 프로토콜 변환의 중요성은 과거보다 많이 줄어들었다.