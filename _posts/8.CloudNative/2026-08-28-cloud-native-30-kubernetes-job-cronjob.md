---
title: Kubernetes Job과 CronJob
description: 완료형 Workload인 Job의 재시도·병렬 실행·자동 정리와 CronJob의 Schedule·동시 실행·History 관리 정리
date: 2026-08-28
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Deployment와 ReplicaSet은 Application이 계속 실행되는 상태를 유지하지만 Job은 정해진 작업이 성공적으로 끝나는 상태를 목표로 한다. CronJob은 Schedule에 따라 Job을 반복 생성하므로 완료 조건과 재시도 정책을 먼저 이해해야 한다.

## 1 ) Run-to-Completion Workload

---

> **Run-to-Completion**
>
> 계속 실행되는 Service가 아니라 정해진 처리를 수행하고 정상 종료하는 것을 목표로 하는 Workload이다.

Job은 Container를 이용하여 한 번 또는 지정한 횟수만큼 작업을 완료한다. 여러 Pod를 병렬로 실행할 수도 있으며 성공한 Pod 수가 원하는 완료 횟수에 도달하도록 관리한다.

| 구분 | ReplicaSet·Deployment | Job |
|---|---|---|
| 목표 | 지정한 수의 Pod가 계속 실행 | 지정한 작업이 성공적으로 완료 |
| 정상 종료된 Pod | 부족한 Replica로 보고 다시 생성 | 성공 횟수로 계산 |
| 대표 사례 | Web Server, API Server | Batch, Migration, Report 생성 |
| 재시도 기준 | 실행 중인 Pod 수 | 작업 성공·실패 상태와 `backoffLimit` |

ReplicaSet은 정상 종료 횟수를 작업 완료로 계산하지 않으므로 Batch 처리에는 Job을 사용한다.

## 2 ) Job의 Control Plane과 Worker 동작

---

Job Manifest를 적용하면 다음 순서로 처리된다.

```text
Master·관리 Client의 kubectl apply
                │
                ▼
            API Server
                │ Job의 원하는 상태 저장
                ▼
          Job Controller
                │ 필요한 Pod 생성
                ▼
             Scheduler
                │ Worker 선택
                ▼
Worker의 kubelet ──▶ Container Runtime ──▶ Command 실행
                │
                └── 성공·실패 상태를 API Server에 보고
```

Job Controller는 성공한 Pod 수와 실패 상태를 확인한다. 작업이 실패하면 `restartPolicy`와 `backoffLimit`에 따라 같은 Pod의 Container를 재시작하거나 새로운 Pod를 생성한다.

## 3 ) Job 생성과 완료 확인

---

다음 예제는 시작 메시지를 출력하고 10초 동안 대기한 뒤 완료 메시지를 출력한다. 내용을 `sample-job.yaml`로 저장한다.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: hello-job
spec:
  template:
    spec:
      containers:
        - name: hello
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "Job 시작"
              sleep 10
              echo "Job 완료"
      restartPolicy: Never
  backoffLimit: 4
```

| Field | 역할 |
|---|---|
| `apiVersion: batch/v1` | Job이 속한 Batch API Version |
| `spec.template` | 작업을 실행할 Pod Template |
| `restartPolicy` | 실패한 Container 또는 Pod를 다시 실행하는 방식 |
| `backoffLimit` | Job 실패를 판단하기 전 허용할 재시도 한도 |

Master 또는 kubeconfig가 설정된 관리 Client에서 Job을 생성한다.

```bash
kubectl apply -f sample-job.yaml
```

Job과 Job이 만든 Pod를 확인한다.

```bash
kubectl get jobs
kubectl get pods -l job-name=hello-job
```

작업이 완료될 때까지 기다린 뒤 Log를 확인한다.

```bash
kubectl wait --for=condition=complete \
  job/hello-job \
  --timeout=120s

