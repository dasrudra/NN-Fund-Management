from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class NnFundAllocation(models.Model):
    _name = "nn.fund.allocation"
    _description = "Fund Allocation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "allocation_date desc, id desc"
    _check_company_auto = True

    _amount_positive = models.Constraint(
        "CHECK (amount > 0)",
        "The allocation amount must be greater than zero.",
    )

    name = fields.Char(
        string="Allocation Number",
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
    allocation_type = fields.Selection(
        selection=[
            ("project", "Project"),
            ("expense_head", "Expense Head"),
        ],
        string="Allocation Type",
        required=True,
        default="project",
        tracking=True,
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        string="Project",
        ondelete="restrict",
        check_company=True,
        tracking=True,
    )
    expense_head_id = fields.Many2one(
        comodel_name="nn.expense.head",
        string="Expense Head",
        ondelete="restrict",
        check_company=True,
        tracking=True,
    )
    allocation_date = fields.Date(
        string="Allocation Date",
        required=True,
        default=fields.Date.context_today,
        index=True,
        tracking=True,
    )
    purpose = fields.Char(
        string="Purpose",
        required=True,
        tracking=True,
    )
    amount = fields.Monetary(
        string="Allocation Amount",
        required=True,
        currency_field="currency_id",
        tracking=True,
    )
    note = fields.Text(
        string="Notes",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("gm_approved", "GM Approved"),
            ("md_approved", "MD Approved"),
            ("rejected", "Rejected"),
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
    gm_approved_by_id = fields.Many2one(
        comodel_name="res.users",
        string="GM Approved By",
        readonly=True,
        copy=False,
    )
    gm_approved_date = fields.Datetime(
        string="GM Approved On",
        readonly=True,
        copy=False,
    )
    md_approved_by_id = fields.Many2one(
        comodel_name="res.users",
        string="MD Approved By",
        readonly=True,
        copy=False,
    )
    md_approved_date = fields.Datetime(
        string="MD Approved On",
        readonly=True,
        copy=False,
    )
    rejected_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Rejected By",
        readonly=True,
        copy=False,
    )
    rejected_date = fields.Datetime(
        string="Rejected On",
        readonly=True,
        copy=False,
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
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
            self._prepare_and_validate_values(values)

            if not values.get("name") or values["name"] == "/":
                values["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "nn.fund.allocation"
                    )
                    or "/"
                )

        return super().create(vals_list)

    def write(self, values):
        values = dict(values)

        if (
            "state" in values
            and not self.env.context.get(
                "allow_fund_allocation_state_transition"
            )
        ):
            raise UserError(
                _(
                    "The allocation status cannot be changed directly. "
                    "Use the workflow buttons."
                )
            )

        protected_fields = {
            "fund_account_id",
            "allocation_type",
            "project_id",
            "expense_head_id",
            "allocation_date",
            "purpose",
            "amount",
            "note",
        }

        if (
            protected_fields.intersection(values)
            and not self.env.context.get(
                "allow_fund_allocation_state_transition"
            )
        ):
            locked_records = self.filtered(
                lambda record: record.state != "draft"
            )

            if locked_records:
                raise UserError(
                    _(
                        "Submitted, approved, rejected, or cancelled "
                        "allocations cannot be edited. Reset the "
                        "allocation to draft before making changes."
                    )
                )

        self._prepare_and_validate_values(values, partial=True)

        result = super().write(values)
        self._check_target_consistency()

        return result

    def unlink(self):
        protected_records = self.filtered(
            lambda record: record.state not in ("draft", "cancelled")
        )

        if protected_records:
            raise UserError(
                _("Only draft or cancelled fund allocations can be deleted.")
            )

        return super().unlink()

    def copy(self, default=None):
        raise UserError(
            _(
                "Fund allocation records cannot be duplicated because "
                "each allocation must follow its own approval workflow."
            )
        )

    def _prepare_and_validate_values(self, values, partial=False):
        if values.get("purpose"):
            values["purpose"] = values["purpose"].strip()

        if "amount" in values:
            self._validate_amount_value(values.get("amount"))

        if not partial or "purpose" in values:
            purpose = values.get("purpose")
            if not purpose or not purpose.strip():
                raise ValidationError(
                    _("The allocation purpose cannot be empty.")
                )

    def _validate_amount_value(self, amount):
        if amount is None:
            return

        if amount <= 0:
            raise ValidationError(
                _("The allocation amount must be greater than zero.")
            )

    @api.constrains(
        "allocation_type",
        "project_id",
        "expense_head_id",
        "fund_account_id",
    )
    def _check_target_consistency(self):
        for record in self:
            if record.allocation_type == "project":
                if not record.project_id:
                    raise ValidationError(
                        _("A project allocation must select a project.")
                    )

                if record.expense_head_id:
                    raise ValidationError(
                        _(
                            "A project allocation cannot also select "
                            "an expense head."
                        )
                    )

            if record.allocation_type == "expense_head":
                if not record.expense_head_id:
                    raise ValidationError(
                        _(
                            "An expense-head allocation must select "
                            "an expense head."
                        )
                    )

                if record.project_id:
                    raise ValidationError(
                        _(
                            "An expense-head allocation cannot also "
                            "select a project."
                        )
                    )

            if (
                record.project_id
                and record.project_id.company_id
                and record.project_id.company_id != record.company_id
            ):
                raise ValidationError(
                    _(
                        "The selected project must belong to the same "
                        "company as the fund account."
                    )
                )

            if (
                record.expense_head_id
                and record.expense_head_id.company_id
                and record.expense_head_id.company_id != record.company_id
            ):
                raise ValidationError(
                    _(
                        "The selected expense head must belong to the "
                        "same company as the fund account."
                    )
                )

    @api.constrains("amount")
    def _check_positive_amount(self):
        for record in self:
            record._validate_amount_value(record.amount)

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

    def _check_gm_approver(self):
        if not self.env.user.has_group(
            "nn_fund_management.group_fund_gm_approver"
        ):
            raise AccessError(
                _(
                    "Only a GM Approver or Fund Administrator can "
                    "perform this action."
                )
            )

    def _check_md_approver(self):
        if not self.env.user.has_group(
            "nn_fund_management.group_fund_md_approver"
        ):
            raise AccessError(
                _(
                    "Only an MD Approver or Fund Administrator can "
                    "perform this action."
                )
            )

    def _check_available_balance_for_submit(self):
        for record in self:
            record.fund_account_id.invalidate_recordset(
                [
                    "total_received",
                    "unassigned_balance",
                    "held_balance",
                    "assigned_balance",
                ]
            )

            available_balance = record.fund_account_id.unassigned_balance

            if record.amount > available_balance:
                raise UserError(
                    _(
                        "Insufficient unassigned balance in %(account)s. "
                        "Available: %(available).2f, Requested: "
                        "%(requested).2f."
                    )
                    % {
                        "account": record.fund_account_id.display_name,
                        "available": available_balance,
                        "requested": record.amount,
                    }
                )

    def action_submit(self):
        self._check_finance_user()

        for record in self:
            if record.state == "submitted":
                continue

            if record.state != "draft":
                raise UserError(
                    _("Only a draft allocation can be submitted.")
                )

            record._check_target_consistency()
            record._check_available_balance_for_submit()

            record.with_context(
                allow_fund_allocation_state_transition=True
            ).write(
                {
                    "state": "submitted",
                    "submitted_by_id": self.env.user.id,
                    "submitted_date": fields.Datetime.now(),
                    "cancelled_by_id": False,
                    "cancelled_date": False,
                    "rejected_by_id": False,
                    "rejected_date": False,
                    "rejection_reason": False,
                }
            )

            record.message_post(
                body=_(
                    "The fund allocation was submitted for GM approval. "
                    "The requested amount is now held."
                )
            )

        return True

    def action_gm_approve(self):
        self._check_gm_approver()

        for record in self:
            if record.state == "gm_approved":
                continue

            if record.state != "submitted":
                raise UserError(
                    _(
                        "Only a submitted allocation can be approved "
                        "by the GM."
                    )
                )

            record.with_context(
                allow_fund_allocation_state_transition=True
            ).write(
                {
                    "state": "gm_approved",
                    "gm_approved_by_id": self.env.user.id,
                    "gm_approved_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "The fund allocation was approved by the GM and "
                    "is waiting for MD approval."
                )
            )

        return True

    def action_md_approve(self):
        self._check_md_approver()

        for record in self:
            if record.state == "md_approved":
                continue

            if record.state != "gm_approved":
                raise UserError(
                    _(
                        "Only a GM-approved allocation can be approved "
                        "by the MD."
                    )
                )

            record.with_context(
                allow_fund_allocation_state_transition=True
            ).write(
                {
                    "state": "md_approved",
                    "md_approved_by_id": self.env.user.id,
                    "md_approved_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "The fund allocation was approved by the MD and "
                    "moved from held balance to assigned balance."
                )
            )

        return True

    def action_reject(self):
        for record in self:
            if record.state == "submitted":
                record._check_gm_approver()
            elif record.state == "gm_approved":
                record._check_md_approver()
            else:
                raise UserError(
                    _(
                        "Only submitted or GM-approved allocations "
                        "can be rejected."
                    )
                )

            record.with_context(
                allow_fund_allocation_state_transition=True
            ).write(
                {
                    "state": "rejected",
                    "rejected_by_id": self.env.user.id,
                    "rejected_date": fields.Datetime.now(),
                    "rejection_reason": _(
                        "Rejected through approval workflow."
                    ),
                }
            )

            record.message_post(
                body=_(
                    "The fund allocation was rejected. The held amount "
                    "has been released back to unassigned balance."
                )
            )

        return True

    def action_cancel(self):
        self._check_finance_user()

        for record in self:
            if record.state == "cancelled":
                continue

            if record.state not in ("draft", "submitted"):
                raise UserError(
                    _(
                        "Only draft or submitted allocations can be "
                        "cancelled by Finance."
                    )
                )

            record.with_context(
                allow_fund_allocation_state_transition=True
            ).write(
                {
                    "state": "cancelled",
                    "cancelled_by_id": self.env.user.id,
                    "cancelled_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "The fund allocation was cancelled. Any held amount "
                    "has been released."
                )
            )

        return True

    def action_reset_to_draft(self):
        self._check_finance_user()

        for record in self:
            if record.state not in ("cancelled", "rejected"):
                raise UserError(
                    _(
                        "Only cancelled or rejected allocations can be "
                        "reset to draft."
                    )
                )

            record.with_context(
                allow_fund_allocation_state_transition=True
            ).write(
                {
                    "state": "draft",
                    "submitted_by_id": False,
                    "submitted_date": False,
                    "gm_approved_by_id": False,
                    "gm_approved_date": False,
                    "md_approved_by_id": False,
                    "md_approved_date": False,
                    "rejected_by_id": False,
                    "rejected_date": False,
                    "rejection_reason": False,
                    "cancelled_by_id": False,
                    "cancelled_date": False,
                }
            )

            record.message_post(
                body=_("The fund allocation was reset to draft.")
            )

        return True