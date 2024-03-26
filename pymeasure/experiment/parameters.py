#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2024 PyMeasure Developers
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
from warnings import warn


class InputField:
    """ Encapsulates the information for an input of an experiment with information about the name.

    :class:`.InputField` serves as a parent-class to :class:`.Parameter` and :class:`.Metadata` (and
    their respective subclasses). These classes differ in whether (and if yes, when) their value is
    writen to the data-file, and whether the value is applied when getting parameters from a file.

    - :class:`.InputField` is not written to file, nor applied when getting parameters from a file.
    - :class:`.Parameter` is written to the "Parameters" section of the file when the experiment is
      queued.
    - :class:`.Metadata` is writen to file after the
      :py:meth:`~pymeasure.experiment.procedure.Procedure.startup` of a
      :class:`~pymeasure.experiment.procedure.Procedure` is run and allows for storing information
      that is to be retrieved upon the start of the procedure (such as the starting time or specific
      instrument attributes or settings).

    :var value: The value of the :class:`.InputField`

    :param name: The :class:`.InputField` name
    :param default: The default value
    :param ui_class: A Qt class to use for the UI of this :class:`.InputField`
    :param group_by: Defines the :class:`InputField(s)<.InputField>` that controls the visibility
        of the associated input; can be a string containing the :class:`.InputField`
        name, a list of strings with multiple :class:`.InputField` names, or a dict
        containing {"InputField name": condition} pairs.
    :param group_condition: The condition for the group_by :class:`.InputField`
        that controls the visibility of this :class:`.InputField`, provided as a value
        or a (lambda)function. If the group_by argument is provided as a
        list of strings, this argument can be either a single condition or
        a list of conditions. If the group_by argument is provided as a dict
        this argument is ignored.
    """

    def __init__(self, name, default=None, ui_class=None, group_by=None, group_condition=True):
        self.name = name
        separator = ": "
        if separator in name:
            raise ValueError(f"The provided name argument '{name}' contains the "
                             f"separator '{separator}'.")

        self._value = None
        if default is not None:
            self.value = default
        self.default = default
        self.ui_class = ui_class
        self._help_fields = [('units are', 'units'), 'default']

        self.group_by = {}
        if isinstance(group_by, dict):
            self.group_by = group_by
        elif isinstance(group_by, str):
            self.group_by = {group_by: group_condition}
        elif isinstance(group_by, (list, tuple)) and all(isinstance(e, str) for e in group_by):
            if isinstance(group_condition, (list, tuple)):
                self.group_by = {g: c for g, c in zip(group_by, group_condition)}
            else:
                self.group_by = {g: group_condition for g in group_by}
        elif group_by is not None:
            raise TypeError("The provided group_by argument is not valid, should be either a "
                            "string, a list of strings, or a dict with {string: condition} pairs.")

    @property
    def value(self):
        if self.is_set():
            return self._value
        else:
            raise ValueError("Parameter value is not set")

    @value.setter
    def value(self, value):
        self._value = self.convert(value)

    @property
    def cli_args(self):
        """ helper for command line interface parsing of parameters

        This property returns a list of data to help formatting a command line
        interface interpreter, the list is composed of the following elements:
        - index 0: default value
        - index 1: List of value to format a help string, that is either,
        the name of the fields to be documented or a tuple with (helps_string,
        field)
        - index 2: type
        """
        return (self.default, self._help_fields, self.convert)

    def is_set(self):
        """ Returns True if the InputField value is set
        """
        return self._value is not None

    def convert(self, value):
        """ Convert user input to python data format

        Subclasses are expected to customize this method.
        Default implementation is the identity function

        :param value: value to be converted

        :return: converted value
        """

        return value

    def __str__(self):
        return str(self._value) if self.is_set() else ''

    def __repr__(self):
        return "<{}(name={},value={},default={})>".format(
            self.__class__.__name__, self.name, self._value, self.default)


