---
title: Apache Kafka
description: Apache Kafka의 등장 배경과 특징, Topic과 Partition 중심의 Kafka의 기본 구조와 동작 방식
date: 2026-08-12
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
---
## 1 ) Apache Kafka

---

### Kafka의 등장 배경

기존에는 데이터를 생성하는 **소스 애플리케이션(Source Application)** 과 데이터를 사용하는 **타깃 애플리케이션(Target Application)** 을 직접 연결하여 데이터를 전달하는 방식이 사용되었다.

예를 들어 하나의 서비스에서 발생한 데이터를 여러 시스템에서 사용해야 한다면 각각의 애플리케이션 사이에 데이터 파이프라인을 구성해야 한다.

```text
Source A ────────→ Target A
    │
    └────────────→ Target B

Source B ────────→ Target A
    │
    └────────────→ Target C
````

서비스가 적을 때는 큰 문제가 없지만 애플리케이션이 증가하면 연결해야 하는 파이프라인도 함께 증가한다.

소스 애플리케이션과 타깃 애플리케이션을 연결하는 파이프라인의 개수가 많아지면서 소스 코드 및 버전 관리에서 이슈가 발생할 수 있다.

또한 타깃 애플리케이션에 장애가 발생하면 그 영향이 소스 애플리케이션에 그대로 전달될 수 있다.

즉, 각각의 애플리케이션이 서로 강하게 연결되어 있기 때문에 데이터 흐름이 복잡해질수록 전체 시스템을 관리하기 어려워진다.

Apache Kafka는 이러한 데이터 흐름을 개선하기 위해 **LinkedIn**에서 개발되었다.

각 애플리케이션을 직접 연결하는 대신 Kafka를 중간에 두고 데이터를 한곳으로 모아 전달하는 구조를 사용할 수 있다.

```text
Source Application
        │
        ▼
      Kafka
        │
        ▼
Target Application
```

여러 애플리케이션이 존재하더라도 Kafka를 중심으로 데이터 흐름을 구성할 수 있다.

```text
Source A ─┐
Source B ─┼──→ Kafka ──┬──→ Target A
Source C ─┘            ├──→ Target B
                       └──→ Target C
```

이를 통해 애플리케이션마다 개별적인 데이터 파이프라인을 구성하는 복잡성을 줄일 수 있다.

Kafka는 오픈소스로 제공되며, 대규모 데이터를 처리하는 **Big Data** 환경이나 **Data Pipeline**을 구축하는 환경에서 주요 구성 요소로 활용된다.

### **Kafka의 데이터 처리 방식**

Kafka에서 데이터를 전송하는 쪽을 **Producer**, 데이터를 가져가 처리하는 쪽을 **Consumer**라고 한다.

```text
Producer
   │
   ▼
 Kafka
   │
   ▼
Consumer
```

Producer가 Kafka로 데이터를 전송하면 Kafka는 데이터를 저장하고, Consumer는 필요한 데이터를 Kafka에서 가져가 처리한다.

Kafka에서 실제로 전달되고 저장되는 데이터 단위를 **Record**라고 한다.

```text
Producer
   │
   │ Record
   ▼
 Kafka
   │
   │ Record
   ▼
