#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2021 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import os
from datetime import datetime
from string import Formatter


def replace_placeholders(string, procedure, date_format="%Y-%m-%d", time_format="%H:%M:%S"):
    """Replace placeholders in string with values from procedure parameters.

    Replaces the placeholders in the provided string with the values of the
    associated parameters, as provided by the procedure. This uses the standard
    python string.format syntax. Apart from the parameter in the procedure (which
    should be called by their full names) "date" and "time" are also added as optional
    placeholders.

    :param string:
        The string in which the placeholders are to be replaced. Python string.format
        syntax is used, e.g. "{Parameter Name}" to insert a FloatParameter called
        "Parameter Name", or "{Parameter Name:.2f}" to also specifically format the
        parameter.

    :param procedure:
        The procedure from which to get the parameter values.

    :param date_format:
        A string to represent how the additional placeholder "date" will be formatted.

    :param time_format:
        A string to represent how the additional placeholder "time" will be formatted.

    """
    now = datetime.now()

    parameters = procedure.parameter_objects()
    placeholders = {param.name: param.value for param in parameters.values()}

    placeholders["date"] = now.strftime(date_format)
    placeholders["time"] = now.strftime(time_format)

    # Check keys against available parameters
    invalid_keys = [i[1] for i in Formatter().parse(string)
                    if i[1] is not None and i[1] not in placeholders]
    if invalid_keys:
        raise KeyError("The following placeholder-keys are not valid: '%s'; "
                       "valid keys are: '%s'." % (
                           "', '".join(invalid_keys),
                           "', '".join(placeholders.keys())
                       ))

    return string.format(**placeholders)


def unique_filename(directory, prefix='DATA', suffix='', ext='csv',
                    dated_folder=False, index=True, datetimeformat="%Y-%m-%d",
                    procedure=None):
    """ Returns a unique filename based on the directory and prefix
    """
    now = datetime.now()
    directory = os.path.abspath(directory)

    if procedure is not None:
        prefix = replace_placeholders(prefix, procedure)
        suffix = replace_placeholders(suffix, procedure)

    if dated_folder:
        directory = os.path.join(directory, now.strftime('%Y-%m-%d'))
    if not os.path.exists(directory):
        os.makedirs(directory)
    if index:
        i = 1
        basename = "%s%s" % (prefix, now.strftime(datetimeformat))
        basepath = os.path.join(directory, basename)
        filename = "%s_%d%s.%s" % (basepath, i, suffix, ext)
        while os.path.exists(filename):
            i += 1
            filename = "%s_%d%s.%s" % (basepath, i, suffix, ext)
    else:
        basename = "%s%s%s.%s" % (prefix, now.strftime(datetimeformat), suffix, ext)
        filename = os.path.join(directory, basename)
    return filename
