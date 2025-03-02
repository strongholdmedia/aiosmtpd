# Copyright 2014-2021 The aiosmtpd Developers
# SPDX-License-Identifier: Apache-2.0

"""Test SMTP over SSL/TLS."""

from email.mime.text import MIMEText
from smtplib import SMTP, SMTP_SSL
from typing import Generator, Union

import pytest

from aiosmtpd.controller import Controller
from aiosmtpd.testing.helpers import ReceivingHandler

from .conftest import Global


@pytest.fixture
def ssl_controller(
    get_controller, ssl_context_server
) -> Generator[Controller, None, None]:
    handler = ReceivingHandler()
    # ssl_context is only used by create_server, and not accessed at all
    controller = get_controller(
        handler,
        ssl_context=ssl_context_server,
        is_using_smtps=True
    )
    controller.start()
    Global.set_addr_from(controller)
    #
    yield controller
    #
    controller.stop()


@pytest.fixture
def smtps_client(ssl_context_client) -> Generator[Union[SMTP_SSL, SMTP], None, None]:
    context = ssl_context_client
    with SMTP_SSL(*Global.SrvAddr, context=context) as client:
        yield client


class TestSMTPS:
    def test_smtps(self, ssl_controller, smtps_client):
        sender = "sender@example.com"
        recipients = ["rcpt1@example.com"]
        code, _ = smtps_client.ehlo("example.com")
        assert code == 250
        assert smtps_client.has_extn("AUTH")
        assert not smtps_client.has_extn("STARTTLS")
        results = smtps_client.send_message(MIMEText("hi"), sender, recipients)
        assert results == {}
        handler: ReceivingHandler = ssl_controller.handler
        assert len(handler.box) == 1
        envelope = handler.box[0]
        assert envelope.mail_from == sender
        assert envelope.rcpt_tos == recipients
