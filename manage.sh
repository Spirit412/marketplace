#!/usr/bin/env bash
#
# manage.sh — Marketplace Management Script
# =========================================
# Console menu for managing Multi-Vendor Marketplace services:
#   - Start/stop individual or all services
#   - View logs
#   - Run tests, lint, format, type-check
#   - Database migrations
#   - Health checks
#   - Local development helpers
#
# Usage:
#   ./manage.sh                # Interactive menu
#   ./manage.sh up             # Start all services
#   ./manage.sh down           # Stop all services
#   ./manage.sh test auth      # Run tests for auth-service
#   ./manage.sh lint           # Lint all services
#   ./manage.sh format         # Format all services
#   ./manage.sh health         # Health check all services
#   ./manage.sh migrate auth   # Run migrations for auth-service
#   ./manage.sh shell auth     # Open shell in auth-service container
#
# Requirements:
#   - docker compose
#   - python 3.12
#   - poetry (for local dev commands)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICES=(
    "mp-auth-service"
    "mp-catalog-service"
    "mp-order-service"
    "mp-payment-service"
    "mp-notification-service"
    "mp-scheduler-service"
    "mp-report-service"
    "mp-inventory-service"
    "mp-dictionary-service"
    "mp-import-service"
)

# ─── Colors ─────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ─── Helpers ────────────────────────────────────────────────
info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*"; }

divider() {
    echo -e "${CYAN}────────────────────────────────────────────────────${NC}"
}

# ─── Commands ───────────────────────────────────────────────

cmd_up() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        info "Starting $service..."
        (cd "$SCRIPT_DIR/$service" && docker compose up -d)
    else
        info "Starting all services..."
        for svc in "${SERVICES[@]}"; do
            if [[ -f "$SCRIPT_DIR/$svc/docker-compose.yml" ]]; then
                info "  Starting $svc..."
                (cd "$SCRIPT_DIR/$svc" && docker compose up -d) &
            fi
        done
        wait
        ok "All services started"
    fi
}

cmd_down() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        info "Stopping $service..."
        (cd "$SCRIPT_DIR/$service" && docker compose down)
    else
        info "Stopping all services..."
        for svc in "${SERVICES[@]}"; do
            if [[ -f "$SCRIPT_DIR/$svc/docker-compose.yml" ]]; then
                (cd "$SCRIPT_DIR/$svc" && docker compose down) &
            fi
        done
        wait
        ok "All services stopped"
    fi
}

cmd_restart() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        cmd_down "$service"
        cmd_up "$service"
    else
        cmd_down
        cmd_up
    fi
}

cmd_logs() {
    local service="${1:-}"
    if [[ -z "$service" ]]; then
        service="${SERVICES[0]}"
    fi
    (cd "$SCRIPT_DIR/$service" && docker compose logs -f)
}

cmd_status() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        (cd "$SCRIPT_DIR/$service" && docker compose ps)
    else
        divider
        printf "%-28s %s\n" "SERVICE" "STATUS"
        divider
        for svc in "${SERVICES[@]}"; do
            if [[ -f "$SCRIPT_DIR/$svc/docker-compose.yml" ]]; then
                local status
                status=$(cd "$SCRIPT_DIR/$svc" && docker compose ps --format json 2>/dev/null | python3 -c "import sys,json; d=[json.loads(l) for l in sys.stdin]; print('up' if any(x.get('State','')=='running' for x in d) else 'down')" 2>/dev/null || echo "down")
                if [[ "$status" == "up" ]]; then
                    printf "%-28s ${GREEN}%s${NC}\n" "$svc" "UP"
                else
                    printf "%-28s ${RED}%s${NC}\n" "$svc" "DOWN"
                fi
            else
                printf "%-28s ${YELLOW}%s${NC}\n" "$svc" "no config"
            fi
        done
        divider
    fi
}

cmd_build() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        info "Building $service..."
        (cd "$SCRIPT_DIR/$service" && docker compose build)
    else
        info "Building all services..."
        for svc in "${SERVICES[@]}"; do
            if [[ -f "$SCRIPT_DIR/$svc/docker-compose.yml" ]]; then
                (cd "$SCRIPT_DIR/$svc" && docker compose build) &
            fi
        done
        wait
        ok "All services built"
    fi
}

