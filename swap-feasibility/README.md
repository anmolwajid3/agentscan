# Library-swap feasibility (P1)

This checks whether open-source Java projects swap libraries often enough, after they start using AI coding tools, for a comparison to be possible. It does not modify `adr-feasibility/`. The adoption date is imported from that package.

The He et al. (2021) lists used here are:

- `source/projects.csv`, 19,652 repositories, from Zenodo `cache.zip` (`10.5281/zenodo.5091384`). Columns include `nameWithOwner`, `fork`, `createdTimestamp`, `lastPushedTimestamp`, `commitsCount`, `pomFilesCount`.
- `source/rules_typed.csv`, 1,194 rules, from Zenodo `gitrepo.zip` at `LibraryMigration/data/rules_typed.csv`. Columns: `fromLib`, `toLib`, `type`.

```bash
cd swap-feasibility
python3 -m unittest discover -s tests -q
python3 -m swap_pilot trial
```

`trial` reads the five repositories named in `config.yaml`.

`sample` screens the He et al. list with `GITHUB_TOKEN`, then clones a random sample of 2,000 eligible projects. The seed is `sample_seed` in `config.yaml`. The main swap count uses the 802 non-rename rules. Rename rules are reported separately. The sample does not declare pass or fail.
