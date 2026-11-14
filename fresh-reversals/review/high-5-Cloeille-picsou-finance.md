# Cloeille/picsou-finance (high)

Old ADR: `docs/decisions/2026-11-03-spring-serves-the-spa.md`
New ADR: `docs/decisions/2026-11-03-one-non-root-process.md`

## Old ADR status line

> Status: Active (the nginx forwarding step is superseded by [One non-root Java process](./2026-11-03-one-non-root-process.md))

## New ADR

ADR: One non-root Java process in the app image

> Date: 2026-11-03 > Status: Active

## Commits

### 31a83ca2a165f1a42ed930ff6de6d6ec14dcee19 (same)

feat(app-image): one non-root Java process, no nginx or supervisord (#342, 3/3) (#437)

* feat(app-image): Spring Boot serves the SPA and every response header (#342)

nginx keeps client-address and port forwarding, timeouts and SSE buffering
only. One header customizer covers both security chains, so HSTS follows
HSTS_ENABLED on the OAuth2 endpoints too. docker/tests/header_diff.py compares
two deployments' headers path by path.

Refs #342

* fix(app-image): address review on #434

- Cache only Vite's hashed /assets/ output for a year; public/ files revalidate.
- SetupFilter reads the decoded path for its allow-list too.
- header_diff.py: each side requests its own bundle; HSTS is accepted only with
  --candidate-hsts-disabled and only when the candidate omits it.
- Docs: process table; A

Changed files:

- .env.example
- .github/tests/test_sidecar_workflows.py
- .github/workflows/ci.yml
- CHANGELOG.md
- CONTRIBUTING.md
- README.md
- backend/src/main/java/com/picsou/adapter/CaisseEpargneAdapter.java
- backend/src/main/java/com/picsou/config/AnonymousBodyLimitFilter.java
- backend/src/main/java/com/picsou/config/AuthorizationServerConfig.java
- backend/src/main/java/com/picsou/config/ClientIp.java
- backend/src/main/java/com/picsou/config/CrossSiteCookieRequestMatcher.java
- backend/src/main/java/com/picsou/config/ForwardedOriginCustomizer.java
- backend/src/main/java/com/picsou/config/McpAuthenticationEntryPoint.java
- backend/src/main/java/com/picsou/config/SecurityConfig.java
- backend/src/main/java/com/picsou/config/SetupFilter.java
- backend/src/main/java/com/picsou/config/TrustedProxyBootstrap.java
- backend/src/main/java/com/picsou/controller/SetupController.java
- backend/src/main/resources/META-INF/spring.factories
- backend/src/main/resources/application.yml
- backend/src/test/java/com/picsou/config/AnonymousBodyLimitFilterTest.java
- backend/src/test/java/com/picsou/config/ForwardedHeadersCorsTest.java
- backend/src/test/java/com/picsou/config/ForwardedOriginServerTest.java
- backend/src/test/java/com/picsou/config/ProductionTomcatEdge.java
- backend/src/test/java/com/picsou/config/SecurityConfigHstsParsingTest.java
- backend/src/test/java/com/picsou/config/SetupFilterTest.java
- backend/src/test/java/com/picsou/config/TrustedProxyClientIpTest.java
- backend/src/test/java/com/picsou/config/hstsslice/SecurityConfigHstsHeaderTest.java
- backend/src/test/java/com/picsou/config/spaslice/SpaServingTest.java
- charts/picsou/README.md
- charts/picsou/templates/migration-job.yaml
- charts/picsou/tests/test_review_regressions.py
- charts/picsou/tests/test_upgrade_safety.py
- charts/picsou/values.yaml
- docker/.env.example
- docker/Caddyfile
- docker/Dockerfile
- docker/deploy.sh
- docker/docker-compose.yml
- docker/entrypoint.sh
- docker/nginx.conf

### 5daff0750ea990704a836ed1de19432360365cad (after)

fix(ci): publish latest only from the highest stable release tag (#553) (#555)

Changed files:

- .github/workflows/docker.yml

### 8ef117381209ca6e613a85554a57cb7780df431d (after)

feat(bnp): BNP Paribas / Hello bank! sync via bnp-auth sidecar (#306) (#541)

Changed files:

- backend/src/main/resources/application.yml
- backend/src/main/resources/db/migration/V150__bnp_sidecar_session.sql
- backend/src/test/java/com/picsou/migration/V142SidecarSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V150BnpSidecarSessionMigrationTest.java
- docker/docker-compose.yml
- services/bnp-auth/Dockerfile

### 370833f77fa6949f3480bf20d8159037440cc21b (after)

feat(banque-populaire): support PER via Natixis Assurances portal (#524) (#542)

Changed files:

- docker/docker-compose.yml

### 98339be26a8a6d1573a325c586bc5883b07b1573 (after)

fix(flyway): refuse to start on a database newer than the image (#553) (#554)

Changed files:

- backend/src/main/resources/application.yml
- backend/src/test/java/com/picsou/migration/FutureMigrationStartupTest.java

### 62875771e7ec34da31980d0266fbb1ee11df2623 (after)

refactor(tr): Trade Republic on sidecar_session with v2 login and refresh (#439)

Changed files:

- backend/src/main/resources/db/migration/V149__trade_republic_sidecar_session.sql
- backend/src/test/java/com/picsou/migration/V142SidecarSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V149TradeRepublicSidecarSessionMigrationTest.java

### 01be0be95b10fbffd20ccae434277ee532f61b0f (after)

feat(banque-populaire): remember identifier across reconnections (#521) (#536)

Changed files:

- backend/src/main/resources/db/migration/V148__banque_populaire_stored_identifier.sql
- backend/src/test/java/com/picsou/migration/V148BanquePopulaireStoredIdentifierMigrationTest.java

### c78ac34c762b75d2f8c418d7aad1da37c4c4dbc2 (after)

refactor(sidecar): Banque Populaire sessions move to sidecar_session (#481)

Changed files:

- backend/src/main/resources/db/migration/V147__banque_populaire_sidecar_session.sql
- backend/src/test/java/com/picsou/migration/V142SidecarSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V147BanquePopulaireSidecarSessionMigrationTest.java

### 1425e09e81b9569d47b248f5a7e43b7bd94518d8 (after)

chore(deps-dev): bump @vitejs/plugin-react from 5.2.0 to 6.2.1 (with Vite 8) (#528)

Changed files:

- frontend/vite.config.ts

### 797a189513ef7630bc405002d013119e4bff315e (after)

Revert "chore(deps-dev): bump @vitejs/plugin-react from 5.2.0 to 6.2.1 in /frontend (#515)" (#525)

Changed files:

- backend/pom.xml
- backend/src/main/resources/application.yml
- backend/src/main/resources/db/migration/V131__wise_connection.sql
- backend/src/main/resources/db/migration/V132__account_institution.sql
- backend/src/main/resources/db/migration/V133__account_type_brokerage.sql
- backend/src/main/resources/db/migration/V134__banque_populaire_session.sql
- backend/src/main/resources/db/migration/V135__account_type_peer_loan.sql
- backend/src/main/resources/db/migration/V136__peer_loans.sql
- backend/src/main/resources/db/migration/V137__peer_loan_cash_leg.sql
- backend/src/main/resources/db/migration/V138__peer_loan_linked_repayment.sql
- backend/src/main/resources/db/migration/V139__peer_loan_rate_period.sql
- backend/src/main/resources/db/migration/V140__widen_peer_loan_rate.sql
- backend/src/main/resources/db/migration/V141__peer_loan_rate_no_upper_bound.sql
- backend/src/main/resources/db/migration/V142__sidecar_session.sql
- backend/src/main/resources/db/migration/V143__lbp_session.sql
- backend/src/main/resources/db/migration/V144__lbp_saved_identifier.sql
- backend/src/main/resources/db/migration/V145__caisse_epargne_stored_identifier.sql
- backend/src/main/resources/db/migration/V146__natixis_sidecar_session.sql
- backend/src/test/java/com/picsou/migration/ReleaseMigrationCliTest.java
- backend/src/test/java/com/picsou/migration/V134BanquePopulaireSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V142SidecarSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V143LbpSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V144LbpSavedIdentifierMigrationTest.java
- backend/src/test/java/com/picsou/migration/V145CaisseEpargneStoredIdentifierMigrationTest.java
- backend/src/test/java/com/picsou/migration/V146NatixisSidecarSessionMigrationTest.java
- backend/src/test/java/com/picsou/service/CmesPlanMigrationPostgresTest.java
- backend/src/test/resources/sql/sync-service-currency-test-schema.sql
- backend/src/test/resources/sql/transaction-repository-account-fetch.sql
- backend/src/test/resources/sql/wise-connection-test-schema.sql
- docker/docker-compose.peer-loans-test.yml
- docker/docker-compose.yml
- frontend/package.json
- services/banque-populaire-auth/Dockerfile
- services/banque-populaire-auth/test_dockerfile.py
- services/base/Dockerfile
- services/base/requirements.txt
- services/caisse-epargne-auth/Dockerfile
- services/caisse-epargne-auth/test_dockerfile.py
- services/lbp-auth/Dockerfile
- services/natixis-auth/Dockerfile

### ee3f8c5c5e220b28ca6bc8c3218848f0d4174f9a (after)

chore(deps-dev): bump @vitejs/plugin-react from 5.2.0 to 6.2.1 in /frontend (#515)

Changed files:

- backend/pom.xml
- backend/src/main/resources/application.yml
- backend/src/main/resources/db/migration/V131__wise_connection.sql
- backend/src/main/resources/db/migration/V132__account_institution.sql
- backend/src/main/resources/db/migration/V133__account_type_brokerage.sql
- backend/src/main/resources/db/migration/V134__banque_populaire_session.sql
- backend/src/main/resources/db/migration/V135__account_type_peer_loan.sql
- backend/src/main/resources/db/migration/V136__peer_loans.sql
- backend/src/main/resources/db/migration/V137__peer_loan_cash_leg.sql
- backend/src/main/resources/db/migration/V138__peer_loan_linked_repayment.sql
- backend/src/main/resources/db/migration/V139__peer_loan_rate_period.sql
- backend/src/main/resources/db/migration/V140__widen_peer_loan_rate.sql
- backend/src/main/resources/db/migration/V141__peer_loan_rate_no_upper_bound.sql
- backend/src/main/resources/db/migration/V142__sidecar_session.sql
- backend/src/main/resources/db/migration/V143__lbp_session.sql
- backend/src/main/resources/db/migration/V144__lbp_saved_identifier.sql
- backend/src/main/resources/db/migration/V145__caisse_epargne_stored_identifier.sql
- backend/src/main/resources/db/migration/V146__natixis_sidecar_session.sql
- backend/src/test/java/com/picsou/migration/ReleaseMigrationCliTest.java
- backend/src/test/java/com/picsou/migration/V134BanquePopulaireSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V142SidecarSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V143LbpSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V144LbpSavedIdentifierMigrationTest.java
- backend/src/test/java/com/picsou/migration/V145CaisseEpargneStoredIdentifierMigrationTest.java
- backend/src/test/java/com/picsou/migration/V146NatixisSidecarSessionMigrationTest.java
- backend/src/test/java/com/picsou/service/CmesPlanMigrationPostgresTest.java
- backend/src/test/resources/sql/sync-service-currency-test-schema.sql
- backend/src/test/resources/sql/transaction-repository-account-fetch.sql
- backend/src/test/resources/sql/wise-connection-test-schema.sql
- docker/docker-compose.peer-loans-test.yml
- docker/docker-compose.yml
- frontend/package.json
- services/banque-populaire-auth/Dockerfile
- services/banque-populaire-auth/test_dockerfile.py
- services/base/Dockerfile
- services/base/requirements.txt
- services/caisse-epargne-auth/Dockerfile
- services/caisse-epargne-auth/test_dockerfile.py
- services/lbp-auth/Dockerfile
- services/natixis-auth/Dockerfile

### 8bb6d5395418a9d1e1744b5a8e380e0f6906b856 (after)

feat(natixis): Natixis Interépargne employee-savings connector (#461)

Changed files:

- backend/src/main/resources/application.yml
- backend/src/main/resources/db/migration/V146__natixis_sidecar_session.sql
- backend/src/test/java/com/picsou/migration/V142SidecarSessionMigrationTest.java
- backend/src/test/java/com/picsou/migration/V146NatixisSidecarSessionMigrationTest.java
- docker/docker-compose.yml
- services/natixis-auth/Dockerfile
