---
title: Kafka를 활용한 CQRS 구현
description: Spring Boot, MySQL, MongoDB와 Kafka를 이용하여 쓰기와 읽기 모델을 분리한 CQRS 구조 구현
date: 2026-08-12
series: CloudNative
tags:
  - CloudNative
  - AutoEverSW
---
## 1 ) Spring Boot 기반 CQRS 구현
---

이번 실습에서는 CQRS (Command Query Responsibility Segregation)의 읽기와 쓰기 책임을 실제 애플리케이션으로 분리한다.

쓰기 프로젝트에서는 **Spring Boot와 MySQL**을 이용하여 데이터를 저장하고, 읽기 프로젝트에서는 **Spring Boot와 MongoDB**를 이용하여 데이터를 조회한다.

최종적으로 Kafka를 이용하여 두 프로젝트 사이의 데이터 변경 사항을 전달하는 구조로 확장한다.

```text
                Command
                   ↓
          Spring Boot Write
                   ↓
                 MySQL
                   ↓
                 Kafka
                   ↓
          Spring Boot Read
                   ↓
                MongoDB
                   ↓
                 Query
````

현재 강의 내용에서는 Write Project와 Read Project의 기본 구현까지 진행하였다. Kafka를 이용하여 두 프로젝트를 연결하는 부분은 이후 과정에서 구현한다.

### **실습 환경**

실습을 위해 다음 환경을 준비한다.

|**구성 요소**|**역할**|
|---|---|
|Java|Spring Boot 애플리케이션 실행|
|IntelliJ IDEA|Spring Boot 프로젝트 개발|
|Docker|Kafka 및 데이터베이스 실행 환경|
|MySQL|Write Database|
|MongoDB|Read Database|
|Kafka|Write와 Read 영역 사이의 Message 전달|
|Git|Source Code 버전 관리|

## 2 ) **Write Project**

---

Write Project는 CQRS에서 **Command 영역**을 담당한다.

사용자로부터 도서 정보를 전달받아 비즈니스 로직을 수행하고 MySQL에 데이터를 저장한다.

```text
Client
  ↓
POST /cqrs/book
  ↓
BookController
  ↓
BookService
  ↓
BookRepository
  ↓
MySQL
```

### **프로젝트 생성**

다음 의존성을 포함하여 Spring Boot 프로젝트를 생성한다.

- Spring Boot DevTools
- Lombok
- Spring Web
- Spring Data JPA
- MySQL Driver
- Kafka

### **application.yml 설정**

Write Project는 `7000` 포트를 사용하고 MySQL에 연결한다.

```yaml
server:
  port: 7000

spring:
  application:
    name: Write

  datasource:
    url: jdbc:mysql://localhost:3306/mysql
    driver-class-name: com.mysql.cj.jdbc.Driver
    username: root
    password: wnddkd

  jpa:
    hibernate:
      ddl-auto: update
    properties:
      hibernate:
        format_sql: true
        show_sql: true

logging:
  level:
    org.hibernate.type.description.sql: trace
```

### **Book Entity**

`Book`은 MySQL의 `book` 테이블과 연결되는 Entity이다.

```java
import jakarta.persistence.*;
import lombok.*;

import java.util.Date;

@Entity
@Table(name = "book")
@ToString
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class Book {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long bid;

    @Column(length = 50, nullable = false)
    private String title;

    @Column(length = 50, nullable = false)
    private String author;

    @Column(length = 50, nullable = false)
    private String category;

    @Column
    private int pages;

    @Column
    private int price;

    @Column
    private Date published_date;

    @Column(length = 50, nullable = false)
    private String description;
}
```

### **BookDTO**

DTO (Data Transfer Object)는 계층 사이에서 데이터를 전달하기 위해 사용하는 객체이다.

클라이언트가 전달한 도서 정보를 `BookDTO`를 통해 전달받는다.

```java
import lombok.Data;

@Data
public class BookDTO {

