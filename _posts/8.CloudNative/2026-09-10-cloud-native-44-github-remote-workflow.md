---
title: GitHub Remote Repository 작업 흐름
description: GitHub 인증 방식과 Clone·Fork·Remote·Fetch·Pull·Push의 차이 및 Local Repository를 Remote와 연결하는 방법
date: 2026-09-10
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - Git
---

[Version Control과 Git 기본 작업 흐름](/cloud-native-42-git-version-control-basics/)에서 Local Repository의 구조를 정리했고 [Git 이력 관리와 Branch 작업](/cloud-native-43-git-history-branch/)에서 Branch를 나누고 통합하는 방법을 다뤘다. 이 글에서는 Local Repository와 GitHub의 Remote Repository 사이에서 Commit과 Branch를 교환한다.

## 1 ) GitHub와 Git

---

Git은 Local에서 Commit과 Branch History를 관리하는 Version Control System이다. GitHub는 Git Repository를 Hosting하고 협업 기능을 제공하는 Service이다.

| GitHub 기능 | 용도 |
|---|---|
| Repository Hosting | Git Commit, Branch와 Tag 저장·공유 |
| Pull Request | Branch 변경 검토와 병합 |
| Issues | 작업과 문제 추적 |
| Actions | Build, Test와 배포 Workflow 실행 |
| Packages | Package와 Container Image 저장 |
| Projects | Issue와 Pull Request 기반 작업 관리 |
| Pages | Repository Content 기반 정적 Site 배포 |

GitHub의 무료 범위, Storage와 Actions 사용량은 Plan에 따라 달라질 수 있으므로 사용 시점의 공식 정책을 확인한다.

```text
Local Repository
├── Working Tree
├── Staging Area
└── Local Branch와 Commit
          │
          │ fetch·pull·push
          ▼
GitHub Remote Repository
├── Remote Branch
├── Tag
└── Pull Request·Issue·Actions
```

## 2 ) Remote Repository 인증 방식

---

Private Repository를 Clone하거나 Push할 때 GitHub는 사용자를 인증하고 Repository 권한을 확인한다. Remote URL 형식에 따라 HTTPS 또는 SSH 인증을 사용한다.

| 방식 | 인증 수단 | 특징 |
|---|---|---|
| HTTPS | Personal Access Token과 Credential Helper | HTTPS URL을 사용하며 운영체제 Credential Store와 연동 가능 |
| SSH | SSH Private Key와 GitHub에 등록한 Public Key | GitHub Password나 PAT를 Push마다 전달하지 않음 |
| GitHub CLI | `gh auth login` | Browser, HTTPS 또는 SSH 인증 설정을 안내하고 GitHub API도 함께 사용 |

### HTTPS와 Personal Access Token

GitHub의 HTTPS Git 작업에서 Account Password를 대신해 Personal Access Token을 사용할 수 있다. Token에는 필요한 Repository와 작업 범위만 부여하고 만료 기간을 설정한다.

Token 값을 다음 위치에 직접 작성하지 않는다.

- Markdown과 Source Code

- `git remote` URL

- Shell Script

- `.gitconfig`의 평문 설정

- CI Log에 출력되는 명령 인자

현재 Credential Helper 설정을 확인한다.

```bash
git config --show-origin --get-all credential.helper
```

Git Credential Manager, macOS Keychain 같은 Helper를 사용하면 Credential을 운영체제의 Credential Store와 연결할 수 있다. 설치 방식과 Helper 이름은 운영체제와 Git 배포판에 따라 다르므로 임의로 덮어쓰기 전에 기존 설정을 확인한다.

저장된 계정을 바꿀 때는 Git 설정만 반복해서 추가하지 않는다. 현재 Helper 또는 운영체제 Credential Manager에서 기존 GitHub Credential을 제거한 뒤 다시 인증한다.

### SSH 인증

SSH Remote는 다음 형식을 사용한다.

```text
git@github.com:<owner>/<repository>.git
```

Local Private Key는 외부에 공개하지 않고 대응하는 Public Key만 GitHub 계정이나 조직에 등록한다. SSH Key 생성과 공개키 등록 이유는 [원격 접속](/12-remote-access/)의 SSH Key 절에서 다룬다.