kubectl logs job/hello-job
```

정상적으로 완료되면 Job의 `COMPLETIONS`가 `1/1`이 되고 Pod의 `STATUS`는 `Completed`로 표시된다. 완료된 Pod는 실행 중이지 않지만 Log와 종료 상태 확인을 위해 남아 있을 수 있다.

## 4 ) restartPolicy와 실패 재시도

---

Job의 `spec.template.spec.restartPolicy`에는 `Never` 또는 `OnFailure`만 지정할 수 있다.

| 값 | 실패 시 동작 | 확인 특징 |
|---|---|---|
| `Never` | 실패한 Pod를 다시 사용하지 않고 Job Controller가 새 Pod를 생성할 수 있음 | 실패한 Pod가 여러 개 남을 수 있음 |
| `OnFailure` | 같은 Pod 안에서 실패한 Container를 다시 시작 | Pod의 `RESTARTS` 증가 |

다음 내용을 `sample-error-job.yaml`로 저장한다. 존재하지 않는 경로를 `ls`로 조회하므로 Container가 실패한다.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: error-job
spec:
  template:
    spec:
      containers:
        - name: error-job
          image: busybox:1.36
          command:
            - ls
            - unvalid path
      restartPolicy: Never
  backoffLimit: 4
```

Job을 적용하고 실패 상태와 재시도 Pod를 확인한다.

```bash
kubectl apply -f sample-error-job.yaml
kubectl get job error-job
kubectl get pods -l job-name=error-job
kubectl describe job error-job
```

실패한 Pod의 이름을 확인하여 Log를 조회한다.

```bash
kubectl logs <ERROR_JOB_POD_NAME>
```

`backoffLimit`는 단순히 Container를 정확히 해당 횟수만큼 실행한다는 뜻이 아니라 Job Controller가 실패를 허용하고 재시도할 한도를 설정한다. 재시도 사이에는 점차 증가하는 대기 시간이 적용될 수 있다.

## 5 ) completions와 parallelism

---

Job의 완료 횟수와 동시에 실행할 수 있는 Pod 수를 조정한다.

| Field | 역할 | 기본 동작 |
|---|---|---|
| `completions` | Job이 완료되기 위해 필요한 성공 횟수 | 일반적인 비병렬 Job에서는 1회 완료 |
| `parallelism` | 동시에 실행할 수 있는 최대 Pod 수 | 기본값 1 |
| `backoffLimit` | 실패 재시도 한도 | 명시하지 않으면 기본값 사용 |

4번 성공해야 하며 동시에 최대 2개 Pod를 실행하는 예시는 다음과 같다.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 4
  parallelism: 2
  template:
    spec:
      containers:
        - name: worker
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "$(hostname) 작업 시작"
              sleep 10
              echo "$(hostname) 작업 완료"
      restartPolicy: Never
  backoffLimit: 4
```

내용을 `sample-parallel-job.yaml`로 저장한 뒤 적용하고 Pod 수를 관찰한다.

```bash
kubectl apply -f sample-parallel-job.yaml
kubectl get pods -l job-name=parallel-job --watch
```

한 번만 수행할 작업에서는 `completions: 1`, `parallelism: 1`과 낮은 `backoffLimit`를 명시할 수 있다. 여러 작업을 병렬 처리할 때는 Worker Resource와 외부 System의 처리 용량을 고려하여 `parallelism`을 조정한다.

한 번 실패하면 재시도하지 않아야 하는 Task는 `backoffLimit: 0`으로 설정할 수 있다. 반대로 일시적인 실패가 발생할 수 있는 병렬 작업은 허용할 재시도 횟수를 정해 두어야 한다.

`parallelism: 1`은 하나의 Job 안에서 동시에 실행되는 Pod 수를 제한한다. 서로 다른 여러 Job의 실행 순서를 보장하지는 않는다. Job이 동일 작업을 다시 시도할 수 있으므로 외부 Data를 변경하는 작업은 중복 실행되어도 안전하도록 설계한다.

## 6 ) 완료된 Job 자동 정리

---

`spec.ttlSecondsAfterFinished`를 설정하면 Job이 `Complete` 또는 `Failed` 상태가 된 뒤 지정한 시간이 지나면 TTL Controller가 Job과 종속 Resource를 정리할 수 있다.

다음 내용을 `sample-ttl-job.yaml`로 저장한다.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: sample-ttl-job
spec:
  ttlSecondsAfterFinished: 30
  template:
    spec:
      containers:
        - name: sample-job
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "Job 시작"
              sleep 10
              echo "Job 완료"
      restartPolicy: OnFailure
  backoffLimit: 4
```