    private String title;
    private String author;
    private String category;
    private int pages;
    private int price;
    private String published_date;
    private String description;
}
```

### **BookRepository**

`BookRepository`는 Spring Data JPA의 `JpaRepository`를 상속하여 `Book` Entity의 데이터베이스 작업을 담당한다.

```java
import org.springframework.data.jpa.repository.JpaRepository;

public interface BookRepository extends JpaRepository<Book, Long> {
}
```

### **BookService**

`BookService`에서는 전달받은 `BookDTO`를 `Book` Entity로 변환한 뒤 MySQL에 저장한다.

`published_date`는 문자열로 전달되므로 `SimpleDateFormat`을 이용하여 `Date`로 변환한다.

```java
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

@Service
@RequiredArgsConstructor
public class BookService {

    private final BookRepository bookRepository;

    public void saveBook(BookDTO bookDTO) {
        try {
            SimpleDateFormat formatter =
                    new SimpleDateFormat("yyyy-MM-dd", Locale.ENGLISH);

            Date published_date =
                    formatter.parse(bookDTO.getPublished_date());

            Book book = Book.builder()
                    .title(bookDTO.getTitle())
                    .author(bookDTO.getAuthor())
                    .category(bookDTO.getCategory())
                    .pages(bookDTO.getPages())
                    .price(bookDTO.getPrice())
                    .published_date(published_date)
                    .description(bookDTO.getDescription())
                    .build();

            bookRepository.save(book);

        } catch (Exception e) {
            System.out.println(e.getMessage());
        }
    }
}
```

처리 흐름은 다음과 같다.

```text
BookDTO
   ↓
published_date 변환
   ↓
Book Entity 생성
   ↓
BookRepository.save()
   ↓
MySQL
```

### **BookController**

`BookController`는 사용자의 HTTP 요청을 처리한다.

```java
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
public class BookController {

    private final BookService bookService;

    @GetMapping("/")
    public String index() {
        return "homepage";
    }

    @GetMapping("/health")
    public String healthCheck() {
        return "success";
    }

    @PostMapping("/cqrs/book")
    public String saveBook(@RequestBody BookDTO bookDTO) {
        bookService.saveBook(bookDTO);
        return "success";
    }
}
```

각 Endpoint의 역할은 다음과 같다.

|**Method**|**Endpoint**|**역할**|
|---|---|---|
|GET|`/`|서버 동작 확인|
|GET|`/health`|Health Check|
|POST|`/cqrs/book`|도서 데이터 저장|

### **Write Project 테스트**

웹 서버를 실행한 뒤 다음 주소로 접근하여 서버가 실행되는지 확인한다.

```text
localhost:7000
```

이후 Postman을 이용하여 REST API에 데이터를 전송하고 MySQL에 정상적으로 저장되는지 확인한다.

```text
Postman
   ↓
POST /cqrs/book
   ↓
BookController
   ↓
BookService
   ↓
BookRepository
   ↓
MySQL
```

## 3 ) **Read Project**

---

Read Project는 CQRS에서 **Query 영역**을 담당한다.

Write Project가 MySQL을 사용한 것과 달리 Read Project에서는 MongoDB를 사용한다.

```text
Client
  ↓
GET /cqrs/book
  ↓
BookController
  ↓
MongoDB
  ↓
조회 결과 반환
```

### **프로젝트 생성**

다음 의존성을 포함하여 Spring Boot 프로젝트를 생성한다.

- Spring Boot DevTools
- Lombok
- Spring Web
- Spring Data JPA
- Spring Data MongoDB
- Kafka

### **BookController**

Read Project에서는 `/cqrs/book` 요청이 들어오면 MongoDB의 `books` Collection에서 데이터를 조회한다.

```java
import com.mongodb.client.*;
import lombok.RequiredArgsConstructor;
import org.bson.Document;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;

@RestController
@RequiredArgsConstructor
public class BookController {

