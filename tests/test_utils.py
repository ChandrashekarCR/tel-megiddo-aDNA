"""Unit tests for `src.db_build.utils`."""

import pytest
import yaml

from src.db_build.utils import get_logger, load_config, mark_done, run, sentinel


class TestLoadConfig:
    def test_load_config_reads_yaml(self, tmp_path):
        config_path = tmp_path / "config.yaml"
        # Dummy data is written in a config file which will be tested
        # if the output is the same as input
        expected = {
            "some_item": "some_item_path",
            "samples": ["sample_a", "sample_b"],
        }
        config_path.write_text(yaml.safe_dump(expected))

        # load_config fundtion from the script it tested here.
        result = load_config(str(config_path))

        assert result == expected


class TestSentinelHelpers:
    def test_sentinel_returns_false_when_missing(self, tmp_path):
        sentinel_path = tmp_path / "step.done"

        # There is no file created here and hence it fails
        assert sentinel(str(sentinel_path)) is False

    def test_mark_done_creates_file(self, tmp_path):
        sentinel_path = tmp_path / "step.done"

        # mark_done is a function which creates the file, so that the step is completes
        mark_done(str(sentinel_path))

        # Pass the test case here
        assert sentinel_path.exists()
        assert sentinel(str(sentinel_path)) is True


class TestGetLogger:
    def test_get_logger_creates_file_handler_and_directory(self, tmp_path):
        log_file = tmp_path / "logs" / "pipeline.log"

        # get_logger function to test if logging is done correctly
        logger = get_logger("tel_megiddo_test_logger", str(log_file))
        logger.info("hello world")

        assert log_file.exists()
        assert len(logger.handlers) == 2
        assert "hello world" in log_file.read_text()


class TestRun:
    def test_run_writes_command_output(self, tmp_path, monkeypatch):
        log_file = tmp_path / "logs" / "run.log"
        messages = []

        class DummyLogger:
            def info(self, message):
                messages.append(("info", message))

            def error(self, message):
                messages.append(("error", message))

        def fake_run(cmd, stdout=None, stderr=None):
            assert cmd == ["echo", "hello"]
            assert stdout is not None
            stdout.write("hello\n")
            return type("Result", (), {"returncode": 0})()

        monkeypatch.setattr("src.db_build.utils.subprocess.run", fake_run)

        run(["echo", "hello"], str(log_file), DummyLogger())

        assert log_file.exists()
        assert "hello" in log_file.read_text()
        assert messages[0] == ("info", "CMD: echo hello")

    def test_run_raises_on_failure(self, tmp_path, monkeypatch):
        log_file = tmp_path / "logs" / "run.log"
        messages = []

        class DummyLogger:
            def info(self, message):
                messages.append(("info", message))

            def error(self, message):
                messages.append(("error", message))

        def fake_run(cmd, stdout=None, stderr=None):
            return type("Result", (), {"returncode": 1})()

        monkeypatch.setattr("src.db_build.utils.subprocess.run", fake_run)

        with pytest.raises(RuntimeError, match="Step failed: false"):
            run(["false"], str(log_file), DummyLogger())

        assert messages[0] == ("info", "CMD: false")
        assert messages[1][0] == "error"
        assert "Command failed (exit 1)" in messages[1][1]
