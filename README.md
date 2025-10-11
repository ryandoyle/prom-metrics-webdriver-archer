# LTE Metrics Exporter for Prometheus

This project provides a Prometheus metrics exporter for LTE signal metrics. It uses Selenium WebDriver to scrape LTE signal data from an TP-Link Archer MR600 and exposes it as Prometheus metrics.

## Features

- **Prometheus metrics endpoint** at `/metrics`
- **Automated scraping** of LTE signal metrics every 60 seconds
- **Exposed metrics**:
  - `lte_rsrp_dbm`: LTE Reference Signal Received Power in dBm
  - `lte_rsrq_db`: LTE Reference Signal Received Quality in dB
  - `lte_snr_db`: LTE Signal to Noise Ratio in dB
  - `signal_strength_percent`: Signal Strength percentage
  - `lte_scrape_success`: Whether the last scrape was successful (1=success, 0=failure)
  - `lte_scrape_duration_seconds`: Duration of the last scrape in seconds
  - `lte_last_successful_scrape_timestamp`: Unix timestamp of the last successful scrape
- **Health check endpoint** at `/health`
- **Containerized** for easy deployment

## Quick Start with Docker Compose (Recommended)

1. Set your admin password as an environment variable:

```bash
export ADMIN_PASS='your_password_here'
export LOGIN_URL='192.168.1.1'
```

2. Start the metrics server:

```bash
docker-compose up --build -d
```

3. Access the metrics endpoint:

```bash
curl http://localhost:8000/metrics
```

4. Check the health status:

```bash
curl http://localhost:8000/health
```

## Configuration

### Environment Variables

- `LOGIN_URL`: URL of the device web interface (eg: `192.168.1.1`)
- `ADMIN_PASS`: Admin password for the device (required)
- `PORT`: Port for the metrics server (default: `8000`)

### Customizing the URL

Edit the `LOGIN_URL` in `docker-compose.yml` or pass it as an environment variable:

```bash
docker-compose up --build -d -e LOGIN_URL=192.168.50.1
```

## Prometheus Configuration

Add the following scrape config to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'lte-metrics'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 60s
```

## Metrics Endpoint

The `/metrics` endpoint exposes data in Prometheus format:

```
# HELP lte_rsrp_dbm LTE Reference Signal Received Power in dBm
# TYPE lte_rsrp_dbm gauge
lte_rsrp_dbm -89.0

# HELP lte_rsrq_db LTE Reference Signal Received Quality in dB
# TYPE lte_rsrq_db gauge
lte_rsrq_db -11.0

# HELP lte_snr_db LTE Signal to Noise Ratio in dB
# TYPE lte_snr_db gauge
lte_snr_db 14.0

# HELP signal_strength_percent Signal Strength percentage
# TYPE signal_strength_percent gauge
signal_strength_percent 100.0

# HELP lte_scrape_success Whether the last scrape was successful (1=success, 0=failure)
# TYPE lte_scrape_success gauge
lte_scrape_success 1.0

# HELP lte_scrape_duration_seconds Duration of the last scrape in seconds
# TYPE lte_scrape_duration_seconds gauge
lte_scrape_duration_seconds 15.234

# HELP lte_last_successful_scrape_timestamp Unix timestamp of the last successful scrape
# TYPE lte_last_successful_scrape_timestamp gauge
lte_last_successful_scrape_timestamp 1736593241.0
```

## Running Locally (Without Docker)

### Prerequisites

- Python 3.6 or higher
- Chrome browser installed
- ChromeDriver (Selenium will manage this automatically with Selenium 4+)

### Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Usage

1. Set the required environment variables:

```bash
export LOGIN_URL='192.168.1.1'
export ADMIN_PASS='your_password_here'
```

2. Run the metrics server:

```bash
python metrics_server.py
```

3. Access the metrics endpoint:

```bash
curl http://localhost:8000/metrics
```

## How It Works

The metrics server:
1. Starts a Flask web server on port 8000
2. Launches a background thread that scrapes metrics every 60 seconds
3. Uses Selenium WebDriver to:
   - Navigate to the device web interface
   - Log in with the provided credentials
   - Navigate to the advanced menu
   - Extract LTE signal metrics
4. Exposes the metrics in Prometheus format at `/metrics`
5. Updates the metrics on each successful scrape

## Standalone WebDriver Script

The original `webdriver_login.py` script is still available for standalone use:

```bash
export LOGIN_URL='192.168.1.1'
export ADMIN_PASS='your_password_here'
python webdriver_login.py
```

This will perform a one-time login and metric extraction without running the metrics server.

## Monitoring and Alerting

You can create Prometheus alerts based on the metrics:

```yaml
groups:
  - name: lte_alerts
    rules:
      - alert: LowSignalStrength
        expr: signal_strength_percent < 50
        for: 5m
        annotations:
          summary: "LTE signal strength is low"
          
      - alert: ScrapeFailed
        expr: lte_scrape_success == 0
        for: 5m
        annotations:
          summary: "LTE metrics scrape failed"
```

## Troubleshooting

### Check container logs

```bash
docker-compose logs -f
```

### Verify environment variables

```bash
docker-compose config
```

### Test the scrape manually

```bash
docker-compose exec lte-metrics python webdriver_login.py
```

## Notes

- The scraper runs every 60 seconds by default
- Uses headless Chrome for automation
- Runs with host network mode to access local network IPs
- Metrics are preserved between scrapes (they don't reset to 0)
- The `lte_last_successful_scrape_timestamp` metric helps monitor scrape freshness
