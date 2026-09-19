name: Markaz Product Grabber

on:
  schedule:
    - cron: '0 3 * * *' # Runs automatically every day at 8:00 AM PKT
  workflow_dispatch: # Allows you to run it manually anytime with 1 click

jobs:
  run-grabber:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install gspread google-generativeai

      - name: Run Markaz Grabber Script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GCP_SA_KEY: ${{ secrets.GCP_SA_KEY }}
        run: python markaz_grabber.py
