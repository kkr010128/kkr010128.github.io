---
title: Kubernetes Kustomize로 Manifest 구성 관리
description: Kustomize의 Resource 조합, 공통 Label, Base·Overlay, Patch와 Secret Generator를 이용한 환경별 Manifest 관리 정리
date: 2026-09-08
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Kubernetes
---

Kubernetes Application은 Deployment 하나만으로 끝나지 않고 Service, Ingress, ConfigMap과 Secret 등 여러 Manifest로 구성된다. Kustomize는 원본 YAML을 Template 문법으로 바꾸지 않고 Resource를 조합하고 공통 설정과 환경별 차이를 적용하여 최종 Manifest를 만든다.

## 1 ) Kustomize

---

> **Kustomize**
>
> Kubernetes Resource YAML을 Base로 유지하면서 Label, Image, Namespace와 Patch를 조합하여 환경별 Manifest를 생성하는 구성 관리 도구이다.

Kustomize가 제공하는 주요 기능은 다음과 같다.

- 여러 Manifest를 하나의 구성 단위로 조합한다.

- 여러 Resource에 공통 Label, Annotation, Namespace와 이름 Prefix를 적용한다.

- Base를 재사용하고 개발·검증·운영 환경의 차이만 Overlay에 기록한다.

- Strategic Merge Patch와 JSON Patch로 필요한 Field만 변경한다.

- File이나 Literal을 이용하여 ConfigMap과 Secret Manifest를 생성한다.

Kustomize는 Cluster 안에서 실행되는 Controller가 아니다. Master 또는 kubeconfig가 설정된 관리 Client에서 Manifest를 Rendering하고, 결과를 API Server에 적용하는 Client 도구이다.

```text
Base Resources + Overlay + Generator
                 │
                 ▼
        Kustomize Rendering
                 │ 최종 Kubernetes Manifest
                 ▼
             API Server
                 │
                 ▼
Deployment·Service 등 각 Controller
                 │
                 ▼
Scheduler ──▶ Worker의 kubelet ──▶ Container Runtime
```

## 2 ) kubectl 내장 기능과 독립 실행형 Kustomize

---

Kustomize는 `kubectl`에 내장된 기능과 별도 설치하는 독립 실행형 Binary로 사용할 수 있다.

| 구분 | Rendering | 적용 | 특징 |
|---|---|---|---|
| kubectl 내장 | `kubectl kustomize <directory>` | `kubectl apply -k <directory>` | 별도 도구 없이 기본 기능 사용 |
| 독립 실행형 | `kustomize build <directory>` | Rendering 결과를 kubectl에 전달 | 최신 Kustomize 기능과 편집 명령을 별도로 선택 가능 |

두 도구에 포함된 Kustomize Version이 다르면 지원 Field나 Rendering 결과가 달라질 수 있다. 팀과 CI에서는 어느 도구와 Version을 기준으로 하는지 고정한다.

```bash
kubectl version --client
kubectl kustomize --help
kustomize version
```

기본적인 Build와 배포만 필요하다면 kubectl의 `-k` 기능으로 시작할 수 있다. 독립 실행형의 특정 기능이나 Version 통일이 필요할 때 별도 Binary를 설치한다.

## 3 ) asdf를 이용한 Version 관리

---

asdf는 여러 언어와 CLI 도구의 Version을 `.tool-versions` File로 관리하는 Version Manager이다. 현재 asdf 0.16 이상은 Go로 다시 작성된 Binary이며, 0.15 이하의 Shell Script 방식과 설치 및 명령 체계가 다르다.

### asdf 0.16 이상

asdf Binary를 운영체제와 Architecture에 맞게 설치하고 `$ASDF_DATA_DIR/shims`를 `PATH` 앞에 추가한다. 설치 방식은 배포판 Package Manager나 공식 Release 절차를 따른다.

Kustomize Plugin과 사용할 Version을 확인한다.

```bash
asdf plugin add kustomize
asdf list all kustomize
asdf install kustomize <kustomize-version>
asdf set --home kustomize <kustomize-version>
kustomize version
```

Project Directory에만 Version을 고정하려면 해당 Directory에서 `--home` 없이 `asdf set kustomize <version>`을 실행한다. 생성된 `.tool-versions`를 함께 관리하면 작업자와 CI가 같은 Version을 선택할 수 있다.

### asdf 0.15 이하의 Legacy 방식

다음 방식은 asdf `v0.14.0`처럼 Bash로 구현된 Version에서 사용하던 설치 방식이다. 현재 설치 절차로 사용하지 않으며, 기존 환경을 이해하거나 Migration할 때만 참고한다.

