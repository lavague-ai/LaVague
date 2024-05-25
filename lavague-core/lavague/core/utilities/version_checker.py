import requests
import pkg_resources
import warnings

YELLOW = "\033[93m"
RESET = "\033[0m"


def compare_versions(version1, version2):
    v1 = list(map(int, version1.split(".")))
    v2 = list(map(int, version2.split(".")))

    while len(v1) < len(v2):
        v1.append(0)
    while len(v2) < len(v1):
        v2.append(0)

    for i in range(len(v1)):
        if v1[i] > v2[i]:
            return 1
        elif v1[i] < v2[i]:
            return -1

    return 0


def get_installed_version(dist_name, lookup_dirs=None):
    req = pkg_resources.Requirement.parse(dist_name)

    if lookup_dirs is None:
        working_set = pkg_resources.WorkingSet()
    else:
        working_set = pkg_resources.WorkingSet(lookup_dirs)

    dist = working_set.find(req)
    return dist.version if dist else None


def check_latest_version():
    package_version = get_installed_version("lavague-core")
    url = "https://pypi.org/pypi/lavague-core/json"
    response = requests.get(url)
    data = response.json()
    latest_version = data["info"]["version"]
    if compare_versions(package_version, latest_version) < 0:
        warnings.warn(
            YELLOW
            + f"You are using lavague-core version {package_version}, however version {latest_version} is "
            "available. You should consider upgrading via the "
            "'pip install --upgrade lavague-core' command." + RESET,
            UserWarning,
        )
