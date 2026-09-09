---
title: Version Control과 Git 기본 작업 흐름
description: Version Control System의 종류와 Git의 Working Tree·Staging Area·Repository 구조, File 상태 및 기본 Commit 흐름
date: 2026-09-09
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Git
---

Container Image, Kubernetes Manifest와 Helm Chart도 Source Code와 함께 계속 변경된다. Git을 사용하면 이러한 File의 변경 이력을 기록하고, 특정 시점의 상태를 다시 확인하며, 여러 사람이 변경 내용을 교환하고 병합할 수 있다.

## 1 ) Version Control System

---

> **Version Control System, VCS**
>
> File의 변경 내용을 시간 순서대로 기록하여 특정 Version을 확인하거나 복원하고 여러 작업자의 변경을 조정하는 System이다.

Version 관리 대상은 Source Code로 제한되지 않는다. Text로 표현할 수 있는 설정 File, 문서, Kubernetes Manifest와 Script도 관리할 수 있다. Binary File도 저장할 수 있지만 작은 변경에도 File 전체가 크게 달라질 수 있어 저장 공간과 변경 비교 측면에서 별도 관리 전략이 필요하다.

Version 관리로 해결하려는 주요 문제는 다음과 같다.

- 누가 언제 어떤 내용을 변경했는지 추적한다.

- 현재 상태와 이전 상태의 차이를 비교한다.

- 문제가 생긴 변경의 범위를 찾고 필요한 Version으로 복원한다.

- 여러 작업자가 만든 변경을 하나의 History로 병합한다.

- Local 작업과 Server의 공유 상태를 분리한다.

## 2 ) Version Control System의 종류

---

Version Control System은 History를 저장하고 공유하는 구조에 따라 Local, Centralized와 Distributed 방식으로 구분할 수 있다.

| 구분 | History 저장 위치 | 협업 방식 | 특징 | 대표 예시 |
|---|---|---|---|---|
| Local VCS | 한 Computer의 Local Database | File을 별도 수단으로 전달 | 개인 변경 추적에는 사용할 수 있지만 중앙 협업 기능이 부족 | RCS |
| Centralized VCS | 중앙 Server | Client가 Server에서 Checkout·Commit | 권한과 History를 중앙에서 관리하지만 Server 의존도가 큼 | CVS, Subversion, Perforce |
| Distributed VCS | 각 Clone에 Repository History 저장 | Remote Repository와 Fetch·Push | Network 연결 없이도 Local Commit과 History 조회 가능 | Git, Mercurial |

### Local Version Control

Local VCS는 같은 Computer 안의 Database에 Revision이나 Patch를 기록한다. 수동으로 날짜별 Directory를 복사하는 것보다 변경 이력을 체계적으로 관리할 수 있지만 다른 작업자와 History를 공유하고 병합하기에는 적합하지 않다.

RCS는 대표적인 Local Version Control System이다. 특정 운영체제나 개발 도구 설치 여부만으로 항상 제공된다고 가정하지 않고 현재 환경에서 Package 존재 여부를 확인한다.

### Centralized Version Control

Centralized VCS는 중앙 Server가 기준 Repository를 관리한다.

```text
Client A ─┐
          ├── Central VCS Server
Client B ─┘
```

모든 사용자가 같은 중앙 History를 기준으로 작업하기 쉬운 반면 Server에 접속할 수 없으면 Update나 Commit 같은 주요 작업이 제한될 수 있다. Server 장애가 곧바로 모든 Local 작업 File의 소실을 의미하지는 않지만 중앙 Repository의 Backup과 가용성이 중요하다.

### Distributed Version Control

Distributed VCS의 Clone에는 Working File만 아니라 Repository History와 Metadata가 함께 저장된다.

```text
Developer A Local Repository
              │ fetch·push
              ▼
        Remote Repository
              ▲
              │ fetch·push
Developer B Local Repository
```

각 작업자는 Network가 없어도 Local Commit, Branch 생성과 History 조회를 수행할 수 있다. `checkout`할 때마다 Repository 전체를 다시 Backup하는 방식은 아니다. 일반적으로 `clone`이 Repository를 처음 가져오고, 이후 `fetch`가 Remote의 새로운 Object와 Reference를 전달하며, `checkout` 또는 `switch`는 가지고 있는 Object를 이용해 Working Tree의 상태를 바꾼다.

## 3 ) Git

---

Git은 File 변경을 추적하고 여러 작업자의 변경을 병합할 수 있는 Open Source Distributed Version Control System이다. Linux Kernel 개발을 지원하기 위해 2005년에 Linus Torvalds를 중심으로 처음 개발되었다.

