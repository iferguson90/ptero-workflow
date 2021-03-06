from ..base import BaseAPITest
import abc


class PostWorkflowFailure(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def post_data(self):
        pass

    def setUp(self):
        super(PostWorkflowFailure, self).setUp()
        self.response = self.post(self.post_url, self.post_data)


    def test_should_set_expected_error_message(self):
        self.assertEqual(400, self.response.status_code)
        self.assertEqual({'error': self.expected_error_message},
                self.response.DATA)

class BorkIsInvalidWebhookName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = "Additional properties are not allowed (u'bork' was unexpected)"
    post_data = {
        'webhooks': {
            'scheduled': 'http://localhost/example/webhook',
            'running': ['http://localhost/example/webhook', 'http://localhost/example/webhook'],
            'failed': ['http://localhost/example/webhook'],
            'errored': ['http://localhost/example/webhook'],
            'succeeded': ['http://localhost/example/webhook'],
            'failed': ['http://localhost/example/webhook'],
            'canceled': ['http://localhost/example/webhook'],
            'ended': ['http://localhost/example/webhook'],
            'bork': ['http://localhost/example/webhook'],
        },
        'tasks': {
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'shell-command',
                        'parameters': {
                            'commandLine': ['cat'],
                            'user': 'testuser',
                            'workingDirectory': '/test/working/directory'
                        }
                    }
                ]
            },
        },
        'links': [
            {
                'source': 'input connector',
                'destination': 'A',
                'sourceProperty': 'in_a',
                'destinationProperty': 'param',
            }, {
                'source': 'A',
                'destination': 'output connector',
                'sourceProperty': 'result',
                'destinationProperty': 'out_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
    }


class InputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = '"input connector" is an illegal task name'
    post_data = {
        'webhooks': {
            'running': ['http://localhost/example/webhook', 'http://localhost/example/webhook'],
        },
        'tasks': {
            'input connector': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'shell-command',
                        'parameters': {
                            'commandLine': ['cat'],
                            'user': 'testuser',
                            'workingDirectory': '/test/working/directory'
                        }
                    }
                ]
            },
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'shell-command',
                        'parameters': {
                            'commandLine': ['cat'],
                            'user': 'testuser',
                            'workingDirectory': '/test/working/directory'
                        }
                    }
                ]
            },
        },
        'links': [
            {
                'source': 'input connector',
                'destination': 'A',
                'sourceProperty': 'in_a',
                'destinationProperty': 'param',
            }, {
                'source': 'A',
                'destination': 'output connector',
                'sourceProperty': 'result',
                'destinationProperty': 'out_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
    }


class OutputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = '"output connector" is an illegal task name'
    post_data = {
        'tasks': {
            'A': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'shell-command',
                        'parameters': {
                            'commandLine': ['cat'],
                            'user': 'testuser',
                            'workingDirectory': '/test/working/directory'
                        }
                    }
                ]
            },
            'output connector': {
                'methods': [
                    {
                        'name': 'execute',
                        'service': 'shell-command',
                        'parameters': {
                            'commandLine': ['cat'],
                            'user': 'testuser',
                            'workingDirectory': '/test/working/directory'
                        }
                    }
                ]
            },
        },
        'links': [
            {
                'source': 'input connector',
                'destination': 'A',
                'sourceProperty': 'in_a',
                'destinationProperty': 'param',
            }, {
                'source': 'A',
                'destination': 'output connector',
                'sourceProperty': 'result',
                'destinationProperty': 'out_a',
            },
        ],
        'inputs': {
            'in_a': 'kittens',
        },
    }

class NestedInputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = '"input connector" is an illegal task name'
    post_data = {
        'tasks': {
            'Inner': {
                'methods': [
                    {
                        'name': 'some_workflow',
                        'parameters': {
                            'tasks': {
                                'A': {
                                    'methods': [
                                        {
                                            'name': 'execute',
                                            'service': 'shell-command',
                                            'parameters': {
                                                'commandLine': ['cat'],
                                                'user': 'testuser',
                                                'workingDirectory': '/test/working/directory'
                                            }
                                        }
                                    ]
                                },
                                'input connector': {
                                    'methods': [
                                        {
                                            'name': 'execute',
                                            'service': 'shell-command',
                                            'parameters': {
                                                'commandLine': ['cat'],
                                                'user': 'testuser',
                                                'workingDirectory': '/test/working/directory'
                                            }
                                        }
                                    ]
                                },
                            },
                            'links': [
                                {
                                    'source': 'input connector',
                                    'destination': 'A',
                                    'sourceProperty': 'inner_input',
                                    'destinationProperty': 'param',
                                }, {
                                    'source': 'A',
                                    'destination': 'output connector',
                                    'sourceProperty': 'result',
                                    'destinationProperty': 'inner_output',
                                },
                            ],
                        },
                        'service': 'workflow'
                    },
                ],
            },
        },

        'links': [
            {
                'source': 'input connector',
                'destination': 'Inner',
                'sourceProperty': 'outer_input',
                'destinationProperty': 'inner_input',
            }, {
                'source': 'Inner',
                'destination': 'output connector',
                'sourceProperty': 'inner_output',
                'destinationProperty': 'outer_output',
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
        },
    }

class NestedOutputConnectorIsInvalidNodeName(PostWorkflowFailure, BaseAPITest):
    expected_error_message = '"output connector" is an illegal task name'
    post_data = {
        'tasks': {
            'Inner': {
                'methods': [
                    {
                        'name': 'some_workflow',
                        'parameters': {
                            'tasks': {
                                'A': {
                                    'methods': [
                                        {
                                            'name': 'execute',
                                            'service': 'shell-command',
                                            'parameters': {
                                                'commandLine': ['cat'],
                                                'user': 'testuser',
                                                'workingDirectory': '/test/working/directory'
                                            }
                                        }
                                    ]
                                },
                                'output connector': {
                                    'methods': [
                                        {
                                            'name': 'execute',
                                            'service': 'shell-command',
                                            'parameters': {
                                                'commandLine': ['cat'],
                                                'user': 'testuser',
                                                'workingDirectory': '/test/working/directory'
                                            }
                                        }
                                    ]
                                },
                            },
                            'links': [
                                {
                                    'source': 'input connector',
                                    'destination': 'A',
                                    'sourceProperty': 'inner_input',
                                    'destinationProperty': 'param',
                                }, {
                                    'source': 'A',
                                    'destination': 'output connector',
                                    'sourceProperty': 'result',
                                    'destinationProperty': 'inner_output',
                                },
                            ],
                        },
                        'service': 'workflow',
                    },
                ],
            },
        },

        'links': [
            {
                'source': 'input connector',
                'destination': 'Inner',
                'sourceProperty': 'outer_input',
                'destinationProperty': 'inner_input',
            }, {
                'source': 'Inner',
                'destination': 'output connector',
                'sourceProperty': 'inner_output',
                'destinationProperty': 'outer_output',
            },
        ],
        'inputs': {
            'outer_input': 'kittens',
        },
    }
