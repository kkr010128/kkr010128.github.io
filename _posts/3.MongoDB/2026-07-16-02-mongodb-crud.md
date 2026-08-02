---
title: MongoDB CRUD
description: MongoDB 데이터 삽입, 조회, 수정, 삭제 및 다양한 쿼리 연산자 정리
date: 2026-07-16
series: MongoDB
tags:
  - MongoDB
  - AutoEverSW
---

## 데이터 삽입
---
- document의 생성은 단일 Collections을 대상으로 수행
- 단일 document level에서 원자적으로 실행(독립적으로 수행되고 작업 도중에는 다른 작업이 끼어들 수 없음) → 원자적
- 데이터를 삽입할 때 `_id`라는 key의 값을 설정하지 않으면 MongoDB가 알아서 생성해서 대입하는데 이 key는 primary key이고 인덱스가 설정됨
- 삽입하는 함수는 insert, insertOne, insertMany, save가 있음
- insert는 deprecated
	- save `_id`가 존재하는 경우 수정을 하고 insert는 `_id`가 존재하면 에러를 발생
- insert의 두 번째 매개변수는 멀티스레드 사용 여부임
	- {ordered:true 또는 false}로 설정함
	- order가 true일 경우 단일스레드, false면 멀티스레드

```sh
db.컬렉션이름.insert({데이터})
→ db.users.insert({name:"Adam", age:25, gender:"male"})

# 확인
db.users.find()

# 배열 삽입
db.users.insert([{name:"rusia"}, {name:"hunt"}])
→ 최상위에 배열은 올 수 없음
→ 배열을 삽입하면 데이터를 나누어 삽입함

# 확인
db.users.find()

# sample 컬렉션을 생성하는데 name의 값을 중복없이 저장하도록 생성
db.sample.createIndex({name:1},{unique:true})

# 데이터 삽입
db.sample.insert({name:"park"})

# 여러 개의 데이터 동시에 삽입
db.sample.insert({[name:"park"}, {name:"lee"}, {name:"choi"}])
# park이 중복되어 에러 발생, 현재는 싱글스레드 형태로 삽입하므로 park이 에러라면
# 뒤의 2개의 데이터는 삽입되지 않음

db.sample.find()

# sample 컬렉션 삭제
db.sample.drop()



# 모든 데이터 동시 삽입 - 멀티스레드
db.sample.insert([{name:"park"}, {name:"lee"}, {name:"choi"}], {ordered:false})
# 중복 에러가 발생하더라도 나머지 데이터는 삽입됨
```

### ObjectId
- MongoDB에서는 데이터를 삽입할 때 `_id` 항목의 값을 설정하지 않으면 Mongo DB가 `ObjectId`라는 자료형으로 일련번호를 만들어서 자동 삽입함
- 12 byte로 구성되어 있고, new ObjectId()를 이용해 직접 생성 가능
- `var newId = new ObjectId`
- `db.sample.insert({_id:newId, name:"user01"})`

### insertOne과 insertMany
- insert 함수는 deprecated
- 하나의 데이터를 삽입할 때는 insertOne 그리고 여러 개의 데이터를 삽입할 때는 insertMany를 사용하도록 권장
- `db.sample.insertOne({name:"karroid",password:"1111"})`
- `db.sample.insertMany([{name:"karroid",password:"1111"},{name:"karroid",password:"1111"}])`

### JavaScript의 반복문 사용 가능
```js
var num = 1
for(var i = 0; i < 3; i++) {db.sample.insertOne({name:"user" + i, score : num})}

```

## 데이터 조회
---
### 개요
- 조회를 할 때는 단일 Collections에서 동작
- cursor: 데이터를 조회할 때 결과 셋을 커서라고 부르는 반복적인 객체를 반환

### find()
- `find(<query>, <projection>`)`
- db.sample.find() → Document 전체 조회

- **조건 검색**
	- find({컬럼이름:값• • • })
	- name이 user1인 데이터 조회 → db.sample.find({name:"user1"})
	- 여러개의 컬럼을 나열하면 AND

```sh
db.containerBox.insertMany([
{name:'bear', weight:60, category:'animal'},
{name:'bear', weight:10, category:'animal'},
{name:'cat', weight:2, category:'animal'},
{name:'phone', weight:1, category:'electronic'},
])