Git의 주요 특징은 다음과 같다.

- 대부분의 작업을 Local Repository에서 수행할 수 있다.

- Commit 단위로 변경 이력과 작성자 정보를 추적한다.

- Branch를 이용해 서로 다른 작업 흐름을 분리한다.

- Remote Repository를 통해 다른 작업자와 History를 교환한다.

- 같은 기반에서 갈라진 변경을 Merge하거나 Rebase할 수 있다.

Git은 GitHub와 같은 Service의 이름이 아니다. Git은 Local에서 실행하는 Version Control 도구이고 GitHub, GitLab과 Bitbucket은 Git Repository Hosting과 협업 기능을 제공하는 Service이다.

## 4 ) Git Hosting Service

---

| Service | Git 이외의 주요 기능 | 자체 설치 선택지 |
|---|---|---|
| GitHub | Pull Request, Issues, Actions, Packages, Pages와 Project 기능 | GitHub Enterprise Server |
| GitLab | Merge Request, Issues, CI/CD, Package·Container Registry | GitLab Self-Managed |
| Bitbucket | Pull Request, Pipeline과 Jira 등 Atlassian 제품 연동 | 제공 형태와 Plan 확인 필요 |

Hosting Service의 무료 사용자 수, Private Repository 범위, CI 실행 시간과 Storage 한도는 변경될 수 있다. 문서에 특정 수치를 고정하지 않고 사용할 시점의 공식 Plan과 조직 정책을 확인한다.

### Remote Repository와 Local Repository

> **Local Repository**
>
> 현재 Computer의 `.git` Directory에 저장된 Git Object, Reference와 설정이다.

> **Remote Repository**
>
> 다른 Repository와 History를 교환하기 위해 이름과 URL로 등록한 Repository이다.

Remote Repository가 반드시 Cloud Service에 있어야 하는 것은 아니다. 접근 가능한 Server의 Bare Repository도 Remote로 사용할 수 있다. `origin`은 특별한 Protocol이 아니라 `git clone`이 기본적으로 등록하는 Remote 이름이다.

```bash
git remote -v
```

## 5 ) Git 설치와 Version 확인

---

Git 공식 배포 경로나 운영체제의 Package Manager를 사용하여 설치한다. Linux 배포판에서는 일반적으로 `git` Package로 제공된다.

설치된 Git Version을 확인한다.

```bash
git --version
```

GitHub 기능을 Terminal에서 사용해야 한다면 GitHub CLI인 `gh`를 별도로 설치할 수 있다. `gh`는 Git 자체를 대체하지 않는다.

```bash
gh --version
```

GUI Client가 필요하면 SourceTree 같은 도구를 사용할 수 있다. GUI에서 Stage, Commit과 Push를 실행해도 내부적으로 다루는 Git Repository와 기본 개념은 같다.

## 6 ) 사용자 정보 설정

---

Git Commit에는 작성자 이름과 Email이 Metadata로 기록된다. 이 값은 Hosting Service Login 정보와 자동으로 같아지는 것이 아니므로 직접 설정을 확인한다.

모든 Local Repository의 기본값으로 사용할 이름과 Email을 설정한다.

```bash
git config --global user.name "<name>"
git config --global user.email "<email>"
```

현재 Repository에서만 다른 값을 사용하려면 `--global`을 제외한다.

```bash
git config user.name "<project-name>"
git config user.email "<project-email>"
```

설정 값을 확인한다.

```bash
git config user.name
git config user.email
git config --list --show-origin
```

| 범위 | Option | 일반적인 저장 위치 | 우선순위 |
|---|---|---|---|
| System | `--system` | System Git 설정 File | 낮음 |
| 사용자 | `--global` | 사용자 Git 설정 File | 중간 |
| 현재 Repository | `--local` 또는 생략 | `.git/config` | 높음 |

같은 Key가 여러 범위에 있으면 더 구체적인 Repository 설정이 사용자 기본값보다 우선한다.

## 7 ) 초기 Branch 이름

---

Git이 새 Repository에 사용할 초기 Branch 이름은 Git Version, 배포판 설정과 사용자 설정에 따라 달라질 수 있다. Hosting Service가 새 Remote Repository에 선택하는 기본 Branch 이름과 Local `git init`의 결과도 항상 같다고 가정할 수 없다.

새 Local Repository의 초기 Branch 이름을 `main`으로 통일하려면 다음과 같이 설정한다.

```bash
git config --global init.defaultBranch main
```

특정 Repository를 만들 때 직접 지정할 수도 있다.

```bash
git init --initial-branch=main
```

이미 Commit이 있는 Repository의 Branch 이름을 바꾸는 작업은 Remote Branch와 협업자에게 영향을 줄 수 있으므로 단순 초기 설정과 구분한다.

