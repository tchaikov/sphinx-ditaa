# -*- coding: utf-8 -*-
"""
    sphinx.ext.ditaa
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Allow ditaa-formatted graphs to by included in Sphinx-generated
    documents inline.

    :copyright: Copyright 2011 by Arthur Gautier
    :copyright: Copyright 2011 by Zenexity
    :license: BSD, see LICENSE for details.
"""

import re
import codecs
import posixpath
from os import path
from math import ceil
from subprocess import Popen, PIPE
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.errors import SphinxError
from sphinx.util.osutil import ensuredir, ENOENT, EPIPE
from sphinx.util.compat import Directive


mapname_re = re.compile(r'<map id="(.*?)"')
svg_dim_re = re.compile(r'<svg\swidth="(\d+)pt"\sheight="(\d+)pt"', re.M)


class DitaaError(SphinxError):
    category = 'Ditaa error'


class ditaa(nodes.General, nodes.Element):
    pass


class Ditaa(Directive):
    """
    Directive to insert ditaa markup.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'alt': directives.unchanged,
        'inline': directives.flag,
        'caption': directives.unchanged,
    }

    def run(self):
        if self.arguments:
            print(self.arguments)
            document = self.state.document
            if self.content:
                return [document.reporter.warning(
                    'Ditaa directive cannot have both content and '
                    'a filename argument', line=self.lineno)]
            env = self.state.document.settings.env
            rel_filename, filename = env.relfn2path(self.arguments[0])
            env.note_dependency(rel_filename)
            try:
                fp = codecs.open(filename, 'r', 'utf-8')
                try:
                    dotcode = fp.read()
                finally:
                    fp.close()
            except (IOError, OSError):
                return [document.reporter.warning(
                    'External Ditaa file %r not found or reading '
                    'it failed' % filename, line=self.lineno)]
        else:
            dotcode = '\n'.join(self.content)
            if not dotcode.strip():
                return [self.state_machine.reporter.warning(
                    'Ignoring "ditaa" directive without content.',
                    line=self.lineno)]
        node = ditaa()
        node['code'] = dotcode
        node['options'] = []
        if 'alt' in self.options:
            node['alt'] = self.options['alt']
        if 'caption' in self.options:
            node['caption'] = self.options['caption']
        node['inline'] = 'inline' in self.options
        return [node]

def render_ditaa(self, code, options, prefix='ditaa'):
    """Render ditaa code into a PNG output file."""
    hashkey = code.encode('utf-8') + str(options).encode('utf-8') + \
              str(self.builder.config.ditaa).encode('utf-8') + \
              str(self.builder.config.ditaa_args).encode('utf-8')
    infname = '%s-%s.%s' % (prefix, sha(hashkey).hexdigest(), "ditaa")
    outfname = '%s-%s.%s' % (prefix, sha(hashkey).hexdigest(), "png")

    imgpath = self.builder.imgpath if hasattr(self.builder, 'imgpath') else ''
    inrelfn = posixpath.join(imgpath, infname)
    infullfn = path.join(self.builder.outdir, '_images', infname)
    outrelfn = posixpath.join(imgpath, outfname)
    outfullfn = path.join(self.builder.outdir, '_images', outfname)

    if path.isfile(outfullfn):
        return outrelfn, outfullfn

    ensuredir(path.dirname(outfullfn))

    # ditaa expects UTF-8 by default
    if isinstance(code, str):
        code = code.encode('utf-8')

    ditaa_args = [self.builder.config.ditaa]
    ditaa_args.extend(self.builder.config.ditaa_args)
    ditaa_args.extend(options)
    ditaa_args.extend( [infullfn] )
    ditaa_args.extend( [outfullfn] )

    f = open(infullfn, 'wb')
    f.write(code)
    f.close()

    try:
        p = Popen(ditaa_args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    except OSError as err:
        if err.errno != ENOENT:   # No such file or directory
            raise
        self.builder.warn('ditaa command %r cannot be run (needed for ditaa '
                          'output), check the ditaa setting' %
                          self.builder.config.ditaa)
        self.builder._ditaa_warned_dot = True
        return None, None
    wentWrong = False
    try:
        # Ditaa may close standard input when an error occurs,
        # resulting in a broken pipe on communicate()
        stdout, stderr = p.communicate(code)
    except OSError as err:
        if err.errno != EPIPE:
            raise
        wentWrong = True
    except IOError as err:
        if err.errno != EINVAL:
            raise
        wentWrong = True
    if wentWrong:
        # in this case, read the standard output and standard error streams
        # directly, to get the error message(s)
        stdout, stderr = p.stdout.read(), p.stderr.read()
        p.wait()
    if p.returncode != 0:
        raise DitaaError('ditaa exited with error:\n[stderr]\n%s\n'
                            '[stdout]\n%s' % (stderr, stdout))
    return outrelfn, outfullfn


def render_ditaa_html(self, node, code, options, prefix='ditaa',
                    imgcls=None, alt=None):
    try:
        fname, outfn = render_ditaa(self, code, options, prefix)
    except DitaaError as exc:
        raise nodes.SkipNode

    inline = node.get('inline', False)
    if inline:
        wrapper = 'span'
    else:
        wrapper = 'p'

    self.body.append(self.starttag(node, wrapper, CLASS='ditaa'))
    if fname is None:
        self.body.append(self.encode(code))
    else:
        # nothing in image map (the lines are <map> and </map>)
        self.body.append('<img src="%s"/>\n' %
                         fname)

    self.body.append('</%s>\n' % wrapper)
    raise nodes.SkipNode


def html_visit_ditaa(self, node):
    render_ditaa_html(self, node, node['code'], node['options'])


def render_ditaa_latex(self, node, code, options, prefix='ditaa'):
    try:
        fname, outfn = render_ditaa(self, code, options, prefix)
    except DitaaError as exc:
        raise nodes.SkipNode

    if fname is not None:
        self.body.append('\\par\\includegraphics{%s}\\par' % outfn)
    raise nodes.SkipNode


def latex_visit_ditaa(self, node):
    render_ditaa_latex(self, node, node['code'], node['options'])


def setup(app):
    app.add_node(ditaa,
                 html=(html_visit_ditaa, None),
                 latex=(latex_visit_ditaa, None))
    app.add_directive('ditaa', Ditaa)
    app.add_config_value('ditaa', 'ditaa', 'html')
    app.add_config_value('ditaa_args', [], 'html')
