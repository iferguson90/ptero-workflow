from ..base import Base
from .. import output
from ..petri import ColorGroup
from .mixins.petri import OperationPetriMixin
from .mixins.parallel import ParallelPetriMixin
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.session import object_session
import logging
import os
import simplejson


__all__ = ['Operation', 'InputHolderOperation']


LOG = logging.getLogger(__file__)


class Operation(Base):
    __tablename__ = 'operation'
    __table_args__ = (
        UniqueConstraint('parent_id', 'name'),
    )

    id        = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('operation.id'), nullable=True)
    name      = Column(Text, nullable=False)
    type      = Column(Text, nullable=False)
    status = Column(Text)

    children = relationship('Operation',
            backref=backref('parent', uselist=False, remote_side=[id]),
            collection_class=attribute_mapped_collection('name'),
            cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_on': 'type',
    }

    @classmethod
    def from_dict(cls, type, **kwargs):
        subclass = cls.subclass_for(type)
        return subclass(**kwargs)

    @classmethod
    def subclass_for(cls, type):
        mapper = inspect(cls)
        return mapper.polymorphic_map[type].class_

    @property
    def to_dict(self):
        result = self._as_dict_data
        result['type'] = self.type
        return result
    as_dict = to_dict

    @property
    def _as_dict_data(self):
        return {}

    @property
    def unique_name(self):
        return '-'.join(['op', str(self.id), self.name.replace(' ', '_')])

    @property
    def success_place_name(self):
        return '%s-success' % self.unique_name

    def success_place_pair_name(self, op):
        return '%s-success-for-%s' % (self.unique_name, op.unique_name)

    @property
    def ready_place_name(self):
        return '%s-ready' % self.unique_name

    @property
    def response_wait_place_name(self):
        return '%s-response-wait' % self.unique_name

    @property
    def response_callback_place_name(self):
        return '%s-response-callback' % self.unique_name

    def notify_callback_url(self, event):
        return 'http://%s:%d/v1/callbacks/operations/%d/events/%s' % (
            os.environ.get('PTERO_WORKFLOW_HOST', 'localhost'),
            int(os.environ.get('PTERO_WORKFLOW_PORT', 80)),
            self.id,
            event,
        )

    def get_petri_transitions(self):
        raise RuntimeError('Operation is abstract')

    @property
    def input_ops(self):
        source_ids = set([l.source_id for l in self.input_links])
        if source_ids:
            s = object_session(self)
            return s.query(Operation).filter(Operation.id.in_(source_ids)).all()
        else:
            return []

    @property
    def output_ops(self):
        destination_ids = set([l.destination_id for l in self.output_links])
        if destination_ids:
            s = object_session(self)
            return s.query(Operation).filter(
                    Operation.id.in_(destination_ids)).all()
        else:
            return []

    def get_workflow(self):
        root = self.get_root()
        return root.workflow

    def get_root(self):
        parent = self.parent
        if parent is None:
            return self

        while parent.parent:
            parent = parent.parent

        return parent

    def get_output(self, name, color):
        return self.get_outputs(color).get(name)

    def get_outputs(self, color):
        # XXX Broken -- does not even use color.
        return {o.name: o.data for o in self.outputs}

    def set_outputs(self, outputs, color):
        s = object_session(self)
        for name, value in outputs.iteritems():
            o = output.create_output(self, name, value, color)

    def get_inputs(self, color):
        workflow = self.get_workflow()
        valid_colors = self._valid_color_list(color, workflow)

        source_operations = self._source_op_data()

        result = {}
        for property_name, source_data in source_operations.iteritems():
            output_holder = self._fetch_input(color, valid_colors, source_data)
            result[property_name] = self._convert_output(property_name,
                    output_holder, color)

        return result

    def _convert_output(self, property_name, output_holder, color):
        return output_holder.data

    def _valid_color_list(self, color, workflow):
        s = object_session(self)
        cg = s.query(ColorGroup).filter_by(workflow=workflow).filter(
            ColorGroup.begin <= color, color < ColorGroup.end
        ).one()

        result = [color]
        while cg.parent_color is not None:
            result.append(cg.parent_color)
            cg = cg.parent_color_group

        return result

    def _source_op_data(self):
        result = {}
        for link in self.input_links:
            result[link.destination_property] =\
                    link.source_operation.get_source_op_and_name(
                            link.source_property)

        return result

    def get_source_op_and_name(self, output_param_name):
        return self, output_param_name

    def get_input_op_and_name(self, input_param_name):
        for link in self.input_links:
            if link.destination_property == input_param_name:
                return link.source_operation.get_source_op_and_name(
                        link.source_property)

    def get_input_sources(self):
        result = {}
        for link in self.input_links:
            result[link.destination_property] = link.source_operation.get_source_op_and_name(
                    link.source_property)
        return result

    def _fetch_input(self, color, valid_color_list, source_data):
        (operation, property_name) = source_data

        s = object_session(self)
        result = s.query(output.Output
                ).filter_by(operation=operation, name=property_name
                ).filter(output.Output.color.in_(valid_color_list)).one()
        return result

    def get_input(self, name, color):
        return self.get_inputs(color)[name]

    def execute(self, inputs):
        pass


