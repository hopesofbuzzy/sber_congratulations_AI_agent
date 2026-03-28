from __future__ import annotations

import html
import mimetypes
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

from app.db.models import Greeting


def _body_paragraphs(text: str) -> list[str]:
    parts = [part.strip() for part in (text or "").split("\n\n")]
    return [part for part in parts if part]


def _paragraph_to_html(text: str) -> str:
    escaped = html.escape(text).replace("\n", "<br>")
    return (
        '<p style="margin:0 0 18px; font-size:16px; line-height:1.82; color:#111111; font-weight:600;">'
        f"{escaped}</p>"
    )


def _resolve_image_asset(greeting: Greeting) -> tuple[bytes, str, str] | None:
    if not greeting.image_path:
        return None

    base_dir = Path(__file__).resolve().parents[2] / "data"
    asset_path = base_dir / greeting.image_path
    if not asset_path.exists() or not asset_path.is_file():
        return None

    content_type, _ = mimetypes.guess_type(str(asset_path))
    if not content_type or "/" not in content_type:
        content_type = "application/octet-stream"
    return asset_path.read_bytes(), content_type, asset_path.name


def build_smtp_message(*, greeting: Greeting, recipient: str, from_email: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = recipient
    msg["Subject"] = greeting.subject

    plain_lines = [
        greeting.subject.strip(),
        "",
        (greeting.body or "").strip(),
        "",
        "С уважением,",
        "Команда Сбер",
    ]

    image_asset = _resolve_image_asset(greeting)
    image_cid_ref = ""
    if image_asset is not None:
        _, _, filename = image_asset
        plain_lines.extend(["", f"Изображение: {filename}"])
        image_cid = make_msgid(domain="sber.local")
        image_cid_ref = image_cid[1:-1]

    msg.set_content("\n".join(plain_lines))

    body_html = "".join(_paragraph_to_html(part) for part in _body_paragraphs(greeting.body or ""))
    image_html = ""
    if image_cid_ref:
        image_html = (
            '<div style="margin:0 0 30px; padding:12px; border-radius:30px; '
            "background:#ffffff; "
            'border:1px solid rgba(19, 109, 75, 0.12); box-shadow:0 18px 46px rgba(8, 78, 54, 0.10);">'
            '<div style="height:8px; width:96px; margin:0 auto 12px; border-radius:999px; '
            'background:linear-gradient(90deg, #0b6a49 0%, #20c784 100%); opacity:0.92;"></div>'
            f'<img src="cid:{image_cid_ref}" alt="Поздравительная иллюстрация" '
            'style="display:block; width:100%; max-width:560px; border-radius:22px; '
            'border:4px solid #ffffff; box-shadow:0 14px 30px rgba(9, 105, 74, 0.12);">'
            "</div>"
        )

    html_body = f"""\
<!doctype html>
<html lang="ru">
  <body style="margin:0; padding:0; background:#f4f7f5; font-family:Arial, Helvetica, sans-serif;">
    <div style="background:#f4f7f5; padding:40px 16px;">
      <div style="max-width:680px; margin:0 auto;">
        <div style="text-align:center; margin-bottom:18px;">
          <span style="display:inline-block; padding:8px 14px; border-radius:999px; background:#e8f5ee; color:#0b6a49; font-size:12px; letter-spacing:0.08em; text-transform:uppercase; border:1px solid rgba(11, 106, 73, 0.10);">Сбер | персональное поздравление</span>
        </div>
        <div style="background:#ffffff; border-radius:32px; overflow:hidden; box-shadow:0 18px 40px rgba(19, 45, 35, 0.10); border:1px solid rgba(18, 74, 54, 0.10);">
          <div style="background:
            radial-gradient(circle at top right, rgba(255,255,255,0.20) 0%, rgba(255,255,255,0) 30%),
            linear-gradient(135deg, #0b6a49 0%, #13956a 58%, #1db77a 100%);
            padding:38px 36px 34px; color:#ffffff;">
            <div style="font-size:13px; opacity:0.92; margin-bottom:12px; letter-spacing:0.04em;">Тёплое поздравление от команды Сбера</div>
            <div style="font-size:31px; font-weight:700; line-height:1.22; color:#ffffff;">{html.escape(greeting.subject)}</div>
            <div style="margin-top:18px; width:112px; height:4px; border-radius:999px; background:rgba(255,255,255,0.78);"></div>
          </div>
          <div style="background:#ffffff; padding:34px 36px 36px;">
            {image_html}
            <div style="padding:28px 28px 12px; border-radius:28px; background:#ffffff; border:1px solid rgba(19, 109, 75, 0.08); box-shadow:none; font-size:16px;">
              {body_html}
            </div>
            <div style="margin-top:26px; padding:20px 24px; border-radius:24px; background:#ffffff; color:#123629; border:1px solid rgba(19, 109, 75, 0.10); box-shadow:0 8px 24px rgba(19, 45, 35, 0.06);">
              <div style="font-size:12px; letter-spacing:0.14em; text-transform:uppercase; color:#0b6a49; margin-bottom:8px;">С уважением</div>
              <div style="font-size:22px; font-weight:700; color:#123629; margin-bottom:6px;">Команда Сбер</div>
              <div style="width:84px; height:3px; border-radius:999px; background:linear-gradient(90deg, #0b6a49 0%, rgba(11, 106, 73, 0.12) 100%);"></div>
              <div style="margin-top:12px; font-size:13px; line-height:1.65; color:#33584c;">
                Персональное поздравление для вас.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
"""

    msg.add_alternative(html_body, subtype="html")

    if image_asset is not None and image_cid_ref:
        image_bytes, content_type, filename = image_asset
        maintype, subtype = content_type.split("/", 1)
        html_part = msg.get_payload()[-1]
        html_part.add_related(
            image_bytes,
            maintype=maintype,
            subtype=subtype,
            cid=f"<{image_cid_ref}>",
            filename=filename,
            disposition="inline",
        )

    return msg
