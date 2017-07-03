# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class LengowProductUnbindingWizard(models.TransientModel):
    _name = 'lengow.product.unbinding.wizard'
    _description = "Wizard to unbind products from a Lengow backend"

    lengow_product_ids = fields.Many2many(
        string='Products',
        comodel_name='lengow.product.product',
        relation='leng_prod_unbind_wizard_rel',
        ondelete='cascade')

    @api.model
    def default_get(self, fields_list):
        res = super(LengowProductUnbindingWizard,
                    self).default_get(fields_list)
        lengow_product_ids = self.env.context.get('active_ids', False)
        if lengow_product_ids:
            res['lengow_product_ids'] = lengow_product_ids
        return res

    @api.multi
    def unbind_products(self):
        for wizard in self:
            wizard.lengow_product_ids.write({'active': False})
