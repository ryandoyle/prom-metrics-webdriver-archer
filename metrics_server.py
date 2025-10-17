#!/usr/bin/env python3
"""
Prometheus metrics server for LTE signal metrics.
Exposes /metrics endpoint that can be scraped by Prometheus.
"""

import os
import sys
import time
import logging
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest, REGISTRY
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create Flask app
app = Flask(__name__)

# Define Prometheus metrics
lte_rsrp_gauge = Gauge('lte_rsrp_dbm', 'LTE Reference Signal Received Power in dBm')
lte_rsrq_gauge = Gauge('lte_rsrq_db', 'LTE Reference Signal Received Quality in dB')
lte_snr_gauge = Gauge('lte_snr_db', 'LTE Signal to Noise Ratio in dB')
signal_strength_gauge = Gauge('lte_signal_strength_percent', 'Signal Strength percentage')
scrape_success_gauge = Gauge('lte_scrape_success', 'Whether the last scrape was successful (1=success, 0=failure)')
scrape_duration_gauge = Gauge('lte_scrape_duration_seconds', 'Duration of the last scrape in seconds')
last_successful_scrape_gauge = Gauge('lte_last_successful_scrape_timestamp', 'Unix timestamp of the last successful scrape')



def parse_metric_value(value_str, unit=''):
    """
    Parse metric value string and extract numeric value.
    Examples: '-89dBm' -> -89, '100%' -> 100, '14.0dB' -> 14.0
    """
    if not value_str or value_str == '--':
        return None
    
    # Remove common units
    cleaned = value_str.replace('dBm', '').replace('dB', '').replace('%', '').strip()
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_metrics():
    """
    Scrape LTE metrics using Selenium WebDriver.
    Returns dict of metrics or None on failure.
    """
    start_time = time.time()
    
    # Get URL from environment variable
    url = os.getenv('LOGIN_URL')
    if not url:
        logger.error("LOGIN_URL environment variable is not set")
        return None
    
    # Get password from environment variable
    password = os.getenv('ADMIN_PASS')
    if not password:
        logger.error("ADMIN_PASS environment variable is not set")
        return None
    
    # Add http:// if not present
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
    
    logger.info(f"Scraping metrics from: {url}")
    
    # Initialize the WebDriver with headless Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to the URL
        driver.get(url)
        
        # Wait for the password element to be present
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pc-login-password"))
        )
        
        # Enter the password
        password_field.send_keys(password)
        
        # Wait for and click the login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pc-login-btn"))
        )
        login_button.click()
        
        # Check for warning message after login
        try:
            warning_div = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "grid-warning-msg"))
            )
            confirm_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "confirm-yes"))
            )
            confirm_button.click()
        except TimeoutException:
            pass  # No warning message
        
        # Wait for and click the advanced menu item
        advanced_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "advanced"))
        )
        advanced_item.click()
        
        # Wait for lteRsrp value to be populated
        def value_is_not_placeholder(driver):
            element = driver.find_element(By.ID, "lteRsrp")
            value = element.get_attribute("value")
            return value and value != "--"
        
        WebDriverWait(driver, 30).until(value_is_not_placeholder)
        
        # Get all metric values
        lte_rsrp_input = driver.find_element(By.ID, "lteRsrp")
        lte_rsrp_value = lte_rsrp_input.get_attribute("value")
        
        signal_strength_input = driver.find_element(By.ID, "signalStrength")
        signal_strength_value = signal_strength_input.get_attribute("value")
        
        lte_rsrq_input = driver.find_element(By.ID, "lteRsrq")
        lte_rsrq_value = lte_rsrq_input.get_attribute("value")
        
        lte_snr_input = driver.find_element(By.ID, "lteSnr")
        lte_snr_value = lte_snr_input.get_attribute("value")
        
        # Parse the values
        metrics = {
            'lte_rsrp': parse_metric_value(lte_rsrp_value),
            'lte_rsrq': parse_metric_value(lte_rsrq_value),
            'lte_snr': parse_metric_value(lte_snr_value),
            'signal_strength': parse_metric_value(signal_strength_value)
        }
        
        duration = time.time() - start_time
        logger.info(f"Metrics scraped successfully in {duration:.2f}s:")
        logger.info(f"  lteRsrp: {lte_rsrp_value}")
        logger.info(f"  lteRsrq: {lte_rsrq_value}")
        logger.info(f"  lteSnr: {lte_snr_value}")
        logger.info(f"  signalStrength: {signal_strength_value}")
        
        return metrics, duration
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error scraping metrics: {str(e)}")
        return None, duration
    finally:
        driver.quit()


@app.route('/metrics')
def metrics():
    """
    Prometheus metrics endpoint.
    Scrapes metrics on-demand and returns them in Prometheus text format.
    """
    try:
        result = scrape_metrics()
        
        if result is None:
            scrape_success_gauge.set(0)
        else:
            metrics_data, duration = result
            scrape_duration_gauge.set(duration)
            
            # Update gauges with new values
            if metrics_data['lte_rsrp'] is not None:
                lte_rsrp_gauge.set(metrics_data['lte_rsrp'])
            if metrics_data['lte_rsrq'] is not None:
                lte_rsrq_gauge.set(metrics_data['lte_rsrq'])
            if metrics_data['lte_snr'] is not None:
                lte_snr_gauge.set(metrics_data['lte_snr'])
            if metrics_data['signal_strength'] is not None:
                signal_strength_gauge.set(metrics_data['signal_strength'])
            
            # Update success indicators
            scrape_success_gauge.set(1)
            current_time = time.time()
            last_successful_scrape_gauge.set(current_time)
    
    except Exception as e:
        logger.error(f"Error scraping metrics: {str(e)}")
        scrape_success_gauge.set(0)
    
    return Response(generate_latest(REGISTRY), mimetype='text/plain')


@app.route('/health')
def health():
    """
    Health check endpoint.
    """
    return {'status': 'healthy'}, 200


@app.route('/')
def index():
    """
    Root endpoint with basic information.
    """
    return {
        'service': 'LTE Metrics Exporter',
        'endpoints': {
            '/metrics': 'Prometheus metrics',
            '/health': 'Health check'
        }
    }, 200


def main():
    """
    Main function to start the metrics server.
    """
    # Check environment variables
    if not os.getenv('LOGIN_URL'):
        logger.error("LOGIN_URL environment variable is not set")
        logger.error("Please set it using: export LOGIN_URL='192.168.101.1'")
        sys.exit(1)
    
    if not os.getenv('ADMIN_PASS'):
        logger.error("ADMIN_PASS environment variable is not set")
        logger.error("Please set it using: export ADMIN_PASS='your_password'")
        sys.exit(1)
    
    # Start the Flask web server
    port = int(os.getenv('PORT', 8000))
    logger.info(f"Starting metrics server on port {port}...")
    logger.info(f"Metrics endpoint: http://0.0.0.0:{port}/metrics")
    logger.info("Note: Metrics will be scraped on-demand when /metrics is requested")
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    main()
