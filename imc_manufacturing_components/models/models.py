# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class MrpComponents(models.Model):
    _name = "mrp.components"
    _description = "Manufacturing Components"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True, tracking=True)
    is_valide = fields.Boolean(string="Is Valid", default=False, tracking=True,
                               help="Only one Components record can be marked as valid.")
    move_raw_ids = fields.One2many(
        "stock.move", "component_id",
        string="Component Moves",
        help="Template raw moves to be used for auto-filling BoM lines."
    )
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company, index=True
    )

    @api.constrains("is_valide")
    def _check_single_valid(self):
        """Allow only one mrp.components with is_valide = True (globally)."""
        for rec in self:
            if rec.is_valide:
                other = self.search([
                    ('is_valide', '=', True),
                    ('id', '!=', rec.id)
                ], limit=1)
                if other:
                    raise ValidationError(_("Only one Components record can be marked as Valid at a time."))


class StockMove(models.Model):
    _inherit = "stock.move"

    component_id = fields.Many2one(
        "mrp.components",
        string="Component",
        ondelete="set null",
        index=True,
    )

    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        compute='_compute_product_uom_id', store=True, readonly=False, precompute=True,

        ondelete="restrict",
    )

    product_uom_qty = fields.Float(string="Qty Ordered")


    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id or False

    def _find_prod_location(self, company_id):
        prod = self.env.ref('stock.stock_location_production', raise_if_not_found=False)
        if prod and (not prod.company_id or prod.company_id.id == company_id):
            return prod.id
        # أي موقع إنتاج للشركة أو عام
        loc = self.env['stock.location'].search([
            ('usage', '=', 'production'),
            ('company_id', 'in', [False, company_id])
        ], limit=1)
        return loc.id if loc else False

    def _find_internal_location(self, company_id):
        stock_loc = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if stock_loc and (not stock_loc.company_id or stock_loc.company_id.id == company_id):
            return stock_loc.id
        # أي موقع داخلي للشركة أو عام
        loc = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [False, company_id])
        ], order="id", limit=1)
        return loc.id if loc else False

    @api.model_create_multi
    def create(self, vals_list):
        res_vals = []
        for vals in vals_list:
            # لو جاي من تاب Components أو فيه component_id
            comp = False
            if vals.get('component_id'):
                comp = self.env['mrp.components'].browse(vals['component_id'])
            elif self.env.context.get('default_component_id'):
                comp = self.env['mrp.components'].browse(self.env.context['default_component_id'])

            company_id = vals.get('company_id') or (comp.company_id.id if comp else self.env.company.id)
            vals.setdefault('company_id', company_id)

            # ضَبّط المواقع الإلزامية إذا ناقصة
            if not vals.get('location_id'):
                src = self._find_internal_location(company_id)
                if src:
                    vals['location_id'] = src
            if not vals.get('location_dest_id'):
                dst = self._find_prod_location(company_id)
                if dst:
                    vals['location_dest_id'] = dst

            # اسم افتراضي آمن
            vals.setdefault('name', 'Component Move')

            res_vals.append(vals)

        return super().create(res_vals)


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # --- Helpers ---
    def _components_recordset_for_fill(self):
        """Prefer components with is_valide=True; otherwise fallback to ALL."""
        comps = self.env["mrp.components"].search([("is_valide", "=", True)])
        return comps if comps else self.env["mrp.components"].search([])

    def _prepare_bom_lines_from_components(self, comps=None):
        """
        Build bom_line_ids values from mrp.components.move_raw_ids.
        Group by (product_id, uom_id) and sum quantities.
        """
        self.ensure_one()
        comps = comps if comps is not None else self._components_recordset_for_fill()
        moves = comps.mapped("move_raw_ids")
        if not moves:
            return []

        agg = {}  # key: (product_id, uom_id) -> qty
        for mv in moves:
            if not mv.product_id:
                continue
            uom = mv.product_uom or mv.product_id.uom_id
            key = (mv.product_id.id, uom.id)
            qty = mv.product_uom_qty or 0.0
            agg[key] = agg.get(key, 0.0) + qty

        line_vals = []
        BomLine = self.env['mrp.bom.line']
        for (product_id, uom_id), qty in agg.items():
            vals = {
                "product_id": product_id,
                "product_qty": qty,
                "product_uom_id": uom_id,
            }
            # Manual Consumption إذا الحقل موجود على سطر BoM
            if 'manual_consumption' in BomLine._fields:
                vals["manual_consumption"] = False
            line_vals.append((0, 0, vals))
        return line_vals

    # --- Onchange: when product changes, fill all lines ---
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_fill_components(self):
        """
        When user picks the BoM Product, auto-fill bom_line_ids
        from mrp.components (valid ones first; else all).
        Always replaces current lines.
        """
        for bom in self:
            line_vals = bom._prepare_bom_lines_from_components()
            # امسح الموجود ثم عبّي من جديد
            bom.bom_line_ids = [(5, 0, 0)] + line_vals if line_vals else [(5, 0, 0)]