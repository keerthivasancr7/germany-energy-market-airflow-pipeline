import io
import tempfile
import unittest
from pathlib import Path

from tools.deploy_glue_script import deploy


class ScriptStore:
    def __init__(self, corrupt=False):
        self.corrupt = corrupt
        self.request = None

    def put_object(self, **request):
        self.request = request

    def get_object(self, **request):
        if request["Bucket"] != self.request["Bucket"] or request["Key"] != self.request["Key"]:
            raise AssertionError("Verification must read back the deployed key")
        return {"Body": io.BytesIO(b"corrupted" if self.corrupt else self.request["Body"])}


class TestScriptDeploy(unittest.TestCase):
    def test_publishes_and_verifies_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "job.py"
            path.write_text("print('energy')\n")
            client = ScriptStore()
            digest = deploy(client, path, "fixture-bucket", "scripts/energy.py", "abc123")
            self.assertEqual(client.request["Metadata"]["sha256"], digest)
            self.assertEqual(client.request["Metadata"]["git-commit"], "abc123")
            self.assertEqual(client.request["ServerSideEncryption"], "AES256")

    def test_corrupt_remote_content_fails_deployment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "job.py"
            path.write_text("print('energy')\n")
            with self.assertRaisesRegex(RuntimeError, "checksum"):
                deploy(ScriptStore(corrupt=True), path, "fixture-bucket", "scripts/energy.py", "abc123")
