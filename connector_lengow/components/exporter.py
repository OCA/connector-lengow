# -*- coding: utf-8 -*-
# Copyright 2017 Acsone SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class LengowExporter(AbstractComponent):
    """ Base exporter for Lengow """
    _name = 'lengow.exporter'
    _inherit = ['base.exporter', 'base.lengow.connector']
    _usage = 'record.exporter'

    def __init__(self, work_context):
        super(LengowExporter, self).__init__(work_context)
        self._lengow_record = None

    def export(self, map_record):
        return map_record.values()

    def _map_data(self):
        return self.mapper.map_record(self._lengow_record)
