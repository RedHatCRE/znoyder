#!/usr/bin/env python3
#
# Copyright 2021 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Classes and functions borrowed from https://opendev.org/zuul/zuul
#

import collections
from copy import deepcopy
import io

import yaml

from znoyder.lib import logger
from znoyder.lib import utils
from znoyder.lib.exceptions import PipelineError
from znoyder.lib.exceptions import YAMLDuplicateKeyError


LOG = logger.LOG


class ZuulPipeline(object):
    """Enumeration for the Zuul Pipeline"""
    # TEMPLATES are same level as other pipelines
    RANGE = (TEMPLATES, CHECK, GATE, POST, EXPERIMENTAL) = range(5)

    @staticmethod
    def to_str(column) -> str:
        return {
            ZuulPipeline.TEMPLATES: 'templates',
            ZuulPipeline.CHECK: 'check',
            ZuulPipeline.GATE: 'gate',
            ZuulPipeline.POST: 'post',
            ZuulPipeline.EXPERIMENTAL: 'experimental',
        }[column]

    @staticmethod
    def to_type(pipeline) -> int:
        pipelines = {
            'templates': ZuulPipeline.TEMPLATES,
            'check': ZuulPipeline.CHECK,
            'gate': ZuulPipeline.GATE,
            'post': ZuulPipeline.POST,
            'experimental': ZuulPipeline.EXPERIMENTAL,
        }
        if pipeline not in pipelines:
            raise PipelineError("Job pipeline is not valid: %s" %
                                pipeline)
        return pipelines[pipeline]

    @staticmethod
    def get_pipelines_str(pipelines) -> list:
        """Gets job types as strings

        Args:
            pipelines (:obj:`list`): Trigger types as ZuulPipeline

        Returns:
            (:obj:`list`): list of pipelines as strings
        """
        # Convert to list if one pipeline was passed
        pipelines = [pipelines] if type(pipelines) \
            is int else pipelines

        for job_pipeline in pipelines:
            if job_pipeline not in ZuulPipeline.RANGE:
                raise PipelineError("Job pipeline is not valid: %s" %
                                    job_pipeline)

        # We are interested only in jobs defined in project
        pipelines = list(map(lambda pipeline: ZuulPipeline.to_str(pipeline),
                             pipelines))
        return pipelines


class ZuulMark:
    # The yaml mark class differs between the C and python versions.
    # The C version does not provide a snippet, and also appears to
    # lose data under some circumstances.
    def __init__(self, start_mark, end_mark, stream):
        self.name = start_mark.name
        self.index = start_mark.index
        self.line = start_mark.line
        self.end_line = end_mark.line
        self.end_index = end_mark.index
        self.column = start_mark.column
        self.end_column = end_mark.column
        self.snippet = stream[start_mark.index:end_mark.index]

    def __str__(self):
        return '  in "{name}", line {line}, column {column}'.format(
            name=self.name,
            line=self.line + 1,
            column=self.column + 1,
        )

    def __eq__(self, other):
        return (self.line == other.line and
                self.snippet == other.snippet)

    def serialize(self):
        return {
            "name": self.name,
            "index": self.index,
            "line": self.line,
            "end_line": self.end_line,
            "end_index": self.end_index,
            "column": self.column,
            "end_column": self.end_column,
            "snippet": self.snippet,
        }

    @classmethod
    def deserialize(cls, data):
        o = cls.__new__(cls)
        o.__dict__.update(data)
        return o


