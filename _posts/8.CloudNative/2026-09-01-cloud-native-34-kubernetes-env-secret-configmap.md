---
title: Kubernetes 환경 변수와 Secret, ConfigMap
description: Pod 환경 변수와 Downward API, Secret 생성과 주입, 갱신 및 ConfigMap을 이용한 설정 분리 방법
date: 2026-09-01
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Container Image와 Application 설정을 분리하면 같은 Image를 여러 환경에서 재사용할 수 있다. Kubernetes는 정적 환경 변수와 Downward API로 실행 정보를 전달하고, 민감하지 않은 설정은 ConfigMap, Password와 인증서 같은 기밀 정보는 Secret으로 관리한다.

## 1 ) Config와 Storage Resource

---

Kubernetes의 Config와 Storage API에는 Application 설정, 기밀 정보와 Persistent Storage를 연결하는 Resource가 포함된다.

| Resource | 목적 |
|---|---|
| ConfigMap | 민감하지 않은 Key-Value 또는 설정 파일 저장 |
| Secret | Password, Token, 인증서와 Registry 인증 정보 저장 |
| PersistentVolumeClaim | 영구 Volume 사용 요청 |

## 2 ) 설정을 Container에 전달하는 방법

---

Pod의 Container에 설정을 전달하는 대표적인 방법은 다음과 같다.

| 방법 | Manifest Field | 특징 |
|---|---|---|
| 개별 환경 변수 | `env` | 이름과 값을 하나씩 지정 |
| 전체 환경 변수 | `envFrom` | ConfigMap이나 Secret의 전체 Key를 주입 |
| 개별 Resource Key | `configMapKeyRef`, `secretKeyRef` | 필요한 Key만 환경 변수에 연결 |
| Volume File | `volumes`, `volumeMounts` | 설정 파일이나 Secret을 File로 제공 |
| Downward API | `fieldRef`, `resourceFieldRef` | Pod와 Container 자신의 실행 정보 제공 |

Manifest를 적용하면 설정이 다음 흐름으로 Container에 전달된다.

```text
Master·관리 Client
  kubectl apply
       │
       ▼
Control Plane
  API Server가 Pod·ConfigMap·Secret 저장
       │
       ▼
Scheduler가 Worker 선택
       │
       ▼
Worker
  kubelet이 Pod Spec과 참조 Resource 확인
       │
       ├─▶ 환경 변수 구성
       └─▶ ConfigMap·Secret Volume 구성
                 │
                 ▼
        Container Runtime이 Container 실행
```

환경 변수는 Process 시작 시점에 정해지는 값에 적합하다. File Mount는 Application이 File 변경을 다시 읽을 수 있을 때 동적 설정 반영에 활용할 수 있다.

## 3 ) 정적 환경 변수

---

`env`는 Container에 전달할 환경 변수를 하나씩 선언한다. 다음 내용을 `sample-env.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-env
  labels:
    app: sample-env
spec:
  containers:
    - name: nginx
      image: nginx:stable
      env:
        - name: MAX_CONNECTION
          value: "100"
        - name: TZ
          value: Asia/Seoul
```

Master 또는 관리 Client에서 Pod를 생성하고 Ready 상태를 확인한다.

```bash
kubectl apply -f sample-env.yaml
kubectl wait --for=condition=Ready pod/sample-env --timeout=120s
kubectl get pod sample-env -o wide
```

Container Process에 전달된 값을 조회한다.

```bash
kubectl exec sample-env -- printenv MAX_CONNECTION
kubectl exec sample-env -- printenv TZ
```

`env`와 `envFrom`으로 설정한 값은 Container Image에 정의된 같은 이름의 환경 변수보다 우선한다. Password를 `env.value`에 직접 기록하면 Manifest와 Pod Spec 조회 결과에 노출될 수 있으므로 Secret을 사용한다.

## 4 ) Downward API와 fieldRef

---

