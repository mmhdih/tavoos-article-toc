#!/usr/bin/env python3
"""Publish only the reviewed TOC 1.0.0 artifact; repository runtime is never used."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

SLUG = "tavoos-article-toc"
VERSION = "1.0.0"
SVN_URL = "https://plugins.svn.wordpress.org/tavoos-article-toc/"
ZIP_URL = "https://wordpress.org/plugins/files/2026/10/10_14-35-14_tavoos-article-toc-1.0.0-prereview.zip"
ZIP_SHA256 = "7769d02900caaebc769ca1b8e55941ceb773dfa6865c5b8cba6881908d946f4d"
ASSET_COMMIT = "aea6b594f7692864d15adec7fc107cadbf49c6f8"
FILES = {
    "LICENSE.txt": "edaef632cbb643e4e7a221717a6c441a4c1a7c918e6e4d56debc3d8739b233f6",
    "assets/toc.css": "b2950b0fbb99f2cd0d844df0197be4a1818de9fe456af69f6ea62c68a71d1aad",
    "assets/toc.js": "e2557e1c58dc179549555ffd7d8c4dd12c18c8b4957d81b1ca33c5fb3a347037",
    "includes/class-plugin.php": "ea5aa6ef84a44fb5c6ce141fa0a3d0450fffb6de57ff15ef085fc5bbbeebfa9a",
    "languages/tavoos-article-toc.pot": "481857dd57420c3def94422e13ceccf8dace12d687fc2dea56edb330178202f7",
    "readme.txt": "3b539bbba260a6f46ab61a788b92050d00079b2194c44614e5c4b51fcb46fda1",
    "tavoos-article-toc.php": "536b971e8f4844da611a61814d404787214a8a8b61002f8c4e69ef201ae16ec5",
    "uninstall.php": "ac4181a05f56f24d714471be4df51c4d293c2461a7eea41986fabb42ff14ef70",
}
# Git object identities returned by GitHub for the existing directory artwork.
ASSETS = {
    "banner-1544x500.png": "c86766a6cc6e5ed10f168d022d5a5d67b5e7737f",
    "banner-772x250.png": "ba4b79ec074f2e6a509002565f0bce43480fd457",
    "icon-128x128.png": "7f108b341bc3eeecafa5c12a29a723f20ed3422b",
    "icon-256x256.png": "239b5221a1f4c2e77679ada073ec0b18f52cef78",
    "screenshot-1.png": "389cfcb8122fa684ebeb3ddb23219ae9de99f67d",
    "screenshot-2.png": "372a7a880cfb26c3bdeffd63894f9ca5427fadcf",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(*args):
    child_env = {k: v for k, v in os.environ.items() if k not in {"SVN_USERNAME", "SVN_PASSWORD"}}
    result = subprocess.run(args, text=True, capture_output=True, env=child_env)
    if result.returncode:
        detail = (result.stdout + result.stderr).strip()
        password = os.environ.get("SVN_PASSWORD", "")
        if password:
            detail = detail.replace(password, "[REDACTED]")
        raise RuntimeError(f"{args[0]} failed ({result.returncode}): {detail}")
    return result.stdout


def download(url, destination):
    with urllib.request.urlopen(url, timeout=90) as response:
        require(response.geturl().startswith("https://"), "Insecure download redirect")
        data = response.read(5_000_001)
    require(len(data) <= 5_000_000, "Unexpected download size")
    destination.write_bytes(data)


def file_map(root):
    require(root.is_dir(), f"Missing directory: {root.name}")
    result = {}
    for path in root.rglob("*"):
        require(not path.is_symlink(), "Symlinks are not allowed")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def verify_package(root):
    actual = file_map(root)
    require(set(actual) == set(FILES), "Runtime file list differs from approved release")
    for name, digest in FILES.items():
        require(hashlib.sha256(actual[name]).hexdigest() == digest, f"Runtime mismatch: {name}")
    header = actual[SLUG + ".php"].decode()
    readme = actual["readme.txt"].decode()
    require(re.search(r"^ \* Version: 1\.0\.0$", header, re.M), "Incorrect plugin version")
    require("define( 'TAVOOS_ARTICLE_TOC_VERSION', '1.0.0' );" in header, "Incorrect version constant")
    require(re.search(r"^Stable tag: 1\.0\.0$", readme, re.M), "Incorrect stable tag")
    require("License: GPL-2.0-or-later" in header and "License: GPL-2.0-or-later" in readme, "License mismatch")
    require(b"GNU GENERAL PUBLIC LICENSE" in actual["LICENSE.txt"], "Missing GPL license")
    require(not any(b"load_plugin_textdomain" in value for value in actual.values()), "Reviewer correction missing")


def verify_assets(root):
    actual = file_map(root)
    require(set(actual) == set(ASSETS), "Directory artwork file list differs")
    for name, digest in ASSETS.items():
        data = actual[name]
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        require(hashlib.sha1(blob).hexdigest() == digest, f"Artwork mismatch: {name}")
        require(data.startswith(b"\x89PNG\r\n\x1a\n"), "Artwork is not PNG")


def extract_approved(archive, destination):
    require(archive.stat().st_size == 19373, "Approved ZIP size differs")
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == ZIP_SHA256, "Approved ZIP checksum differs")
    with zipfile.ZipFile(archive) as source:
        names = source.namelist()
        expected = {SLUG + "/" + name for name in FILES}
        require(len(names) == len(expected) and set(names) == expected, "Unexpected ZIP entries")
        require(source.testzip() is None, "ZIP integrity check failed")
        for info in source.infolist():
            path = PurePosixPath(info.filename)
            require(not path.is_absolute() and ".." not in path.parts, "Unsafe ZIP path")
            require(not stat.S_ISLNK(info.external_attr >> 16), "ZIP symlinks are forbidden")
            target = destination.joinpath(*path.parts[1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read(info))
    verify_package(destination)


def verify_wc(wc):
    verify_package(wc / "trunk")
    verify_package(wc / "tags" / VERSION)
    verify_assets(wc / "assets")
    require({p.name for p in (wc / "tags").iterdir()} == {VERSION}, "Unexpected SVN release tags")
    status = ET.fromstring(run("svn", "status", "--xml", "--no-ignore", "--show-updates", "--non-interactive", str(wc)))
    for entry in status.findall(".//entry"):
        item = entry.find("wc-status")
        require(item is not None and item.get("item") in {"added", "normal", "none"}, "Unexpected SVN working-copy changes")
        require(item.get("tree-conflicted") != "true" and item.get("props") in {"none", "normal"}, "SVN conflict or unexpected properties")
        remote = entry.find("repos-status")
        require(remote is None or (remote.get("item") == "none" and remote.get("props") in {"none", "normal"}), "SVN changed remotely; stop and inspect")


def prepare(work):
    require(not work.exists(), "Release work directory must be fresh")
    work.mkdir(parents=True)
    archive = work / "approved.zip"
    download(ZIP_URL, archive)
    package = work / "package"
    extract_approved(archive, package)
    for name in FILES:
        if name.endswith(".php"):
            print(run("php", "-l", str(package / name)).strip())
    run("node", "--check", str(package / "assets/toc.js"))
    assets = work / "artwork"
    assets.mkdir()
    for name in ASSETS:
        download(f"https://raw.githubusercontent.com/mmhdih/{SLUG}/{ASSET_COMMIT}/wordpress-org/{name}", assets / name)
    verify_assets(assets)
    wc = work / "svn"
    run("svn", "checkout", "--non-interactive", SVN_URL, str(wc))
    require({p.name for p in wc.iterdir()} == {".svn", "trunk", "tags", "assets"}, "Unexpected SVN repository layout")
    empty = all(not any((wc / folder).iterdir()) for folder in ("trunk", "tags", "assets"))
    if empty:
        shutil.copytree(package, wc / "trunk", dirs_exist_ok=True)
        shutil.copytree(assets, wc / "assets", dirs_exist_ok=True)
        run("svn", "add", "--force", "--no-ignore", str(wc / "trunk"), str(wc / "assets"))
        run("svn", "copy", str(wc / "trunk"), str(wc / "tags" / VERSION))
    else:
        print("Existing SVN content found; proceeding only if all bytes already match this approved release.")
    verify_wc(wc)
    print(run("svn", "status", "--no-ignore", str(wc)))
    print("Approved ZIP, PHP/JS syntax, directory artwork and staged SVN content verified.")


def publish(work):
    wc = work / "svn"
    verify_wc(wc)
    if not run("svn", "status", "--no-ignore", str(wc)).strip():
        print("Exact approved release is already present; no commit or authentication needed.")
        return
    username = os.environ.get("SVN_USERNAME", "")
    password = os.environ.get("SVN_PASSWORD", "")
    require(username == "mmhdih", "Existing SVN_USERNAME secret must identify the approved mmhdih account")
    require(bool(password), "Existing SVN_PASSWORD repository secret is missing; configure it securely before publishing")
    child_env = {k: v for k, v in os.environ.items() if k not in {"SVN_USERNAME", "SVN_PASSWORD"}}
    result = subprocess.run(
        ["svn", "commit", str(wc), "--username", username, "--password-from-stdin", "--non-interactive", "--no-auth-cache", "-m", "Publish approved Tavoos Article TOC 1.0.0"],
        input=password + "\n", text=True, capture_output=True, env=child_env,
    )
    output = (result.stdout + result.stderr).replace(password, "[REDACTED]")
    print(output)
    require(result.returncode == 0, "SVN commit failed; inspect the sanitized error before retrying")


def verify_remote(work):
    log = ET.fromstring(run("svn", "log", "--xml", "--limit", "1", "--non-interactive", SVN_URL))
    latest = log.find("logentry")
    require(latest is not None and latest.get("revision", "").isdigit(), "Cannot verify the SVN revision")
    revision = latest.get("revision")
    for remote, local in (("trunk", "remote-trunk"), ("tags/" + VERSION, "remote-tag"), ("assets", "remote-assets")):
        destination = work / local
        run("svn", "export", "--non-interactive", "-r", revision, SVN_URL + remote, str(destination))
        (verify_assets if remote == "assets" else verify_package)(destination)
    summary = f"Verified SVN revision {revision}: trunk and tags/1.0.0 exactly match the approved eight-file package; directory artwork verified.\n\nPublic directory indexing/download availability must still be verified separately.\n\nhttps://wordpress.org/plugins/tavoos-article-toc/\n"
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as target:
            target.write(summary)


if __name__ == "__main__":
    require(len(sys.argv) == 3, "Usage: publish-approved-wordpress-1.0.0.py prepare|publish|verify-remote WORKDIR")
    command = {"prepare": prepare, "publish": publish, "verify-remote": verify_remote}.get(sys.argv[1])
    require(command is not None, "Unknown command")
    command(Path(sys.argv[2]).resolve())