Consumer
```

Kafka에 전달된 Record는 단순히 메모리에 존재하는 것이 아니라 Broker의 **파일 시스템에 기록하여 보관할 수 있다.**

따라서 Consumer가 데이터를 읽는 순간 데이터가 바로 사라지는 일반적인 Queue와는 차이가 있다.

### **Kafka를 사용하는 이유**

Kafka를 사용하는 주요 이유는 **높은 처리량, 확장성, 영속성, 고가용성**이다.

|**특징**|**설명**|
|---|---|
|높은 처리량|대량의 데이터를 지속적으로 처리할 수 있다.|
|확장성|Broker와 Partition 등을 확장하여 처리 능력을 증가시킬 수 있다.|
|영속성|전달받은 데이터를 파일 시스템에 저장할 수 있다.|
|고가용성|여러 Broker에 데이터를 분산하여 장애에 대응할 수 있다.|

#### **높은 처리량**

Kafka는 많은 양의 데이터를 지속적으로 전달하고 처리하는 환경을 고려하여 설계되었다.

따라서 Big Data 처리나 여러 시스템 사이에 대량의 데이터를 전달하는 Data Pipeline에서 사용할 수 있다.

#### **확장성**

데이터 처리량이 증가하면 시스템의 규모도 함께 확장해야 한다.

Kafka는 여러 Broker로 Cluster를 구성할 수 있기 때문에 필요에 따라 서버를 추가하는 **Scale-Out** 방식으로 확장할 수 있다.

강의에서는 Kafka의 Scale-Out과 Scale-In 과정이 비교적 용이하다는 점을 특징으로 다루었다.

#### **영속성**

Kafka는 Producer로부터 전달받은 데이터를 파일 시스템에 기록할 수 있다.

따라서 데이터를 단순히 중간에서 전달하는 역할만 수행하는 것이 아니라 일정 기간 데이터를 저장하고 Consumer가 이후에 읽을 수 있도록 구성할 수 있다.

#### **고가용성**

Kafka는 하나의 서버만 사용하는 것이 아니라 여러 Broker를 이용하여 분산 환경을 구성할 수 있다.

```text
Kafka Cluster

├── Broker 1
├── Broker 2
└── Broker 3
```

강의에서는 상용 환경의 경우 Kafka를 여러 대의 Broker로 분산 운영하며, 일반적으로 최소 3대 이상의 서버로 구성하는 형태를 예로 들었다.

Producer가 전달한 데이터는 Broker의 파일 시스템에 기록되고, 여러 Broker를 이용한 분산 구성을 통해 특정 Broker에 장애가 발생하는 상황에 대응할 수 있다.

**중간 정리**

- 기존 방식은 소스와 타깃 애플리케이션을 직접 연결하기 때문에 시스템이 커질수록 데이터 파이프라인이 복잡해질 수 있다.
- Kafka를 중간에 두면 애플리케이션 간 데이터 흐름을 Kafka 중심으로 구성할 수 있다.
- Producer는 데이터를 Kafka에 전송하고 Consumer는 Kafka의 데이터를 읽어 처리한다.
- Kafka는 높은 처리량, 확장성, 영속성, 고가용성을 제공하기 위해 사용된다.

## 2 ) **Data Lake Architecture**

---

Kafka를 이해하기 위해서는 대규모 데이터를 처리하는 아키텍처가 어떻게 변화했는지도 함께 볼 필요가 있다.

강의에서는 다음과 같은 데이터 처리 아키텍처를 다루었다.

```text
전통적인 방식
      ↓
Lambda Architecture
      ↓
Kappa Architecture
      ↓
Streaming Data Lake Architecture
```

### **전통적인 데이터 처리 방식**

전통적인 방식에서는 각 서비스 애플리케이션을 **End-to-End** 형태로 연결하여 데이터를 수집하고 처리하였다.

```text
Service A ─────────→ Storage A

Service B ─────────→ Storage B

Service C ─────────→ Storage C
```

각 서비스가 필요한 데이터를 직접 수집하고 처리하기 때문에 시스템이 커질수록 애플리케이션 사이의 데이터 연결 관계도 복잡해질 수 있다.

### **Lambda Architecture**

대규모 데이터를 처리하기 위한 방식으로 **Lambda Architecture**가 사용된다.

강의에서는 데이터 처리 아키텍처의 흐름에서 Lambda Architecture를 다루었으며, 이후 실시간 데이터 처리와 관련된 구조로 Kappa Architecture가 등장하는 흐름을 설명하였다.

### **Kappa Architecture**

**Kappa Architecture**는 데이터 처리 흐름을 스트리밍 중심으로 구성하는 아키텍처이다.

강의에서는 Lambda Architecture 이후 실시간 데이터 처리와 속도 측면을 고려하면서 등장한 구조로 설명하였다.

### **Streaming Data Lake Architecture**

실시간으로 지속해서 발생하는 데이터를 처리하는 환경에서는 **Streaming Data Lake Architecture**를 사용할 수 있다.

Kafka는 이러한 스트리밍 데이터 파이프라인을 구성할 때 데이터를 전달하고 저장하는 중간 계층으로 활용할 수 있다.

## 3 ) **Kafka의 주요 구성 요소**

---

Kafka의 기본적인 데이터 흐름은 다음과 같이 볼 수 있다.

```text
Producer
    │
    ▼
  Topic
    │
    ├── Partition 0
    ├── Partition 1
    └── Partition 2
              │
              ▼
          Consumer
