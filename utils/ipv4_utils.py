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


def assign_ip_from_as(asn, iface_id):
    high = asn // 256
    low = asn % 256
    return f"10.{high}.{low}.{iface_id}/32"


def safe_next_ip(ip_str):
    ip = ipaddress.ip_address(ip_str)
    try:
        return str(ip + 1)
    except ValueError:
        return None  # 已经是最大地址了


def safe_prev_ip(ip_str):
    ip = ipaddress.ip_address(ip_str)
    try:
        return str(ip - 1)
    except ValueError:
        return None  # 已经是最小地址了


def is_valid_cidr(prefix):
    """
    Check if the given prefix is a valid CIDR format.

    :param prefix: The IP prefix in CIDR format (e.g., '192.168.1.0/24')
    :return: True if the prefix is a valid CIDR, False otherwise
    """
    try:
        # Try to create an ip_network object, which validates the CIDR format
        ipaddress.ip_network(prefix, strict=True)
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
        # If the prefix has 2 parts, assume a /16 subnet (65536 addresses)
        if len(parts) == 1:
            return f"{prefix}0.0.0/8"
        elif len(parts) == 2:
            return f"{prefix}0.0/16"
        # If the prefix has 3 parts, assume a /24 subnet (256 addresses)
        elif len(parts) == 3:
            return f"{prefix}0/24"
        # Handle cases where the prefix is already full (e.g., '1.2.3.4')
        elif len(parts) == 4:
            return f"{prefix}/32"
        else:
            raise ValueError("Invalid prefix format.")


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


# def generate_random_ipv4(prefix="172.20.20.", count=1, IP_STORAGE_FILE="./used_ips"):
#     """
#     Generate unique random IPv4 addresses with an optional prefix.
#
#     :param prefix: The prefix of the IPv4 address (e.g., "192.168.1.", "10.0.").
#     However, default value is '172.20.20.0/24' because it is container-lab's default prefix.
#     :param count: Number of unique IPs to generate (default: 1).
#     :return: A single IP string if count=1, or a list of IP strings if count > 1.
#     """
#     if count < 1:
#         raise ValueError("Count must be at least 1.")
#
#     used_ips = load_used_ips(prefix, IP_STORAGE_FILE=IP_STORAGE_FILE)
#     generated_ips = set()  # Temporary set for this function call
#
#     if prefix:
#         # Ensure prefix does not have the last octet
#         prefix_parts = prefix.split(".")
#         prefix_parts = [item for item in prefix_parts if item != '']
#         if len(prefix_parts) >= 4 or not prefix.endswith("."):
#             raise ValueError("Invalid prefix format. Ensure it's in the form 'x.x.x.' or 'x.x.'")
#
#         # Count the missing octets
#         missing_octets = 4 - prefix.count(".")
#         max_possible_ips = 256 ** missing_octets
#
#         if len(used_ips) + count > max_possible_ips:
#             raise RuntimeError(f"Not enough available IPs in the subnet {prefix}!")
#
#         while len(generated_ips) < count:
#             random_parts = [str(random.randint(0, 255)) for _ in range(missing_octets)]
#             ip = prefix + ".".join(random_parts) if missing_octets > 1 else prefix + random_parts[0]
#
#             if ip not in used_ips and ip not in generated_ips:
#                 generated_ips.add(ip)
#     else:
#         # Generate fully random IPv4 addresses
#         max_possible_ips = 256 ** 4
#         if len(used_ips) + count > max_possible_ips:
#             raise RuntimeError("Not enough available IPv4 addresses!")
#
#         while len(generated_ips) < count:
#             ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
#             if ip not in used_ips and ip not in generated_ips:
#                 generated_ips.add(ip)
#
#     # Save generated IPs and return the result
#     save_used_ips(generated_ips, IP_STORAGE_FILE=IP_STORAGE_FILE)
#     return list(generated_ips) if count > 1 else next(iter(generated_ips))


