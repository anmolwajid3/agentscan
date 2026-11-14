# onetimesecret/onetimesecret (low)

Old ADR: `docs/adr/adr-016-domain-validation-state-model.md`
New ADR: `docs/adr/adr-049-operator-managed-domain-authorization.md`

## Old ADR status line

accepted

## New ADR

Status

Accepted

## Commits

### b4108deafd802aa150acb0f27561489ee6adaaa2 (after)

fix(boot): assert Redis TLS and add redis.require_tls

Changed files:

- lib/onetime/initializers/check_redis_url.rb

### db57f7df925bd2b4e63ccc07cc7346dc134dfa0b (before)

[#4450] Keep the datastore password out of boot logs and errors

Changed files:

- lib/onetime/initializers/check_redis_url.rb

### 36c87e11bfabc65c37c87303cc31fcad554ad813 (before)

fix: use string keys for config dig lookups

Changed files:

- lib/onetime/initializers/check_redis_url.rb

### 8c9187749765d2930d1574864a786cc9ec92b615 (before)

Remove dead bcrypt and encryptor dependencies

Changed files:

- apps/web/auth/try/operations/migrate_password_from_redis_try.rb

### 4c20244e11a439995dda1aa7613c0732a3b56e12 (before)

refactor: Remove detect-legacy-data initializer

Changed files:

- lib/onetime/cli/migrate_redis_data_command.rb
