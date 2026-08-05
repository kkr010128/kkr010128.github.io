---
title: Ping을 막는 이유는 무엇일까
description: CMP의 실제 역할과 Ping 차단의 이유, 운영 환경에서 ICMP를 제한하는 사례 메모
date: 2026-08-04
series: TechNotes
tags:
  - Notes
  - CS
  - Network
---

### Q. Ping을 막는 이유는 무엇일까? ICMP는 Ping만을 위한 프로토콜일까?

네트워크를 공부하다 보면 일부 서버는 `ping`이 동작하지 않는 경우를 자주 볼 수 있다.

그렇다면 Ping을 차단하는 이유는 무엇일까? 또한 ICMP는 Ping만을 위해 존재하는 프로토콜일까?

### A. ICMP는 Ping만을 위한 프로토콜이 아니다.

많은 사람들이 ICMP를 Ping 프로토콜이라고 생각하지만, Ping은 **ICMP를 이용하는 하나의 기능**일 뿐이다.

ICMP(Internet Control Message Protocol)는 네트워크 장비들이 **오류를 알리거나 네트워크 상태를 진단**하기 위해 사용하는 제어 프로토콜이다.

대표적으로 다음과 같은 기능을 수행한다.

- Echo Request / Echo Reply (Ping)
- Destination Unreachable
- Time Exceeded (Traceroute)
- Redirect
- Fragmentation Needed (PMTU Discovery)

즉, Ping은 ICMP의 여러 메시지 타입 중 하나일 뿐이며 ICMP 자체가 Ping 전용 프로토콜은 아니다.

### 왜 Ping을 차단할까?

Ping을 차단한다고 해서 서버가 숨겨지는 것은 아니다.

다만 외부 공격자가 서버를 탐색(Reconnaissance)하기 어렵게 만드는 효과가 있다.

대표적인 이유는 다음과 같다.

- 서버의 존재 여부를 쉽게 노출하지 않기 위해
- Ping Sweep과 같은 대량 정찰을 어렵게 하기 위해
- ICMP Flood 공격의 영향을 줄이기 위해
- 필요한 서비스 포트만 외부에 노출하기 위해

특히 금융권이나 클라우드 환경에서는 ICMP Echo를 기본적으로 차단하는 경우가 많다.

### 실제 운영 환경 사례

#### AWS EC2

AWS EC2는 기본 Security Group에서 ICMP Echo(Ping)를 허용하지 않는다.

따라서 서버가 정상적으로 동작하더라도 SSH나 HTTP는 접속되지만 Ping에는 응답하지 않을 수 있다.

#### Microsoft Azure

Azure 역시 기본적으로 외부 ICMP를 허용하지 않는다.

필요한 경우 NSG(Network Security Group)와 운영체제 방화벽에서 별도로 허용해야 한다.

#### Google Cloud

Google Cloud도 방화벽 정책을 통해 ICMP를 제어한다.

필요한 경우에만 ICMP 허용 규칙을 추가하는 방식을 권장한다.

#### IBM TechZone

IBM TechZone 환경에서는 공인 IP에 대한 ICMP Echo 응답을 의도적으로 차단한다.

공식 문서에서도 Ping이 응답하지 않는 것은 정상적인 동작이며, SSH나 서비스 포트로 상태를 확인하도록 안내한다.

### Ping이 안 된다고 서버가 죽은 것은 아니다.

다음과 같은 상황은 충분히 발생할 수 있다.

```text
Ping          : 응답 없음
TCP 22 (SSH)  : 정상
TCP 443 (HTTPS): 정상
```

즉, ICMP만 차단되어 있을 뿐 실제 서비스는 정상적으로 제공되는 경우이다.

실제 장애 여부는 서비스 포트가 정상적으로 응답하는지를 기준으로 판단하는 것이 일반적이다.

### 정리

- ICMP는 Ping 전용 프로토콜이 아니다.
- Ping은 ICMP Echo Request/Reply 기능을 이용한다.
- ICMP는 오류 보고와 네트워크 진단을 위한 다양한 메시지를 제공한다.
- 운영 환경에서는 보안상의 이유로 ICMP Echo를 차단하는 경우가 많다.
- Ping이 실패하더라도 서비스 자체는 정상적으로 동작할 수 있다.