Job을 적용하고 완료 후 삭제되는 과정을 확인한다.

```bash
kubectl apply -f sample-ttl-job.yaml
kubectl get job sample-ttl-job --watch
```

`ttlSecondsAfterFinished: 30`은 Job 실행 시작 후 30초가 아니라 Job이 완료된 시점부터 30초를 계산한다.

## 7 ) 명령형 Job 생성

---

간단한 일회성 작업은 Manifest 없이 생성할 수 있다.

```bash
kubectl create job my-job \
  --image=busybox:1.36 \
  -- date
```

Job 상태와 출력 결과를 확인한다.

```bash
kubectl get job my-job
kubectl logs job/my-job
```

명령형 생성은 짧은 확인에는 편리하지만 재시도, 병렬성, TTL과 같은 설정을 반복 관리하려면 Manifest를 사용하는 편이 적합하다.

## 8 ) CronJob

---

> **CronJob**
>
> Cron 형식의 Schedule에 따라 Job Object를 반복 생성하는 Workload Controller이다.

CronJob이 Container를 직접 실행하는 것은 아니다. CronJob Controller가 Schedule에 맞춰 Job을 생성하고, Job Controller가 Pod를 만들며 Worker의 kubelet과 Container Runtime이 실제 Command를 실행한다.

```text
CronJob Controller
      │ Schedule에 따라 Job 생성
      ▼
  Job Controller
      │ Pod 생성과 완료 횟수 관리
      ▼
   Scheduler
      │ Worker 선택
      ▼
Worker의 kubelet ──▶ Container Runtime ──▶ Command 실행
```

## 9 ) CronJob 생성과 Schedule

---

다음 CronJob은 1분마다 현재 시간과 메시지를 출력한다. 내용을 `sample-cronjob.yaml`로 저장한다.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello
spec:
  schedule: "*/1 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: hello
              image: busybox:1.36
              imagePullPolicy: IfNotPresent
              command:
                - /bin/sh
                - -c
                - date; echo Hello from the Kubernetes cluster
          restartPolicy: OnFailure
```

| 위치 | 역할 |
|---|---|
| `spec.schedule` | Job을 생성할 Cron Schedule |
| `spec.jobTemplate` | Schedule마다 생성할 Job Template |
| `jobTemplate.spec.template` | Job이 생성할 Pod Template |

CronJob을 생성하고 Schedule과 최근 실행 시간을 확인한다.

```bash
kubectl apply -f sample-cronjob.yaml
kubectl get cronjobs
kubectl get jobs --watch
```

CronJob이 만든 Job과 Pod의 Log를 확인한다.

```bash
kubectl get jobs --sort-by=.metadata.creationTimestamp
kubectl logs job/<JOB_NAME>
```

CronJob이 생성한 Job 이름은 일반적으로 `hello-<schedule 식별값>` 형태이므로 목록에서 최근 Job 이름을 확인한다.

## 10 ) CronJob 일시 정지

---

신규 Job 생성을 일시 정지한다.

```bash
kubectl patch cronjob hello \
  -p '{"spec":{"suspend":true}}'
