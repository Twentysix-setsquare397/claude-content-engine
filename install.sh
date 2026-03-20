#!/usr/bin/env bash
#
# claude-content-engine installer
# Install, update, or uninstall the claude-content-engine for Claude Code.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/quionie/claude-content-engine/main/install.sh | bash
#   ./install.sh --update
#   ./install.sh --uninstall
#

set -euo pipefail

# --- Configuration ---
REPO_URL="https://github.com/quionie/claude-content-engine.git"
PACK_NAME="claude-content-engine"
CLAUDE_DIR="${HOME}/.claude"
PLUGINS_DIR="${CLAUDE_DIR}/plugins"
MARKETPLACES_DIR="${PLUGINS_DIR}/marketplaces"
INSTALL_DIR="${MARKETPLACES_DIR}/${PACK_NAME}"
KNOWN_MARKETPLACES="${PLUGINS_DIR}/known_marketplaces.json"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Helpers ---
info()    { printf "${BLUE}[info]${NC}  %s\n" "$1"; }
success() { printf "${GREEN}[ok]${NC}    %s\n" "$1"; }
warn()    { printf "${YELLOW}[warn]${NC}  %s\n" "$1"; }
error()   { printf "${RED}[error]${NC} %s\n" "$1" >&2; }

check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        error "$1 is required but not installed."
        exit 1
    fi
}

# --- Pre-flight checks ---
preflight() {
    check_dependency git
    check_dependency jq

    if [ ! -d "${CLAUDE_DIR}" ]; then
        error "Claude Code config directory not found at ${CLAUDE_DIR}"
        error "Is Claude Code installed? Visit https://claude.ai/code to get started."
        exit 1
    fi

    # Create plugins directories if they don't exist
    mkdir -p "${MARKETPLACES_DIR}"

    # Initialize known_marketplaces.json if it doesn't exist
    if [ ! -f "${KNOWN_MARKETPLACES}" ]; then
        printf '{}' > "${KNOWN_MARKETPLACES}"
    fi

    # Validate known_marketplaces.json is valid JSON
    if ! jq empty "${KNOWN_MARKETPLACES}" 2>/dev/null; then
        error "${KNOWN_MARKETPLACES} is not valid JSON. Please fix it manually."
        exit 1
    fi
}

# --- Install ---
do_install() {
    if [ -d "${INSTALL_DIR}" ]; then
        warn "claude-content-engine is already installed at ${INSTALL_DIR}"
        info "Run with --update to pull the latest version."
        exit 0
    fi

    info "Cloning claude-content-engine..."
    git clone --depth 1 --single-branch "${REPO_URL}" "${INSTALL_DIR}" 2>/dev/null

    if [ ! -d "${INSTALL_DIR}/.claude-plugin" ]; then
        error "Clone succeeded but plugin structure is invalid. Cleaning up."
        rm -rf "${INSTALL_DIR}"
        exit 1
    fi

    register_marketplace

    printf "\n"
    success "claude-content-engine installed successfully!"
    printf "\n"
    list_skills
    printf "\n"
    info "Restart Claude Code to activate your new skills."
    info "To update later: ${BOLD}./install.sh --update${NC} (or re-run this script with --update)"
    info "To uninstall:    ${BOLD}./install.sh --uninstall${NC}"
}

# --- Update ---
do_update() {
    if [ ! -d "${INSTALL_DIR}" ]; then
        error "claude-content-engine is not installed. Run without flags to install."
        exit 1
    fi

    info "Updating claude-content-engine..."
    git -C "${INSTALL_DIR}" fetch --depth 1 origin main 2>/dev/null
    git -C "${INSTALL_DIR}" reset --hard origin/main 2>/dev/null

    printf "\n"
    success "claude-content-engine updated to the latest version!"
    printf "\n"
    list_skills
    printf "\n"
    info "Restart Claude Code to pick up changes."
}

# --- Uninstall ---
do_uninstall() {
    if [ ! -d "${INSTALL_DIR}" ]; then
        warn "claude-content-engine is not installed. Nothing to do."
        exit 0
    fi

    info "Removing claude-content-engine..."
    rm -rf "${INSTALL_DIR}"

    # Remove from known_marketplaces.json
    if [ -f "${KNOWN_MARKETPLACES}" ] && jq -e ".\"${PACK_NAME}\"" "${KNOWN_MARKETPLACES}" > /dev/null 2>&1; then
        local tmp
        tmp=$(mktemp)
        jq "del(.\"${PACK_NAME}\")" "${KNOWN_MARKETPLACES}" > "${tmp}" && mv "${tmp}" "${KNOWN_MARKETPLACES}"
    fi

    printf "\n"
    success "claude-content-engine has been uninstalled."
    info "Restart Claude Code to complete removal."
}

# --- Register in known_marketplaces.json ---
register_marketplace() {
    local tmp
    tmp=$(mktemp)
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

    jq --arg name "${PACK_NAME}" \
       --arg loc "${INSTALL_DIR}" \
       --arg ts "${timestamp}" \
       --arg repo "${REPO_URL}" \
       '.[$name] = {
         "source": { "source": "github", "repo": $repo },
         "installLocation": $loc,
         "lastUpdated": $ts
       }' "${KNOWN_MARKETPLACES}" > "${tmp}" && mv "${tmp}" "${KNOWN_MARKETPLACES}"

    success "Registered in Claude Code plugin system."
}

# --- List installed skills ---
list_skills() {
    printf "${BOLD}Installed skills:${NC}\n"
    local count=0
    if [ -d "${INSTALL_DIR}/skills" ]; then
        for skill_dir in "${INSTALL_DIR}"/skills/*/; do
            if [ -f "${skill_dir}SKILL.md" ]; then
                local skill_name
                skill_name=$(basename "${skill_dir}")
                printf "  ${GREEN}✓${NC} %s\n" "${skill_name}"
                count=$((count + 1))
            fi
        done
    fi
    printf "\n  ${BOLD}%d skills ready to use.${NC}\n" "${count}"
}

# --- Main ---
main() {
    printf "\n"
    printf "${BOLD}  claude-content-engine${NC} installer\n"
    printf "  ─────────────────────────────\n"
    printf "\n"

    preflight

    case "${1:-}" in
        --update|-u)
            do_update
            ;;
        --uninstall|--remove|-r)
            do_uninstall
            ;;
        --help|-h)
            printf "Usage: install.sh [OPTIONS]\n\n"
            printf "Options:\n"
            printf "  (none)        Install claude-content-engine\n"
            printf "  --update      Update to the latest version\n"
            printf "  --uninstall   Remove claude-content-engine\n"
            printf "  --help        Show this help message\n"
            ;;
        "")
            do_install
            ;;
        *)
            error "Unknown option: $1"
            printf "Run with --help for usage information.\n"
            exit 1
            ;;
    esac
}

main "$@"
