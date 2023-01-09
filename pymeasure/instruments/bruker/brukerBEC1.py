import logging
from enum import IntFlag

from pyvisa import VisaIOError
from pyvisa.constants import VI_ERROR_TMO

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import (
    strict_discrete_set,
    strict_range
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class BrukerBEC1(Instrument):
    """ A class representing the Bruker B-EC1 magnet power supply controller.
    """
    CURRENT_RANGE = (-60, 60)
    VOLTAGE_RANGE = (-45, 45)

    def __init__(self, adapter, **kwargs):
        super().__init__(
            adapter,
            "Bruker B-EC1 magnet power supply controller",
            includeSCPI=False,
            asrl=dict(
                baud_rate=9600,
                data_bits=8,
                stop_bits=10,
                parity=1,
                write_termination='\r',
                # write_termination='\n',
            ),
            **kwargs,
        )

    class ERRORS(IntFlag):
        """ Enum element for error decoding
        """
        FUNCTION = 1  # Function not supported, also e.g. during polarity reversal
        ARGUMENT = 2  # The argument contains unknown characters
        PORT_NOT_AVAILABLE = 3  # Port not available
        LOCAL_ERROR = 4  # Access denied, check the local / remote switch
        RANGE_ERROR = 5  # The argument is out of the allowed range
        REF_ERROR = 6  # Access denied, Ext Ref or BH-15 active
        ERROR_PENDING = 7  # DC command denied, there is still an error pending
        CYCLE_ERROR = 8  # Access denied, cycle is active
        DC_ERROR = 9  # Access denied, DC power is off

    def check_errors(self):
        """ Read the error message from the instrument, by reading the echo after a write command
        """
        timeout = self.adapter.connection.timeout
        try:
            self.adapter.connection.timeout = 200
            message = self.read()
            error = self.check_response_for_error(message)
            self.adapter.connection.timeout = timeout
            return error
        except VisaIOError as exc:
            self.adapter.connection.timeout = timeout
            if not exc.error_code == VI_ERROR_TMO:
                raise exc

    @staticmethod
    def check_response_for_error(message):
        if isinstance(message, str) and message.startswith("E"):
            error_code = int(message[1:])
            error = BrukerBEC1.ERRORS(error_code)
            log.error(error)
            return error
        return

    @staticmethod
    def preprocess_reply(result):
        error = BrukerBEC1.check_response_for_error(result)
        if error:
            raise ConnectionError(f"Controller echoed with error: {error}.")

        # Remove space between sign and value
        if result.startswith("+ ") or result.startswith("- ") or result.startswith("* "):
            result = "".join(result.split(" ")).replace("*", "")

        return result

    remote_enabled = Instrument.measurement(
        "REM/",
        """ A xxx property that returns the local/remote state of the instrument.
        """,
        values={True: 1, False: 0},
        map_values=True,
        check_set_errors=True,
    )

    DC_power_enabled = Instrument.control(
        "DCP/", "DCP=%d",
        """ A bool property that controls whether the dc power is enabled. Can be set.
        """,
        values={True: 1, False: 0},
        map_values=True,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    current = Instrument.control(
        "CUR/", "CUR=%f",
        """ A float property that controls the output current in amps. Can be set
        """,
        values=CURRENT_RANGE,
        validator=strict_range,
        dynamic=True,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    polarity = Instrument.control(
        "POL/", "POL=%d",
        """ A string property that controls the polarity of the power supply. Valid values are
        "positive" and "negative". The property can also return "no reversal unit" and "unit busy".
        Can be set.
        """,
        values={"positive": 1, "negative": 2, "no reversal unit": 0, "unit busy": 3},
        map_values=True,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    output_current = Instrument.measurement(
        "CHN/",
        """ A property that returns the output current in amps.
        """,
        preprocess_reply=preprocess_reply,
    )

    output_voltage = Instrument.measurement(
        "VLT/",
        """ A property that returns the output voltage.
        """,
        preprocess_reply=preprocess_reply,
    )

    magnet_resistance = Instrument.measurement(
        "RES/",
        """ A property that returns the magnet resistance.
        """,
        preprocess_reply=preprocess_reply,
    )

    power_stage_temperature = Instrument.measurement(
        "TEM/",
        """ A property that returns the power stage temperature (in celsius), if installed.
        """,
        preprocess_reply=preprocess_reply,
    )

    passbank_dissipation = Instrument.measurement(
        "POW/",
        """ A property that returns the passbank power dissipation, if installed.
        """,
        preprocess_reply=preprocess_reply,
    )

    uce_voltage = Instrument.measurement(
        "UCE/",
        """ A property that returns the Uce voltage, if installed.
        """,
        preprocess_reply=preprocess_reply,
    )

    external_reference = Instrument.control(
        "EXT/", "EXT=%d",
        """ A string property that controls the reference source. Valid values are "internal",
        "external", and "BH-15". Can be set.
        """,
        values={"internal": 0, "external": 1, "BH-15": 2},
        map_values=True,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    def reset_error_message(self):
        """ Reset the error messages.
        """
        self.write("RST=0")
        self.check_errors()

    status = Instrument.control(
        "STA/", "STA=%d",
        """ A property that reads the information about the power supply's status. If set to 0, the
        command flow is reset.
        """,
        values=[0],
        validator=strict_discrete_set,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    def reset_command_flow(self):
        """ Reset the command flow.
        """
        self.status = 0

    cycle_state = Instrument.control(
        "CYC/", "CYC=%d",
        """ A string property that controls the cycle state. Valid values are "running", "stopped",
        and "interrupted". Can be set.
        """,
        values={"running": 1, "stopped": 0, "interrupted": 2},
        map_values=True,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    cycle_current_up = Instrument.control(
        "CCU/", "CCU=%f",
        """ A float property that controls the cycle current up (in amps). Can be set.
        """,
        values=CURRENT_RANGE,
        validator=strict_range,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    cycle_current_down = Instrument.control(
        "CCD/", "CCD=%f",
        """ A float property that controls the cycle current down (in amps). Can be set.
        """,
        values=CURRENT_RANGE,
        validator=strict_range,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    cycle_rate_up = Instrument.control(
        "RCU/", "RCU=%f",
        """ A float property that controls the cycle current up rate (in amps). Can be set.
        """,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    cycle_rate_down = Instrument.control(
        "RCD/", "RCD=%f",
        """ A float property that controls the cycle current down rate (in amps). Can be set.
        """,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    cycle_time_up = Instrument.control(
        "WCU/", "WCU=%d",
        """ A float property that controls the cycle time up (in seconds). Can be set.
        """,
        values=[0, 65536],
        validator=strict_range,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    cycle_time_up_remaining = Instrument.measurement(
        "TIU/",
        """ A float property that returns the remaining cycle time up (in seconds).
        """,
        preprocess_reply=preprocess_reply,
    )

    cycle_time_down = Instrument.control(
        "WCD/", "WCD=%d",
        """ A float property that controls the cycle time up (in seconds). Can be set.
        """,
        values=[0, 65536],
        validator=strict_range,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    cycle_time_down_remaining = Instrument.measurement(
        "TID/",
        """ A float property that returns the remaining cycle time up (in seconds).
        """,
        preprocess_reply=preprocess_reply,
    )

    number_of_cycles = Instrument.control(
        "WCD/", "WCD=%d",
        """ An int property that controls the number of cycles to perform. Valid values are between
        0 and 65536 cycles. Can be set.
        """,
        values=[0, 65536],
        validator=strict_range,
        check_set_errors=True,
        preprocess_reply=preprocess_reply,
    )

    number_of_cycles_remaining = Instrument.measurement(
        "TID/",
        """ An int property that returns the remaining number of cycles.
        """,
        preprocess_reply=preprocess_reply,
    )
