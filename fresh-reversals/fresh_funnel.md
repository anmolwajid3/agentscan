# Fresh reversal funnel (interim)

Interim. No builds were run. This is not a pass or fail.

Sample seed: 20261114. Review seed: 20261114. Cap: 1500.
The 1,500 repositories were drawn at random from the path-query names after sorting, not in the order Sourcegraph returned them.
The implementing-commit window is 180 days before and 180 days after the new ADR's author date.

## Step 1. ADR folders

Unique GitHub repositories from the path queries: 1598.

- docs_adr: returned 1129, Sourcegraph matchCount 1129.
- doc_adr: returned 57, Sourcegraph matchCount 57.
- docs_decisions: returned 265, Sourcegraph matchCount 265.
- arch_decisions: returned 46, Sourcegraph matchCount 46.
- doc_arch_decisions: returned 4, Sourcegraph matchCount 4.
- adr_root: returned 51, Sourcegraph matchCount 51.
- docs_adrs: returned 79, Sourcegraph matchCount 79.

Drawn for the capped run: 1500.

## Step 2. Not a fork, not archived, has a build file

Screened: 1500.
Kept: 1225.
- fork: 0.
- archived: 2.
- no build file: 271.
- api error: 2.

## Step 3. Superseded pairs

Repositories whose clone or read failed: 3.
Repositories with at least two ADR files: 974.
Markdown links to other ADRs rejected because they were ordinary cross-references: 16917.
Superseded wording whose newer ADR could not be resolved: 335.
Pairs written: 2397.

## Step 4. Implementing commits

High confidence: 2236.
Medium confidence: 93.
Low confidence: 10.
No commit found: 58.

Pairs lost at this step:

- 46: no implementing commit in the 180-day window
- 10: new ADR commit not found
- 2: git log timed out

## Step 5. Comparison with the old 133

Old superseded records reconstructed from the saved measurements: 133.
New pairs that were in that set: 8.
Old records missing from the new pairs: 126.

### no build file (1)

- home-assistant/architecture `adr/0002-minimum-supported-python-version.md`

### no resolvable newer ADR under the link rule (1)

- MaibornWolff/codecharta `gh-pages/_posts/adr/2017-01-02-ADR_3_pick_visualization_language.md`

### repository was not returned by the path queries (124)

