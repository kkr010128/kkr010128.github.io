---
title: Kubernetes Health Check와 restartPolicy
description: Probe와 restartPolicy, Init Container, Lifecycle Hook 및 Graceful Shutdown의 동작과 실습 정리
date: 2026-09-04
updated_at: 2026-09-07
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Kubernetes는 Process가 실행 중이라는 사실만으로 Application이 정상이라고 판단하지 않는다. Worker의 kubelet은 Probe를 실행하여 Container의 생존 여부, 요청 처리 가능 여부와 시작 완료 여부를 확인한다. Probe 결과와 `restartPolicy`를 함께 이해하면 Container가 재시작되는 경우와 Service Traffic에서만 제외되는 경우를 구분할 수 있다.

## 1 ) Health Check와 Pod 상태

---

Probe는 Pod 전체가 아니라 Pod 안의 각 Container에 설정한다. 같은 Container에도 목적이 다른 Probe를 함께 설정할 수 있다.

| Probe | 확인 대상 | 실패가 계속될 때의 결과 |
|---|---|---|
| Liveness Probe | Container가 계속 정상 동작할 수 있는가 | kubelet이 해당 Container를 재시작함 |
| Readiness Probe | 현재 요청을 처리할 준비가 되었는가 | Container는 유지하고 Pod를 Service Endpoint에서 제외함 |
| Startup Probe | Application의 최초 시작이 끝났는가 | 성공할 때까지 Liveness·Readiness Probe를 보류하고, 계속 실패하면 Container를 재시작함 |

Liveness Probe는 Process가 살아 있지만 Deadlock이나 Memory Leak 등의 문제로 정상 응답하지 못하고, 재시작 없이는 회복하기 어려운 상태를 감지할 때 사용한다.

Readiness Probe는 Database 연결, Cache Load, 초기 Data 준비처럼 요청 처리에 필요한 조건을 확인한다. 일시적으로 실패해도 Container를 재시작하지 않으며, 다시 성공하면 Service Endpoint에 포함될 수 있다.

Startup Probe는 시작 시간이 긴 Application을 보호한다. Startup Probe가 성공하기 전에는 Liveness·Readiness Probe가 실행되지 않으므로, 시작 중인 Container가 Liveness Probe 실패로 반복 재시작되는 상황을 방지할 수 있다.

외부 Load Balancer의 Health Check와 kubelet의 Probe는 별개의 검사이다. Load Balancer의 검사 방식과 대상은 Cloud Provider와 구성에 따라 달라지며, 외부 검사만으로 Container 내부의 생존 상태와 준비 상태를 모두 판단할 수는 없다.

## 2 ) Control Plane과 Worker의 상태 처리

---

Probe 실행과 상태 반영 과정은 다음과 같다.

1. 사용자가 Pod Spec에 Container별 Probe를 선언하여 API Server에 저장한다.

2. Scheduler가 Pod를 실행할 Worker를 선택한다.

3. Worker의 kubelet이 Pod Spec에 따라 Probe를 주기적으로 실행한다.

4. Liveness·Startup Probe가 실패 기준에 도달하면 kubelet이 해당 Container를 종료하고 `restartPolicy`에 따라 다시 시작한다.

5. Readiness Probe 결과는 Pod의 `Ready`와 `ContainersReady` Condition에 반영되어 API Server로 보고된다.

6. EndpointSlice Controller는 Ready 상태를 기준으로 Service가 요청을 전달할 Endpoint를 갱신한다.

따라서 Liveness 실패는 주로 Worker 안의 Container Lifecycle 변화로 나타나고, Readiness 실패는 Control Plane에 보고된 Pod Condition과 Service Endpoint 변화로 나타난다.

[Kubernetes Pod Lifecycle과 kubectl wait](/cloud-native-24-pod-lifecycle-kubectl-wait/)에서 정리한 `Running` Phase는 Container가 실행 중임을 나타낸다. Application이 Traffic을 받을 준비가 되었는지는 `Ready` Condition과 Readiness Probe를 함께 확인해야 한다.

## 3 ) Probe 실행 방식

---

### exec

Container 안에서 명령을 실행한다. 종료 코드가 `0`이면 성공이고, 그 외의 값이면 실패이다.

