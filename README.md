# 🏢 B2B Enterprise Marketplace & Escrow Ledger System

An enterprise-grade B2B procurement marketplace built with **Django 5**, **HTMX**, **Tailwind CSS**, and **MySQL**, designed to facilitate high-value business-to-business commerce with multi-tenant organization isolation, an automated escrow vaulting engine, and microservice-backed financial settlements.

---

## 📌 Overview

Traditional B2B commerce often faces counterparty risk, rigid credit cycles, and manual payment reconciliation. This platform implements an automated **Escrow Lifecycle Engine**: buyer payments are vaulted into an intermediate holding escrow upon order approval and only settled into the supplier's available balance once the buyer verifies delivery.

---

## 🏛️ System Architecture

                  +-----------------------------+
                  |   Modern Frontend / HTMX    |
                  |  (Tailwind CSS, Zero-Reload)|
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |   Django 5.0 Core Engine    |
                  |  - Multi-Org Role Routing   |
                  |  - Order State Machine      |
                  |  - Catalog & Auth Service   |
                  +--------------+--------------+
                                 |
         +-----------------------+-----------------------+
         |                                               |
         v                                               v
+-------------------------+                     +-------------------------+
|      MySQL Database     |                     |  Financial Microservice |
|  - Custom User Model    |                     |  (Spring Boot / Ledger) |
|  - Organizations/Orders |                     |  - Double-Entry Ledger  |
|  - Products & Inventory |                     |  - Escrow Lock & Settle |
+-------------------------+                     +-------------------------+


---

## 🚀 Key Features

### 1. Multi-Tenant Role Isolation
* **Procurement Buyers:** Search active supplier catalogs with real-time query filtering, generate immediate purchase orders, and trigger zero-reload escrow holds via JazzCash/1Link gateway mocks.
* **Goods Suppliers (Vendors):** Manage product inventory, monitor total transaction volume, inspect live funds divided between **Escrow Pending** and **Available Balance**, and initiate payout requests.
* **Platform Governance (Super Admin):** Audit all marketplace activity with color-coded status badges, run 1-click ledger execution actions, and process dispute reversals.

### 2. Escrow State Machine
[ DRAFT ] ──> [ APPROVED ] ──> [ PAID (Escrow Locked) ] ──> [ COMPLETED (Settled) ]
│
└───> [ CANCELLED (Refunded) ]


* **APPROVED:** Purchase order generated and awaiting payment authorization.
* **PAID:** Funds locked into escrow holding vault; unique transaction reference hash generated.
* **COMPLETED:** Delivery confirmed by buyer; escrow funds released to supplier's payout ledger.
* **CANCELLED:** Dispute raised; funds reversed back to buyer via double-entry ledger reversal.

### 3. Dynamic HTMX UI
* Real-time order state updates and catalog search without page reloads.
* Inline feedback for payment execution, delivery confirmation, and disputes.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Django 5.0.x (Python 3.14) |
| **Database** | MySQL 8.x (via PyMySQL) |
| **Frontend & UX** | HTMX, Tailwind CSS, Django Templates |
| **Escrow Engine** | Spring Boot Ledger Microservice / Python Service Fallback |
| **Authentication** | Django Custom User Model (`core.User`) with Multi-Tenant Organization links |

---

## 📦 Project Structure

```text
enterprise_marketplace/
├── apps/
│   ├── core/           # Custom User Model & Base Utilities
│   ├── orders/         # Orders, Products, Escrow State Machine & Admin Actions
│   ├── organizations/  # Multi-tenant Organization Models
│   └── portal/         # Buyer/Vendor Portals, Auth Views, Forms & HTMX Handlers
├── config/             # Django Settings, ASGI/WSGI, Root URLs
├── templates/          # Responsive UI Templates
│   ├── auth/           # Login & Multi-Role Registration
│   ├── buyer/          # Catalog & Order Detail Screens
│   ├── partials/       # HTMX Dynamic Components
│   └── vendor/         # Dashboard & Wallet Management
├── manage.py
└── requirements.txt