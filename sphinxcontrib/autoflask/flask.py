"""
    sphinxcontrib.autohttp.flask
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The sphinx.ext.autodoc-style HTTP API reference builder (from Flask)
    for sphinxcontrib.httpdomain.

    :copyright: Copyright 2011 by Hong Minhee
    :license: BSD, see LICENSE for details.

"""

import re
import six

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList

from sphinx.util import force_decode
from sphinx.util.compat import Directive
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.util.docstrings import prepare_docstring
from sphinx.pycode import ModuleAnalyzer

from sphinxcontrib import httpdomain
from sphinxcontrib.autohttp.common import http_directive, import_object

def sort_by_method(entries):
    def cmp(item):
        order = ['HEAD', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH',
                 'OPTIONS', 'TRACE', 'CONNECT', 'COPY', 'ANY']
        method = item[0].split(' ', 1)[0]
        if method in order:
            return order.index(method)
        return 100
    return sorted(entries, key=cmp)


def http_resource_anchor(method, path):
    path = re.sub(r'[{}]', '', re.sub(r'[<>:/]', '-', path))
    return method.lower() + '-' + path

def translate_werkzeug_rule(rule):
    from werkzeug.routing import parse_rule
    buf = six.StringIO()
    for conv, arg, var in parse_rule(rule):
        if conv:
            buf.write('(')
            if conv != 'default':
                buf.write(conv)
                buf.write(':')
            buf.write(var)
            buf.write(')')
        else:
            buf.write(var)
    return buf.getvalue()


def get_routes(app):
    for rule in app.url_map.iter_rules():
        methods = rule.methods.difference(['OPTIONS', 'HEAD'])
        for method in methods:
            path = translate_werkzeug_rule(rule.rule)
            yield method, path, rule.endpoint


class AutoflaskDirective(Directive):

    has_content = True
    required_arguments = 1
    option_spec = {'endpoints': directives.unchanged,
                   'blueprints': directives.unchanged,
                   'undoc-endpoints': directives.unchanged,
                   'undoc-blueprints': directives.unchanged,
                   'undoc-static': directives.unchanged,
                   'include-empty-docstring': directives.unchanged}

    @property
    def endpoints(self):
        endpoints = self.options.get('endpoints', None)
        if not endpoints:
            return None
        return frozenset(re.split(r'\s*,\s*', endpoints))

    @property
    def undoc_endpoints(self):
        undoc_endpoints = self.options.get('undoc-endpoints', None)
        if not undoc_endpoints:
            return frozenset()
        return frozenset(re.split(r'\s*,\s*', undoc_endpoints))

    @property
    def blueprints(self):
        blueprints = self.options.get('blueprints', None)
        if not blueprints:
            return None
        return frozenset(re.split(r'\s*,\s*', blueprints))

    @property
    def undoc_blueprints(self):
        undoc_blueprints = self.options.get('undoc-blueprints', None)
        if not undoc_blueprints:
            return frozenset()
        return frozenset(re.split(r'\s*,\s*', undoc_blueprints))

    def _make_toc(self, routes):
        content = {}
        items = [(method, path, endpoint) for method, path, endpoint in routes]

        entries = []
        items = sorted(items, key=lambda item: item[1])
        for method, path, info in items:
            fmt = "`{label}: <#{anchor}>`_\n"
            entries.append(fmt.format(label=method+" "+path, anchor=http_resource_anchor(method, path)))
        return entries
    
    def make_rst(self):
        app = import_object(self.arguments[0])
        yield "Services:\n"
        yield ""
        for x in self._make_toc(get_routes(app)):
            yield '- {}'.format(x)
            yield ""
        
        for method, path, endpoint in get_routes(app):
            try:
                blueprint, _, endpoint_internal = endpoint.rpartition('.')
                if self.blueprints and blueprint not in self.blueprints:
                    continue
                if blueprint in self.undoc_blueprints:
                    continue
            except ValueError:
                pass  # endpoint is not within a blueprint

            if self.endpoints and endpoint not in self.endpoints:
                continue
            if endpoint in self.undoc_endpoints:
                continue
            try:
                static_url_path = app.static_url_path # Flask 0.7 or higher
            except AttributeError:
                static_url_path = app.static_path # Flask 0.6 or under
            if ('undoc-static' in self.options and endpoint == 'static' and
                path == static_url_path + '/(path:filename)'):
                continue
            view = app.view_functions[endpoint]
            docstring = view.__doc__ or ''
            if hasattr(view, 'view_class'):
                meth_func = getattr(view.view_class, method.lower(), None)
                if meth_func and meth_func.__doc__:
                    docstring = meth_func.__doc__
            if not isinstance(docstring, six.text_type):
                analyzer = ModuleAnalyzer.for_module(view.__module__)
                docstring = force_decode(docstring, analyzer.encoding)

            if not docstring and 'include-empty-docstring' not in self.options:
                continue

            #Thanks flask-classy for this :D
            if len(endpoint.split(":")) == 2:
                view_cls, view_func = endpoint.split(":")
                if hasattr(app, 'view_classes') and view_cls in app.view_classes:
                    cls = app.view_classes[view_cls]
                    if hasattr(cls,'args_rules'):
                        rules = cls.args_rules
                        if view_func in rules:
                            docstring += '\n\n'
                            for a in rules[view_func]:
                                t = str(a.type).replace('type','').replace("'","").replace('<','').replace('>','')
                                params = dict(
                                    type=t,
                                    name=str(a.name),
                                    description=str(a.description),
                                    default=str(a.default)
                                )
                                if a.required:
                                    docstring += '    :<json {type} {name}: {description}.\n'.format(**params)
                                else:
                                    docstring += '    :<json {type} {name}: *(optional)* {description}. *Default*={default}\n'.format(**params)
            docstring = prepare_docstring(docstring)
            for line in http_directive(method, path, docstring):
                yield line

    def run(self):
        node = nodes.section()
        node.document = self.state.document
        result = ViewList()
        for line in self.make_rst():
            result.append(line, '<autoflask>')
        nested_parse_with_titles(self.state, result, node)
        return node.children

def setup(app):
    if 'http' not in app.domains:
        httpdomain.setup(app)
    app.add_directive('autoflask', AutoflaskDirective)

