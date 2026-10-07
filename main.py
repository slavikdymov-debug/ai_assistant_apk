# -*- coding: utf-8 -*-
import os
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_CrDFmxeUc9Y1@ep-nameless-shape-b1l49djd-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require"
os.environ["DEEPSEEK_API_KEY"] = "sk-f403433880cd42ed9af2280ab02ece64"

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.metrics import dp

import db
from db import check_password

BG = (0.10, 0.12, 0.16, 1)
FG = (0.95, 0.95, 0.95, 1)
ACCENT = (0.20, 0.60, 0.95, 1)
DANGER = (0.90, 0.30, 0.30, 1)
Window.clearcolor = BG

class State:
    user = None
    users = {}
    categories = {}

STATE = State()

def load_all():
    try:
        STATE.users = db.load_users()
        STATE.categories = db.load_categories()
    except Exception as e:
        print(f"Ошибка загрузки: {e}")

class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(10))
        layout.add_widget(Label(text="AI Assistant 3D", font_size=dp(22), color=FG))
        layout.add_widget(Label(text="Логин:", size_hint=(1,0.1), color=FG))
        self.login_in = TextInput(multiline=False, size_hint=(1,0.12))
        layout.add_widget(self.login_in)
        layout.add_widget(Label(text="Пароль:", size_hint=(1,0.1), color=FG))
        self.pass_in = TextInput(multiline=False, password=True, size_hint=(1,0.12))
        layout.add_widget(self.pass_in)
        self.status = Label(text="", size_hint=(1,0.1), color=DANGER)
        layout.add_widget(self.status)
        btn = Button(text="Войти", size_hint=(1,0.15), background_color=ACCENT, font_size=dp(18))
        btn.bind(on_press=self.do_login)
        layout.add_widget(btn)
        self.add_widget(layout)

    def do_login(self, *args):
        u = STATE.users.get(self.login_in.text.strip())
        if u and check_password(self.pass_in.text, u["password_hash"]):
            STATE.user = u
            self.manager.current = "main"
        else:
            self.status.text = "Неверный логин или пароль"

class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.build()

    def build(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        u = STATE.user or {}
        top = BoxLayout(size_hint=(1,0.12))
        top.add_widget(Label(text=u.get("full_name",""), font_size=dp(16), color=FG))
        lo = Button(text="Выйти", size_hint=(0.3,1), background_color=DANGER)
        lo.bind(on_press=self.logout)
        top.add_widget(lo)
        layout.add_widget(top)
        menu = GridLayout(cols=1, spacing=dp(8), size_hint=(1,0.88))
        for name, screen in [("Принтеры","printers"),("Товары","products"),("Ярмарка","fair"),("Помощник","assistant"),("Чат","chat"),("Кабинет","profile"),("Настройки","settings")]:
            b = Button(text=name, font_size=dp(16), background_color=ACCENT)
            b.bind(on_press=lambda x, s=screen: setattr(self.manager, "current", s))
            menu.add_widget(b)
        layout.add_widget(menu)
        self.add_widget(layout)

    def logout(self, *args):
        STATE.user = None
        self.manager.current = "login"

class ProductsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.build()

    def build(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        top = BoxLayout(size_hint=(1,0.1))
        top.add_widget(Label(text="Товары", font_size=dp(20), color=FG))
        back = Button(text="Назад", size_hint=(0.3,1))
        back.bind(on_press=lambda x: setattr(self.manager, "current", "main"))
        top.add_widget(back)
        layout.add_widget(top)
        scroll = ScrollView(size_hint=(1,0.9))
        self.box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self.box.bind(minimum_height=self.box.setter("height"))
        scroll.add_widget(self.box)
        layout.add_widget(scroll)
        self.add_widget(layout)
        self.refresh()

    def refresh(self):
        self.box.clear_widgets()
        try:
            STATE.categories = db.load_categories()
        except Exception as e:
            self.box.add_widget(Label(text=f"Ошибка: {e}", color=DANGER))
            return
        for cat_name, data in STATE.categories.items():
            self.box.add_widget(Label(text=cat_name, size_hint_y=None, height=dp(40), color=ACCENT, bold=True))
            for item in data["items"]:
                self.box.add_widget(Label(text=f"  {item['name']} - {item['price']} RUB", size_hint_y=None, height=dp(35), color=FG))

class ChatScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.channel = "общий"
        self.build()

    def build(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        top = BoxLayout(size_hint=(1,0.1))
        top.add_widget(Label(text="Чат", font_size=dp(20), color=FG))
        back = Button(text="Назад", size_hint=(0.3,1))
        back.bind(on_press=lambda x: setattr(self.manager, "current", "main"))
        top.add_widget(back)
        layout.add_widget(top)
        self.spinner = Spinner(text="общий", values=["общий","смена","техотдел","менеджеры"], size_hint=(1,0.12))
        self.spinner.bind(text=self.on_channel)
        layout.add_widget(self.spinner)
        scroll = ScrollView(size_hint=(1,0.65))
        self.box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self.box.bind(minimum_height=self.box.setter("height"))
        scroll.add_widget(self.box)
        layout.add_widget(scroll)
        bottom = BoxLayout(size_hint=(1,0.15), spacing=dp(5))
        self.entry = TextInput(multiline=False, size_hint=(0.75,1))
        bottom.add_widget(self.entry)
        send = Button(text="->", size_hint=(0.25,1), background_color=ACCENT)
        send.bind(on_press=self.send)
        bottom.add_widget(send)
        layout.add_widget(bottom)
        self.add_widget(layout)
        self.refresh()

    def on_channel(self, sp, text):
        self.channel = text
        self.refresh()

    def refresh(self):
        self.box.clear_widgets()
        try:
            msgs = db.load_messages(self.channel)
        except Exception as e:
            self.box.add_widget(Label(text=f"Ошибка: {e}", color=DANGER))
            return
        for m in msgs[-50:]:
            self.box.add_widget(Label(text=f"{m['author']}: {m['text']}", size_hint_y=None, height=dp(35), color=FG))

    def send(self, *args):
        text = self.entry.text.strip()
        if not text or not STATE.user: return
        self.entry.text = ""
        try:
            db.add_message(self.channel, STATE.user["username"], STATE.user["role"], text)
        except Exception as e:
            print(e)
        self.refresh()

class SimpleScreen(Screen):
    def __init__(self, title="Экран", **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        top = BoxLayout(size_hint=(1,0.1))
        top.add_widget(Label(text=title, font_size=dp(20), color=FG))
        back = Button(text="Назад", size_hint=(0.3,1))
        back.bind(on_press=lambda x: setattr(self.manager, "current", "main"))
        top.add_widget(back)
        layout.add_widget(top)
        layout.add_widget(Label(text="В разработке", color=FG))
        self.add_widget(layout)

class AssistantApp(App):
    def build(self):
        self.title = "AI Assistant 3D"
        load_all()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(ProductsScreen(name="products"))
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(SimpleScreen(title="Принтеры", name="printers"))
        sm.add_widget(SimpleScreen(title="Ярмарка", name="fair"))
        sm.add_widget(SimpleScreen(title="Помощник", name="assistant"))
        sm.add_widget(SimpleScreen(title="Кабинет", name="profile"))
        sm.add_widget(SimpleScreen(title="Настройки", name="settings"))
        return sm

if __name__ == "__main__":
    AssistantApp().run()