class IntegerInputField(InputField):
    """ :class:`.InputField` subclass that uses the integer type to store the value.

    :var value: The integer value of the InputField

    :param name: the InputField name
    :param units: The units of measure for the InputField
    :param minimum: The minimum allowed value (default: -1e9)
    :param maximum: The maximum allowed value (default: 1e9)
    :param default: The default integer value
    :param ui_class: A Qt class to use for the UI of this InputField
    :param step: int step size for the field's UI spinbox. If None, spinbox will have step disabled
    """

    def __init__(self, name, units=None, minimum=-1e9, maximum=1e9, step=None, **kwargs):
        self.units = units
        self.minimum = int(minimum)
        self.maximum = int(maximum)
        super().__init__(name, **kwargs)
        self.step = int(step) if step else None
        self._help_fields.append('minimum')
        self._help_fields.append('maximum')

    def convert(self, value):
        if isinstance(value, str):
            value, _, units = value.strip().partition(" ")
            if units != "" and units != self.units:
                raise ValueError("Units included in string (%s) do not match"
                                 "the units of the IntegerInputField (%s)" % (units, self.units))

        try:
            value = int(value)
        except ValueError:
            raise ValueError("IntegerInputField given non-integer value of "
                             "type '%s'" % type(value))
        if value < self.minimum:
            raise ValueError("IntegerInputField value is below the minimum")
        elif value > self.maximum:
            raise ValueError("IntegerInputField value is above the maximum")

        return value

    def __str__(self):
        if not self.is_set():
            return ''
        result = "%d" % self._value
        if self.units:
            result += " %s" % self.units
        return result

    def __repr__(self):
        return "<{}(name={},value={},units={},default={})>".format(
            self.__class__.__name__, self.name, self._value, self.units, self.default)


class BooleanInputField(InputField):
    """ :class:`.InputField` subclass that uses the boolean type to store the value.

    :var value: The boolean value of the InputField

    :param name: the InputField name
    :param default: The default boolean value
    :param ui_class: A Qt class to use for the UI of this InputField
    """

    def convert(self, value):
        if isinstance(value, str):
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            else:
                raise ValueError("BooleanInputField given string value of '%s'" % value)
        elif isinstance(value, (int, float)) and value in [0, 1]:
            value = bool(value)
        elif isinstance(value, bool):
            value = value
        else:
            raise ValueError("BooleanInputField given non-boolean value of "
                             "type '%s'" % type(value))
        return value


class FloatInputField(InputField):
    """ :class:`.InputField` subclass that uses the floating point type to store the value.

    :var value: The floating point value of the InputField

    :param name: the InputField name
    :param units: The units of measure for the InputField
    :param minimum: The minimum allowed value (default: -1e9)
    :param maximum: The maximum allowed value (default: 1e9)
    :param decimals: The number of decimals considered (default: 15)
    :param default: The default floating point value
    :param ui_class: A Qt class to use for the UI of this InputField
    :param step: step size for the field's UI spinbox. If None, spinbox will have step disabled
    """

    def __init__(self, name, units=None, minimum=-1e9, maximum=1e9,
                 decimals=15, step=None, **kwargs):
        self.units = units
        self.minimum = minimum
        self.maximum = maximum
        super().__init__(name, **kwargs)
        self.decimals = decimals
        self.step = step
        self._help_fields.append('decimals')

    def convert(self, value):
        if isinstance(value, str):
            value, _, units = value.strip().partition(" ")
            if units != "" and units != self.units:
                raise ValueError("Units included in string (%s) do not match"
                                 "the units of the FloatInputField (%s)" % (units, self.units))

        try:
            value = float(value)
        except ValueError:
            raise ValueError("FloatInputField given non-float value of "
                             "type '%s'" % type(value))
        if value < self.minimum:
            raise ValueError("FloatInputField value is below the minimum")
        elif value > self.maximum:
            raise ValueError("FloatInputField value is above the maximum")

        return value

    def __str__(self):
        if not self.is_set():
            return ''
        result = "%g" % self._value
        if self.units:
            result += " %s" % self.units
        return result

    def __repr__(self):
        return "<{}(name={},value={},units={},default={})>".format(
            self.__class__.__name__, self.name, self._value, self.units, self.default)