> **Downward API**
>
> Pod가 Kubernetes API를 직접 호출하지 않고 자신의 Metadata, 배치 정보와 Resource 설정을 환경 변수 또는 File로 확인하도록 제공하는 기능이다.

`fieldRef`는 Pod Field를 환경 변수에 연결한다. 다음 내용을 `sample-env-pod.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-env-pod
  namespace: default
  labels:
    app: sample-env-pod
spec:
  containers:
    - name: tools
      image: busybox:1.37
      command:
        - /bin/sh
        - -c
      args:
        - sleep 3600
      env:
        - name: K8S_NODE
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: K8S_POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: K8S_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: K8S_POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
```

Pod YAML에서 원본 Field를 먼저 확인한다.

```bash
kubectl apply -f sample-env-pod.yaml
kubectl wait --for=condition=Ready pod/sample-env-pod --timeout=120s
kubectl get pod sample-env-pod -o yaml
```

Container에 주입된 값과 비교한다.

```bash
kubectl exec sample-env-pod -- printenv K8S_NODE
kubectl exec sample-env-pod -- printenv K8S_POD_NAME
kubectl exec sample-env-pod -- printenv K8S_NAMESPACE
kubectl exec sample-env-pod -- printenv K8S_POD_IP
```

API Server에 저장된 Pod 상태를 Worker의 kubelet이 확인하여 Container 환경 변수를 구성한다. Application은 자신의 Node나 Pod IP를 알아내기 위해 API Server 조회 권한을 별도로 가질 필요가 없다.

## 5 ) resourceFieldRef

---

`resourceFieldRef`는 특정 Container에 선언한 CPU와 Memory Request·Limit을 환경 변수로 전달한다. 실제 값을 확인할 수 있도록 Resource 설정과 참조를 함께 정의한다.

다음 내용을 `sample-env-container.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-env-container
  labels:
    app: sample-env-container
spec:
  containers:
    - name: tools
      image: busybox:1.37
      command:
        - /bin/sh
        - -c
      args:
        - sleep 3600
      resources:
        requests:
          cpu: 125m
          memory: 32Mi
        limits:
          cpu: 250m
          memory: 64Mi
      env:
        - name: CPU_REQUEST
          valueFrom:
            resourceFieldRef:
              containerName: tools
              resource: requests.cpu
        - name: CPU_LIMIT
          valueFrom:
            resourceFieldRef:
              containerName: tools
              resource: limits.cpu
        - name: MEMORY_REQUEST
          valueFrom:
            resourceFieldRef:
              containerName: tools
              resource: requests.memory
        - name: MEMORY_LIMIT
          valueFrom:
            resourceFieldRef:
              containerName: tools
              resource: limits.memory
```

```bash
kubectl apply -f sample-env-container.yaml
kubectl wait --for=condition=Ready pod/sample-env-container --timeout=120s
kubectl exec sample-env-container -- \
  printenv CPU_REQUEST CPU_LIMIT MEMORY_REQUEST MEMORY_LIMIT
```

`containerName`은 같은 Pod 안의 어떤 Container Resource를 참조하는지 지정한다. Request와 Limit이 변경되면 새 Pod가 생성될 때 해당 값이 환경 변수에 반영된다.

## 6 ) command와 args의 환경 변수 확장

---

Kubernetes가 `command`와 `args`에서 환경 변수를 확장할 때는 `$(VAR_NAME)` 형식을 사용한다. Shell의 `${VAR_NAME}` 문법과 처리 시점이 다르다.

| 표현 | 처리 주체 | 결과 |
|---|---|---|
| `$(TESTENV)` | kubelet의 Container Command·Args 구성 | 앞에서 정의된 환경 변수 값으로 확장 |
| `${TESTENV}` | Kubernetes가 직접 확장하지 않음 | Literal Argument로 전달될 수 있음 |
| `$TESTENV` | 실행된 Shell | `/bin/sh -c` 안에서 Shell이 확장 |

