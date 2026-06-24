# Architecture Explanation — NN Fund Management

## 1. Purpose of the Module

The `nn_fund_management` module is designed to manage fund-related workflows in Odoo 19. It covers fund accounts, incoming funds, fund allocations, fund requisitions, bill control, approval stages, balance protection, access control, and audit tracking.

The main goal is to ensure that financial movements are controlled through workflow states and that the same money cannot be reused, over-allocated, or over-billed.

---

## 2. High-Level Business Flow

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

Explanation:

1. Incoming money is first recorded through Incoming Funds.
2. Confirmed incoming funds increase the Fund Account's unassigned balance.
3. Fund Allocation assigns available money to a project or expense head.
4. Fund Requisition requests usage of assigned money.
5. Fund Bill records spending against an approved requisition.
6. Chatter and audit fields preserve workflow history.

---

## 3. Main Odoo Models

The module uses the following main models:

- `nn.fund.account`
- `nn.incoming.fund`
- `nn.expense.head`
- `nn.fund.allocation`
- `nn.fund.requisition`
- `nn.fund.bill`

---

## 4. Model Relationship

nn.fund.account
 ├── nn.incoming.fund
 ├── nn.fund.allocation
 └── nn.fund.requisition
       └── nn.fund.bill

Relationship explanation:

- A Fund Account receives incoming funds.
- A Fund Account is used for fund allocations.
- A Fund Requisition is linked to a fund account and either a project or an expense head.
- A Fund Bill is linked to an approved fund requisition.
- Bill amounts are used to compute total billed amount and remaining billable amount.

---

## 5. Fund Account Layer

The Fund Account model is the central balance container.

It tracks:

- Total received amount
- Available unassigned balance
- Held balance
- Assigned balance
- Company
- Currency
- Account type

The balance fields are computed from confirmed incoming funds and allocation workflow records. Users should not manually edit calculated balances.

---

## 6. Incoming Fund Layer

Incoming Funds represent money received into a fund account.

Workflow:

Draft → Submitted → Confirmed → Cancelled

Important rules:

- Only authorized finance users can submit or confirm incoming funds.
- Confirmed incoming funds increase available unassigned balance.
- Duplicate transaction references are blocked per fund account.
- Confirmed records cannot be directly modified without workflow logic.

---

## 7. Fund Allocation Layer

Fund Allocation moves unassigned money into a project or expense head.

Workflow:

Draft → Submitted → GM Approved → MD Approved → Rejected / Cancelled

Important rules:

- Allocation can target either a project or an expense head.
- The same allocation cannot select both project and expense head.
- On submission, the requested amount moves to held balance.
- Held amount cannot be reused by another request.
- GM approval must happen before MD approval.
- MD approval converts the held amount into assigned amount.
- Rejection or cancellation releases held amount back to unassigned balance.
- Over-allocation is blocked server-side.

---

## 8. Fund Requisition Layer

Fund Requisition requests usage of already assigned project or expense-head money.

Workflow:

Draft → Submitted → GM Approved → MD Approved → Rejected / Cancelled / Closed

Important rules:

- A requisition can be created against either a project or an expense head.
- Target type controls whether project or expense head is selected.
- Approval users and approval dates are recorded.
- Remaining billable amount is computed.
- Direct state editing is blocked.
- Non-draft requisitions are protected from direct editing.

---

## 9. Bill Control Layer

The module uses a custom bill model:

`nn.fund.bill`

Workflow:

Draft → Posted → Cancelled

Important rules:

- A bill must be linked to an approved requisition.
- Only approved requisitions can be used for bills.
- Multiple partial bills are allowed.
- Bill amount cannot exceed the remaining billable amount.
- Posted bill decreases remaining billable amount.
- Cancelled bill restores remaining billable amount.
- Posted bills cannot be deleted directly.
- Bill posting and cancellation are logged in chatter.

---

## 10. Approval Architecture

The approval architecture is based on Odoo security groups and server-side workflow methods.

Main groups:

- Fund User
- Finance User
- GM Approver
- MD Approver
- Fund Administrator

Approval sequence:

Draft
  ↓
Submitted
  ↓
GM Approved
  ↓
MD Approved

Security explanation:

- Finance users handle financial operations such as confirming incoming funds and posting bills.
- GM Approver performs the first approval stage.
- MD Approver performs the final approval stage.
- Fund Administrator has administrative access.
- UI buttons are restricted by group, but Python methods also enforce permission checks.

---

## 11. Security Architecture

Security is implemented through:

- `security/fund_management_security.xml`
- `security/ir.model.access.csv`
- `security/fund_requisition_rules.xml`
- `security/fund_bill_rules.xml`
- Server-side Python permission checks
- Multi-company record rules

The module does not rely only on hiding buttons. Critical workflow actions check user permission at method level.

---

## 12. Double-Spending Prevention

The module prevents duplicate financial usage through workflow-based balance movement.

Double-spending control points:

1. Confirmed incoming funds increase unassigned balance only once.
2. Submitted allocations move money from available balance to held balance.
3. Held allocation amount cannot be used by another allocation.
4. MD-approved allocations move money from held balance to assigned balance.
5. Requisitions reserve approved assigned money for billing.
6. Posted bills reduce remaining billable amount.
7. Cancelled bills restore remaining billable amount without creating extra funds.
8. Over-allocation and over-billing are blocked by server-side validations.

---

## 13. Audit and Traceability

Audit history is maintained through:

- Chatter messages
- Creator fields
- Submitted by fields
- GM approved by fields
- MD approved by fields
- Posted by fields
- Cancelled by fields
- Date/time fields for workflow actions
- State tracking

This helps trace who performed each financial action and when.

---

## 14. Data Integrity Controls

The module includes the following data integrity controls:

- Positive amount constraints
- Duplicate transaction reference blocking
- Project/expense-head mutual exclusivity
- Workflow-only state transitions
- Computed balance fields
- Over-allocation blocking
- Over-billing blocking
- Posted bill deletion restriction
- Cancel/reversal workflow
- Multi-company record rules
- Server-side permission checks

---

## 15. Current Known Limitations

The following assessment items are not fully implemented in the current version:

- Fund Transfer module
- Dashboard
- Bank email integration
- Dynamic configurable approval rule engine
- Live server deployment
- Direct integration with Odoo Vendor Bills

A custom fund bill model was implemented instead of extending Odoo Vendor Bills.