    @GetMapping("/cqrs/book")
    public ResponseEntity<List> getBooks() {

        MongoClient mongoClient =
                MongoClients.create("mongodb://localhost:27017");

        MongoDatabase database =
                mongoClient.getDatabase("mymongo");

        MongoCollection<Document> mongo_books =
                database.getCollection("books");

        List<Document> list = new ArrayList<Document>();

        try {
            try (MongoCursor<Document> cur =
                         mongo_books.find().iterator()) {

                while (cur.hasNext()) {
                    Document doc = cur.next();
                    list.add(doc);
                }
            }

        } catch (Exception e) {
            e.printStackTrace();

        } finally {
            mongoClient.close();
        }

        return ResponseEntity
                .status(HttpStatus.OK)
                .body(list);
    }
}
```

조회 과정은 다음과 같다.

```text
GET /cqrs/book
       ↓
MongoClient 생성
       ↓
mymongo Database 선택
       ↓
books Collection 선택
       ↓
find()
       ↓
MongoCursor
       ↓
List<Document>
       ↓
HTTP Response
```

`MongoClients.create()`를 이용하여 MongoDB에 연결하고 `mymongo` Database의 `books` Collection을 가져온다.

`find()`를 통해 Collection의 Document를 조회하고 `MongoCursor`를 순회하면서 결과를 `List<Document>`에 저장한다.

조회가 끝나면 `mongoClient.close()`를 호출하여 MongoDB 연결을 종료하고, 조회 결과를 HTTP Response로 반환한다.

## 4 ) **CQRS 구조에서의 역할**

---

이번 실습에서는 하나의 애플리케이션과 하나의 데이터베이스에서 읽기와 쓰기를 모두 처리하지 않는다.

```text
                  Client
                    │
          ┌─────────┴─────────┐
          │                   │
     데이터 변경 요청        데이터 조회 요청
      (Command)            (Query)
          │                   │
          ▼                   ▼
   Write Project        Read Project
          │                   │
          ▼                   ▼
        MySQL               MongoDB
```

Write Project는 데이터 변경을 담당하고 MySQL을 사용한다.

Read Project는 데이터 조회를 담당하고 MongoDB를 사용한다.

이를 통해 CQRS에서 설명한 **Command와 Query의 책임 분리**를 실제 Spring Boot 프로젝트 수준에서 확인할 수 있다.

현재 구현 상태는 다음과 같다.

```text
Write Project → MySQL

Read Project  → MongoDB
```

이후 Kafka를 연결하면 다음 구조로 확장할 수 있다.

```text
Write Project
     ↓
   MySQL
     ↓
   Kafka
     ↓
Read Project
     ↓
  MongoDB
```

> **실습 정리**
>
> - CQRS 구현을 위해 Write Project와 Read Project를 서로 분리하였다.
>
> - Write Project는 Spring Boot, Spring Data JPA, MySQL을 이용하여 Command 영역을 구현한다.
>
> - 사용자가 전달한 데이터는 `BookDTO`를 통해 Controller와 Service로 전달되고, `Book` Entity로 변환된 뒤 `BookRepository`를 통해 MySQL에 저장된다.
>
> - Read Project는 MongoDB의 `books` Collection에서 데이터를 조회하여 Query 요청에 응답한다.
>
> - Write 영역에서는 MySQL을 사용하고 Read 영역에서는 MongoDB를 사용하여 각각의 작업에 서로 다른 저장 기술을 적용하였다.
>
> - 이를 통해 CQRS에서 설명한 읽기와 쓰기의 책임 분리를 실제 Spring Boot 프로젝트로 구성하였다.
>
> - 두 프로젝트 모두 Kafka 의존성을 포함하고 있지만 현재 제공된 강의 내용에서는 Kafka를 통한 Write와 Read 영역의 연동까지 구현하지 않았다.
>
> - 이후 Kafka를 이용하여 Write 영역에서 발생한 데이터 변경을 Read 영역으로 전달하는 구조로 확장한다.

```
현재 내용은 CQRS 기본 프로젝트 구성 단계까지임
다음 수업에서 Kafka 연동 내용이 이어지면 이 문서 후반에 붙이기
강사님이 Git에 Repo 올려주신다고 하셨음
https://github.com/ggangpae1
IntelliJ Ultimate 라이센스 expr 언제인지 확인하기
```