```yaml
livenessProbe:
  exec:
    command:
      - test
      - -e
      - /ok.txt
```

Application 상태를 검증하는 명령이 Container Image 안에 존재해야 한다.

### httpGet

kubelet이 지정한 Path와 Port로 HTTP GET 요청을 보낸다. 응답 Status Code가 `200` 이상 `400` 미만이면 성공으로 판단한다.

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 80
    scheme: HTTP
    httpHeaders:
      - name: Host
        value: web.example.com
      - name: Authorization
        value: Bearer REPLACE_WITH_TOKEN
```

`host` Field는 접속할 대상 Host를 지정한다. HTTP `Host` Header가 필요하면 `httpHeaders`에 지정한다. 인증 정보는 Manifest에 직접 저장하지 않고 실제 환경의 Secret 관리 방식을 사용해야 한다.

### tcpSocket

kubelet이 지정한 Port에 TCP Connection을 열 수 있는지 확인한다. Connection이 성립하면 성공이고 열 수 없으면 실패이다.

```yaml
livenessProbe:
  tcpSocket:
    port: 80
```

TCP Probe는 Port가 열려 있는지는 확인할 수 있지만 Application이 요청을 올바르게 처리하는지까지 검증하지는 않는다.

## 4 ) Probe 주기와 실패 판정

---

세 Probe는 공통적으로 다음 시간 관련 Field를 사용한다.

| Field | 의미 |
|---|---|
| `initialDelaySeconds` | Container 시작 후 첫 Probe까지 기다리는 시간 |
| `periodSeconds` | Probe를 반복하는 간격 |
| `timeoutSeconds` | 한 번의 Probe 응답을 기다리는 제한 시간 |
| `successThreshold` | 실패 상태에서 성공으로 판단하기 위해 필요한 연속 성공 횟수 |
| `failureThreshold` | 실패 동작을 수행하기 위해 필요한 연속 실패 횟수 |

`successThreshold`는 1 이상이어야 한다. Liveness·Startup Probe에서는 반드시 `1`이어야 하며 Readiness Probe에는 더 큰 값을 사용할 수 있다.

Liveness Probe의 `failureThreshold`가 너무 작으면 일시적인 지연에도 Container가 재시작될 수 있다. 반대로 너무 크면 실제 장애 감지가 늦어진다. 시작 시간 때문에 Liveness Probe의 `initialDelaySeconds`를 과도하게 늘리는 대신 Startup Probe로 최초 시작 구간을 분리할 수 있다.

## 5 ) Liveness와 Readiness Probe 적용

---

다음 예제는 nginx의 `/index.html`을 Liveness Probe로 확인하고, `/usr/share/nginx/html/50x.html`의 존재 여부를 Readiness Probe로 확인한다. `sample-healthcheck.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-healthcheck
  labels:
    app: sample-healthcheck
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      livenessProbe:
        httpGet:
          path: /index.html
          port: 80
          scheme: HTTP
        initialDelaySeconds: 5
        periodSeconds: 3
        timeoutSeconds: 1
        successThreshold: 1
        failureThreshold: 2
      readinessProbe:
        exec:
          command:
            - test
            - -e
            - /usr/share/nginx/html/50x.html
        initialDelaySeconds: 5
        periodSeconds: 3
        timeoutSeconds: 1
        successThreshold: 2
        failureThreshold: 1
```

Pod를 생성하고 두 Probe의 결과를 확인한다.

```bash
kubectl apply -f sample-healthcheck.yaml
kubectl wait \
  --for=condition=Ready \
  pod/sample-healthcheck \
  --timeout=60s
kubectl describe pod sample-healthcheck
```

`kubectl describe`의 `Containers` 영역에서 Liveness·Readiness 설정을 확인하고 `Conditions` 영역에서 `Ready`와 `ContainersReady` 값을 확인한다.

## 6 ) Liveness Probe 실패

---

Liveness Probe 실패가 Container 재시작으로 이어지는지 확인한다. 다음 내용을 `sample-liveness.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-liveness
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      livenessProbe:
        httpGet:
          path: /index.html
          port: 80
          scheme: HTTP
        initialDelaySeconds: 5
        periodSeconds: 3
        timeoutSeconds: 1
        successThreshold: 1
        failureThreshold: 2