## 8 ) Git의 세 작업 영역

---

Git의 기본 흐름을 이해하려면 Working Tree, Staging Area와 Local Repository를 구분해야 한다.

```text
Working Tree
    │ git add
    ▼
Staging Area(Index)
    │ git commit
    ▼
Local Repository(.git)
    │ git push
    ▼
Remote Repository
```

| 영역 | 저장되는 내용 | 주요 확인 명령 |
|---|---|---|
| Working Tree | 사용자가 현재 편집하는 File | `git status`, `git diff` |
| Staging Area | 다음 Commit에 넣기로 선택한 내용 | `git diff --staged` |
| Local Repository | Commit, Tree, Blob와 Reference 등 Git Object | `git log`, `git show` |
| Remote Repository | 다른 Repository와 교환한 Commit과 Branch Reference | `git remote -v`, `git branch -r` |

### Working Tree

Working Tree는 특정 Commit에서 Checkout한 File을 실제로 편집하는 공간이다. 일반 Repository에서는 `.git` Directory를 제외한 Project File 영역으로 볼 수 있다.

### Staging Area

Staging Area는 다음 Commit에 포함할 내용을 선택하는 영역이며 Index라고도 한다. File을 단순히 다른 Directory로 이동시키는 것이 아니라 다음 Commit의 Snapshot에 포함할 내용을 Git Index에 기록한다.

### Local Repository

`.git` Directory에는 Git Object Database, Branch와 Tag Reference, Repository 설정 등이 저장된다. `.git`을 삭제하면 Working File이 남아 있더라도 해당 Local Repository의 History와 설정을 잃을 수 있다.

## 9 ) File 상태

---

| 상태 | 의미 | 다음에 주로 사용하는 명령 |
|---|---|---|
| Untracked | Working Tree에는 있지만 현재 Commit이 추적하지 않는 File | `git add` 또는 `.gitignore` 등록 |
| Modified | 추적 중인 File이 Index 또는 현재 Commit과 달라진 상태 | `git diff`, `git add` |
| Staged | 다음 Commit에 포함할 내용이 Index에 기록된 상태 | `git diff --staged`, `git commit` |
| Committed | 내용이 Local Repository의 Commit에 기록된 상태 | `git log`, `git show` |

하나의 File이 항상 한 상태만 가지는 것은 아니다. File을 Stage한 후 다시 수정하면 같은 File에 Staged 변경과 아직 Stage하지 않은 변경이 동시에 존재할 수 있다.

```bash
git status
git diff
git diff --staged
```

`git status`는 상태를 요약하고 `git diff`는 Working Tree와 Index의 차이, `git diff --staged`는 Index와 현재 Commit의 차이를 보여준다.

## 10 ) Local Repository 기본 실습

---

### Repository 생성

새 실습 Directory를 만들고 이동한다.

```bash
mkdir git-basic-lab
cd git-basic-lab
git init --initial-branch=main
```

`.git` Directory와 현재 상태를 확인한다.

```bash
git status
ls -la
```

### Untracked File 생성

`README.md`를 작성한 뒤 상태를 확인한다.

```bash
touch README.md
git status
```

`README.md`는 아직 Commit이 추적하지 않는 Untracked 상태이다.

### Staging Area에 등록

다음 Commit에 포함할 File을 선택한다.

```bash
git add README.md
git status
git diff --staged
```

`git add`는 File을 Repository History에 즉시 기록하지 않는다. 현재 내용을 Staging Area에 올려 다음 Commit의 입력으로 만든다.

### 첫 Commit 생성

Editor를 열어 Commit Message를 작성한다.

```bash
git commit
```

짧은 실습에서는 `-m`으로 제목을 지정할 수 있다.

```bash
git commit -m "docs: add project README"
```

Commit과 Working Tree 상태를 확인한다.

```bash
git log --oneline --decorate
git status
```

### 수정 후 두 번째 Commit

`README.md`를 수정한 뒤 Working Tree와 현재 Commit의 차이를 확인한다.

```bash
git status
git diff
```

변경 내용을 Stage하고 실제로 Commit될 차이를 다시 검토한다.

```bash
git add README.md
git diff --staged
git commit -m "docs: explain project purpose"
```

History를 확인한다.

```bash
git log --oneline --graph --decorate
```

## 11 ) Commit

---

Commit은 Staging Area에 선택한 Project 상태를 가리키는 Snapshot과 다음 Metadata를 Local Repository에 기록한다.

- 작성자와 Committer 정보

- 작성 시각

- Commit Message

- Project File과 Directory 구조를 가리키는 Tree