잘못된 형식을 확인하는 `sample-env-fail.yaml`은 다음과 같다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-env-fail
spec:
  restartPolicy: Never
  containers:
    - name: env-print
      image: busybox:1.37
      command:
        - echo
      args:
        - "${TESTENV}"
      env:
        - name: TESTENV
          value: "100"
```

Container가 출력 후 종료되므로 `exec`가 아니라 Log를 확인한다.

```bash
kubectl apply -f sample-env-fail.yaml
kubectl wait --for=jsonpath='{.status.phase}'=Succeeded \
  pod/sample-env-fail --timeout=120s
kubectl logs sample-env-fail
```

출력에는 `${TESTENV}`가 그대로 남을 수 있다. 올바른 Kubernetes 확장 형식은 다음과 같다.

```yaml
args:
  - "$(TESTENV)"
```

여러 Shell 명령, Pipe나 Shell 자체의 환경 변수 확장이 필요하면 Shell을 명시한다.

```yaml
command:
  - /bin/sh
  - -c
args:
  - 'echo "$TESTENV"'
```

`env` 배열에서 다른 환경 변수를 참조할 때는 참조 대상이 먼저 선언되어야 한다. 정의되지 않은 `$(VAR_NAME)`은 Container 시작을 항상 막는 것이 아니라 확장되지 않은 문자열로 남을 수 있다.

## 7 ) Secret이 필요한 이유

---

Secret은 Password, OAuth Token, SSH Key와 인증서처럼 기밀성이 필요한 Data를 Application에 전달한다.

| 전달 방법 | 문제점 |
|---|---|
| Container Image에 포함 | Registry와 Image Layer에 기밀 정보가 남고 값 변경 시 다시 Build해야 함 |
| Pod Manifest의 `env.value` | Git, Review, 배포 Log와 Pod Spec에 평문 노출 가능 |
| 여러 Manifest에 반복 | 값 교체와 접근 범위 관리가 어려움 |
| Secret Resource 참조 | 설정과 Workload를 분리할 수 있지만 별도 보안 설정 필요 |

Secret의 `data` 값은 Base64로 Encoding될 뿐 암호화되는 것이 아니다. Base64 Decode 권한과 Secret 조회 권한이 있으면 원래 값을 확인할 수 있다.

Kubernetes의 Secret은 기본 설정에서 etcd에 암호화되지 않은 상태로 저장될 수 있다. 운영 환경에서는 다음 보호를 함께 적용한다.

- etcd Encryption at Rest를 구성한다.

- RBAC로 Secret의 `get`, `list`, `watch` 권한을 최소화한다.

- Application이 Secret을 Log에 출력하지 않게 한다.

- Secret Manifest와 임시 Credential File을 Version Control에 Commit하지 않는다.

## 8 ) Secret Type

---

Secret Type은 Data의 사용 목적과 필요한 Key를 구분한다.

| Type | 용도 | 주요 Key·주의 사항 |
|---|---|---|
| `Opaque` | 일반 Password와 Token | 임의의 Key 사용 가능 |
| `kubernetes.io/tls` | TLS 인증서와 Private Key | `tls.crt`, `tls.key` |
| `kubernetes.io/basic-auth` | Username과 Password | `username`, `password` |
| `kubernetes.io/dockerconfigjson` | Private Registry 인증 | `.dockerconfigjson` |
| `kubernetes.io/ssh-auth` | SSH Private Key | `ssh-privatekey` |
| `kubernetes.io/service-account-token` | 장기 ServiceAccount Token | 신규 일반 사용 비권장 |
| `bootstrap.kubernetes.io/token` | Node Bootstrap Token | kubeadm Bootstrap 등에 사용 |

장기 ServiceAccount Token Secret은 만료와 자동 Rotation 측면에서 비권장이다. 일반적인 Pod 인증에는 TokenRequest API로 발급되는 짧은 수명의 Projected ServiceAccount Token을 사용한다.

## 9 ) Opaque Secret 생성

---

일반적인 Key-Value Secret은 `generic` Subcommand로 생성한다. 모든 명령은 Master 또는 관리 Client에서 실행한다.

### File에서 생성

실습용 값을 명시적인 File에 저장한다.

```bash
printf '%s' 'root' > username
printf '%s' 'rootpassword' > password
```

File의 Basename이 기본 Key가 된다. 확장자 사용이 금지되는 것은 아니며 원하는 Key를 직접 지정할 수도 있다.

```bash
kubectl create secret generic sample-db-auth \
  --from-file=username=./username \
  --from-file=password=./password
