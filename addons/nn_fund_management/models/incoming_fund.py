from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class NnIncomingFund(models.Model):
    _name = "nn.incoming.fund"
    _description = "Incoming Fund"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "transaction_date desc, id desc"
    _check_company_auto = True

    _transaction_reference_account_unique = models.Constraint(
        "unique(fund_account_id, transaction_reference)",
        (
            "The transaction reference must be unique "
            "within each fund account."
        ),
    )

    _amount_positive = models.Constraint(
        "CHECK (amount > 0)",
        "The incoming amount must be greater than zero.",
    )

    name = fields.Char(
        string="Document Number",
        required=True,
        readonly=True,
        copy=False,
        default="/",
        index=True,
        tracking=True,
    )
    fund_account_id = fields.Many2one(
        comodel_name="nn.fund.account",
        string="Fund Account",
        required=True,
        ondelete="restrict",
        check_company=True,
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="fund_account_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="fund_account_id.currency_id",
        store=True,
        readonly=True,
    )
    transaction_reference = fields.Char(
        string="Transaction Reference",
        required=True,
        copy=False,
        index=True,
        tracking=True,
        help=(
            "Bank transaction ID, cheque number, mobile banking "
            "reference, receipt number, or other external reference."
        ),
    )
    transaction_date = fields.Date(
        string="Transaction Date",
        required=True,
        default=fields.Date.context_today,
        index=True,
        tracking=True,
    )
    source_name = fields.Char(
        string="Sender / Source",
        required=True,
        tracking=True,
    )
    payment_method = fields.Selection(
        selection=[
            ("bank_transfer", "Bank Transfer"),
            ("cash", "Cash"),
            ("cheque", "Cheque"),
            ("mobile_banking", "Mobile Banking"),
            ("other", "Other"),
        ],
        string="Payment Method",
        required=True,
        default="bank_transfer",
        tracking=True,
    )
    amount = fields.Monetary(
        string="Amount",
        required=True,
        currency_field="currency_id",
        tracking=True,
    )
    proof_file = fields.Binary(
        string="Transaction Proof",
        attachment=True,
        copy=False,
    )
    proof_filename = fields.Char(
        string="Proof Filename",
        copy=False,
    )
    note = fields.Text(
        string="Notes",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="draft",
        copy=False,
        index=True,
        tracking=True,
    )
    submitted_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Submitted By",
        readonly=True,
        copy=False,
    )
    submitted_date = fields.Datetime(
        string="Submitted On",
        readonly=True,
        copy=False,
    )
    confirmed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Confirmed By",
        readonly=True,
        copy=False,
    )
    confirmed_date = fields.Datetime(
        string="Confirmed On",
        readonly=True,
        copy=False,
    )
    cancelled_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Cancelled By",
        readonly=True,
        copy=False,
    )
    cancelled_date = fields.Datetime(
        string="Cancelled On",
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            values["state"] = "draft"
            self._prepare_and_validate_create_values(values)

            if not values.get("name") or values["name"] == "/":
                values["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "nn.incoming.fund"
                    )
                    or "/"
                )

        return super().create(vals_list)

    def write(self, values):
        values = dict(values)

        if (
            "state" in values
            and not self.env.context.get(
                "allow_incoming_fund_state_transition"
            )
        ):
            raise UserError(
                _(
                    "The incoming fund status cannot be changed "
                    "directly. Use the workflow buttons."
                )
            )

        protected_fields = {
            "fund_account_id",
            "transaction_reference",
            "transaction_date",
            "source_name",
            "payment_method",
            "amount",
            "proof_file",
            "proof_filename",
            "note",
        }

        if protected_fields.intersection(values):
            locked_records = self.filtered(
                lambda record: record.state != "draft"
            )
            if locked_records:
                raise UserError(
                    _(
                        "Submitted, confirmed, or cancelled incoming "
                        "funds cannot be edited. Cancel and reset the "
                        "record to draft before making changes."
                    )
                )

        self._prepare_and_validate_write_values(values)

        return super().write(values)

    def unlink(self):
        protected_records = self.filtered(
            lambda record: record.state not in ("draft", "cancelled")
        )

        if protected_records:
            raise UserError(
                _(
                    "Only draft or cancelled incoming fund records "
                    "can be deleted."
                )
            )

        return super().unlink()

    def copy(self, default=None):
        raise UserError(
            _(
                "Incoming fund records cannot be duplicated because "
                "each transaction must represent a unique receipt."
            )
        )

    def _prepare_and_validate_create_values(self, values):
        if values.get("transaction_reference"):
            values["transaction_reference"] = (
                values["transaction_reference"].strip().upper()
            )

        if values.get("source_name"):
            values["source_name"] = values["source_name"].strip()

        self._validate_amount_value(values.get("amount"))
        self._validate_required_text_values(values)
        self._validate_unique_reference_values(values)

    def _prepare_and_validate_write_values(self, values):
        if values.get("transaction_reference"):
            values["transaction_reference"] = (
                values["transaction_reference"].strip().upper()
            )

        if values.get("source_name"):
            values["source_name"] = values["source_name"].strip()

        if "amount" in values:
            self._validate_amount_value(values.get("amount"))

        if (
            "transaction_reference" in values
            or "source_name" in values
        ):
            self._validate_required_text_values(values, partial=True)

        if (
            "fund_account_id" in values
            or "transaction_reference" in values
        ):
            for record in self:
                fund_account_id = values.get(
                    "fund_account_id",
                    record.fund_account_id.id,
                )
                transaction_reference = values.get(
                    "transaction_reference",
                    record.transaction_reference,
                )

                self._validate_unique_reference_values(
                    {
                        "fund_account_id": fund_account_id,
                        "transaction_reference": transaction_reference,
                    },
                    exclude_record=record,
                )

    def _validate_amount_value(self, amount):
        if amount is None:
            return

        if amount <= 0:
            raise ValidationError(
                _("The incoming amount must be greater than zero.")
            )

    def _validate_required_text_values(self, values, partial=False):
        if not partial or "transaction_reference" in values:
            transaction_reference = values.get("transaction_reference")
            if (
                not transaction_reference
                or not transaction_reference.strip()
            ):
                raise ValidationError(
                    _("The transaction reference cannot be empty.")
                )

        if not partial or "source_name" in values:
            source_name = values.get("source_name")
            if not source_name or not source_name.strip():
                raise ValidationError(
                    _("The sender or source cannot be empty.")
                )

    def _validate_unique_reference_values(
        self,
        values,
        exclude_record=None,
    ):
        fund_account_id = values.get("fund_account_id")
        transaction_reference = values.get("transaction_reference")

        if not fund_account_id or not transaction_reference:
            return

        domain = [
            ("fund_account_id", "=", fund_account_id),
            (
                "transaction_reference",
                "=",
                transaction_reference.strip().upper(),
            ),
        ]

        if exclude_record:
            domain.append(("id", "!=", exclude_record.id))

        duplicate = self.search(domain, limit=1)

        if duplicate:
            raise ValidationError(
                _(
                    "The transaction reference must be unique "
                    "within each fund account."
                )
            )

    @api.constrains("transaction_reference", "source_name")
    def _check_required_text_values(self):
        for record in self:
            if (
                not record.transaction_reference
                or not record.transaction_reference.strip()
            ):
                raise ValidationError(
                    _("The transaction reference cannot be empty.")
                )

            if not record.source_name or not record.source_name.strip():
                raise ValidationError(
                    _("The sender or source cannot be empty.")
                )

    @api.constrains("amount")
    def _check_positive_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(
                    _("The incoming amount must be greater than zero.")
                )

    @api.constrains("fund_account_id", "transaction_reference")
    def _check_unique_transaction_reference_per_account(self):
        for record in self:
            self._validate_unique_reference_values(
                {
                    "fund_account_id": record.fund_account_id.id,
                    "transaction_reference": record.transaction_reference,
                },
                exclude_record=record,
            )

    def _check_finance_user(self):
        if not self.env.user.has_group(
            "nn_fund_management.group_fund_finance"
        ):
            raise AccessError(
                _(
                    "Only a Finance User or Fund Administrator "
                    "can perform this action."
                )
            )

    def action_submit(self):
        self._check_finance_user()

        for record in self:
            if record.state == "submitted":
                continue

            if record.state != "draft":
                raise UserError(
                    _("Only a draft incoming fund can be submitted.")
                )

            record.with_context(
                allow_incoming_fund_state_transition=True
            ).write(
                {
                    "state": "submitted",
                    "submitted_by_id": self.env.user.id,
                    "submitted_date": fields.Datetime.now(),
                    "cancelled_by_id": False,
                    "cancelled_date": False,
                }
            )

            record.message_post(
                body=_("The incoming fund was submitted for confirmation.")
            )

        return True

    def action_confirm(self):
        self._check_finance_user()

        for record in self:
            if record.state == "confirmed":
                continue

            if record.state != "submitted":
                raise UserError(
                    _("Only a submitted incoming fund can be confirmed.")
                )

            record.with_context(
                allow_incoming_fund_state_transition=True
            ).write(
                {
                    "state": "confirmed",
                    "confirmed_by_id": self.env.user.id,
                    "confirmed_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "The incoming fund was confirmed and added "
                    "to the unassigned account balance."
                )
            )

        return True

    def action_cancel(self):
        self._check_finance_user()

        for record in self:
            if record.state == "cancelled":
                continue

            if record.state == "confirmed":
                raise UserError(
                    _(
                        "A confirmed incoming fund cannot be cancelled "
                        "directly because it has already affected the "
                        "available balance."
                    )
                )

            if record.state not in ("draft", "submitted"):
                raise UserError(
                    _(
                        "Only draft or submitted incoming funds "
                        "can be cancelled."
                    )
                )

            record.with_context(
                allow_incoming_fund_state_transition=True
            ).write(
                {
                    "state": "cancelled",
                    "cancelled_by_id": self.env.user.id,
                    "cancelled_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_("The incoming fund was cancelled.")
            )

        return True

    def action_reset_to_draft(self):
        self._check_finance_user()

        for record in self:
            if record.state != "cancelled":
                raise UserError(
                    _("Only a cancelled incoming fund can be reset to draft.")
                )

            record.with_context(
                allow_incoming_fund_state_transition=True
            ).write(
                {
                    "state": "draft",
                    "submitted_by_id": False,
                    "submitted_date": False,
                    "confirmed_by_id": False,
                    "confirmed_date": False,
                    "cancelled_by_id": False,
                    "cancelled_date": False,
                }
            )

            record.message_post(
                body=_("The incoming fund was reset to draft.")
            )

        return True
