"""Runs last (file name): the QA server's log must not contain any unhandled exception or error line."""


def test_server_log_has_no_errors(server):
    log = server.log_text()
    bad = [line for line in log.splitlines()
           if "Traceback" in line or " ERROR " in line or "Exception" in line or "CRITICAL" in line]
    assert not bad, "\n".join(bad[:20])
