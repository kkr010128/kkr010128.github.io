---
title: Redis 개요
description: Redis 특징, 자료구조, 아키텍처, 사용 사례 정리
date: 2026-07-16
series: Redis
tags:
  - Redis
  - AutoEverSW
---

## 1) 특징
---
- Key - Value Data Store
- 싱글 스레드로 동장
- In Memory Database 방식이라 속도가 매우 빠름
- MariaDB와 MongoDB는 On Disk Database

 1. **고가용성**
	 - 언제든지 사용할 수 있어야 함
	 - 자체적으로 HA(High Availability) 기능 제공
	 - 복제를 통해 여러 서버에 분산시킬 수 있음
	 - Sentinel은 장애 상황을 자동 탐지해서 자동 **fail-over**를 수행
		 - fail-over
			→ 시스템에 장애가 발생했을 때 예비 시스템으로 업무를 즉시 전환
			→ 서비스 중단 없이 운영을 유지하는 기술

	 - Sentinel을 이용해 데이터를 받아옴
		 - 노드에 직접 접속해 데이터를 받아오지 않음
		 - 마스터 노드에 장애가 발생해도 엔드포인트 변경 필요 없음

2. **확장성**
	- Redis를 Cluster 모드로 구성하면 손쉬운 수평 확장이 가능
	- 데이터는 Redis Cluster 내에서 자동으로 샤딩된 후 저장되며 여러 개의 복제본을 저장
	- 애플리케이션에서는 실제 데이터가 어떤 노드에 있는지 몰라도 사용 가능
		- → 위치 투명성
	- Cluster 구조에서 모든 Redis Instance는 Cluster Bus라는 Protocol로 상호 감시함
		- Cluster의 Master node에 문제가 발생하면 자동으로 fail-over를 이용
		- → 고가용성 유지
	- 대다수의 클라우드 벤더들이 서비스를 제공
		- AWS: Amazon ElastiChe for Redis
		- GCP: Cloud Memory store for Redis
		- Azure, NHN, Naver Cloud • • • 


## 2) MicroService와 Redis
---
### 데이터 저장소로서의 Redis
- 서비스 별 개별 저장소로 사용하기에 적합
- 설치가 간편
- 다양한 자료구조를 제공하고 사용이 간단
- 고가용성을 위해 로드밸런서• 프록시 등 추가적인 서비스를 설치할 필요 없음
- AOF(Append Only File)과 RDB(Redis DataBase) 형식으로 디스크에 저장 가능

### Message Broker로서의 Redis
- MSA에서는 특별한 경우 아니면 Message Broker가 필요함
- Message Broker는 서비스들 간의 비동기 데이터 전달을 수행
- publish / subscribe 기능을 이용
- 모든 데이터는 전달된 뒤 삭제
	- fire-and-forget 패턴이 필요한 간단한 알림 서비스에서 유용
- stream과 list 자료구조를 이용한 구현이 가능
	- stream의 경우 Apache Kafka에서 영감을 얻어서 추가됨


## 3) 반영구적 저장
---

### RDB(Redis DataBase)
- 현재 메모리에 있는 데이터 전체에 대한 스냅샷을 작성, 디스크에 저장하는 방식
- 간단한 사용 가능

- *하지만* 스냅샷 이후 변경된 데이터는 복구 안 됨
### AOF(Append Only File)
- Redis에 데이터가 변경되는 이벤트가 발생하면 이를 모두 저장하는 방식
- 데이터 복구 시 RDB 대비 유실량이 적음

- *하지만* 속도가 느림
- 로그의 크기가 커짐

## 4) Event Loop
---
- Client가 실행한 명령어들을 Event Queue에 저장 후 단일 스레드로 하나씩 처리

**멀티 스레드 방식의 문제점**
- Context-Switching이 발생
- Dead Lock 발생할 수 있음

## 5) 장점
---
1. In-Memory 구조 → 빠른 성능 (일반적으로 1ms 미만)
2. 다양성과 사용 편의성(자료구조)
3. 대다수의 개발 언어 지원
4. 복제 및 지속성

## 6) 사용사례
---
1. 주 데이터 저장소
2. Caching
	- Access 시간을 줄임
		→ 자주 사용하는 데이터를 저장할 용도로 다른 DB 앞에 배치

3. Session 관리 
	→  session: 서버의 메모리에 저장하는 정보
	- 게임, 전자상거래, 소셜 미디어 플랫폼에서 주로 이용

4. 실시간 순위표
5. 분산 락
	- 다수의 컴퓨터가 공유 자원을 사용할 때 실제 사용 중인지 여부를 판단하기 위한 Lock

6. Message Broker
7. 채팅 및 메시징


## 7) Architecture
---
- Redis는 Sentinel, Master, Replica로 구성
- Sentinel이 Master와 Replica를 관리
- Sentinel이 주기적으로 서버들을 모니터링
	- Master가 서비스할 수 없는 상태일 시 Replica중 하나를 Master로 변경
- Redis Sentinel도 장애가 발생할 수 있으므로 여러대의 서버로 구성
- 클러스터 아키텍처
	- 클러스터를 구성하면 클러스터에 포함된 모든 노드들이 서로 통신하며 고가용성을 유지
	- 샤딩 기능이 기본 기능
	- 클러스터 구조를 이용하면 Sentinel을 설정할 필요가 없음
	- 클러스터 내부의 모든 노드들이 Mesh형으로 연결
	- 샤딩을 할 때 해시 함수를 이용해 데이터를 분배하기 때문에 데이터가 균등하게 저장됨
	- 노드를 추가하거나 삭제하면 자동으로 재분배(리밸런싱, 리샤딩)
	- Application Client는 Redis Cluster의 노드 중 하나라도 연결되면 Cluster의 전체 상태 정보를 확인할 수 있음(cluster 내부의 노드는 전체 )
- 클러스터에 한 번 접속한 클라이언트는 장애가 발생한 노드나 확장을 위해 추가한 노드 정보들도 모두 업데이트 받기 때문에 실제 Production환경에서 운영 중 증설을 하더라도 애플리케이션의 설정을 바꿀 필요 없음

