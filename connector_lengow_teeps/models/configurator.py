# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.connector_lengow.models.configurator import\
    MarketPlaceConfigurator


class TeepsMarketPlaceConfigurator(MarketPlaceConfigurator):
    marketplace = 'teeps'
    _param_tracking_code_name = 'tracking_number'
    _param_tracking_carrier_name = 'carrier_name'
    _restricted_carrier_code = {
        'chronopost',
        'lapostecourriersuivi',
        'chronorelais',
        'colissimo',
        'ups',
        'fedex',
        'dhl',
        'usps',
        'tnt',
        'parcelforce',
        'exapaq',
        'gls',
    }

    def get_export_picking_api(self, id_flux, order_id):
        url = 'teeps/%s/%s/ship.xml'
        return url % (id_flux, order_id)

    def get_export_picking_tracking_params(self):
        params = {}
        params[self._param_tracking_code_name] = None
        params[self._param_tracking_carrier_name] = None
        return params