```bash
git clone https://github.com/asdf-vm/asdf.git ~/.asdf \
  --branch v0.14.0

echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc
source ~/.bashrc

asdf plugin add kustomize
asdf install kustomize 5.3.0
asdf global kustomize 5.3.0
```

asdf 0.16 이상에서는 `asdf global`과 `asdf local`이 제거되고 `asdf set`으로 대체됐다. 기존 설치를 Migration할 때는 Shell RC File의 `. "$HOME/.asdf/asdf.sh"` 설정도 현재 Binary와 Shim 경로 설정으로 변경해야 한다.

## 4 ) Base Directory와 Resource 작성

---

Echo Application의 공통 Resource를 다음 구조로 작성한다.

```text
echo/
└── base/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    └── kustomization.yaml
```

Directory를 생성하고 이동한다.

```bash
mkdir -p echo/base
cd echo/base
```

다음 내용을 `deployment.yaml`로 저장한다. nginx Container가 같은 Pod의 Echo Container에 `localhost:8080`으로 요청을 전달한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: echo
  template:
    metadata:
      labels:
        app.kubernetes.io/name: echo
    spec:
      containers:
        - name: nginx
          image: ghcr.io/jpubdocker/simple-nginx-proxy:v0.1.0
          env:
            - name: NGINX_PORT
              value: "80"
            - name: SERVER_NAME
              value: localhost
            - name: BACKEND_HOST
              value: localhost:8080
            - name: BACKEND_MAX_FAILS
              value: "3"
            - name: BACKEND_FAIL_TIMEOUT
              value: 10s
          ports:
            - name: http
              containerPort: 80
        - name: echo
          image: ghcr.io/jpubdocker/echo:v0.1.0
```

같은 Pod의 Container는 Network Namespace를 공유하므로 nginx는 Echo Container를 `localhost:8080`으로 호출할 수 있다.

다음 내용을 `service.yaml`로 저장한다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: echo
spec:
  selector:
    app.kubernetes.io/name: echo
  ports:
    - name: echo
      port: 80
      targetPort: http
      protocol: TCP
```

다음 내용을 `ingress.yaml`로 저장한다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: echo
spec:
  ingressClassName: nginx
  rules:
    - host: echo.jpub.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: echo
                port:
                  number: 80
```

Ingress Resource가 실제 Traffic을 처리하려면 `nginx` IngressClass를 담당하는 Controller가 필요하다. ingress-nginx Controller의 현재 상태와 실습 조건은 [Kubernetes Ingress Resource와 HTTP Routing](/cloud-native-33-kubernetes-ingress-routing/)에서 확인할 수 있다.

## 5 ) kustomization.yaml로 Resource 조합

---

독립 실행형 Kustomize는 현재 Directory의 Resource를 검색하여 `kustomization.yaml`을 만들 수 있다.

```bash
kustomize create --autodetect
```

직접 작성한다면 다음과 같다.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - ingress.yaml
```

`resources`의 경로는 `kustomization.yaml`을 기준으로 해석된다. 조합 결과를 화면에 출력한다.

```bash
kustomize build .
```

kubectl 내장 기능으로 같은 구성을 Rendering할 수 있다.

```bash
kubectl kustomize .
```

Rendering 결과를 File로 저장하지 않아도 Directory를 직접 적용하고 삭제할 수 있다.

```bash
kubectl diff -k .
kubectl apply -k .
kubectl delete -k .
```

독립 실행형 Kustomize 결과를 Pipe로 전달할 때는 kubectl이 표준 입력의 Manifest를 읽도록 `-f -`를 사용한다.

```bash
kustomize build . | kubectl apply -f -
kustomize build . | kubectl delete -f -
```

`kustomize build . | kubectl apply -k .`처럼 사용하면 앞 명령의 표준 출력은 적용 대상이 되지 않는다. `-k`는 표준 입력이 아니라 지정한 Kustomization Directory를 읽는 Option이다.

## 6 ) 공통 Label 적용

---

여러 Resource에 같은 Label을 반복하지 않고 `labels` Transformer로 추가할 수 있다. `kustomization.yaml`에 다음 내용을 추가한다.

```yaml
labels:
  - pairs:
      app.kubernetes.io/part-of: echo-system
    includeSelectors: false
```

`includeSelectors: false`는 Resource의 Metadata와 Pod Template 등에 Label을 추가하되 기존 Selector를 바꾸지 않는다. Application을 식별하는 `app.kubernetes.io/name: echo`는 Deployment Selector, Pod Label과 Service Selector의 연결 조건이므로 Base Manifest에 명시적으로 유지한다.

