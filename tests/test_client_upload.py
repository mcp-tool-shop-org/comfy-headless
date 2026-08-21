"""Tests for ComfyClient asset uploads (POST /upload/image, POST /upload/mask).

These cover the route that gets an input image *into* ComfyUI so a core
``LoadImage`` node can reference it. All HTTP is mocked - no live ComfyUI.
"""

import json
from unittest.mock import Mock, patch

import pytest

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 32


def _upload_response(name="photo.png", subfolder="", type_="input", **extra):
    """Build a mock requests.Response for a successful upload."""
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.text = json.dumps({"name": name, "subfolder": subfolder, "type": type_})
    payload = {"name": name, "subfolder": subfolder, "type": type_}
    payload.update(extra)
    response.json.return_value = payload
    return response


def _client():
    from comfy_headless.client import ComfyClient

    return ComfyClient(base_url="http://localhost:8188")


# ============================================================================
# HAPPY PATH
# ============================================================================


class TestUploadImageHappyPath:
    """Successful uploads and multipart shape."""

    @patch("comfy_headless.client.ComfyClient._post")
    def test_upload_bytes_returns_server_name(self, mock_post):
        """Upload from raw bytes returns the server-reported name."""
        mock_post.return_value = _upload_response(name="photo.png")

        result = _client().upload_image(PNG_BYTES, filename="photo.png")

        assert result["name"] == "photo.png"
        assert result["subfolder"] == ""
        assert result["type"] == "input"
        assert result["ref"] == "photo.png"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_upload_posts_to_upload_image_route(self, mock_post):
        """The upload hits POST /upload/image."""
        mock_post.return_value = _upload_response()

        _client().upload_image(PNG_BYTES, filename="photo.png")

        assert mock_post.call_args[0][0] == "/upload/image"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_multipart_field_is_named_image_not_file(self, mock_post):
        """The file part is literally named 'image' (a 'file' field is wrong)."""
        mock_post.return_value = _upload_response()

        _client().upload_image(PNG_BYTES, filename="photo.png")

        files = mock_post.call_args.kwargs["files"]
        assert "image" in files
        assert "file" not in files
        sent_name, sent_data, content_type = files["image"]
        assert sent_name == "photo.png"
        assert sent_data == PNG_BYTES
        assert content_type == "image/png"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_type_defaults_to_input(self, mock_post):
        """The 'type' form field defaults to 'input'."""
        mock_post.return_value = _upload_response()

        _client().upload_image(PNG_BYTES, filename="photo.png")

        assert mock_post.call_args.kwargs["data"]["type"] == "input"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_temp_type_is_forwarded(self, mock_post):
        """A non-default folder type is forwarded verbatim."""
        mock_post.return_value = _upload_response(type_="temp")

        result = _client().upload_image(PNG_BYTES, filename="photo.png", type="temp")

        assert mock_post.call_args.kwargs["data"]["type"] == "temp"
        assert result["type"] == "temp"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_upload_from_path(self, mock_post, tmp_path):
        """Upload from a filesystem path reads the file and uses its basename."""
        source = tmp_path / "cat.png"
        source.write_bytes(PNG_BYTES)
        mock_post.return_value = _upload_response(name="cat.png")

        result = _client().upload_image(str(source))

        sent_name, sent_data, _ = mock_post.call_args.kwargs["files"]["image"]
        assert sent_name == "cat.png"
        assert sent_data == PNG_BYTES
        assert result["ref"] == "cat.png"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_bytes_without_filename_sniffs_extension(self, mock_post):
        """Raw bytes with no filename get a generated name with a sniffed suffix."""
        mock_post.return_value = _upload_response(name="generated.jpg")

        _client().upload_image(JPEG_BYTES)

        sent_name = mock_post.call_args.kwargs["files"]["image"][0]
        assert sent_name.endswith(".jpg")
        assert sent_name.startswith("comfy_headless_")

    @patch("comfy_headless.client.ComfyClient._post")
    def test_upload_uses_image_timeout(self, mock_post):
        """Uploads honour the configured image transfer timeout."""
        from comfy_headless.config import settings

        mock_post.return_value = _upload_response()

        _client().upload_image(PNG_BYTES, filename="photo.png")

        assert mock_post.call_args.kwargs["timeout"] == settings.comfyui.timeout_image


# ============================================================================
# COLLISION RENAME - the server's name is authoritative
# ============================================================================


