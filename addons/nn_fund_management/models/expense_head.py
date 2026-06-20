from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class NnExpenseHead(models.Model):
    _name = "nn.expense.head"
    _description = "Expense Head"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, code, name"
    _check_company_auto = True

    _code_company_unique = models.Constraint(
        "unique(code, company_id)",
        "The expense head code must be unique within each company.",
    )

    name = fields.Char(
        string="Expense Head",
        required=True,
        tracking=True,
        index=True,
    )
    code = fields.Char(
        string="Code",
        required=True,
        copy=False,
        tracking=True,
        index=True,
        help="Unique expense-head identifier within the selected company.",
    )
    sequence = fields.Integer(
        default=10,
        help="Determines the ordering of expense heads.",
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
    description = fields.Text(
        string="Description",
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
                    _("The expense head name cannot be empty.")
                )

            if not record.code or not record.code.strip():
                raise ValidationError(
                    _("The expense head code cannot be empty.")
                )