```

이미 같은 이름의 Secret이 있으면 `create`가 실패한다. 반복 가능한 Manifest를 먼저 확인하려면 Client-side Dry Run을 사용할 수 있다.

```bash
kubectl create secret generic sample-db-auth \
  --from-file=username=./username \
  --from-file=password=./password \
  --dry-run=client -o yaml
```

Dry Run 출력에도 Base64로 표현된 실제 값이 포함되므로 Log나 공유 화면에 노출하지 않는다.

### Env File에서 생성

다음 내용을 `env-secret.txt`로 저장한다.

```dotenv
username=root
password=rootpassword
```

기존 실습 Secret을 교체해야 한다면 먼저 사용 중인 Pod가 없는지 확인한 뒤 명시적으로 삭제하고 다시 생성한다.

```bash
kubectl delete secret sample-db-auth --ignore-not-found
kubectl create secret generic sample-db-auth \
  --from-env-file=./env-secret.txt
```

### Literal 값으로 생성

```bash
kubectl create secret generic sample-db-auth-literal \
  --from-literal=username=root \
  --from-literal=password=rootpassword
```

실제 Password를 Command Line에 직접 입력하면 Shell History나 Process 정보에 노출될 수 있으므로 운영 환경에서는 안전한 입력과 Secret 관리 절차를 사용한다.

### Manifest의 data와 stringData

다음 내용을 `sample-db-auth.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: sample-db-auth-manifest
type: Opaque
data:
  username: cm9vdA==
  password: cm9vdHBhc3N3b3Jk
```

`data`에는 Base64 Encoding된 값을 작성한다. `stringData`를 사용하면 작성 시 Base64 Encoding을 생략할 수 있다.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: sample-db-auth-string
type: Opaque
stringData:
  username: root
  password: rootpassword
```

`stringData`도 Manifest에 평문이 존재하므로 안전하게 Commit할 수 있다는 뜻이 아니다. API Server는 입력된 문자열을 처리하여 Secret의 `data`로 저장한다.

```bash
kubectl apply -f sample-db-auth.yaml
kubectl get secrets
```

## 10 ) Secret 조회와 Base64 Decode

---

Secret Metadata와 Type은 값을 노출하지 않고 확인할 수 있다.

```bash
kubectl get secret sample-db-auth
kubectl describe secret sample-db-auth
```

Data Key와 Base64 값은 JSON으로 조회할 수 있다.

```bash
kubectl get secret sample-db-auth -o json
```

특정 Key를 Decode하면 원래 값이 Terminal에 출력된다.

```bash
kubectl get secret sample-db-auth \
  -o jsonpath='{.data.username}' | base64 --decode
```

이 작업은 복호화가 아니라 Base64 Decode이다. 화면 공유, Terminal 기록과 CI Log에서 실행하면 Secret이 노출될 수 있으므로 학습 환경 이외에는 값 자체를 출력하지 않는다.

## 11 ) TLS Secret

---

`kubernetes.io/tls` Secret은 TLS 인증서와 Private Key를 정해진 Key 이름으로 저장한다.

| File | Secret Key | 역할 |
|---|---|---|
| `tls.crt` | `tls.crt` | Server 인증서와 필요한 인증서 Chain |
| `tls.key` | `tls.key` | 인증서와 일치하는 Private Key |