- 이전 History를 연결하는 Parent Commit

Git은 File의 전체 복사본을 날짜별 Directory에 반복 저장하는 방식처럼 보이지 않는다. Content를 Object로 관리하고 같은 Content는 같은 Object를 재사용하며 Commit이 Project Snapshot을 가리키도록 구성한다.

### Commit Message

Commit Message는 변경한 결과뿐 아니라 변경 이유를 History에 남기는 정보이다. 여러 줄 Message는 다음 구조로 작성할 수 있다.

```text
변경 내용을 요약한 제목

변경한 이유, 고려한 제약과 필요한 추가 설명
```

제목과 본문 사이를 빈 줄로 구분하면 `git log`, Hosting Service와 여러 Git 도구가 두 영역을 구분해서 표시할 수 있다.

### Commit Object ID

Commit은 Git Object ID로 식별된다. 일반적인 SHA-1 Repository에서는 40자리 16진수이고 SHA-256 형식의 Repository에서는 64자리 16진수이다. 화면에서는 식별에 필요한 앞부분만 축약하여 보여주는 경우가 많다.

```bash
git log --oneline
git rev-parse HEAD
```

짧은 ID는 현재 Repository에서 다른 Object와 구분될 때 편리하게 사용할 수 있지만 고정 길이의 전역 Identifier라고 가정하지 않는다.

## 12 ) Remote Repository와 Push

---

Local Commit은 `git commit`만으로 Remote에 전송되지 않는다. Remote Repository URL을 등록하고 Push해야 한다.

```bash
git remote add origin <remote-repository-url>
git remote -v
```

현재 `main` Branch를 `origin`에 Push하고 Upstream 관계를 설정한다.

```bash
git push -u origin main
```

```text
Working Tree 변경
      │ git add
      ▼
Staging Area
      │ git commit
      ▼
Local main Branch
      │ git push
      ▼
Remote의 main Branch
```

`git push`는 Working Tree File을 바로 Server로 복사하는 명령이 아니다. Local Repository의 Commit과 Reference를 Remote와 교환하여 Remote Branch를 갱신한다.

Push가 거절되면 강제 Push부터 실행하지 않는다. Remote에 Local이 가지고 있지 않은 Commit이 있는지 먼저 확인한다.

```bash
git fetch origin
git log --oneline --graph --decorate --all
```

## 13 ) Container·Kubernetes 작업과 Git

---

Git Repository에는 Container Image Binary 자체보다 Image를 재현할 수 있는 입력을 저장한다.

| 저장 대상 | 예시 |
|---|---|
| Application Source | Python, Java, Go와 JavaScript Source File |
| Image Build 정의 | `Dockerfile`, `.dockerignore` |
| Package 의존성 | `requirements.txt`, `package.json`, Build 설정 |
| Kubernetes 설정 | Deployment, Service, ConfigMap Manifest |
| 배포 구성 | Kustomize Base·Overlay, Helm Chart와 Values |
| 자동화 | CI/CD Workflow와 Shell Script |

다음 정보는 Repository에 직접 Commit하지 않는다.

- Docker Hub Personal Access Token

- Private Key

- 실제 Password가 들어 있는 Secret Manifest

- Cloud Access Key

- Local 개발 환경의 Credential File

Secret을 `.gitignore`에 넣는 것은 실수 방지 수단일 뿐 이미 Commit된 Secret을 History에서 자동으로 제거하지 않는다. Credential이 Commit되거나 외부에 노출됐다면 값을 삭제하는 것과 별개로 해당 Credential을 폐기하고 새로 발급해야 한다.

## 전체 정리

---

> **최종 정리**
>
> - Version Control System은 File의 변경 이력을 기록하고 특정 Version의 비교, 복원과 협업을 지원한다.
>
> - Git은 각 Clone이 Local Repository와 History를 가지는 Distributed Version Control System이다.
>
> - Git과 GitHub·GitLab·Bitbucket 같은 Hosting Service는 서로 다른 대상이다.
>
> - Git의 기본 작업 영역은 Working Tree, Staging Area와 Local Repository이다.
>
> - `git add`는 다음 Commit에 포함할 내용을 선택하고 `git commit`은 이를 Local Repository에 기록한다.
>
> - `git push`는 Local Commit과 Branch Reference를 Remote Repository로 전송한다.
>
> - 초기 Branch 이름과 Object ID 길이는 Version과 Repository 형식에 따라 달라질 수 있으므로 고정된 값으로 단정하지 않는다.
>
> - Container와 Kubernetes 작업에서는 재현 가능한 설정을 Git에 저장하고 Token, Password와 Private Key는 Commit하지 않는다.
