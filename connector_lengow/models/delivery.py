# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    lengow_code = fields.Char()
    lengow_value = fields.Char('Value to Export to Lengow',
                               compute='_compute_lengow_value')

    def _compute_lengow_value(self):
        for carrier in self:
            carrier.lengow_value = carrier.lengow_code or carrier.name
