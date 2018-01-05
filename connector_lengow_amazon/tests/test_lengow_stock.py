# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import mock

from odoo.osv.expression import TRUE_LEAF

from odoo.addons.connector_lengow.tests import common


class TestStock20(common.SetUpLengowBase20):

    def setUp(self):
        super(TestStock20, self).setUp()
        self.json_data.update({
            'amazon_update': {
                'status_code': 200,
                'json': {}}})
        with self.backend.work_on('lengow.sale.order') as work:
            sale_importer = work.component(usage='record.importer')

            order_message = self.json_data['orders']['json']
            order_data = order_message['orders'][0]
            sale_importer.run('999-2121515-6705141', order_data)
        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121515-6705141')])
        self.env['automatic.workflow.job'].run()
        self.assertEqual(order.state, 'sale')
        self.picking = order.picking_ids[0]

    def test_export_picking_done(self):
        with mock.patch(self.post_method) as mock_post:
            mock_post = self._configure_mock_request('amazon_update',
                                                     mock_post)
            self.picking.force_assign()
            self.picking.do_transfer()

            self.assertEqual(len(self.picking.lengow_bind_ids), 1)

            jobs = self.env['queue.job'].search([TRUE_LEAF])

            self.assertEqual(len(jobs), 1)
            self.assertEqual(
                jobs.name,
                'Export Lengow Picking %s'
                ' (Order: AMAZON-999-2121515-6705141)' % self.picking.name)

            with self.backend.work_on('lengow.stock.picking') as work:
                exporter = work.component(usage='record.exporter')
                exporter.run(self.picking.lengow_bind_ids.id)

            mock_post.assert_called_with(
                'http://anywsdlurl/amazon/99128/999-2121515-6705141'
                '/acceptOrder.xml', params={}, data={}, headers={})

    def test_export_picking_done_tracking(self):
        with mock.patch(self.post_method) as mock_post:
            mock_post = self._configure_mock_request('amazon_update',
                                                     mock_post)
            self.picking.write({'carrier_tracking_ref': 'tracking code test'})
            self.picking.force_assign()
            self.picking.do_transfer()

            self.assertEqual(len(self.picking.lengow_bind_ids), 1)

            jobs = self.env['queue.job'].search([TRUE_LEAF])

            self.assertEqual(len(jobs), 1)
            self.assertEqual(
                jobs.name,
                'Export Lengow Picking %s'
                ' (Order: AMAZON-999-2121515-6705141)' % self.picking.name)

            with self.backend.work_on('lengow.stock.picking') as work:
                exporter = work.component(usage='record.exporter')
                exporter.run(self.picking.lengow_bind_ids.id)

            mock_post.assert_called_with(
                'http://anywsdlurl/amazon/99128/999-2121515-6705141'
                '/acceptOrder.xml',
                params={'colis_idTracking': 'tracking code test',
                        'transporteur': 'Normal Delivery Charges'},
                data={}, headers={})
