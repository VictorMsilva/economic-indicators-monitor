# economic-indicators-monitor
Automated pipeline that ingests Brazilian economic indicators (Selic, IPCA, exchange rates, GDP) from Bacen’s SGS API, applies Data Quality checks, stores in a Medallion architecture (Bronze/Silver/Gold) with Delta Lake for versioning, and delivers curated data for dashboards, alerts, and predictive models.
