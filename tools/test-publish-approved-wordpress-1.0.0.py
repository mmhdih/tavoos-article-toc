"""Exercise the release working-copy guards with a local-only SVN repository."""
import hashlib
import importlib.util
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("release_helper", HERE / "publish-approved-wordpress-1.0.0.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

def rejected(call, expected):
    try:
        call()
    except RuntimeError as error:
        assert expected in str(error), str(error)
    else:
        raise AssertionError("Unsafe working copy was accepted")

with tempfile.TemporaryDirectory(prefix="tavoos-svn-guard-test-") as folder:
    root = Path(folder)
    repository = root / "repository"
    command("svnadmin", "create", str(repository))
    url = repository.as_uri()
    command("svn", "mkdir", url + "/trunk", url + "/tags", url + "/assets", "-m", "Create local test layout")
    wc = root / "wc"
    command("svn", "checkout", url, str(wc))

    # Small local runtime fixture: approved-package checks are separate from this SVN-property regression.
    payload = b"<?php // local guard-test fixture\n"
    (wc / "trunk" / "fixture.php").write_bytes(payload)
    def fixture_package(path):
        release.require(release.file_map(path) == {"fixture.php": payload}, "Fixture runtime differs")
    release.verify_package = fixture_package
    png = (HERE.parent / "wordpress-org" / "icon-128x128.png").read_bytes()
    blob = b"blob " + str(len(png)).encode() + b"\0" + png
    release.ASSETS = {"icon-128x128.png": hashlib.sha1(blob).hexdigest()}
    image = wc / "assets" / "icon-128x128.png"
    image.write_bytes(png)
    command("svn", "add", "--force", "--no-ignore", "--no-auto-props", str(wc / "trunk"), str(wc / "assets"))
    detected = command("svn", "propget", "svn:mime-type", str(image)).strip()
    print("Actual SVN binary auto-detection MIME type:", detected)
    assert detected in {"application/octet-stream", "image/png"}
    status = release.ET.fromstring(command("svn", "status", "--xml", str(image)))
    item = status.find(".//wc-status")
    assert item.get("item") == "added" and item.get("props") == "modified", "Binary-property regression was not reproduced"

    command("svn", "propset", "svn:mime-type", "image/png", str(image))
    command("svn", "copy", str(wc / "trunk"), str(wc / "tags" / release.VERSION))
    release.verify_wc(wc)
    print("PASS: exact new PNG with only image/png is accepted")

    command("svn", "propset", "test:unexpected", "not allowed", str(image))
    rejected(lambda: release.verify_wc(wc), "Unexpected artwork properties")
    command("svn", "propdel", "test:unexpected", str(image))
    command("svn", "propset", "svn:mime-type", "application/octet-stream", str(image))
    rejected(lambda: release.verify_wc(wc), "Unexpected artwork properties")
    command("svn", "propset", "svn:mime-type", "image/png", str(image))
    print("PASS: extra properties and noncanonical PNG MIME type are rejected")

    runtime = wc / "trunk" / "fixture.php"
    command("svn", "propset", "test:unexpected", "not allowed", str(runtime))
    rejected(lambda: release.verify_wc(wc), "outside directory artwork")
    command("svn", "propdel", "test:unexpected", str(runtime))
    (wc / "tags" / "unapproved").mkdir()
    rejected(lambda: release.verify_wc(wc), "Unexpected SVN release tags")
    (wc / "tags" / "unapproved").rmdir()
    (wc / "extra-untracked.txt").write_text("not allowed")
    rejected(lambda: release.verify_wc(wc), "Unexpected SVN working-copy changes")
    (wc / "extra-untracked.txt").unlink()
    print("PASS: runtime properties, extra tags and untracked files are rejected")

    command("svn", "commit", str(wc), "-m", "Commit local test fixture")
    command("svn", "update", str(wc))
    release.verify_wc(wc)
    command("svn", "propset", "svn:mime-type", "application/octet-stream", str(image))
    rejected(lambda: release.verify_wc(wc), "SVN conflict or unexpected properties")
    command("svn", "revert", str(image))
    runtime.write_bytes(payload + b"// changed\n")
    rejected(lambda: release.verify_wc(wc), "Fixture runtime differs")
    command("svn", "revert", str(runtime))
    release.verify_wc(wc)
    print("PASS: identical committed release is accepted; later property/runtime edits are rejected")

    other = root / "other"
    command("svn", "checkout", url, str(other))
    (other / "trunk" / "fixture.php").write_bytes(payload + b"// remote change\n")
    command("svn", "commit", str(other), "-m", "Create local remote-change fixture")
    rejected(lambda: release.verify_wc(wc), "SVN changed remotely")
    print("PASS: remote changes are rejected")
print("All local SVN working-copy regression checks passed; no WordPress server or credentials used.")