class TestCollisionRename:
    """With overwrite=False the server renames on collision; we must read it back."""

    @patch("comfy_headless.client.ComfyClient._post")
    def test_server_rename_is_honoured(self, mock_post):
        """A different name in the response wins over the name we sent."""
        mock_post.return_value = _upload_response(name="photo (2).png")

        result = _client().upload_image(PNG_BYTES, filename="photo.png")

        assert mock_post.call_args.kwargs["files"]["image"][0] == "photo.png"
        assert result["name"] == "photo (2).png"
        assert result["ref"] == "photo (2).png"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_server_rename_with_subfolder(self, mock_post):
        """Rename plus subfolder produces the correct LoadImage ref."""
        mock_post.return_value = _upload_response(name="photo_1.png", subfolder="refs")

        result = _client().upload_image(PNG_BYTES, filename="photo.png", subfolder="refs")

        assert result["name"] == "photo_1.png"
        assert result["subfolder"] == "refs"
        assert result["ref"] == "refs/photo_1.png"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_server_may_relocate_subfolder(self, mock_post):
        """The server's subfolder is authoritative too, even if it differs."""
        mock_post.return_value = _upload_response(name="photo.png", subfolder="")

        result = _client().upload_image(PNG_BYTES, filename="photo.png", subfolder="refs")

        assert result["subfolder"] == ""
        assert result["ref"] == "photo.png"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_overwrite_false_does_not_send_the_field(self, mock_post):
        """overwrite=False omits the field (presence alone reads truthy on some builds)."""
        mock_post.return_value = _upload_response()

        _client().upload_image(PNG_BYTES, filename="photo.png", overwrite=False)

        assert "overwrite" not in mock_post.call_args.kwargs["data"]

    @patch("comfy_headless.client.ComfyClient._post")
    def test_overwrite_true_sends_string_true(self, mock_post):
        """overwrite=True is sent as the string 'true'."""
        mock_post.return_value = _upload_response()

        _client().upload_image(PNG_BYTES, filename="photo.png", overwrite=True)

        assert mock_post.call_args.kwargs["data"]["overwrite"] == "true"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_missing_name_does_not_fall_back_to_sent_filename(self, mock_post):
        """A response without a name is an error, never a silent local-name fallback."""
        from comfy_headless.exceptions import UploadError

        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "{}"
        response.json.return_value = {"subfolder": "", "type": "input"}
        mock_post.return_value = response

        with pytest.raises(UploadError) as exc_info:
            _client().upload_image(PNG_BYTES, filename="photo.png")

        assert exc_info.value.code == "UPLOAD_ERROR"
        assert "filename" in str(exc_info.value).lower()

    @patch("comfy_headless.client.ComfyClient._post")
    def test_filename_key_alias_is_tolerated(self, mock_post):
        """A server answering with 'filename' instead of 'name' still works."""
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "{}"
        response.json.return_value = {"filename": "photo_3.png", "subfolder": "", "type": "input"}
        mock_post.return_value = response

        result = _client().upload_image(PNG_BYTES, filename="photo.png")

        assert result["name"] == "photo_3.png"


# ============================================================================
# SUBFOLDER HANDLING
# ============================================================================


class TestSubfolderHandling:
    """Subfolder normalization and traversal rejection."""

    @patch("comfy_headless.client.ComfyClient._post")
    def test_subfolder_is_sent(self, mock_post):
        """A subfolder is forwarded as a form field."""
        mock_post.return_value = _upload_response(subfolder="refs")

        _client().upload_image(PNG_BYTES, filename="photo.png", subfolder="refs")

        assert mock_post.call_args.kwargs["data"]["subfolder"] == "refs"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_empty_subfolder_is_omitted(self, mock_post):
        """No subfolder means no subfolder field."""
        mock_post.return_value = _upload_response()

        _client().upload_image(PNG_BYTES, filename="photo.png")

        assert "subfolder" not in mock_post.call_args.kwargs["data"]

    @patch("comfy_headless.client.ComfyClient._post")
    def test_subfolder_slashes_normalized(self, mock_post):
        """Leading/trailing slashes and backslashes are normalized."""
        mock_post.return_value = _upload_response(subfolder="a/b")

        _client().upload_image(PNG_BYTES, filename="photo.png", subfolder="\\a\\b\\")

        assert mock_post.call_args.kwargs["data"]["subfolder"] == "a/b"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_subfolder_traversal_rejected(self, mock_post):
        """A '..' segment is a SecurityError, and nothing is sent."""
        from comfy_headless.exceptions import SecurityError

        with pytest.raises(SecurityError):
            _client().upload_image(PNG_BYTES, filename="photo.png", subfolder="../../etc")

        mock_post.assert_not_called()

    @patch("comfy_headless.client.ComfyClient._post")
    def test_filename_directory_component_stripped(self, mock_post):
        """A directory component in the filename never reaches the wire."""
        mock_post.return_value = _upload_response(name="passwd")

        _client().upload_image(PNG_BYTES, filename="../../etc/passwd")

        assert mock_post.call_args.kwargs["files"]["image"][0] == "passwd"