class VectorInputField(InputField):
    """ :class:`.InputField` subclass that stores the value in a vector format.

    :var value: The value of the InputField as a list of floating point numbers

    :param name: the InputField name
    :param length: The integer dimensions of the vector
    :param units: The units of measure for the InputField
    :param default: The default value
    :param ui_class: A Qt class to use for the UI of this InputField
    """

    def __init__(self, name, length=3, units=None, **kwargs):
        self._length = length
        self.units = units
        super().__init__(name, **kwargs)
        self._help_fields.append('_length')

    def convert(self, value):
        if isinstance(value, str):
            # strip units if included
            if self.units is not None and value.endswith(" " + self.units):
                value = value[:-len(self.units)].strip()

            # Strip initial and final brackets
            if (value[0] != '[') or (value[-1] != ']'):
                raise ValueError("VectorInputField must be passed a vector"
                                 " denoted by square brackets if initializing"
                                 " by string.")
            raw_list = value[1:-1].split(",")
        elif isinstance(value, (list, tuple)):
            raw_list = value
        else:
            raise ValueError("VectorInputField given undesired value of "
                             "type '%s'" % type(value))
        if len(raw_list) != self._length:
            raise ValueError("VectorInputField given value of length "
                             "%d instead of %d" % (len(raw_list), self._length))
        try:
            value = [float(ve) for ve in raw_list]

        except ValueError:
            raise ValueError("VectorInputField given input '%s' that could "
                             "not be converted to floats." % str(value))

        return value

    def __str__(self):
        """If we eliminate spaces within the list __repr__ then the
        csv parser will interpret it as a single value."""
        if not self.is_set():
            return ''
        result = "".join(repr(self.value).split())
        if self.units:
            result += " %s" % self.units
        return result

    def __repr__(self):
        return "<{}(name={},value={},units={},length={})>".format(
            self.__class__.__name__, self.name, self._value, self.units, self._length)


class ListInputField(InputField):
    """ :class:`.InputField` subclass that stores the value as a list.
    String representation of choices must be unique.

    :param name: the InputField name
    :param choices: An explicit list of choices, which is disregarded if None
    :param units: The units of measure for the InputField
    :param default: The default value
    :param ui_class: A Qt class to use for the UI of this InputField
    """

    def __init__(self, name, choices=None, units=None, **kwargs):
        self.units = units
        if choices is not None:
            keys = [str(c) for c in choices]
            # check that string representation is unique
            if not len(keys) == len(set(keys)):
                raise ValueError(
                    "String representation of choices is not unique!")
            self._choices = {k: c for k, c in zip(keys, choices)}
        else:
            self._choices = None
        super().__init__(name, **kwargs)
        self._help_fields.append(('choices are', 'choices'))

    def convert(self, value):
        if self._choices is None:
            raise ValueError("ListInputField cannot be set since "
                             "allowed choices are set to None.")

        # strip units if included
        if isinstance(value, str):
            if self.units is not None and value.endswith(" " + self.units):
                value = value[:-len(self.units)].strip()

        if str(value) in self._choices.keys():
            value = self._choices[str(value)]
        else:
            raise ValueError("Invalid choice for parameter. "
                             "Must be one of %s" % str(self._choices))

        return value

    @property
    def choices(self):
        """ Returns an immutable iterable of choices, or None if not set. """
        return tuple(self._choices.values())


