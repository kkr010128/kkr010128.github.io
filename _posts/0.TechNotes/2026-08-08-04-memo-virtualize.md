---
title: Type 1 Hypervisor가 Type 2보다 빠른 이유
description: Bare-Metal 구조와 Host OS 경유 여부에 따른 Hypervisor의 성능 차이
date: 2026-08-08
series: TechNotes
tags:
  - DeepDive
  - CS
  - Virtualization
  - Hypervisor
---
### Q. Type 1 Hypervisor가 Type 2보다 빠른 이유는 무엇일까?
Type 1과 Type 2 Hypervisor는 모두 하나의 물리 서버에서 여러 가상 머신(Virtual Machine)을 실행하기 위한 기술이다.
그런데 Type 1은 서버와 데이터센터에서 주로 사용하고, Type 2는 개인 PC의 개발·테스트 환경에서 많이 사용한다.
이 차이는 어디에서 발생할까?
### A. 가장 큰 차이는 Host OS를 거치는지 여부이다.
Type 1 Hypervisor는 물리 하드웨어 위에서 직접 실행된다.
```text
Virtual Machine
      ↓
Hypervisor
      ↓
Hardware

반면 Type 2 Hypervisor는 기존 Host OS 위에서 실행된다.

Virtual Machine
      ↓
Hypervisor
      ↓
Host OS
      ↓
Hardware

Type 2에서는 Host OS 자체도 CPU, Memory, Disk 등의 자원을 사용한다.

또한 가상화 소프트웨어가 Host OS 위에서 동작하기 때문에 Type 1보다 추가적인 처리 과정과 자원 소비가 발생할 수 있다.

Bare-Metal 구조

Type 1은 물리 하드웨어에 직접 Hypervisor가 실행되기 때문에 Bare-Metal Hypervisor라고도 한다.

Hypervisor가 물리 자원을 직접 관리하여 각 VM에 할당한다.

* Physical CPU → vCPU
* Physical Memory → Virtual Memory
* Physical Disk → Virtual Disk
* Physical NIC → Virtual Network Adapter

일반적인 Host OS가 따로 자원을 소비하지 않으므로 많은 VM을 운영해야 하는 서버 환경에서 자원 활용에 유리하다.

그렇다면 Type 1은 항상 더 빠를까?

반드시 압도적으로 빠른 것은 아니다.

현대 CPU는 Intel VT-x, AMD-V와 같은 하드웨어 가상화 기능을 제공하므로 Type 2도 많은 작업을 하드웨어에서 직접 처리할 수 있다.

따라서 단순한 개발이나 실습 환경에서는 성능 차이를 크게 느끼지 못할 수도 있다.

핵심은 다음과 같다.

Type 1은 가상화 전용 환경에서 하드웨어 자원을 직접 관리하고, 일반적인 Host OS에 사용되는 자원을 줄일 수 있기 때문에 서버 환경에서 더 유리하다.

서버와 개인 실습 환경의 차이

구분	Type 1	Type 2
구조	Hardware 위에서 직접 실행	Host OS 위에서 실행
다른 이름	Bare-Metal	Hosted
오버헤드	상대적으로 적음	상대적으로 큼
주요 환경	서버, 데이터센터	개발, 테스트, 개인 실습
대표 예시	VMware ESXi, Xen	VMware Workstation, VirtualBox

Type 1은 여러 VM을 장기간 안정적으로 실행해야 하는 서버 환경에 적합하다.

반면 Type 2는 기존 Windows나 macOS를 그대로 사용하면서 필요할 때 VM을 실행할 수 있어 개인 실습 환경에서 편리하다.

정리

* Type 1은 하드웨어 위에서 Hypervisor가 직접 실행된다.
* Type 2는 Host OS 위에서 Hypervisor가 실행된다.
* Type 2는 Host OS가 자원을 함께 사용하므로 추가적인 오버헤드가 발생할 수 있다.
* Type 1은 서버와 데이터센터 환경에 적합하다.
* Type 2는 설치와 사용이 편리하여 개발 및 개인 실습에 적합하다.
* 성능 차이를 단순히 계층 수만으로 판단하기보다 자원 관리 구조의 차이로 이해하는 것이 좋다.

