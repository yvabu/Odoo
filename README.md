# 🏨 Hotel ERP — Odoo 18

A custom Hotel Management System developed using **Odoo 18 and Python**, designed to manage hotel operations, reservations, guests, rooms, payments, and daily business workflows.

This project is a practical implementation of Odoo ERP development concepts, focusing on custom modules, business logic, database models, access control, automation, and website functionality.

## 🎯 Project Overview

The main goal of this project is to build a hotel management solution that simplifies daily hotel operations and provides an integrated environment for managing reservations, guests, rooms, and payments.

The system is developed as a collection of custom Odoo modules, extending the standard Odoo functionality to meet hotel business requirements.

## 🛠️ Technologies

- **Python** — Backend development and business logic.
- **Odoo 18** — ERP framework and ORM.
- **PostgreSQL** — Database management.
- **XML** — Views, menus, actions, security rules, and data records.
- **JavaScript** — Frontend interactions and website functionality.
- **QWeb** — Odoo website templates.
- **Docker** — Containerized development environment (where applicable).
- **Git / GitHub** — Version control.

## 🚀 Core Features

### 1. Room Management
- Create and manage hotel rooms.
- Room types: Single, Double, and VIP.
- Room availability and occupancy management.
- Housekeeping status management.
- Room maintenance status.

### 2. Guest Management
- Guest registration and profile management.
- Personal information validation.
- Unique guest information constraints.
- Guest contact information management.

### 3. Reservation Management
- Create and manage hotel reservations.
- Reservation lifecycle:
  - Draft
  - Pending
  - Confirmed
  - Checked In
  - Checked Out
  - Cancelled
  - Expired
- Reservation expiration using scheduled actions.
- Configurable reservation hold duration.
- Reservation validation and business rules.

### 4. Payment Management
- Payment registration.
- Advance payment workflow.
- Payment validation before reservation confirmation.
- Payment tracking.
- Full payment validation during checkout.

### 5. Check-in / Check-out
- Check-in validation based on room housekeeping status.
- Reservation and room status updates.
- Checkout workflow.
- Payment verification during checkout.

### 6. Access Control
- Custom user groups:
  - Hotel Manager
  - Receptionist
- Role-based access permissions.
- Restricted operations depending on user roles.

### 7. Website Functionality
- Hotel homepage.
- Room details pages.
- Room image carousel.
- Dynamic website content.
- Custom website templates.

## ⚙️ Odoo Technical Implementation

This project demonstrates practical experience with:

- Custom Odoo model development using `models.Model`.
- Odoo ORM and recordsets.
- Model relationships (`Many2one`, `One2many`, `Many2many`).
- Computed and related fields.
- Constraints and Python business validations.
- Model inheritance and method overriding.
- XML views, menus, actions, and security rules.
- Access Control Lists (ACLs) and record rules.
- Odoo controllers and HTTP routes.
- QWeb templates.
- Scheduled actions (Cron Jobs).
- Wizards and transient models.
- Backend and website integration.
- JavaScript frontend customization.
- PostgreSQL database operations.

## 📁 Project Structure

The project is organized into custom Odoo modules.

Example structure:

```text
hotel_erp/
│
├── hotel_erp/
│   ├── __init__.py
│   ├── __manifest__.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── hotel_room.py
│   │   ├── hotel_guest.py
│   │   └── hotel_reservation.py
│   │
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── views/
│   ├── security/
│   ├── data/
│   ├── wizard/
│   └── static/
│
└── README.md
```

*Note: This is an illustrative structure. Actual folders and filenames may differ.*

## 💻 Installation

### Requirements

- Python 3
- Odoo 18
- PostgreSQL
- Git

### Steps

1. Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
```

2. Copy the custom module into your Odoo custom addons directory.

3. Add the custom addons directory to your Odoo configuration:

```ini
addons_path = /path/to/odoo/addons,/path/to/custom_addons
```

4. Restart the Odoo server.

5. Activate Developer Mode and update the Apps List.

6. Install the Hotel ERP module from the Apps menu.

## 📸 Screenshots

Screenshots of the application will be added here to demonstrate:

- Hotel Dashboard
- Room Management
- Guest Management
- Reservation Management
- Payment Workflows
- Hotel Website

## 📚 Learning & Development

This project is part of my practical learning journey in Python and Odoo ERP development.

Through this project, I have been developing my skills in:

- Building custom ERP solutions.
- Understanding Odoo architecture and ORM.
- Implementing business requirements in Python.
- Developing custom modules and integrations.
- Debugging and troubleshooting Odoo applications.
- Working with databases and backend workflows.
- Extending existing Odoo functionality.

I am continuously improving this project and expanding my knowledge of Odoo development.

## 👨‍💻 Author

**Saba Kobalia**

IT Student | Junior Python / Odoo Developer

- GitHub: [github.com/yvabu](https://github.com/yvabu)
- LinkedIn: [Saba Kobalia](https://www.linkedin.com/in/saba-kobalia-689b173a/)

**Career Goal:** To grow as an Odoo Python Developer by contributing to real-world ERP projects, learning from experienced developers, and continuously improving my technical skills.