```

Pod를 생성하고 변화 과정을 감시한다.

```bash
kubectl apply -f sample-liveness.yaml
kubectl get pod sample-liveness --watch
```

다른 터미널에서 Liveness Probe가 확인하는 File을 삭제한다.

```bash
kubectl exec sample-liveness -- \
  rm -f /usr/share/nginx/html/index.html
```

연속 실패 횟수가 `failureThreshold`에 도달하면 kubelet이 nginx Container를 재시작한다. Pod Object가 새로 만들어지는 것은 아니므로 Pod 이름과 UID는 유지되고 `RESTARTS`가 증가한다. Container가 재시작되면 Image의 File System으로 다시 시작하므로 삭제했던 기본 `index.html`도 복구된다.

```bash
kubectl get pod sample-liveness \
  -o custom-columns=NAME:.metadata.name,UID:.metadata.uid,RESTARTS:.status.containerStatuses[0].restartCount
kubectl describe pod sample-liveness
```

`kubectl describe`의 Event에서 Liveness Probe 실패와 Container 재시작 기록을 확인한다.

## 7 ) Readiness Probe 실패

---

Readiness 실패가 Service Endpoint에 미치는 영향을 확인한다. 다음 내용을 `sample-readiness.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-readiness
  labels:
    app: sample-readiness
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      readinessProbe:
        exec:
          command:
            - test
            - -e
            - /usr/share/nginx/html/50x.html
        initialDelaySeconds: 5
        periodSeconds: 3
        timeoutSeconds: 1
        successThreshold: 2
        failureThreshold: 1
---
apiVersion: v1
kind: Service
metadata:
  name: sample-readiness-service
spec:
  selector:
    app: sample-readiness
  ports:
    - port: 80
      targetPort: 80
```

Pod와 Service를 생성하고 Ready 상태와 EndpointSlice를 확인한다.

```bash
kubectl apply -f sample-readiness.yaml
kubectl wait \
  --for=condition=Ready \
  pod/sample-readiness \
  --timeout=60s
kubectl get pod sample-readiness
kubectl get endpointslice \
  -l kubernetes.io/service-name=sample-readiness-service
```

Readiness Probe가 확인하는 File을 삭제한다.

```bash
kubectl exec sample-readiness -- \
  rm -f /usr/share/nginx/html/50x.html
```

Probe 실패 후 Pod의 `READY` 값과 EndpointSlice 상태를 다시 확인한다.

```bash
kubectl get pod sample-readiness --watch
kubectl get endpointslice \
  -l kubernetes.io/service-name=sample-readiness-service \
  -o yaml
```

Container는 재시작되지 않지만 Pod는 Ready 상태에서 벗어나고 Service의 정상 Endpoint에서 제외된다. File을 다시 생성하면 연속 두 번 성공한 뒤 Ready 상태로 돌아간다.

```bash
kubectl exec sample-readiness -- \
  touch /usr/share/nginx/html/50x.html
kubectl wait \
  --for=condition=Ready \
  pod/sample-readiness \
  --timeout=60s
```

## 8 ) Startup Probe로 시작 구간 보호

---

다음 예제는 Container가 시작된 지 20초 후 `/tmp/started` File을 생성한다. Startup Probe가 이 File을 발견하기 전에는 Liveness·Readiness Probe가 실행되지 않는다. `sample-startup.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-startup
spec:
  containers:
    - name: nginx-container
      image: nginx:stable
      command:
        - /bin/sh
        - -c
        - |
          rm -f /tmp/started /tmp/probe.log
          (sleep 20; touch /tmp/started) &
          exec nginx -g 'daemon off;'
      startupProbe:
        exec:
          command:
            - /bin/sh
            - -c
            - |
              echo "[$(date)] startup" >> /tmp/probe.log
              test -e /tmp/started
        periodSeconds: 3
        timeoutSeconds: 1
        successThreshold: 1
        failureThreshold: 10
      livenessProbe:
        exec:
          command:
            - /bin/sh
            - -c
            - |
              echo "[$(date)] liveness" >> /tmp/probe.log
              test ! -e /tmp/liveness-fail
        periodSeconds: 3
        timeoutSeconds: 1
        successThreshold: 1
        failureThreshold: 3
      readinessProbe:
        exec:
          command:
            - /bin/sh
            - -c
            - |
              echo "[$(date)] readiness" >> /tmp/probe.log
              test ! -e /tmp/readiness-fail
        periodSeconds: 3
        timeoutSeconds: 1
        successThreshold: 1
        failureThreshold: 1
