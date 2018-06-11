# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.connector_lengow.models.configurator import\
    MarketPlaceConfigurator


class NatdecPlaceConfigurator(MarketPlaceConfigurator):
    marketplace = 'natdec'
    _param_tracking_code_name = 'tracking_number'
    _param_tracking_url_name = 'tracking_url'
    _param_tracking_carrier_name = 'carrier_code'
    _param_tracking_unknown_carrier_name = 'carrier_name'
    _tracking_mandatory = True
    _restricted_carrier_code = {
        'CO',
        'CHR',
        'COS',
        'Group',
        'UPS',
        'SEUR',
        'TNT',
    }

    def get_export_picking_api(self, id_flux, order_id):
        url = 'natdec/%s/%s/shipped.xml'
        return url % (id_flux, order_id)

    def get_export_picking_tracking_params(self):
        params = {}
        params[self._param_tracking_code_name] = None
        params[self._param_tracking_carrier_name] = None
        return params
