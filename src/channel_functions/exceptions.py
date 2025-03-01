class ChannelFunctionError(Exception):
    """Dummy exception class for channel function errors."""
    pass


class MissingArgsError(ChannelFunctionError):
    """Exception raised when the user calls an IRC command without the required
    number of arguments."""
    def __init__(self, correct_syntax):
        message = f"Missing arguments. Correct usage is: {correct_syntax}"
        super().__init__(message)


class InvalidQuery(ChannelFunctionError):
    """User failed to provide anything to query"""
    def __init__(self, key_map):
        leagues = ', '.join(key_map.keys())
        message = f"To use the sportsbook function, try: .sb [league] [city or team name]. Valid leagues are {leagues}."
        super().__init__(message)


class BadStatusCode(ChannelFunctionError):
    """Failed to pull data from Odds API"""
    def __init__(self, code):
        message = f"Failed to fetch odds: status code {code}."
        super().__init__(message)


class NoOddsFound(ChannelFunctionError):
    """Could not find any odds in the response JSON"""
    def __init__(self):
        message = "The API returned no data. Try again later."
        super().__init__(message)


class NoGameFound(ChannelFunctionError):
    """Could not find odds for the queried team"""
    def __init__(self):
        message = "The API has no matchup for that city or team name."
        super().__init__(message)


class NoGameOddsFound(ChannelFunctionError):
    """Could not find odds for the queried team"""
    def __init__(self):
        message = "The API returned this matchup with no odds. ¯\_(ツ)_/¯"
        super().__init__(message)