```

Pod를 생성하고 Probe 실행 순서를 확인한다.

```bash
kubectl apply -f sample-startup.yaml
kubectl get pod sample-startup --watch
```

다른 터미널에서 Probe 기록을 확인한다.

```bash
kubectl exec sample-startup -- \
  cat /tmp/probe.log
```

처음에는 `startup`만 기록된다. `/tmp/started`가 생성되어 Startup Probe가 성공하면 `startup` 검사는 끝나고 `liveness`와 `readiness`가 기록되기 시작한다.

이 예제에서 Startup Probe는 최대 약 30초 동안 시작 완료를 기다릴 수 있다. 그 안에 성공하지 못하면 kubelet은 해당 Container를 재시작한다. Pod Object 자체를 다시 생성하는 동작은 아니다.

## 9 ) restartPolicy

---

`spec.restartPolicy`는 Pod 안의 Container가 종료되었을 때 kubelet이 다시 시작할지를 결정한다. Pod를 새로 생성하는 정책이 아니다.

| 값 | 종료 코드 `0` | 종료 코드 `0` 이외 |
|---|---|---|
| `Always` | 재시작 | 재시작 |
| `OnFailure` | 재시작하지 않음 | 재시작 |
| `Never` | 재시작하지 않음 | 재시작하지 않음 |

일반 Pod의 기본값은 `Always`이다. Deployment와 StatefulSet 같은 일반적인 장기 실행 Workload의 Pod Template도 `Always`를 사용한다. 완료형 Workload인 Job은 성공한 Container가 다시 시작되면 작업을 완료할 수 없으므로 `OnFailure` 또는 `Never`만 사용할 수 있다. Job의 재시도 방식은 [Kubernetes Job과 CronJob](/cloud-native-30-kubernetes-job-cronjob/)에서 다룬다.

정상 종료한 Container도 `Always`에서 재시작되는지 확인한다. 다음 내용을 `sample-restart-always.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-restart-always
spec:
  restartPolicy: Always
  containers:
    - name: tools-container
      image: busybox:1.36
      command:
        - /bin/sh
        - -c
        - exit 0
