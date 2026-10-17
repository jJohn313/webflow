#!/usr/bin/env python3
"""
webflow vault - Sovereign Credential Engine for Webflow
Backends: FreeDesktop Secret Service (libsecret / GNOME Keyring) with local encrypted/protected metadata registry.
"""
import os
import sys
import json
import time
import secrets
import string
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, List, Dict

try:
    import gi
    gi.require_version("Secret", "1")
    from gi.repository import Secret
    HAS_LIBSECRET = True
except Exception:
    HAS_LIBSECRET = False


def extract_domain_parts(url_or_domain: str) -> Tuple[str, str]:
    """Returns (exact_host, root_domain)."""
    raw = url_or_domain.strip()
    if "://" in raw:
        netloc = urllib.parse.urlparse(raw).netloc.split(":")[0].lower()
    else:
        netloc = raw.split("/")[0].split(":")[0].lower()
    
    if not netloc:
        return "local", "local"
        
    parts = netloc.split(".")
    root = netloc
    if len(parts) >= 2:
        if len(parts) >= 3 and len(parts[-2]) <= 3 and len(parts[-1]) == 2:
            root = ".".join(parts[-3:])
        else:
            root = ".".join(parts[-2:])
    return netloc, root


class WebflowVault:
    def __init__(self):
        self.base_share = Path.home() / ".local" / "share" / "webflow"
        self.base_share.mkdir(parents=True, exist_ok=True)
        self.meta_file = self.base_share / "vault_meta.json"
        self.fallback_file = self.base_share / "vault_fallback.json"
        
        self.schema = None
        if HAS_LIBSECRET:
            try:
                self.schema = Secret.Schema.new(
                    "org.webflow.Password",
                    Secret.SchemaFlags.NONE,
                    {
                        "domain": Secret.SchemaAttributeType.STRING,
                        "username": Secret.SchemaAttributeType.STRING,
                    }
                )
            except Exception:
                self.schema = None

        self._ensure_meta()

    def _ensure_meta(self):
        if not self.meta_file.exists():
            data = {"accounts": [], "ignored_domains": []}
            self._write_meta(data)

    def _read_meta(self) -> dict:
        try:
            if self.meta_file.exists():
                return json.loads(self.meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"accounts": [], "ignored_domains": []}

    def _write_meta(self, data: dict):
        try:
            self.meta_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.meta_file.chmod(0o600)
        except Exception:
            pass

    def _read_fallback(self) -> dict:
        try:
            if self.fallback_file.exists():
                return json.loads(self.fallback_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _write_fallback(self, data: dict):
        try:
            self.fallback_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.fallback_file.chmod(0o600)
        except Exception:
            pass

    def is_domain_ignored(self, domain_or_url: str) -> bool:
        netloc, root = extract_domain_parts(domain_or_url)
        meta = self._read_meta()
        ignored = meta.get("ignored_domains", [])
        return netloc in ignored or root in ignored

    def ignore_domain(self, domain_or_url: str):
        _, root = extract_domain_parts(domain_or_url)
        meta = self._read_meta()
        ignored = meta.get("ignored_domains", [])
        if root not in ignored:
            ignored.append(root)
            meta["ignored_domains"] = ignored
            self._write_meta(meta)

    def unignore_domain(self, domain_or_url: str):
        netloc, root = extract_domain_parts(domain_or_url)
        meta = self._read_meta()
        ignored = [d for d in meta.get("ignored_domains", []) if d not in (netloc, root)]
        meta["ignored_domains"] = ignored
        self._write_meta(meta)

    def save_credentials(self, domain_or_url: str, username: str, password: str) -> bool:
        """Stores credentials securely into FreeDesktop Secret Service and local registry."""
        if not username or not password:
            return False

        netloc, root = extract_domain_parts(domain_or_url)
        target_domain = root if root else netloc
        success = False

        if HAS_LIBSECRET and self.schema:
            try:
                attrs = {"domain": target_domain, "username": username}
                label = f"Webflow: {target_domain} ({username})"
                success = Secret.password_store_sync(
                    self.schema,
                    attrs,
                    Secret.COLLECTION_DEFAULT,
                    label,
                    password,
                    None
                )
            except Exception as e:
                success = False

        # Always update local fallback store (protected with chmod 0600)
        fb = self._read_fallback()
        key = f"{target_domain}::{username}"
        fb[key] = {
            "domain": target_domain,
            "username": username,
            "password": password,
            "updated_at": int(time.time())
        }
        self._write_fallback(fb)

        # Update metadata index
        meta = self._read_meta()
        accounts = meta.get("accounts", [])
        updated = False
        now = int(time.time())
        for acc in accounts:
            if acc.get("domain") == target_domain and acc.get("username") == username:
                acc["updated_at"] = now
                updated = True
                break
        if not updated:
            accounts.append({
                "domain": target_domain,
                "username": username,
                "updated_at": now
            })
        meta["accounts"] = accounts
        # If user explicitly saves, unignore
        meta["ignored_domains"] = [d for d in meta.get("ignored_domains", []) if d != target_domain]
        self._write_meta(meta)
        return True

    def get_credentials(self, domain_or_url: str) -> Optional[Tuple[str, str]]:
        """
        Retrieves primary (username, password) for the domain.
        Checks exact host first, then root domain.
        """
        netloc, root = extract_domain_parts(domain_or_url)
        for d in (netloc, root):
            creds = self.get_all_for_domain(d)
            if creds:
                # Return the most recently updated
                return creds[0]["username"], creds[0]["password"]
        return None

    def get_all_for_domain(self, domain_or_url: str) -> List[Dict[str, str]]:
        """Returns all saved credentials for this domain."""
        netloc, root = extract_domain_parts(domain_or_url)
        domains_to_check = list(dict.fromkeys([netloc, root]))
        
        results = []
        meta = self._read_meta()
        matching_accounts = [
            a for a in meta.get("accounts", [])
            if a.get("domain") in domains_to_check
        ]
        # Sort by updated_at descending
        matching_accounts.sort(key=lambda x: x.get("updated_at", 0), reverse=True)

        for acc in matching_accounts:
            dom = acc["domain"]
            u = acc["username"]
            pwd = self._lookup_secret(dom, u)
            if pwd is not None:
                results.append({
                    "domain": dom,
                    "username": u,
                    "password": pwd,
                    "updated_at": acc.get("updated_at", 0)
                })

        # If meta index had nothing, check direct secret service search
        if not results and HAS_LIBSECRET and self.schema:
            for d in domains_to_check:
                try:
                    items = Secret.password_search_sync(
                        self.schema,
                        {"domain": d},
                        Secret.SearchFlags.ALL | Secret.SearchFlags.UNLOCK,
                        None
                    )
                    for item in items:
                        attrs = item.get_attributes()
                        u = attrs.get("username", "")
                        pwd = item.retrieve_secret_sync(None).get_text()
                        if u and pwd:
                            results.append({
                                "domain": d,
                                "username": u,
                                "password": pwd,
                                "updated_at": int(time.time())
                            })
                except Exception:
                    pass

        return results

    def _lookup_secret(self, domain: str, username: str) -> Optional[str]:
        if HAS_LIBSECRET and self.schema:
            try:
                pwd = Secret.password_lookup_sync(
                    self.schema,
                    {"domain": domain, "username": username},
                    None
                )
                if pwd:
                    return pwd
            except Exception:
                pass
        
        # Check fallback
        fb = self._read_fallback()
        key = f"{domain}::{username}"
        if key in fb:
            return fb[key].get("password")
        return None

    def delete_credentials(self, domain_or_url: str, username: Optional[str] = None) -> bool:
        netloc, root = extract_domain_parts(domain_or_url)
        domains = [netloc, root]

        if HAS_LIBSECRET and self.schema:
            for d in domains:
                try:
                    attrs = {"domain": d}
                    if username:
                        attrs["username"] = username
                    Secret.password_clear_sync(self.schema, attrs, None)
                except Exception:
                    pass

        meta = self._read_meta()
        if username:
            meta["accounts"] = [
                a for a in meta.get("accounts", [])
                if not (a.get("domain") in domains and a.get("username") == username)
            ]
        else:
            meta["accounts"] = [
                a for a in meta.get("accounts", [])
                if a.get("domain") not in domains
            ]
        self._write_meta(meta)

        fb = self._read_fallback()
        keys_to_del = [
            k for k in fb.keys()
            if any(k.startswith(f"{d}::") for d in domains) and (not username or k.endswith(f"::{username}"))
        ]
        for k in keys_to_del:
            del fb[k]
        self._write_fallback(fb)
        return True

    def list_accounts(self) -> List[Dict]:
        meta = self._read_meta()
        accounts = list(meta.get("accounts", []))
        accounts.sort(key=lambda x: (x.get("domain", ""), x.get("username", "")))
        return accounts

    @staticmethod
    def generate_password(length: int = 24) -> str:
        """Generates a cryptographically strong sovereign password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}<>"
        while True:
            pwd = "".join(secrets.choice(alphabet) for _ in range(length))
            if (any(c.islower() for c in pwd)
                    and any(c.isupper() for c in pwd)
                    and any(c.isdigit() for c in pwd)
                    and any(c in "!@#$%^&*()-_=+[]{}<>" for c in pwd)):
                return pwd
