# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class LengowModelBinder(Component):
    _name = 'lengow.binder'
    _inherit = ['base.binder', 'base.lengow.connector']
    _apply_on = [
        'lengow.market.place',
        'lengow.sale.order',
        'lengow.sale.order.line',
        'lengow.res.partner',
        'lengow.product.product'
    ]

    _external_field = 'lengow_id'
