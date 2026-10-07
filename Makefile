up:
	docker compose up -d postgres

prepare:
	python scripts/run_all.py

api:
	uvicorn app.main:app --reload

dashboard:
	streamlit run dashboard/app.py

test:
	pytest

down:
	docker compose down