인증서 File이 준비된 관리 Client에서 생성한다.

```bash
kubectl create secret tls example-tls \
  --cert=./tls.crt \
  --key=./tls.key
```

Ingress에서는 같은 Namespace의 TLS Secret을 참조한다.

```yaml
spec:
  tls:
    - hosts:
        - example.com
      secretName: example-tls
```

Ingress Host, 인증서의 DNS Name과 Client가 요청하는 Domain이 일치해야 한다. TLS Secret을 만들었다는 사실만으로 Ingress Controller의 HTTPS Listener와 외부 Firewall이 자동으로 모두 준비되는 것은 아니다.

## 12 ) Private Registry Secret

---

Private Registry에서 Image를 Pull하려면 `kubernetes.io/dockerconfigjson` Type의 Secret을 Pod와 같은 Namespace에 준비한다.

```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=myuser \
  --docker-password='<password>' \
  --docker-email=user@example.com
```

실제 Credential을 Command Line에 넣으면 Shell History와 실행 중인 Process 정보에 노출될 수 있다. 가능한 경우 안전하게 관리되는 Docker Config File이나 외부 Credential 관리 방식을 사용한다.

다음 Pod Template은 `imagePullSecrets`를 참조한다. 내용을 `sample-private-registry.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-private-registry
spec:
  containers:
    - name: app
      image: registry.example.com/myproject/myapp:1.0
  imagePullSecrets:
    - name: regcred
```

예제 Registry와 Image는 Placeholder이므로 실제 접근 가능한 주소로 바꿔야 한다. Image Pull이 실패하면 Pod Event를 확인한다.

```bash
kubectl apply -f sample-private-registry.yaml
kubectl describe pod sample-private-registry
```

`FailedToRetrieveImagePullSecret`은 Secret 이름이나 Namespace 문제를 나타낼 수 있고 `ImagePullBackOff`는 인증, Image 경로와 Registry 통신 상태를 함께 확인해야 한다.

## 13 ) Basic Auth Secret

---

`kubernetes.io/basic-auth` Type은 `username`과 `password` Key를 사용한다. 다음 내용을 `sample-basic-auth.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: sample-basic-auth
type: kubernetes.io/basic-auth
stringData:
  username: sample-user
  password: sample-password
```

```bash
kubectl apply -f sample-basic-auth.yaml
kubectl get secret sample-basic-auth
```

예제 값은 학습용이며 실제 Database나 Web Login Credential로 사용하지 않는다. 실제 값을 넣은 Manifest는 Version Control에 Commit하지 않는다.

## 14 ) Secret을 환경 변수로 전달

---

### 특정 Key만 전달

`secretKeyRef`는 필요한 Key 하나를 지정한 환경 변수에 연결한다. 다음 내용을 `sample-secret-single-env.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-secret-single-env
spec:
  containers:
    - name: nginx
      image: nginx:stable
      env:
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: sample-db-auth
              key: username
```

Secret이 먼저 존재해야 Pod를 정상적으로 시작할 수 있다.

```bash
kubectl apply -f sample-secret-single-env.yaml
kubectl wait --for=condition=Ready \
  pod/sample-secret-single-env --timeout=120s
kubectl exec sample-secret-single-env -- printenv DB_USERNAME
```

### 전체 Key 전달

`envFrom.secretRef`는 Secret의 전체 Key를 같은 이름의 환경 변수로 전달한다. 다음 내용을 `sample-secret-multi-env.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-secret-multi-env
spec:
  containers:
    - name: nginx
      image: nginx:stable
      envFrom:
        - secretRef:
            name: sample-db-auth
```

```bash
kubectl apply -f sample-secret-multi-env.yaml
kubectl wait --for=condition=Ready \
  pod/sample-secret-multi-env --timeout=120s
kubectl exec sample-secret-multi-env -- printenv username
```