# Check the class ZuulSafeLoader from configloader.py from zuul project
class ZuulSafeLoader(yaml.SafeLoader):
    zuul_node_types = frozenset(('job', 'nodeset', 'secret', 'pipeline',
                                 'project', 'project-template',
                                 'semaphore', 'queue', 'pragma'))

    def __init__(self, stream, context):
        wrapped_stream = io.StringIO(stream)
        wrapped_stream.name = str(context)
        super(ZuulSafeLoader, self).__init__(wrapped_stream)
        self.add_multi_constructor('!encrypted/', self.construct_encrypted)
        self.name = str(context)
        self.zuul_context = context
        self.zuul_stream = stream

    @classmethod
    def construct_encrypted(cls, loader, tag_suffix, node):
        return loader.construct_sequence(node)

    def construct_mapping(self, node, deep=False):
        keys = set()
        for k, v in node.value:
            # The key << needs to be treated special since that will merge
            # the anchor into the mapping and not create a key on its own.
            if k.value == '<<':
                continue

            if not isinstance(k.value, collections.abc.Hashable):
                # This happens with "foo: {{ bar }}"
                # This will raise an error in the superclass
                # construct_mapping below; ignore it for now.
                continue

            if k.value in keys:
                mark = ZuulMark(node.start_mark, node.end_mark,
                                self.zuul_stream)
                raise YAMLDuplicateKeyError(k.value, node, self.zuul_context,
                                            mark)
            keys.add(k.value)
        r = super(ZuulSafeLoader, self).construct_mapping(node, deep)
        keys = frozenset(r.keys())
        if len(keys) == 1 and keys.intersection(self.zuul_node_types):
            d = list(r.values())[0]
            if isinstance(d, dict):
                d['_start_mark'] = ZuulMark(node.start_mark,
                                            node.end_mark,
                                            self.zuul_stream)
                d['_source_context'] = self.zuul_context
        return r


class ZuulProject(object):
    """A Project represents top level component.
       It may define or use jobs directly as well job templates.

    Args:
        project_name (:obj:`str`): Name of the project e.g. neutron
        project_path (:obj:`str`): Local path to the project directory
    """
    def __init__(self, project_name=None, project_path=None, templates=None):
        if templates is None:
            templates = []

        self.project_name = project_name
        self.project_path = project_path
        self.all_templates = templates  # defined by other projects
        self.project_templates = []     # used by this project
        self.defined_templates = []     # defined by this project
        self.project_jobs = []
        self.config_paths = []
        if project_path and not self.project_name:
            self.project_name = project_path.strip("/").split("/")[-1]

    def get_project_config_files(self) -> list:
        if self.config_paths:
            return self.config_paths
        self.config_paths = utils.get_config_paths(self.project_path)
        return self.config_paths

    def get_list_of_jobs(self, pipelines=None) -> list:
        """Gets list of jobs for a particular project.
           This does not include jobs defined under templates.

        Args:
            pipelines (:obj:`list`): Pipelines as list of ZuulPipeline objects

        Returns:
            (:obj:`list`): list of ZuulJob objects associated with the project
        """
        if pipelines is None:
            pipelines = []

        pipelines = ZuulPipeline.get_pipelines_str(pipelines)

        LOG.debug('Discovering jobs for pipelines: %s' %
                  pipelines)

        CASE = 'project'

        for config_file in self.get_project_config_files():
            projects = self._get_entries_from_config(config_file, CASE)
            for project in projects:
                for pipeline in pipelines:
                    if pipeline in project:
                        jobs = project.get(pipeline).get('jobs')
                        if not jobs:
                            continue
                        for job in jobs:
                            z_jobs = self._get_jobs_from_entry(job,
                                                               pipeline)
                            self.project_jobs.extend(z_jobs)

        return self.project_jobs

    def get_list_of_used_templates(self) -> list:
        """Gets list of templates used by a project.

        Returns:
            (:obj:`list`): list of ZuulProjectTemplate objects
                           associated with the project
        """

        LOG.debug('Discovering templates')

        CASE = 'project'

        for config_file in self.get_project_config_files():
            project = self._get_entries_from_config(config_file, CASE)

            template_str = ZuulPipeline.to_str(ZuulPipeline.TEMPLATES)
            for used_template in project:
                if template_str in used_template:
                    templates = used_template.get(template_str)
                    LOG.debug("Found templates %s" % templates)
                    for template in templates:
                        zuul_template = self._get_availabie_template(template)
                        self.project_templates.append(zuul_template)

        return self.project_templates

    def _get_availabie_template(self, template_name) -> object:
        """Gets template from passed by other projects

        Args:
            template_name (:obj:`str`): Name of the template

        Returns:
            (:obj:`ZuulProjectTemplate`): project template
        """
        found = False
        template_obj = None
        for template in self.all_templates:
            if str(template) == template_name:
                found = True
                template_obj = template
                break

        if not found:
            LOG.warning("Used template not found in base templates: %s"
                        % template_name)
            template_obj = ZuulProjectTemplate(template_name)

        return template_obj

    def get_list_of_defined_templates(self, pipelines=None) -> list:
        """Gets list of templates defined in a project.

        Args:
            pipelines (:obj:`list`): Pipelines as list of ZuulPipeline objects

        Returns:
            (:obj:`list`): list of ZuulProjectTemplate objects
                           associated with the project
        """
        if pipelines is None:
            pipelines = []

        pipelines = ZuulPipeline.get_pipelines_str(pipelines)

        LOG.debug('Discovering templates and jobs for pipelines: %s' %
                  pipelines)

        CASE = 'project-template'

        for config_file in self.get_project_config_files():
            project = self._get_entries_from_config(config_file, CASE)

            for template in project:
                p_template = ZuulProjectTemplate(template.get('name'),
                                                 self.project_name,
                                                 template)

                for pipeline in pipelines:
                    if pipeline in template:
                        jobs = template.get(pipeline).get('jobs')
                        for job_r in jobs:
                            job = self._get_jobs_from_entry(job_r, pipeline)
                            p_template.associate_job(job)

                self.defined_templates.append(p_template)

        return self.defined_templates

    def _get_entries_from_config(self, config_file, config_section) -> list:
        """Helper function to get part of the config

        Args:
            config_file (:obj:`str`): path to the config file
            config_section (:obj:`str`): config section

        Returns:
            (:obj:`list`): partial config
        """

        LOG.debug('Discovering section "%s" from config: %s' %
                  (config_section, config_file))

        config = []

        with open(config_file, 'r') as file:
            data = file.read()
            loader = ZuulSafeLoader(data, 'null').get_single_data()
            for entry in loader:
                if config_section in entry:
                    config.append(entry.get(config_section))
        return config

    def _get_jobs_from_entry(self, job_entry, pipeline) -> list:
        """Helper function to standardize job object as the zuul job entry
           may be just a string or dictionary.

        Args:
            job_entry (:obj:`str`): zuul entry for the job
            pipeline (:obj:`str`): ZuulPipeline as string name

        Returns:
            (:obj:`list`): list of ZuulJob objects associated with the project
        """
        jobs = []
        if isinstance(job_entry, str):
            LOG.debug('Found %s job: %s' % (pipeline, job_entry))
            jobs.append(ZuulJob(job_entry, pipeline, {}))
        else:
            for job_name, job_parameters in job_entry.items():
                LOG.debug('Found %s job: %s with options %s' %
                          (pipeline, job_name, job_parameters))
                jobs.append(ZuulJob(job_name, pipeline, job_parameters))

        return jobs