class PhysicalInputField(VectorInputField):
    """ :class:`.VectorInputField` subclass of 2 dimensions to store a value
    and its uncertainty.

    :var value: The value of the InputField as a list of 2 floating point numbers

    :param name: the InputField name
    :param uncertainty_type: Type of uncertainty, 'absolute', 'relative' or 'percentage'
    :param units: The units of measure for the InputField
    :param default: The default value
    :param ui_class: A Qt class to use for the UI of this InputField
    """

    def __init__(self, name, uncertaintyType='absolute', **kwargs):
        super().__init__(name, length=2, **kwargs)
        self._utype = ListParameter("uncertainty type",
                                    choices=['absolute', 'relative', 'percentage'],
                                    default=None)
        self._utype.value = uncertaintyType

    def convert(self, value):
        if isinstance(value, str):
            # strip units if included
            if self.units is not None and value.endswith(" " + self.units):
                value = value[:-len(self.units)].strip()

            # Strip initial and final brackets
            if (value[0] != '[') or (value[-1] != ']'):
                raise ValueError("PhysicalInputField must be passed a vector"
                                 " denoted by square brackets if initializing"
                                 " by string.")
            raw_list = value[1:-1].split(",")
        elif isinstance(value, (list, tuple)):
            raw_list = value
        else:
            raise ValueError("PhysicalInputField given undesired value of "
                             "type '%s'" % type(value))
        if len(raw_list) != self._length:
            raise ValueError("PhysicalInputField given value of length "
                             "%d instead of %d" % (len(raw_list), self._length))
        try:
            value = [float(ve) for ve in raw_list]
        except ValueError:
            raise ValueError("PhysicalInputField given input '%s' that could "
                             "not be converted to floats." % str(value))
        # Uncertainty must be non-negative
        value[1] = abs(value[1])

        return value

    @property
    def uncertainty_type(self):
        return self._utype.value

    @uncertainty_type.setter
    def uncertainty_type(self, uncertaintyType):
        oldType = self._utype.value
        self._utype.value = uncertaintyType
        newType = self._utype.value

        if self.is_set():
            # Convert uncertainty value to the new type
            if (oldType, newType) == ('absolute', 'relative'):
                self._value[1] = abs(self._value[1] / self._value[0])
            if (oldType, newType) == ('relative', 'absolute'):
                self._value[1] = abs(self._value[1] * self._value[0])
            if (oldType, newType) == ('relative', 'percentage'):
                self._value[1] = abs(self._value[1] * 100.0)
            if (oldType, newType) == ('percentage', 'relative'):
                self._value[1] = abs(self._value[1] * 0.01)
            if (oldType, newType) == ('percentage', 'absolute'):
                self._value[1] = abs(self._value[1] * self._value[0] * 0.01)
            if (oldType, newType) == ('absolute', 'percentage'):
                self._value[1] = abs(self._value[1] * 100.0 / self._value[0])

    def __str__(self):
        if not self.is_set():
            return ''
        result = f"{self._value[0]:g} +/- {self._value[1]:g}"
        if self.units:
            result += " %s" % self.units
        if self._utype.value is not None:
            result += " (%s)" % self._utype.value
        return result

    def __repr__(self):
        return "<{}(name={},value={},units={},uncertaintyType={})>".format(
            self.__class__.__name__, self.name, self._value, self.units, self._utype.value)


class Parameter(InputField):
    pass


class IntegerParameter(Parameter, IntegerInputField):
    pass


class BooleanParameter(Parameter, BooleanInputField):
    pass


class FloatParameter(Parameter, FloatInputField):
    pass


class VectorParameter(Parameter, VectorInputField):
    pass


class ListParameter(Parameter, ListInputField):
    pass


class PhysicalParameter(Parameter, PhysicalInputField):
    pass