독립 실행형 Kustomize의 편집 명령으로도 Label을 설정할 수 있다.

```bash
kustomize edit set label \
  'app.kubernetes.io/part-of:echo-system'
```

편집 명령이 생성하는 Field 형태는 Kustomize Version에 따라 달라질 수 있으므로 변경된 `kustomization.yaml`과 Build 결과를 함께 확인한다.

```bash
sed -n '1,160p' kustomization.yaml
kustomize build .
```

Deployment의 `spec.selector`는 필수이며 `spec.template.metadata.labels`와 일치해야 한다. 공통 Label 기능을 사용한다는 이유로 Base Deployment의 필수 Selector를 제거하지 않는다.

## 7 ) Base와 Overlay

---

Base에는 환경에 공통인 Resource를 두고 Overlay에는 개발·검증·운영 환경별 차이만 둔다.

```text
echo/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── kustomization.yaml
└── overlays/
    └── dev/
        ├── kustomization.yaml
        ├── patch-deployment.yaml
        └── patch-ingress.yaml
```

`echo/base`에서 상위 Directory로 이동한 뒤 개발 Overlay를 생성한다.

```bash
cd ..
mkdir -p overlays/dev
cd overlays/dev
kustomize create --resources ../../base
```

생성되는 `overlays/dev/kustomization.yaml`의 기본 형태는 다음과 같다.

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
```

Base Directory 자체도 `kustomization.yaml`을 가지므로 Overlay의 `resources`에서 하나의 구성 단위로 참조할 수 있다. Version Control에는 `kustomize build` 결과보다 Base, Overlay와 Patch 원본을 저장한다.

## 8 ) Strategic Merge 방식의 Patch

---

개발 환경에서 Replica를 2개로 늘리고 nginx의 실패 허용 횟수를 변경한다. 다음 내용을 `patch-deployment.yaml`로 저장한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: nginx
          env:
            - name: BACKEND_MAX_FAILS
              value: "5"
```

전체 Deployment를 복사하지 않고 변경할 Field와 병합 기준이 되는 Resource·Container 이름만 작성한다. `overlays/dev/kustomization.yaml`에 Patch를 추가한다.

```yaml
patches:
  - path: patch-deployment.yaml
    target:
      group: apps
      version: v1
      kind: Deployment
      name: echo
```

`patchesStrategicMerge`는 기존 구성에서 볼 수 있는 Legacy Field이다. 현재 문서에서는 Strategic Merge Patch와 JSON Patch를 모두 통합해서 표현할 수 있는 `patches` Field를 사용한다.

## 9 ) JSON Patch

---

Ingress Host처럼 배열 안의 특정 Field를 경로로 지정할 때 JSON Patch를 사용할 수 있다. 다음 내용을 `patch-ingress.yaml`로 저장한다.

```yaml
- op: replace
  path: /spec/rules/0/host
  value: dev-echo.jpub.local
```

JSON Pointer의 `/spec/rules/0/host`는 첫 번째 Rule의 `host` Field를 의미한다. 마지막에 `/`를 추가하면 다른 경로로 해석되므로 붙이지 않는다.

`overlays/dev/kustomization.yaml`의 `patches`에 다음 항목을 추가한다.

```yaml
patches:
  - path: patch-deployment.yaml
    target:
      group: apps
      version: v1
      kind: Deployment
      name: echo
  - path: patch-ingress.yaml
    target:
      group: networking.k8s.io
      version: v1
      kind: Ingress
      name: echo
```

개발 Overlay의 최종 결과와 변경 사항을 확인한다.

```bash
kustomize build .
kubectl diff -k .
```

Build 결과에서 Deployment의 Replica가 `2`, `BACKEND_MAX_FAILS`가 `5`, Ingress Host가 `dev-echo.jpub.local`인지 확인한다.

## 10 ) Secret Generator

---

Kustomize의 `secretGenerator`는 File, Env File 또는 Literal을 읽어 Secret Manifest를 생성한다. 다음 내용을 `secret.env`로 저장한다.

```dotenv
API_USERNAME=echo-user
API_PASSWORD=REPLACE_WITH_SECRET
```

실제 Secret 값이 있는 File은 Version Control 대상에서 제외한다.

```gitignore
secret.env
```

`overlays/dev/kustomization.yaml`에 Generator를 추가한다.

```yaml
secretGenerator:
  - name: echo-secret
    envs:
      - secret.env
```

생성 결과를 확인한다.

```bash
kustomize build .
```

생성된 이름에는 `echo-secret-<content-hash>` 형태의 Suffix가 붙는다. Secret을 참조하는 Workload가 같은 Kustomization 안에 있으면 Kustomize가 알려진 참조 Field의 이름도 함께 변환한다.

