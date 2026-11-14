# DependencyTrack/dependency-track (low)

Old ADR: `docs/adr/003-notification-publishing.md`
New ADR: `docs/adr/011-notification-outbox.md`

## Old ADR status line

| Superseded by [ADR-011](011-notification-outbox.md) | 2025-01-19 | [@nscuro](https://github

## New ADR

Context

| Status   | Date       | Author(s)                            | |:---------|:-----------|:-------------------------------------| | Accepted | 2025-10-26 | [@nscuro](https://github.com/nscuro) |

## Commits

### e7677dee09f398df42dc2a97c548840ffa3a80a9 (after)

Preprocess SPDX license list

Changed files:

- apiserver/src/main/resources/license-list-data/json/details/PostgreSQL.json

### fe9a79d1cc8ca1c5bd32b4ced0cdce261a1db2d0 (after)

Promote various Error Prone checks to ERROR

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisher.java

### 33f4316575f6149c1902ed5a7e3ff80944c07362 (after)

Expose outbound connection policy to plugins

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactory.java
- notification/publishing/src/test/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactoryTest.java
- notification/publishing/src/test/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherTest.java

### 6b8595a485568c7c6e5e5727f0b64d389cc95450 (after)

Remove ServiceRegistry from plugin API

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactory.java

### a0e91ce6680087f21106296011c669b102ce9b6b (after)

Apply code formatting preferences

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisher.java
- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactory.java
- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/package-info.java
- notification/publishing/src/test/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactoryTest.java
- notification/publishing/src/test/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherTest.java

### a2a38b96add6437b194aa4473eb231faa789e4b4 (after)

Define display names for all extensions

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactory.java

### a9ea3ccde2dad5f306ab6e11c3ac85de39c5f009 (after)

Fix KafkaNotificationPublisherTest flakiness

Changed files:

- notification/publishing/src/test/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherTest.java

### adcc9b227bd2797777f1842366cdff856c9e1c58 (after)

Handle moved CompressionType class in kafka-clients

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactory.java

### 363bec0aa3686b3fba7eaa9587dc0f63a6ca93a3 (after)

Add v4 migration tooling

Changed files:

- support/v4-migrator/src/test/resources/v4-schema.postgresql.sql

### 0d6411d6fcfbce8fcce2da4f0b5e17ab64294e1d (after)

Remove PROJECT_VULN_ANALYSIS_COMPLETE notifications

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisher.java

### 42c7414915a3396ef819c12d23a79c053b8c7384 (after)

Update version references in code to 5.0.0

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisher.java
- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactory.java

### e026cdae255a8f0b24452bcdaa54f57a1c65960b (before)

Streamline plugin API

Changed files:

- notification/publishing/src/main/java/org/dependencytrack/notification/publishing/kafka/KafkaNotificationPublisherFactory.java
