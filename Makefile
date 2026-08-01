.PHONY: demo test backtest fit predict list install clean

demo:
	python -m olbg_roi init-demo

test:
	python -m unittest discover -s tests -v

backtest:
	python -m olbg_roi backtest --sport tennis --data data/raw/tennis_demo.csv

fit:
	python -m olbg_roi fit --sport tennis --data data/raw/tennis_demo.csv --out models

predict:
	python -m olbg_roi predict --sport tennis --model models/elo_tennis.json \
		--fixtures data/raw/tennis_demo_fixtures.csv

list:
	python -m olbg_roi list-sports

install:
	python -m pip install -e .

clean:
	rm -rf models reports data/predictions __pycache__
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
