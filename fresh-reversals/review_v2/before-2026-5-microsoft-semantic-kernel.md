# microsoft/semantic-kernel (before-2026)

Old ADR: `docs/decisions/0015-completion-service-selection.md`
New ADR: `docs/decisions/0038-completion-service-selection.md`
New ADR date: 2024-03-19T14:06:01+00:00
Partial: no

## Old ADR status line

superseded by [ADR-0038](0038-completion-service-selection.md)

## New ADR

These are optional elements. Feel free to remove any of them.



## Best commit

`5f49880d52a0691c8c5fa2e7bc9830fa872f75e1` (after)

Python: Json schema improvements for Union and Optional (#7367)

commit title matches the new ADR: optional; changes application code

Changed files:

- M python/samples/getting_started/00-getting-started.ipynb
- M python/semantic_kernel/connectors/ai/function_calling_utils.py
- M python/semantic_kernel/const.py
- M python/semantic_kernel/exceptions/function_exceptions.py
- M python/semantic_kernel/functions/kernel_function_decorator.py
- M python/semantic_kernel/schema/kernel_json_schema_builder.py
- M python/tests/integration/connectors/memory/test_postgres.py
- M python/tests/unit/functions/test_kernel_parameter_metadata.py
- M python/tests/unit/schema/test_schema_builder.py
- M python/tests/unit/services/test_service_utils.py

## Other candidates

6fa1d6ec5663 Java: optionally allow/disallow missing functions in sequential planner (#3384); a29acc70352a .Net: Make modelId optional for Azure AI services (#4159); ab2e72394f8d .Net: Optional arguments parameter for template and code rendering API (#3773); e6b3633925f5 .Net: Update stepwise planner to accept optional chatHistory to resume execution; 03c1db876c77 .Net: Remove implicit operator string from base content types (#4075); 079371d8b67a .Net: Python: remove _async from methods (#5160); 0a9e74a3c62a .Net: Remove JsonSchema.Net dependency from Microsoft.SemanticKernel.Abstraction; 0ed68b7e7df5 Java17 - Remove Double Brace - vectorSize/queryDialect - Use timestamp
