"""Install a current-user protocol handler; never overwrite a different app."""
import json
from pathlib import Path
import subprocess
import sys
import winreg

ROOT = Path(__file__).resolve().parent
KEY = r'Software\Classes\videosummarizer'
COMMAND_KEY = KEY + r'\shell\open\command'
COMMAND = subprocess.list2cmdline([str(ROOT / '.venv' / 'Scripts' / 'pythonw.exe'),
                                  str(ROOT / 'bookmark_launcher.py')]) + ' "%1"'


def existing_command():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as key:
            return winreg.QueryValueEx(key, '')[0]
    except FileNotFoundError:
        return None


def install():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY):
            if existing_command() != COMMAND:
                raise RuntimeError('videosummarizer 協議已被其他設定使用；未覆蓋。')
    except FileNotFoundError:
        pass
    for file in (ROOT / '.venv' / 'Scripts' / 'pythonw.exe', ROOT / 'bookmark_launcher.py'):
        if not file.is_file():
            raise RuntimeError('缺少必要檔案：' + str(file))
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEY) as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, 'URL:VideoSummarizer')
        winreg.SetValueEx(key, 'URL Protocol', 0, winreg.REG_SZ, '')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, COMMAND)
    assert existing_command() == COMMAND
    print('已註冊目前 Windows 使用者的 videosummarizer://open 連結。')


def remove():
    if existing_command() is None:
        print('沒有本專案的協議註冊。')
        return
    if existing_command() != COMMAND:
        raise RuntimeError('協議已由其他設定接管；未刪除。')
    for key in (COMMAND_KEY, KEY + r'\shell\open', KEY + r'\shell', KEY):
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
    print('已移除本專案的連結註冊；模型及摘要檔案保留。')


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['--remove']:
            remove()
        elif not sys.argv[1:]:
            install()
        else:
            raise ValueError('只接受 --remove 或不帶參數。')
    except Exception as exc:
        print('註冊失敗：' + str(exc))
        sys.exit(1)
