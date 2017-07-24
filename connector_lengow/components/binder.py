# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component
from odoo import tools


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

    def to_internal(self, external_id, unwrap=False):
        """ Give the Odoo recordset for an external ID

        :param external_id: external ID for which we want
                            the Odoo ID
        :param unwrap: if True, returns the normal record
                       else return the binding record
        :return: a recordset, depending on the value of unwrap,
                 or an empty recordset if the external_id is not mapped
        :rtype: recordset
        """
        bindings = self.model.with_context(active_test=False).search(
            [(self._external_field, '=', tools.ustr(external_id)),
             (self._backend_field, '=', self.backend_record.id)]
        )
        if not bindings:
            if unwrap:
                return self.model.browse()[self._odoo_field]
            return self.model.browse()

        if len(bindings) > 1:
            # can be the case for lengow.product.product because the same
            # product can be binded to several catalogue
            assert len(set([binding[self._odoo_field]
                            for binding in bindings])) == 1, (
                "Multiple value for same id %s" % external_id)
            bindings = bindings[0]

        if unwrap:
            bindings = bindings[self._odoo_field]
        return bindings
