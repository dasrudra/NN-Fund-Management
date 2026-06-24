# Demo Video Guide — NN Fund Management

Recommended video length: 6 to 8 minutes.

The assessment requires a short screen recording with facecam. The video should show the implemented Odoo features, code structure, AI usage, errors found in AI-generated code, candidate-made fixes, known limitations, and understanding of the submitted code.

---

## 1. Opening Statement

Suggested opening:

Hello, I am Rudra Das. This is my Odoo technical assessment submission for the Trainee Software Developer position at NN Services & Engineering Ltd.

The module name is `nn_fund_management`, developed for Odoo 19 Community.

The module focuses on fund accounts, incoming funds, fund allocations, fund requisitions, bill control, approval workflow, access control, computed balances, and prevention of duplicate financial usage.

---

## 2. Show GitHub Repository

Open the GitHub repository:

https://github.com/dasrudra/NN-Fund-Management

Show:

- Meaningful commit history
- README.md
- Dockerfile
- docker-compose.yml
- addons/nn_fund_management
- docs/ARCHITECTURE.md
- docs/DEMO_VIDEO_GUIDE.md

Brief explanation:

This repository contains the complete custom Odoo module, Docker setup files, documentation, architecture explanation, and demo guide.

---

## 3. Show README

Open `README.md`.

Briefly show:

- Odoo version
- Implemented features
- Installation guide
- Docker setup
- Testing instructions
- AI usage transparency
- Known limitations

Mention:

The README explains how to install, configure, test, and understand the project.

---

## 4. Show Code Structure in VS Code

Open VS Code and show:

- `addons/nn_fund_management/models`
- `addons/nn_fund_management/views`
- `addons/nn_fund_management/security`
- `addons/nn_fund_management/data`
- `addons/nn_fund_management/tests`

Brief explanation:

- `models/` contains the business logic and workflow methods.
- `views/` contains Odoo XML views and menus.
- `security/` contains access control, security groups, and record rules.
- `data/` contains sequence definitions.
- `tests/` contains automated tests for important fund workflows.

---

## 5. Show Main Models

Show these files:

- `models/fund_account.py`
- `models/incoming_fund.py`
- `models/fund_allocation.py`
- `models/fund_requisition.py`
- `models/fund_bill.py`

Explain:

The business flow starts from incoming funds, then allocation, then requisition, then bill control.

---

## 6. Show Security Files

Show:

- `security/fund_management_security.xml`
- `security/ir.model.access.csv`
- `security/fund_requisition_rules.xml`
- `security/fund_bill_rules.xml`

Explain:

The module includes role-based access control for Fund User, Finance User, GM Approver, MD Approver, and Fund Administrator.

Important workflow actions are protected not only by hidden buttons but also by Python server-side permission checks.

---

## 7. Start Odoo

From PowerShell, run:

& "C:\Odoo\venv\Scripts\python.exe" `
"C:\Odoo\odoo\odoo-bin" `
-c ".\config\odoo.local.conf" `
-d nnsel_fund_dev

Open browser:

http://127.0.0.1:8070

Login and open:

Fund Management

---

## 8. Demonstrate Fund Account

Menu path:

Fund Management → Configuration → Fund Accounts

Show:

- Main Operating Bank
- Total received amount
- Available unassigned balance
- Held balance
- Assigned balance

Explain:

Fund Account is the central balance container. Incoming funds and allocations update these computed balances.

---

## 9. Demonstrate Incoming Fund

Menu path:

Fund Management → Operations → Incoming Funds

Show or create an incoming fund:

- Fund Account: Main Operating Bank
- Amount: BDT 1,000,000
- Transaction reference
- Sender/source
- Description

Workflow:

Draft → Submitted → Confirmed

Explain:

After confirmation, the amount increases the fund account's available unassigned balance.

Also mention:

Duplicate transaction reference is blocked per fund account.

---

## 10. Demonstrate Fund Allocation

Menu path:

Fund Management → Operations → Fund Allocations

Show or create an allocation:

- Fund Account: Main Operating Bank
- Target: Project or Expense Head
- Amount
- Purpose

Workflow:

Draft → Submitted → GM Approved → MD Approved

Explain:

When submitted, the allocation amount goes to held balance. After MD approval, it becomes assigned balance. Over-allocation is blocked server-side.

---

## 11. Demonstrate Fund Requisition

Menu path:

Fund Management → Operations → Fund Requisitions

Show or create a requisition:

- Fund Account: Main Operating Bank
- Requisition Against: Project or Expense Head
- Amount: BDT 150,000
- Purpose
- Required date

Workflow:

Draft → Submitted → GM Approved → MD Approved

Explain:

An approved requisition becomes available for bill control. Remaining billable amount is computed automatically.

---

## 12. Demonstrate Bill Control

Menu path:

Fund Management → Operations → Fund Bills

Create a bill:

- Approved Requisition: select an approved requisition
- Vendor / Payee: Demo Vendor
- Description: Partial bill against approved requisition
- Amount: BDT 100,000

Click:

Post Bill

Explain:

Posted bill reduces the requisition's remaining billable amount.

Then create another bill above remaining billable amount and show that the system blocks it.

Then cancel a posted bill and explain:

Cancelled bill restores remaining billable amount without creating extra funds.

---

## 13. Explain Double-Spending Prevention

Mention these points:

1. Confirmed incoming funds increase unassigned balance only once.
2. Submitted allocations move available money into held balance.
3. Held amount cannot be reused.
4. MD-approved allocation becomes assigned.
5. Approved requisition controls billable amount.
6. Posted bill decreases remaining billable amount.
7. Over-allocation and over-billing are blocked.
8. Cancelled bill restores billable balance without creating extra funds.

---

## 14. Explain AI Usage

Suggested explanation:

AI tools were used as a development assistant for planning, code drafting, debugging, test planning, and documentation. I reviewed, tested, corrected, and understood the submitted code before committing it.

AI helped with:

- Breaking the task into phases
- Drafting model structures
- Suggesting XML views
- Planning security groups
- Writing documentation
- Debugging Odoo 19 compatibility issues

---

## 15. Explain Errors Found and Fixed

Mention these examples:

- Wrong security group XML IDs were corrected.
- Missing sequence XML file was added.
- Unsupported Odoo 19 `states` field parameter was removed.
- Odoo 19 XML search view syntax was corrected.
- Fund Account dropdown domain/company issue was fixed.
- Bill remaining balance computation was implemented and corrected.
- Docker files were added, but Docker was not tested locally because Docker was not installed on the development machine.

---

## 16. Known Limitations

Mention clearly:

- Fund Transfer module is not implemented.
- Dashboard is not implemented.
- Bank email integration is not implemented.
- Dynamic configurable approval rule engine is not implemented.
- Live server deployment is not completed.
- Direct Odoo Vendor Bill integration is not implemented.
- A custom fund bill model was implemented instead.

---

## 17. Closing Statement

Suggested closing:

This implementation prioritizes the main fund management workflow, approval sequence, data integrity, access control, computed balances, bill control, audit tracking, and maintainable Odoo module structure. I understand the implementation and can explain or modify the workflow during the technical interview.