전체 Key를 주입하면 Application에 불필요한 Secret까지 노출될 수 있다. 필요한 Container에 필요한 Key만 제공하는 구성이 접근 범위를 줄이는 데 유리하다.

환경 변수로 주입된 Secret은 Container 시작 시점에 정해진다. Secret Object가 변경돼도 실행 중인 Container 환경 변수는 자동으로 바뀌지 않으므로 Pod를 다시 생성해야 한다.

## 15 ) Secret을 Volume File로 전달

---

Secret Volume은 각 Key를 File로 제공한다. 다음 내용을 `sample-secret-volume.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-secret-volume
spec:
  containers:
    - name: nginx
      image: nginx:stable
      volumeMounts:
        - name: secret-volume
          mountPath: /config
          readOnly: true
  volumes:
    - name: secret-volume
      secret:
        secretName: sample-db-auth
```

```bash
kubectl apply -f sample-secret-volume.yaml
kubectl wait --for=condition=Ready \
  pod/sample-secret-volume --timeout=120s
kubectl exec sample-secret-volume -- ls -l /config
```

`username`과 `password` Key는 `/config/username`, `/config/password` File로 Mount된다. 실제 값을 `cat`으로 출력하면 Terminal에 노출되므로 File 존재와 Application 동작 중심으로 확인한다.

## 16 ) Secret의 동적 갱신

---

Secret Volume에서 사용하는 Secret Object가 변경되면 kubelet은 Eventually Consistent 방식으로 Projected File을 갱신한다.

```text
Secret 변경
  → API Server 저장
  → Worker kubelet의 Watch·Cache 또는 Polling
  → Projected Volume File 교체
  → Application이 File을 다시 읽어야 새 값 사용
```

기본 변경 감지 전략은 Watch이다. 반영 지연은 고정 60초가 아니라 kubelet Sync 주기와 Cache 전파 지연의 영향을 받는다.

| Secret 사용 방법 | Secret 변경 시 동작 |
|---|---|
| 환경 변수 | 실행 중인 Container에는 자동 반영되지 않음 |
| 일반 Secret Volume | 일정 지연 후 File 갱신 가능 |
| `subPath` Secret Mount | 자동 갱신되지 않음 |

Volume File이 바뀌어도 Application이 설정 File을 다시 읽지 않으면 실제 동작은 변하지 않는다. Application Reload 또는 Pod Rollout 전략을 함께 설계해야 한다.

## 17 ) 외부 Secret 관리 도구의 역할

---

Secret Manifest를 Git에서 안전하게 관리하거나 외부 Secret Store와 연결하기 위한 도구는 역할이 서로 다르다.

| 방식 | 역할 |
|---|---|
| Sealed Secrets | 공개키로 암호화한 Custom Resource를 Cluster 안에서 Secret으로 변환 |
| External Secrets | 외부 Secret Store의 값을 Kubernetes Secret으로 동기화 |
| Secret 보안 검사 도구 | Manifest와 Workload의 보안 위험을 분석하며 암호화 기능과는 구분 |

`kubesec`이라는 이름은 보안 분석 도구 등 서로 다른 Project 문맥에서 사용될 수 있으므로 Secret 암호화 도구로 단정하지 않는다.

## 18 ) ConfigMap

---

> **ConfigMap**
>
> 민감하지 않은 Application 설정을 Key-Value 또는 File 형태로 저장하는 Kubernetes Resource이다.

ConfigMap은 Secret과 달리 기밀 정보 보호를 목적으로 하지 않는다. Password, API Token과 Private Key는 ConfigMap에 저장하지 않는다.

| 항목 | 설명 |
|---|---|
| `data` | UTF-8 문자열 Data |
| `binaryData` | Base64로 표현하는 Binary Data |
| 최대 크기 | 하나의 ConfigMap에서 1MiB 이하 |
| 대표 사용 | 환경별 Parameter, Application 설정 File |

