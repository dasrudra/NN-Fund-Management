from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class NnFundAccount(models.Model):
    _name = "nn.fund.account"
    _description = "Fund Account"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "company_id, code, name"
    _check_company_auto = True

    _code_company_unique = models.Constraint(
        "unique(code, company_id)",
        "The fund account code must be unique within each company.",
    )

    name = fields.Char(
        string="Account Name",
        required=True,
        tracking=True,
        index=True,
    )
    code = fields.Char(
        string="Account Code",
        required=True,
        copy=False,
        tracking=True,
        index=True,
        help="Unique account identifier within the selected company.",
    )
    account_type = fields.Selection(
        selection=[
            ("bank", "Bank"),
            ("cash", "Cash"),
            ("other", "Other"),
        ],
        string="Account Type",
        required=True,
        default="bank",
        tracking=True,
    )
    bank_id = fields.Many2one(
        comodel_name="res.bank",
        string="Bank",
        tracking=True,
    )
    account_number = fields.Char(
        string="Account Number",
        copy=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    incoming_fund_ids = fields.One2many(
        comodel_name="nn.incoming.fund",
        inverse_name="fund_account_id",
        string="Incoming Funds",
    )
    incoming_fund_count = fields.Integer(
        string="Incoming Fund Count",
        compute="_compute_incoming_fund_count",
    )
    allocation_ids = fields.One2many(
        comodel_name="nn.fund.allocation",
        inverse_name="fund_account_id",
        string="Fund Allocations",
    )
    allocation_count = fields.Integer(
        string="Allocation Count",
        compute="_compute_allocation_count",
    )
    total_received = fields.Monetary(
        string="Total Received",
        currency_field="currency_id",
        compute="_compute_fund_balances",
        store=True,
        readonly=True,
    )
    unassigned_balance = fields.Monetary(
        string="Unassigned Balance",
        currency_field="currency_id",
        compute="_compute_fund_balances",
        store=True,
        readonly=True,
    )
    held_balance = fields.Monetary(
        string="Held Balance",
        currency_field="currency_id",
        compute="_compute_fund_balances",
        store=True,
        readonly=True,
    )
    assigned_balance = fields.Monetary(
        string="Assigned Balance",
        currency_field="currency_id",
        compute="_compute_fund_balances",
        store=True,
        readonly=True,
    )
    note = fields.Text(
        string="Notes",
    )
    active = fields.Boolean(
        default=True,
        tracking=True,
    )

    @api.depends("incoming_fund_ids")
    def _compute_incoming_fund_count(self):
        for record in self:
            record.incoming_fund_count = len(record.incoming_fund_ids)

    @api.depends("allocation_ids")
    def _compute_allocation_count(self):
        for record in self:
            record.allocation_count = len(record.allocation_ids)

    @api.depends(
        "incoming_fund_ids.amount",
        "incoming_fund_ids.state",
        "allocation_ids.amount",
        "allocation_ids.state",
    )
    def _compute_fund_balances(self):
        for record in self:
            confirmed_total = sum(
                incoming.amount
                for incoming in record.incoming_fund_ids
                if incoming.state == "confirmed"
            )

            held_total = sum(
                allocation.amount
                for allocation in record.allocation_ids
                if allocation.state in ("submitted", "gm_approved")
            )

            assigned_total = sum(
                allocation.amount
                for allocation in record.allocation_ids
                if allocation.state == "md_approved"
            )

            record.total_received = confirmed_total
            record.held_balance = held_total
            record.assigned_balance = assigned_total
            record.unassigned_balance = (
                confirmed_total - held_total - assigned_total
            )

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get("code"):
                values["code"] = values["code"].strip().upper()

            if values.get("name"):
                values["name"] = values["name"].strip()

        return super().create(vals_list)

    def write(self, values):
        values = dict(values)

        if values.get("code"):
            values["code"] = values["code"].strip().upper()

        if values.get("name"):
            values["name"] = values["name"].strip()

        return super().write(values)

    @api.constrains("name", "code")
    def _check_required_text_values(self):
        for record in self:
            if not record.name or not record.name.strip():
                raise ValidationError(
                    _("The fund account name cannot be empty.")
                )

            if not record.code or not record.code.strip():
                raise ValidationError(
                    _("The fund account code cannot be empty.")
                )

    def action_open_incoming_funds(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id(
            "nn_fund_management.action_nn_incoming_fund"
        )

        action["domain"] = [
            ("fund_account_id", "=", self.id),
        ]
        action["context"] = dict(
            self.env.context,
            default_fund_account_id=self.id,
        )

        return action

    def action_open_allocations(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id(
            "nn_fund_management.action_nn_fund_allocation"
        )

        action["domain"] = [
            ("fund_account_id", "=", self.id),
        ]
        action["context"] = dict(
            self.env.context,
            default_fund_account_id=self.id,
        )

        return action