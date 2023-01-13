class ChannelFunctionError(Exception):
    """Dummy exception class for channel function errors."""
    pass


class MissingArgsError(ChannelFunctionError):
    """Exception raised when the user calls an IRC command without the required
    number of arguments."""
    def __init__(self, correct_syntax):
        message = f"Missing arguments. Correct usage is: {correct_syntax}"
        super().__init__(message)


