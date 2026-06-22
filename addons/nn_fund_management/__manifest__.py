{
    "name": "NN Fund Management",
    "summary": (
        "Secure fund allocation, requisition, transfer, "
        "approval, and expenditure control"
    ),
    "description": """
NN Fund Management
==================

A secure fund management application for recording incoming funds,
allocating funds to projects or expense heads, processing requisitions,
controlling bills, transferring funds, managing multi-level approvals,
and maintaining complete financial audit trails.
    """,
    "author": "Rudra Das",
    "website": "https://github.com/dasrudra/NN-Fund-Management",
    "category": "Accounting",
    "version": "19.0.4.0.0",
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
    "security/fund_management_security.xml",
    "security/fund_requisition_rules.xml",
    "security/ir.model.access.csv",
    "views/fund_account_views.xml",
    "views/expense_head_views.xml",
    "views/incoming_fund_views.xml",
    "views/fund_allocation_views.xml",
    "views/fund_requisition_views.xml",
    "views/fund_management_menus.xml",
],
    "application": True,
    "installable": True,
    "auto_install": False,
}
