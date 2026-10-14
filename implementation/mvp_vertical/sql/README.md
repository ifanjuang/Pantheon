# Migrations

Two lineages, two directories.

```text
sql/            Agency and Cockpit
sql/hermes/     Hermes execution
```

They were numbered independently from the start, into one directory, so four
prefixes named two files each — `003`, `004`, `005` and `010`. Nothing ran in the
wrong order because of it: every cross-file dependency held under both readings.
What broke is narrower and worth stating plainly — `sql/003_*` stopped naming one
file, so the prefix no longer answered the only question a numeric prefix exists
to answer.

Separating the directories removes three of the four collisions without changing
a single number. The fourth was inside the Agency lineage and was resolved by
moving `source_intake_admission` from `010` to the free `009`, which is earlier
in every initializer that replays both.

`006` and `007` are absent from the Agency lineage. They belong to Hermes and
always did.

## The number is not the replay order

Order is declared in Python, not inferred from filenames:

- `cockpit_composed.initialize_composed_schema()` replays twelve migrations, in
  an order that is deliberately not the prefix order;
- `cockpit_shell.initialize_cockpit_schema()` replays the first four of those;
- the Hermes modules, `store.DDL` and `paperless_ingestion` each replay their
  own.

There is no single sequence to encode, so the prefix records when a migration
joined its lineage — not when it runs. Both orders satisfy every dependency; the
tests are what keep that true, not the numbering.

## What is enforced

`tests/test_migration_naming.py` fails on a duplicate prefix within a lineage, on
a module naming a migration that does not exist, and on a `.sql` file no module
replays.

`tests/test_startup_migrations_lock_light.py` fails on an unguarded `ALTER TABLE`
in anything the composed initializer replays on every boot, and applies the whole
startup set to a throwaway database to prove the guarded blocks reach their target
schema rather than being skipped.

A guard must key on a value the migration **adds**, never one it shares with the
definition it replaces — a marker present in both concludes "already applied" and
skips the migration forever, on fresh databases only, which is the one case local
development never exercises.
