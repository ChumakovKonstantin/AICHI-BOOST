async function toggle(feature, enable) {
    let result;
    console.log(`Toggling ${feature} to ${enable}`);
    switch (feature) {
        case 'cortana': result = await eel.toggle_cortana(enable)(); break;
        case 'gameMode': result = await eel.toggle_game_mode(enable)(); break;
        case 'gameBar': result = await eel.toggle_game_bar(enable)(); break;
        case 'updates': result = await eel.toggle_windows_update(enable)(); break;
        case 'touch': result = await eel.toggle_touch_input(enable)(); break;
        case 'clipboard': result = await eel.toggle_cloud_clipboard(enable)(); break;
        case 'stickyKeys': result = await eel.toggle_sticky_keys(enable)(); break;
        case 'menuDelay': result = await eel.toggle_menu_delay(enable)(); break;
        case 'smartScreen': result = await eel.toggle_smart_screen(enable)(); break;
        case 'mouseAcceleration': result = await eel.toggle_mouse_acceleration(enable)(); break;
        case 'protectionNotifications': result = await eel.toggle_protection_notifications(enable)(); break;
        case 'transparency': result = await eel.toggle_transparency(enable)(); break;
        case 'bestPerformance': result = await eel.set_best_performance(enable)(); break;
        case 'textShadows': result = await eel.toggle_text_shadows(enable)(); break;
        case 'thumbnails': result = await eel.toggle_thumbnail_previews(enable)(); break;
        case 'animations': result = await eel.toggle_animations(enable)(); break;
        case 'unnecessaryServices': result = await eel.toggle_unnecessary_services(enable)(); break;
        case 'driverAutoupdate': result = await eel.toggle_driver_autoupdate(enable)(); break;
        case 'telemetry': result = await eel.toggle_telemetry(enable)(); break;
        case 'officeTelemetry': result = await eel.toggle_office_telemetry(enable)(); break;
        case 'firefoxTelemetry': result = await eel.toggle_firefox_telemetry(enable)(); break;
        case 'chromeTelemetry': result = await eel.toggle_chrome_telemetry(enable)(); break;
        case 'nvidiaTelemetry': result = await eel.toggle_nvidia_telemetry(enable)(); break;
        case 'visualStudioTelemetry': result = await eel.toggle_visualstudio_telemetry(enable)(); break;
        case 'deviceList': result = await eel.toggle_app_access_to_device_list(enable)(); break;
        case 'wirelessSync': result = await eel.toggle_app_sync_with_wireless(enable)(); break;
        case 'analytics': result = await eel.toggle_app_access_to_analytics(enable)(); break;
        case 'contacts': result = await eel.toggle_app_access_to_contacts(enable)(); break;
        case 'calendar': result = await eel.toggle_app_access_to_calendar(enable)(); break;
        case 'callHistory': result = await eel.toggle_app_access_to_call_history(enable)(); break;
        case 'email': result = await eel.toggle_app_access_to_email(enable)(); break;
        case 'tasks': result = await eel.toggle_app_access_to_tasks(enable)(); break;
        case 'messaging': result = await eel.toggle_app_access_to_messaging(enable)(); break;
        case 'radio': result = await eel.toggle_app_access_to_radio(enable)(); break;
        case 'bluetooth': result = await eel.toggle_app_access_to_bluetooth(enable)(); break;
        case 'documents': result = await eel.toggle_app_access_to_documents(enable)(); break;
        case 'pictures': result = await eel.toggle_app_access_to_pictures(enable)(); break;
        case 'videos': result = await eel.toggle_app_access_to_videos(enable)(); break;
        case 'filesystem': result = await eel.toggle_app_access_to_filesystem(enable)(); break;
    }
    playSound();
    document.getElementById('status').innerText = result;
    showStatus();
    console.log(`Toggle ${feature} completed with result: ${result}`);
}

async function optimizeSystem() {
    const button = event.target;
    button.classList.add('pulse');
    const statusElement = document.getElementById('status');
    statusElement.innerText = "Выполняется...";
    statusElement.classList.add('loading');

    try {
        console.log("Starting system optimization");
        const result = await eel.optimize_system()();
        playSound();
        statusElement.innerText = result;
        console.log(`Optimization result: ${result}`);
    } catch (error) {
        console.error("Ошибка при оптимизации системы:", error);
        statusElement.innerText = "Ошибка оптимизации: " + error;
    } finally {
        statusElement.classList.remove('loading');
        showStatus();
        setTimeout(() => button.classList.remove('pulse'), 500);
    }
}