GitHub SSH 연결을 확인한다.

```bash
ssh -T git@github.com
```

첫 연결에서는 Host Key Fingerprint를 GitHub 공식 문서의 값과 대조한 뒤 신뢰 여부를 결정한다.

### GitHub CLI 인증

GitHub CLI를 사용한다면 대화형 Login 절차를 실행할 수 있다.

```bash
gh auth login
gh auth status
```

필요한 경우 현재 `gh` 인증을 Git Credential 설정에 연결한다.

```bash
gh auth setup-git
```

계정을 변경할 때는 현재 인증 상태를 확인하고 Logout한다.

```bash
gh auth status
gh auth logout
gh auth login
```

`gh` 인증과 SSH Agent에 올라간 Key는 별도 상태일 수 있다. 오류가 발생하면 Remote URL이 HTTPS인지 SSH인지 먼저 확인한다.

## 3 ) 올바른 Remote URL

---

GitHub Repository의 HTTPS와 SSH URL은 형식이 다르다.

```text
HTTPS
https://github.com/<owner>/<repository>.git

SSH
git@github.com:<owner>/<repository>.git
```

다음 주소는 HTTPS Scheme과 SSH 구분자를 섞었으므로 올바른 GitHub Remote URL이 아니다.

```text
https://github.com:<owner>/<repository>.git
```

현재 Repository의 Remote 이름과 URL을 확인한다.

```bash
git remote -v
git remote get-url origin
```

Remote 이름은 URL 자체가 아니다. `origin`은 `git clone`이 기본으로 등록하는 관례적인 이름이며 원하는 이름으로 바꿀 수 있다.

## 4 ) Clone과 Fork

---

Clone과 Fork는 Repository의 복사 위치와 소유 관계가 다르다.

| 작업 | 생성 위치 | 결과 |
|---|---|---|
| Clone | Local Computer | Remote Repository의 Local Repository와 Working Tree 생성 |
| Fork | GitHub 계정 | 원본과 별도로 관리되는 GitHub Remote Repository 생성 |

### Clone

Repository를 현재 Directory 아래에 복제한다.

```bash
git clone \
  https://github.com/<owner>/<repository>.git
```

Local Directory 이름을 직접 지정할 수 있다. 대상 Directory는 비어 있거나 존재하지 않아야 한다.

```bash
git clone \
  https://github.com/<owner>/<repository>.git \
  <local-directory>
```

Clone이 끝나면 등록된 Remote와 Branch를 확인한다.

```bash
cd <local-directory>
git remote -v
git branch --all
git log --oneline --decorate -n 5
```

큰 공개 Repository를 예제로 그대로 Clone하면 Network와 Disk를 많이 사용할 수 있다. Git 명령 학습에는 직접 만든 작은 Repository나 전용 실습 Repository를 사용한다.

### Fork

Fork는 GitHub에서 원본 Repository를 자신의 계정이나 조직 아래에 복사하는 기능이다. 원본 Repository에 직접 Push 권한이 없어도 Fork에서 Branch를 Push하고 Pull Request를 만들 수 있다.

Fork를 Clone하면 일반적으로 자신의 Fork가 `origin`이 된다. 원본 Repository의 변경을 가져오려면 `upstream` Remote를 별도로 등록한다.

```bash
git remote add upstream \
  https://github.com/<original-owner>/<repository>.git
git remote -v
```

```text
origin
└── 자신의 GitHub Fork

upstream
└── 원본 GitHub Repository
```

## 5 ) Remote 연결과 변경

---

### Remote 추가

기존 Local Repository에 GitHub Repository를 연결한다.

```bash
git remote add origin \
  https://github.com/<owner>/<repository>.git
git remote -v
```

같은 이름의 Remote가 이미 있으면 `remote origin already exists` 오류가 발생한다. 기존 URL을 확인하고 새 Remote가 필요한지 URL 변경이 필요한지 판단한다.

```bash
git remote get-url origin
```

### Remote URL 변경

```bash
git remote set-url origin \
  git@github.com:<owner>/<repository>.git
git remote -v
```

