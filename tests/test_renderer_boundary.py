from PySide6.QtCore import QUrl

from app.ui.window import WEB_ROOT, renderer_url_allowed


def test_local_scene_allowed_but_network_and_other_files_denied(tmp_path):
    assert renderer_url_allowed(QUrl.fromLocalFile(str(WEB_ROOT / "index.html")))
    assert renderer_url_allowed(QUrl("qrc:///qtwebchannel/qwebchannel.js"))
    assert not renderer_url_allowed(QUrl("https://example.com"))
    assert not renderer_url_allowed(QUrl("http://127.0.0.1:11434/api/tags"))
    assert not renderer_url_allowed(QUrl("file://untrusted-server/share/file.js"))
    assert not renderer_url_allowed(QUrl("qrc:///other/resource"))
    secret = tmp_path / "credentials.txt"
    secret.write_text("private", encoding="utf-8")
    assert not renderer_url_allowed(QUrl.fromLocalFile(str(secret)))
