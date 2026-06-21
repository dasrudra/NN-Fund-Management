from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase
from odoo.tools import mute_logger


class TestIncomingFund(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        cls.fund_account = cls.env["nn.fund.account"].create(
            {
                "name": "Incoming Fund Test Account",
                "code": "TEST-BANK-001",
                "account_type": "bank",
                "company_id": cls.company.id,
            }
        )

        cls.finance_group = cls.env.ref(
            "nn_fund_management.group_fund_finance"
        )
        cls.fund_user_group = cls.env.ref(
            "nn_fund_management.group_fund_user"
        )

        cls.finance_user = cls.env["res.users"].create(
            {
                "name": "Incoming Fund Finance Tester",
                "login": "incoming.fund.finance.tester",
                "email": "incoming.fund.finance@example.com",
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
                "name": "Incoming Fund Read Only Tester",
                "login": "incoming.fund.readonly.tester",
                "email": "incoming.fund.readonly@example.com",
                "company_id": cls.company.id,
                "company_ids": [
                    Command.set(cls.company.ids),
                ],
                "group_ids": [
                    Command.set([cls.fund_user_group.id]),
                ],
            }
        )

        cls.IncomingFund = cls.env["nn.incoming.fund"]

    def _incoming_values(self, **overrides):
        values = {
            "fund_account_id": self.fund_account.id,
            "transaction_reference": "TEST-TXN-001",
            "transaction_date": fields.Date.today(),
            "source_name": "Test Funding Source",
            "payment_method": "bank_transfer",
            "amount": 1000.0,
        }
        values.update(overrides)
        return values

    def _create_incoming_fund(self, **overrides):
        return self.IncomingFund.with_user(
            self.finance_user
        ).create(
            self._incoming_values(**overrides)
        )

    def test_finance_user_can_confirm_incoming_fund(self):
        incoming = self._create_incoming_fund()

        self.assertEqual(incoming.state, "draft")

        incoming.action_submit()
        self.assertEqual(incoming.state, "submitted")
        self.assertEqual(
            incoming.submitted_by_id,
            self.finance_user,
        )

        incoming.action_confirm()
        self.assertEqual(incoming.state, "confirmed")
        self.assertEqual(
            incoming.confirmed_by_id,
            self.finance_user,
        )

    def test_confirmation_updates_account_balance(self):
        incoming = self._create_incoming_fund(
            transaction_reference="TEST-TXN-BALANCE",
            amount=1000000.0,
        )

        incoming.action_submit()
        incoming.action_confirm()

        self.fund_account.invalidate_recordset(
            [
                "total_received",
                "unassigned_balance",
                "held_balance",
                "assigned_balance",
            ]
        )

        self.assertEqual(
            self.fund_account.total_received,
            1000000.0,
        )
        self.assertEqual(
            self.fund_account.unassigned_balance,
            1000000.0,
        )
        self.assertEqual(
            self.fund_account.held_balance,
            0.0,
        )
        self.assertEqual(
            self.fund_account.assigned_balance,
            0.0,
        )

    def test_duplicate_reference_is_blocked_per_account(self):
        self._create_incoming_fund(
            transaction_reference="TEST-DUPLICATE-001"
        )

        with mute_logger("odoo.sql_db"), self.assertRaises(
            ValidationError
        ):
            with self.env.cr.savepoint():
                self._create_incoming_fund(
                    transaction_reference="test-duplicate-001"
                )

    def test_non_positive_amount_is_blocked(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(
            ValidationError
        ):
            with self.env.cr.savepoint():
                self._create_incoming_fund(
                    transaction_reference="TEST-ZERO-AMOUNT",
                    amount=0.0,
                )

    def test_fund_user_cannot_create_incoming_fund(self):
        with self.assertRaises(AccessError):
            self.IncomingFund.with_user(
                self.fund_user
            ).create(
                self._incoming_values(
                    transaction_reference="TEST-READONLY-001"
                )
            )

    def test_fund_user_cannot_submit_incoming_fund(self):
        incoming = self._create_incoming_fund(
            transaction_reference="TEST-SECURITY-001"
        )

        with self.assertRaises(AccessError):
            incoming.with_user(
                self.fund_user
            ).action_submit()

    def test_direct_state_manipulation_is_blocked(self):
        incoming = self._create_incoming_fund(
            transaction_reference="TEST-STATE-001"
        )

        with self.assertRaises(UserError):
            incoming.write(
                {
                    "state": "confirmed",
                }
            )

    def test_submitted_financial_data_is_immutable(self):
        incoming = self._create_incoming_fund(
            transaction_reference="TEST-LOCK-001"
        )

        incoming.action_submit()

        with self.assertRaises(UserError):
            incoming.write(
                {
                    "amount": 2000.0,
                }
            )

    def test_confirmed_fund_cannot_be_cancelled(self):
        incoming = self._create_incoming_fund(
            transaction_reference="TEST-CANCEL-001"
        )

        incoming.action_submit()
        incoming.action_confirm()

        with self.assertRaises(UserError):
            incoming.action_cancel()
            