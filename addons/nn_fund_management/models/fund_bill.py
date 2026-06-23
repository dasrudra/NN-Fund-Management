from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class NnFundBill(models.Model):
    _name = "nn.fund.bill"
    _description = "Fund Bill"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "bill_date desc, id desc"
    _check_company_auto = True

    _amount_positive = models.Constraint(
        "CHECK (amount > 0)",
        "The bill amount must be greater than zero.",
    )

    name = fields.Char(
        string="Bill Number",
        required=True,
        readonly=True,
        copy=False,
        default="/",
        index=True,
        tracking=True,
    )
    requisition_id = fields.Many2one(
        comodel_name="nn.fund.requisition",
        string="Approved Requisition",
        required=True,
        ondelete="restrict",
        check_company=True,
        index=True,
        tracking=True,
        domain="[('state', 'in', ['md_approved', 'approved'])]",
    )
    fund_account_id = fields.Many2one(
        comodel_name="nn.fund.account",
        string="Fund Account",
        related="requisition_id.fund_account_id",
        store=True,
        readonly=True,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="requisition_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="requisition_id.currency_id",
        store=True,
        readonly=True,
    )
    target_type = fields.Selection(
        related="requisition_id.target_type",
        string="Bill Against",
        store=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        string="Project",
        related="requisition_id.project_id",
        store=True,
        readonly=True,
        index=True,
    )
    expense_head_id = fields.Many2one(
        comodel_name="nn.expense.head",
        string="Expense Head",
        related="requisition_id.expense_head_id",
        store=True,
        readonly=True,
        index=True,
    )
    bill_date = fields.Date(
        string="Bill Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    vendor_name = fields.Char(
        string="Vendor / Payee",
        required=True,
        tracking=True,
    )
    reference = fields.Char(
        string="Vendor Bill Reference",
        tracking=True,
    )
    description = fields.Char(
        string="Description",
        required=True,
        tracking=True,
    )
    amount = fields.Monetary(
        string="Bill Amount",
        required=True,
        currency_field="currency_id",
        tracking=True,
    )
    supporting_file = fields.Binary(
        string="Bill Attachment",
        attachment=True,
        copy=False,
    )
    supporting_filename = fields.Char(
        string="Bill Attachment Filename",
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="draft",
        copy=False,
        index=True,
        tracking=True,
    )
    posted_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Posted By",
        readonly=True,
        copy=False,
    )
    posted_date = fields.Datetime(
        string="Posted On",
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
    cancellation_reason = fields.Text(
        string="Cancellation Reason",
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            values["state"] = "draft"
            self._prepare_and_validate_values(values)

            if not values.get("name") or values["name"] == "/":
                values["name"] = (
                    self.env["ir.sequence"].next_by_code("nn.fund.bill")
                    or "/"
                )

        records = super().create(vals_list)
        records._check_requisition_is_billable()
        return records

    def write(self, values):
        values = dict(values)

        if (
            "state" in values
            and not self.env.context.get("allow_fund_bill_state_transition")
        ):
            raise UserError(
                _(
                    "The bill status cannot be changed directly. "
                    "Use the workflow buttons."
                )
            )

        protected_fields = {
            "requisition_id",
            "bill_date",
            "vendor_name",
            "reference",
            "description",
            "amount",
            "supporting_file",
            "supporting_filename",
        }

        if (
            protected_fields.intersection(values)
            and not self.env.context.get("allow_fund_bill_state_transition")
        ):
            locked_records = self.filtered(
                lambda record: record.state != "draft"
            )
            if locked_records:
                raise UserError(
                    _("Posted or cancelled bills cannot be edited.")
                )

        self._prepare_and_validate_values(values, partial=True)

        result = super().write(values)
        self._check_requisition_is_billable()

        return result

    def unlink(self):
        protected_records = self.filtered(
            lambda record: record.state == "posted"
        )

        if protected_records:
            raise UserError(
                _(
                    "Posted bills cannot be deleted. Cancel the bill "
                    "through the workflow instead."
                )
            )

        return super().unlink()

    def _prepare_and_validate_values(self, values, partial=False):
        if values.get("vendor_name"):
            values["vendor_name"] = values["vendor_name"].strip()

        if values.get("description"):
            values["description"] = values["description"].strip()

        if "amount" in values:
            self._validate_amount_value(values.get("amount"))

        if not partial or "vendor_name" in values:
            vendor_name = values.get("vendor_name")
            if not vendor_name or not vendor_name.strip():
                raise ValidationError(_("Vendor / payee cannot be empty."))

        if not partial or "description" in values:
            description = values.get("description")
            if not description or not description.strip():
                raise ValidationError(_("Bill description cannot be empty."))

    def _validate_amount_value(self, amount):
        if amount is None:
            return

        if amount <= 0:
            raise ValidationError(_("The bill amount must be greater than zero."))

    @api.constrains("amount")
    def _check_positive_amount(self):
        for record in self:
            record._validate_amount_value(record.amount)

    @api.constrains("requisition_id")
    def _check_requisition_is_billable(self):
        for record in self:
            if not record.requisition_id:
                continue

            if record.requisition_id.state not in ("md_approved", "approved"):
                raise ValidationError(
                    _(
                        "Only MD-approved or approved requisitions can "
                        "be used for bills."
                    )
                )

    def _check_finance_user(self):
        if not self.env.user.has_group(
            "nn_fund_management.group_fund_finance"
        ):
            raise AccessError(
                _(
                    "Only a Finance User or Fund Administrator can "
                    "perform this action."
                )
            )

    def _check_available_billable_amount(self):
        for record in self:
            requisition = record.requisition_id

            if requisition.state not in ("md_approved", "approved"):
                raise UserError(
                    _("Only approved requisitions can be billed.")
                )

            if record.amount > requisition.remaining_billable_amount:
                raise UserError(
                    _(
                        "The bill amount cannot exceed the remaining "
                        "billable amount of the requisition."
                    )
                )

    def action_post(self):
        self._check_finance_user()

        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft bills can be posted."))

            record._check_available_billable_amount()

            record.with_context(
                allow_fund_bill_state_transition=True
            ).write(
                {
                    "state": "posted",
                    "posted_by_id": self.env.user.id,
                    "posted_date": fields.Datetime.now(),
                    "cancelled_by_id": False,
                    "cancelled_date": False,
                    "cancellation_reason": False,
                }
            )

            record.message_post(
                body=_("The fund bill was posted and marked as spent.")
            )
            record.requisition_id.message_post(
                body=_(
                    "Bill %(bill)s was posted for amount %(amount)s."
                )
                % {
                    "bill": record.name,
                    "amount": record.amount,
                }
            )

        return True

    def action_cancel(self):
        self._check_finance_user()

        for record in self:
            if record.state != "posted":
                raise UserError(_("Only posted bills can be cancelled."))

            record.with_context(
                allow_fund_bill_state_transition=True
            ).write(
                {
                    "state": "cancelled",
                    "cancelled_by_id": self.env.user.id,
                    "cancelled_date": fields.Datetime.now(),
                    "cancellation_reason": _(
                        "Cancelled through bill control workflow."
                    ),
                }
            )

            record.message_post(
                body=_(
                    "The fund bill was cancelled. The amount is now "
                    "available again as remaining billable balance."
                )
            )
            record.requisition_id.message_post(
                body=_("Bill %(bill)s was cancelled.")
                % {
                    "bill": record.name,
                }
            )

        return True
