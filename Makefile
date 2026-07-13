.PHONY: open-data audit

open-data:
	python3 ocr/compile.py
	python3 docs/compile17.py
	python3 scripts/build_open_data.py --check

audit:
	python3 scripts/build_open_data.py --check
