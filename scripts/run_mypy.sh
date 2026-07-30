#!/usr/bin/env bash
# Run mypy inside each service container, where that service's dependencies
# are installed. Services that are not running are skipped, not failed —
# the hook must stay usable without the whole stack up.
set -uo pipefail

SERVICES=(auth catalog order payment notification scheduler report inventory dictionary import)
failed=()
skipped=()

for svc in "${SERVICES[@]}"; do
  container="mp-${svc}-service"
  if ! docker ps --format '{{.Names}}' | grep -qx "$container"; then
    skipped+=("$svc")
    continue
  fi
  if ! docker exec -w /usr/src "$container" python -m mypy 2>&1 | tail -20; then
    failed+=("$svc")
  fi
done

[ ${#skipped[@]} -gt 0 ] && echo "mypy skipped (container not running): ${skipped[*]}"

if [ ${#failed[@]} -gt 0 ]; then
  echo "mypy failed: ${failed[*]}"
  exit 1
fi
exit 0