class Measurable:
    """ Encapsulates the information for a measurable experiment parameter
    with information about the name, fget function and units if supplied.
    The value property is called when the procedure retrieves a datapoint
    and calls the fget function. If no fget function is specified, the value
    property will return the latest set value of the parameter (or default
    if never set).

    :var value: The value of the parameter

    :param name: The parameter name
    :param fget: The parameter fget function (e.g. an instrument parameter)
    :param default: The default value
    """
    DATA_COLUMNS = []

    def __init__(self, name, fget=None, units=None, measure=True, default=None, **kwargs):
        self.name = name
        self.units = units
        self.measure = measure
        if fget is not None:
            self.fget = fget
            self._value = fget()
        else:
            self._value = default
        Measurable.DATA_COLUMNS.append(name)

    def fget(self):
        return self._value

    @property
    def value(self):
        if hasattr(self, 'fget'):
            self._value = self.fget()
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class Metadata(InputField):
    """ Encapsulates the information for metadata of the experiment with
    information about the name, the fget function and the units, if supplied.
    If no fget function is specified, the value property will return the
    latest set value of the parameter (or default if never set).

    :var value: The value of the parameter. This returns (if a value is set)
        the value obtained from the `fget` (after evaluation) or a manually
        set value. Returns `None` if no value has been set

    :param name: The parameter name
    :param fget: The parameter fget function; can be provided as a callable,
        or as a string, in which case it is assumed to be the name of a
        method or attribute of the `Procedure` class in which the Metadata is
        defined. Passing a string also allows for nested attributes by separating
        them with a period (e.g. to access an attribute or method of an
        instrument) where only the last attribute can be a method.
    :param units: The parameter units

        .. deprecated:: 0.14
            Removed from the base :class:`Metadata` class; the numeric subclasses
            :class:`.IntegerMetadata`, :class:`.FloatMetadata`, :class:`.VectorMetadata`,
            :class:`.ListMetadata`, and :class:`.PhysicalMetadata` do provide the possibility to
            define units.

    :param default: The default value, in case no value is assigned or if no
        fget method is provided
    :param fmt: A string used to format the value upon writing it to a file.
        Default is "%s"

        .. deprecated:: 0.14
            The formatting is now defined by the specific :class:`.Metadata` subclasses; the
            :class:`.Metadata` base class uses :code:`str` to convert the value to a string.

    """

    def __init__(self, name, fget=None, units=None, fmt=None, **kwargs):
        self.fget = fget
        self.evaluated = False
        super().__init__(name, **kwargs)

        if units is not None:
            self.units = units
            warn("units parameter is deprecated, use appropriate Metadata subclass instead"
                 " instead", FutureWarning)

        if fmt is not None:
            self.fmt = fmt
            warn("fmt parameter is deprecated, use appropriate Metadata subclass instead"
                 " instead", FutureWarning)

    def evaluate(self, parent=None, new_value=None):
        if new_value is not None and self.fget is not None:
            raise ValueError("Metadata with a defined fget method"
                             " cannot be manually assigned a value")
        elif new_value is not None:
            self._value = new_value
        elif self.fget is not None:
            self._value = self.eval_fget(parent)

        self.evaluated = True
        return self.value

    def eval_fget(self, parent):
        fget = self.fget
        if isinstance(fget, str):
            obj = parent
            for obj_name in fget.split('.'):
                obj = getattr(obj, obj_name)
            fget = obj

        if callable(fget):
            return fget()
        else:
            return fget

    def __str__(self):
        # Deprecated, can be removed once the units and fmt parameters are removed from the
        # Metadata base class
        if hasattr(self, 'fmt'):
            result = self.fmt % self.value
        else:
            result = super().__str__()

        if hasattr(self, 'units') and self.units is not None:
            result += " %s" % self.units

        return result


class IntegerMetadata(Metadata, IntegerInputField):
    pass


class BooleanMetadata(Metadata, BooleanInputField):
    pass


class FloatMetadata(Metadata, FloatInputField):
    pass


class VectorMetadata(Metadata, VectorInputField):
    pass


class ListMetadata(Metadata, ListInputField):
    pass


class PhysicalMetadata(Metadata, PhysicalInputField):
    pass
