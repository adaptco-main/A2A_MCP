from prime_directive.sovereignty.chain import event_fingerprint, verify_link
from prime_directive.sovereignty.event import SovereigntyEvent


def test_event_fingerprint_deterministic():
    event = SovereigntyEvent(event_type="state.transition", state="rendering", payload={"a": 1})
    assert event_fingerprint(event) == event_fingerprint(event)


def test_verify_link():
    event = SovereigntyEvent(event_type="gate.preflight", state="validating", payload={"ok": True}, prev_hash="abc")
    assert verify_link(event, "abc")
