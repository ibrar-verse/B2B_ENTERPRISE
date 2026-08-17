# Project Context & Architecture: Enterprise B2B Marketplace

## 1. High-Level Overview
This project is an enterprise B2B marketplace with a dual-service architecture:
- **Django Monolith (Port 8000)**: Handles multi-tenant organization management (`BUYER`, `VENDOR`, `ADMIN`), user authentication, purchase order state machines, and portal UI.
- **Spring Boot Financial Microservice (Port 8080)**: Handles double-entry escrow accounting, idempotency, and audit ledgers using MySQL (`payment_db`).

## 2. Hard Constraints (DO NOT BREAK)
- **Database Schema**: Do not alter, rename, or drop existing database tables or columns in `payment_db` (`payment_transactions`, `ledger_entries`) or Django models (`Order`, `Organization`).
- **Microservice Integration**: Django talks to Spring Boot via HTTP REST (`PaymentGatewayClient` in `apps.orders.services`):
  - `POST http://localhost:8080/api/v1/payments/process` (Initial Escrow Hold)
  - `POST http://localhost:8080/api/v1/payments/settle` (Escrow Release to Vendor Wallet)
  - `POST http://localhost:8080/api/v1/payments/refund` (Dispute & Balance Reversal)
- **Frontend Theme**: Clean, professional **White & Emerald Green** enterprise fintech aesthetic using Tailwind CSS, HTMX, and Alpine.js. No dark/glowing purples or heavy 3D canvases.

## 3. Order Lifecycle State Machine
`DRAFT` -> `APPROVED` -> `PAID` (Escrow locked) -> `SHIPPED` -> `COMPLETED` (Funds settled to vendor) or `CANCELLED` (Refunded/Reversed).

## 4. Key Directories
- `apps/orders/`: Order models, state transitions, and `PaymentGatewayClient`.
- `apps/organizations/`: Multi-tenant organization and user profile models.
- `apps/portal/`: Views, forms, and routes for Buyer, Vendor, and Admin user flows.
- `templates/`: HTML templates (Base, Auth, Buyer, Vendor, HTMX Partials).
- `payment_service/`: Spring Boot Java source code for financial processing.