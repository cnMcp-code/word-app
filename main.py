import flet as ft
import json
import os
import random
import threading
from datetime import datetime
from flet_audio import Audio

# ==================== 加载词库 ====================
def load_word_list():
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "word_list.json")
    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        print("警告: word_list.json 未找到，使用备用词库。")
        return [
            {"word": "young", "meaning": "年轻的", "emoji": "🧒", "example": "My teacher is young."},
            {"word": "old", "meaning": "年老的", "emoji": "🧓", "example": "My grandpa is old."},
        ]

WORD_LIST = load_word_list()

# ==================== 数据管理 ====================
DATA_FILE = "user_data.json"

def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for user, info in data.items():
                    if not isinstance(info.get("learned"), list):
                        info["learned"] = []
                    if not isinstance(info.get("completed_dates"), list):
                        info["completed_dates"] = []
                return data
        except:
            return {}
    return {}

def save_users(data):
    for user, info in data.items():
        if not isinstance(info.get("learned"), list):
            info["learned"] = []
        if not isinstance(info.get("completed_dates"), list):
            info["completed_dates"] = []
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_name):
    users = load_users()
    if user_name not in users:
        users[user_name] = {
            "grade": "五年级上册",
            "learned": [],
            "completed_dates": []
        }
        save_users(users)
    return users[user_name]

def save_user(user_name, user_data):
    if not isinstance(user_data.get("learned"), list):
        user_data["learned"] = []
    if not isinstance(user_data.get("completed_dates"), list):
        user_data["completed_dates"] = []
    users = load_users()
    users[user_name] = user_data
    save_users(users)

