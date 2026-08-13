---
title: 클라우드 보안
description: IAM과 네트워크 보안, 데이터 암호화, 보안 감사 및 규정 준수 중심의 AWS 클라우드 보안 전략
date: 2026-08-13
series: Cloud
tags:
  - Cloud
  - AutoEverSW
---
## 1 ) 클라우드 보안

---

클라우드 환경에서는 설정 오류, 자격 증명 노출, 과도한 권한 부여 등이 보안 사고로 이어질 수 있다.

대표적인 사례는 다음과 같다.

- S3 Bucket을 Public으로 설정하여 고객 정보가 유출되는 경우
- 개발자가 AWS Access Key를 GitHub에 업로드하는 경우
- 사용자 또는 서비스에 과도한 권한을 부여하는 경우

특히 Access Key를 소스 코드에 직접 포함하면 GitHub와 같은 외부 저장소에 코드가 공개될 때 자격 증명도 함께 노출될 수 있다.

최근에는 GitHub에서 AWS Access Key가 포함된 코드를 Push하지 못하도록 제한하며, AWS에서도 GitHub에 노출된 Key를 이용한 접근을 감지하면 계정을 잠그는 방식으로 대응한다.

### 클라우드 보안이 중요한 이유

클라우드 보안은 크게 비용, 신뢰, 법적인 측면에서 중요하다.

| 구분 | 내용 |
|---|---|
| 비용 | 보안 사고로 인한 직접적인 금전적 피해가 발생할 수 있다. |
| 신뢰 | 정보 유출 등의 사고는 서비스와 기업에 대한 신뢰 하락으로 이어질 수 있다. |
| 법 | 개인정보 및 데이터와 관련된 법적 책임이 발생할 수 있다. |

## 2 ) IAM

---

IAM (Identity and Access Management)은 AWS에서 사용자와 서비스의 접근 권한을 관리하기 위한 서비스이다.

### 주요 구성 요소

| 구성 요소 | 역할 |
|---|---|
| User | AWS를 사용하는 개별 사용자 |
| Group | 여러 User를 묶어 관리 |
| Role | 권한의 묶음 |
| Policy | 허용하거나 거부할 권한을 정의하는 정책 |

### Root 사용자와 IAM 사용자

| 구분 | Root 사용자 | IAM 사용자 |
|---|---|---|
| 권한 | 모든 권한 소유 | 부여된 권한만 사용 |
| 생성 | 자동 생성 | Root 사용자가 생성 |
| 삭제 | 삭제할 수 없음 | 삭제 가능 |
| 일상 사용 | 사용하지 않음 | 일상 업무에 사용 |

Root 계정에서는 다음과 같은 작업을 수행한다.

- AWS 계정 이름, 이메일, 비밀번호 변경
- 결제 정보 변경
- AWS Support Plan 변경
- 계정 해지
- IAM 사용자의 권한 복원

Root 계정은 모든 권한을 가지고 있으므로 반드시 MFA (Multi-Factor Authentication)를 설정한다.

### IAM Role

Role은 권한을 묶어서 필요한 대상에게 부여하는 방식이다.

대표적인 사용 사례는 다음과 같다.

- AWS 서비스 간 접근
- 다른 AWS 계정에서 접근
- 임시 접근 권한 부여

예를 들어 EC2가 S3에 접근해야 하는 경우 EC2에 필요한 Role을 부여할 수 있다.

