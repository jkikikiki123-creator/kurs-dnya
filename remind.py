"""Напоминалка для Telegram: присылает фразу и кнопку, открывающую мини-апку.

Запускается по расписанию из GitHub Actions (.github/workflows/remind.yml).
Нужны переменные окружения: BOT_TOKEN, CHAT_ID, APP_URL.
"""
import json
import os
import random
import sys
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# План тренировок (пн → вс): (велик, зал). Должен совпадать с планом в апке.
PLAN = [
    ("Зона 2, 30–40 мин", "Силовая"),
    ("4×4", ""),
    ("Зона 2, 30–40 мин", "Силовая"),
    ("Зона 2, 45–60 мин", ""),
    ("Зона 2, 20–30 мин, очень легко", "Силовая"),
    ("Второе тяжёлое: 4×4 или 30 сек тяжело / 30 сек легко ×10–15", ""),
    ("Зона 2, длинная, 60–90 мин", ""),
]

MORNING = [
    "Доброе утро. Сначала вода и белок, потом решения. Голод — сигнал, а не приказ.",
    "Если заказываешь еду — только из своего списка нормальных заказов в SOS.",
    "Запиши главную задачу дня. Если сделаешь только её — день удался.",
    "Сегодня один правильный завтрак = голос за того, кем ты становишься.",
    "Не пропускай дважды. Если вчера был пропуск — сегодня обязательно.",
    "Выносливость строится в скучные дни. Отметь привычки и запиши 1–3 дела.",
]
EVENING = [
    "Вечерняя проверка: отметь привычки, запиши траты и закрой день — 3 вопроса, 1 минута.",
    "Минута на итоги: что получилось, что помешало, что завтра сделаешь иначе?",
    "Что сегодня сделал для выносливости? Отметь в «Курсе дня».",
    "Пара минут на финансы: сколько ушло сегодня и на что?",
    "Подготовь еду на завтрашнее утро — так утренний выбор станет лёгким.",
]


def main() -> None:
    token = os.environ["BOT_TOKEN"]
    chat_id = os.environ["CHAT_ID"]
    app_url = os.environ["APP_URL"]
    slot = os.environ.get("SLOT") or ("morning" if datetime.now(timezone.utc).hour < 12 else "evening")

    text = random.choice(MORNING if slot == "morning" else EVENING)
    now_local = datetime.now(ZoneInfo(os.environ.get("TZ_NAME", "Europe/Warsaw")))
    if slot == "evening" and now_local.weekday() == 6:
        text = "Воскресенье — время недельного обзора. Апка уже собрала цифры: ответь на два вопроса, 5 минут."
    if slot == "morning":
        day = datetime.now(ZoneInfo(os.environ.get("TZ_NAME", "Europe/Warsaw"))).weekday()
        bike, gym = PLAN[day]
        parts = [f"🚴 {bike}"] if bike else []
        if gym:
            parts.append(f"🏋️ {gym}")
        text += "\n\nТренировка сегодня:\n" + ("\n".join(parts) if parts else "отдых")
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": [[{"text": "Открыть «Курс дня»", "web_app": {"url": app_url}}]]
        },
    }
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        body = json.load(r)
    if not body.get("ok"):
        print(body, file=sys.stderr)
        sys.exit(1)
    print("sent:", text)


if __name__ == "__main__":
    main()