```

Suspend 상태를 확인한다.

```bash
kubectl get cronjob hello
```

`suspend: true`는 이후 Schedule에 대한 Job 생성을 멈추지만 이미 시작된 Job을 중단하지 않는다.

다시 Schedule 실행을 허용한다.

```bash
kubectl patch cronjob hello \
  -p '{"spec":{"suspend":false}}'
```

## 11 ) 동시 실행 제어

---

이전 Schedule의 Job이 끝나기 전에 다음 실행 시간이 도착했을 때 `spec.concurrencyPolicy`로 동작을 결정한다.

| 값 | 동작 |
|---|---|
| `Allow` | 동시 실행을 허용하는 기본값 |
| `Forbid` | 이전 Job이 실행 중이면 새 실행을 건너뜀 |
| `Replace` | 이전 Job을 중단하고 새 Job으로 교체 |

하나의 CronJob 안에서 실행이 겹치지 않게 하려면 다음 Field를 추가한다.

```yaml
spec:
  schedule: "*/1 * * * *"
  concurrencyPolicy: Forbid
```

`concurrencyPolicy`는 서로 다른 CronJob 사이의 동시 실행을 제어하지 않는다.

## 12 ) 지연 실행 허용 시간

---

Controller 중단이나 Scheduling 지연으로 Schedule을 놓친 경우 `spec.startingDeadlineSeconds` 이내라면 Job 생성을 허용할 수 있다.

```yaml
spec:
  schedule: "0 * * * *"
  startingDeadlineSeconds: 300
```

매시 정각 실행할 CronJob에서 `300`초를 지정하면 정각 Schedule을 놓친 뒤 5분 이내에는 Job을 시작할 수 있다. 허용 시간을 넘긴 실행은 놓친 Schedule로 처리한다.

## 13 ) Job History 보관

---

CronJob이 만든 완료·실패 Job을 몇 개까지 남길지 설정한다.

```yaml
spec:
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

| Field | 역할 | 기본값 |
|---|---|---|
| `successfulJobsHistoryLimit` | 남겨 둘 성공 Job 수 | `3` |
| `failedJobsHistoryLimit` | 남겨 둘 실패 Job 수 | `1` |

보관된 Job과 Pod를 통해 완료 상태와 Log를 확인할 수 있다. 값을 `0`으로 설정하면 해당 상태의 완료 Job을 보관하지 않는다.

## 14 ) 실습 Resource 정리

---

Master 또는 관리 Client에서 생성한 Resource를 정리한다.

```bash
kubectl delete -f sample-cronjob.yaml --ignore-not-found
kubectl delete -f sample-parallel-job.yaml --ignore-not-found
kubectl delete -f sample-error-job.yaml --ignore-not-found
kubectl delete -f sample-ttl-job.yaml --ignore-not-found
kubectl delete -f sample-job.yaml --ignore-not-found
kubectl delete job my-job --ignore-not-found
```

남아 있는 Job과 CronJob을 확인한다.

```bash
kubectl get jobs,cronjobs
```

## 전체 정리

---

> **최종 정리**
>
> - Job은 계속 실행되는 Pod 수가 아니라 정해진 작업의 성공적인 완료를 관리한다.
>
> - `restartPolicy`, `backoffLimit`, `completions`와 `parallelism`으로 실패 재시도와 병렬 실행을 조정한다.
>
> - `ttlSecondsAfterFinished`는 완료된 Job과 종속 Resource를 일정 시간 뒤 정리한다.
>
> - CronJob은 Schedule에 따라 Job을 만들고 실제 Pod 실행과 완료 관리는 Job Controller가 담당한다.
>
> - `suspend`, `concurrencyPolicy`, `startingDeadlineSeconds`와 History Limit으로 예약 작업의 실행과 보관 범위를 조정한다.
>
> - Control Plane의 Controller가 Job과 Pod의 원하는 상태를 관리하고 Worker의 kubelet과 Container Runtime이 Command를 실행한다.
