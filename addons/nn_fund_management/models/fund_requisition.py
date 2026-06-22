from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class NnFundRequisition(models.Model):
    _name = "nn.fund.requisition"
    _description = "Fund Requisition"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, id desc"
    _check_company_auto = True

    _amount_positive = models.Constraint(
        "CHECK (amount > 0)",
        "The requisition amount must be greater than zero.",
    )

    name = fields.Char(
        string="Requisition Number",
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
        required=True,
        default=lambda self: self.env.company,
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
    target_type = fields.Selection(
    selection=[
        ("project", "Project"),
        ("expense_head", "Expense Head"),
    ],
    string="Requisition Against",
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
    amount = fields.Monetary(
        string="Requested Amount",
        required=True,
        currency_field="currency_id",
        tracking=True,
    )
    remaining_billable_amount = fields.Monetary(
        string="Remaining Billable Amount",
        currency_field="currency_id",
        compute="_compute_remaining_billable_amount",
        store=True,
        readonly=True,
    )
    purpose = fields.Char(
        string="Purpose",
        required=True,
        tracking=True,
    )
    request_date = fields.Date(
        string="Request Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    required_date = fields.Date(
        string="Required Date",
        tracking=True,
    )
    requested_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Requested By",
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    supporting_file = fields.Binary(
        string="Supporting Attachment",
        attachment=True,
        copy=False,
    )
    supporting_filename = fields.Char(
        string="Supporting Filename",
        copy=False,
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
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("closed", "Closed"),
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
    closed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Closed By",
        readonly=True,
        copy=False,
    )
    closed_date = fields.Datetime(
        string="Closed On",
        readonly=True,
        copy=False,
    )

    @api.depends("amount", "state")
    def _compute_remaining_billable_amount(self):
        for record in self:
            if record.state in ("md_approved", "approved", "closed"):
                record.remaining_billable_amount = record.amount
            else:
                record.remaining_billable_amount = 0.0

    @api.onchange("target_type")
    def _onchange_target_type(self):
        for record in self:
            if record.target_type == "project":
                record.expense_head_id = False
            elif record.target_type == "expense_head":
                record.project_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            values["state"] = "draft"
            self._prepare_and_validate_values(values)

            if not values.get("name") or values["name"] == "/":
                values["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "nn.fund.requisition"
                    )
                    or "/"
                )

        return super().create(vals_list)

    def write(self, values):
        values = dict(values)

        if (
            "state" in values
            and not self.env.context.get(
                "allow_fund_requisition_state_transition"
            )
        ):
            raise UserError(
                _(
                    "The requisition status cannot be changed directly. "
                    "Use the workflow buttons."
                )
            )

        protected_fields = {
            "fund_account_id",
            "project_id",
            "expense_head_id",
            "amount",
            "purpose",
            "request_date",
            "required_date",
            "supporting_file",
            "supporting_filename",
            "note",
        }

        if (
            protected_fields.intersection(values)
            and not self.env.context.get(
                "allow_fund_requisition_state_transition"
            )
        ):
            locked_records = self.filtered(
                lambda record: record.state != "draft"
            )
            if locked_records:
                raise UserError(
                    _(
                        "Submitted, approved, rejected, cancelled, or "
                        "closed requisitions cannot be edited."
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
                _(
                    "Only draft or cancelled fund requisitions can be "
                    "deleted."
                )
            )

        return super().unlink()

    def _prepare_and_validate_values(self, values, partial=False):
        if values.get("purpose"):
            values["purpose"] = values["purpose"].strip()
        if values.get("fund_account_id"):
            fund_account = self.env["nn.fund.account"].browse(
                values["fund_account_id"]
            )
            values["company_id"] = fund_account.company_id.id
        elif not partial and not values.get("company_id"):
            values["company_id"] = self.env.company.id
        if values.get("target_type") == "project":
            values["expense_head_id"] = False
        elif values.get("target_type") == "expense_head":
            values["project_id"] = False

        if "amount" in values:
            self._validate_amount_value(values.get("amount"))

        if not partial or "purpose" in values:
            purpose = values.get("purpose")
            if not purpose or not purpose.strip():
                raise ValidationError(
                    _("The requisition purpose cannot be empty.")
                )

    def _validate_amount_value(self, amount):
        if amount is None:
            return

        if amount <= 0:
            raise ValidationError(
                _("The requisition amount must be greater than zero.")
            )

    @api.constrains("amount")
    def _check_positive_amount(self):
        for record in self:
            record._validate_amount_value(record.amount)

    @api.constrains("target_type", "project_id", "expense_head_id")
    def _check_target_consistency(self):
        for record in self:
            if record.target_type == "project":
                if not record.project_id:
                    raise ValidationError(
                        _("Select a project for this requisition.")
                    )

                if record.expense_head_id:
                    raise ValidationError(
                        _(
                            "A project requisition cannot also select an "
                            "expense head."
                        )
                    )

            elif record.target_type == "expense_head":
                if not record.expense_head_id:
                    raise ValidationError(
                        _("Select an expense head for this requisition.")
                    )

                if record.project_id:
                    raise ValidationError(
                        _(
                            "An expense-head requisition cannot also select "
                            "a project."
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

    def action_submit(self):
        self._check_finance_user()

        for record in self:
            if record.state != "draft":
                raise UserError(
                    _("Only a draft requisition can be submitted.")
                )

            record._check_target_consistency()

            record.with_context(
                allow_fund_requisition_state_transition=True
            ).write(
                {
                    "state": "submitted",
                    "submitted_by_id": self.env.user.id,
                    "submitted_date": fields.Datetime.now(),
                    "rejected_by_id": False,
                    "rejected_date": False,
                    "rejection_reason": False,
                    "cancelled_by_id": False,
                    "cancelled_date": False,
                }
            )

            record.message_post(
                body=_(
                    "The fund requisition was submitted for GM approval."
                )
            )

        return True

    def action_gm_approve(self):
        self._check_gm_approver()

        for record in self:
            if record.state != "submitted":
                raise UserError(
                    _(
                        "Only a submitted requisition can be approved "
                        "by the GM."
                    )
                )

            record.with_context(
                allow_fund_requisition_state_transition=True
            ).write(
                {
                    "state": "gm_approved",
                    "gm_approved_by_id": self.env.user.id,
                    "gm_approved_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "The fund requisition was approved by the GM and "
                    "is waiting for MD approval."
                )
            )

        return True

    def action_md_approve(self):
        self._check_md_approver()

        for record in self:
            if record.state != "gm_approved":
                raise UserError(
                    _(
                        "Only a GM-approved requisition can be approved "
                        "by the MD."
                    )
                )

            record.with_context(
                allow_fund_requisition_state_transition=True
            ).write(
                {
                    "state": "md_approved",
                    "md_approved_by_id": self.env.user.id,
                    "md_approved_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_(
                    "The fund requisition was approved by the MD and "
                    "is now available for bill control."
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
                        "Only submitted or GM-approved requisitions "
                        "can be rejected."
                    )
                )

            record.with_context(
                allow_fund_requisition_state_transition=True
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
                body=_("The fund requisition was rejected.")
            )

        return True

    def action_cancel(self):
        self._check_finance_user()

        for record in self:
            if record.state not in ("draft", "submitted"):
                raise UserError(
                    _(
                        "Only draft or submitted requisitions can be "
                        "cancelled by Finance."
                    )
                )

            record.with_context(
                allow_fund_requisition_state_transition=True
            ).write(
                {
                    "state": "cancelled",
                    "cancelled_by_id": self.env.user.id,
                    "cancelled_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_("The fund requisition was cancelled.")
            )

        return True

    def action_close(self):
        self._check_finance_user()

        for record in self:
            if record.state not in ("md_approved", "approved"):
                raise UserError(
                    _(
                        "Only an approved requisition can be closed."
                    )
                )

            record.with_context(
                allow_fund_requisition_state_transition=True
            ).write(
                {
                    "state": "closed",
                    "closed_by_id": self.env.user.id,
                    "closed_date": fields.Datetime.now(),
                }
            )

            record.message_post(
                body=_("The fund requisition was closed.")
            )

        return True