async function setHighPerformance(enable) {
    const statusElement = document.getElementById('status');
    statusElement.innerText = "Выполняется...";
    statusElement.classList.add('loading');

    console.log(`Setting high performance to ${enable}`);
    const result = await eel.set_high_performance(enable)();
    playSound();
    statusElement.innerText = result;
    console.log(`High performance result: ${result}`);
    statusElement.classList.remove('loading');
    updatePowerSwitches('highPerformance', enable);
    showStatus();
}

async function setBalanced(enable) {
    const statusElement = document.getElementById('status');
    statusElement.innerText = "Выполняется...";
    statusElement.classList.add('loading');

    console.log(`Setting balanced to ${enable}`);
    const result = await eel.set_balanced(enable)();
    playSound();
    statusElement.innerText = result;
    console.log(`Balanced result: ${result}`);
    statusElement.classList.remove('loading');
    updatePowerSwitches('balanced', enable);
    showStatus();
}

async function setPowerSaving(enable) {
    const statusElement = document.getElementById('status');
    statusElement.innerText = "Выполняется...";
    statusElement.classList.add('loading');

    console.log(`Setting power saving to ${enable}`);
    const result = await eel.set_power_saving(enable)();
    playSound();
    statusElement.innerText = result;
    console.log(`Power saving result: ${result}`);
    statusElement.classList.remove('loading');
    updatePowerSwitches('powerSaving', enable);
    showStatus();
}

function updatePowerSwitches(activeId, enable) {
    const switches = ['highPerformance', 'balanced', 'powerSaving'];
    switches.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) {
            if (id === activeId) {
                checkbox.checked = enable;
                console.log(`Set ${id} to ${enable}`);
            } else {
                checkbox.checked = false;
                console.log(`Unset ${id}`);
            }
        }
    });
}

async function createRestorePoint() {
    const button = event.target;
    button.classList.add('pulse');
    const statusElement = document.getElementById('status');
    statusElement.innerText = "Выполняется...";
    statusElement.classList.add('loading');

    console.log("Creating restore point");
    const result = await eel.create_restore_point()();
    playSound();
    statusElement.innerText = result;
    console.log(`Restore point result: ${result}`);
    statusElement.classList.remove('loading');
    showStatus();
    setTimeout(() => button.classList.remove('pulse'), 500);
}

async function activateWindows() {
    const button = event.target;
    button.classList.add('pulse');
    const statusElement = document.getElementById('status');
    statusElement.innerText = "Активация выполняется...";
    statusElement.classList.add('loading');

    console.log("Activating Windows");
    const result = await eel.activate_windows()();
    playSound();
    statusElement.innerText = result;
    console.log(`Windows activation result: ${result}`);
    statusElement.classList.remove('loading');
    showStatus();
    setTimeout(() => button.classList.remove('pulse'), 500);
}

