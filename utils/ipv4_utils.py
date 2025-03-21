import random
import ipaddress
import os

def is_ipv4(ip):
    ip_type = check_ip_version(ip)
    if ip_type==4:
        return True
    else:
        return False

def is_ipv6(ip):
    ip_type = check_ip_version(ip)
    if ip_type==6:
        return True
    else:
        return False

def check_ip_version(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        if isinstance(ip_obj, ipaddress.IPv4Address):
            return 4
        elif isinstance(ip_obj, ipaddress.IPv6Address):
            return 6
    except ValueError:
        return 0

def is_valid_cidr(prefix):
    """
    Check if the given prefix is a valid CIDR format.

    :param prefix: The IP prefix in CIDR format (e.g., '192.168.1.0/24')
    :return: True if the prefix is a valid CIDR, False otherwise
    """
    try:
        # Try to create an ip_network object, which validates the CIDR format
        ipaddress.ip_network(prefix, strict=False)
        return True
    except ValueError:
        return False

def prefix_to_cidr(prefix):
    """
    Convert a simple IP prefix (e.g., '1.2.' or '1.2.3.') to a standard CIDR format.
    The function will assume a /24 subnet for a 3-part prefix (e.g., '1.2.3.') and a /16 subnet for a 2-part prefix (e.g., '1.2.').

    :param prefix: The IP prefix (e.g., '1.2.' or '1.2.3.')
    :return: The CIDR formatted prefix (e.g., '1.2.3.0/24' or '1.2.0.0/16')
    """
    if is_valid_cidr(prefix):
        return prefix
    else:
        parts = prefix.split('.')
        parts = [item for item in parts if item != '']
        # If the prefix has 3 parts, assume a /24 subnet (256 addresses)
        if len(parts) == 3:
            return f"{prefix}0/24"
        # If the prefix has 2 parts, assume a /16 subnet (65536 addresses)
        elif len(parts) == 2:
            return f"{prefix}0.0/16"
        # Handle cases where the prefix is already full (e.g., '1.2.3.4')
        elif len(parts) == 4:
            return f"{prefix}/32"
        else:
            raise ValueError("Invalid prefix format. The prefix must have 2, 3, or 4 parts.")

def load_used_ips(prefix=None, IP_STORAGE_FILE="./used_ips"):
    """Load previously generated IPs from a file and optionally count the ones under a given prefix"""
    if os.path.exists(IP_STORAGE_FILE):
        with open(IP_STORAGE_FILE, "r") as f:
            used_ips = set(f.read().splitlines())

        if prefix:
            # Create a network object for the given prefix
            network = ipaddress.ip_network(prefix_to_cidr(prefix), strict=False)
            # Filter and count IPs that fall under the prefix
            return [ip for ip in used_ips if ipaddress.ip_address(ip) in network]

        return used_ips
    return set()


def save_used_ips(ips, IP_STORAGE_FILE="./used_ips"):
    """Save newly generated IPs to the file."""
    with open(IP_STORAGE_FILE, "a") as f:
        f.writelines(ip + "\n" for ip in ips)


def generate_random_ipv4(prefix="172.20.20.", count=1, IP_STORAGE_FILE="./used_ips"):
    """
    Generate unique random IPv4 addresses with an optional prefix.

    :param prefix: The prefix of the IPv4 address (e.g., "192.168.1.", "10.0.").
    However, default value is '172.20.20.0/24' because it is container-lab's default prefix.
    :param count: Number of unique IPs to generate (default: 1).
    :return: A single IP string if count=1, or a list of IP strings if count > 1.
    """
    if count < 1:
        raise ValueError("Count must be at least 1.")

    used_ips = load_used_ips(prefix, IP_STORAGE_FILE=IP_STORAGE_FILE)
    generated_ips = set()  # Temporary set for this function call

    if prefix:
        # Ensure prefix does not have the last octet
        prefix_parts = prefix.split(".")
        prefix_parts = [item for item in prefix_parts if item != '']
        if len(prefix_parts) >= 4 or not prefix.endswith("."):
            raise ValueError("Invalid prefix format. Ensure it's in the form 'x.x.x.' or 'x.x.'.")

        # Count the missing octets
        missing_octets = 4 - prefix.count(".")
        max_possible_ips = 256 ** missing_octets

        if len(used_ips) + count > max_possible_ips:
            raise RuntimeError(f"Not enough available IPs in the subnet {prefix}!")

        while len(generated_ips) < count:
            random_parts = [str(random.randint(0, 255)) for _ in range(missing_octets)]
            ip = prefix + ".".join(random_parts) if missing_octets > 1 else prefix + random_parts[0]

            if ip not in used_ips and ip not in generated_ips:
                generated_ips.add(ip)
    else:
        # Generate fully random IPv4 addresses
        max_possible_ips = 256 ** 4
        if len(used_ips) + count > max_possible_ips:
            raise RuntimeError("Not enough available IPv4 addresses!")

        while len(generated_ips) < count:
            ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
            if ip not in used_ips and ip not in generated_ips:
                generated_ips.add(ip)

    # Save generated IPs and return the result
    save_used_ips(generated_ips, IP_STORAGE_FILE=IP_STORAGE_FILE)
    return list(generated_ips) if count > 1 else next(iter(generated_ips))


# Example usage
if __name__ == "__main__":
    print(generate_random_ipv4("10.0.0.", 256))  # Generate 5 unique IPs