### File에서 ConfigMap 생성

다음 내용을 `nginx.conf`로 저장한다.

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;
```

File 이름인 `nginx.conf`가 기본 Key가 된다.

```bash
kubectl create configmap sample-configmap \
  --from-file=./nginx.conf
```

원하는 Key 이름을 명시할 수도 있다.

```bash
kubectl create configmap sample-configmap-dry-run \
  --from-file=nginx-config=./nginx.conf \
  --dry-run=client -o yaml
```

### Literal 값으로 ConfigMap 생성

```bash
kubectl create configmap sample-config-literal \
  --from-literal=MAX_CONNECTION=100 \
  --from-literal=TZ=Asia/Seoul
```

### ConfigMap 조회

```bash
kubectl get configmap sample-configmap
kubectl get configmap sample-configmap -o json
kubectl describe configmap sample-configmap
```

ConfigMap은 환경 변수나 Volume File로 Container에 전달할 수 있다.

## 19 ) 실습 Resource 정리

---

Master 또는 관리 Client에서 Secret과 ConfigMap을 참조하는 Pod부터 제거한다.

```bash
kubectl delete pod sample-secret-volume --ignore-not-found
kubectl delete pod sample-secret-multi-env --ignore-not-found
kubectl delete pod sample-secret-single-env --ignore-not-found
kubectl delete pod sample-private-registry --ignore-not-found
kubectl delete pod sample-env-fail --ignore-not-found
kubectl delete pod sample-env-container --ignore-not-found
kubectl delete pod sample-env-pod --ignore-not-found
kubectl delete pod sample-env --ignore-not-found
```

실습용 ConfigMap과 Secret을 제거한다.

```bash
kubectl delete configmap sample-config-literal --ignore-not-found
kubectl delete configmap sample-configmap --ignore-not-found
kubectl delete secret sample-basic-auth --ignore-not-found
kubectl delete secret regcred --ignore-not-found
kubectl delete secret example-tls --ignore-not-found
kubectl delete secret sample-db-auth-string --ignore-not-found
kubectl delete secret sample-db-auth-manifest --ignore-not-found
kubectl delete secret sample-db-auth-literal --ignore-not-found
kubectl delete secret sample-db-auth --ignore-not-found
```

Local에 만든 실습 File은 실제 운영 Credential이 아닌지와 다른 작업에서 사용하지 않는지 확인한 뒤 명시적으로 정리한다.

```bash
rm -f ./username ./password ./env-secret.txt ./nginx.conf
```

`tls.crt`와 `tls.key`는 실제 인증서일 수 있으므로 자동 정리 명령에 포함하지 않는다. 보관 정책과 사용 여부를 확인한 뒤 별도로 관리한다.

## 전체 정리

---

> **최종 정리**
>
> - `env`와 `envFrom`은 정적 설정을 Container 환경 변수로 전달하고 Downward API는 Pod와 Container 자신의 정보를 제공한다.
>
> - `fieldRef`는 Pod Field, `resourceFieldRef`는 Container의 CPU·Memory Request와 Limit을 참조한다.
>
> - Kubernetes의 `command`와 `args`에서는 `$(VAR_NAME)`으로 환경 변수를 확장하며 Shell의 `${VAR_NAME}` 문법과 구분해야 한다.
>
> - Secret의 Base64 Encoding은 암호화가 아니므로 etcd Encryption at Rest, RBAC와 Version Control 보호가 필요하다.
>
> - Secret은 특정 Key 환경 변수, 전체 환경 변수 또는 Volume File로 전달할 수 있으며 환경 변수와 Volume의 갱신 방식이 다르다.
>
> - 장기 ServiceAccount Token Secret은 비권장이고 짧은 수명의 Projected Token을 우선 사용한다.
>
> - ConfigMap은 민감하지 않은 설정을 저장하며 하나의 Object에 저장하는 Data는 1MiB를 넘을 수 없다.