async function updateProfileList() {
    const profileSelect = document.getElementById("profile-select");
    profileSelect.innerHTML = '<option value="">Выберите профиль</option>';
    try {
        const profiles = await eel.get_profiles()();
        console.log("Полученные профили:", profiles); // Отладочный вывод
        if (profiles.length === 0) {
            console.log("Список профилей пуст");
        }
        profiles.forEach(profile => {
            const option = document.createElement("option");
            option.value = profile;
            option.textContent = profile;
            profileSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Ошибка при загрузке списка профилей:", error);
        showNotification("Не удалось загрузить список профилей");
    }
}

// Привяжите выбор профиля к полю ввода
document.getElementById("profile-select").addEventListener("change", (e) => {
    const selectedProfile = e.target.value;
    if (selectedProfile) {
        document.getElementById("profile-name").value = selectedProfile;
    }
});

// Обновите функцию initState, чтобы загружать список профилей при старте
async function initState() {
    const state = await eel.get_system_state()();
    document.getElementById("cortana").checked = state.cortana;
    // ... (остальной код initState остается без изменений до этого места)

    document.getElementById("language-select").value = state.language;
    updateLanguage(state.language);

    // Загрузка списка профилей
    await updateProfileList();

    const autostartList = document.getElementById("autostart-list");
    autostartList.innerHTML = "";
    const programs = await eel.get_autostart_programs()();
    programs.forEach(program => {
        const label = document.createElement("label");
        label.className = "toggle-switch";
        label.innerHTML = `
            <input type="checkbox" id="autostart-${program.name}" ${program.enabled ? "checked" : ""} onchange="toggleAutostart('${program.name}', this.checked)">
            <span class="switch"></span>
            <span class="label">${program.name}</span>
        `;
        autostartList.appendChild(label);
    });

    const systemInfo = await eel.get_system_info()();
    document.getElementById("cpu-name").textContent = systemInfo.cpu || "Неизвестно";
    // ... (остальной код initState остается без изменений)
}

async function saveProfile() {
    const name = document.getElementById("profile-name").value;
    if (!name) {
        showNotification(translations[currentLang]["enter-profile-name"]);
        return;
    }
    const result = await eel.save_profile(name)();
    showNotification(result);
    playSound();
    await updateProfileList(); // Обновляем список после сохранения
}

async function loadProfile() {
    const name = document.getElementById("profile-name").value;
    if (!name) {
        showNotification(translations[currentLang]["enter-profile-name"]);
        return;
    }
    const result = await eel.load_profile(name)();
    showNotification(result);
    playSound();
    await initState(); // Перезагружаем состояние, включая список профилей
}

// Инициализация
window.onload = () => {
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.getElementById("theme-toggle").value = savedTheme;
    changeTheme(savedTheme);
    initState();
    updatePerformance();
    setInterval(updateStats, 2000);
    setInterval(updatePerformance, 30000);
    openTab({ currentTarget: document.querySelector('.tab-button.active') }, 'windows');
};

async function updateAutostartList() {
    const autostartList = document.getElementById('autostart-list');
    autostartList.innerHTML = '';
    const programs = await eel.get_autostart_programs()();
    programs.forEach(program => {
        const label = document.createElement('label');
        label.className = 'toggle-switch';
        label.innerHTML = `
            <input type="checkbox" id="autostart-${program.name}" ${program.enabled ? 'checked' : ''} onchange="toggleAutostart('${program.name}', this.checked)">
            <span class="switch"></span>
            <span class="label">${program.name}</span>
        `;
        autostartList.appendChild(label);
    });
}

function showStatus() {
    const statusElement = document.getElementById('status');
    statusElement.classList.remove('show');
    void statusElement.offsetWidth;
    statusElement.classList.add('show');
}

function playSound() {
    eel.play_click_sound()().catch(error => console.log("Не удалось воспроизвести звук:", error));
}

function openTab(event, tabName) {
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = 'none';
    }
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }
    document.getElementById(tabName).style.display = 'block';
    event.currentTarget.classList.add('active');
    document.getElementById('status').innerText = translations[currentLang]["ready"];
    showStatus();

    if (tabName === 'autostart') {
        updateAutostartList();
    } else if (tabName === 'profiles') {
        updateProfileList(); // Должно быть здесь
    }
}

async function updatePerformance() {
    const scoreElement = document.getElementById('performance-score');
    const statusElement = document.getElementById('performance-status');
    try {
        console.log("Updating performance");
        const score = await eel.get_performance_score()();
        scoreElement.innerText = `Оптимизация: ${score}%`;
        statusElement.innerText = getPerformanceStatus(score);
        console.log(`Performance updated: ${score}%`);
    } catch (error) {
        scoreElement.innerText = "Оптимизация: 0%";
        statusElement.innerText = "Ошибка анализа";
        console.error("Ошибка обновления производительности:", error);
    }
}

function getPerformanceStatus(score) {
    if (score >= 80) return "Высокая производительность";
    if (score >= 50) return "Хорошая производительность";
    if (score >= 20) return "Средняя производительность";
    return "Низкий уровень";
}

async function loadSystemState() {
    console.log("Loading system state");
    const state = await eel.get_system_state()();
    Object.entries(state).forEach(([key, value]) => {
        const el = document.getElementById(key);
        if (el && el.type === "checkbox") {
            el.checked = value;
            console.log(`Set ${key} to ${value}`);
        }
    });
    const powerPlan = state.power_plan;
    updatePowerSwitches(
        powerPlan === 'high' ? 'highPerformance' :
        powerPlan === 'balanced' ? 'balanced' :
        powerPlan === 'power_saving' ? 'powerSaving' : null,
        powerPlan !== null
    );
    console.log(`Power plan set to ${powerPlan}`);
}

document.addEventListener('DOMContentLoaded', function() {
    openTab({ currentTarget: document.querySelector('.tab-button.active') }, 'windows');
    updatePerformance();
    loadSystemState();
    setInterval(updatePerformance, 5000);
});