```

이를 구성하는 주요 개념으로 **Broker, Producer, Consumer, Topic, Partition, Record**가 있다.

### **Broker**

Kafka가 실행되는 서버를 **Broker**라고 한다.

Broker는 Producer로부터 전달받은 Record를 저장하고 Consumer가 데이터를 읽을 수 있도록 제공한다.

하나의 Kafka 시스템은 여러 Broker로 구성할 수 있다.

```text
Kafka Cluster

┌──────────┐
│ Broker 1 │
└──────────┘

┌──────────┐
│ Broker 2 │
└──────────┘

┌──────────┐
│ Broker 3 │
└──────────┘
```

여러 Broker를 이용하여 데이터를 분산 처리하고 장애에 대응할 수 있다.

### **Producer**

**Producer**는 Kafka에 데이터를 전송하는 역할을 한다.

```text
Application
     │
     ▼
  Producer
     │
     ▼
   Kafka
```

Producer는 데이터를 어떤 Topic으로 보낼 것인지 결정하여 Kafka Broker로 전송한다.

### **Consumer**

**Consumer**는 Kafka에 저장된 데이터를 가져와 처리하는 역할을 한다.

```text
Kafka
  │
  ▼
Consumer
  │
  ▼
Application
```

여러 Consumer를 하나의 그룹으로 구성하여 Partition의 Record를 병렬로 처리할 수도 있다.

### **Topic**

**Topic**은 Kafka에서 데이터를 구분하기 위해 사용하는 단위이다.

Producer는 특정 Topic에 데이터를 전송하고 Consumer는 필요한 Topic의 데이터를 가져간다.

```text
Producer
   │
   ▼
book-topic
   │
   ▼
Consumer
```

하나의 Topic은 **하나 이상의 Partition을 가진다.**

```text
Topic
│
├── Partition 0
├── Partition 1
└── Partition 2
```

Producer가 보낸 데이터는 Partition에 저장되며, 이렇게 저장되는 각각의 데이터를 **Record**라고 한다.

### **Record**

**Record**는 Kafka에 저장되는 데이터의 단위이다.

```text
Partition

Record → Record → Record → Record
```

강의에서는 Kafka가 Java로 구현되어 Java 객체를 사용할 수 있다고 설명하였다.

실제로 Kafka를 통해 객체 형태의 데이터를 전달할 때는 객체 자체를 그대로 저장하는 것이 아니라 **Serialization(직렬화)** 과정을 통해 전송 가능한 데이터 형태로 변환한다.

```text
Java Object
    │
    ▼
Serialization
    │
    ▼
 Producer
    │
    ▼
  Kafka
```

따라서 Java 객체를 포함한 다양한 형태의 데이터를 직렬화하여 Kafka를 통해 전달할 수 있다.

### **Partition**

**Partition**은 Topic 내부에서 Record가 실제로 저장되는 단위이며 Kafka의 **병렬 처리에서 핵심적인 역할**을 한다.

```text
Topic
│
├── Partition 0 → Record → Record → Record
│
├── Partition 1 → Record → Record → Record
│
└── Partition 2 → Record → Record → Record
```

강의에서는 Partition을 자료구조의 Queue와 비슷한 구조로 설명하였다.

Partition 내부에서는 먼저 들어온 Record부터 순서대로 저장되기 때문에 **FIFO(First In First Out)와 유사한 형태로 이해할 수 있다.**

다만 Kafka의 Record는 Consumer가 읽었다고 즉시 삭제되는 Queue와는 다르며, 설정된 보존 정책에 따라 일정 기간 유지된다.

Partition은 Kafka에서 병렬 처리를 가능하게 하는 핵심 요소이기도 하다.

예를 들어 하나의 Topic에 여러 Partition이 있다면 Consumer Group에 속한 여러 Consumer가 각각의 Partition을 담당할 수 있다.

```text
Topic

