from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderSupportInfo:
    name: str
    support_email: str | None = None
    support_phone: str | None = None
    support_url: str | None = None


PROVIDER_REGISTRY: dict[str, ProviderSupportInfo] = {
    "converge ict": ProviderSupportInfo(
        name="Converge ICT",
        support_email="support@converge.com.ph",
        support_phone="1-800-1888-8388",
        support_url="https://www.converge.com.ph/support",
    ),
    "pldt": ProviderSupportInfo(
        name="PLDT",
        support_email="pldthomecare@pldt.com.ph",
        support_phone="171",
        support_url="https://pldthome.com/contact",
    ),
    "globe": ProviderSupportInfo(
        name="Globe Telecom",
        support_email="globe@customer.globe.com.ph",
        support_phone="211",
        support_url="https://www.globe.com.ph/help",
    ),
    "sky cable": ProviderSupportInfo(
        name="Sky Cable",
        support_email="mysky@sky.com.ph",
        support_phone="1-800-10-759-4759",
        support_url="https://www.mysky.com.ph/contact",
    ),
}


def lookup(provider_name: str | None) -> ProviderSupportInfo | None:
    """Return support info for the provider, or None if not in the registry.

    Matching is case-insensitive. A partial match is attempted when an exact
    normalised key is not found — e.g. "Converge" matches "converge ict".
    """
    if not provider_name or not provider_name.strip():
        return None

    normalised = provider_name.strip().lower()

    if normalised in PROVIDER_REGISTRY:
        return PROVIDER_REGISTRY[normalised]

    for key, info in PROVIDER_REGISTRY.items():
        if key in normalised or normalised in key:
            return info

    return None
