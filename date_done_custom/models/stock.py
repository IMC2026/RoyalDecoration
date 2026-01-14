from odoo import models, fields, api

class StockPickingValidateWizard(models.TransientModel):
    _name = 'stock.picking.validate.wizard'
    _description = 'Validate Stock Picking with Custom Date'

    change_date = fields.Boolean(string="Change Effective Date?")
    date_done = fields.Datetime(string="Effective Date", default=fields.Datetime.now)

    def action_confirm_validate(self):
        active_id = self.env.context.get('active_id')
        picking = self.env['stock.picking'].browse(active_id)

        if self.change_date:
            picking.date_done = self.date_done

        # Call original button_validate logic
        return picking.with_context(skip_wizard=True).button_validate()

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        # Call the original method logic
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)

        # Update the date field in stock.move.line to match the picking's date_done
        for move in self:
            if move.picking_id and move.picking_id.date_done:
                move.move_line_ids.write({'date': move.picking_id.date_done})

        return res

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validates(self):
        if self.env.context.get('skip_wizard'):
            return super(StockPicking, self).button_validate()

        return {
            'name': 'Validate Picking',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.validate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    # def button_validate(self):
    #     if self.env.context.get('skip_wizard'):
    #         return super(StockPicking, self).button_validate()
    #
    #     return {
    #         'name': 'Validate Picking',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'stock.picking.validate.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {'active_id': self.id},
    #     }

    def _action_done(self):
        """Call _action_done on the stock.move of the stock.picking in self.
        This method makes sure every stock.move.line is linked to a stock.move by either
        linking them to an existing one or a newly created one.

        If the context key cancel_backorder is present, backorders won't be created.

        :return: True
        :rtype: bool
        """
        self._check_company()

        todo_moves = self.move_ids.filtered(
            lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        for picking in self:
            if picking.owner_id:
                picking.move_ids.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
            picking.move_line_ids.write({'date': picking.date_done or fields.Datetime.now()})

        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        if not self.date_done:
           self.write({'date_done': fields.Datetime.now(), 'priority': '0'})

        # if incoming/internal moves make other confirmed/partially_available moves available, assign them
        done_incoming_moves = self.filtered(
            lambda p: p.picking_type_id.code in ('incoming', 'internal')).move_ids.filtered(lambda m: m.state == 'done')
        done_incoming_moves._trigger_assign()

        self._send_confirmation_email()
        return True




class StockScrapValidateWizard(models.TransientModel):
    _name = 'stock.scrap.validate.wizard'
    _description = 'Validate Scrap Order with Custom Date'

    change_date = fields.Boolean(string="Change Effective Date?")
    date_done = fields.Datetime(string="Effective Date", default=fields.Datetime.now)

    def action_confirm_scrap(self):
        """ Confirm the scrap order and optionally change the effective date """
        active_id = self.env.context.get('active_id')
        scrap = self.env['stock.scrap'].browse(active_id)

        if self.change_date:
            scrap.date_done = self.date_done

            # Ensure move_ids exist before writing to move lines
            if scrap.move_ids:
                scrap.move_ids.mapped('move_line_ids').write({'date': self.date_done})

        return scrap.with_context(skip_wizard=True).do_scrap()


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def do_scrap(self):
        """ Override do_scrap to launch a validation wizard before executing the scrap """
        if self.env.context.get('skip_wizard'):
            return super(StockScrap, self).do_scrap()

        return {
            'name': 'Validate Scrap',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.scrap.validate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }


        # def do_scrap_wiard(self):
        #     if self.env.context.get('skip_wizard'):
        #         return super(StockScrap, self).do_scrap()
        #
        #     return {
        #         'name': 'Validate Scrap',
        #         'type': 'ir.actions.act_window',
        #         'res_model': 'stock.scrap.validate.wizard',
        #         'view_mode': 'form',
        #         'target': 'new',
        #         'context': {'active_id': self.id},
        #     }



# class StockQuant(models.Model):
#     _inherit = 'stock.quant'
#
#     def action_apply_inventory(self):
#         if self.env.context.get('skip_wizard'):
#             return super(StockQuant, self).action_apply_inventory()
#
#         return {
#             'name': 'Adjust Inventory',
#             'type': 'ir.actions.act_window',
#             'res_model': 'stock.quant.adjust.wizard',
#             'view_mode': 'form',
#             'target': 'new',
#             'context': {'active_ids': self.ids},
#         }
#
# class StockQuantAdjustWizard(models.TransientModel):
#     _name = 'stock.quant.adjust.wizard'
#     _description = 'Inventory Adjustment with Custom Date'
#
#     change_date = fields.Boolean(string="Change Effective Date?")
#     adjustment_date = fields.Datetime(string="Effective Date", default=fields.Datetime.now)
#
#     def action_confirm_adjustment(self):
#         active_ids = self.env.context.get('active_ids', [])
#         quants = self.env['stock.quant'].browse(active_ids)
#
#         if self.change_date:
#             for quant in quants:
#                 quant.write({'inventory_date': self.adjustment_date})
#                 quant.with_context(skip_wizard=True).action_apply_inventory()
#         # Custom logic for adjustments (if needed)
#         return True