Partition 0 ───→ Consumer 1
Partition 1 ───→ Consumer 2
Partition 2 ───→ Consumer 3
```

따라서 처리해야 하는 데이터가 많아지면 Partition과 Consumer를 적절하게 구성하여 여러 데이터를 병렬로 처리할 수 있다.

강의에서는 **Consumer 개수와 Partition 개수를 늘리는 방법을 통해 처리량을 증가시킬 수 있다**는 점을 다루었다.

## **ZooKeeper**

---

**ZooKeeper**는 분산 시스템에서 여러 서버의 상태와 구성 정보를 관리하는 **분산 코디네이터(Distributed Coordinator)** 역할을 한다.

기존 Kafka에서는 Kafka Cluster를 관리하기 위해 ZooKeeper를 함께 사용하였다.

```text
              ZooKeeper
                  │
          Kafka Cluster 관리
                  │
       ┌──────────┼──────────┐
       ↓          ↓          ↓
    Broker 1   Broker 2   Broker 3
````

Kafka에서 ZooKeeper는 Broker의 상태를 관리하고, Cluster를 제어하는 Controller를 선출하거나 Topic과 Partition 등의 Metadata를 관리하는 과정에 사용되었다.

따라서 ZooKeeper가 Kafka의 Record를 직접 저장하거나 Producer와 Consumer 사이에서 Message를 전달하는 것은 아니다.

```text
Producer → Kafka Broker → Consumer
                ↑
            ZooKeeper
        Cluster 상태 관리
```

기존 Kafka에서는 이러한 Cluster 관리 기능을 ZooKeeper에 의존했지만, 이후 **KRaft(Kafka Raft)** 방식이 도입되면서 Kafka가 자체적으로 Metadata를 관리할 수 있게 되었다.

```text
기존 방식

Kafka Broker
     ↕
ZooKeeper
```

```text
KRaft 방식

Kafka
└─ 자체적으로 Metadata 관리
```

따라서 강의에서 사용하는 ZooKeeper 기반 Kafka는 기존 Kafka의 Cluster 관리 구조이며, 최신 Kafka에서는 ZooKeeper 없이 Kafka Cluster를 구성할 수 있다.

> **정리**
>
> - Apache Kafka는 LinkedIn 내부의 복잡한 데이터 흐름을 개선하기 위해 개발된 오픈소스 분산 이벤트 스트리밍 플랫폼이다. 기존처럼 소스와 타깃 애플리케이션을 직접 연결하는 대신 Kafka를 중간에 두어 데이터 흐름을 구성할 수 있으며, Big Data와 Data Pipeline 구축에 활용된다.
>
> - Kafka를 사용하는 주요 이유는 **높은 처리량, 확장성, 영속성, 고가용성**이다. Kafka Server를 Broker라고 하며, 여러 Broker를 이용하여 분산 환경을 구성할 수 있다.
>
> - Producer는 Kafka에 데이터를 **Record** 형태로 전송하고 Consumer는 저장된 Record를 읽어 처리한다. Record는 **Topic**을 기준으로 구분되며, 하나의 Topic은 하나 이상의 **Partition**으로 구성된다.
>
> - Partition은 Kafka의 병렬 처리에서 핵심적인 역할을 한다. 하나의 Partition 내부에서는 Record의 순서가 유지되며, Consumer Group의 Consumer들이 서로 다른 Partition을 담당하여 병렬로 처리할 수 있다.
>
> - 기존 Kafka에서는 분산 코디네이터인 **ZooKeeper**가 Broker와 Metadata 관리에 사용되었다. 이후 **KRaft(Kafka Raft)** 가 도입되면서 ZooKeeper 없이 Kafka 자체적으로 Metadata를 관리할 수 있게 되었다.
>
> - 강의에서는 데이터 처리 아키텍처의 변화와 함께 **Lambda Architecture, Kappa Architecture, Streaming Data Lake Architecture**를 다루었으며, Kafka가 실시간 데이터 처리와 Streaming Pipeline을 구성하는 데 활용될 수 있음을 확인하였다.

