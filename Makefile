# Reproducible build of the ASLO-SIL 2026 landscape analysis

.PHONY: all install audit inventory landscape fticr clean

all: landscape fticr

install:
	pip install -r requirements.txt

audit:
	python scripts/01_audit_capture.py

inventory:
	python scripts/02_complete_inventory_and_prune.py

landscape:
	python scripts/03_landscape_analysis.py

fticr:
	python scripts/fticr/01_venue_breakdown.py
	python scripts/fticr/02_comprehensive_subdiscipline.py
	python scripts/fticr/habitat_coarse.py

clean:
	rm -rf output/charts/*.png output/tables/*.json output/tables/*.csv

# Rebuild figures from cached data (no network)
figures-only:
	python scripts/03_landscape_analysis.py
