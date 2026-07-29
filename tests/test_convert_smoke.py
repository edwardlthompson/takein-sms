"""Smoke tests for Google Voice HTML → SMS conversion."""

from __future__ import annotations

from convert_gvoice import parse_iso_to_ms, parse_messages_from_html

SAMPLE = """
<div class="hChatLog hfeed">
<div class="message"><abbr class="dt" title="2024-01-10T16:54:41.322-04:00">x</abbr>:
<cite class="sender vcard"><a class="tel" href="tel:+12013508475"><span class="fn">Adobe</span></a></cite>:
<q>468610 is your Adobe code</q>
</div>
<div class="message"><abbr class="dt" title="2024-01-10T16:55:00.000-04:00">x</abbr>:
<cite class="sender vcard"><a class="tel" href="tel:+14694764376"><abbr class="fn" title="">Me</abbr></a></cite>:
<q>Thanks</q>
</div>
</div>
"""


def test_parse_iso_to_ms() -> None:
    ms = parse_iso_to_ms("2024-01-10T16:54:41.322-04:00")
    assert ms is not None
    assert ms > 1_700_000_000_000


def test_parse_messages_direction() -> None:
    msgs = parse_messages_from_html(SAMPLE, "+12013508475")
    assert len(msgs) == 2
    assert msgs[0].type_ == 1
    assert "Adobe code" in msgs[0].body
    assert msgs[1].type_ == 2
    assert msgs[1].body == "Thanks"
