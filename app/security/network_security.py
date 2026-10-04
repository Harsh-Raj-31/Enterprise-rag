import ipaddress
import socket



def is_unsafe_ip(ip_address: str) -> bool:
    """
    Return True when an IP address should not be
    reachable by the enterprise Web Agent.
    """

    address = ipaddress.ip_address(ip_address)

    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )

def validate_hostname(hostname: str) -> None:
    """
    Resolve a hostname and reject it if any resolved
    address points to a private or otherwise unsafe network.
    """

    try:
        addresses = {
            result[4][0]
            for result in socket.getaddrinfo(
                hostname,
                None,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise ValueError(
            "Unable to resolve the target hostname."
        ) from exc

    if not addresses:
        raise ValueError(
            "Hostname did not resolve to an IP address."
        )

    for address in addresses:
        if is_unsafe_ip(address):
            raise ValueError(
                "Access to private or unsafe network "
                "addresses is blocked."
            )