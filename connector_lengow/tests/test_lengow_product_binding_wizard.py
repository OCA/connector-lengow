# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from . import common


class TestLengowProductBinding(common.SetUpLengowBase20):

    def setUp(self):
        super(TestLengowProductBinding, self).setUp()
        self.product = self.env.ref('product.product_product_12')

    def test_product_binding(self):
        '''
            Select a product and
            - bind it to a Lengow Catalogue
            - unbind it
            - bind it again
        '''
        # --------------------------------
        # Bind the product to the Backend
        # --------------------------------
        bind_wizard = self.bind_wizard_model.create(
            {'catalogue_id': self.catalogue.id,
             'product_ids': [(6, 0, [self.product.id])]})

        bind_wizard.bind_products()

        # A binding record should exists
        bind_record = self.product_bind_model.search(
            [('odoo_id', '=', self.product.id),
             ('backend_id', '=', self.backend.id),
             ('catalogue_id', '=', self.catalogue.id),
             ('lengow_id', '=', self.product.default_code)])

        self.assertEqual(len(bind_record), 1)

        # --------------------------------
        # UnBind the product
        # --------------------------------
        unbind_wizard = self.unbind_wizard_model.create(
            {'lengow_product_ids': [(6, 0, [bind_record.id])]})
        unbind_wizard.unbind_products()

        # The binding record should be unreachable
        bind_record = self.product_bind_model.search(
            [('odoo_id', '=', self.product.id),
             ('backend_id', '=', self.backend.id),
             ('catalogue_id', '=', self.catalogue.id),
             ('lengow_id', '=', self.product.default_code)])

        self.assertEqual(len(bind_record), 0)

        # The binding record should still exist but inactive
        bind_record = self.product_bind_model.with_context(
            active_test=False).search(
                [('odoo_id', '=', self.product.id),
                 ('backend_id', '=', self.backend.id),
                 ('catalogue_id', '=', self.catalogue.id),
                 ('lengow_id', '=', self.product.default_code)])

        self.assertEqual(len(bind_record), 1)

        # --------------------------------
        # Bind the product again
        # --------------------------------
        bind_wizard.bind_products()

        # The binding record should be re-activated
        bind_record = self.product_bind_model.search(
            [('odoo_id', '=', self.product.id),
             ('backend_id', '=', self.backend.id),
             ('catalogue_id', '=', self.catalogue.id),
             ('lengow_id', '=', self.product.default_code)])

        self.assertEqual(len(bind_record), 1)

    def test_product_inactivation(self):
        '''
            Select a product and bind it to a Lengow Catalogue
            Inactivation of the product must unbind the product
        '''
        # --------------------------------
        # Bind the product to the Backend
        # --------------------------------
        bind_wizard = self.bind_wizard_model.create(
            {'catalogue_id': self.catalogue.id,
             'product_ids': [(6, 0, [self.product.id])]})

        bind_wizard.bind_products()

        # A binding record should exists
        bind_record = self.product_bind_model.search(
            [('odoo_id', '=', self.product.id),
             ('backend_id', '=', self.backend.id),
             ('catalogue_id', '=', self.catalogue.id),
             ('lengow_id', '=', self.product.default_code)])

        self.assertEqual(len(bind_record), 1)

        # --------------------------------
        # Inactivate the product
        # --------------------------------
        self.product.write({'active': False})

        # The binding record should be unreachable
        bind_record = self.product_bind_model.search(
            [('odoo_id', '=', self.product.id),
             ('backend_id', '=', self.backend.id),
             ('catalogue_id', '=', self.catalogue.id),
             ('lengow_id', '=', self.product.default_code)])

        self.assertEqual(len(bind_record), 0)

        # --------------------------------
        # Activate the product
        # --------------------------------
        self.product.write({'active': True})

        # The binding record should be still unreachable
        bind_record = self.product_bind_model.search(
            [('odoo_id', '=', self.product.id),
             ('backend_id', '=', self.backend.id),
             ('catalogue_id', '=', self.catalogue.id),
             ('lengow_id', '=', self.product.default_code)])

        self.assertEqual(len(bind_record), 0)
