"""
Shared in-memory data stores for API routes.
Separating stores to avoid circular imports between route modules.
"""

from __future__ import annotations

from datetime import datetime

# In-memory race data store
# Key: race_id, Value: dict with driver_name, laps, analyses, created_at
race_store: dict[str, dict] = {}
