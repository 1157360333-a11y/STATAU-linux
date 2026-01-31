/**
 * STATAU 主题切换模块
 * 支持暗色/浅色主题切换，并保存用户偏好到localStorage
 */

class ThemeSwitcher {
    constructor() {
        // 从localStorage读取保存的主题，默认为暗色
        this.currentTheme = localStorage.getItem('statau-theme') || 'dark';
        this.init();
    }

    // 初始化
    init() {
        this.applyTheme(this.currentTheme);
        this.setupEventListeners();
    }

    // 应用主题
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        // 保存到localStorage
        localStorage.setItem('statau-theme', theme);
        this.updateToggleButton();
    }

    // 切换主题
    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
    }

    // 更新切换按钮UI
    updateToggleButton() {
        const button = document.getElementById('theme-toggle-btn');
        if (!button) return;

        const icon = button.querySelector('i');
        const text = button.querySelector('.theme-text');

        if (this.currentTheme === 'dark') {
            icon.className = 'fa-solid fa-sun';
            if (text) text.textContent = '浅色';
        } else {
            icon.className = 'fa-solid fa-moon';
            if (text) text.textContent = '暗色';
        }
    }

    // 设置事件监听
    setupEventListeners() {
        const button = document.getElementById('theme-toggle-btn');
        if (button) {
            button.addEventListener('click', () => this.toggleTheme());
        }
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    window.themeSwitcher = new ThemeSwitcher();
});
