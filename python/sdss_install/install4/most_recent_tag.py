# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def most_recent_tag(tags,username=None):
    """Scan an SVN tags directory and return the most recent tag.

    Parameters
    ----------
    tags : str
        A URL pointing to an SVN tags directory.
    username : str, optional
        If set, pass the value to SVN's ``--username`` option.

    Returns
    -------
    most_recent_tag : str
        The most recent tag found in ``tags``.  The tag will be converted into
        a `PEP 386`_ / `PEP 440`_ -style version string, if it does not already
        follow that convention.

    Notes
    -----
    This function tries really, really hard to convert any non-standard tags
    into `PEP 386`_ / `PEP 440`_ -style version strings.  Any tags that fail
    this conversion step are ignored (and they should be!).

    .. _`PEP 386`: http://legacy.python.org/dev/peps/pep-0386/
    .. _`PEP 440`: http://legacy.python.org/dev/peps/pep-0440/

    This function was 'trained' on the tags in the idlutils, idlspec2d and
    photoop products.
    """
    from distutils.version import StrictVersion
    from subprocess import Popen, PIPE
    import re
    bare_digit_re = re.compile(r'^v?([0-9]+)(a|b|)$') # match things like v3a or v4
    almost_good_re = re.compile(r'^v?([0-9]+)(\.[0-9]+)(\.[0-9]+)*(a|b|)$') # match things like v5.0.2a
    command = ['svn']
    if username is not None: command += ['--username', username]
    command += ['ls',tags]
    proc = Popen(command,stdout=PIPE,stderr=PIPE)
    out, err = proc.communicate()
    try:
        tags = [v.rstrip('/').replace('_','.') for v in out.split('\n') if len(v) > 0]
    except TypeError:
        tags = [v.rstrip('/').replace('_','.') for v in out.decode('utf-8').split('\n') if len(v) > 0]
    valid_tags = list()
    for t in tags:
        v = None
        try:
            v = StrictVersion(t)
        except ValueError:
            if t.startswith('v'):
                try:
                    v = StrictVersion(t[1:])
                except ValueError:
                    m = bare_digit_re.match(t)
                    if m is not None:
                        g = m.groups()
                        if len(g[1]) > 0:
                            v = StrictVersion(g[0]+'.0'+g[1]+'0')
                        else:
                            v = StrictVersion(g[0]+'.0')
                    else:
                        m = almost_good_re.match(t)
                        if m is not None:
                            g = m.groups()
                            tt = g[0]+g[1]
                            if g[2] is None:
                                tt += '.0'
                            else:
                                tt += g[2]
                            if len(g[3]) > 0:
                                tt += g[3]+'0'
                            try:
                                v = StrictVersion(tt)
                            except ValueError:
                                # Give up at this point!
                                # print(t)
                                pass
        if v is not None:
            valid_tags.append(v)
    if len(valid_tags) == 0:
        return '0.0.0'
    mrt = sorted(valid_tags)
    return str(mrt[-1])

