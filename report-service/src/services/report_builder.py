from datetime import datetime
from typing import Any, Literal

from sqlalchemy import text

from src.engines.postgres import _get_session_factory


class ResultSet:
    """Wrapper around query results."""

    def __init__(
        self,
        columns: list[str],
        rows: list[list[Any]],
    ) -> None:
        self.columns = columns
        self.rows = rows

    def to_dicts(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row, strict=True)) for row in self.rows]

    def __len__(self) -> int:
        return len(self.rows)


class ReportBuilder:
    """Fluent builder for constructing and executing report queries against Postgres.

    Table and column names come from REPORT_TYPE_REGISTRY (report_registry.py),
    a fixed internal config — safe to interpolate directly into SQL. Filter
    *values* come from the report request body (user input, via `parameters`)
    and are always bound as SQL parameters, never interpolated, so a crafted
    filter value can't break out of its value position. Filter *keys* can't be
    parameterized at all (SQL doesn't support bound column names), so they're
    checked against the same fixed column list before being used.
    """

    def __init__(self) -> None:
        self._source: Literal["postgres"] = "postgres"
        self._filters: dict[str, Any] = {}
        self._aggregations: list[str] = []
        self._table: str = ""
        self._columns: list[str] = ["*"]

    def with_source(self, source: Literal["postgres"]) -> "ReportBuilder":
        self._source = source
        return self

    def with_table(self, table: str) -> "ReportBuilder":
        self._table = table
        return self

    def _quoted_table(self) -> str:
        """Quote each dotted segment — `order` is a reserved SQL keyword, and
        report_registry.py's schema-qualified names (`order.orders`) would
        otherwise fail to parse.
        """
        return ".".join(f'"{part}"' for part in self._table.split("."))

    def with_columns(self, columns: list[str]) -> "ReportBuilder":
        self._columns = columns
        return self

    def with_filters(self, filters: dict[str, Any]) -> "ReportBuilder":
        self._filters = filters
        return self

    def with_aggregations(self, aggs: list[str]) -> "ReportBuilder":
        self._aggregations = aggs
        return self

    def _allowed_filter_keys(self) -> set[str]:
        return {c for c in self._columns if c != "*"} | {"date_range"}

    def build_query(self) -> tuple[str, dict[str, Any]]:
        """Build a parameterized SQL query.

        Returns (query with named `:bind` placeholders, bind parameter dict)
        rather than a plain string — callers must run it through execute(),
        not string-format it further.
        """
        cols = ", ".join(self._columns)
        query = f"SELECT {cols} FROM {self._quoted_table()}"

        allowed = self._allowed_filter_keys()
        conditions: list[str] = []
        params: dict[str, Any] = {}

        for key, value in self._filters.items():
            if key not in allowed or value is None:
                continue

            if key == "date_range":
                date_from, date_to = self._parse_date_range(value)
                if date_from is not None:
                    conditions.append("created_at >= :date_from")
                    params["date_from"] = date_from
                if date_to is not None:
                    conditions.append("created_at <= :date_to")
                    params["date_to"] = date_to
                continue

            if isinstance(value, list):
                placeholders = []
                for i, v in enumerate(value):
                    param_name = f"{key}_{i}"
                    placeholders.append(f":{param_name}")
                    params[param_name] = v
                conditions.append(f"{key} IN ({', '.join(placeholders)})")
            else:
                conditions.append(f"{key} = :{key}")
                params[key] = value

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if self._aggregations:
            safe_aggs = [a for a in self._aggregations if a in allowed]
            if safe_aggs:
                query += " GROUP BY " + ", ".join(safe_aggs)

        return query, params

    @staticmethod
    def _parse_date_range(value: Any) -> tuple[Any, Any]:
        """Accept {"from": ..., "to": ...} or a two-element [from, to] list.

        asyncpg binds timestamptz parameters as native datetime objects, not
        ISO strings — an unparsed string reaches the driver and fails with
        "expected a datetime.date or datetime.datetime instance, got 'str'".
        """
        if isinstance(value, dict):
            raw_from, raw_to = value.get("from"), value.get("to")
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            raw_from, raw_to = value[0], value[1]
        else:
            return None, None
        return ReportBuilder._parse_date(raw_from), ReportBuilder._parse_date(raw_to)

    @staticmethod
    def _parse_date(value: Any) -> datetime | None:
        if value is None or isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    async def execute(self) -> ResultSet:
        """Execute the built query against Postgres and return the results.

        All services share one PostgreSQL instance with per-service schemas
        (see "Детальная архитектура", раздел 1) — reading another service's
        table (order.orders, catalog.products, ...) is a plain cross-schema
        query on this same connection, no replication/ETL involved.
        """
        query, params = self.build_query()
        session_factory = _get_session_factory()
        async with session_factory() as session:
            result = await session.execute(text(query), params)
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchall()]
        return ResultSet(columns=columns, rows=rows)
