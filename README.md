# Rubber & Commodity Price Automation System

A Python-based backend automation system designed to scrape rubber price data from multiple domestic and international sources, process it on a scheduled basis, store it in a database, and integrate it with an admin dashboard for monitoring and management.

## Tech Stack
- Python
- Requests
- BeautifulSoup
- Selenium
- PostgreSQL 
- Scheduler ( Python-based scheduler)
- React

## Features
- Automated scraping of tabular price data from multiple sources
- Scheduled execution for daily data collection
- Database integration for structured and historical data storage
- Backend integration with an admin UI dashboard
- Robust error handling to ensure uninterrupted scheduler execution

## Workflow Overview
1. Scheduler triggers scraping jobs at predefined intervals  
2. Price tables are scraped and parsed from source websites  
3. Data is processed and stored in the database  
4. Stored data is made available to the admin dashboard for viewing and management  

## Project Context
Developed as part of a Backend Developer Internship at **TVS Srichakra Ltd**.  
Company-specific URLs, credentials, and internal configurations are excluded for confidentiality.

## Use Case
This system eliminates manual price tracking by providing a reliable, automated pipeline for collecting and managing rubber commodity price data.


