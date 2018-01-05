# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta, date
import mock

from odoo import fields
from odoo.tools.safe_eval import safe_eval
from odoo.osv.expression import TRUE_LEAF
from odoo.exceptions import ValidationError
from . import common


class TestImportSaleOrders20(common.SetUpLengowBase20):
    ''' Test form sale orders with API 2.0'''

    def setUp(self):
        super(TestImportSaleOrders20, self).setUp()

    def test_import_partner(self):
        with self.backend.work_on('lengow.sale.order') as work:
            sale_importer = work.component(usage='record.importer')

            order_message = self.json_data['orders']['json']
            order_data = order_message['orders'][0]
            sale_importer.run('999-2121515-6705141', order_data)
        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121515-6705141')])
        self.assertEqual(order.partner_id.name, "Lengow A")
        self.assertEqual(order.partner_id.email,
                         "LengowA@marketplace.amazon.de")
        self.assertEqual(order.partner_id.city, "Nantes")
        self.assertEqual(order.partner_id.zip, "44000")
        self.assertEqual(order.partner_id.phone, "099999689492")
        self.assertEqual(order.partner_id.mobile, "099999689493")
        self.assertEqual(order.partner_shipping_id.name, "Lengow B")
        self.assertEqual(order.partner_invoice_id.name, "Lengow A")

        # import order with a company name in billing and delivery addresses
        with self.backend.work_on('lengow.sale.order') as work:
            sale_importer = work.component(usage='record.importer')

            order_message = self.json_data['orders']['json']
            order_data = order_message['orders'][1]
            sale_importer.run('999-2121615-6705263', order_data)
        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121615-6705263')])
        self.assertEqual(order.partner_id.name, "Company X, Mister Lengow A")
        self.assertEqual(order.partner_shipping_id.name,
                         "Company Y, Mister Lengow B")
        self.assertEqual(order.partner_invoice_id.name,
                         "Company X, Mister Lengow A")

    def test_import_sale_order_date_filter(self):
        with mock.patch(self.get_method) as mock_get:
            # mock get request for orders data
            mock_get = self._configure_mock_request('orders', mock_get)
            with self.backend.work_on('lengow.sale.order') as work:
                importer = work.component(usage='batch.importer')
                importer.run()
                date_from = fields.Date.to_string(date.today() - timedelta(
                    days=1))
                date_to = fields.Date.today()
                expected_url = 'http://anyurl/V2/%s/%s/'\
                    'a4a506440102b8d06a0f63fdd1eadd5f/0/orders/'\
                    'commands/processing/json/' % (date_from, date_to)
                mock_get.assert_called_with(expected_url, data={}, params={},
                                            headers={})

    def test_import_sale_order_date_backend(self):
        date_from = fields.Date.to_string(date.today() - timedelta(days=5))
        self.backend.import_orders_from_date = date_from
        self.backend.import_sale_orders()
        job = self.env['queue.job'].search([TRUE_LEAF])
        self.assertEqual(len(job), 1)
        args_start = job.func_string.index('{')
        args = safe_eval(job.func_string[args_start:-1])
        self.assertEqual(args['from_date'], date_from)
        self.assertEqual(args['to_date'], fields.Date.today())
        self.assertEqual(self.backend.import_orders_from_date,
                         fields.Date.to_string(date.today() - timedelta(
                             days=1)))

    def test_import_sale_order_filters(self):
        date_from = fields.Date.to_string(date.today() - timedelta(days=5))
        self.backend.import_orders_from_date = date_from
        self.backend.import_sale_orders(filters={'id_flux': 12345,
                                                 'state': 'shipped'})
        job = self.env['queue.job'].search([TRUE_LEAF])
        self.assertEqual(len(job), 1)
        args_start = job.func_string.index('{')
        args = safe_eval(job.func_string[args_start:-1])
        self.assertEqual(args['from_date'], date_from)
        self.assertEqual(args['to_date'], fields.Date.today())
        self.assertEqual(args['id_flux'], 12345)
        self.assertEqual(args['state'], 'shipped')
        self.assertEqual(self.backend.import_orders_from_date,
                         fields.Date.to_string(date.today() - timedelta(
                             days=1)))

    def test_import_sale_orders(self):
        with mock.patch(self.get_method) as mock_get:
            # mock get request for orders data
            mock_get = self._configure_mock_request('orders', mock_get)
            with self.backend.work_on('lengow.sale.order') as work:
                importer = work.component(usage='batch.importer')
                importer.run(filters={'from_date': '2016-10-01',
                                      'to_date': '2016-10-01'})
                mock_get.assert_called_with(
                    'http://anyurl/V2/2016-10-01/2016-10-01/'
                    'a4a506440102b8d06a0f63fdd1eadd5f/0/orders/'
                    'commands/processing/json/',
                    data={},
                    params={},
                    headers={})
                jobs = self.env['queue.job'].search([TRUE_LEAF])

                self.assertEqual(len(jobs), 2)
                expected_names = [
                    'Import lengow.sale.order 999-2121515-6705141'
                    ' from Lengow Backend Test Lengow',
                    'Import lengow.sale.order 999-2121615-6705263'
                    ' from Lengow Backend Test Lengow'
                ]
                for qjob in jobs:
                    self.assertIn(qjob.name, expected_names)

    def test_import_sale_order(self):
        with self.backend.work_on('lengow.sale.order') as work:
            sale_importer = work.component(usage='record.importer')

            order_message = self.json_data['orders']['json']
            order_data = order_message['orders'][0]
            sale_importer.run('999-2121515-6705141', order_data)

        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121515-6705141')])
        self.assertEqual(len(order), 1)

        self.assertTrue(order.is_from_lengow)
        self.assertEqual(order.name, 'AMAZON-999-2121515-6705141')

        # order should be in EUR
        self.assertEqual(order.currency_id.id,
                         self.env.ref('base.main_company').currency_id.id)

        # check partner linked
        self.assertEqual(order.partner_id.name, 'Lengow A')
        self.assertEqual(order.partner_id.id, order.partner_invoice_id.id)

        # order should not be assigned to a vendor
        self.assertFalse(order.user_id)

        # order should be linked to the right marketplace
        self.assertEqual(order.lengow_bind_ids[0].marketplace_id.id,
                         self.marketplace.id)

        # order should use the right fiscal position
        self.assertEqual(order.fiscal_position_id.id,
                         self.fiscal_position.id)

        # id flux should be stored on order
        self.assertEqual(order.lengow_bind_ids[0].id_flux, '99128')

        # order should be assigned to analytic for Amazon
        self.assertEqual(order.project_id.id, self.amazon_analytic.id)

        # payment method should be the amazon one
        self.assertEqual(order.payment_mode_id.id,
                         self.marketplace.payment_mode_id.id)

        # order should have 2 order lines and one shipping cost line
        self.assertEqual(len(order.order_line), 3)

        # check amount total
        self.assertEqual(order.lengow_total_amount, 305.65)
        self.assertAlmostEqual(order.lengow_total_amount,
                               order.amount_total)

        # check order lines
        order_line = order.order_line[0]
        self.assertEqual(order_line.product_id.id, self.product1.id)
        self.assertEqual(order_line.name, "Pantalon G-star rovic"
                                          " slim, micro stretch "
                                          "twill GS Dk Fig Taille W29/L32")
        self.assertEqual(order_line.product_uom_qty, 2)
        self.assertEqual(order_line.price_unit, 99.90)
        self.assertEqual(order_line.price_subtotal, 199.8)

        order_line = order.order_line[1]
        self.assertEqual(order_line.product_id.id, self.product2.id)
        self.assertEqual(order_line.name, "Pantalon G-star rovic"
                                          " slim, micro stretch "
                                          "twill GS Dk Fig Taille W30/L33")
        self.assertEqual(order_line.product_uom_qty, 1)
        self.assertEqual(order_line.price_unit, 99.95)
        self.assertEqual(order_line.price_subtotal, 99.95)

        order_line = order.order_line[2]
        self.assertEqual(order_line.product_id.id,
                         self.env.ref('connector_ecommerce.'
                                      'product_product_shipping').id)
        self.assertEqual(order_line.name, "Shipping Costs")
        self.assertEqual(order_line.product_uom_qty, 1)
        self.assertEqual(order_line.price_unit, 5.9)
        self.assertEqual(order_line.price_subtotal, 5.9)

        # check payment linked to sale
        self.assertTrue(order.workflow_process_id)
        self.env['automatic.workflow.job'].run()
        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.invoice_ids)
        invoice = order.invoice_ids
        self.assertEqual(invoice.state, 'paid')
        self.assertEqual(invoice.reference, order.name)

        # route for auto-delivery should be assigned on each line
        self.assertTrue(order.order_line[0].route_id.id, self.route.id)
        self.assertTrue(order.order_line[1].route_id.id, self.route.id)
        self.assertFalse(order.order_line[2].route_id)

    def test_sale_multiple_import(self):
        # test update is ignored
        with self.backend.work_on('lengow.sale.order') as work:
            sale_importer = work.component(usage='record.importer')
            order_message = self.json_data['orders']['json']
            order_data = order_message['orders'][0]
            order_data2 = order_message['orders'][0].copy()
            sale_importer.run('999-2121515-6705141', order_data)

        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121515-6705141')])
        self.assertEqual(len(order), 1)

        self.assertTrue(order.workflow_process_id)
        self.env['automatic.workflow.job'].run()
        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.invoice_ids)
        invoice = order.invoice_ids
        self.assertEqual(invoice.state, 'paid')

        sale_importer.run('999-2121515-6705141', order_data2)
        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121515-6705141')])
        self.assertEqual(len(order), 1)

    def test_import_sale_order_country_fiscal(self):
        fiscal_position = self.env['account.fiscal.position'].create(
            {
                'name': 'Test Lengow'
            }
        )
        self.env['lengow.tax.mapping'].create({
            'backend_id': self.backend.id,
            'country_id': self.env.ref('base.fr').id,
            'fiscal_position_id': fiscal_position.id
        })

        with self.backend.work_on('lengow.sale.order') as work:
            sale_importer = work.component(usage='record.importer')
            order_message = self.json_data['orders']['json']
            order_data = order_message['orders'][0]
            sale_importer.run('999-2121515-6705141', order_data)

        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121515-6705141')])
        self.assertEqual(len(order), 1)

        # order should use the right fiscal position
        self.assertEqual(order.fiscal_position_id.id, fiscal_position.id)

    def test_sale_currency_mapping_fail(self):
        gbp = self.env.ref('base.GBP')
        gbp_pricelist = self.env['product.pricelist'].create({
            'name': 'GBP pricelist'})

        # Pricelist should be in the same currency
        with self.assertRaises(ValidationError):
            self.env['lengow.currency.mapping'].create({
                'backend_id': self.backend.id,
                'currency_id': gbp.id,
                'pricelist_id': gbp_pricelist.id
            })

    def test_sale_currency(self):
        gbp = self.env.ref('base.GBP')
        gbp.write({'active': True})
        gbp_pricelist = self.env['product.pricelist'].create({
            'name': 'GBP pricelist',
            'currency_id': gbp.id})

        self.env['lengow.currency.mapping'].create({
            'backend_id': self.backend.id,
            'currency_id': gbp.id,
            'pricelist_id': gbp_pricelist.id})

        order_message = self.json_data['orders']['json']
        order_data = order_message['orders'][0]
        order_data['order_currency'] = "GBP"
        with self.backend.work_on('lengow.sale.order') as work:
            sale_importer = work.component(usage='record.importer')
            sale_importer.run('999-2121515-6705141', order_data)

        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121515-6705141')])
        self.assertEqual(len(order), 1)
        self.assertEqual(order.currency_id.id, gbp.id)
        self.assertEqual(order.pricelist_id.id, gbp_pricelist.id)
