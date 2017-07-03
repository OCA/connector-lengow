# -*- coding: utf-8 -*-
# Copyright 2017 Acsone SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import AbstractComponent


class BaseLengowConnectorComponent(AbstractComponent):

    _name = 'base.lengow.connector'
    _inherit = 'base.connector'
    _collection = 'lengow.backend'
