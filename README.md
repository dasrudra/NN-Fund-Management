# NN Fund Management — Odoo 19 Custom Module

A custom Odoo 19 Community module developed for the NN Services & Engineering Ltd. Trainee Software Developer technical assessment.

## Module Name

```text
nn_fund_management
```

## Repository

```text
https://github.com/dasrudra/NN-Fund-Management
```

## Project Overview

`nn_fund_management` is a custom fund management module for Odoo 19. The module manages incoming funds, fund accounts, fund allocation, requisition approval, bill control, balance tracking, and role-based security.

The project focuses on clean Odoo model design, server-side validation, workflow control, access control, computed balances, and prevention of duplicate or unauthorized financial usage.

## Development Environment

The module was developed and tested in the following environment:

```text
Odoo Version: Odoo Community 19.0
Python: 3.12
Database: PostgreSQL 15
Operating System: Windows 11
Development Mode: Local Odoo source installation
```

## Implemented Features

### 1. Fund Accounts

Fund Accounts are used to represent bank, cash, or other financial accounts.

Implemented features:

- Fund account name
- Fund account code
- Account type
- Company
- Currency
- Total received amount
- Available unassigned balance
- Held balance
- Assigned balance
- Multi-company support
- Duplicate account-code protection per company

### 2. Incoming Funds

Incoming Funds are used to record received money before it is allocated.

Workflow:

```text
Draft → Submitted → Confirmed → Cancelled
```

Implemented rules:

- Finance users can submit incoming funds.
- Finance users can confirm incoming funds.
- Confirmed incoming funds increase the fund account's unassigned balance.
- Duplicate transaction reference is blocked per fund account.
- Confirmed records cannot be edited directly.
- Chatter/audit tracking is enabled.

### 3. Fund Allocation

Fund Allocation is used to allocate available unassigned money to a project or expense head.

Workflow:

```text
Draft → Submitted → GM Approved → MD Approved → Rejected / Cancelled
```

Implemented rules:

- Allocation can be made to either a project or an expense head.
- Project and expense head cannot be selected together.
- Submitted allocation places the amount on hold.
- Held amount cannot be reused by another allocation.
- GM approval must happen before MD approval.
- MD approval converts held amount into assigned amount.
- Rejected or cancelled allocation releases the held amount back.
- Over-allocation is blocked by server-side validation.

### 4. Fund Requisition

Fund Requisition is used to request money from an approved project or expense-head fund.

Workflow:

```text
Draft → Submitted → GM Approved → MD Approved → Rejected / Cancelled / Closed
```

Implemented rules:

- Requisition can be created against a project or an expense head.
- Target type controls whether project or expense head is selected.
- Supporting attachment field is available.
- Requested amount is tracked.
- Approval users and approval dates are tracked.
- Remaining billable amount is computed.
- Direct state editing is blocked.
- Non-draft requisitions are protected from direct editing.

### 5. Bill Control

A custom bill model was implemented for bill control.

Custom model:

```text
nn.fund.bill
```

Workflow:

```text
Draft → Posted → Cancelled
```

Implemented rules:

- A bill must be linked to an approved requisition.
- Only approved requisitions can be billed.
- Multiple partial bills are allowed.
- Bill amount cannot exceed the requisition's remaining billable amount.
- Posted bill reduces remaining billable amount.
- Cancelled bill restores remaining billable amount.
- Posted bills cannot be deleted directly.
- Bill posting and cancellation are logged in chatter.

### 6. Security and Access Control

Security groups:

```text
Fund User
Finance User
GM Approver
MD Approver
Fund Administrator
```

Security implementation includes:

- Access control list in `ir.model.access.csv`
- Security groups
- Record rules
- Multi-company isolation
- Server-side workflow permission checks
- Group-based UI buttons

The module does not depend only on hidden buttons. Important workflow actions are also protected in Python methods.

## Module Structure

```text
nn_fund_management/
├── data/
│   ├── incoming_fund_sequence.xml
│   ├── fund_allocation_sequence.xml
│   ├── fund_requisition_sequence.xml
│   └── fund_bill_sequence.xml
├── models/
│   ├── fund_account.py
│   ├── incoming_fund.py
│   ├── expense_head.py
│   ├── fund_allocation.py
│   ├── fund_requisition.py
│   └── fund_bill.py
├── security/
│   ├── fund_management_security.xml
│   ├── fund_requisition_rules.xml
│   ├── fund_bill_rules.xml
│   └── ir.model.access.csv
├── tests/
│   ├── test_incoming_fund.py
│   └── test_fund_allocation.py
├── views/
│   ├── fund_account_views.xml
│   ├── incoming_fund_views.xml
│   ├── expense_head_views.xml
│   ├── fund_allocation_views.xml
│   ├── fund_requisition_views.xml
│   ├── fund_bill_views.xml
│   └── fund_management_menus.xml
└── __manifest__.py
```