- ASethi93/james `src/adr/0003-distributed-workqueue.md`
- ASethi93/james `src/adr/0026-removing-configured-additional-mailboxListeners.md`
- Amsterdam/signals-frontend `docs/adr/0010-naming-conventions.md`
- Controlix/akka-monitor `doc/adr/0004-use-micrometer-prometheus.md`
- DFE-Digital/buy-for-your-school `doc/architecture/decisions/0003-use-standard-rb.md`
- DFE-Digital/buy-for-your-school `doc/architecture/decisions/0005-use-bullet-to-catch-nplus1-queries.md`
- DFE-Digital/claim-additional-payments-for-teaching `docs/architecture-decisions/0008-use-govuk-verify-for-claiment-identity-assurance.md`
- JulianG/bananatabs `doc/adr/0002-react-testing-library.md`
- LBHackney-IT/Data-Platform-Playbook `docs/architecture-decisions/records/008-production-data-in-staging.md`
- MITLibraries/mario `docs/architecture-decisions/0002-use-elasticsearch.md`
- MITLibraries/mario `docs/architecture-decisions/0005-use-aws-lambda.md`
- MITLibraries/mario `docs/architecture-decisions/0008-use-one-s3-bucket-per-source.md`
- MITLibraries/mario `docs/architecture-decisions/0011-indexing-commands-and-flows.md`
- MITLibraries/mario `docs/architecture-decisions/0012-use-lambda-and-fargate-for-task-execution.md`
- NERC-CEH/datalab `architecture/decisions/0013-custom-redbird-proxy.md`
- NERC-CEH/datalab `architecture/decisions/0014-use-traefik-for-reverse-proxy.md`
- NERC-CEH/datalab `architecture/decisions/0015-use-kong-for-reverse-proxy.md`
- NERC-CEH/datalab `architecture/decisions/0024-vault-for-secret-store.md`
- NERC-CEH/datalab `architecture/decisions/0034-custom-k8s-deployment-tool.md`
- PakkuDon/SoundCloudVisualizer `doc/architecture/decisions/0002-manage-client-side-dependencies-using-bower.md`
- PakkuDon/SoundCloudVisualizer `doc/architecture/decisions/0003-use-angularjs-1-x.md`
- PakkuDon/SoundCloudVisualizer `doc/architecture/decisions/0004-use-gulp-to-build-source-code.md`
- SAP/cloud-sdk-js `knowledge-base/adr/outdated/0001-circuit-breaker-options.md`
- SAP/cloud-sdk-js `knowledge-base/adr/outdated/0007-use-yarn-workspaces.md`
- SAP/cloud-sdk-js `knowledge-base/adr/outdated/0015-date-time-handling.md`
- UKGovernmentBEIS/beis-report-official-development-assistance `doc/architecture/decisions/0006-use-auth0-for-authentication.md`
- UKGovernmentBEIS/beis-report-official-development-assistance `doc/architecture/decisions/0008-use-heroku-for-hosting.md`
- UKGovernmentBEIS/beis-report-official-development-assistance `doc/architecture/decisions/0020-use-skylight-application-performance-monitoring.md`
- UKGovernmentBEIS/beis-report-official-development-assistance `doc/architecture/decisions/0026-use-omniauth-to-standardise-authentication.md`
- Vodurden/CrossyToad `docs/architecture/decisions/adr-0007-SUPERSEDED-mtl-style-for-affects.md`
- Vodurden/CrossyToad `docs/architecture/decisions/adr-0012-SUPERSEDED-use-concrete-state-monad.md`
- Voronenko/runbooks-mkdocs `docs/architecture/decisions/0002-use-sphinx-as-our-knowledge-base-system.md`
- adoble/adr-j `doc/adr/0002-implement-as-Java.md`
- adoble/adr-j `doc/adr/0004-markdown-format.md`
- akvo/akvo-lumen `doc/arch/adr-002-elasticsearch.md`
- alphagov/accessibility-monitoring `docs/architecture/adrs/ADR000-database-accessibility-monitoring.md`
- alphagov/accessibility-monitoring `docs/architecture/adrs/ADR000-template.md`
- alphagov/content-publisher `docs/adr/0006-tagging-governments.md`
- alphagov/govuk-aws `docs/architecture/decisions/0003-aws-networking-outline.md`
- alphagov/govuk-aws `docs/architecture/decisions/0004-dns-definitions-for-hosts-and-services.md`
- alphagov/gsp `docs/architecture/adr/ADR000-template.md`
- alphagov/gsp `docs/architecture/adr/ADR004-tenant-isolation.md`
- alphagov/gsp `docs/architecture/adr/ADR005-ingress.md`
- alphagov/gsp `docs/architecture/adr/ADR006-authentication-method.md`
- alphagov/gsp `docs/architecture/adr/ADR007-identity-provider.md`
- alphagov/gsp `docs/architecture/adr/ADR009-multitenant-ci-cd.md`
- alphagov/gsp `docs/architecture/adr/ADR010-placement-of-ci-cd-tools.md`
- alphagov/gsp `docs/architecture/adr/ADR012-docker-image-repositories.md`
- alphagov/gsp `docs/architecture/adr/ADR015-aws-iam-authentication.md`
- alphagov/gsp `docs/architecture/adr/ADR028-container-tools.md`
- alphagov/gsp `docs/architecture/adr/ADR030-aws-service-operator.md`
- alphagov/gsp `docs/architecture/adr/ADR032-sre-permissions.md`
- alphagov/gsp `docs/architecture/adr/ADR038-sre-permissions-istio.md`
- alphagov/monitoring-doc `documentation/architecture/decisions/0003-use-ecs-for-initial-beta-buildout.md`
- alphagov/paas-team-manual `source/architecture_decision_records/ADR017-cell-capacity-assignment.html.md`
- alphagov/paas-team-manual `source/architecture_decision_records/ADR022-web_app_language_and_framework_selection.html.md`
- alphagov/verify-service-provider `docs/adr/0003-use-files-to-store-private-keys.md`
- alphagov/verify-service-provider `docs/adr/0008-provide-an-end-to-end-stub.md`
- apache/james-project `src/adr/0003-distributed-workqueue.md`
- apache/james-project `src/adr/0026-removing-configured-additional-mailboxListeners.md`
- benjamminj/portfolio `docs/architecture/decisions/0002-use-nextjs.md`
- benjamminj/portfolio `docs/architecture/decisions/0007-use-custom-json-serialization.md`
- benjamminj/portfolio `docs/architecture/decisions/0011-use-preact.md`
- benjamminj/portfolio `docs/architecture/decisions/0013-migrate-to-sveltekit.md`
- benjamminj/portfolio `docs/architecture/decisions/0014-migrate-to-remix.md`
- cloudfoundry/cf-k8s-networking `doc/architecture-decisions/0002-directly-create-istio-resources.md`
- cloudfoundry/cf-k8s-networking `doc/architecture-decisions/0007-maintain-generated-istio.md`
- cookstaar/adr-example `doc/architecture/decisions/0003-use-ember-as-the-main-frontend-js-framework.md`
- cosmos/cosmos-sdk `docs/architecture/adr-010-modular-antehandler.md`
- cosmos/cosmos-sdk `docs/architecture/adr-022-custom-panic-handling.md`
- dogmatiq/dogma `docs/adr/0010-handler-timeout-hints.md`
- elifesciences/tech-team `adr/0004-supported-python-versions.md`
- hyprnz/terraform-aws-msk-module `docs/architecture/decisions/0008-key-pair-utility.md`
- latextemplates/generator-latex-template `docs/decisions/0003-use-cleveref.md`
- lcobucci/kafka `docs/architecture-decisions/0002-require-php-7-2-64-bit.md`
- lucentminds/osticket-ticket-options-plugin `widgets/ui-agent-search/docs/adrs/000-template.md`
- lucentminds/osticket-ticket-options-plugin `widgets/ui-dialog-confirm/docs/adrs/000-template.md`
- lucentminds/osticket-ticket-options-plugin `widgets/ui-error-banner/docs/adrs/000-template.md`
- lucentminds/osticket-ticket-options-plugin `widgets/ui-show-agent-add/docs/adrs/000-template.md`
- lucentminds/osticket-ticket-options-plugin `widgets/ui-show-agent-remove/docs/adrs/000-template.md`
- lucentminds/osticket-ticket-options-plugin `widgets/ui-user-list/docs/adrs/000-template.md`
- mahanhz/clean-architecture-example `doc/adr/0005-api-versioning.md`
- matwei/ipsec-tester `doc/adr/0002-use-libpcap-and-libnet.md`
- michelezamuner/smjs `docs/system/decisions/superseded/2018121502-data-unit-is-parameterized-type.md`
- ministryofjustice/opg-lpa `docs/architecture/adrs/0013-connection-pooling.md`
- ministryofjustice/opg-use-an-lpa `docs/architecture/decisions/0003-session-storage-using-jwt.md`
- mozilla/bedrock `docs/architecture/decisions/0002-move-ci-cd-pipelines-to-gitlab.md`
- mozilla/bedrock `docs/architecture/decisions/0006-revise-tooling-for-python-dependency-management.md`
- mozilla/bedrock `docs/architecture/decisions/0009-use-manage-contentful-migrations.md`
- mozmeao/snippets-service `docs/architecture/decisions/0006-release-jobs-in-nightly-bundles.md`
- mxsolid/james-project `src/adr/0003-distributed-workqueue.md`
- nais/kafkarator `doc/adr/0001-record-architecture-decisions.md`
- nais/kafkarator `doc/adr/0002-combine-topic-creation-and-credentials-management-in-same-app.md`
- nhsuk/connecting-to-services `doc/adr/0005-add-cache-control-headers.md`
- nhsuk/connecting-to-services `doc/adr/0011-add-google-sitelinks-searchbox-metadata.md`
- nhsuk/gp-finder `doc/adr/0003-use-mongodb-for-search.md`
- nhsuk/nearby-services-api `doc/adr/0003-use-mongodb-for-data-storage.md`
- nhsuk/register-with-a-gp-beta-web `docs/architecture/decisions/0004-cookies-encryption.md`
- nhsuk/sexual-health-service-finder `doc/adr/0003-use-elasticsearch.md`
- nulib/meadow `doc/architecture/decisions/0002-ulids.md`
- nulib/meadow `doc/architecture/decisions/0004-api.md`
- nulib/meadow `doc/architecture/decisions/0022-iiif-manifests.md`
- nulib/meadow `doc/architecture/decisions/0029-npm.md`
- omair-sajid-confiz/adr-poc `doc/adr/0003-write-help-file.md`
- omair-sajid-confiz/adr-poc `doc/adr/0005-hardcode-dependencies.md`
- openkfw/TruBudget `doc/adr/0006-multi-node-setup.md`
- openlobby/openlobby-server `docs/architecture/decisions/0006-use-flask.md`
- orevial/adr-demo `doc/adr/0003-use-cassandra-as-storage-backend/0003-use-cassandra-as-storage-backend.md`
- palantir/atlasdb `docs/source/miscellaneous/doc/adr/0002-prevent-tables-from-being-creating-simultaneously-in-cassandra-via-a-locks-table.md`
- palantir/atlasdb `docs/source/miscellaneous/doc/adr/0004-create-schema-lock-table-via-a-one-off-cli-command.md`
- palantir/atlasdb `docs/source/miscellaneous/doc/adr/0006-create-schema-lock-table-using-configuration.md`
- palantir/atlasdb `docs/source/miscellaneous/doc/adr/0008-add-heartbeat-for-schema-lock-holders.md`
- pau2882/nso.aurora `adr/Kiosks-Fridge-customer-vendor-management.md`
- pau2882/nso.aurora `adr/LoyaltyProgram.md`
- pau2882/nso.aurora `adr/MartketPlace.md`
- pau2882/nso.aurora `adr/SegmentationEngine.md`
- qbit86/arborescence `docs/decisions/0004-restrict-language-version-to-csharp-8.md`
- qbit86/arborescence `docs/decisions/0005-restrict-language-version-to-csharp-9.md`
- qbit86/arborescence `docs/decisions/0006-restrict-language-version-to-csharp-10.md`
- servian/TechChallengeApp `doc/adr/0004-config-only-in-config-file.md`
- umd-lib/caia `docs/adr/0006-aleph-interaction-assumptions-for-circrequests.md`
- umd-lib/caia `docs/adr/0008-aleph-circrequests-denied-entries-handling.md`
- wmde/fundraising-application `doc/adr/029_Megarepo.md`
- zooniverse/front-end-monorepo `docs/arch/adr-15.md`

Review packets are in `review/`. Five were requested at each confidence. A short band means fewer than five pairs had that confidence.
