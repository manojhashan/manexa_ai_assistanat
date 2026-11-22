import pytest

from app.core.state import HeadPose
from app.security.credentials import CredentialError, CredentialVault


class MemoryVault:
    """Test double; the production vault explicitly instantiates WinVaultKeyring."""

    def __init__(self):
        self.values = {}

    def get_password(self, service, account):
        return self.values.get((service, account))

    def set_password(self, service, account, value):
        self.values[service, account] = value

    def delete_password(self, service, account):
        del self.values[service, account]


def test_keys_are_scoped_to_provider_and_endpoint():
    backend = MemoryVault()
    vault = CredentialVault(lambda: backend)
    vault.set("custom", "https://first.example/v1", "credential")
    assert vault.get("custom", "https://first.example/v1") == "credential"
    assert vault.get("custom", "https://second.example/v1") == ""
    vault.delete("custom", "https://first.example/v1")
    assert vault.get("custom", "https://first.example/v1") == ""


def test_no_plaintext_fallback_on_credential_failure():
    def broken():
        raise RuntimeError("private detail")

    vault = CredentialVault(broken)
    with pytest.raises(CredentialError, match="could not be saved") as error:
        vault.set("openai", "https://api.openai.com/v1", "never-log-this")
    assert "never-log-this" not in str(error.value)


def test_pose_is_bounded_and_nan_is_rejected():
    assert HeadPose(yaw=100, pitch=-100).to_dict() == {"yaw": 0.6, "pitch": -0.4}
    with pytest.raises(ValueError):
        HeadPose(yaw=float("nan")).to_dict()
