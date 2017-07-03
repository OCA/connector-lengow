# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.connector.connector import get_odoo_module,\
    is_module_installed
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class MetaMarketPlaceConfigurator(type):
    """ Metaclass for MarketPlaceConfigurator classes. """
    by_marketplace = {}

    def __init__(cls, name, bases, attrs):
        super(MetaMarketPlaceConfigurator, cls).__init__(name, bases, attrs)
        if cls.marketplace and cls.marketplace not in\
           MetaMarketPlaceConfigurator.by_marketplace:
            MetaMarketPlaceConfigurator.by_marketplace[cls.marketplace] = cls


class MarketPlaceConfigurator(object):
    """
        For Lengow API 2.0, each market place as its own way to update
        orders. This class should be inherited and specified for each
        marketplace
    """
    marketplace = None
    _param_tracking_code_name = None
    _param_tracking_url_name = None
    _param_tracking_carrier_name = None
    _param_tracking_unknown_carrier_name = None
    _tracking_mandatory = False
    _restricted_carrier_code = {}

    __metaclass__ = MetaMarketPlaceConfigurator

    def get_configurator(self, env, marketplace):
        configurator = self.__class__.by_marketplace.get(marketplace, None)
        if configurator:
            if is_module_installed(env, get_odoo_module(configurator)):
                return configurator
        return None

    def get_export_picking_api(self, id_flux, order_id):
        return None

    def get_export_picking_tracking_params(self):
        return {}

    def check_carrier_code(self, carrier_code):
        # 2 ways to manage an unknow carrier
        # - some marketplace forbids it -> Validation Error
        # - some marketplace allows it -> the tracking code parameters
        #   is replaced by a tracking url_parameter
        if self._restricted_carrier_code:
            if carrier_code not in self._restricted_carrier_code:
                if not self._param_tracking_url_name:
                    raise ValidationError(_('Carrier code %s is not allowed '
                                            'for marketplace %s' %
                                            (carrier_code, self.marketplace)))
                else:
                    return False
        return True

    def configure_tracking_params(self, tracking_number, carrier_code):
        if self._tracking_mandatory and (not tracking_number or
                                         not carrier_code):
            raise ValidationError(_('The tracking number and tracking carrier'
                                    'are mandatory for marketplace %s' %
                                    self.marketplace))
        tracking_params = self.get_export_picking_tracking_params()
        if tracking_params and tracking_number:
            tracking_param = self._param_tracking_code_name
            carrier_name_param = self._param_tracking_carrier_name
            if carrier_code:
                # For some marketplaces, the carrier is limited to a restricted
                # list (e.g.: Fnac)
                # For other marketplace, if the carrier is unknown, we should
                # send a tracking url
                known_carrier = self.check_carrier_code(carrier_code)
                if not known_carrier:
                    tracking_param = self._param_tracking_url_name
                    if self._param_tracking_unknown_carrier_name:
                        carrier_name_param = \
                            self._param_tracking_unknown_carrier_name
                        tracking_params.pop(self._param_tracking_carrier_name)
                    tracking_params.pop(self._param_tracking_code_name)
            tracking_params[tracking_param] = tracking_number
            tracking_params[carrier_name_param] = carrier_code
        else:
            tracking_params = {}
        return tracking_params