class InputHolderOperation(Operation):
    __tablename__ = 'operation_input_holder'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': '__input_holder',
    }

    def get_inputs(self, color):
        raise RuntimeError()

    def get_input(self, name, color):
        raise RuntimeError()

    def get_petri_transitions(self):
        return []


class InputConnectorOperation(Operation):
    __tablename__ = 'operation_input_connector'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'input connector',
    }

    def get_source_op_and_name(self, output_param_name):
        op, name = self.parent.get_input_op_and_name(output_param_name)
        return op.get_source_op_and_name(name)

    def get_output(self, name, color):
        return self.get_inputs(color).get(name)

    def get_outputs(self, color):
        return self.get_inputs(color)

    def get_inputs(self, color):
        return self.parent.get_inputs(color)

    def get_input(self, name, color):
        return self.parent.get_input(name, color)

    def get_petri_transitions(self):
        return [
            {
                'inputs': [self.parent.ready_place_name],
                'outputs': [self.success_place_name],
            },
            {
                'inputs': [self.success_place_name],
                'outputs': [self.success_place_pair_name(o) for o in self.output_ops],
            }
        ]


class OutputConnectorOperation(Operation):
    __tablename__ = 'operation_output_connector'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'output connector',
    }

    def get_outputs(self, color):
        source_data = self.get_input_sources()
        valid_color_list = self._valid_color_list(color, self.get_workflow())
        result = {}
        for property_name, source in source_data.iteritems():
            source_op, source_name = source
            result[property_name] = source_op.get_output(source_name, color)
        return result

    def get_source_op_and_name(self, output_param_name):
        op, name = self.get_input_op_and_name(output_param_name)
        return op.get_source_op_and_name(name)

    def get_petri_transitions(self):
        return []


class ModelOperation(Operation):
    __tablename__ = 'operation_model'

    id = Column(Integer, ForeignKey('operation.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'model',
    }

    @property
    def real_child_ops(self):
        data = dict(self.children)
        del data['input connector']
        del data['output connector']
        return data.values()

    def get_outputs(self, color):
        return self.children['output connector'].get_outputs(color)

    def get_source_op_and_name(self, output_param_name):
        oc = self.children['output connector']
        return oc.get_source_op_and_name(output_param_name)

    def get_petri_transitions(self):
        result = []

        if self.input_ops:
            result.append({
                'inputs': [o.success_place_pair_name(self) for o in self.input_ops],
                'outputs': [self.ready_place_name],
            })

        if self.output_ops:
            success_outputs = [self.success_place_pair_name(o) for o in self.output_ops]
            if self.parent:
                success_outputs.append(self.success_place_pair_name(self.parent))
            result.append({
                'inputs': [self.success_place_name],
                'outputs': success_outputs,
            })

        result.append({
            'inputs': [o.success_place_pair_name(self)
                for o in self.real_child_ops],
            'outputs': [self.success_place_name],
            'action': {
                'type': 'notify',
                'url': self.notify_callback_url('done'),
            },
        })

        for child in self.children.itervalues():
            result.extend(child.get_petri_transitions())

        return result


def _parallel_index(color, group):
    try:
        return int(color) - int(group['begin'])
    except:
        return None