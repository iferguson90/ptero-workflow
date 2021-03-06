from . import result
from .base import Base
from .json_type import JSON
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
import logging


__all__ = ['InputSource']


LOG = logging.getLogger(__name__)


class InputSource(Base):
    __tablename__ = 'input_source'
    __table_args__ = (
        UniqueConstraint('destination_id', 'destination_property'),
    )

    id = Column(Integer, primary_key=True)

    source_id      = Column(Integer, ForeignKey('task.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('task.id'), nullable=False)

    source_property      = Column(Text, nullable=False)
    destination_property = Column(Text, nullable=False)

    parallel_depths = Column(JSON, nullable=None)

    source_task = relationship('Task', foreign_keys=[source_id])
    destination_task = relationship('Task', backref='input_sources',
            foreign_keys=[destination_id])

    def parallel_indexes(self, colors, begins):
        indexes = []
        for depth in self.parallel_depths:
            if depth >= len(colors):
                return indexes
            indexes.append(colors[depth] - begins[depth])
        return indexes

    def get_data(self, colors, begins):
        LOG.debug('get_data %s[%s] -> %s[%s] with parallel_depths=%s, '
                'colors=%s, begins=%s',
                self.destination_task.name, self.destination_property,
                self.source_task.name, self.source_property,
                self.parallel_depths, colors, begins)
        s = object_session(self)

        r = s.query(result.Result
                ).filter_by(task=self.source_task, name=self.source_property
                ).filter(result.Result.color.in_(colors)).one()

        indexes = self.parallel_indexes(colors, begins)
        LOG.debug('%s[%s]  parallel_depths=%s, colors=%s, begins=%s '
                '-> indexes=%s',
                self.source_task.name, self.source_property,
                self.parallel_depths, colors, begins, indexes)
        return r.get_data(indexes)

    def get_size(self, colors, begins):
        indexes = self.parallel_indexes(colors, begins)
        s = object_session(self)
        r = s.query(result.Result
                ).filter_by(task=self.source_task, name=self.source_property
                ).filter(result.Result.color.in_(colors)).one()
        return r.get_size(indexes)
