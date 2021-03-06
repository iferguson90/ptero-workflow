from .base import Base
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
from sqlalchemy import event
from collections import defaultdict
import celery
import logging
from ptero_common.statuses import succeeded, failed, canceled, errored

LOG = logging.getLogger(__name__)

__all__ = ['Webhook']

class Webhook(Base):
    __tablename__ = 'webhook'

    id = Column(Integer, primary_key=True)

    method_id = Column(Integer, ForeignKey('method.id'), nullable=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=True)

    task = relationship('Task', backref='webhooks')
    method = relationship('Method', backref='webhooks')

    name = Column(String, nullable=False)
    url = Column(String, nullable=False)

    @property
    def http(self):
        return celery.current_app.tasks[
                'ptero_common.celery.http.HTTP']

    def send(self, **data):
        self.http.delay('PUT', self.url, webhookName=self.name, **data)

    def send_after_commit(self, **data):
        session = object_session(self)
        url = self.url
        name = self.name

        # Note: closure over self, url, name, and data
        def callback(session):
            self.http.delay('PUT', url, webhookName=name, **data)
        event.listen(session, "after_commit", callback)


NAME_SYNONYMS = {
        succeeded : [succeeded, "ended"],
        failed : [failed, "ended"],
        canceled : [canceled, "ended"],
        errored : [errored, "ended"],
}

def get_sorted_webhook_dict(entity):
    unsorted_webhook_dict = defaultdict(list)
    for webhook in entity.webhooks:
        unsorted_webhook_dict[webhook.name].append(webhook.url)

    sorted_webhook_dict = {}
    for name, unsorted_urls in unsorted_webhook_dict.iteritems():
        if len(unsorted_urls) == 1:
            entry = unsorted_urls.pop()
        else:
            entry = sorted(unsorted_urls)
        sorted_webhook_dict[name] = entry
    return sorted_webhook_dict

def get_webhooks_for_task(task, name):
    s = object_session(task)
    equivalent_names = NAME_SYNONYMS.get(name, [name])
    return s.query(Webhook).filter_by(task_id=task.id).filter(
        Webhook.name.in_(equivalent_names)).all()

def get_webhooks_for_method(method, name):
    s = object_session(method)
    equivalent_names = NAME_SYNONYMS.get(name, [name])
    return s.query(Webhook).filter_by(method_id=method.id).filter(
        Webhook.name.in_(equivalent_names)).all()
