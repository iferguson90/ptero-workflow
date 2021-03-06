# PTero Workflow Service
[![Build Status](https://travis-ci.org/genome/ptero-workflow.svg?branch=master)](https://travis-ci.org/genome/ptero-workflow)
[![Coverage Status](https://img.shields.io/coveralls/genome/ptero-workflow.svg)](https://coveralls.io/r/genome/ptero-workflow?branch=master)
[![Requirements Status](https://requires.io/github/genome/ptero-workflow/requirements.svg?branch=master)](https://requires.io/github/genome/ptero-workflow/requirements/?branch=master)

This project provides the client facing API for the PTero Workflow system.
This system is designed to be a highly scalable replacement of the [legacy
Workflow](https://github.com/genome/tgi-workflow) system from [The Genome
Institute](http://genome.wustl.edu/).

The current implementation, which does not provide an easy to use API, easily
handles our production workflows with tens of thousands of nodes.  For
reference, it can be found in two parts:
[core](https://github.com/genome/flow-core) and
[workflow](https://github.com/genome/flow-workflow)

The workflows are driven using an implementation of [Petri
nets](https://en.wikipedia.org/wiki/Petri_net) with some extensions for
[color](https://en.wikipedia.org/wiki/Coloured_Petri_net) and token data.

The API is currently described
[here](https://github.com/genome/ptero-apis/blob/master/workflow.md).
The other existing components are: the [petri
core](https://github.com/genome/ptero-petri) service and a [forking shell
command](https://github.com/genome/ptero-shell-command) service.


## Testing

The tests for this service depend on a running petri and forking shell command
service.  To run the tests, first install some tools:

    pip install tox

Then setup the [petri](https://github.com/genome/ptero-petri) service and the
[shell-command](https://github.com/genome/ptero-shell-command) service. In the
parent directory:

    git clone https://github.com/genome/ptero-petri.git
    git clone https://github.com/genome/ptero-shell-command.git

And in the ptero-workflow directory:

    ln -s ../ptero-petri
    ln -s ../ptero-shell-command

Now, you can run the tests using tox:

    tox -e py27

To see a coverage report after successfully running the tests:

    coverage report
