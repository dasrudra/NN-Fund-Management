from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase


class TestFundAllocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.finance_group = cls.env.ref(
            "nn_fund_management.group_fund_finance"
        )
        cls.fund_user_group = cls.env.ref(
            "nn_fund_management.group_fund_user"
        )
        cls.gm_group = cls.env.ref(
            "nn_fund_management.group_fund_gm_approver"
        )
        cls.md_group = cls.env.ref(
            "nn_fund_management.group_fund_md_approver"
        )

        cls.finance_user = cls.env["res.users"].create(
            {
                "name": "Allocation Finance Tester",
                "login": "allocation.finance.tester",
                "email": "allocation.finance@example.com",
                "company_id": cls.company.id,
                "company_ids": [
                    Command.set(cls.company.ids),
                ],
                "group_ids": [
                    Command.set([cls.finance_group.id]),
                ],
            }
        )

        cls.fund_user = cls.env["res.users"].create(
            {
                "name": "Allocation Read Only Tester",
                "login": "allocation.readonly.tester",
                "email": "allocation.readonly@example.com",
                "company_id": cls.company.id,
                "company_ids": [
                    Command.set(cls.company.ids),
                ],
                "group_ids": [
                    Command.set([cls.fund_user_group.id]),
                ],
            }
        )

        cls.gm_user = cls.env["res.users"].create(
            {
                "name": "Allocation GM Tester",
                "login": "allocation.gm.tester",
                "email": "allocation.gm@example.com",
                "company_id": cls.company.id,
                "company_ids": [
                    Command.set(cls.company.ids),
                ],
                "group_ids": [
                    Command.set([cls.gm_group.id]),
                ],
            }
        )

        cls.md_user = cls.env["res.users"].create(
            {
                "name": "Allocation MD Tester",
                "login": "allocation.md.tester",
                "email": "allocation.md@example.com",
                "company_id": cls.company.id,
                "company_ids": [
                    Command.set(cls.company.ids),
                ],
                "group_ids": [
                    Command.set([cls.md_group.id]),
                ],
            }
        )

        cls.fund_account = cls.env["nn.fund.account"].create(
            {
                "name": "Allocation Test Fund Account",
                "code": "ALLOC-TEST-BANK-001",
                "account_type": "bank",
                "company_id": cls.company.id,
            }
        )

        incoming = cls.env["nn.incoming.fund"].with_user(
            cls.finance_user
        ).create(
            {
                "fund_account_id": cls.fund_account.id,
                "transaction_reference": "ALLOC-INCOMING-001",
                "transaction_date": fields.Date.today(),
                "source_name": "Allocation Test Source",
                "payment_method": "bank_transfer",
                "amount": 1000000.0,
            }
        )
        incoming.action_submit()
        incoming.action_confirm()

        cls.project = cls.env["project.project"].create(
            {
                "name": "Allocation Test Project",
                "company_id": cls.company.id,
            }
        )

        cls.expense_head = cls.env["nn.expense.head"].create(
            {
                "name": "Allocation Test Expense Head",
                "code": "ALLOC-EXP-001",
                "company_id": cls.company.id,
            }
        )

        cls.Allocation = cls.env["nn.fund.allocation"]

    def _allocation_values(self, **overrides):
        values = {
            "fund_account_id": self.fund_account.id,
            "allocation_type": "project",
            "project_id": self.project.id,
            "allocation_date": fields.Date.today(),
            "purpose": "Project setup allocation",
            "amount": 400000.0,
        }
        values.update(overrides)
        return values

    def _create_allocation(self, **overrides):
        return self.Allocation.with_user(
            self.finance_user
        ).create(
            self._allocation_values(**overrides)
        )

    def _refresh_account_balances(self):
        self.fund_account.invalidate_recordset(
            [
                "total_received",
                "unassigned_balance",
                "held_balance",
                "assigned_balance",
            ]
        )

    def test_submit_allocation_places_amount_on_hold(self):
        allocation = self._create_allocation()

        allocation.action_submit()

        self._refresh_account_balances()

        self.assertEqual(allocation.state, "submitted")
        self.assertEqual(self.fund_account.total_received, 1000000.0)
        self.assertEqual(self.fund_account.unassigned_balance, 600000.0)
        self.assertEqual(self.fund_account.held_balance, 400000.0)
        self.assertEqual(self.fund_account.assigned_balance, 0.0)

    def test_gm_and_md_approval_moves_hold_to_assigned(self):
        allocation = self._create_allocation()

        allocation.action_submit()
        allocation.with_user(self.gm_user).action_gm_approve()

        self._refresh_account_balances()

        self.assertEqual(allocation.state, "gm_approved")
        self.assertEqual(self.fund_account.unassigned_balance, 600000.0)
        self.assertEqual(self.fund_account.held_balance, 400000.0)
        self.assertEqual(self.fund_account.assigned_balance, 0.0)

        allocation.with_user(self.md_user).action_md_approve()

        self._refresh_account_balances()

        self.assertEqual(allocation.state, "md_approved")
        self.assertEqual(self.fund_account.unassigned_balance, 600000.0)
        self.assertEqual(self.fund_account.held_balance, 0.0)
        self.assertEqual(self.fund_account.assigned_balance, 400000.0)

    def test_over_allocation_is_blocked(self):
        allocation = self._create_allocation(
            amount=1200000.0,
            purpose="Over allocation test",
        )

        with self.assertRaises(UserError):
            allocation.action_submit()

    def test_gm_rejection_releases_held_balance(self):
        allocation = self._create_allocation()

        allocation.action_submit()

        self._refresh_account_balances()
        self.assertEqual(self.fund_account.held_balance, 400000.0)

        allocation.with_user(self.gm_user).action_reject()

        self._refresh_account_balances()

        self.assertEqual(allocation.state, "rejected")
        self.assertEqual(self.fund_account.unassigned_balance, 1000000.0)
        self.assertEqual(self.fund_account.held_balance, 0.0)
        self.assertEqual(self.fund_account.assigned_balance, 0.0)

    def test_md_rejection_releases_held_balance(self):
        allocation = self._create_allocation()

        allocation.action_submit()
        allocation.with_user(self.gm_user).action_gm_approve()
        allocation.with_user(self.md_user).action_reject()

        self._refresh_account_balances()

        self.assertEqual(allocation.state, "rejected")
        self.assertEqual(self.fund_account.unassigned_balance, 1000000.0)
        self.assertEqual(self.fund_account.held_balance, 0.0)
        self.assertEqual(self.fund_account.assigned_balance, 0.0)

    def test_fund_user_cannot_create_allocation(self):
        with self.assertRaises(AccessError):
            self.Allocation.with_user(
                self.fund_user
            ).create(
                self._allocation_values(
                    purpose="Read only allocation test"
                )
            )

    def test_finance_user_cannot_gm_approve(self):
        allocation = self._create_allocation()

        allocation.action_submit()

        with self.assertRaises(AccessError):
            allocation.with_user(
                self.finance_user
            ).action_gm_approve()

    def test_gm_user_cannot_md_approve(self):
        allocation = self._create_allocation()

        allocation.action_submit()
        allocation.with_user(self.gm_user).action_gm_approve()

        with self.assertRaises(AccessError):
            allocation.with_user(
                self.gm_user
            ).action_md_approve()

    def test_submitted_allocation_cannot_be_edited(self):
        allocation = self._create_allocation()

        allocation.action_submit()

        with self.assertRaises(UserError):
            allocation.write(
                {
                    "amount": 200000.0,
                }
            )

    def test_non_positive_allocation_is_blocked(self):
        with self.assertRaises(ValidationError):
            self._create_allocation(
                amount=0.0,
                purpose="Zero allocation test",
            )

    def test_expense_head_allocation_target_is_supported(self):
        allocation = self._create_allocation(
            allocation_type="expense_head",
            project_id=False,
            expense_head_id=self.expense_head.id,
            purpose="Expense head allocation",
            amount=250000.0,
        )

        allocation.action_submit()
        allocation.with_user(self.gm_user).action_gm_approve()
        allocation.with_user(self.md_user).action_md_approve()

        self._refresh_account_balances()

        self.assertEqual(allocation.state, "md_approved")
        self.assertEqual(self.fund_account.assigned_balance, 250000.0)