cmd_test() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        info "Running tests for $service..."
        (cd "$SCRIPT_DIR/$service" && poetry run pytest tests/ -v)
    else
        info "Running all tests..."
        local failed=()
        for svc in "${SERVICES[@]}"; do
            if [[ -d "$SCRIPT_DIR/$svc/tests" ]]; then
                info "  $svc..."
                (cd "$SCRIPT_DIR/$svc" && poetry run pytest tests/ -v) || failed+=("$svc")
            fi
        done
        if [[ ${#failed[@]} -gt 0 ]]; then
            err "Failed services: ${failed[*]}"
        else
            ok "All tests passed"
        fi
    fi
}

cmd_lint() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        info "Linting $service..."
        (cd "$SCRIPT_DIR/$service" && ruff check src/ && ruff format --check src/ && mypy src/)
    else
        info "Linting all services..."
        for svc in "${SERVICES[@]}"; do
            if [[ -f "$SCRIPT_DIR/$svc/pyproject.toml" ]]; then
                info "  $svc..."
                (cd "$SCRIPT_DIR/$svc" && ruff check src/ && ruff format --check src/)
            fi
        done
        ok "Lint complete"
    fi
}

cmd_format() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        info "Formatting $service..."
        (cd "$SCRIPT_DIR/$service" && ruff format src/ && ruff check --fix src/)
    else
        info "Formatting all services..."
        for svc in "${SERVICES[@]}"; do
            if [[ -f "$SCRIPT_DIR/$svc/pyproject.toml" ]]; then
                (cd "$SCRIPT_DIR/$svc" && ruff format src/ && ruff check --fix src/) &
            fi
        done
        wait
        ok "Format complete"
    fi
}

cmd_typecheck() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        info "Type-checking $service..."
        (cd "$SCRIPT_DIR/$service" && mypy src/)
    else
        info "Type-checking all services..."
        for svc in "${SERVICES[@]}"; do
            if [[ -f "$SCRIPT_DIR/$svc/pyproject.toml" ]]; then
                info "  $svc..."
                (cd "$SCRIPT_DIR/$svc" && mypy src/)
            fi
        done
        ok "Type-check complete"
    fi
}

cmd_migrate() {
    local service="${1:-}"
    if [[ -z "$service" ]]; then
        err "Usage: ./manage.sh migrate <service>"
        return 1
    fi
    if [[ ! -f "$SCRIPT_DIR/$service/alembic.ini" ]]; then
        warn "$service has no alembic.ini — skipping"
        return
    fi
    info "Running migrations for $service..."
    (cd "$SCRIPT_DIR/$service" && poetry run alembic upgrade head)
    ok "Migrations complete for $service"
}

cmd_migrate_all() {
    for svc in "${SERVICES[@]}"; do
        if [[ -f "$SCRIPT_DIR/$svc/alembic.ini" ]]; then
            info "Migrating $svc..."
            (cd "$SCRIPT_DIR/$svc" && poetry run alembic upgrade head) || warn "$svc migration failed"
        fi
    done
    ok "All migrations done"
}

cmd_seed() {
    local service="${1:-}"
    if [[ -z "$service" ]]; then
        err "Usage: ./manage.sh seed <service>"
        return 1
    fi

    local container="mp-${service}-service"
    if ! docker ps --format '{{.Names}}' | grep -qx "$container"; then
        err "$container is not running — start it first (./manage.sh up $service)"
        return 1
    fi

    local modules=()
    case "$service" in
        auth)         modules=("src.seeds.rbac") ;;
        catalog)      modules=("src.seeds.catalog" "src.seeds.products") ;;
        dictionary)   modules=("src.seeds.dictionary") ;;
        inventory)    modules=("src.seeds.stock") ;;
        notification) modules=("src.seeds.seed_templates") ;;
        report)       modules=("src.seeds.seed_report_templates") ;;
        *)
            warn "$service has no seed script — skipping"
            return
            ;;
    esac

    for module in "${modules[@]}"; do
        info "Seeding $service ($module)..."
        docker exec "$container" sh -c "cd /usr/src && python -m $module" || {
            err "Seed failed for $service ($module)"
            return 1
        }
    done
    ok "Seed complete for $service"
}

