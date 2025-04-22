import os
import subprocess
import sys
import eel
import logging
import ctypes
import win32gui
import win32con
import psutil
import json
import winreg
import winsound
import platform
import argparse
import wmi
import GPUtil
import shutil
import pyadl

PROFILE_DIR = "profiles"
eel.init("web")

# Проверка на Windows
if platform.system() != "Windows":
    print("Эта программа поддерживает только Windows!")
    sys.exit(1)

# Настройка логирования
parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true", help="Включить отладочный вывод")
args = parser.parse_args()
logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="aichi_boost.log",
)
logger = logging.getLogger(__name__)

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)

@eel.expose
def play_click_sound():
    try:
        winsound.PlaySound(resource_path("opt/sounds/click.wav"), winsound.SND_ASYNC)
    except Exception as e:
        logger.error(f"Ошибка воспроизведения звука: {e}")

background_path = resource_path("opt/background/fon.png")
if not os.path.exists(background_path):
    logger.error(f"Фон не найден: {background_path}")

def check_registry_value(hive, key_path, value_name):
    try:
        key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return value
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Ошибка проверки реестра: {e}")
        return None

def toggle_feature(reg_path, value_name, value, enable_text, disable_text):
    try:
        subprocess.run(
            ["reg", "add", reg_path, "/v", value_name, "/t", "REG_DWORD", "/d", str(value), "/f"],
            check=True,
            shell=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Registry updated: {reg_path} {value_name} = {value}")
        return enable_text if value else disable_text
    except subprocess.CalledProcessError as e:
        logger.error(f"Error updating registry: {e.stderr}")
        return f"Ошибка изменения реестра: {e.stderr}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Ошибка: {str(e)}"

@eel.expose
def activate_windows():
    try:
        logger.warning("Использование внешнего KMS-сервера для активации Windows может быть небезопасным. Убедитесь, что вы доверяете серверу.")
        kms_keys = {
            "Windows 11 Home": "TX9XD-98N7V-6WMQ6-BX7FG-H8Q99",
            "Windows 11 Pro": "W269N-WFGWX-YVC9B-4J6C9-T83GX",
            "Windows 11 Enterprise": "NPPR9-FWDCX-D2C8J-H872K-2YT43",
            "Windows 10 Home": "TX9XD-98N7V-6WMQ6-BX7FG-H8Q99",
            "Windows 10 Pro": "W269N-WFGWX-YVC9B-4J6C9-T83GX",
            "Windows 10 Enterprise": "NPPR9-FWDCX-D2C8J-H872K-2YT43",
            "Windows 8.1 Core": "M9Q9P-WN3C3-8P4QH-4W8X9-8WQ9M",
            "Windows 8.1 Pro": "GCRJD-8NW9H-F2CDX-CCM8D-9D6T9",
            "Windows 8.1 Enterprise": "MHF9N-XY6XB-WVXMC-BTDCT-MKKG7",
            "Windows 7 Professional": "FJ82H-XT6CR-J8D7P-XQJJ2-GPDD4",
            "Windows 7 Enterprise": "33PXH-7Y6KF-2VJC9-XBBR8-HVTHH",
            "Windows 7 Ultimate": "D4F6K-QK3RD-TMVMJ-BBMRX-3MBMV",
        }
        kms_server = "kms.digiboy.ir"
        version_output = subprocess.run(["wmic", "os", "get", "caption"], capture_output=True, text=True, shell=True).stdout
        key = None
        for os_version, os_key in kms_keys.items():
            if os_version in version_output:
                key = os_key
                break
        if not key:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as reg_key:
                product_name = winreg.QueryValueEx(reg_key, "ProductName")[0]
                for os_version, os_key in kms_keys.items():
                    if os_version in product_name:
                        key = os_key
                        break
        if not key:
            return "Ошибка: Версия Windows не поддерживается"
        subprocess.run(["slmgr", "/skms", kms_server], check=True, shell=True, capture_output=True)
        subprocess.run(["slmgr", "/ipk", key], check=True, shell=True, capture_output=True)
        subprocess.run(["slmgr", "/ato"], check=True, shell=True, capture_output=True)
        play_click_sound()
        return "Windows успешно активирован!"
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка активации Windows: {e.stderr}, код ошибки: {e.returncode}")
        return f"Ошибка активации: {e.stderr or 'Неизвестная ошибка'} (код: {e.returncode})"
    except Exception as e:
        logger.error(f"Неизвестная ошибка активации: {e}")
        return f"Ошибка активации: {str(e)}"

@eel.expose
def toggle_cortana(enabled):
    settings = load_settings()
    settings["cortana"] = enabled
    result = toggle_feature(
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search",
        "AllowCortana",
        1 if enabled else 0,
        "Cortana включена",
        "Cortana отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_game_mode(enabled):
    settings = load_settings()
    settings["gameMode"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\GameBar",
        "AllowAutoGameMode",
        1 if enabled else 0,
        "Игровой режим включён",
        "Игровой режим отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_game_bar(enabled):
    settings = load_settings()
    settings["gameBar"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR",
        "AppCaptureEnabled",
        1 if enabled else 0,
        "Game Bar включён",
        "Game Bar отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_windows_update(enabled):
    settings = load_settings()
    settings["updates"] = enabled
    result = toggle_feature(
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU",
        "NoAutoUpdate",
        0 if enabled else 1,
        "Обновления Windows включены",
        "Обновления Windows отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_touch_input(enabled):
    settings = load_settings()
    settings["touch"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Wisp\Touch",
        "TouchGate",
        1 if enabled else 0,
        "Сенсорный ввод включён",
        "Сенсорный ввод отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_cloud_clipboard(enabled):
    settings = load_settings()
    settings["clipboard"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Clipboard",
        "EnableClipboardHistory",
        1 if enabled else 0,
        "Облачный буфер включён",
        "Облачный буфер отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_sticky_keys(enabled):
    settings = load_settings()
    settings["stickyKeys"] = enabled
    result = toggle_feature(
        r"HKCU\Control Panel\Accessibility\StickyKeys",
        "Flags",
        510 if enabled else 506,
        "Залипание клавиш включено",
        "Залипание клавиш отключено",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_menu_delay(enabled):
    settings = load_settings()
    settings["menuDelay"] = enabled
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "MenuShowDelay", 0, winreg.REG_SZ, "400" if enabled else "0")
        winreg.CloseKey(key)
        save_settings(settings)
        play_click_sound()
        return "Задержка меню включена" if enabled else "Задержка меню отключена"
    except Exception as e:
        logger.error(f"Ошибка изменения задержки меню: {e}")
        return f"Ошибка: {e}"

@eel.expose
def toggle_smart_screen(enabled):
    settings = load_settings()
    settings["smartScreen"] = enabled
    result = toggle_feature(
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System",
        "EnableSmartScreen",
        1 if enabled else 0,
        "Smart Screen включён",
        "Smart Screen отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_mouse_acceleration(enabled):
    settings = load_settings()
    settings["mouseAcceleration"] = enabled
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "MouseSensitivity", 0, winreg.REG_SZ, "10")
        winreg.SetValueEx(key, "MouseThreshold1", 0, winreg.REG_SZ, "6" if enabled else "0")
        winreg.SetValueEx(key, "MouseThreshold2", 0, winreg.REG_SZ, "10" if enabled else "0")
        winreg.CloseKey(key)
        save_settings(settings)
        play_click_sound()
        return "Акселерация мыши включена" if enabled else "Акселерация мыши отключена"
    except Exception as e:
        logger.error(f"Ошибка изменения акселерации мыши: {e}")
        return f"Ошибка: {e}"

@eel.expose
def toggle_protection_notifications(enabled):
    settings = load_settings()
    settings["protectionNotifications"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\Security Health\State",
        "AccountProtectionNotification",
        1 if enabled else 0,
        "Уведомления защиты включены",
        "Уведомления защиты отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_transparency(enabled):
    settings = load_settings()
    settings["transparency"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        "EnableTransparency",
        1 if enabled else 0,
        "Прозрачность включена",
        "Прозрачность отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def optimize_system():
    try:
        # Удаление временных файлов
        temp_dirs = [os.path.expandvars("%temp%"), os.path.expandvars("%systemroot%\\Temp")]
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir, topdown=False):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            os.remove(file_path)
                            logger.info(f"Удален файл: {file_path}")
                        except (PermissionError, OSError) as pe:
                            logger.warning(f"Нет доступа к файлу {file_path}: {pe}")
                            continue
                    for dir in dirs:
                        try:
                            dir_path = os.path.join(root, dir)
                            shutil.rmtree(dir_path, ignore_errors=True)
                            logger.info(f"Удалена директория: {dir_path}")
                        except (PermissionError, OSError) as pe:
                            logger.warning(f"Нет доступа к директории {dir_path}: {pe}")
                            continue
        # Отключение телеметрии
        try:
            result = subprocess.run(
                ["sc", "config", "DiagTrack", "start=", "disabled"],
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Команда отключения телеметрии выполнена: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка отключения телеметрии: {e.stderr}")
            return f"Ошибка отключения телеметрии: {e.stderr or 'Неизвестная ошибка'}"
        play_click_sound()
        return "Система оптимизирована"
    except PermissionError as pe:
        logger.error(f"Ошибка доступа: {pe}")
        return "Ошибка: Нет доступа к временным файлам, запустите от имени администратора"
    except Exception as e:
        logger.error(f"Общая ошибка оптимизации: {e}")
        return f"Ошибка оптимизации: {str(e)}"

@eel.expose
def set_best_performance(enabled):
    settings = load_settings()
    settings["bestPerformance"] = enabled
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(
            key,
            "UserPreferencesMask",
            0,
            winreg.REG_BINARY,
            bytes([0x90, 0x12, 0x03, 0x80]) if enabled else bytes([0x9E, 0x12, 0x03, 0x80]),
        )
        winreg.CloseKey(key)
        save_settings(settings)
        play_click_sound()
        return "Наилучшее быстродействие включено" if enabled else "Наилучшее быстродействие отключено"
    except Exception as e:
        logger.error(f"Ошибка изменения производительности: {e}")
        return f"Ошибка: {e}"

@eel.expose
def toggle_text_shadows(enabled):
    settings = load_settings()
    settings["textShadows"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
        "ListviewShadow",
        1 if enabled else 0,
        "Тени на тексте включены",
        "Тени на тексте отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_thumbnail_previews(enabled):
    settings = load_settings()
    settings["thumbnails"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
        "IconsOnly",
        0 if enabled else 1,
        "Эскизы значков включены",
        "Эскизы значков отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_animations(enabled):
    settings = load_settings()
    settings["animations"] = enabled
    result = toggle_feature(
        r"HKCU\Control Panel\Desktop\WindowMetrics",
        "MinAnimate",
        1 if enabled else 0,
        "Анимации включены",
        "Анимации отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_unnecessary_services(enabled):
    settings = load_settings()
    settings["unnecessaryServices"] = enabled
    try:
        services = ["dmwappushservice", "MapsBroker"]
        for service in services:
            result = subprocess.run(
                ["sc", "query", service],
                capture_output=True,
                text=True,
                shell=True
            )
            if "SERVICE_NAME" in result.stdout:
                subprocess.run(
                    ["sc", "config", service, "start=", "auto" if enabled else "disabled"],
                    check=True,
                    shell=True,
                    capture_output=True,
                )
        save_settings(settings)
        play_click_sound()
        return "Ненужные службы включены" if enabled else "Ненужные службы отключены"
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка переключения служб: {e.stderr}")
        return f"Ошибка: {e.stderr}"
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return f"Ошибка: {e}"

@eel.expose
def toggle_driver_autoupdate(enabled):
    settings = load_settings()
    settings["driverAutoupdate"] = enabled
    result = toggle_feature(
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate",
        "ExcludeWUDriversInQualityUpdate",
        0 if enabled else 1,
        "Автообновление драйверов включено",
        "Автообновление драйверов отключено",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_telemetry(enabled):
    settings = load_settings()
    settings["telemetry"] = enabled
    result = toggle_feature(
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
        "AllowTelemetry",
        1 if enabled else 0,
        "Телеметрия включена",
        "Телеметрия отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_office_telemetry(enabled):
    settings = load_settings()
    settings["officeTelemetry"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Policies\Microsoft\Office\16.0\osm",
        "EnableLogging",
        1 if enabled else 0,
        "Телеметрия Office включена",
        "Телеметрия Office отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_firefox_telemetry(enabled):
    settings = load_settings()
    settings["firefoxTelemetry"] = enabled
    save_settings(settings)
    play_click_sound()
    return "Телеметрия Firefox включена" if enabled else "Телеметрия Firefox отключена (настройте в about:config вручную)"

@eel.expose
def toggle_chrome_telemetry(enabled):
    settings = load_settings()
    settings["chromeTelemetry"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Policies\Google\Chrome",
        "MetricsReportingEnabled",
        1 if enabled else 0,
        "Телеметрия Chrome включена",
        "Телеметрия Chrome отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_nvidia_telemetry(enabled):
    settings = load_settings()
    settings["nvidiaTelemetry"] = enabled
    result = toggle_feature(
        r"HKLM\SOFTWARE\NVIDIA Corporation\Global\FTS",
        "EnableTelemetry",
        1 if enabled else 0,
        "Телеметрия NVIDIA включена",
        "Телеметрия NVIDIA отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_visualstudio_telemetry(enabled):
    settings = load_settings()
    settings["visualStudioTelemetry"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\VisualStudio\Telemetry",
        "TurnOffTelemetry",
        0 if enabled else 1,
        "Телеметрия Visual Studio включена",
        "Телеметрия Visual Studio отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def set_high_performance(enabled):
    settings = load_settings()
    if enabled:
        settings["power_plan"] = "high"
        subprocess.run(
            ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
            check=True,
            shell=True,
            capture_output=True,
        )
        save_settings(settings)
        play_click_sound()
        return "Высокая производительность"
    else:
        settings["power_plan"] = "balanced"
        subprocess.run(
            ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
            check=True,
            shell=True,
            capture_output=True,
        )
        save_settings(settings)
        play_click_sound()
        return "Схема сбалансирована"

@eel.expose
def set_balanced(enabled):
    settings = load_settings()
    if enabled:
        settings["power_plan"] = "balanced"
        subprocess.run(
            ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
            check=True,
            shell=True,
            capture_output=True,
        )
        save_settings(settings)
        play_click_sound()
        return "Сбалансированная"
    else:
        settings["power_plan"] = "balanced"
        save_settings(settings)
        return "Схема осталась сбалансированной"

@eel.expose
def set_power_saving(enabled):
    settings = load_settings()
    if enabled:
        settings["power_plan"] = "power_saving"
        subprocess.run(
            ["powercfg", "/setactive", "a1841308-3541-4fab-bc81-f71556f20b4a"],
            check=True,
            shell=True,
            capture_output=True,
        )
        save_settings(settings)
        play_click_sound()
        return "Экономия энергии"
    else:
        settings["power_plan"] = "balanced"
        subprocess.run(
            ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"],
            check=True,
            shell=True,
            capture_output=True,
        )
        save_settings(settings)
        play_click_sound()
        return "Схема сбалансирована"

@eel.expose
def toggle_app_access_to_device_list(enabled):
    settings = load_settings()
    settings["deviceList"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\deviceList",
        "Value",
        1 if enabled else 0,
        "Список устройств включён",
        "Список устройств отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_sync_with_wireless(enabled):
    settings = load_settings()
    settings["wirelessSync"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\broadFileSystemAccess",
        "Value",
        1 if enabled else 0,
        "Синхронизация с беспроводными включена",
        "Синхронизация с беспроводными отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_analytics(enabled):
    settings = load_settings()
    settings["analytics"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\appDiagnostics",
        "Value",
        1 if enabled else 0,
        "Аналитика включена",
        "Аналитика отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_contacts(enabled):
    settings = load_settings()
    settings["contacts"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\contacts",
        "Value",
        1 if enabled else 0,
        "Контакты включены",
        "Контакты отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_calendar(enabled):
    settings = load_settings()
    settings["calendar"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\appointments",
        "Value",
        1 if enabled else 0,
        "Календарь включён",
        "Календарь отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_call_history(enabled):
    settings = load_settings()
    settings["callHistory"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\phoneCallHistory",
        "Value",
        1 if enabled else 0,
        "Журнал вызовов включён",
        "Журнал вызовов отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_email(enabled):
    settings = load_settings()
    settings["email"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\email",
        "Value",
        1 if enabled else 0,
        "Электронная почта включена",
        "Электронная почта отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_tasks(enabled):
    settings = load_settings()
    settings["tasks"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\userDataTasks",
        "Value",
        1 if enabled else 0,
        "Задачи включены",
        "Задачи отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_messaging(enabled):
    settings = load_settings()
    settings["messaging"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\chat",
        "Value",
        1 if enabled else 0,
        "Сообщения включены",
        "Сообщения отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_radio(enabled):
    settings = load_settings()
    settings["radio"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\radios",
        "Value",
        1 if enabled else 0,
        "Радио включено",
        "Радио отключено",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_bluetooth(enabled):
    settings = load_settings()
    settings["bluetooth"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\bluetooth",
        "Value",
        1 if enabled else 0,
        "Bluetooth включён",
        "Bluetooth отключён",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_documents(enabled):
    settings = load_settings()
    settings["documents"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\documentsLibrary",
        "Value",
        1 if enabled else 0,
        "Документы включены",
        "Документы отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_pictures(enabled):
    settings = load_settings()
    settings["pictures"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\picturesLibrary",
        "Value",
        1 if enabled else 0,
        "Изображения включены",
        "Изображения отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_videos(enabled):
    settings = load_settings()
    settings["videos"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\videosLibrary",
        "Value",
        1 if enabled else 0,
        "Видео включены",
        "Видео отключены",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def toggle_app_access_to_filesystem(enabled):
    settings = load_settings()
    settings["filesystem"] = enabled
    result = toggle_feature(
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\broadFileSystemAccess",
        "Value",
        1 if enabled else 0,
        "Файловая система включена",
        "Файловая система отключена",
    )
    if "Ошибка" not in result:
        save_settings(settings)
        play_click_sound()
    return result

@eel.expose
def get_autostart_programs():
    try:
        settings = load_settings()
        autostart_settings = settings.get("autostart", {})
        programs = []
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                if name in autostart_settings:
                    enabled = autostart_settings[name]["enabled"]
                    path = autostart_settings[name]["path"]
                else:
                    enabled = True
                    path = value
                programs.append({"name": name, "path": path, "enabled": enabled})
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
        return programs
    except Exception as e:
        logger.error(f"Ошибка получения программ автозапуска: {e}")
        return []

@eel.expose
def toggle_autostart(name, enabled):
    try:
        settings = load_settings()
        autostart_settings = settings.get("autostart", {})

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        if name in autostart_settings:
            path = autostart_settings[name]["path"]
        else:
            try:
                path = winreg.QueryValueEx(key, name)[0]
            except FileNotFoundError:
                path = ""

        if enabled:
            if not path:
                winreg.CloseKey(key)
                return f"Ошибка: Путь для {name} не указан"
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, path)
        else:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass

        winreg.CloseKey(key)

        autostart_settings[name] = {"enabled": enabled, "path": path}
        settings["autostart"] = autostart_settings
        save_settings(settings)
        play_click_sound()
        return f"Автозапуск для {name} {'включён' if enabled else 'отключён'}"
    except Exception as e:
        logger.error(f"Ошибка переключения автозапуска: {e}")
        return f"Ошибка: {e}"

@eel.expose
def get_profiles():
    try:
        profiles_dir = "profiles"
        absolute_profiles_dir = os.path.abspath(profiles_dir)
        logger.info(f"Проверка папки профилей: {absolute_profiles_dir}")

        if not os.path.exists(profiles_dir):
            logger.warning(f"Папка {absolute_profiles_dir} не существует, создаем её")
            os.makedirs(profiles_dir, exist_ok=True)
            return []

        profiles = [f[:-5] for f in os.listdir(profiles_dir) if f.endswith(".json")]
        logger.info(f"Найдено профилей: {profiles}")
        return profiles
    except Exception as e:
        logger.error(f"Ошибка получения списка профилей: {e}")
        return []

@eel.expose
def get_performance_score():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage("/").percent
        score = max(0, 100 - (cpu_usage + ram_usage + disk_usage) // 3)
        return int(score)
    except Exception as e:
        logger.error(f"Ошибка получения производительности: {e}")
        return 0

@eel.expose
def create_restore_point():
    try:
        c = wmi.WMI()
        result = c.Win32_SystemRestore.CreateRestorePoint("AICHI BOOST Restore Point", 0, 100)
        if result[0] == 0:
            play_click_sound()
            return "Точка восстановления создана"
        else:
            logger.error(f"Ошибка создания точки восстановления: код {result[0]}")
            return "Ошибка создания точки восстановления"
    except Exception as e:
        logger.error(f"Ошибка создания точки восстановления: {e}")
        return f"Ошибка: Требуются права администратора или WMI недоступен ({str(e)})"

@eel.expose
def get_system_info():
    try:
        cpu = platform.processor()
        ram = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        disk = round(psutil.disk_usage("/").total / (1024 ** 3), 2)
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage("/").percent

        gpu_name = "Неизвестно"
        gpu_usage = 0
        gpu_memory_total = 0
        gpu_memory_used = 0
        gpu_temp = 0

        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_name = gpu.name
                gpu_usage = gpu.load * 100
                gpu_memory_total = gpu.memoryTotal / 1024
                gpu_memory_used = gpu.memoryUsed / 1024
                gpu_temp = gpu.temperature
                logger.info(f"Обнаружена видеокарта через GPUtil: {gpu_name}, использование: {gpu_usage}%, память: {gpu_memory_used}/{gpu_memory_total} GB, температура: {gpu_temp}°C")
            else:
                logger.warning("Видеокарта не обнаружена с помощью GPUtil")
        except Exception as e:
            logger.error(f"Ошибка получения данных через GPUtil: {e}")

        if gpu_name == "Неизвестно":
            try:
                wmi_obj = wmi.WMI()
                video_controllers = wmi_obj.Win32_VideoController()
                if video_controllers:
                    gpu_name = video_controllers[0].Name
                    logger.info(f"Обнаружена видеокарта через WMI: {gpu_name}")
                else:
                    logger.warning("Видеокарта не обнаружена через WMI")
            except Exception as e:
                logger.error(f"Ошибка получения видеокарты через WMI: {e}")

            if "Radeon" in gpu_name:
                try:
                    logger.info("Попытка инициализации pyadl...")
                    devices = pyadl.ADLManager.getInstance().getDevices()
                    if devices:
                        device = devices[0]
                        logger.info(f"Обнаружено устройство AMD: {device.name}")
                        usage = device.getCurrentUsage()
                        if usage is not None:
                            gpu_usage = usage
                            logger.info(f"Использование видеокарты: {gpu_usage}%")
                        else:
                            logger.warning("Не удалось получить использование видеокарты через pyadl")
                        memory_info = device.getMemoryInfo()
                        if memory_info:
                            gpu_memory_total = memory_info.total / (1024 ** 3)
                            gpu_memory_used = (memory_info.total - memory_info.free) / (1024 ** 3)
                            logger.info(f"Память видеокарты: {gpu_memory_used}/{gpu_memory_total} GB")
                        else:
                            logger.warning("Не удалось получить данные о памяти видеокарты через pyadl")
                        temperature = device.getCurrentTemperature()
                        if temperature is not None:
                            gpu_temp = temperature
                            logger.info(f"Температура видеокарты: {gpu_temp}°C")
                        else:
                            logger.warning("Не удалось получить температуру видеокарты через pyadl")
                    else:
                        logger.warning("Видеокарта AMD не обнаружена через pyadl")
                except Exception as e:
                    logger.error(f"Ошибка получения данных через pyadl: {e}")

        cpu_temp = 0
        try:
            wmi_obj = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            temperature_infos = wmi_obj.Sensor()
            for sensor in temperature_infos:
                if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                    cpu_temp = sensor.Value
                    logger.info(f"Температура процессора: {cpu_temp}°C")
                    break
            if cpu_temp == 0:
                logger.warning("Температура процессора не обнаружена через Open Hardware Monitor")
        except Exception as e:
            logger.error(f"Ошибка получения температуры процессора: {e}")

        if gpu_temp == 0 and "Radeon" in gpu_name:
            try:
                wmi_obj = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                temperature_infos = wmi_obj.Sensor()
                for sensor in temperature_infos:
                    if sensor.SensorType == "Temperature" and "GPU" in sensor.Name:
                        gpu_temp = sensor.Value
                        logger.info(f"Температура видеокарты через Open Hardware Monitor: {gpu_temp}°C")
                        break
                if gpu_temp == 0:
                    logger.warning("Температура видеокарты не обнаружена через Open Hardware Monitor")
            except Exception as e:
                logger.error(f"Ошибка получения температуры видеокарты через Open Hardware Monitor: {e}")

        return {
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "cpu_usage": cpu_usage,
            "ram_usage": ram_usage,
            "disk_usage": disk_usage,
            "gpu_name": gpu_name,
            "gpu_usage": gpu_usage if gpu_usage else "Н/Д",
            "gpu_memory_total": gpu_memory_total if gpu_memory_total else "Н/Д",
            "gpu_memory_used": gpu_memory_used if gpu_memory_used else "Н/Д",
            "cpu_temp": cpu_temp if cpu_temp else "Н/Д",
            "gpu_temp": gpu_temp if gpu_temp else "Н/Д",
        }
    except Exception as e:
        logger.error(f"Ошибка получения системной информации: {e}")
        return {
            "cpu": "Неизвестно",
            "ram": 0,
            "disk": 0,
            "cpu_usage": 0,
            "ram_usage": 0,
            "disk_usage": 0,
            "gpu_name": "Неизвестно",
            "gpu_usage": "Н/Д",
            "gpu_memory_total": "Н/Д",
            "gpu_memory_used": "Н/Д",
            "cpu_temp": "Н/Д",
            "gpu_temp": "Н/Д",
        }

@eel.expose
def get_system_stats():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        ram_used = round(ram.used / (1024 ** 3), 2)
        ram_total = round(ram.total / (1024 ** 3), 2)
        gpus = GPUtil.getGPUs()
        gpu_usage = gpus[0].load * 100 if gpus else 0
        cpu_temp = 0
        gpu_temp = gpus[0].temperature if gpus else 0
        return {
            "cpu_usage": cpu_usage,
            "ram_used": ram_used,
            "ram_total": ram_total,
            "gpu_usage": gpu_usage,
            "cpu_temp": cpu_temp,
            "gpu_temp": gpu_temp,
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики системы: {e}")
        return {"cpu_usage": 0, "ram_used": 0, "ram_total": 0, "gpu_usage": 0, "cpu_temp": 0, "gpu_temp": 0}

@eel.expose
def get_system_state():
    settings = load_settings()
    power_plan_output = subprocess.run(
        ["powercfg", "/getactivescheme"], capture_output=True, text=True, shell=True
    ).stdout
    power_plan = "balanced"
    if "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" in power_plan_output:
        power_plan = "high"
    elif "a1841308-3541-4fab-bc81-f71556f20b4a" in power_plan_output:
        power_plan = "power_saving"

    state = {
        "cortana": check_registry_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana") == 1,
        "gameMode": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", "AllowAutoGameMode") == 1,
        "gameBar": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled") == 1,
        "updates": check_registry_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", "NoAutoUpdate") != 1,
        "touch": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Wisp\Touch", "TouchGate") == 1,
        "clipboard": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Clipboard", "EnableClipboardHistory") == 1,
        "stickyKeys": check_registry_value(winreg.HKEY_CURRENT_USER, r"Control Panel\Accessibility\StickyKeys", "Flags") == 510,
        "menuDelay": check_registry_value(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "MenuShowDelay") == "400",
        "smartScreen": check_registry_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableSmartScreen") == 1,
        "mouseAcceleration": check_registry_value(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold1") == "6" and check_registry_value(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", "MouseThreshold2") == "10",
        "protectionNotifications": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Security Health\State", "AccountProtectionNotification") == 1,
        "transparency": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency") == 1,
        "bestPerformance": check_registry_value(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "UserPreferencesMask") == bytes([0x90, 0x12, 0x03, 0x80]),
        "textShadows": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "ListviewShadow") == 1,
        "thumbnails": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "IconsOnly") != 1,
        "animations": check_registry_value(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop\WindowMetrics", "MinAnimate") == 1,
        "unnecessaryServices": settings.get("unnecessaryServices", False),
        "driverAutoupdate": check_registry_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate", "ExcludeWUDriversInQualityUpdate") != 1,
        "telemetry": check_registry_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry") == 1,
        "officeTelemetry": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Policies\Microsoft\Office\16.0\osm", "EnableLogging") == 1,
        "firefoxTelemetry": settings.get("firefoxTelemetry", False),
        "chromeTelemetry": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Policies\Google\Chrome", "MetricsReportingEnabled") == 1,
        "nvidiaTelemetry": check_registry_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\NVIDIA Corporation\Global\FTS", "EnableTelemetry") == 1,
        "visualStudioTelemetry": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\VisualStudio\Telemetry", "TurnOffTelemetry") != 1,
        "deviceList": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\deviceList", "Value") == 1,
        "wirelessSync": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\broadFileSystemAccess", "Value") == 1,
        "analytics": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\appDiagnostics", "Value") == 1,
        "contacts": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\contacts", "Value") == 1,
        "calendar": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\appointments", "Value") == 1,
        "callHistory": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\phoneCallHistory", "Value") == 1,
        "email": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\email", "Value") == 1,
        "tasks": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\userDataTasks", "Value") == 1,
        "messaging": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\chat", "Value") == 1,
        "radio": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\radios", "Value") == 1,
        "bluetooth": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\bluetooth", "Value") == 1,
        "documents": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\documentsLibrary", "Value") == 1,
        "pictures": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\picturesLibrary", "Value") == 1,
        "videos": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\videosLibrary", "Value") == 1,
        "filesystem": check_registry_value(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\broadFileSystemAccess", "Value") == 1,
        "autostart": settings.get("autostart", {}),
        "power_plan": settings.get("power_plan", power_plan),
        "language": settings.get("language", "ru"),
    }
    return state

@eel.expose
def save_profile(name):
    try:
        if not os.path.exists("profiles"):
            os.makedirs("profiles")
        state = get_system_state()
        with open(f"profiles/{name}.json", "w") as f:
            json.dump(state, f, indent=4)
        play_click_sound()
        return f"Профиль {name} сохранён"
    except Exception as e:
        logger.error(f"Ошибка сохранения профиля: {e}")
        return f"Ошибка: {e}"

@eel.expose
def load_profile(name):
    try:
        if not os.path.exists(f"profiles/{name}.json"):
            return f"Ошибка: Профиль {name} не найден"
        with open(f"profiles/{name}.json", "r") as f:
            state = json.load(f)
        settings = load_settings()
        settings.update(state)

        for prog_name, data in state.get("autostart", {}).items():
            toggle_autostart(prog_name, data["enabled"])

        for feature, value in state.items():
            if feature == "power_plan":
                if value == "high":
                    set_high_performance(True)
                elif value == "balanced":
                    set_balanced(True)
                elif value == "power_saving":
                    set_power_saving(True)
            elif feature != "autostart" and feature != "language":
                if feature in globals() and callable(globals()[f"toggle_{feature}"]):
                    globals()[f"toggle_{feature}"](value)

        save_settings(settings)
        play_click_sound()
        return f"Профиль {name} загружен"
    except Exception as e:
        logger.error(f"Ошибка загрузки профиля: {e}")
        return f"Ошибка: {e}"

@eel.expose
def restart_explorer():
    try:
        subprocess.run("taskkill /f /im explorer.exe", shell=True, check=True, capture_output=True)
        subprocess.run("start explorer.exe", shell=True, check=True, capture_output=True)
        play_click_sound()
        return "Проводник перезапущен"
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка перезапуска проводника: {e.stderr}")
        return f"Ошибка: {e.stderr}"
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return f"Ошибка: {e}"

@eel.expose
def set_language(lang):
    settings = load_settings()
    settings["language"] = lang
    save_settings(settings)
    return "Язык изменён"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logger.error(f"Ошибка проверки прав администратора: {e}")
        return False

def start_app():
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)
        except Exception as e:
            logger.error(f"Не удалось запустить с правами администратора: {e}")
            print("Ошибка: Запустите приложение от имени администратора вручную.")
            sys.exit(1)
    
    if not os.path.exists(PROFILE_DIR):
        try:
            os.makedirs(PROFILE_DIR, exist_ok=True)
            logger.info(f"Создана папка профилей: {os.path.abspath(PROFILE_DIR)}")
        except Exception as e:
            logger.error(f"Ошибка создания папки профилей: {e}")
    
    browsers = ["chrome", "firefox", "edge", "yandex", "opera", None]
    for browser in browsers:
        try:
            eel.start("index.html", size=(1000, 750), port=8000, mode=browser)
            break
        except Exception as e:
            logger.error(f"Ошибка с {browser or 'системным браузером'}: {e}")
    else:
        logger.error("Ошибка: Не удалось найти браузер.")
        sys.exit(1)

if __name__ == "__main__":
    if not os.path.exists("profiles"):
        os.makedirs("profiles")
    start_app()