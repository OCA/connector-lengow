# -*- coding: utf-8 -*-
# Copyright 2017 Acsone SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import AbstractComponent


class LengowImportMapper(AbstractComponent):
    _name = 'lengow.import.mapper'
    _inherit = ['base.lengow.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class LengowExportMapper(AbstractComponent):
    _name = 'lengow.export.mapper'
    _inherit = ['base.lengow.connector', 'base.export.mapper']
    _usage = 'export.mapper'
