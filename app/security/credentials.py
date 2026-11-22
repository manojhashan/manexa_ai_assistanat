"""Windows Credential Manager only: never silently fall back to plaintext storage."""

import sys
from collections.abc import Callable


class CredentialError(RuntimeError):
    pass


class CredentialVault:
    def __init__(self, backend_factory: Callable | None = None):
        self._factory = backend_factory

    def _backend(self):
        if self._factory:
            return self._factory()
        if sys.platform != "win32":
            raise CredentialError("Saving API keys requires Windows Credential Manager.")
        try:
            from keyring.backends.Windows import WinVaultKeyring

            return WinVaultKeyring()
        except Exception as exc:
            raise CredentialError("Windows Credential Manager is unavailable.") from exc

    @staticmethod
    def _account(provider: str, endpoint: str) -> str:
        # Scoping to the endpoint prevents a custom URL from inheriting another server's key.
        return f"{provider}:{endpoint.rstrip('/')}"

    def get(self, provider: str, endpoint: str) -> str:
        try:
            return (
                self._backend().get_password("MANEXA AI", self._account(provider, endpoint)) or ""
            )
        except CredentialError:
            raise
        except Exception as exc:
            raise CredentialError("The API key could not be read from Credential Manager.") from exc

    def set(self, provider: str, endpoint: str, value: str) -> None:
        if not value.strip():
            raise CredentialError("Enter a non-empty API key.")
        try:
            self._backend().set_password("MANEXA AI", self._account(provider, endpoint), value)
        except CredentialError:
            raise
        except Exception as exc:
            raise CredentialError("The API key could not be saved to Credential Manager.") from exc

    def delete(self, provider: str, endpoint: str) -> None:
        try:
            backend = self._backend()
            account = self._account(provider, endpoint)
            if backend.get_password("MANEXA AI", account):
                backend.delete_password("MANEXA AI", account)
        except CredentialError:
            raise
        except Exception as exc:
            raise CredentialError(
                "The API key could not be removed from Credential Manager."
            ) from exc