def generate_random_ipv4(prefix="172.20.20.0/24", count=1, IP_STORAGE_FILE="./used_ips"):
    """
    Generate unique random IPv4 addresses within a CIDR subnet with improved performance.

    :param prefix: CIDR notation of the subnet (e.g., "192.168.1.0/24", "10.0.0.0/8").
    :param count: Number of unique IPs to generate (default: 1).
    :param IP_STORAGE_FILE: File to store used IP addresses.
    :return: A single IP string if count=1, or a list of IP strings if count > 1.
    """
    if count < 1:
        raise ValueError("Count must be at least 1.")

    # Parse the CIDR prefix
    try:
        network = ipaddress.IPv4Network(prefix, strict=True)
    except ValueError:
        raise ValueError(f"Invalid CIDR prefix format: {prefix}. Use format like '192.168.1.0/24'")

    # Calculate network parameters
    start_int = int(network.network_address)
    if network.prefixlen < 31:
        # Exclude network and broadcast addresses for normal networks
        start_int += 1
        end_int = int(network.broadcast_address) - 1
    else:
        # For /31 and /32, all addresses are usable
        end_int = int(network.broadcast_address)

    max_possible_ips = end_int - start_int + 1

    # Load previously used IPs (more efficiently)
    used_ips = set()
    if os.path.exists(IP_STORAGE_FILE):
        network_str = str(network)
        with open(IP_STORAGE_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(network_str):
                    ip_parts = line.split()
                    if len(ip_parts) > 1:
                        used_ips.add(ip_parts[1])  # Store just the IP string

    # Check if there are enough available IPs
    if len(used_ips) + count > max_possible_ips:
        raise RuntimeError(f"Not enough available IPs in the subnet {prefix}! "
                           f"Available: {max_possible_ips - len(used_ips)}, Requested: {count}")

    # Generate unique IPs more efficiently
    generated_ips = set()
    attempts = 0
    max_attempts = count * 10  # Safety limit to prevent infinite loops

    while len(generated_ips) < count and attempts < max_attempts:
        attempts += 1
        # Generate a random integer between start and end
        random_int = random.randint(start_int, end_int)
        ip = str(ipaddress.IPv4Address(random_int))

        if ip not in used_ips and ip not in generated_ips:
            generated_ips.add(ip)

    if len(generated_ips) < count:
        # If we couldn't generate enough IPs randomly, try sequential allocation as fallback
        # Todo: im not sure if this will meet error when generating large amount of /30 ips.
        current_int = start_int
        while len(generated_ips) < count and current_int <= end_int:
            ip = str(ipaddress.IPv4Address(current_int))
            if ip not in used_ips and ip not in generated_ips:
                generated_ips.add(ip)
            current_int += 1

    return list(generated_ips) if count > 1 else next(iter(generated_ips))

def generate_random_ipv4_with_save(prefix="172.20.20.0/24", count=1, IP_STORAGE_FILE="./used_ips"):
    generated_ips = generate_random_ipv4(prefix=prefix, count=count, IP_STORAGE_FILE=IP_STORAGE_FILE)
    save_used_ips(generated_ips, IP_STORAGE_FILE)
    return generated_ips


def generate_p2p_ip_pairs(IP_STORAGE_FILE="./used_ips"):
    used_ips = load_used_ips(IP_STORAGE_FILE)

    while True:
        net_addr = generate_random_ipv4("10.0.0.0/8", count=1, IP_STORAGE_FILE=IP_STORAGE_FILE)
        if not is_valid_cidr(net_addr + "/31"):
            continue

        first_ip = net_addr
        second_ip = safe_next_ip(net_addr)

        if first_ip in used_ips or second_ip in used_ips:
            continue

        save_used_ips( [first_ip, second_ip], IP_STORAGE_FILE)
        return first_ip, second_ip

# Example usage
if __name__ == "__main__":
    print(is_valid_cidr("192.168.1.254/31"))  # Generate 5 unique IPs