# → db.containerBox.find({name:'bear', category:'animal'})
```


### 특정 컬럼 추출
- 두 번째 매개변수로 컬럼 이름과 true or false(1,0)으로 설정하면 되는데 true면 조회가 되고 false면 조회가 되지 않음
```sh
# _id는 false를 설정하지 않으면 기본적으로 조회가 됨
db.containerBox.find({}, {name:ture})

# _id와 name을 제외하고 조회
db.containerBox.find({}, {_id:false, name:false})
```


### 비교 오퍼레이터
- **$eq:** equal
- **$ne:** not equal
- **$gt:** greater than
- **$gte:** greater than or equals
- **$lt:** less than
- **$lte:** less than or equals
- **$in:** 배열 안에 속한 값

- height 값이 175에서 180 사이
	- {height:{$gte: 175, $lte: 180}}
```sh
# inventory Collection에서 item 컬럼의 값이 hello인 데이터 조회
→ db.inventory.find({item:{$eq: 'hello'}})

# inventory Collection에서 tags 컬럼의 값이 blank나 blue인 데이터 조회
→ db.inventory.find({tags:{$in: ['blank', 'blue']})

# inventory Collection에서 tags 컬럼의 값이 blank나 blue가 아닌 데이터 조회
→ db.inventory.find({tags:{$in: ['blank', 'blue']})
```


### 논리 결합 오퍼레이터
- **$not:**
- **$or:**
- **$and:**
- **$nor:** 주어진 조건 중 하나라도 만족하지 않는 데이터 조회
```sh
# inventory Collection에서 qty가 2보다 크지 않은 데이터 조회
→ db.inventory.find({qty:{$not:{$gt:2}}})
# inventory Collection에서 qty가 100보다 크거나 qty가 10보다 작은 데이터 조회
→ db.inventory.find({$or:[{qty:{$gt:100}}, {qty:{$gt:10}}]})
# inventory Collection에서 price의 값이 0.99 또는 1.99이고 sale 필드의 값이 true 또는 qty의 값이 20 미만인 데이터 조회
→ db.inventory.find({$and:[$or:[{price:0.99},{price:1.99}]]})
```

### null 조회
- 실제 값이 null인 데이터도 조회가 되고 key가 없어도 null로 간주
```sh
db.temp.insert({y:null})
db.temp.insert({y:1})

db.temp.find({y:null})
db.temp.find({x:null})
```
### 정규 표현식
- $regex를 사용
- {컬럼이름: {$regex:/pattern/, $options: '옵션'}}
- option
	- i → 대소문자 무시
	- m → 정규식에 ^를 사용할 때 \n이 있으면 무시
	- x → 정규식 안에 있는 모든 공백을 무시
	- s → .을 사용할 때 \n을 포함해서 매치
	
	db.users.insert((name:"paulo")) db.users.insert fname:"patric"))
	db.users.insert(name "pedro"))
	a가 포함된 데이터 조회 db.users.find((name:/a/))
	pa로 시작하는 데이터를 조회 db.users.find{name:/^pa/))
	l로 끝나는 데이터를 조회 db.users.find((name:/lo$/))
	


db.users.insert({name:"paulo"})
db.users.insert({name:"patric"})
db.users.insert({name:"pedro"})

### 배열 연산자
- $all → 순서와 상관 없이 배열 안의 요소가 모두 포함되면 선택
- $elemMatch → 조건과 맞는 배열 요소를 가진 Document를 선택
- $size → 배열의 크기가 같은 Document를 선택

*MongoDB는 RDBMS와 달리 배열을 넣을 수 있음
```sh
db.inventory.insertMany([
{item:"journal", qty:25, tags:["blank", "red"]},
{item:"notebook", qty:50, tags:["red", "blank"]},
{item:"paper", qty:100, tags:[]},
{item:"planner", qty:75, tags:["blank", "red"]},
{item:"postcard", qty:45, tags:["blue"]}
]);

#tags에 red가 포함된 데이터 조회
db.inventory.find({tags:"red"},{_id:false})

# tags에 red와 blank가 포함된 데이터를 조회
db.inventory.find({tags:["red", "blank"]},{_id:false})

# tags에 red가 포함된 데이터 중 배열에서 일치하는 데이터만 조회
db.inventory.find({tags:"red"}, {tags.$true})

# users Collection에서 scores가 80보다 크고 90보다 작은 데이터가 1개라도 포함되어있으면 조회
db.users.find({scores:{$elemMatch:{$gt:80, $lt:90}}})

# tags에 순서 상관 없이 red와 blank를 포함하는 데이터 조회
db.inventory.find({tags:{$all: ["red", "blank"]}}, {_id:false})

# tags에 값이 없는 데이터 조회
db.inventory.find({tags:{$size: 0}}, {_id:false})
```

- 필드 소유 여부: $exists 에 true를 설정하면 필드가 있는 경우에만 조건을 확인
	- `db.inventory.find(qty:{$exists:true, $nin: [5,15]}})`

### $where
- 일반적인 쿼리 연산자로 표현하기 어려운 복잡한 논리를 js 표현식이나 함수를 통해 실행할 대 사용
- 데이터베이스 내에서 js 코드를 돌려 문서를 필터링


### Sub Document Field Serching Query
- RDBMS는 컬럼에 배열이나 다른 데이터를 삽입하는 것이 안 되므로 이러한 쿼리가 존재하지 않음
- db.users.insert({name:"matt", contact:{type:"office", phone:"031-0000-0000"}});
- 조회 시에는 전체 조회 가능 하고 특정 필드 조회할 때는 " **.** " 이용
- db.users.find({contact:{type:"office", phone:"031-0000-0000}});
- db.usersfind({"contact.type":"office"});

### limit( ) - 개수 제한 함수
- db.inventory.find().limit(3)

### findOne( ) - 한 개만 검색


### skip( ) - 데이터를 건너 뜀


### sort( ) - 정렬
- 컬럼 이름을 기재하고 1을 설정하면 오름차순이고 -1을 설정하면 내림차순
- `db.inventory.find().sort({qty:1})`

### cursor
- 쿼리 결과에 대한 포인터로 find 함수를 호출하면 결과로 document를 직접 반환하지 않고 커서를 반환
- 커서에는 hasNext()라는 함수가 존재하는데 다음 데이터 존재 여부를 리턴하고 next는 다음 데이터를 리턴

### 쿼리의 성능 측정
- find( ) 를 호출하고 연달아서 explain("executionStats")을 호출하면 쿼리 계획을 확인할 수 있음
- db.inventory.find({qty:{$gte:30, $lte:90}}).explain("excutionStats")

### Index 설정
- `createIndex({"필드이름":1})`



## 데이터 집계
---
### 개요
- 저장되어 있는 정보에 다른 정보를 합해서 출력하거나 그룹화를 통해서 다른 형태로 정보를 생성해서 리턴하는 작업
- 집계 방법 

|       | 데이터를 가져와서 애플리케이션에서 수행 | Map-Reduce | Pipeline 활용 |
| ----- | --------------------- | ---------- | ----------- |
| 자유도   | 좋음                    | 좋음         | 나쁨          |
| 처리 속도 | 가장 느림                 | 보통         | 가장 좋음       |

### 기본 형식
```
db.컬렉션.mapReduce(map, reduce, {
out:<collection>,
query: <document>,
sort: <document>,
limit <number>,
finalize: <function>,
scope: <document>,
isMode: <boolean>,
verbose: <boolean>,
})
```
- 동작 순서
	- query(필터링) → sort(정렬) → limit(개수 제한) → Map 함수 수행 → 그룹화 → Reduce 함수 적용 → finalizer 함수 → out

- **map 함수**
```
var mapper = function() {
emit(this.rating, this.user, id)
}
```

- reduce 함수
```
var reducer = function(key, value){return values.length}
```

- 수행
```
db.rating.mapReduce(mapper, reducer, {out:{inline:1}})
```

### 집계 파이프라인
- 데이터 개수는 countDocuments( )
- db.products.countDocuments( );

- 중복 제거는 distict("필드 이름")
- db.products.distinct('manufacture')

- aggregate( )
- $group 으로 그룹화 할 항목을 설정
- $sum, max, min, avg, first, last, push, addToSet 등의 집계함수 설정

- products에서 manufacture 별로 price의 합계
- `db.products.aggregate([{$group:{_id:{"maker":"$manufacture"}, sum_prices:{$sum:"$price"}}}])`

- 세부 그룹화
- db.product



## 데이터 수정 및 삭제
---
### 갱신을 위한 함수
- update( )
- updateOne( )
- updateMany( )
- replaceOne( )

```bash
db.collection이름.replaceOne(
<query>,
<replacement - 수정할 내용>
{
	upsert: <boolean>,
	writeConcern: <document>,
	collation: <document>
})

db.user.replaceOne(
{name: "matt"},
{username:"karoid", status:"sleep", points:100, password:2222}
);
```