```

Pod를 생성하면 Process가 종료 코드 `0`으로 끝나지만 kubelet이 계속 Container를 재시작한다.

```bash
kubectl apply -f sample-restart-always.yaml
kubectl get pod sample-restart-always --watch
kubectl describe pod sample-restart-always
```

반복 종료가 발생하면 재시작 사이의 지연이 증가하며 kubectl의 `STATUS`에 `CrashLoopBackOff`가 표시될 수 있다. `CrashLoopBackOff`는 Pod Phase가 아니라 반복 실패에 대한 kubectl 상태 표시이다.

## 10 ) Probe와 restartPolicy의 연결

---

Liveness·Startup Probe 실패가 기준 횟수에 도달하면 kubelet은 실패한 Container를 종료한다. 이후 Container 수준의 `restartPolicy` 적용 결과에 따라 재시작 여부가 결정된다. Readiness Probe는 Container를 종료하지 않으므로 `restartPolicy`를 작동시키지 않는다.

| 상황 | Container 종료 | `restartPolicy` 적용 | Service Traffic |
|---|---|---|---|
| Liveness 실패 기준 도달 | 종료함 | 적용함 | 재시작과 Ready 상태에 따라 제외될 수 있음 |
| Readiness 실패 | 종료하지 않음 | 적용하지 않음 | 정상 Endpoint에서 제외됨 |
| Startup 실패 기준 도달 | 종료함 | 적용함 | 시작 완료 전에는 Ready가 아님 |
| Container Process 자체 종료 | 이미 종료됨 | 적용함 | Ready가 아니므로 정상 Endpoint에서 제외됨 |

여러 Container가 있는 Pod에서는 Liveness 실패가 발생한 Container만 재시작한다. 다만 Container 중 하나라도 Ready 상태가 아니면 `ContainersReady`와 일반적인 `Ready` Condition에 영향을 줄 수 있다.

> **중간 정리**
>
> - kubelet은 Worker에서 Container별 Probe를 실행한다.
>
> - Liveness와 Startup 실패는 Container 재시작으로 이어질 수 있고 Readiness 실패는 Traffic 전달을 중단한다.
>
> - `restartPolicy`는 종료된 Container의 재시작 여부를 결정하며 Pod Object를 다시 생성하지 않는다.

## 11 ) Init Container

---

> **Init Container**
>
> Main Container가 시작되기 전에 초기 설정이나 준비 작업을 완료하는 Container이다.

Init Container는 `spec.initContainers`에 여러 개를 선언할 수 있다. 목록 위에서부터 하나씩 실행되며 각 Init Container가 성공해야 다음 Init Container가 시작된다. 모든 초기화가 끝나야 `spec.containers`의 Main Container가 시작된다.

| 구분 | Init Container | Main Container |
|---|---|---|
| 시작 시점 | Main Container보다 먼저 시작 | 모든 Init Container 성공 후 시작 |
| 여러 Container의 순서 | 선언 순서대로 하나씩 실행 | 기본적으로 서로 병렬로 시작 |
| 실행 형태 | 준비 작업을 마치고 정상 종료 | 일반적으로 Application Process를 계속 실행 |
| 주요 용도 | 설정 생성, 의존 대상 대기, 초기 Data 준비 | 실제 요청 처리와 Background 작업 |

초기화에만 필요한 Script나 Utility를 별도 Image에 둘 수 있으므로 Main Image의 구성과 권한을 줄이는 데 도움이 된다. Init Container와 Main Container가 결과를 공유하려면 공통 Volume을 Mount해야 한다. 서로의 Container File System은 자동으로 공유되지 않는다.

Control Plane과 Worker 관점의 실행 순서는 다음과 같다.

```text
API Server에 저장된 Pod Spec
            │
            ▼
Scheduler가 Worker 선택
            │
            ▼
Worker의 kubelet
  ├── 첫 번째 Init Container 실행·성공 확인
  ├── 두 번째 Init Container 실행·성공 확인
  └── Main Container 실행
            │
            ▼
       Probe와 Ready 판정
```

Init Container가 실패하면 kubelet은 Pod의 `restartPolicy`에 따라 다시 시도한다. 초기화가 성공하지 않는 동안 Main Container는 시작되지 않는다.

## 12 ) Init Container 실습

---

다음 내용을 `sample-initcontainer.yaml`로 저장한다. 두 Init Container와 nginx Container는 `emptyDir` Volume을 공유한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-initcontainer
spec:
  initContainers:
    - name: output-1
      image: alpine:3.20
      command:
        - sh
        - -c
        - sleep 20; echo 1st > /usr/share/nginx/html/index.html
      volumeMounts:
        - name: html-volume
          mountPath: /usr/share/nginx/html
    - name: output-2
      image: alpine:3.20
      command:
        - sh
        - -c
        - sleep 10; echo 2nd > /usr/share/nginx/html/index.html
      volumeMounts:
        - name: html-volume
          mountPath: /usr/share/nginx/html
  containers:
    - name: nginx-container
      image: nginx:stable
      volumeMounts:
        - name: html-volume
          mountPath: /usr/share/nginx/html
  volumes:
    - name: html-volume
      emptyDir: {}
```

Pod를 적용하면서 `STATUS`와 Init Container 진행 번호를 관찰한다.

```bash
kubectl get pods --watch
```

다른 Terminal에서 다음 명령을 실행한다.

```bash
kubectl apply -f sample-initcontainer.yaml
```

초기화가 끝나면 각 Init Container의 Log와 Main Container가 읽는 File을 확인한다.