# ============================================================================
# FAILURE PATHS
# ============================================================================


class TestUploadFailurePaths:
    """Structured errors instead of raw stacks."""

    @patch("comfy_headless.client.ComfyClient._post")
    def test_http_error_raises_upload_error(self, mock_post):
        """A non-2xx response becomes a structured UploadError."""
        from comfy_headless.exceptions import UploadError

        response = Mock()
        response.ok = False
        response.status_code = 413
        response.text = "payload too large"
        mock_post.return_value = response

        with pytest.raises(UploadError) as exc_info:
            _client().upload_image(PNG_BYTES, filename="photo.png")

        error = exc_info.value
        assert error.code == "UPLOAD_ERROR"
        assert error.details["status_code"] == 413
        assert error.details["filename"] == "photo.png"
        assert error.details["endpoint"] == "/upload/image"
        assert error.suggestions

    @patch("comfy_headless.client.ComfyClient._post")
    def test_non_json_response_raises_upload_error(self, mock_post):
        """An HTML/proxy response becomes an UploadError, not a JSONDecodeError."""
        from comfy_headless.exceptions import UploadError

        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "<html>not comfyui</html>"
        response.url = "http://localhost:8188/upload/image"
        response.json.side_effect = json.JSONDecodeError("nope", "<html>", 0)
        mock_post.return_value = response

        with pytest.raises(UploadError):
            _client().upload_image(PNG_BYTES, filename="photo.png")

    @patch("comfy_headless.client.ComfyClient._post")
    def test_non_dict_response_raises_upload_error(self, mock_post):
        """A JSON list response is rejected with a structured error."""
        from comfy_headless.exceptions import UploadError

        response = Mock()
        response.ok = True
        response.status_code = 200
        response.text = "[]"
        response.json.return_value = []
        mock_post.return_value = response

        with pytest.raises(UploadError):
            _client().upload_image(PNG_BYTES, filename="photo.png")

    @patch("comfy_headless.client.ComfyClient._post")
    def test_connection_error_propagates(self, mock_post):
        """Connection failures keep their existing exception type."""
        from comfy_headless.exceptions import ComfyUIConnectionError

        mock_post.side_effect = ComfyUIConnectionError(message="down", url="http://localhost:8188")

        with pytest.raises(ComfyUIConnectionError):
            _client().upload_image(PNG_BYTES, filename="photo.png")

    def test_invalid_type_rejected(self):
        """An unknown folder type is an InvalidParameterError."""
        from comfy_headless.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            _client().upload_image(PNG_BYTES, filename="photo.png", type="nowhere")

    def test_missing_file_raises_validation_error(self, tmp_path):
        """A path that does not exist is a ValidationError."""
        from comfy_headless.exceptions import ValidationError

        with pytest.raises(ValidationError):
            _client().upload_image(str(tmp_path / "does_not_exist.png"))

    def test_unsupported_source_type_rejected(self):
        """An int is not a valid upload source."""
        from comfy_headless.exceptions import InvalidParameterError

        with pytest.raises(InvalidParameterError):
            _client().upload_image(12345)

    def test_empty_bytes_rejected(self):
        """Empty data is refused before hitting the network."""
        from comfy_headless.exceptions import ValidationError

        with pytest.raises(ValidationError):
            _client().upload_image(b"", filename="photo.png")


# ============================================================================
# MASK UPLOAD
# ============================================================================


