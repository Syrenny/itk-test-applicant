PROJECT ?= itk-test-applicant
COMPOSE := docker compose -p $(PROJECT)
FILES := -f docker/compose.yml -f docker/compose.infra.yml
FILES_INFRA := -f docker/compose.infra.yml

up:
	$(COMPOSE) $(FILES) --env-file docker/.env up -d --build

down:
	$(COMPOSE) $(FILES) down --remove-orphans

ps:
	$(COMPOSE) $(FILES) ps

logs:
	$(COMPOSE) $(FILES) logs -f --tail=100 $(service)

# --- Infra only (infra) ---

up-infra:
	$(COMPOSE) $(FILES_INFRA) --env-file docker/.env up -d --build

down-infra:
	$(COMPOSE) $(FILES_INFRA) down --remove-orphans

ps-infra:
	$(COMPOSE) $(FILES_INFRA) ps

logs-infra:
	# pass SERVICE=name to tail a single infra service
	$(COMPOSE) $(FILES_INFRA) logs -f --tail=100 $(SERVICE)

# --- Database cleanup ---
postgres-clean:
	@echo "Removing Postgres data volume $(PROJECT)_postgres-data ..."
	docker volume rm $(PROJECT)_postgres-data || true

.PHONY: help up down ps logs up-infra down-infra ps-infra logs-infra postgres-clean


help:
	@echo "Makefile targets:"
	@echo "  make up             # start app + infra (use SERVICE=<name> to limit logs)"
	@echo "  make down           # stop app + infra"
	@echo "  make ps             # docker compose ps (app + infra)"
	@echo "  make logs           # follow logs (app + infra) (SERVICE=...)"
	@echo "  make up-infra       # start infra only"
	@echo "  make down-infra     # stop infra only"
	@echo "  make ps-infra       # docker compose ps for infra"
	@echo "  make logs-infra     # follow infra logs (SERVICE=...)"
	@echo "  make postgres-clean # remove postgres data volume"
	@echo ""
	@echo "Environment overrides: PROJECT, ENV_FILE, DOCKER_COMPOSE, SERVICE"