cmd_seed_all() {
    # Order matters: catalog products look up the seller in auth.users,
    # inventory stock looks up products in catalog.products by sku.
    for svc in auth dictionary catalog inventory notification report; do
        cmd_seed "$svc" || warn "$svc seed failed — continuing"
    done
    ok "All seeds done"
}

cmd_health() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        local port
        port=$(grep -oP 'ports:\s*-\s*"\K\d+' "$SCRIPT_DIR/$service/docker-compose.yml" | head -1 || echo "")
        if [[ -n "$port" ]]; then
            info "Health check $service (port $port)..."
            curl -sf "http://localhost:$port/health" | python3 -m json.tool 2>/dev/null || err "Health check failed for $service"
        else
            warn "Cannot determine port for $service"
        fi
    else
        divider
        printf "%-28s %s\n" "SERVICE" "HEALTH"
        divider
        for svc in "${SERVICES[@]}"; do
            local port
            port=$(grep -oP 'ports:\s*-\s*"\K\d+' "$SCRIPT_DIR/$svc/docker-compose.yml" 2>/dev/null | head -1 || echo "")
            if [[ -n "$port" ]]; then
                if curl -sf "http://localhost:$port/health" -o /dev/null 2>/dev/null; then
                    printf "%-28s ${GREEN}%s${NC}\n" "$svc" "healthy"
                else
                    printf "%-28s ${RED}%s${NC}\n" "$svc" "unhealthy"
                fi
            else
                printf "%-28s ${YELLOW}%s${NC}\n" "$svc" "no port"
            fi
        done
        divider
    fi
}

cmd_shell() {
    local service="${1:-}"
    if [[ -z "$service" ]]; then
        err "Usage: ./manage.sh shell <service>"
        return 1
    fi
    (cd "$SCRIPT_DIR/$service" && docker compose exec "$service" sh)
}

cmd_install() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        info "Installing dependencies for $service..."
        (cd "$SCRIPT_DIR/$service" && poetry install)
    else
        info "Installing all dependencies..."
        for svc in "${SERVICES[@]}"; do
            if [[ -f "$SCRIPT_DIR/$svc/pyproject.toml" ]]; then
                info "  $svc..."
                (cd "$SCRIPT_DIR/$svc" && poetry install) &
            fi
        done
        wait
        ok "All dependencies installed"
    fi
}

cmd_clean() {
    warn "This will remove all containers, volumes, and images."
    read -rp "Are you sure? [y/N] " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        info "Cancelled"
        return
    fi
    cmd_down
    for svc in "${SERVICES[@]}"; do
        if [[ -f "$SCRIPT_DIR/$svc/docker-compose.yml" ]]; then
            (cd "$SCRIPT_DIR/$svc" && docker compose down -v --rmi local) 2>/dev/null || true
        fi
    done
    ok "Cleaned up"
}

cmd_dev() {
    local service="${1:-}"
    if [[ -z "$service" ]]; then
        service="mp-auth-service"
    fi
    info "Starting $service in dev mode..."
    (cd "$SCRIPT_DIR/$service" && docker compose up -d postgres redis 2>/dev/null || true)
    sleep 2
    info "Running migrations..."
    (cd "$SCRIPT_DIR/$service" && poetry run alembic upgrade head)
    info "Starting uvicorn with reload..."
    (cd "$SCRIPT_DIR/$service" && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8110 --reload)
}

# ─── Interactive Menu ───────────────────────────────────────

show_menu() {
    clear
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}     ${GREEN}Multi-Vendor Marketplace Manager${NC}            ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${YELLOW}Services:${NC}"
    echo -e "    ${GREEN}1)${NC}  Start all services       ${GREEN}2)${NC}  Stop all services"
    echo -e "    ${GREEN}3)${NC}  Restart all services     ${GREEN}4)${NC}  Status"
    echo -e "    ${GREEN}5)${NC}  Build all services       ${GREEN}6)${NC}  Start specific service"
    echo ""
    echo -e "  ${YELLOW}Development:${NC}"
    echo -e "    ${GREEN}7)${NC}  Install dependencies     ${GREEN}8)${NC}  Run all tests"
    echo -e "    ${GREEN}9)${NC}  Lint all services        ${GREEN}10)${NC} Format all services"
    echo -e "    ${GREEN}11)${NC} Type-check all           ${GREEN}12)${NC} Run specific tests"
    echo ""
    echo -e "  ${YELLOW}Operations:${NC}"
    echo -e "    ${GREEN}13)${NC} Health check all         ${GREEN}14)${NC} Migrate all"
    echo -e "    ${GREEN}15)${NC} View logs               ${GREEN}16)${NC} Shell into service"
    echo -e "    ${GREEN}17)${NC} Dev mode (auth-service)  ${GREEN}18)${NC} Clean all"
    echo -e "    ${GREEN}19)${NC} Seed all demo data"
    echo ""
    echo -e "  ${RED}0)${NC}  Exit"
    echo ""
}

