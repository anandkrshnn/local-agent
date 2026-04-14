# LocalAgent Makefile - Deployment and Development Helpers

IMAGE_NAME = anandkrshnn/local-agent
VERSION = v0.6.0

.PHONY: build run stop clean test logs shell help

help:
	@echo "LocalAgent v0.6.0 Makefile"
	@echo "Usage:"
	@echo "  make build    - Build the production Docker image"
	@echo "  make run      - Start the agent using docker-compose"
	@echo "  make stop     - Stop the agent"
	@echo "  make clean    - Remove the container and volumes"
	@echo "  make test     - Run the smoke test"
	@echo "  make logs     - View container logs"
	@echo "  make shell    - Open a shell inside the container"

build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

run:
	docker-compose up -d

stop:
	docker-compose stop

clean:
	docker-compose down -v

test:
	python tests/smoke_test.py

logs:
	docker logs -f local-agent

shell:
	docker exec -it local-agent /bin/bash
