---
title: GitHub Actions Workflow와 CI/CD 실습
description: GitHub Actions의 실행 구조를 이해하고 Node.js와 Python Test부터 Docker Image Build 및 Docker Hub Push까지 자동화한다
date: 2026-09-11
updated_at: 2026-09-17
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
  - GitHubActions
---

[CI/CD Pipeline과 Container 배포 흐름](/cloud-native-45-cicd-pipeline/)에서 Code 변경부터 Build, Test와 배포까지의 전체 흐름을 정리했다. GitHub Actions는 GitHub Repository에서 발생하는 Event를 기준으로 이 작업을 자동 실행하는 Workflow 도구이다.

## 1 ) GitHub Actions 개요

---

GitHub Actions는 Software 개발 주기에 필요한 Build, Test와 배포 작업을 Repository 안의 Workflow File로 정의한다. GitHub의 `push`, Pull Request, Release 같은 Event가 발생하면 지정한 Runner에서 Job을 실행한다.

Workflow를 시작하는 방법은 두 가지이다.

- GitHub Repository의 **Actions** Tab에서 Starter Workflow를 선택한다.

- Repository의 `.github/workflows` Directory에 YAML File을 직접 작성한다.

Starter Workflow는 [actions/starter-workflows](https://github.com/actions/starter-workflows)에서 확인할 수 있고, 재사용 가능한 Action은 [GitHub Marketplace](https://github.com/marketplace?type=actions)에서 찾을 수 있다. Public Repository, Private Repository와 GitHub-hosted 또는 Self-hosted Runner에 따라 제공 범위와 과금 방식이 달라지므로 사용 시점의 공식 정책을 확인한다.

## 2 ) Event, Workflow, Job, Step과 Runner

---

GitHub Actions의 실행 단위는 다음 관계를 가진다.

{% include visuals/github-actions-execution-flow.html %}

| 구성 요소 | 역할 | 예시 |
|---|---|---|
| Event | Workflow를 시작하는 활동 | `push`, `pull_request`, 수동 실행, 일정 |
| Workflow | 하나 이상의 Job을 정의한 자동화 File | `.github/workflows/ci.yml` |
| Job | 하나의 Runner에서 실행되는 Step 묶음 | Build, Test, Package |
| Step | Job 안에서 순서대로 실행되는 최소 작업 단위 | Action 호출 또는 Shell 명령 실행 |
| Action | `uses`로 가져와 실행하는 재사용 가능한 작업 | Source Checkout, Runtime 설치 |
| Runner | Job을 실행하는 Virtual Machine, Physical Machine 또는 Container | `ubuntu-latest`, Self-hosted Runner |

하나의 Job에 있는 Step은 같은 Runner에서 작성 순서대로 실행되므로 앞 Step에서 만든 File과 설치 상태를 뒤 Step이 사용할 수 있다. 서로 다른 Job은 기본적으로 독립된 Runner에서 병렬 실행되며 File System을 자동으로 공유하지 않는다.

Job 실행 순서가 필요하면 `needs`를 사용한다.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  package:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: npm pack
```

`package` Job은 `test` Job이 성공한 뒤 시작한다. Job의 성공 또는 실패 상태뿐 아니라 각 Step의 실행 명령, 출력과 실패 위치도 GitHub Actions 화면에서 확인할 수 있다.

## 3 ) Workflow 기본 구조와 Trigger

---

Workflow File의 기본 구조는 `name`, `on`과 `jobs`이다.

```yaml
name: CI

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "run test"
```

| Key | 의미 |
|---|---|
| `name` | Actions 화면에 표시할 Workflow 이름 |
| `on` | Workflow를 시작할 Event와 조건 |
| `jobs` | 실행할 Job Map |
| `runs-on` | Job을 실행할 Runner 환경 |
| `steps` | 같은 Runner에서 순차 실행할 작업 목록 |
| `uses` | Repository에 공개된 Action 또는 Local Action 사용 |
| `run` | Runner의 Shell에서 명령 실행 |
| `with` | Action에 전달할 입력 값 |

### Code 변경 Event

`push`와 `pull_request`에 Branch와 Pull Request 활동 조건을 지정할 수 있다.

```yaml
on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
```

`create`와 `delete` Event는 Branch 또는 Tag가 생성되거나 삭제될 때 실행할 수 있다.

`pull_request_target`은 Pull Request의 Head가 아니라 Base Branch 문맥에서 실행되고 Base Repository의 권한과 Secret에 접근할 수 있다. 외부 Fork의 신뢰하지 않은 Code를 Checkout해 실행하는 Workflow에는 사용하지 않는다. 일반적인 Pull Request Build와 Test에는 `pull_request`가 안전한 기본 선택이다.

### 수동 실행과 외부 호출

| Event | 사용 시점 |
|---|---|
| `workflow_dispatch` | Actions 화면 또는 API에서 사용자가 직접 실행 |
| `repository_dispatch` | 외부 Application이나 Server가 GitHub API로 실행 요청 |
| `workflow_call` | 다른 Workflow가 현재 Workflow를 재사용 |

수동 실행 Button을 제공하려면 다음과 같이 작성한다.

```yaml
on:
  workflow_dispatch:
```

### 일정 실행

일정은 POSIX Cron 형식으로 작성한다. 기본 시간대는 UTC이며, 필요하면 IANA Time Zone 이름을 지정할 수 있다.

```yaml
on:
  schedule:
    - cron: "0 9 * * 1-5"
      timezone: "Asia/Seoul"
```

이 예시는 평일 Asia/Seoul 09:00에 실행된다. 예약 Workflow는 Default Branch의 최신 Commit을 사용한다.

Issue, Issue Comment, Release와 Watch 같은 GitHub 활동도 Event로 사용할 수 있다. 실제 Workflow에는 필요한 Trigger만 지정해야 불필요한 실행과 비용을 줄일 수 있다.

### Workflow 작성 중 값과 문법을 찾는 방법

Workflow에 사용할 수 있는 Key, Event와 내부 값은 한 문서에 모두 모여 있지 않다. 찾으려는 대상에 따라 다음 공식 문서를 사용한다.

| 확인할 대상 | 공식 문서 | 확인할 내용 |
|---|---|---|
| YAML 구조와 Key | [Workflow syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) | `on`, `permissions`, `jobs`, `needs`, `runs-on`, `steps` 등 |
| Trigger와 세부 동작 | [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) | `issues`, `pull_request`, `push`와 각 Event의 `types`, Filter, 주의 사항 |
| Expression에서 접근할 객체 | [Contexts reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts) | `github`, `env`, `vars`, `secrets`, `runner`, `job`, `steps`, `matrix`, `needs` 등 |
| Runner의 기본 환경 변수 | [Variables reference](https://docs.github.com/en/actions/reference/workflows-and-actions/variables) | `GITHUB_REPOSITORY`, `GITHUB_SHA`, `GITHUB_REF`, `RUNNER_OS` 등 |
| 조건식, 연산자와 함수 | [Evaluate expressions in workflows and actions](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions) | `if`, 비교 연산자, `contains`, `startsWith`, `toJSON`, 상태 확인 함수 등 |
| `uses` Action의 입력과 출력 | [GitHub Marketplace](https://github.com/marketplace?type=actions)와 해당 Action의 README | `with`에 전달할 입력, `steps.<id>.outputs`로 받을 출력, 지원 Version |

`on`, `jobs`와 `permissions`는 GitHub Actions 자체의 Workflow 문법이다. 반면 `with` 아래에서 사용할 수 있는 값은 호출하는 Action마다 다르다. 예를 들어 `actions/setup-node`의 `node-version`과 `cache`는 해당 Action의 README에서 확인해야 한다.

Event가 제공하는 값도 Trigger마다 다르다. `issues` Event로 실행된 Workflow에서는 `github.event.issue`를 사용할 수 있지만, `push` Event에는 같은 객체가 없다. Issue가 닫혔을 때 전달되는 값을 확인하는 최소 Workflow는 다음과 같다.

{% raw %}
```yaml
name: Inspect closed issue

on:
  issues:
    types: [closed]

permissions:
  contents: read
  issues: read

jobs:
  inspect:
    runs-on: ubuntu-latest
    steps:
      - name: Show selected event values
        env:
          EVENT_ACTION: ${{ github.event.action }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          ISSUE_URL: ${{ github.event.issue.html_url }}
          REPOSITORY: ${{ github.repository }}
        run: |
          echo "action=$EVENT_ACTION"
          echo "issue_number=$ISSUE_NUMBER"
          echo "issue_url=$ISSUE_URL"
          echo "repository=$REPOSITORY"
```
{% endraw %}

| 값 | 역할 |
|---|---|
| `github.event.action` | Event의 세부 동작이다. 이 예시에서는 `closed`이다. |
| `github.event.issue.number` | 닫힌 Issue의 번호이다. |
| `github.event.issue.html_url` | 닫힌 Issue의 Web URL이다. |
| `github.repository` | `owner/repository` 형식의 실행 대상 Repository이다. |

필요한 Property가 명확하지 않으면 [Triggering a workflow의 event information](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#using-event-information)과 연결된 Webhook Payload 문서를 확인한다. 임시 진단 단계에서는 `toJSON(github.event)`로 Event Payload를 확인할 수도 있다. Issue 본문과 사용자 입력 같은 신뢰할 수 없는 값이 포함될 수 있으므로 Payload를 명령으로 실행하거나 외부로 전달하지 않는다. `github` Context 전체에는 Token 같은 민감한 값이 포함될 수 있으므로 통째로 Log에 출력하지 않는다.

### Issue 종료 시 Project 상태를 Done으로 변경

Issue나 Pull Request가 닫힐 때 Project의 `Status`를 `Done`으로 바꾸는 작업은 별도의 Actions YAML을 작성하기 전에 [GitHub Projects의 내장 자동화](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations)를 사용한다. 새 Project에는 닫힌 Issue·Pull Request와 병합된 Pull Request의 상태를 `Done`으로 바꾸는 기본 Workflow가 활성화되어 있다.

설정은 Project의 **메뉴 → Workflows → Default workflows**에서 대상 Workflow를 선택하고, 변경할 `Status`를 `Done`으로 지정한 뒤 저장하여 활성화한다. 이 자동화는 Project에 들어 있는 Item의 상태를 변경한다. Issue를 Project에 넣는 과정도 자동화하려면 별도의 [Auto-add to project](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically) Workflow와 Filter를 설정한다.

내장 자동화로 표현할 수 없는 조건이나 사용자 정의 Field를 변경해야 한다면 [Automating Projects using Actions](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)와 [Projects GraphQL reference](https://docs.github.com/en/graphql/reference/projects#updateprojectv2itemfieldvalue)를 사용한다. 이 경우 Project ID, Item ID, Field ID와 선택 Option ID를 조회한 뒤 `updateProjectV2ItemFieldValue` Mutation을 호출한다. Repository 범위의 `GITHUB_TOKEN`은 Projects에 접근할 수 없으므로 Organization Project에는 GitHub App, User Project에는 필요한 Project 권한을 가진 Personal Access Token을 사용한다.

## 4 ) 가장 작은 Workflow 실행

---

실습용 Remote Repository를 만들고 Local Directory를 초기화한다.

```bash
mkdir githubaction-sample
cd githubaction-sample
git init
git branch -M main
```

확인용 File을 만든 뒤 Commit하고 자신의 Remote Repository URL을 연결한다.

```bash
touch README.md
git add .
git commit -m "Add GitHub Actions sample"
git remote add origin \
  https://github.com/<owner>/githubaction-sample.git
git push -u origin main
```

`<owner>`는 자신의 GitHub 계정이나 Organization 이름으로 바꾼다. `git remote -v`로 등록된 URL을 확인할 수 있다.

`.github/workflows/ci-example.yml`을 작성한다.

```bash
mkdir -p .github/workflows
```

```yaml
name: CI Example

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository code
        uses: actions/checkout@v7

      - name: Print one line
        run: echo "Hello GitHub Actions"

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Display Python version
        run: python --version
```

`actions/checkout`은 Runner에 Repository Source를 가져오고 `actions/setup-python`은 지정한 Python을 사용할 수 있도록 설정한다. `permissions: contents: read`는 Workflow Token에 Source를 읽는 최소 권한만 부여한다.

예시의 공식 Action Major Version은 2026년 9월 기준이다. Version 7 Action을 Self-hosted Runner에서 사용하려면 Runner Version이 `v2.327.1` 이상인지 확인한다. 장기간 유지하는 운영 Workflow에서는 Action Release Note를 확인하고, 공급망 변경을 엄격하게 제어해야 한다면 검증한 Full Commit SHA로 고정한다.

Workflow File을 Commit하고 Push한다.

```bash
git add .github/workflows/ci-example.yml
git commit -m "Add CI example workflow"
git push
```

GitHub Repository의 **Actions → CI Example**에서 실행 중인 Workflow와 각 Step의 Log를 확인한다.

## 5 ) Node.js와 Mocha Test 자동화

---

### Local Project 생성

Node.js Project를 만들고 Mocha를 Development Dependency로 설치한다.

```bash
mkdir nodetest
cd nodetest
npm init -y
npm install --save-dev mocha
```

| 명령 | 결과 |
|---|---|
| `npm init -y` | 기본값으로 `package.json` 생성 |
| `npm install --save-dev mocha` | Mocha를 개발용 Dependency에 추가하고 `package-lock.json` 생성 |

`test.spec.js`에 실제 Assertion이 있는 Test를 작성한다.

```javascript
const assert = require("node:assert/strict");

describe("Default Test Set", () => {
  it("adds two numbers", () => {
    assert.equal(1 + 1, 2);
  });

  it("compares text", () => {
    assert.equal("github".toUpperCase(), "GITHUB");
  });
});
```

`console.log`만 실행하면 Test가 실패 조건을 검증하지 못한다. `assert.equal`을 사용하면 실제 값이 기대값과 다를 때 Mocha가 실패 상태를 반환한다.

`package.json`의 `scripts`를 다음과 같이 설정한다.

```json
{
  "scripts": {
    "test": "mocha test.spec.js"
  }
}
```

Local에서 먼저 실행한다.

```bash
npm test
```

두 Test가 통과하고 Process 종료 Code가 `0`인지 확인한다. 실패하면 Mocha는 0이 아닌 종료 Code를 반환하고 GitHub Actions의 Step도 실패 처리된다.

### Git Repository 준비

`node_modules`는 설치 결과이므로 Commit하지 않는다. `.gitignore`에 추가하고 Source, Package Metadata와 Lockfile을 Commit한다.

```gitignore
node_modules/
```

```bash
git init
git branch -M main
git add .
git commit -m "Add Node.js tests"
git remote add origin https://github.com/<owner>/nodetest.git
git push -u origin main
```

### Node.js Workflow

`.github/workflows/nodetest.yml`을 작성한다.

```bash
mkdir -p .github/workflows
```

{% raw %}
```yaml
name: Node.js CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [24.x]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v7
        with:
          node-version: ${{ matrix.node-version }}
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build when a build script exists
        run: npm run build --if-present

      - name: Run tests
        run: npm test
```
{% endraw %}

`npm ci`는 `package-lock.json`의 정확한 Dependency Version을 사용해 깨끗하게 설치한다. 따라서 Lockfile을 Repository에 Commit해야 한다. `cache: npm`은 npm의 Download Cache를 재사용하지만 `node_modules` 자체를 Job 사이에 공유하지는 않는다.

Matrix에 Version을 추가하면 같은 Test Job을 여러 Node.js Version에서 실행할 수 있다.

{% raw %}
```yaml
strategy:
  matrix:
    node-version: [22.x, 24.x]
```
{% endraw %}

Matrix의 각 조합은 별도 Job으로 실행되므로 한 Version의 실패가 다른 Version의 Log와 섞이지 않는다.

## 6 ) 환경 변수, Variable과 Secret

---

Workflow는 GitHub가 제공하는 기본 환경 변수와 사용자가 정의한 Configuration을 사용할 수 있다.

| 종류 | 이름 또는 문법 | 용도 |
|---|---|---|
| 기본 환경 변수 | `GITHUB_*`, `RUNNER_*` | Repository, Commit, Workflow와 Runner 정보 |
| Workflow 환경 변수 | `env` | Workflow, Job 또는 Step 범위의 일반 설정 |
| Configuration Variable | `vars` Context | 환경별 공개 설정 값 |
| Secret | `secrets` Context | Token, Password와 인증 정보 |

기본 환경 변수는 Shell에서 직접 확인할 수 있다.

```yaml
- name: Show workflow context
  run: |
    echo "repository=$GITHUB_REPOSITORY"
    echo "sha=$GITHUB_SHA"
    echo "runner=$RUNNER_OS"
```

일반 환경 변수와 Repository Variable을 함께 사용할 수 있다.

{% raw %}
```yaml
env:
  APP_NAME: sample-api

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "$APP_NAME runs in $APP_ENV"
        env:
          APP_ENV: ${{ vars.APP_ENV }}
```
{% endraw %}

Password나 Access Token을 Workflow File에 직접 적지 않는다. Repository 또는 Environment의 Secret으로 등록하고 필요한 Step에서만 전달한다.

{% raw %}
```yaml
- name: Authenticate
  env:
    REGISTRY_TOKEN: ${{ secrets.REGISTRY_TOKEN }}
  run: ./scripts/login.sh
```
{% endraw %}

Secret은 Log에서 Masking되지만 변환하거나 조합한 값이 항상 안전하게 가려진다고 가정해서는 안 된다. Secret 자체를 `echo`하거나 Debug Log에 출력하지 않고, 외부 Fork에서 시작한 Workflow에 어떤 권한과 Secret이 제공되는지 확인한다.

## 7 ) Python, Flask와 Pytest 자동화

---

### Project와 Virtual Environment

Python Project Directory에서 Virtual Environment를 만들고 활성화한다.

```bash
mkdir python-ci-sample
cd python-ci-sample
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell에서는 다음 명령을 사용한다.

```powershell
.venv\Scripts\Activate.ps1
```

필요한 Package를 설치한다.

```bash
python -m pip install \
  flask requests beautifulsoup4 pymongo pytest
```

`app.py`는 MongoDB Host를 환경 변수로 받도록 작성한다. Host Computer에서 실행할 때 기본값은 `localhost`이고, Container Network에서 Service 이름이 `mongo`라면 `MONGO_HOST=mongo`를 전달할 수 있다.

```python
import os

from flask import Flask, render_template
from pymongo import MongoClient


app = Flask(__name__)
client = MongoClient(os.getenv("MONGO_HOST", "localhost"), 27017)
db = client.dbsparta


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
```

`templates/index.html`을 작성한다.

```html
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <title>Flask sample</title>
  </head>
  <body>
    <h3>Flask Web Application</h3>
  </body>
</html>
```

Application까지 Local에서 실행하려면 MongoDB가 필요하다. Docker를 사용할 경우 Project Directory의 `data`에 DB Data를 연결한다.

```bash
mkdir -p data
docker run \
  --name mongodb \
  -v "$PWD/data:/data/db" \
  -p 27017:27017 \
  -d mongo
docker ps --filter name=mongodb
```

| Option | 의미 |
|---|---|
| `--name mongodb` | Container 이름 지정 |
| `-v "$PWD/data:/data/db"` | Host Directory를 MongoDB Data Directory에 Mount |
| `-p 27017:27017` | Host와 Container의 MongoDB Port 연결 |
| `-d` | Background에서 Container 실행 |

`python app.py`를 실행한 뒤 `http://localhost:5000`에서 Page를 확인한다.

### 외부 환경에 의존하지 않는 Unit Test

`utils.py`에 작은 함수를 작성한다.

```python
def get_title():
    return "title"
```

`test_utils.py`에서 반환 값을 검증한다.

```python
from utils import get_title


def test_get_title():
    assert get_title() == "title"
```

Test를 실행한다.

```bash
pytest
```

이 Test는 Flask Server나 MongoDB를 사용하지 않는 Unit Test이다. 따라서 CI Runner에 MongoDB Container를 시작하지 않아도 된다. DB 연결까지 검증하는 Integration Test를 추가한다면 Workflow에 MongoDB Service Container와 준비 상태 확인이 필요하다.

Virtual Environment에서 실제로 설치한 Package Version을 `requirements.txt`에 기록한다.

```bash
python -m pip freeze > requirements.txt
```

`.gitignore`에는 Local 환경과 실행 중 생긴 File을 추가한다.

```gitignore
.venv/
__pycache__/
.pytest_cache/
data/
```

### Pytest Workflow

`.github/workflows/ci-test.yml`을 작성한다.

```bash
mkdir -p .github/workflows
```

```yaml
name: Python CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run tests
        run: pytest
```

Workflow가 실행하는 것은 Dependency 설치와 Pytest까지이다. Container Image를 Build하거나 Registry에 Push하는 Step은 정의되어 있지 않다.

Workflow와 Project File을 Remote Repository에 Push한다.

```bash
git init
git branch -M main
git add .
git commit -m "Add Python CI workflow"
git remote add origin \
  https://github.com/<owner>/python-ci-sample.git
git push -u origin main
```

Push가 끝나면 Actions Tab에서 `Python CI` Workflow의 `Install dependencies`와 `Run tests` Step을 확인한다.

## 8 ) Flask Application을 Image로 만들기

---

Pytest가 통과한 Source를 같은 실행 환경으로 전달하려면 Container Image로 Package할 수 있다. 다음 `Dockerfile`은 Python 3.13 기반 Image에 Dependency와 Application Source를 넣고 Flask Server를 실행한다.

```dockerfile
FROM python:3.13-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
```

Flask는 `app.py`를 기본 Application Module로 탐색한다. File 이름이 다르면 `FLASK_APP` 환경 변수를 지정해야 한다. Image에 Local Virtual Environment와 MongoDB Data가 들어가지 않도록 `.dockerignore`도 작성한다.

```dockerignore
.git/
.github/
.venv/
__pycache__/
.pytest_cache/
data/
```

Workflow에 연결하기 전에 Local에서 Image를 Build하고 Container가 시작되는지 확인한다.

```bash
docker build -t flaskweb:local .
docker run --rm -d \
  --name flaskweb \
  -p 5000:5000 \
  flaskweb:local
docker ps --filter name=flaskweb
curl http://localhost:5000
docker stop flaskweb
```

`docker build`가 성공해도 Application Process가 정상적으로 시작된다는 보장은 없다. `docker ps`, HTTP 요청과 `docker logs flaskweb`을 함께 사용해 Build 결과와 실행 결과를 구분해서 확인한다.

## 9 ) Test 성공 후 Docker Hub에 Push

---

[Container Image Registry](/cloud-native-41-container-image-registry/)에서 정리한 Docker Hub Repository를 생성하고, Docker Hub Personal Access Token(PAT)을 준비한다. 계정 Password나 Token을 Workflow File에 직접 작성하면 Git 이력과 Log를 통해 노출될 수 있으므로 Repository Secret으로 등록한다.

GitHub Repository의 **Settings → Secrets and variables → Actions → New repository secret**에서 다음 값을 만든다.

| Secret | 저장할 값 | 사용 목적 |
|---|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub 계정 이름 | Registry 로그인과 Image 이름 구성 |
| `DOCKERHUB_TOKEN` | Docker Hub PAT | Password 대신 Registry 인증 |
| `DOCKERHUB_REPO` | 생성한 Repository 이름 | Push할 Image Repository 지정 |

실제 Token을 Source, Workflow, 화면 캡처 또는 문서에 기록하지 않는다. 이미 노출한 Token은 삭제만으로 안전해지지 않으므로 Docker Hub에서 폐기하고 새 Token을 발급한다.

기존 `.github/workflows/ci-test.yml`을 다음과 같이 확장한다.

{% raw %}
```yaml
name: Python CI and Docker Image

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run tests
        run: pytest

  build-and-push:
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Log in to Docker Hub
        uses: docker/login-action@v4
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build image
        env:
          IMAGE: ${{ secrets.DOCKERHUB_USERNAME }}/${{ secrets.DOCKERHUB_REPO }}
        run: docker build -t "$IMAGE:${GITHUB_SHA}" -t "$IMAGE:latest" .

      - name: Push image
        env:
          IMAGE: ${{ secrets.DOCKERHUB_USERNAME }}/${{ secrets.DOCKERHUB_REPO }}
        run: |
          docker push "$IMAGE:${GITHUB_SHA}"
          docker push "$IMAGE:latest"
```
{% endraw %}

`needs: test`는 Test가 성공해야 `build-and-push` Job을 시작한다. `if: github.event_name == 'push'`는 Pull Request 검증에서는 Test만 수행하고 `main` Branch에 실제 Push된 실행에서만 Registry를 변경하도록 제한한다.

Image에는 두 Tag를 붙인다.

| Tag | 역할 |
|---|---|
| `${GITHUB_SHA}` | 어떤 Commit으로 만든 Image인지 추적 |
| `latest` | 가장 최근에 Push한 Image를 가리키는 편의용 Tag |

배포 자동화에서는 변경될 수 있는 `latest`보다 Commit SHA처럼 불변에 가까운 Tag를 지정하는 편이 재현과 Rollback에 유리하다. Workflow를 Push한 뒤 Actions 화면에서 `test`, `build-and-push` 순서와 각 Step의 Log를 확인하고 Docker Hub Repository에서 두 Tag가 생성됐는지 확인한다.

공식 입력 값과 권장 인증 방식은 [docker/login-action](https://github.com/docker/login-action)과 [Docker Hub access token](https://docs.docker.com/security/access-tokens/) 문서에서 확인한다.

## 10 ) SSH로 배포 Server의 Container 교체

---

`build-and-push` Job이 Commit SHA Tag Image를 Docker Hub에 Push하면 별도의 `deploy` Job이 SSH로 배포 Server에 접속해 같은 Tag를 실행할 수 있다. Runner가 Application File을 직접 복사하는 방식이 아니라, 배포 Server가 Registry에서 검증된 Image를 Pull하는 구조이다.

### 배포 Server 준비

배포 Server에는 Docker를 설치하고 SSH 접속이 가능해야 한다. Application Port `5000`을 외부에 직접 공개할지, Reverse Proxy 뒤에서만 사용할지는 Network 정책에 따라 결정한다.

Server에서 Docker 동작을 먼저 확인한다.

```bash
sudo docker version
sudo docker run --rm hello-world
```

GitHub Repository의 **Settings → Secrets and variables → Actions**에 다음 값을 등록한다.

| Secret | 저장할 값 | 사용 범위 |
|---|---|---|
| `EC2_HOST` | 배포 Server의 DNS 이름 또는 IP | SSH 접속 대상 |
| `EC2_USERNAME` | SSH Login 계정 | SSH 인증 |
| `EC2_SSH_KEY` | 배포 전용 Private Key 전체 내용 | SSH 인증 |
| `EC2_HOST_FINGERPRINT` | SSH Host Public Key Fingerprint | 접속 대상 검증 |
| `DOCKERHUB_USERNAME` | Docker Hub 계정 | Private Image Login |
| `DOCKERHUB_TOKEN` | Docker Hub PAT | Private Image Pull |
| `DOCKERHUB_REPO` | Docker Hub Repository 이름 | Image 경로 구성 |

배포 전용 SSH Key는 개인용 Key와 분리하고, Server의 `authorized_keys`에는 필요한 계정에만 등록한다. `EC2_HOST_FINGERPRINT`를 사용하면 DNS나 IP만 믿지 않고 접속한 Server의 Host Key도 검증할 수 있다.

### Deploy Job 연결

기존 Workflow의 `jobs` 아래에 `deploy` Job을 추가한다. `needs: build-and-push`에 의해 Test와 Image Push가 모두 성공한 뒤에만 시작한다.

{% raw %}
```yaml
  deploy:
    needs: build-and-push
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - name: Deploy commit image over SSH
        uses: appleboy/ssh-action@v1
        env:
          IMAGE: ${{ secrets.DOCKERHUB_USERNAME }}/${{ secrets.DOCKERHUB_REPO }}
          IMAGE_TAG: ${{ github.sha }}
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
          DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          fingerprint: ${{ secrets.EC2_HOST_FINGERPRINT }}
          envs: IMAGE,IMAGE_TAG,DOCKERHUB_USERNAME,DOCKERHUB_TOKEN
          timeout: 30s
          command_timeout: 5m
          script: |
            set -eu

            echo "$DOCKERHUB_TOKEN" \
              | sudo docker login \
                  --username "$DOCKERHUB_USERNAME" \
                  --password-stdin

            sudo docker pull "$IMAGE:$IMAGE_TAG"
            sudo docker rm --force flaskweb 2>/dev/null || true

            sudo docker run -d \
              --name flaskweb \
              --restart unless-stopped \
              -p 5000:5000 \
              "$IMAGE:$IMAGE_TAG"

            for attempt in $(seq 1 15); do
              if curl --fail --silent http://127.0.0.1:5000/ >/dev/null; then
                sudo docker ps --filter name=flaskweb
                sudo docker image prune --force
                exit 0
              fi
              sleep 2
            done

            sudo docker logs --tail 100 flaskweb
            exit 1
```
{% endraw %}

| 설정 | 역할 |
|---|---|
| `needs: build-and-push` | Registry Push 성공 후 배포 시작 |
| `if` | Pull Request에서는 배포하지 않고 `main` Push에서만 실행 |
| GitHub Commit SHA | Workflow를 시작한 Commit과 배포 Image를 일치시킴 |
| `fingerprint` | SSH Server Host Key 검증 |
| `--restart unless-stopped` | Docker Daemon 재시작 후 Container 복구 |
| HTTP 반복 확인 | Process 시작뿐 아니라 실제 응답 가능 상태 확인 |

Public Docker Hub Image라면 원격 Server의 Registry Login을 생략할 수 있다. Private Image에서는 Token을 SSH Action의 `envs`로 필요한 Session에만 전달하고, Script에서 출력하지 않는다.

이 방식은 기존 Container를 제거한 다음 새 Container를 시작하므로 짧은 중단이 발생한다. 무중단 교체가 필요하면 Reverse Proxy, 복수 Instance, Blue-Green 또는 Kubernetes Rolling Update 같은 별도 배포 전략이 필요하다.

### 배포 결과와 Log 확인

배포 Server에서 실행 상태와 실제 Tag를 확인한다.

{% raw %}
```bash
sudo docker ps --filter name=flaskweb
sudo docker inspect flaskweb --format '{{.Config.Image}}'
sudo docker logs --tail 100 flaskweb
curl --fail http://127.0.0.1:5000/
```
{% endraw %}

`docker inspect` 결과가 Workflow Run의 Commit SHA Tag와 같아야 Source, Image와 Runtime의 연결을 추적할 수 있다.

### 이전 Image로 Rollback

문제가 발생하면 이전에 정상 동작한 Commit SHA를 지정해 같은 교체 절차를 수행한다.

```bash
IMAGE='<dockerhub-username>/<repository>'
PREVIOUS_TAG='<previous-commit-sha>'

sudo docker pull "$IMAGE:$PREVIOUS_TAG"
sudo docker rm --force flaskweb
sudo docker run -d \
  --name flaskweb \
  --restart unless-stopped \
  -p 5000:5000 \
  "$IMAGE:$PREVIOUS_TAG"
```

`latest`는 새로운 Push에 따라 가리키는 Image가 바뀌므로 Rollback 기준으로 적합하지 않다. 배포와 복구에는 변경되지 않는 Commit SHA Tag를 사용한다.

## 11 ) Actions 화면과 Log 확인

---

Workflow를 Push한 뒤 다음 순서로 결과를 확인한다.

1. GitHub Repository의 **Actions** Tab을 연다.

2. 왼쪽에서 Workflow 이름을 선택한다.

3. Commit에 대응하는 Workflow Run을 선택한다.

4. 실패하거나 확인할 Job을 선택한다.

5. Step을 펼쳐 실행 명령, 표준 출력과 Error Message를 확인한다.

| 상태 | 우선 확인할 항목 |
|---|---|
| Workflow가 시작되지 않음 | Workflow File 경로, YAML 문법, `on` Branch 조건 |
| Checkout 실패 | Repository 권한, `permissions`, Submodule 설정 |
| `npm ci` 실패 | `package-lock.json` 누락 또는 `package.json`과 불일치 |
| Python Package 설치 실패 | `requirements.txt`, Python Version, Package 지원 범위 |
| Test 실패 | 실패한 Step의 Log, Assertion, Local과 CI 환경 차이 |
| Secret을 찾지 못함 | Secret 이름, Repository·Environment 범위, Fork Event 정책 |

실패한 Step 이름이 구체적이면 전체 Log를 훑지 않고도 `Install dependencies`, `Run tests`처럼 문제 범위를 빠르게 좁힐 수 있다. 하나의 Job이 너무 많은 책임을 가지면 독립적으로 재실행하거나 원인을 분리하기 어려우므로 Build, Test와 Package 경계를 기준으로 나눈다.

> **최종 정리**
> - Event가 Workflow를 시작하고 Job은 Runner에서 실행되며, Job 내부 Step은 작성 순서대로 실행된다.
>
> - 서로 다른 Job은 실행 환경을 자동으로 공유하지 않고, 순서가 필요하면 `needs`로 의존성을 정의한다.
>
> - Node.js CI는 Lockfile과 `npm ci`를 사용하고, Python CI는 Virtual Environment에서 확정한 Dependency와 Pytest를 사용한다.
>
> - Variable과 Secret은 역할을 구분하고 인증 정보를 Workflow File이나 Log에 직접 노출하지 않는다.
>
> - Workflow 작성 중에는 Syntax, Event, Context, Variable, Expression과 Action별 README를 구분하여 필요한 값을 찾는다.
>
> - Issue 종료에 따른 Project 상태 변경은 내장 자동화를 우선 사용하고, 복잡한 조건과 사용자 정의 Field 변경에는 Actions와 GraphQL API를 사용한다.
>
> - Python Test가 성공한 뒤 `needs`로 Image Build를 연결하고, Docker Hub 인증 정보는 Repository Secret으로 주입한다.
>
> - Image에는 Commit SHA Tag를 함께 붙여 Source와 배포 Artifact의 관계를 추적한다.
>
> - SSH 배포는 Host Key를 검증하고 Commit SHA Tag Image로 대상 Container만 교체하며, 상태 확인과 이전 Tag Rollback 절차를 함께 둔다.
>
> - Actions 화면에서는 Workflow, Job과 Step 단위로 상태와 Log를 확인할 수 있다.

다음 글인 [Docker로 GitLab CE 설치와 운영 준비](/cloud-native-54-gitlab-docker-installation/)에서는 GitLab Data를 Host Volume에 유지하면서 Docker Container로 Git Server를 구성한다.