# ==================== 主应用 ====================
def main(page: ft.Page):
    page.title = "宝宝背单词"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = ft.Colors.WHITE
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ---------- 状态 ----------
    current_user = None
    user_data = None
    today_words = []
    today_index = 0
    quiz_mode = False
    quiz_questions = []
    quiz_index = 0
    current_dialog = None
    audio_player = None

    # ---------- 辅助函数 ----------
    def get_today_date():
        return datetime.now().strftime("%Y-%m-%d")

    def is_today_completed(data):
        return get_today_date() in data.get("completed_dates", [])

    def prepare_today():
        nonlocal today_words, today_index, quiz_mode
        if not current_user or not user_data:
            return
        learned_set = set(user_data.get("learned", []))
        unlearned = [w for w in WORD_LIST if w["word"] not in learned_set]
        if is_today_completed(user_data):
            today_words = []
            today_index = 0
            quiz_mode = False
        else:
            today_words = unlearned[:15]
            today_index = 0
            quiz_mode = False

    def close_dialog():
        nonlocal current_dialog
        if current_dialog:
            page.close(current_dialog)
            current_dialog = None
            page.update()

    def play_pronunciation(word):
        nonlocal audio_player
        if audio_player:
            page.overlay.remove(audio_player)
        url = f"https://dict.youdao.com/dictvoice?audio={word}&type=2"
        audio_player = Audio(src=url, autoplay=True)
        page.overlay.append(audio_player)
        page.update()

    # ---------- 页面切换 ----------
    def show_login():
        page.clean()
        page.add(build_login())

    def show_main():
        page.clean()
        page.add(build_main())

    # ---------- 登录界面 ----------
    def build_login():
        username_input = ft.TextField(
            label="新用户名",
            width=320,
            autofocus=True,
            border_color=ft.Colors.INDIGO_300,
            focused_border_color=ft.Colors.INDIGO,
            border_radius=12,
            filled=True,
            fill_color=ft.Colors.INDIGO_50,
            prefix_icon=ft.Icons.PERSON_OUTLINE,
        )
        grade_dropdown = ft.Dropdown(
            label="选择年级",
            width=320,
            border_color=ft.Colors.INDIGO_300,
            focused_border_color=ft.Colors.INDIGO,
            border_radius=12,
            filled=True,
            fill_color=ft.Colors.INDIGO_50,
            options=[
                ft.dropdown.Option("三年级上册"), ft.dropdown.Option("三年级下册"),
                ft.dropdown.Option("四年级上册"), ft.dropdown.Option("四年级下册"),
                ft.dropdown.Option("五年级上册"), ft.dropdown.Option("五年级下册"),
                ft.dropdown.Option("六年级上册"), ft.dropdown.Option("六年级下册"),
            ],
            value="五年级上册",
        )
        status_text = ft.Text("", color=ft.Colors.RED, size=14)

        users = load_users()
        recent_users = list(users.keys())
        recent_list = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        if recent_users:
            recent_list.controls.append(ft.Text(
                "最近登录",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREY_700,
            ))
            for uname in recent_users[:5]:
                data = users[uname]
                learned = data.get("learned", [])
                if not isinstance(learned, list):
                    learned = []
                completed_dates = data.get("completed_dates", [])
                if not isinstance(completed_dates, list):
                    completed_dates = []
                learned_count = len(learned)
                total = len(WORD_LIST)
                completed_days = len(completed_dates)

                recent_list.controls.append(
                    ft.Container(
                        width=320,
                        ink=True,
                        on_click=lambda e, name=uname: quick_login(name),
                        border_radius=12,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_200),
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=10,
                                    controls=[
                                        ft.Container(
                                            width=36,
                                            height=36,
                                            border_radius=18,
                                            bgcolor=ft.Colors.INDIGO_100,
                                            alignment=ft.alignment.center,
                                            content=ft.Text(uname[0].upper() if uname else "?", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                                        ),
                                        ft.Text(uname, size=15, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_800),
                                    ],
                                ),
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Container(
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                            border_radius=8,
                                            bgcolor=ft.Colors.BLUE_50,
                                            content=ft.Text(f"已学 {learned_count}/{total}", size=12, color=ft.Colors.BLUE_700),
                                        ),
                                        ft.Container(
                                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                            border_radius=8,
                                            bgcolor=ft.Colors.GREEN_50,
                                            content=ft.Text(f"坚持 {completed_days} 天", size=12, color=ft.Colors.GREEN_700),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    )
                )

        def quick_login(name):
            nonlocal current_user, user_data
            current_user = name
            user_data = get_user(name)
            prepare_today()
            show_main()

        def on_login(e):
            nonlocal current_user, user_data
            name = username_input.value.strip()
            if not name:
                status_text.value = "请输入用户名"
                page.update()
                return
            current_user = name
            user_data = get_user(name)
            user_data["grade"] = grade_dropdown.value
            save_user(name, user_data)
            prepare_today()
            show_main()

        login_card = ft.Container(
            width=360,
            padding=36,
            border_radius=24,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=30,
                color=ft.Colors.with_opacity(0.12, ft.Colors.INDIGO),
                offset=ft.Offset(0, 8),
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
                controls=[
                    ft.Container(
                        width=80,
                        height=80,
                        border_radius=24,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.Colors.INDIGO_400, ft.Colors.PURPLE_400],
                        ),
                        alignment=ft.alignment.center,
                        content=ft.Text("📚", size=40),
                    ),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                        controls=[
                            ft.Text("宝宝背单词", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                            ft.Text("每天15个词，轻松学英语", size=14, color=ft.Colors.GREY_500),
                        ],
                    ),
                    ft.Container(height=4),
                    username_input,
                    grade_dropdown,
                    ft.Container(
                        width=320,
                        height=50,
                        border_radius=14,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.center_left,
                            end=ft.alignment.center_right,
                            colors=[ft.Colors.INDIGO_500, ft.Colors.PURPLE_500],
                        ),
                        ink=True,
                        on_click=on_login,
                        alignment=ft.alignment.center,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.ROCKET_LAUNCH, color=ft.Colors.WHITE, size=20),
                                ft.Text("开始学习", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                    ),
                    status_text,
                ],
            ),
        )

        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.Colors.BLUE_50, ft.Colors.INDIGO_50, ft.Colors.PURPLE_50],
            ),
            alignment=ft.alignment.center,
            padding=30,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=24,
                controls=[
                    login_card,
                    recent_list if recent_users else ft.Container(),
                ],
            ),
        )

    # ---------- 主页面 ----------
    def build_main():
        nonlocal today_index, today_words, quiz_mode, quiz_index, quiz_questions

        if is_today_completed(user_data):
            return ft.Container(
                expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[ft.Colors.GREEN_50, ft.Colors.TEAL_50],
                ),
                alignment=ft.alignment.center,
                padding=30,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=24,
                    controls=[
                        ft.Container(
                            width=100,
                            height=100,
                            border_radius=50,
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=[ft.Colors.GREEN_400, ft.Colors.TEAL_400],
                            ),
                            alignment=ft.alignment.center,
                            content=ft.Text("🎉", size=50),
                        ),
                        ft.Text("今日任务已完成！", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                        ft.Text("太棒了，明天再来吧！", size=16, color=ft.Colors.GREY_600),
                        ft.Container(height=8),
                        ft.Container(
                            width=220,
                            height=48,
                            border_radius=14,
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.center_left,
                                end=ft.alignment.center_right,
                                colors=[ft.Colors.PURPLE_500, ft.Colors.PINK_500],
                            ),
                            ink=True,
                            on_click=lambda e: show_calendar(),
                            alignment=ft.alignment.center,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.WHITE, size=20),
                                    ft.Text("查看日历", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                                ],
                            ),
                        ),
                        ft.Container(
                            width=220,
                            height=48,
                            border_radius=14,
                            border=ft.border.all(1.5, ft.Colors.GREY_300),
                            ink=True,
                            on_click=lambda e: logout(),
                            alignment=ft.alignment.center,
                            content=ft.Text("退出登录", size=16, color=ft.Colors.GREY_600),
                        ),
                    ]
                ),
            )

        if not today_words and not quiz_mode:
            return ft.Container(
                expand=True,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[ft.Colors.AMBER_50, ft.Colors.ORANGE_50],
                ),
                alignment=ft.alignment.center,
                padding=30,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=24,
                    controls=[
                        ft.Container(
                            width=100,
                            height=100,
                            border_radius=50,
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=[ft.Colors.AMBER_400, ft.Colors.ORANGE_400],
                            ),
                            alignment=ft.alignment.center,
                            content=ft.Text("🏆", size=50),
                        ),
                        ft.Text("所有单词已学完！", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800),
                        ft.Text("你太厉害了！", size=16, color=ft.Colors.GREY_600),
                        ft.Container(height=8),
                        ft.Container(
                            width=220,
                            height=48,
                            border_radius=14,
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.center_left,
                                end=ft.alignment.center_right,
                                colors=[ft.Colors.INDIGO_500, ft.Colors.PURPLE_500],
                            ),
                            ink=True,
                            on_click=lambda e: reset_all(),
                            alignment=ft.alignment.center,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.REFRESH, color=ft.Colors.WHITE, size=20),
                                    ft.Text("重新开始", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                                ],
                            ),
                        ),
                        ft.Container(
                            width=220,
                            height=48,
                            border_radius=14,
                            border=ft.border.all(1.5, ft.Colors.GREY_300),
                            ink=True,
                            on_click=lambda e: logout(),
                            alignment=ft.alignment.center,
                            content=ft.Text("退出登录", size=16, color=ft.Colors.GREY_600),
                        ),
                    ]
                ),
            )

        if quiz_mode:
            return build_quiz_page()

        if not today_words and not quiz_mode:
            start_quiz()
            return build_quiz_page()

        if today_index >= len(today_words):
            start_quiz()
            return build_quiz_page()

        current_word = today_words[today_index]

        # ----- UI -----
        header = ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=14,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Container(
                                width=32,
                                height=32,
                                border_radius=16,
                                bgcolor=ft.Colors.INDIGO_100,
                                alignment=ft.alignment.center,
                                content=ft.Text(current_user[0].upper() if current_user else "?", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                            ),
                            ft.Text(current_user, size=15, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                        ],
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=10,
                        bgcolor=ft.Colors.BLUE_50,
                        content=ft.Text(f"📚 {user_data['grade']}", size=13, color=ft.Colors.BLUE_700, weight=ft.FontWeight.W_500),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT_OUTLINED,
                        icon_size=20,
                        icon_color=ft.Colors.GREY_400,
                        tooltip="退出",
                        on_click=lambda e: logout(),
                    ),
                ]
            ),
        )

        progress_text = ft.Text(
            f"单词 {today_index + 1} / {len(today_words)}",
            size=14,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.GREY_500,
        )

        progress_bar = ft.ProgressBar(
            width=300,
            height=6,
            value=(today_index + 1) / len(today_words) if today_words else 0,
            color=ft.Colors.INDIGO_400,
            bgcolor=ft.Colors.INDIGO_50,
            border_radius=3,
        )

        # Word card
        emoji_display = ft.Text(
            value=current_word["emoji"],
            size=72,
            text_align=ft.TextAlign.CENTER,
        )

        word_display = ft.Text(
            value=current_word["word"],
            size=44,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.INDIGO_900,
            text_align=ft.TextAlign.CENTER,
        )

        hint_display = ft.Text(
            value=f"{current_word['meaning']}",
            size=22,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER,
        )

        example_display = ft.Text(
            value=f"💬  {current_word['example']}",
            size=15,
            color=ft.Colors.GREY_500,
            text_align=ft.TextAlign.CENTER,
            italic=True,
        )

        pronounce_btn = ft.Container(
            width=56,
            height=56,
            border_radius=28,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.Colors.INDIGO_400, ft.Colors.PURPLE_400],
            ),
            ink=True,
            on_click=lambda e: play_pronunciation(current_word["word"]),
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.3, ft.Colors.INDIGO_400),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Icon(ft.Icons.VOLUME_UP, color=ft.Colors.WHITE, size=28),
        )

        word_card = ft.Container(
            width=340,
            padding=30,
            border_radius=24,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=25,
                color=ft.Colors.with_opacity(0.10, ft.Colors.INDIGO),
                offset=ft.Offset(0, 8),
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Container(
                        width=110,
                        height=110,
                        border_radius=55,
                        gradient=ft.RadialGradient(
                            center=ft.alignment.center,
                            radius=0.8,
                            colors=[ft.Colors.INDIGO_50, ft.Colors.PURPLE_50],
                        ),
                        alignment=ft.alignment.center,
                        content=emoji_display,
                    ),
                    word_display,
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=16, vertical=6),
                        border_radius=12,
                        bgcolor=ft.Colors.AMBER_50,
                        content=hint_display,
                    ),
                    example_display,
                    ft.Container(height=4),
                    pronounce_btn,
                ],
            ),
        )

        # ----- 考试弹窗（拼写）-----
        exam_input = ft.TextField(
            label="输入英文单词",
            hint_text="请输入单词，按回车提交",
            width=300,
            autofocus=True,
            border_color=ft.Colors.INDIGO_300,
            focused_border_color=ft.Colors.INDIGO,
            border_radius=12,
            filled=True,
            fill_color=ft.Colors.INDIGO_50,
            text_size=18,
        )
        exam_result = ft.Text("", size=16, color=ft.Colors.RED, weight=ft.FontWeight.W_600)
        exam_hint = ft.Text("", size=18, color=ft.Colors.INDIGO_700, weight=ft.FontWeight.W_600)

        def check_exam(e=None):
            nonlocal today_index, today_words
            if not today_words or today_index >= len(today_words):
                close_dialog()
                if not today_words:
                    start_quiz()
                    show_main()
                page.update()
                return
            user_input = exam_input.value.strip()
            if not user_input:
                exam_result.value = "⚠️ 请输入单词"
                exam_result.color = ft.Colors.RED
                page.update()
                return
            word = today_words[today_index]
            if user_input.lower() == word["word"].lower():
                exam_result.value = "✅ 正确！"
                exam_result.color = ft.Colors.GREEN
                exam_input.disabled = True
                learned = user_data.get("learned", [])
                if not isinstance(learned, list):
                    learned = []
                if word["word"] not in learned:
                    learned.append(word["word"])
                    user_data["learned"] = learned
                    save_user(current_user, user_data)
                today_words.pop(today_index)
                if today_index >= len(today_words):
                    today_index = len(today_words) - 1
                close_dialog()
                update_main()
                if not today_words:
                    start_quiz()
                    show_main()
            else:
                exam_result.value = "❌ 错误，再试一次"
                exam_result.color = ft.Colors.RED
                exam_input.value = ""
            page.update()

        exam_dialog = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.EDIT_NOTE, color=ft.Colors.INDIGO_600, size=24),
                    ft.Text("单词拼写", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                ],
            ),
            content=ft.Container(
                width=320,
                padding=ft.padding.only(top=8),
                content=ft.Column(
                    width=320,
                    spacing=14,
                    controls=[
                        ft.Text("请拼写下方中文对应的英文单词：", size=14, color=ft.Colors.GREY_500),
                        ft.Container(
                            width=320,
                            padding=ft.padding.symmetric(horizontal=16, vertical=12),
                            border_radius=12,
                            bgcolor=ft.Colors.INDIGO_50,
                            alignment=ft.alignment.center,
                            content=exam_hint,
                        ),
                        exam_input,
                        exam_result,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda e: close_dialog()),
                ft.ElevatedButton(
                    "提交答案",
                    on_click=check_exam,
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.INDIGO_600,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                ),
            ],
            modal=True,
        )

        def show_exam(e):
            nonlocal current_dialog
            if not today_words or today_index >= len(today_words):
                if not today_words and not quiz_mode:
                    start_quiz()
                    show_main()
                return
            word = today_words[today_index]
            exam_hint.value = f"{word['meaning']}"
            exam_input.value = ""
            exam_result.value = ""
            exam_input.disabled = False
            close_dialog()
            page.open(exam_dialog)
            current_dialog = exam_dialog
            page.update()

        exam_btn = ft.Container(
            width=340,
            height=52,
            border_radius=14,
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=[ft.Colors.GREEN_500, ft.Colors.TEAL_500],
            ),
            ink=True,
            on_click=show_exam,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.25, ft.Colors.GREEN_500),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.EDIT_NOTE, color=ft.Colors.WHITE, size=22),
                    ft.Text("考试（通过后进入下一词）", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                ],
            ),
        )

        calendar_btn = ft.Container(
            width=340,
            height=48,
            border_radius=14,
            border=ft.border.all(1.5, ft.Colors.PURPLE_300),
            ink=True,
            on_click=lambda e: show_calendar(),
            alignment=ft.alignment.center,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.PURPLE_600, size=20),
                    ft.Text("学习日历", color=ft.Colors.PURPLE_700, size=16, weight=ft.FontWeight.W_600),
                ],
            ),
        )

        main_column = ft.Column(
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                header,
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                    controls=[progress_text, progress_bar],
                ),
                word_card,
                exam_btn,
                calendar_btn,
            ],
        )

        def update_main():
            if not today_words or today_index >= len(today_words):
                return
            word = today_words[today_index]
            emoji_display.value = word["emoji"]
            word_display.value = word["word"]
            hint_display.value = f"{word['meaning']}"
            example_display.value = f"💬  {word['example']}"
            progress_text.value = f"单词 {today_index + 1} / {len(today_words)}"
            progress_bar.value = (today_index + 1) / len(today_words) if today_words else 0
            page.update()

        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.Colors.BLUE_50, ft.Colors.INDIGO_50, ft.Colors.PURPLE_50],
            ),
            padding=25,
            alignment=ft.alignment.center,
            content=main_column,
        )

    # ---------- 选择题 ----------
    def start_quiz():
        nonlocal quiz_questions, quiz_index, quiz_mode
        learned = user_data.get("learned", [])
        if not isinstance(learned, list):
            learned = []
        if len(learned) < 15:
            all_words = [w["word"] for w in WORD_LIST]
            unlearned = [w for w in all_words if w not in learned]
            sample = learned + unlearned[:15-len(learned)]
        else:
            sample = random.sample(learned, 15)
        questions = []
        for word_str in sample:
            word_data = next((w for w in WORD_LIST if w["word"] == word_str), None)
            if not word_data:
                continue
            other_words = [w["word"] for w in WORD_LIST if w["word"] != word_str]
            if len(other_words) >= 3:
                wrongs = random.sample(other_words, 3)
            else:
                wrongs = other_words + ["apple", "book", "cat"][:3-len(other_words)]
            options = [word_str] + wrongs
            random.shuffle(options)
            questions.append({
                "chinese": word_data["meaning"],
                "correct": word_str,
                "options": options
            })
        random.shuffle(questions)
        quiz_questions = questions[:15]
        quiz_index = 0
        quiz_mode = True

    def build_quiz_page():
        nonlocal quiz_index, quiz_questions
        if quiz_index >= len(quiz_questions):
            user_data["completed_dates"].append(get_today_date())
            save_user(current_user, user_data)
            quiz_mode = False
            show_main()
            return

        q = quiz_questions[quiz_index]
        option_btns = []
        for opt in q["options"]:
            btn = ft.Container(
                width=300,
                height=50,
                border_radius=14,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1.5, ft.Colors.GREY_200),
                ink=True,
                on_click=lambda e, w=opt: check_quiz(w),
                alignment=ft.alignment.center,
                content=ft.Text(opt, size=17, color=ft.Colors.GREY_800, weight=ft.FontWeight.W_500),
            )
            option_btns.append(btn)

        quiz_status = ft.Text(
            f"选择题 {quiz_index+1} / {len(quiz_questions)}",
            size=14,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.GREY_500,
        )

        quiz_progress = ft.ProgressBar(
            width=300,
            height=6,
            value=(quiz_index + 1) / len(quiz_questions),
            color=ft.Colors.PURPLE_400,
            bgcolor=ft.Colors.PURPLE_50,
            border_radius=3,
        )

        chinese_display = ft.Text(
            q["chinese"],
            size=36,
            color=ft.Colors.INDIGO_900,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        result_text = ft.Text("", size=16, color=ft.Colors.RED, weight=ft.FontWeight.W_600)

        def check_quiz(selected):
            nonlocal quiz_index
            if selected == q["correct"]:
                result_text.value = "✅ 正确！"
                result_text.color = ft.Colors.GREEN
                for btn in option_btns:
                    btn.disabled = True
                page.update()
                threading.Timer(0.5, next_quiz).start()
            else:
                result_text.value = "❌ 错误，再选一次"
                result_text.color = ft.Colors.RED
                page.update()

        def next_quiz():
            nonlocal quiz_index
            quiz_index += 1
            page.clean()
            page.add(build_quiz_page() if quiz_index < len(quiz_questions) else build_main())

        question_card = ft.Container(
            width=340,
            padding=36,
            border_radius=24,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=25,
                color=ft.Colors.with_opacity(0.10, ft.Colors.PURPLE),
                offset=ft.Offset(0, 8),
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    ft.Container(
                        width=64,
                        height=64,
                        border_radius=32,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.Colors.PURPLE_400, ft.Colors.PINK_400],
                        ),
                        alignment=ft.alignment.center,
                        content=ft.Icon(ft.Icons.QUIZ, color=ft.Colors.WHITE, size=32),
                    ),
                    ft.Text("选择正确的英文单词", size=14, color=ft.Colors.GREY_500),
                    chinese_display,
                ],
            ),
        )

        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.Colors.PURPLE_50, ft.Colors.INDIGO_50, ft.Colors.BLUE_50],
            ),
            padding=25,
            alignment=ft.alignment.center,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        width=340,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Container(
                                        width=32,
                                        height=32,
                                        border_radius=16,
                                        bgcolor=ft.Colors.PURPLE_100,
                                        alignment=ft.alignment.center,
                                        content=ft.Text(current_user[0].upper() if current_user else "?", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                                    ),
                                    ft.Text(current_user, size=15, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800),
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.LOGOUT_OUTLINED,
                                icon_size=20,
                                icon_color=ft.Colors.GREY_400,
                                tooltip="退出",
                                on_click=lambda e: logout(),
                            ),
                        ]
                    ),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=[quiz_status, quiz_progress],
                    ),
                    question_card,
                    ft.Column(controls=option_btns, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    result_text,
                ],
            ),
        )

    # ---------- 日历 ----------
    def show_calendar():
        close_dialog()
        now = datetime.now()
        year, month = now.year, now.month
        first_day = datetime(year, month, 1)
        start_weekday = first_day.weekday()
        if month == 12:
            next_month = datetime(year+1, 1, 1)
        else:
            next_month = datetime(year, month+1, 1)
        days_in_month = (next_month - first_day).days

        completed_dates = set(user_data.get("completed_dates", []))
        grid = ft.GridView(expand=1, runs_count=7, max_extent=50,
                           child_aspect_ratio=1.0, spacing=5, run_spacing=5)
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        weekday_colors = [ft.Colors.RED_400, ft.Colors.ORANGE_400, ft.Colors.AMBER_400,
                          ft.Colors.GREEN_400, ft.Colors.TEAL_400, ft.Colors.BLUE_400, ft.Colors.PURPLE_400]
        for i, wd in enumerate(weekdays):
            grid.controls.append(ft.Container(
                content=ft.Text(wd, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                alignment=ft.alignment.center,
                bgcolor=weekday_colors[i],
                border_radius=8,
            ))
        for _ in range(start_weekday):
            grid.controls.append(ft.Container())

        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            is_completed = date_str in completed_dates
            is_today = date_str == get_today_date()
            if is_completed:
                color = ft.Colors.GREEN_500
                text_color = ft.Colors.WHITE
            elif is_today:
                color = ft.Colors.INDIGO_50
                text_color = ft.Colors.INDIGO_700
            else:
                color = ft.Colors.GREY_50
                text_color = ft.Colors.GREY_600
            grid.controls.append(ft.Container(
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    controls=[
                        ft.Text(str(day), size=15, color=text_color, weight=ft.FontWeight.W_600 if (is_completed or is_today) else ft.FontWeight.NORMAL),
                        ft.Text("✓", size=10, color=ft.Colors.WHITE) if is_completed else ft.Container(),
                    ],
                ),
                alignment=ft.alignment.center,
                bgcolor=color,
                border_radius=8,
                border=ft.border.all(2, ft.Colors.INDIGO_400) if is_today else None,
            ))

        dialog = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.PURPLE_600, size=24),
                    ft.Text(f"{year}年{month}月 学习日历", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                ],
            ),
            content=ft.Container(
                width=400,
                height=340,
                content=ft.Column(
                    controls=[
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.Row(spacing=4, controls=[
                                    ft.Container(width=12, height=12, border_radius=3, bgcolor=ft.Colors.GREEN_500),
                                    ft.Text("已完成", size=12, color=ft.Colors.GREY_600),
                                ]),
                                ft.Row(spacing=4, controls=[
                                    ft.Container(width=12, height=12, border_radius=3, bgcolor=ft.Colors.INDIGO_50, border=ft.border.all(2, ft.Colors.INDIGO_400)),
                                    ft.Text("今天", size=12, color=ft.Colors.GREY_600),
                                ]),
                                ft.Row(spacing=4, controls=[
                                    ft.Container(width=12, height=12, border_radius=3, bgcolor=ft.Colors.GREY_50),
                                    ft.Text("未完成", size=12, color=ft.Colors.GREY_600),
                                ]),
                            ],
                        ),
                        ft.Container(height=8),
                        grid,
                    ],
                ),
            ),
            actions=[
                ft.ElevatedButton(
                    "关闭",
                    on_click=lambda e: close_calendar_dialog(),
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.PURPLE_600,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                ),
            ],
        )

        def close_calendar_dialog():
            nonlocal current_dialog
            if current_dialog:
                page.close(current_dialog)
                current_dialog = None
            page.update()

        page.open(dialog)
        current_dialog = dialog
        page.update()

    # ---------- 辅助 ----------
    def reset_all():
        nonlocal user_data, today_words, today_index, quiz_mode
        user_data["learned"] = []
        user_data["completed_dates"] = []
        save_user(current_user, user_data)
        prepare_today()
        quiz_mode = False
        show_main()

    def logout():
        nonlocal current_user, user_data
        current_user = None
        user_data = None
        show_login()

    show_login()

ft.app(target=main)