## Dependencies

Required Odoo apps/modules:

```text
base
mail
project
```

Required local tools:

```text
Python 3.12
PostgreSQL 15
Git
Odoo Community 19.0 source code
```

Optional:

```text
Docker Desktop / Docker Engine
```

## Local Installation Guide

This section explains how to run the module locally.

There are two different cases:

1. Fresh installation from GitHub.
2. Existing local project already available.

Do not run `git clone` inside an existing copy of this repository. That creates a nested repository folder and causes path/configuration confusion.

---

### Case 1: Fresh Installation from GitHub

Use this only on a fresh machine or inside a clean workspace folder.

Open PowerShell and go to a workspace folder.

Example:

```powershell
Set-Location "E:\Rudra\Rudra's Projects\Assessment - NNSEL"
```

Clone the repository:

```powershell
git clone https://github.com/dasrudra/NN-Fund-Management.git
```

Enter the project folder:

```powershell
Set-Location ".\NN-Fund-Management"
```

Check that the module exists:

```powershell
Test-Path ".\addons\nn_fund_management\__manifest__.py"
```

Expected output:

```text
True
```

---

### Case 2: Existing Local Project

Use this if the project is already available locally.

Open PowerShell and go to the real project root:

```powershell
Set-Location "E:\Rudra\Rudra's Projects\Assessment - NNSEL\nn-fund-management"
```

Verify current location:

```powershell
Get-Location
```

Expected example:

```text
E:\Rudra\Rudra's Projects\Assessment - NNSEL\nn-fund-management
```

Verify that the module exists:

```powershell
Test-Path ".\addons\nn_fund_management\__manifest__.py"
```

Expected output:

```text
True
```

---

### Create Local Odoo Configuration

The real local configuration file should not be committed because it may contain local database credentials and machine-specific paths.

A safe example configuration should be available at:

```text
config/odoo.example.conf
```

Copy the example file:

```powershell
Copy-Item ".\config\odoo.example.conf" ".\config\odoo.local.conf"
```

Open the local config:

```powershell
code ".\config\odoo.local.conf"
```

Update the `addons_path`.

Example:

```ini
addons_path = C:\Odoo\odoo\addons,E:\Rudra\Rudra's Projects\Assessment - NNSEL\nn-fund-management\addons
```

Check database settings:

```ini
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
http_port = 8070
```

Save the file.

---

### Create or Check Database

The development database used for this module is:

```text
nnsel_fund_dev
```

Check whether the database exists:

```powershell
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" `
-h localhost `
-p 5432 `
-U odoo `
-d postgres `
-P pager=off `
-tAc "SELECT datname FROM pg_database WHERE datname='nnsel_fund_dev';"
```

If the database exists, expected output:

```text
nnsel_fund_dev
```

If the database does not exist, create it:

```powershell
& "C:\Program Files\PostgreSQL\15\bin\createdb.exe" `
-h localhost `
-p 5432 `
-U odoo `
nnsel_fund_dev
```

---

### Start Odoo

From the project root, run:

```powershell
& "C:\Odoo\venv\Scripts\python.exe" `
"C:\Odoo\odoo\odoo-bin" `
-c ".\config\odoo.local.conf" `
-d nnsel_fund_dev
```

Keep this terminal running.

Open browser:

```text
http://127.0.0.1:8070
```

Login to Odoo.

---

### Install Module from Odoo UI

In the Odoo interface:

1. Go to **Apps**
2. Remove default app filters if necessary
3. Search for:

```text
NN Fund Management
```

or:

```text
nn_fund_management
```

4. Click **Install**

After installation, the top menu should show:

```text
Fund Management
```

---

### Upgrade Module from Terminal

Whenever code is changed, stop the running Odoo server first:

```text
Ctrl + C
```

Then run:

```powershell
& "C:\Odoo\venv\Scripts\python.exe" `
"C:\Odoo\odoo\odoo-bin" `
-c ".\config\odoo.local.conf" `
-d nnsel_fund_dev `
-u nn_fund_management `
--stop-after-init
```

Check exit code:

```powershell
$LASTEXITCODE
```

Expected output:

```text
0
```

---

## Static Validation

Run Python compilation:

```powershell
& "C:\Odoo\venv\Scripts\python.exe" -m compileall ".\addons\nn_fund_management"
```

Expected result:

```text
0
```

Run XML validation:

```powershell
& "C:\Odoo\venv\Scripts\python.exe" -c "from pathlib import Path; from lxml import etree; import sys; files=sorted(Path(sys.argv[1]).rglob('*.xml')); [etree.parse(str(f)) for f in files]; print(f'XML validation passed: {len(files)} files')" ".\addons\nn_fund_management"
```