```yaml
envFrom:
  - secretRef:
      name: echo-secret
```

Hash Suffix는 Secret 내용이 바뀌었을 때 Pod Template의 참조 이름도 바뀌게 하여 새 Rollout을 유도한다. `generatorOptions.disableNameSuffixHash: true`로 끌 수 있지만 자동 갱신 동작도 사라지므로 이유 없이 비활성화하지 않는다.

Secret을 Git에서 제외해도 보안이 완성되는 것은 아니다. `kustomize build` 결과에는 Base64로 표현된 값이 포함되며 Base64는 암호화가 아니다. Terminal 출력, CI Log, 임시 File과 Cluster 접근 권한을 함께 관리해야 한다.

## 11 ) Remote Resource

---

공개된 Git Repository나 URL의 Kustomization을 `resources`에서 참조할 수 있다. Remote Resource는 재사용에 편리하지만 외부 Network와 공급자의 변경에 의존한다.

```yaml
resources:
  - https://example.com/application/kustomization.yaml
```

운영 구성에서는 움직이는 Branch나 변경 가능한 URL보다 검증한 Commit이나 Release Tag를 고정하고, 적용 전 Build 결과와 Resource 권한을 검토한다.

ingress-nginx `controller-v1.8.1`의 Remote Kustomization은 Kustomize의 Network Resource 예제로 사용된 적이 있지만 현재 설치 대상으로 사용하지 않는다. ingress-nginx는 2026년 3월 24일 이후 신규 Release와 보안 수정이 없는 Retirement 상태이다.

```bash
curl https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/kustomization.yaml
```

위 명령은 과거 Kustomization File의 내용을 확인할 뿐 Cluster에 배포하지 않는다. 신규 환경에서는 유지보수 중인 Controller나 Gateway API 구현을 선택한다.

## 12 ) 개발 Overlay 적용과 확인

---

Master 또는 관리 Client의 `echo/overlays/dev`에서 최종 Manifest를 먼저 확인한다.

```bash
kubectl kustomize .
kubectl diff -k .
kubectl apply -k .
```

Control Plane은 Rendering된 결과만 받으며 Base와 Overlay Directory 구조를 알지 못한다. API Server에 저장된 Deployment와 Service를 각 Controller가 조정하고, Scheduler가 선택한 Worker에서 kubelet이 Pod를 실행한다.

```bash
kubectl rollout status deployment/echo
kubectl get deployment,service,ingress
kubectl get pods \
  -l app.kubernetes.io/name=echo \
  -o wide
kubectl get endpointslice \
  -l kubernetes.io/service-name=echo
```

문제가 있으면 적용된 Resource만 보지 말고 Rendering 결과가 예상한 Selector, Image, Host와 Secret 이름을 포함하는지 먼저 확인한다.

## 13 ) 실습 Resource 정리

---

적용에 사용한 같은 Overlay Directory에서 Resource를 삭제한다.

```bash
kubectl delete -k echo/overlays/dev
```

현재 Directory가 `echo/overlays/dev`라면 다음과 같이 실행한다.

```bash
kubectl delete -k .
```

Secret Generator가 만든 Secret도 같은 Kustomization의 Resource이므로 함께 삭제된다.

## 전체 정리

---

> **최종 정리**
>
> - Kustomize는 Base Resource에 공통 설정과 환경별 Patch를 적용하여 최종 Kubernetes Manifest를 만든다.
>
> - kubectl 내장 기능은 `kubectl kustomize`와 `kubectl apply -k`로 사용하고 독립 실행형은 `kustomize build`로 Rendering한다.
>
> - Base에는 공통 구성을, Overlay에는 환경별 차이를 두며 Build 결과보다 Base와 Patch 원본을 Version Control에서 관리한다.
>
> - Deployment Selector와 Pod Label, Service Selector의 연결은 Kustomize를 사용해도 유지해야 한다.
>
> - `patches`에서 Strategic Merge Patch와 JSON Patch를 사용하여 필요한 Field만 변경할 수 있다.
>
> - `secretGenerator`는 Secret 이름에 Content Hash를 추가하지만 Secret 값을 암호화하지는 않는다.
>
> - Control Plane은 Rendering된 Kubernetes Resource만 처리하고 Worker의 kubelet이 최종 Pod Spec을 실행한다.
>
> - 다음 글인 [Kubernetes Helm Chart와 Release 관리](/cloud-native-40-kubernetes-helm/)에서는 여러 Resource를 Version이 있는 Package로 묶고 설치·Upgrade·Rollback하는 방법을 다룬다.
