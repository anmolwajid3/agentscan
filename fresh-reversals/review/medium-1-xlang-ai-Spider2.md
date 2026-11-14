# xlang-ai/Spider2 (medium)

Old ADR: `spider2-dbt/examples/quickbooks002/dbt_packages/dbt_utils/docs/decisions/adr-0000-documenting-architecture-decisions.md`
New ADR: `spider2-dbt/examples/xero_new002/dbt_packages/dbt_utils/docs/decisions/adr-0001-decision-record-format.md`

## Old ADR status line

Superseded by [ADR-0001](adr-0001-decision-record-format.md).

## New ADR

FORMAT AND STRUCTURE OF DECISION RECORDS



## Commits

### ef559e1c56c8bb13d12ed3d97a5c5481c05690d7 (after)

upload spider2 full examples and answer

Changed files:

- spider2/examples/airbnb001/dbt_packages/dbt_utils/dev-requirements.txt
- spider2/examples/airbnb001/dbt_packages/dbt_utils/docker-compose.yml
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_cardinality_equality_a.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_cardinality_equality_b.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_not_null_proportion.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_accepted_range.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_at_least_one.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_equal_rowcount.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_expression_is_true.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_fewer_rows_than_table_1.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_fewer_rows_than_table_2.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_mutually_exclusive_ranges_no_gaps.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_mutually_exclusive_ranges_with_gaps.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_mutually_exclusive_ranges_with_gaps_zero_length.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_not_accepted_values.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_not_constant.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_not_null_where.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_relationships_where_table_1.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_relationships_where_table_2.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_sequential_timestamps.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_sequential_values.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_test_unique_where.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/data_unique_combination_of_columns.csv
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/data/schema_tests/schema.yml
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/macros/assert_equal_values.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/macros/limit_zero.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/macros/tests.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/schema.yml
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_any_value.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_array_append.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_array_concat.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_array_construct.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_bool_or.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_concat.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_current_timestamp.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_current_timestamp_in_utc.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_date_trunc.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_dateadd.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_datediff.sql
- spider2/examples/airbnb001/dbt_packages/dbt_utils/integration_tests/models/cross_db_utils/test_hash.sql

### c62529ceb020dbde672e09be5ce28bf0787fc2bd (same)

commit message

Changed files:

- assets/bigquery-view-schema.png
- methods/spider-agent-snow/requirements.txt
- methods/spider-agent-snow/spider_agent/controllers/setup.py
- methods/spider-agent-snow/spider_agent/images/spider_agent-image/Dockerfile
- methods/spider-agent-snow/spider_agent/images/spider_agent_clickhouse-image/Dockerfile
- methods/spider-agent-snow/spider_agent/images/spider_agent_postgres-image/Dockerfile
- methods/spider-agent/requirements.txt
- methods/spider-agent/spider_agent/controllers/setup.py
- methods/spider-agent/spider_agent/images/spider_agent-image/Dockerfile
- methods/spider-agent/spider_agent/images/spider_agent_clickhouse-image/Dockerfile
- methods/spider-agent/spider_agent/images/spider_agent_postgres-image/Dockerfile
- spider2-lite/baselines/codes/requirements.txt
- spider2-lite/baselines/codes/schema_item_filter.py
- spider2-lite/baselines/dailsql/requirements.txt
- spider2-lite/baselines/dinsql/requirements.txt
- spider2-lite/evaluation_suite/example_submission_folder/bq026_2.sql
- spider2-lite/evaluation_suite/example_submission_folder/bq117.sql
- spider2-lite/evaluation_suite/example_submission_folder/bq207.sql
- spider2-lite/evaluation_suite/gold/sql/bq001.sql
- spider2-lite/resource/databases/bigquery/HTAN_1/isb-cgc-bq.HTAN_versioned/schema_r2.json
- spider2-lite/resource/databases/bigquery/HTAN_1/isb-cgc-bq.HTAN_versioned/schema_r3.json
- spider2-lite/resource/databases/bigquery/HTAN_1/isb-cgc-bq.HTAN_versioned/schema_r4.json
- spider2-lite/resource/databases/bigquery/HTAN_1/isb-cgc-bq.HTAN_versioned/schema_r5.json
- spider2-lite/resource/databases/snowflake/HTAN_2/HTAN/SCHEMA_CURRENT.json
- spider2-lite/resource/databases/snowflake/HUMAN_GENOME_VARIANTS/HUMAN_GENOME_VARIANTS/_1000_GENOMES_PHASE_3_OPTIMIZED_SCHEMA_VARIANTS_20150220.json
- spider2-lite/resource/databases/snowflake/US_REAL_ESTATE/CYBERSYN/IRS_MIGRATION_BY_CHARACTERISTIC_ATTRIBUTES.json
- spider2-lite/resource/databases/snowflake/US_REAL_ESTATE/CYBERSYN/IRS_MIGRATION_BY_CHARACTERISTIC_TIMESERIES.json
- spider2-lite/resource/databases/snowflake/US_REAL_ESTATE/CYBERSYN/IRS_ORIGIN_DESTINATION_MIGRATION_TIMESERIES.json
- spider2-snow/resource/databases/HTAN_1/HTAN_VERSIONED/SCHEMA_R2.json
- spider2-snow/resource/databases/HTAN_1/HTAN_VERSIONED/SCHEMA_R3.json
- spider2-snow/resource/databases/HTAN_1/HTAN_VERSIONED/SCHEMA_R4.json
- spider2-snow/resource/databases/HTAN_1/HTAN_VERSIONED/SCHEMA_R5.json
- spider2-snow/resource/databases/HTAN_2/HTAN/SCHEMA_CURRENT.json
- spider2-snow/resource/databases/HUMAN_GENOME_VARIANTS/HUMAN_GENOME_VARIANTS/_1000_GENOMES_PHASE_3_OPTIMIZED_SCHEMA_VARIANTS_20150220.json
- spider2-snow/resource/databases/US_REAL_ESTATE/CYBERSYN/IRS_MIGRATION_BY_CHARACTERISTIC_ATTRIBUTES.json
- spider2-snow/resource/databases/US_REAL_ESTATE/CYBERSYN/IRS_MIGRATION_BY_CHARACTERISTIC_TIMESERIES.json
- spider2-snow/resource/databases/US_REAL_ESTATE/CYBERSYN/IRS_ORIGIN_DESTINATION_MIGRATION_TIMESERIES.json
- spider2/evaluation_suite/example_submission_folder/335fb285-c9fd-45ff-ba8d-fe89a62016f7/gold.sql
- spider2/evaluation_suite/example_submission_folder/9863d716-0af4-422a-9bfd-65ff5684eca1/query.sql
- spider2/examples/activity001/dbt_packages/dbt_utils/dev-requirements.txt