Expected example:

```text
XML validation passed: 14 files
```

## Automated Tests

Run:

```powershell
& "C:\Odoo\venv\Scripts\python.exe" `
"C:\Odoo\odoo\odoo-bin" `
-c ".\config\odoo.local.conf" `
-d nnsel_fund_dev `
-u nn_fund_management `
--test-tags /nn_fund_management `
--stop-after-init
```

Implemented automated tests cover key incoming fund and allocation logic.

## Functional Verification

Start Odoo:

```powershell
& "C:\Odoo\venv\Scripts\python.exe" `
"C:\Odoo\odoo\odoo-bin" `
-c ".\config\odoo.local.conf" `
-d nnsel_fund_dev
```

Open:

```text
http://127.0.0.1:8070
```

Verify menu:

```text
Fund Management
```

Expected submenus:

```text
Operations
Configuration
```

Recommended verification flow:

1. Go to **Fund Management → Configuration → Fund Accounts**
2. Create or open `Main Operating Bank`
3. Go to **Fund Management → Operations → Incoming Funds**
4. Create and confirm an incoming fund
5. Go to **Fund Management → Operations → Fund Allocations**
6. Create an allocation and approve it through GM and MD
7. Go to **Fund Management → Operations → Fund Requisitions**
8. Create and approve a requisition
9. Go to **Fund Management → Operations → Fund Bills**
10. Create a partial bill
11. Post the bill
12. Verify remaining billable amount decreases
13. Try to over-bill and confirm that the system blocks it
14. Cancel the posted bill and confirm that billable balance is restored

## Docker Setup

Docker files are included:

```text
Dockerfile
docker-compose.yml
docker/odoo.conf
.dockerignore
```

Run on a machine where Docker Desktop or Docker Engine is installed:

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:8069
```

Then create a database and install:

```text
NN Fund Management
```

Note: Docker files are included for assessment submission. Docker was not executed locally because Docker was not installed on the development machine.

## Architecture Summary

```text
Incoming Fund
     ↓
Fund Account
     ↓
Fund Allocation
     ↓
Fund Requisition
     ↓
Fund Bill
     ↓
Audit History / Chatter
```

Model relationship:

```text
nn.fund.account
 ├── nn.incoming.fund
 ├── nn.fund.allocation
 └── nn.fund.requisition
       └── nn.fund.bill
```

Approval flow:

```text
Draft → Submitted → GM Approved → MD Approved
```

Rejected, cancelled, posted, and closed states are available depending on the transaction type.

## Data Integrity Controls

- Positive amount constraints
- Duplicate transaction reference blocking
- Project/expense-head mutual exclusivity
- Workflow-only state transitions
- Computed balance fields
- Over-allocation blocking
- Over-billing blocking
- Multi-company record rules
- Server-side permission checks
- Chatter-based audit history

## AI Usage Transparency

AI tools were used for:

- Planning implementation phases
- Drafting model and XML structure
- Planning tests
- Debugging Odoo 19 compatibility issues
- Preparing documentation

Candidate actions included:

- Running commands locally
- Testing in browser
- Checking Odoo logs
- Verifying PostgreSQL tables
- Fixing generated issues
- Reviewing and modifying code
- Creating Git commits

Important issues fixed:

- Wrong security group XML IDs
- Missing sequence XML file
- Unsupported Odoo 19 `states` field parameter
- Odoo 19 XML syntax compatibility issue
- Fund Account dropdown domain/company issue
- Bill remaining balance computation

## Known Limitations

The following items are not fully implemented:

- Fund Transfer module
- Dashboard
- Bank email integration
- Dynamic configurable approval rule engine
- Live server deployment
- Direct Odoo Vendor Bill integration

A custom fund bill model was implemented instead of extending Odoo Vendor Bills.

## Assumptions

- Finance users manage incoming funds, allocations, requisitions, and bills.
- GM and MD users are assigned through Odoo security groups.
- A fund account is created once and reused.
- Project records are created using Odoo's Project app.
- Docker runtime requires Docker to be installed separately.
- Full completion was not mandatory, so the implementation prioritizes core workflow, data integrity, access control, and code quality.

## Final Submission Checklist

- [x] Installable Odoo module
- [x] Git repository
- [x] README
- [x] Security files
- [x] Architecture explanation
- [x] Meaningful Git commit history
- [x] Dockerized project files
- [x] AI usage transparency
- [ ] Demo video Google Drive public link
- [ ] Google Form submission

## Author

Rudra Das
Trainee Software Developer Candidate
NN Services & Engineering Ltd. Technical Assessment