class TestUploadMask:
    """POST /upload/mask with an original_ref pointing at the base image."""

    @patch("comfy_headless.client.ComfyClient._post")
    def test_mask_posts_to_upload_mask_route(self, mock_post):
        """The mask upload hits POST /upload/mask."""
        mock_post.return_value = _upload_response(name="mask.png")

        _client().upload_mask(PNG_BYTES, "photo.png", filename="mask.png")

        assert mock_post.call_args[0][0] == "/upload/mask"

    @patch("comfy_headless.client.ComfyClient._post")
    def test_original_ref_from_filename(self, mock_post):
        """A bare filename is expanded into the expected original_ref JSON."""
        mock_post.return_value = _upload_response(name="mask.png")

        _client().upload_mask(PNG_BYTES, "photo.png", filename="mask.png")

        ref = json.loads(mock_post.call_args.kwargs["data"]["original_ref"])
        assert ref == {"filename": "photo.png", "subfolder": "", "type": "input"}

    @patch("comfy_headless.client.ComfyClient._post")
    def test_original_ref_from_upload_result(self, mock_post):
        """The dict returned by upload_image() is accepted directly."""
        mock_post.return_value = _upload_response(name="mask.png")
        base = {"name": "photo_2.png", "subfolder": "refs", "type": "input", "ref": "x"}

        _client().upload_mask(PNG_BYTES, base, filename="mask.png")

        ref = json.loads(mock_post.call_args.kwargs["data"]["original_ref"])
        assert ref == {"filename": "photo_2.png", "subfolder": "refs", "type": "input"}

    @patch("comfy_headless.client.ComfyClient._post")
    def test_mask_collision_rename_honoured(self, mock_post):
        """Mask uploads read the stored name back the same way."""
        mock_post.return_value = _upload_response(name="mask (1).png")

        result = _client().upload_mask(PNG_BYTES, "photo.png", filename="mask.png")

        assert result["name"] == "mask (1).png"

    def test_original_ref_without_name_rejected(self):
        """An original_ref that names no base image is a ValidationError."""
        from comfy_headless.exceptions import ValidationError

        with pytest.raises(ValidationError):
            _client().upload_mask(PNG_BYTES, {"subfolder": "refs"}, filename="mask.png")

    def test_original_ref_wrong_type_rejected(self):
        """A non-dict, non-str original_ref is a ValidationError."""
        from comfy_headless.exceptions import ValidationError

        with pytest.raises(ValidationError):
            _client().upload_mask(PNG_BYTES, 42, filename="mask.png")


# ============================================================================
# ROUND TRIP INTO A WORKFLOW
# ============================================================================


class TestUploadToLoadImageWiring:
    """The whole point: upload -> ref -> core LoadImage node."""

    @patch("comfy_headless.client.ComfyClient._post")
    def test_ref_feeds_a_load_image_node(self, mock_post):
        """The returned ref is exactly what LoadImage.inputs.image wants."""
        mock_post.return_value = _upload_response(name="photo_1.png", subfolder="refs")

        uploaded = _client().upload_image(PNG_BYTES, filename="photo.png", subfolder="refs")
        node = {"class_type": "LoadImage", "inputs": {"image": uploaded["ref"]}}

        assert node["inputs"]["image"] == "refs/photo_1.png"

    @patch("comfy_headless.client.ComfyClient._get")
    @patch("comfy_headless.client.ComfyClient._post")
    def test_round_trip_read_back_via_view(self, mock_post, mock_get):
        """The stored name/subfolder read back through /view with type=input."""
        mock_post.return_value = _upload_response(name="photo_1.png", subfolder="refs")
        view_response = Mock()
        view_response.ok = True
        view_response.content = PNG_BYTES
        mock_get.return_value = view_response

        client = _client()
        uploaded = client.upload_image(PNG_BYTES, filename="photo.png", subfolder="refs")
        content = client.get_image(uploaded["name"], uploaded["subfolder"], "input")

        assert content == PNG_BYTES
        assert mock_get.call_args[0][0] == "/view"
        assert mock_get.call_args.kwargs["params"] == {
            "filename": "photo_1.png",
            "subfolder": "refs",
            "type": "input",
        }

    def test_video_builders_use_core_load_image(self):
        """Every img2vid builder emits the core LoadImage node."""
        from comfy_headless.video import VIDEO_PRESETS, VideoModel, build_video_workflow

        i2v_presets = [
            name
            for name, preset in VIDEO_PRESETS.items()
            if preset.model
            in (
                VideoModel.SVD,
                VideoModel.SVD_XT,
                VideoModel.LTXV,
                VideoModel.LTXV_I2V,
                VideoModel.WAN,
                VideoModel.WAN_I2V,
            )
        ]
        assert i2v_presets, "expected at least one image-to-video preset"

        for name in i2v_presets:
            workflow = build_video_workflow(
                prompt="a cat walking",
                preset=name,
                init_image="uploaded_photo.png",
            )
            load_nodes = [
                node for node in workflow.values() if node.get("class_type") == "LoadImage"
            ]
            assert load_nodes, f"preset {name} emitted no LoadImage node"
            for node in load_nodes:
                assert node["inputs"]["image"] == "uploaded_photo.png"

    def test_no_load_image_from_base64_anywhere(self):
        """The unresolvable custom-pack node is gone from the package."""
        from pathlib import Path

        import comfy_headless

        package_root = Path(comfy_headless.__file__).parent
        offenders = [
            path.name
            for path in package_root.rglob("*.py")
            if "LoadImageFromBase64" in path.read_text(encoding="utf-8")
        ]
        assert offenders == []
