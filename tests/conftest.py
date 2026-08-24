import os
import tempfile

_tmp = tempfile.NamedTemporaryFile(prefix="devlens-test-", suffix=".db", delete=False)
os.environ["DEVLENS_DB_PATH"] = _tmp.name
_tmp.close()