이 명령은 Local Repository의 연결 URL을 변경한다. GitHub Repository의 이름이나 소유자를 바꾸는 작업은 아니다.

### Remote 이름 변경

```bash
git remote rename <old-name> <new-name>
git remote -v
```

### Remote 연결 제거

```bash
git remote remove <remote-name>
git remote -v
```

`git remote remove`는 Local `.git/config`의 Remote 연결을 제거한다. GitHub의 Remote Repository와 그 안의 Data는 삭제하지 않는다.

## 6 ) Fetch와 Pull

---

Remote의 변경을 가져오는 명령은 Local Branch를 자동으로 바꾸는지에 따라 구분한다.

### Fetch

```bash
git fetch origin
```

Fetch는 Remote의 새 Commit, Tag와 Branch Reference를 Local Repository로 가져온다. 현재 Working Tree와 Local Branch에는 자동으로 통합하지 않는다.

```text
GitHub origin/main
        │ git fetch origin
        ▼
Local origin/main 갱신
        │
        └── 현재 Local main은 그대로 유지
```

가져온 상태와 Local Branch를 비교한다.

```bash
git log --oneline --graph --decorate --all
git diff main..origin/main
```

### Pull

```bash
git pull origin main
```

Pull은 먼저 Fetch한 뒤 가져온 변경을 현재 Branch에 통합한다. 기본 통합 방식은 Git 설정과 Option에 따라 Merge 또는 Rebase가 될 수 있다.

실행 전 현재 Branch와 Working Tree 상태를 확인한다.

```bash
git branch --show-current
git status
git fetch origin
git log --oneline --graph --decorate --all
```

통합 방식을 명시하면 의도가 분명해진다.

```bash
# Merge 방식
git pull --no-rebase origin main

# Rebase 방식
git pull --rebase origin main

# Fast-forward만 허용
git pull --ff-only origin main
```

팀이 정한 History 정책과 현재 Branch의 공유 여부에 맞는 방식을 선택한다.

## 7 ) Local Repository를 GitHub에 Push

---

빈 GitHub Repository를 준비한 뒤 기존 Local Repository를 연결하는 흐름은 다음과 같다.

```text
Local File 작성
      │ git add
      ▼
Staging Area
      │ git commit
      ▼
Local Branch
      │ git remote add
      ▼
Remote 연결
      │ git push -u
      ▼
GitHub Remote Branch
```

### Local Repository 확인

```bash
git status
git branch --show-current
git log --oneline --decorate -n 5
```

아직 Commit이 없다면 File을 Stage하고 Commit한다.

```bash
git add <file>
git diff --staged
git commit -m "docs: add initial content"
```

GitHub에서 만든 빈 Repository를 `origin`으로 등록한다.

```bash
git remote add origin \
  https://github.com/<owner>/<repository>.git
git remote -v
```

현재 Branch 이름을 확인한 뒤 같은 이름의 Remote Branch로 Push한다.

```bash
git branch --show-current
git push -u origin main
```

`-u` 또는 `--set-upstream`은 현재 Local Branch가 어느 Remote Branch를 추적할지 설정한다. 관계가 설정된 뒤에는 Remote와 Branch 인자를 생략할 수 있다.

```bash
git push
git pull --ff-only
```

새로운 Local Branch를 처음 Push할 때는 해당 Branch의 Upstream을 다시 설정할 수 있다.

```bash
git switch -c feature/login
git push -u origin feature/login
```

Local Repository의 초기 Branch가 항상 `master`이고 GitHub가 항상 `main`인 것은 아니다. 실제 이름을 확인하고 필요할 때만 Branch 이름을 변경한다.

```bash
git branch --show-current
git branch -M main
```

공유 중인 Branch 이름을 변경하면 Remote 설정, Pull Request와 다른 작업자의 Local Branch에 영향을 줄 수 있다.

## 8 ) SourceTree에서 Remote 작업

---

SourceTree의 Remote 작업도 같은 Git 상태를 변경한다.

