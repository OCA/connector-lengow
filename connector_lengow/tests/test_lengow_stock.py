# -*- coding: utf-8 -*-
# Copyright 2016 Cédric Pigeon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.osv.expression import TRUE_LEAF

from . import common


class TestStock20(common.SetUpLengowBase20):

    def setUp(self):
        super(TestStock20, self).setUp()

    def test_export_picking_done(self):
        order_message = self.json_data['orders']['json']
        order_data = order_message['orders'][0]
        with self.backend.work_on('lengow.sale.order') as work:
            sale_importer = work.component(usage='record.importer')
            sale_importer.run('999-2121515-6705141', order_data)
        order = self.env['sale.order'].search([('client_order_ref',
                                                '=',
                                                '999-2121515-6705141')])
        self.env['automatic.workflow.job'].run()
        self.assertEqual(order.state, 'sale')
        picking = order.picking_ids[0]
        picking.force_assign()
        picking.do_transfer()

        self.assertEqual(len(picking.lengow_bind_ids), 1)

        jobs = self.env['queue.job'].search([TRUE_LEAF])

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs.name, 'Export Lengow Picking %s'
                         ' (Order: AMAZON-999-2121515-6705141)' % picking.name)

        with self.assertRaises(AssertionError):
            with self.backend.work_on('lengow.stock.picking') as work:
                exporter = work.component(usage='record.exporter')
                exporter.run(self.picking.lengow_bind_ids.id)