```bash
kubectl logs pod/sample-initcontainer -c output-1
kubectl logs pod/sample-initcontainer -c output-2
kubectl exec pod/sample-initcontainer -- \
  cat /usr/share/nginx/html/index.html
```

두 번째 Init Container가 첫 번째 Container의 File을 덮어쓰므로 최종 출력은 `2nd`이다. 이 결과는 두 작업이 병렬로 경쟁한 것이 아니라 선언 순서대로 완료되었음을 보여준다.

## 13 ) Container Lifecycle Hook

---

Container Lifecycle Hook은 Container 시작 직후나 종료 직전에 한 번 수행할 작업을 정의한다.

| Hook | 실행 시점 | 주요 용도 |
|---|---|---|
| `postStart` | Container가 생성된 직후 | 초기화 신호 전달, Cache Warm-up, 내부 API 호출 |
| `preStop` | Container가 종료되기 전 | 새 작업 수신 중단, Connection 정리, Application의 안전한 종료 요청 |

`postStart`와 Container의 `ENTRYPOINT`는 비동기적으로 시작되므로 어느 쪽이 먼저 실행된다고 보장되지 않는다. 다만 Kubernetes는 `postStart`가 완료될 때까지 Container를 완전히 Running 상태로 관리하지 않는다. 시작 전에 반드시 끝나야 하는 순차 작업은 `postStart`보다 Init Container가 적합하다.

Hook은 한 번의 Lifecycle Event에 대해 실행되며 Probe처럼 주기적으로 상태를 검사하지 않는다. Hook Handler가 실패하면 Kubernetes는 Container를 종료하고 Pod의 `restartPolicy`에 따라 처리한다. Hook 실행에는 별도의 Timeout Field가 없으므로 외부 호출이나 장시간 작업에는 명령 자체의 제한 시간과 실패 처리를 구성해야 한다.

`exec` Handler는 Container 안에서 명령을 실행한다.

```yaml
postStart:
  exec:
    command:
      - /bin/sh
      - -c
      - sleep 10; touch /tmp/poststart
```

`httpGet` Handler는 지정한 Endpoint에 HTTP 요청을 보낸다.

```yaml
postStart:
  httpGet:
    path: /warmup
    port: 8080
    host: application.example.com
    scheme: HTTP
```

`postStart`는 Application의 지속적인 정상 여부를 판정하지 않는다. 실행 중 상태 점검에는 Liveness·Readiness·Startup Probe를 사용한다.

## 14 ) Lifecycle Hook 실습

---

다음 내용을 `sample-lifecycle-exec.yaml`로 저장한다. `postStart`는 시작 표시 File을 만들고, `preStop`은 nginx에 안전한 종료를 요청한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sample-lifecycle-exec
spec:
  terminationGracePeriodSeconds: 30
  containers:
    - name: nginx-container
      image: nginx:stable
      lifecycle:
        postStart:
          exec:
            command:
              - /bin/sh
              - -c
              - sleep 10; touch /tmp/poststart
        preStop:
          exec:
            command:
              - /bin/sh
              - -c
              - |
                echo "preStop started" > /proc/1/fd/1
                nginx -s quit
                sleep 5
```

Pod를 적용하고 시작 상태를 관찰한다.

```bash
kubectl apply -f sample-lifecycle-exec.yaml
kubectl get pod sample-lifecycle-exec --watch
```

`postStart`가 끝난 뒤 생성된 File을 확인한다.

```bash
kubectl exec pod/sample-lifecycle-exec -- ls -l /tmp/poststart
```

한 Terminal에서 Log를 확인한다.

```bash
kubectl logs -f pod/sample-lifecycle-exec
```

다른 Terminal에서 Pod를 삭제하면 `preStop started`가 기록되고 Grace Period 안에서 nginx가 종료된다.

```bash
kubectl delete -f sample-lifecycle-exec.yaml
```

Pod가 완전히 삭제된 뒤에는 `kubectl exec`로 `/tmp/prestop` 같은 Container 내부 File을 확인할 수 없다. 종료 과정은 Hook Log, Application Log와 Event를 통해 관찰해야 한다.

## 15 ) Graceful Shutdown

---

> **Graceful Shutdown**
>
> 처리 중인 요청과 Data를 가능한 한 안전하게 마무리한 뒤 Application Process를 종료하는 절차이다.

Pod 삭제나 Rolling Update로 Container가 종료될 때의 주요 흐름은 다음과 같다.

```text
Pod 종료 요청
    │ terminationGracePeriodSeconds Countdown 시작
    ▼