| SourceTree 작업 | Git 동작 | 실행 후 확인 |
|---|---|---|
| Clone | `git clone` | `git remote -v` |
| Remote 추가 | `git remote add` | `git remote get-url` |
| Fetch | `git fetch` | `git log --all --graph` |
| Pull | `git pull` | `git status`, `git log` |
| Push | `git push` | Local·Remote Branch 관계 |

Push 화면에서는 대상 Remote와 Branch, Tag 포함 여부를 확인한다. GUI에 저장된 계정과 Repository를 실제로 Push할 권한이 있는 GitHub 계정이 다르면 인증 오류가 발생할 수 있다.

SourceTree에서 작업한 뒤 CLI로 다음 상태를 확인할 수 있다.

```bash
git status
git remote -v
git branch -vv
git log --oneline --graph --decorate --all
```

## 9 ) Push 실패 진단

---

오류 Message에서 인증, 권한, URL과 History 문제를 먼저 구분한다.

| 증상 | 우선 확인할 내용 |
|---|---|
| `non-fast-forward` | Remote에 Local이 가지지 않은 Commit이 있는지 확인 |
| HTTPS `403` | 현재 계정의 Repository 쓰기 권한과 Token Scope |
| `Authentication failed` | PAT 만료·폐기 여부와 Credential Helper의 저장 계정 |
| `Permission denied (publickey)` | SSH Key, SSH Agent, GitHub Public Key 등록과 SSH URL |
| `Repository not found` | Owner·Repository 이름, Private Repository 접근 권한 |
| `remote origin already exists` | 기존 `origin` URL과 추가하려는 URL 비교 |
| `src refspec ... does not match any` | Local Commit 존재 여부와 Branch 이름 |

### 현재 연결 상태 확인

```bash
git remote -v
git branch --show-current
git branch -vv
git status
```

### GitHub CLI 인증 확인

```bash
gh auth status
```

### SSH 인증 확인

Remote가 SSH URL일 때 실행한다.

```bash
ssh -T git@github.com
```

### Remote History 확인

Non-fast-forward 오류가 발생하면 Force Push 전에 Remote History를 가져온다.

```bash
git fetch origin
git log --oneline --graph --decorate --all
```

Remote 변경을 확인하지 않은 `git push --force`는 다른 작업자의 Commit을 Remote Branch에서 제외할 수 있다. History를 다시 써야 하는 명확한 이유와 팀 합의가 없다면 사용하지 않는다.

## 10 ) Credential 노출 대응

---

PAT, Password나 Private Key가 Source File, Commit 또는 화면 공유에 노출되면 문자열을 지우는 작업만으로 해결되지 않는다.

1. GitHub에서 해당 Credential을 폐기한다.

2. 필요한 최소 권한과 만료 기간으로 새 Credential을 발급한다.

3. Local Credential Helper와 CI Secret을 새 값으로 갱신한다.

4. Repository에 Commit됐다면 Git History와 Remote Cache의 정리 범위를 확인한다.

5. Audit Log와 관련 Service Log에서 의심스러운 사용 기록을 확인한다.

새 Token 값을 문서의 예제에 다시 넣지 않는다.

```text
<GITHUB_USERNAME>
<GITHUB_PAT>
<REPOSITORY_URL>
```

## 전체 정리

---

> **최종 정리**
>
> - GitHub는 Git Remote Repository를 Hosting하고 Pull Request, Issue와 자동화 기능을 제공한다.
>
> - HTTPS는 PAT와 Credential Helper를, SSH는 Local Private Key와 GitHub에 등록한 Public Key를 사용한다.
>
> - Clone은 Local Repository를 만들고 Fork는 GitHub 계정 아래에 별도 Remote Repository를 만든다.
>
> - Fetch는 Remote 상태를 가져오고 Pull은 가져온 변경을 현재 Branch에 통합한다.
>
> - `git push -u`는 현재 Local Branch와 Remote Branch의 Upstream 관계를 설정한다.
>
> - Push 실패 시 Force Push보다 Remote URL, 인증 계정, 권한, Branch와 Remote History를 먼저 확인한다.
>
> - 노출된 Credential은 문서에서 삭제한 뒤 GitHub에서 폐기하고 새로 발급해야 한다.
