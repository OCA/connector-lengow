# -*- coding: utf-8 -*-
# Copyright 2017 Acsone SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import hashlib
import logging

from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import NothingToDoJob

_logger = logging.getLogger(__name__)


class LengowImporter(AbstractComponent):
    """ Base importer for Lengow """
    _name = 'lengow.importer'
    _inherit = ['base.importer', 'base.lengow.connector']
    _usage = 'record.importer'

    def __init__(self, work_context):
        super(LengowImporter, self).__init__(work_context)
        self.external_id = None
        self.lengow_record = None

    def _import_dependency(self, lengow_id, binding_model, lengow_data,
                           importer=None, always=False):

        """ Import a dependency. """
        binder = self.binder_for(binding_model)
        if always or not binder.to_internal(lengow_id):
            if importer is None:
                importer = self.component(usage='record.importer',
                                          model_name=binding_model)
            try:
                importer.run(lengow_id, lengow_data)
            except NothingToDoJob:
                _logger.info(
                    'Dependency import of %s(%s) has been ignored.',
                    binding_model._name, lengow_id
                )

    def _import_dependencies(self):
        """ Import the dependencies for the record

        Import of dependencies can be done manually or by calling
        :meth:`_import_dependency` for each dependency.
        """
        return

    def _get_binding(self):
        return self.binder.to_internal(self.lengow_id)

    def _map_data(self):
        return self.mapper.map_record(self.lengow_record)

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        """ Create the Odoo record """
        model = self.model.with_context(connector_no_export=True)
        binding = model.create(data)
        _logger.debug('%d created from Lengow %s', binding, self.lengow_id)
        return binding

    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        """ Update an OpenERP record """
        # special check on data before import
        binding.with_context(connector_no_export=True).write(data)
        _logger.debug('%d updated from Lengow %s', binding, self.lengow_id)
        return

    def _generate_hash_key(self, record_data):
        '''
            This method is used to generate a key from record not identified
            on Lengow.
            For exemple, customers doesn't have any id on Lengow.
            The connector will generate one based on select data such as name,
            email and city.
        '''
        discriminant_values = dict((key, record_data[key])
                                   for key in self._discriminant_fields)
        hashtring = ''.join(discriminant_values.values())
        if not hashtring:
            return False
        hash_object = hashlib.sha1(hashtring.encode('utf8'))
        return hash_object.hexdigest()

    def _before_import(self):
        """ Hook called before the import, when we have the Lengow
        data"""

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    def run(self, lengow_id, lengow_data):
        """ Run the synchronization

        :param lengow_id: identifier of the record on Lengow
        :param lengow_data: data of the record on Lengow
        """
        if not lengow_id:
            lengow_id = self._generate_hash_key(lengow_data)

        self.lengow_id = lengow_id
        self.lengow_record = lengow_data

        binding = self._get_binding()

        self._before_import()
        self._import_dependencies()

        map_record = self._map_data()

        if binding:
            record = self._update_data(map_record)
            self._update(binding, record)
        else:
            record = self._create_data(map_record)
            binding = self._create(record)

        self.binder.bind(self.lengow_id, binding)
        self._after_import(binding)


class BatchImporter(AbstractComponent):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    _name = 'lengow.batch.importer'
    _inherit = ['base.importer', 'base.lengow.connector']
    _usage = 'batch.importer'

    def run(self, filters=None):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters)
        for record_id, record_data in record_ids.iteritems():
            self._import_record(record_id, record_data)

    def _import_record(self, external_id):
        """ Import a record directly or delay the import of the record.
        Method to implement in sub-classes.
        """
        raise NotImplementedError


class DirectBatchImporter(AbstractComponent):
    """ Import the records directly, without delaying the jobs. """

    _name = 'lengow.direct.batch.importer'
    _inherit = 'lengow.batch.importer'

    def _import_record(self, external_id, record_data):
        """ Import the record directly """
        self.model.import_record(self.backend_record, external_id, record_data)


class DelayedBatchImporter(AbstractComponent):
    """ Delay import of the records """

    _name = 'lengow.delayed.batch.importer'
    _inherit = 'lengow.batch.importer'

    def _import_record(self, external_id, record_data, job_options=None,
                       **kwargs):
        """ Delay the import of the records"""
        description = 'Import %s %s from Lengow Backend %s' % \
                      (self.model._name,
                       external_id,
                       self.backend_record.name)
        job_options = job_options or {}
        job_options.update({'description': description})
        delayable = self.model.with_delay(**job_options or {})
        delayable.import_record(self.backend_record, external_id,
                                record_data, **kwargs)
