# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class LengowPDiscountWizard(models.TransientModel):
    _name = 'lengow.discount.wizard'

    lengow_product_ids = fields.Many2many(
        string='Products',
        comodel_name='lengow.product.product',
        ondelete='cascade')
    discount_type = fields.Selection([('price', '€'),
                                      ('percent', '%')],
                                     string='Mode',
                                     default="percent",
                                     required=True)
    discount = fields.Float()
    discount_start = fields.Date('Start Date')
    discount_end = fields.Date('End Date')

    @api.model
    def default_get(self, fields_list):
        res = super(LengowPDiscountWizard,
                    self).default_get(fields_list)
        domain = self.env.context.get('active_domain', False)
        lengow_product_ids = self.env.context.get('active_ids', False)
        if domain:
            lengow_product_ids = self.env['lengow.product.product'].search(
                domain)
            lengow_product_ids = lengow_product_ids.ids
        if lengow_product_ids:
            res['lengow_product_ids'] = lengow_product_ids
        return res

    @api.constrains('discount')
    def _check_discount(self):
        if self.discount_type == "percent" and not self.env.context.get(
                'reset', False):
            if self.discount <= 0.0 or self.discount > 100:
                raise ValidationError(_('Discount rate should be between 0 and'
                                        ' 100 %'))

    @api.constrains('discount_start', 'discount_end')
    def _check_dates(self):
        if self.discount_end < self.discount_start\
                and not self.env.context.get('reset', False):
            raise ValidationError(_('Start Date must be lower than End Date'))

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        if self.env.context.get('reset', False):
            self.lengow_product_ids.write({'sale_price': False,
                                           'sale_from_date': False,
                                           'sale_end_date': False})
            return
        if self.discount_type == 'price':
            self.lengow_product_ids.write({'sale_price': self.discount,
                                           'sale_from_date':
                                               self.discount_start,
                                           'sale_end_date': self.discount_end})
        else:
            for product in self.lengow_product_ids:
                discount_price = product.lengow_price - (
                    (product.lengow_price * self.discount) / 100.0)
                product.write({'sale_price': discount_price,
                               'sale_from_date':
                                   self.discount_start,
                               'sale_end_date': self.discount_end})
