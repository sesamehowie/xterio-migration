CH_OS_LIST = [
    "Android",
    "Chrome OS",
    "Chromium OS",
    "iOS",
    "Linux",
    "macOS",
    "Windows",
    "Unknown",
]


def get_platform(user_agent):
    for os_name in CH_OS_LIST:
        if os_name in user_agent:
            return os_name
    return "Windows"