```text
EC2
 │
 │ IAM Role
 ▼
S3
````

### **IAM Policy**

Policy는 무엇을 허용하고 무엇을 거부할지를 정의한 규칙이다.

Policy는 JSON으로 직접 작성하거나 GUI를 이용하여 작성할 수 있다.

주요 구성 요소는 다음과 같다.

|**항목**|**역할**|**예**|
|---|---|---|
|Effect|허용 또는 거부|`Allow`, `Deny`|
|Action|수행할 작업|`s3:GetObject`|
|Resource|작업 대상 Resource|`arn:aws:s3:::my-bucket/*`|

예시는 다음과 같다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket"
      ]
    }
  ]
}
```

Policy에서 `Allow`와 `Deny`가 동시에 적용되는 경우 `Deny`가 적용된다.

### **최소 권한 원칙**

사용자와 서비스에는 작업에 필요한 최소한의 권한만 부여한다.

불필요하게 많은 권한을 부여하면 계정이나 Access Key가 탈취되었을 때 피해 범위도 커질 수 있다.

### **IAM 모범 사례**

- Root 계정에 MFA를 설정한다.
- 일상적인 작업에는 IAM 계정을 생성하여 사용한다.
- Group을 이용하여 권한을 관리한다.
- 최소 권한 원칙을 적용한다.
- 강력한 비밀번호 정책을 설정한다.
- Access Key를 코드에 직접 포함하지 않는다.
- 사용하지 않는 사용자와 Key를 정리한다.
- Access Key 대신 IAM Role을 활용한다.

IAM 계정을 사용하면 누가 어떤 작업을 수행했는지 구분할 수 있으며, Group을 이용하면 여러 사용자의 권한을 일관되고 효율적으로 관리할 수 있다.

### **비밀번호 정책**

권장하는 비밀번호 정책은 다음과 같다.

- 최소 길이 12자 이상
- 대문자, 소문자, 숫자, 특수 문자 포함
- 비밀번호 만료 시간 설정
- 최근 12개의 비밀번호를 기억하여 재사용 방지
- 사용자가 자신의 비밀번호를 변경할 수 있도록 허용

짧은 비밀번호는 무차별 대입 공격에 취약할 수 있으며, 여러 종류의 문자를 사용하여 비밀번호 복잡도를 높일 수 있다.

### **AWS 접근 방법**

AWS에는 콘솔을 이용하는 방법과 Access Key를 이용하는 방법이 있다.

|**구분**|**Console Login**|**Access Key**|
|---|---|---|
|접근 방법|Web Browser로 AWS Console 접속|프로그램이나 명령어로 AWS API 호출|
|사용 방법|ID + Password + MFA|Access Key ID + Secret Access Key|
|사용 대상|사람|프로그램, CLI Tool, 자동화 Script|
|보안 위험|비밀번호 유출, Phishing|Key를 코드에 포함하면 유출 위험|

프로그램에서 AWS에 접근할 때는 Access Key를 코드에 직접 저장하는 것보다 IAM Role을 사용하는 것을 권장한다.

**정리**

- IAM은 AWS Resource에 대한 접근 권한을 관리한다.
- User, Group, Role, Policy가 주요 구성 요소이다.
- Root 계정은 일상적인 작업에 사용하지 않고 MFA를 설정한다.
- 사용자와 서비스에는 필요한 최소한의 권한만 부여한다.
- Access Key를 소스 코드에 직접 포함하지 않는다.

## **3 ) 네트워크 보안 아키텍처**

---

AWS에서는 하나의 보안 장치에만 의존하지 않고 여러 계층에 보안 기능을 배치하는 방어 심층 전략 (Defense in Depth)을 적용할 수 있다.

### **방어 심층 전략**

|**계층**|**서비스**|**보호 대상**|**주요 기능**|
|---|---|---|---|
|Edge|CloudFront, Shield, WAF|외부 Internet 경계|DDoS 방어, L7 Filtering|
|VPC 경계|Network Firewall, IGW|VPC 진입점|IDS/IPS, Stateful 검사|
|Subnet|NACL, Route Table|Subnet 경계|Stateless Filtering|
|Instance|Security Group|Instance 경계|Stateful Filtering|
|Application|IAM, 암호화, 인증|Application 내부|인증/인가, 데이터 암호화|

### **AWS 네트워크 보안 서비스**

|**서비스**|**역할**|
|---|---|
|AWS Shield|DDoS 방어|
|AWS WAF|Web Application 공격 Filtering|
|AWS Firewall Manager|여러 계정의 보안 정책 중앙 관리|
|AWS Network Firewall|VPC 수준 Firewall 및 IDS/IPS|
|VPC Flow Logs|Network Interface Traffic 기록|
|Traffic Mirroring|Traffic을 복제하여 보안 분석 도구로 전달|
|Route 53 Resolver DNS Firewall|악성 Domain DNS Query 차단 및 DNS Tunneling 방지|

**AWS Shield**

DDoS 방어를 목적으로 사용한다.

- Standard: 무료이며 L3/L4 자동 보호
- Advanced: L7 방어

**AWS WAF**

Web Application Firewall로 SQL Injection, XSS, Bot 등 L7 공격을 Filtering한다.

CloudFront와 ALB 등에 적용할 수 있다.

**AWS Firewall Manager**

여러 AWS 계정에서 사용하는 WAF, Shield, Security Group, NACL 규칙 등을 중앙에서 관리한다.

**AWS Network Firewall**

VPC 수준에서 Stateful/Stateless Packet 검사를 수행하며 IDS/IPS 기능을 제공한다.

**VPC Flow Logs**

VPC 내부 Network Interface의 Traffic 정보를 기록한다.

**Traffic Mirroring**

Traffic을 복제하여 보안 분석 도구로 전달한다.

**Route 53 Resolver DNS Firewall**

악성 Domain에 대한 DNS Query를 차단하고 DNS Tunneling을 방지하는 데 사용한다.

## **4 ) AWS WAF**

---

AWS WAF는 Web ACL에 Rule을 정의하고 CloudFront 또는 ALB에 연결하여 HTTP/HTTPS Traffic을 Filtering한다.

### **WAF 동작 구조**

```text
Web Request
HTTP / HTTPS
     │
     ▼
CloudFront / ALB
     │
     │ WAF Web ACL
     ▼
Rule 평가
     │
     │ 우선순위 순서로 Rule Matching
     ▼
Allow / Block / Count
```

Rule에 Matching되면 해당 Action을 수행하고, Matching되지 않으면 기본 Action을 수행한다.

### **WAF 규칙 유형**

|**유형**|**설명**|
|---|---|
|IP 기반|특정 IP/CIDR을 허용하거나 차단|
|Rate 기반|일정 시간 동안의 요청 수 제한|
|관리형 규칙|AWS 또는 Marketplace에서 제공하는 규칙|
|사용자 정의|Header, Query String 등의 조건을 직접 정의|
|정규식 패턴|URL, User-Agent 등을 정규표현식으로 Matching|

관리형 규칙은 OWASP Top 10이나 Bot 제어 등에 활용할 수 있다.

### **AWS 관리형 규칙 그룹**

- `AWSManagedRulesCommonRuleSet`: XSS, 파일 포함, SSRF 등 공통 취약점
- `AWSManagedRulesSQLiRuleSet`: SQL Injection 공격 패턴
- `AWSManagedRulesKnownBadInputsRuleSet`: Log4j, Java Deserialization 등 알려진 악성 입력
- `AWSManagedRulesAmazonIpReputationRuleSet`: AWS 위협 Intelligence 기반 악성 IP
- `AWSManagedRulesBotControlRuleSet`: Bot Traffic 탐지 및 제어

### **WAF Logging**

WAF Log를 분석하면 공격 패턴을 파악하고 Rule을 최적화할 수 있다.

|**로그 대상**|**활용**|
|---|---|
|S3|대용량 저장 및 Athena를 이용한 장기 분석|
|CloudWatch Logs|실시간 조회 및 Metric Filter를 이용한 차단 현황 Monitoring|
|Kinesis Data Firehose|SIEM 연동 및 실시간 Dashboard 활용|

## **5 ) VPC 보안 전략**

---

### **VPC 보안 설계 원칙**

**최소 노출**

Internet에 노출되는 Resource를 최소화한다. Public Subnet에는 ALB, NAT 등의 최소한의 Resource만 배치한다.

**네트워크 분리**

워크로드별 Network를 격리한다. 예를 들어 `dev`, `stg`, `prod` 환경별로 VPC를 분리할 수 있다.

**트래픽 제어**

SG와 NACL을 이용하여 허용된 Traffic만 통과시키는 White List 방식을 사용한다.

**가시성 확보**

VPC Flow Logs를 활성화하여 Traffic 흐름을 기록한다.

**암호화 전송**

Network 구간의 데이터를 보호하기 위해 TLS를 강제하고 VPN, PrivateLink 등을 활용한다.

### **Subnet 분리 전략**

|**Tier**|**Subnet**|**배치 Resource**|**Internet 접근**|**보안**|
|---|---|---|---|---|
|Public Tier|Public Subnet|ALB, NAT Gateway, Bastion|Inbound/Outbound 허용|최소 Resource|
|App Tier|Private Subnet|EC2, ECS, Lambda|NAT를 통한 Outbound만|ALB에서만 접근|
|Data Tier|격리된 Private Subnet|RDS, ElastiCache|Internet 접근 불가|App Tier에서만 접근|

### **VPC 간 연결 보안**

|**연결 방식**|**용도**|**보안 고려사항**|
|---|---|---|
|VPC Peering|두 VPC 간 Private 연결|CIDR 중복 불가, 전이적 Routing 불가|
|Transit Gateway|다수 VPC/On-Premises Hub 연결|Routing Table을 통한 Traffic 제어, Blackhole Routing|
|PrivateLink|서비스 간 Private 접근|Internet 노출 없이 서비스 제공|
|Site-to-Site VPN|On-Premises와 VPC의 암호화 연결|IPSec Tunnel, BGP Routing, 이중화|
|Direct Connect|전용선 연결|물리적 분리, MACsec 암호화|

### **VPC Endpoint**

VPC Endpoint를 이용하면 Internet Gateway 없이 AWS 서비스에 Private하게 접근할 수 있어 공격 표면을 줄일 수 있다.

|**유형**|**지원 서비스**|**보안 제어**|**비용**|
|---|---|---|---|
|Gateway Endpoint|S3, DynamoDB|Endpoint Policy로 접근 제한|무료|
|Interface Endpoint|대부분의 AWS 서비스|Security Group 적용|시간당 + GB당 과금|

Interface Endpoint는 PrivateLink 기반 ENI를 사용한다.

보안에 필요한 주요 VPC Endpoint는 다음과 같다.

- **S3**: Private Subnet에서 Internet을 경유하지 않고 접근하며 NAT Gateway 비용을 줄일 수 있다.
- **STS**: 임시 자격 증명 발급을 Private하게 수행한다.
- **Secrets Manager**: 비밀값을 Internet을 통하지 않고 조회한다.

## **6 ) Security Group과 NACL**

---

Security Group과 NACL (Network Access Control List)은 AWS Network Traffic을 제어하지만 적용 범위와 동작 방식이 다르다.

|**구분**|**Security Group**|**Network ACL**|
|---|---|---|
|적용 대상|Instance 수준|Subnet 수준|
|상태|Stateful|Stateless|
|응답 Traffic|자동 허용|별도 Rule 필요|
|기본 동작|Inbound 거부 / Outbound 허용|기본 NACL 모두 허용 / Custom NACL 모두 거부|
|Rule 유형|Allow만 가능|Allow / Deny 가능|
|Rule 평가|모든 Rule 종합 평가|번호 순서대로 평가 후 첫 Matching에서 중단|
|SG 참조|다른 SG를 Source로 참조 가능|IP/CIDR 사용|

### **트래픽 평가 순서**

```text
Internet
   ↓
NACL Inbound
   ↓
Security Group Inbound
   ↓
Instance
   ↓
Security Group 응답 자동 허용
   ↓
NACL Outbound
```

Security Group은 Stateful이므로 허용된 요청에 대한 응답 Traffic은 자동으로 허용된다.

NACL은 Stateless이므로 Inbound와 Outbound Rule을 각각 설정해야 한다.

### **서비스별 Security Group 설정**

**RDS**

- App SG에서만 DB Port 허용
- Public 접근 비활성화
- DB 전용 Subnet 사용

**ElastiCache**

- App SG에서만 Redis/Memcached Port 허용
- VPC 외부 접근 불가
- 전송 중 TLS 활성화

**Lambda**

- Outbound 중심으로 관리
- Lambda SG의 Outbound를 필요한 서비스에만 허용

**정리**

- AWS Network 보안은 Defense in Depth 방식으로 여러 계층에서 구성한다.
- WAF는 Web Application Traffic을 Filtering한다.
- VPC는 Public, App, Data Tier 등으로 분리하여 Resource 노출을 최소화할 수 있다.
- VPC Endpoint를 이용하면 AWS 서비스에 Internet을 통하지 않고 접근할 수 있다.
- Security Group은 Stateful이며 NACL은 Stateless이다.

## **7 ) 데이터 보안 전략**

---

데이터 보안의 기본 원칙은 기밀성, 무결성, 가용성이다.

- **기밀성 (Confidentiality)**: 허가된 대상만 데이터에 접근할 수 있도록 한다.
- **무결성 (Integrity)**: 데이터가 허가되지 않은 방식으로 변경되지 않도록 한다.
- **가용성 (Availability)**: 필요한 시점에 데이터와 서비스를 사용할 수 있도록 한다.

### **암호화 유형**

|**구분**|**저장 데이터 암호화**|**전송 데이터 암호화**|
|---|---|---|
|보호 대상|Disk, S3, DB 등에 저장된 데이터|Network를 통해 이동하는 데이터|
|방법|AES-256 대칭키 암호화|TLS 1.2/1.3|
|AWS|KMS, CloudHSM|ACM|
|적용 대상|EBS, S3, RDS, DynamoDB, EFS 등|HTTPS, VPN, PrivateLink|

### **서비스별 암호화**

|**서비스**|**저장 암호화**|**전송 암호화**|**특징**|
|---|---|---|---|
|S3|SSE-S3, SSE-KMS, SSE-C|HTTPS 강제|기본 암호화 설정 가능|
|EBS|KMS 암호화|Instance-EBS 간 자동 암호화|계정 수준 암호화|
|RDS|KMS 암호화|SSL/TLS 인증서|생성 후 암호화 변경 불가|
|DynamoDB|기본 암호화|HTTPS Endpoint|고객 관리 Key 선택 가능|
|EFS|KMS 암호화|TLS Mount Helper|생성 시 암호화 설정|

## **8 ) 보안 감사**

---

AWS에서는 Resource의 설정을 지속적으로 확인하고 보안 상태와 규정 준수 여부를 점검하기 위한 여러 서비스를 제공한다.

### **AWS Config**

AWS Config는 Resource의 구성 변경을 지속적으로 기록하고 Rule에 따라 규정 준수 여부를 자동으로 평가하는 서비스이다.

#### **Config Rule 유형**

- **AWS 관리형 Rule**: AWS가 사전에 정의한 Rule
- **사용자 정의 Rule**: Lambda 함수로 작성한 Custom Rule

보안에 활용할 수 있는 Rule로 `restricted-ssh`가 있다.

```text
Security Group
      │
      │ SSH 0.0.0.0/0
      ▼
AWS Config
      │
      ▼
Rule 위반 탐지
```

#### **Auto Remediation**

Config Rule을 위반하면 SSM Automation 문서를 연결하여 자동으로 교정할 수 있다.

|**위반 사항**|**대응**|
|---|---|
|Public S3 Bucket|Block Public Access 자동 활성화|
|암호화되지 않은 EBS|알림 전송 후 새로운 Volume 생성 필요|
|SSH `0.0.0.0/0` 허용 SG|해당 Rule 자동 제거|

### **AWS Security Hub**

AWS Security Hub는 여러 보안 서비스의 결과를 중앙에서 통합 관리하는 서비스이다.

주요 보안 표준은 다음과 같다.

|**보안 표준**|**설명**|
|---|---|
|AWS Foundational Security Best Practices|AWS 자체 보안 모범 사례, 약 200개|
|CIS AWS Foundations Benchmark|CIS의 AWS 보안 Benchmark, 약 50개|
|PCI DSS|결제 카드 산업 보안 표준, 약 30개|
|NIST SP 800-53|미국 연방 보안 Framework, 약 160개|

#### **CIS Benchmark**

CIS (Center for Internet Security)는 System과 Cloud 환경을 안전하게 구성하기 위한 보안 Benchmark를 제공한다.

Ubuntu Server에서는 다음과 같은 항목을 점검할 수 있다.

- 불필요한 서비스 비활성화
- SSH 보안 설정
- 비밀번호 정책 강화
- 파일 및 Directory 권한 설정
- Log 및 감사 설정
- Firewall 설정
- 계정 및 권한 관리
- 시간 동기화
- Kernel 및 Package 보안 설정

SSH를 예로 들면 단순히 SSH 설치 여부만 확인하는 것이 아니라 다음과 같은 보안 설정을 점검할 수 있다.

```text
Root 직접 로그인 차단
        ↓
비밀번호 인증 제한
        ↓
적절한 암호화 알고리즘 사용
        ↓
접근 가능한 사용자 제한
```

Kubernetes에도 별도의 CIS Kubernetes Benchmark가 존재한다.

Security Hub를 활성화하면 Security Score가 산출되며 이를 기반으로 개선 우선순위를 설정하고 Critical/High 항목부터 대응할 수 있다.

### **AWS Audit Manager**

AWS Audit Manager는 AWS 사용에 대한 감사 증거를 자동으로 수집하고 규정 준수 보고서를 생성하는 서비스이다.

|**기능**|**설명**|
|---|---|
|사전 정의 Framework|SOC 2, PCI DSS, GDPR, HIPAA 등 제공|
|자동 증거 수집|Config, CloudTrail, Security Hub 등에서 증거 수집|
|Custom Framework|조직의 내부 정책에 맞는 감사 Framework 생성|
|감사 보고서|감사인에게 제출 가능한 보고서 생성|

### **AWS Trusted Advisor**

AWS Trusted Advisor는 AWS 환경의 보안, 비용 최적화, 성능, 서비스 한도 등을 점검하는 서비스이다.

보안과 관련된 주요 점검 항목은 다음과 같다.

|**점검 항목**|**내용**|
|---|---|
|S3 Bucket Public 접근|Public 읽기/쓰기가 허용된 S3 Bucket 탐지|
|Root 계정 MFA|Root 계정 MFA 활성화 여부 확인|
|Security Group 무제한 접근|`0.0.0.0/0`으로 개방된 Port 탐지|
|IAM Access Key Rotation|90일 이상 Rotation되지 않은 Access Key 탐지|
|EBS Public Snapshot|Public으로 공유된 EBS Snapshot 탐지|
|CloudTrail Logging|CloudTrail 활성화 여부 확인|

CloudTrail은 AWS에서 누가 무엇을 수행했는지를 기록하는 감사 및 보안 Logging 서비스이다.

### **Amazon Inspector**

Amazon Inspector는 EC2 Instance, Container Image, Lambda 함수의 Software 취약점과 Network 노출을 자동으로 Scan하는 서비스이다.

|**Scan 대상**|**검출 내용**|**특징**|
|---|---|---|
|EC2 Instance|OS Package 취약점, Network 도달 가능성|SSM Agent 기반 Agentless Scan|
|ECR Container Image|Container Image 내부 Package 취약점|Image Push 시 자동 Scan|
|Lambda 함수|함수 Code 및 Dependency 취약점|배포 시 자동 Scan|

ECR은 Docker Image 등을 저장하는 Container Image Repository로 사용할 수 있다.

### **규정 준수의 코드화**

규정 준수의 코드화는 규정 준수 요구 사항을 코드로 정의하고 자동으로 검증하는 접근 방식이다.

|**구성 요소**|**AWS 서비스**|**역할**|
|---|---|---|
|정책 정의|AWS Config Rules, SCP, CloudFormation Guard|보안 정책을 코드로 정의|
|자동 평가|AWS Config, Security Hub|Resource의 정책 준수 여부 지속 평가|
|자동 교정|SSM Automation, Lambda|위반 사항 자동 수정|
|증거 수집|Audit Manager, CloudTrail|규정 준수 증거 자동 수집|
|보고|Security Hub, Audit Manager|규정 준수 현황 보고|

전체 흐름은 다음과 같다.

```text
정책 코드 작성
      ↓
CI/CD 배포
      ↓
지속적 평가
      ↓
자동 교정 / 보고
```

---

> **전체 정리**
>
> - 클라우드 보안에서는 Public Resource 설정, Access Key 노출, 과도한 권한과 같은 보안 위험을 줄이는 것이 중요하다.
> - IAM을 통해 User, Group, Role, Policy를 관리하며, Root 계정의 사용을 최소화하고 MFA와 최소 권한 원칙을 적용한다.
> - AWS Network는 WAF, Network Firewall, NACL, Security Group 등을 이용하여 여러 계층을 보호하는 Defense in Depth 전략을 적용할 수 있다.
> - VPC에서는 Public, App, Data 영역을 분리하고 필요한 Traffic만 허용하여 Resource의 외부 노출을 최소화한다.
> - 저장 데이터와 전송 데이터에는 각각 적절한 암호화를 적용하여 데이터의 기밀성과 무결성을 보호한다.
> - AWS Config, Security Hub, Audit Manager, Trusted Advisor, Amazon Inspector 등을 활용하여 보안 상태와 취약점, 규정 준수 여부를 지속적으로 점검할 수 있다.
> - 규정 준수 요구 사항을 코드로 정의하면 정책 정의 → 지속적 평가 → 자동 교정 → 증거 수집 → 보고 과정으로 관리할 수 있다.