preStop Hook 실행
    ▼
Container의 주 Process에 SIGTERM 전달
    ▼
Application이 신규 요청을 중단하고 기존 작업 정리
    ├── Grace Period 안에 종료 ──▶ 정상 종료
    └── 종료하지 못함 ──────────▶ SIGKILL로 강제 종료
```

`terminationGracePeriodSeconds`의 기본값은 30초이다. `preStop` 실행 시간과 Application이 `SIGTERM`을 처리하는 시간은 같은 Grace Period 안에서 사용된다. 단순히 값을 늘리기 전에 실제 요청 처리 시간, Connection 종료, Data Flush와 종료 Log를 측정해야 한다.

nginx는 `SIGTERM`을 받으면 빠르게 종료할 수 있다. Worker Process가 처리 중인 요청을 마치도록 하려면 `preStop`에서 `nginx -s quit`으로 Graceful Shutdown을 요청할 수 있다. Application마다 종료 Signal 처리 방식이 다르므로 Container의 PID 1 Process가 Signal을 전달받고 올바르게 처리하는지도 확인해야 한다.

Rolling Update에서 Readiness Probe, `preStop`, Grace Period는 서로 다른 역할을 한다.

| 구성 | 역할 |
|---|---|
| Readiness Probe | 새 요청을 받을 수 있는 Pod인지 판단 |
| `preStop` | Container 종료 직전에 Application별 정리 작업 수행 |
| `terminationGracePeriodSeconds` | 종료 작업을 마칠 수 있는 전체 유예 시간 제공 |

## 16 ) 실습 Resource 정리

---

실습 중 생성한 Pod와 Service를 확인한다.

```bash
kubectl get pods
kubectl get service sample-readiness-service
kubectl get endpointslice \
  -l kubernetes.io/service-name=sample-readiness-service
```

Manifest로 생성한 Resource를 삭제한다.

```bash
kubectl delete -f sample-healthcheck.yaml
kubectl delete -f sample-liveness.yaml
kubectl delete -f sample-readiness.yaml
kubectl delete -f sample-startup.yaml
kubectl delete -f sample-restart-always.yaml
kubectl delete -f sample-initcontainer.yaml
kubectl delete -f sample-lifecycle-exec.yaml --ignore-not-found
```

## 전체 정리

---

> **최종 정리**
>
> - Liveness Probe는 Container가 계속 동작할 수 있는지 확인하고, 실패 기준에 도달하면 kubelet이 해당 Container를 재시작한다.
>
> - Readiness Probe는 현재 요청을 처리할 수 있는지 확인하며, 실패한 Pod는 재시작하지 않고 Service의 정상 Endpoint에서 제외한다.
>
> - Startup Probe가 성공하기 전에는 Liveness·Readiness Probe를 실행하지 않아 시작 시간이 긴 Application의 반복 재시작을 방지한다.
>
> - Probe는 `exec`, `httpGet`, `tcpSocket` 방식으로 실행할 수 있으며 주기, Timeout과 성공·실패 횟수를 Application 특성에 맞게 설정한다.
>
> - Worker의 kubelet이 Probe를 실행하고 결과를 API Server에 보고하면 Control Plane의 Controller가 Ready 상태를 Service Endpoint에 반영한다.
>
> - `restartPolicy`는 Pod가 아니라 종료된 Container의 재시작 여부를 결정한다.
>
> - Init Container는 Main Container보다 먼저 선언 순서대로 실행되며 공통 Volume으로 초기화 결과를 전달할 수 있다.
>
> - `postStart`와 `preStop`은 Lifecycle Event에 한 번 실행되고 Probe는 Container 상태를 주기적으로 검사한다.
>
> - Graceful Shutdown에서는 `preStop`과 Application의 종료 처리가 같은 `terminationGracePeriodSeconds` 안에 완료되어야 한다.
