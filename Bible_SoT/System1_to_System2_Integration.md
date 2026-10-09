# REVO Master Data -> GBP Analyzer Integration Guide

## Overview
This document describes how **System 2 (GBP Analyzer & AI Personalization)** interacts with **System 1 (REVO Master Data)**.
The integration is built primarily around a **Webhook (Push) architecture**. System 1 pushes fully enriched, deduplicated, and scored leads directly to System 2. System 2 is then responsible for analyzing the GBP (Google Business Profile), generating a personalized PDF/HTML audit, and executing the outreach campaigns.

## 1. Webhook (Push) Mechanism
System 1 will send an HTTP POST request to a configured URL in System 2 whenever new leads are ready for outreach (either automatically after a scraping campaign finishes, or manually triggered by the user via the "CRM Sync" button in the Master Data Grid).

### Request Format
- **Method:** `POST`
- **Headers:** 
  - `Content-Type: application/json`
  - `X-Revo-Signature: <hmac-sha256>` (Optional, for security validation)
- **Body:** JSON Array of Lead Objects.

### Payload Schema
```json
{
  "event": "leads.sync",
  "timestamp": "2026-10-09T12:00:00Z",
  "campaign_id": "uuid-string-here",
  "campaign_name": "Dubai Restaurants Campaign",
  "leads": [
    {
      "lead_id": "uuid-string-here",
      "company_name": "Tummy Tales Restaurant & Catering",
      "business_type": "Punjabi restaurant",
      "city": "Dubai",
      "address": "Level, JLT - R2-C...",
      "latitude": 25.0633806,
      "longitude": 55.1377617,
      "website": "https://tummytales.ae",
      "rating": 4.7,
      "reviews_count": 542,
      "revo_score": 95,
      "audit_notes": "Strong rating, phone available, website available.",
      "contacts": [
        {
          "type": "phone",
          "value": "+97145722123",
          "is_verified": true
        },
        {
          "type": "whatsapp",
          "value": "+97145722123",
          "is_verified": true
        }
      ]
    }
  ]
}
```

## 2. API Polling (Pull) Mechanism - (Fallback/Alternative)
If System 2 prefers to fetch data on its own schedule (e.g., via a Cron job), it can query System 1's REST API.

### Request
- **Endpoint:** `GET /api/v1/leads`
- **Query Parameters:**
  - `campaign_id` (UUID) - Filter by specific campaign
  - `min_score` (Integer) - E.g., `80` to only fetch high-quality leads
  - `min_rating` (Float) - E.g., `3.6`
  - `max_rating` (Float) - E.g., `4.4` (To find businesses needing reputation help)
  - `page` (Integer)
  - `page_size` (Integer, max 500)

### Response
```json
{
  "items": [
    {
      "id": "uuid-string-here",
      "company_name": "...",
      "revo_score": 85,
      "contacts": [...]
    }
  ],
  "total": 1500,
  "page": 1,
  "page_size": 500,
  "total_pages": 3
}
```

## 3. How the AI Agent for System 2 Should Proceed
If you are the AI Agent building System 2, your immediate steps are:
1. **Create an HTTP Endpoint (Webhook Receiver)** in your stack (e.g., FastAPI, Express, Next.js API route) that accepts `POST` requests at `/api/webhooks/revo-leads`.
2. **Validate the Payload:** Parse the incoming JSON array. Extract `company_name`, `website`, and `rating`.
3. **Execute AI Workflow:** Pass the `website` and `company_name` to your web scraper/LLM module to perform the deep-dive GBP analysis and generate the personalized report.
4. **Trigger Outreach:** Queue the enriched report into your Email/WhatsApp sender module.

## Summary for System 2 Developers
- Assume data coming from System 1 is already cleaned and standardized.
- Phone numbers are formatted in E.164.
- Only focus on the **analysis** and **outreach** logic. System 1 handles the heavy lifting of raw data extraction.
