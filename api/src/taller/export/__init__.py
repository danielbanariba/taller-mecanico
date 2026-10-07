"""Read-only data export: a ZIP of per-entity CSVs for the current workshop.

This package never defines its own entity, migration, or ORM model. It reads
other features' existing tables, always scoped by ``workshop_id``
(``design.md``'s AD-13), and never writes.
"""
