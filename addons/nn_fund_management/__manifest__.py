{
    "name": "NN Fund Management",
    "summary": (
        "Secure fund allocation, requisition, bill control, "
        "approval, and balance management"
    ),
    "description": """
NN Fund Management
==================

A secure fund management application for recording incoming funds,
allocating funds to projects or expense heads, processing requisitions,
controlling bills, managing multi-level approvals, and maintaining
financial audit trails.

Implemented scope includes fund accounts, incoming funds, fund allocations,
fund requisitions, custom bill control, access control, record rules,
computed balances, and server-side workflow validation.
    """,
    "author": "Rudra Das",
    "website": "https://github.com/dasrudra/NN-Fund-Management",
    "category": "Accounting",
    "version": "19.0.5.0.1",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "project",
    ],
    "data": [
        "data/incoming_fund_sequence.xml",
        "data/fund_allocation_sequence.xml",
        "data/fund_requisition_sequence.xml",
        "data/fund_bill_sequence.xml",
        "security/fund_management_security.xml",
        "security/fund_requisition_rules.xml",
        "security/fund_bill_rules.xml",
        "security/ir.model.access.csv",
        "views/fund_account_views.xml",
        "views/expense_head_views.xml",
        "views/incoming_fund_views.xml",
        "views/fund_allocation_views.xml",
        "views/fund_requisition_views.xml",
        "views/fund_bill_views.xml",
        "views/fund_management_menus.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
