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
    note = fields.Text(
        string="Notes",
    )
    active = fields.Boolean(
        default=True,
        tracking=True,
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