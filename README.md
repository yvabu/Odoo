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

<img width="2558" height="1181" alt="Screenshot from 2026-11-13 15-04-41" src="https://github.com/user-attachments/assets/0c0d9402-b4be-4349-bd7d-eb9e3c9faa91" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/296b8120-84cc-4191-a11e-21625ffa40ea" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/5aea5721-2883-4b52-bfe0-7a965a9704b7" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/80a249d4-c925-4892-a1db-0a2ed07acc3e" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/ab361e2e-cfa4-4129-9220-eea01cbb1254" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/948b1df3-b9e9-4ace-a115-bca8453d2045" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/46bd4cc6-20c7-426b-93ce-c054c9ef0aa6" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/97ec308c-97c1-4e8c-a695-93721560dda0" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/bc99c935-0a22-4dfa-a918-fa50dc31c02e" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/ffc16735-8a8f-4e42-989e-1b4776d59d88" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/91d104a7-e2fb-4d6f-82d6-d2c32bacdd13" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/704347cb-6890-4bd6-9e3a-3fb1bf139adf" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/b122ff8b-4664-4701-b8d6-64b73af7672c" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/03f31284-60a5-4d9a-aa87-1cecf201812f" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/ed151e53-2809-4673-a4ec-bc0051a62a5d" />
<img width="2558" height="1181" alt="image" src="https://github.com/user-attachments/assets/00fd8a52-caff-4063-abc6-cf2dd0cfe818" />

















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
