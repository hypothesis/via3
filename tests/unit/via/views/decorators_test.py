from unittest import mock

import checkmatelib
import pytest
from checkmatelib import CheckmateException
from h_vialib.exceptions import TokenException
from pyramid.response import Response

from via.views.decorators import checkmate_block, has_secure_url_token


@checkmate_block
def dummy_view_checkmate_block(context, request):
    return Response("ok")


@has_secure_url_token
def dummy_view_url_token(context, request):
    return Response("ok")


class TestCheckMateBlockDecorator:
    @pytest.mark.parametrize("allow_all", [True, False])
    def test_allowed_url(self, pyramid_request, allow_all):
        url = "http://example.com"
        pyramid_request.params["url"] = url
        pyramid_request.registry.settings["checkmate_allow_all"] = allow_all

        response = dummy_view_checkmate_block(None, pyramid_request)

        pyramid_request.checkmate.check_url.assert_called_once_with(
            url, allow_all=allow_all, blocked_for=None, ignore_reasons=None
        )
        assert response.status_code == 200
        assert response.text == "ok"

    @pytest.mark.parametrize("allow_all", [True, False])
    def test_blocked_url(self, pyramid_request, block_response, allow_all):
        url = "http://bad.example.com"
        pyramid_request.checkmate.check_url.return_value = block_response
        pyramid_request.params["url"] = url
        pyramid_request.registry.settings["checkmate_allow_all"] = allow_all

        response = dummy_view_checkmate_block(None, pyramid_request)

        pyramid_request.checkmate.check_url.assert_called_once_with(
            url, allow_all=allow_all, blocked_for=None, ignore_reasons=None
        )
        assert response.status_code == 307
        assert response.location == block_response.presentation_url

    def test_invalid_url(self, pyramid_request):
        url = "http://bad.example.com]"
        pyramid_request.checkmate.check_url.side_effect = CheckmateException
        pyramid_request.params["url"] = url

        response = dummy_view_checkmate_block(None, pyramid_request)

        # Request continues despite Checkmate errors
        assert response.status_code == 200
        assert response.text == "ok"

    @pytest.fixture
    def block_response(self):
        return mock.create_autospec(
            checkmatelib.client.BlockResponse, instance=True, spec_set=True
        )


class TestSignedURLDecorator:
    def test_signed_urls_disabled(self, pyramid_request, ViaSecureURL):
        pyramid_request.registry.settings["signed_urls_required"] = False

        response = dummy_view_url_token(None, pyramid_request)

        ViaSecureURL.assert_not_called()
        assert response.status_code == 200
        assert response.text == "ok"

    def test_signed_urls_disabled_with_signature(self, pyramid_request, ViaSecureURL):
        pyramid_request.params["via.sec"] = "invalid"
        pyramid_request.registry.settings["signed_urls_required"] = False
        ViaSecureURL.return_value.verify.side_effect = TokenException()

        response = dummy_view_url_token(None, pyramid_request)

        assert response.status_code == 401

    def test_invalid_token(self, pyramid_request, ViaSecureURL):
        ViaSecureURL.return_value.verify.side_effect = TokenException()
        pyramid_request.params["via.sec"] = "invalid"

        response = dummy_view_url_token(None, pyramid_request)

        assert response.status_code == 401

    def test_valid_token(self, pyramid_request, ViaSecureURL):
        ViaSecureURL.return_value.verify.return_value = "secure"
        pyramid_request.params["via.sec"] = "secure"

        response = dummy_view_url_token(None, pyramid_request)

        assert response.status_code == 200
        assert response.text == "ok"

    @pytest.fixture
    def ViaSecureURL(self, patch):
        return patch("via.views.decorators.ViaSecureURL")
