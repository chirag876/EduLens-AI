from fastapi import Header
from user_agents import parse


async def get_user_agent(user_agent: str = Header(None)):
    """
    Asynchronously gets the user agent details, including the operating system, device, and browser.
    The user agent information is captured along with the access token generation, allowing the tracking of the token's origin.
    To revoke a user's access later from their profile, you could implement a functionality to delete the access token and the related refresh token.
    This would render all previously generated access tokens and refresh tokens invalid, since they were generated from the now-revoked refresh token.

    Args:
        user_agent (str, optional): The user agent string to parse. Defaults to None.

    Returns:
        dict: A dictionary containing the user agent details, including the operating system, device, and browser.
    """
    agent_details = parse(user_agent)
    return {'os': agent_details.os.family, 'device': f'{agent_details.device.brand}:{agent_details.device.model}', 'browser': f'{agent_details.browser.family}:{agent_details.browser.version_string}'}
