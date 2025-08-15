# Driver Profiling Dashboard

A full-stack application for monitoring and analyzing driver performance, compliance, and safety trends.

## Documentation: 
https://docs.google.com/document/d/1CoelF0zPx3EmWG7NGE2wVveEDkQRirva4RKGWVMRi0s/edit?usp=sharing

## Features

- **Driver Profiles** – Stores and displays:
  - Drug test results
  - Work-related violations and infractions
  - Uploaded credentials and validity checks
  - Driver feedback and ratings
- **Automated Credential Validation** – Runs background checks using queued jobs.
- **Interactive Dashboard** – Embedded Metabase dashboards to visualize:
  - Line chart: Drug test result trends
  - Table: Drivers with more than 3 violations
  - Bar chart: Credential validity rates
  - Heatmap: Monthly infractions

## Tech Stack

- **Backend**: Laravel (PHP) + PostgreSQL
- **Frontend**: Next.js (TypeScript, TSX components)
- **Data Visualization**: Metabase Embedded Dashboards
- **Background Jobs**: Laravel Queues
- **Optional Analytics API**: Python (FastAPI / Flask) for advanced chart data

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-repo/driver-profiling-dashboard.git
cd driver-profiling-dashboard