interactive() {
    while true; do
        show_menu
        read -rp "  Select option [0-19]: " choice
        case "$choice" in
            1)  cmd_up ;;
            2)  cmd_down ;;
            3)  cmd_restart ;;
            4)  cmd_status ;;
            5)  cmd_build ;;
            6)  read -rp "  Service name: " svc; cmd_up "$svc" ;;
            7)  cmd_install ;;
            8)  cmd_test ;;
            9)  cmd_lint ;;
            10) cmd_format ;;
            11) cmd_typecheck ;;
            12) read -rp "  Service name: " svc; cmd_test "$svc" ;;
            13) cmd_health ;;
            14) cmd_migrate_all ;;
            15) read -rp "  Service name: " svc; cmd_logs "$svc" ;;
            16) read -rp "  Service name: " svc; cmd_shell "$svc" ;;
            17) cmd_dev "mp-auth-service" ;;
            18) cmd_clean ;;
            19) cmd_seed_all ;;
            0)  info "Goodbye!"; exit 0 ;;
            *)  warn "Invalid option" ;;
        esac
        echo ""
        read -rp "  Press Enter to continue..."
    done
}

# ─── CLI dispatcher ─────────────────────────────────────────
dispatch() {
    case "${1:-}" in
        up)         shift; cmd_up "${1:-}" ;;
        down)       shift; cmd_down "${1:-}" ;;
        restart)    shift; cmd_restart "${1:-}" ;;
        status)     shift; cmd_status "${1:-}" ;;
        build)      shift; cmd_build "${1:-}" ;;
        test)       shift; cmd_test "${1:-}" ;;
        lint)       shift; cmd_lint "${1:-}" ;;
        format)     shift; cmd_format "${1:-}" ;;
        typecheck)  shift; cmd_typecheck "${1:-}" ;;
        migrate)    shift; cmd_migrate "${1:-}" ;;
        migrate-all) cmd_migrate_all ;;
        seed)       shift; cmd_seed "${1:-}" ;;
        seed-all)   cmd_seed_all ;;
        health)     shift; cmd_health "${1:-}" ;;
        logs)       shift; cmd_logs "${1:-}" ;;
        shell)      shift; cmd_shell "${1:-}" ;;
        install)    shift; cmd_install "${1:-}" ;;
        clean)      cmd_clean ;;
        dev)        shift; cmd_dev "${1:-}" ;;
        help|--help|-h)
            echo "Usage: ./manage.sh [command] [service]"
            echo ""
            echo "Commands:"
            echo "  up [svc]       Start service(s)"
            echo "  down [svc]     Stop service(s)"
            echo "  restart [svc]  Restart service(s)"
            echo "  status [svc]   Show status"
            echo "  build [svc]    Build Docker images"
            echo "  test [svc]     Run tests"
            echo "  lint [svc]     Lint code (ruff)"
            echo "  format [svc]   Format code (ruff)"
            echo "  typecheck [svc] Type-check (mypy)"
            echo "  migrate <svc>  Run DB migrations"
            echo "  migrate-all    Run all migrations"
            echo "  seed <svc>     Seed demo data (auth/catalog/dictionary/inventory/notification/report)"
            echo "  seed-all       Seed all, in dependency order"
            echo "  health [svc]   Health check via HTTP"
            echo "  logs [svc]     View Docker logs"
            echo "  shell <svc>    Open shell in container"
            echo "  install [svc]  Install Python deps"
            echo "  clean          Remove all containers/volumes"
            echo "  dev [svc]      Dev mode (auto-reload)"
            echo ""
            echo "Services: ${SERVICES[*]}"
            ;;
        *)  interactive ;;
    esac
}

dispatch "$@"
