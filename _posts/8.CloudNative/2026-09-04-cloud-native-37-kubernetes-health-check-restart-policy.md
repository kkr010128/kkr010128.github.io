---
title: Kubernetes Health Check와 restartPolicy
description: Liveness·Readiness·Startup Probe의 역할과 kubelet의 상태 점검, Container 재시작 정책을 실습으로 정리
date: 2026-09-04
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

## 11 ) 실습 Resource 정리

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