class ZuulProjectTemplate(object):
    """Project Template defines jobs which can be used by multiple
       Zuul Projects.

    Args:
        template_name (:obj:`str`): Template name
    """
    def __init__(self, template_name, template_project=None,
                 template_data=None):
        if template_data is None:
            template_data = {}

        # Project that defines template
        self.template_project = template_project
        self.template_name = template_name
        self.template_data = template_data
        self.template_jobs = []

    def associate_job(self, job):
        if job not in self.template_jobs:
            self.template_jobs.extend(job)
        else:
            LOG.warning('JOB %s defined multiple times' % job)

    def get_jobs(self, pipeline):
        """Get jobs associated with template and specific pipeline

        Args:
            pipeline (:obj:`ZuulPipeline`): Job pipeline, e.g. check, gate

        Returns:
            (:obj:`list`): list of ZuulJob objects associated with the project
        """
        jobs = []
        for job in self.template_jobs:
            job_pipeline = ZuulPipeline.to_type(job.pipeline)
            if job_pipeline in pipeline:
                jobs.append(job)

        return jobs

    def __str__(self) -> str:
        return self.template_name

    def __repr__(self) -> str:
        return self.template_name


class ZuulJob(yaml.YAMLObject):
    """Zuul Job representation

    Args:
        name (:obj:`str`): Job name
        pipeline (:obj:`str`): Job pipeline, e.g. check, gate, post
        parameters (:obj:`dict`): JSON job parameters
    """
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!ZuulJob'

    def __init__(self, name, pipeline, parameters=None):
        if parameters is None:
            parameters = {}

        self.name = name
        self.pipeline = pipeline
        self.parameters = deepcopy(parameters)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash((self.name, self.pipeline))

    def __eq__(self, other) -> bool:
        return type(other) is type(self) and (
            self.name == other.name
            and self.pipeline == other.pipeline
        )

    def really_equal(self, other) -> bool:
        return type(other) is type(self) and (
            self.name == other.name
            and self.pipeline == other.pipeline
            and self.parameters == other.parameters
        )
