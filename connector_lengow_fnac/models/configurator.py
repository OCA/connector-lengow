# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.connector_lengow.models.configurator import\
    MarketPlaceConfigurator


class FnacMarketPlaceConfigurator(MarketPlaceConfigurator):
    marketplace = 'fnac'
    _param_tracking_code_name = 'trackingColis'
    _param_tracking_carrier_name = 'transporteurColis'
    _tracking_mandatory = True

    def get_export_picking_api(self, id_flux, order_id):
        url = 'fnac/%s/%s/Shipped.xml'
        return url % (id_flux, order_id)

    def get_export_picking_tracking_params(self):
        params = {}
        params[self._param_tracking_code_name] = None
        params[self._param_tracking_carrier_name] = None
        return params
