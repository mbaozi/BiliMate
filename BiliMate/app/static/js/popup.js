// 统一弹窗API设计
const Popup = {
    // 配置项
    config: {
        autoClose: true,
        duration: 3000,
        position: 'top-right',
        zIndex: 1050,
        animation: 'fade',
        backdrop: true
    },
    
    // 弹窗类型枚举
    Type: {
        INFO: 'info',
        SUCCESS: 'success',
        ERROR: 'error',
        WARNING: 'warning'
    },
    
    // 设置全局配置
    setConfig(options) {
        this.config = { ...this.config, ...options };
    },
    
    // 创建弹窗容器
    createContainer() {
        let container = document.getElementById('popup-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'popup-container';
            document.body.appendChild(container);
        }
        return container;
    },
    
    // 获取弹窗标题
    getTitle(type) {
        switch (type) {
            case this.Type.SUCCESS:
                return '成功';
            case this.Type.ERROR:
                return '错误';
            case this.Type.WARNING:
                return '警告';
            default:
                return '提示';
        }
    },
    
    // 基础弹窗实现
    createElement(type, message, options = {}) {
        const container = this.createContainer();
        const mergedOptions = { ...this.config, ...options };
        
        // 创建弹窗元素
        const popup = document.createElement('div');
        popup.className = `popup popup-${type}`;
        
        // 设置弹窗内容
        popup.innerHTML = `
            <div class="popup-content">
                <div class="popup-header">
                    <div class="popup-title">${mergedOptions.title || this.getTitle(type)}</div>
                </div>
                <div class="popup-body">
                    <div class="popup-message">${message}</div>
                </div>
                <div class="popup-footer">
                    ${mergedOptions.footerContent || ''}
                </div>
            </div>
        `;
        
        // 添加到容器
        container.appendChild(popup);
        
        return popup;
    },
    
    // 关闭弹窗
    close(popup) {
        popup.classList.remove('show');
        setTimeout(() => {
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
        }, 300);
    },
    
    // 创建不可关闭的进度弹窗
    createProgressPopup(title = '升级中', message = '开始下载升级包...') {
        const container = this.createContainer();
        
        // 创建弹窗元素
        const popup = document.createElement('div');
        popup.className = 'popup popup-info';
        popup.id = 'download-progress-popup';
        
        // 设置弹窗内容
        popup.innerHTML = `
            <div class="popup-content">
                <div class="popup-header">
                    <div class="popup-title">${title}</div>
                </div>
                <div class="popup-body">
                    <div class="popup-message">${message}</div>
                    <div class="progress-container" style="margin-top: 1rem;">
                        <div class="progress-bar" style="width: 0%; height: 8px; background-color: #007bff; border-radius: 4px; transition: width 0.3s ease;"></div>
                    </div>
                    <div class="progress-text" style="margin-top: 0.5rem; font-size: 0.9rem; color: #6c757d;">
                        0% (0 MB / 0 MB)
                    </div>
                </div>
                <div class="popup-footer">
                    <!-- 无按钮，不可关闭 -->
                </div>
            </div>
        `;
        
        // 添加到容器
        container.appendChild(popup);
        
        // 显示弹窗
        setTimeout(() => {
            popup.classList.add('show');
        }, 10);
        
        // 禁用点击外部关闭
        popup.addEventListener('click', (e) => {
            // 不做任何操作，阻止事件冒泡
            e.stopPropagation();
        });
        
        // 禁用按Esc键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
            }
        };
        document.addEventListener('keydown', handleEsc);
        
        // 保存Esc键监听器，以便后续移除
        popup._escListener = handleEsc;
        
        return popup;
    },
    
    // 创建不可关闭的倒计时弹窗
    createCountdownPopup(title = '应用重启中', message = '应用重启中，5秒后自动刷新...') {
        const container = this.createContainer();
        
        // 创建弹窗元素
        const popup = document.createElement('div');
        popup.className = 'popup popup-info';
        popup.id = 'countdown-popup';
        
        // 设置弹窗内容（无进度条）
        popup.innerHTML = `
            <div class="popup-content">
                <div class="popup-header">
                    <div class="popup-title">${title}</div>
                </div>
                <div class="popup-body">
                    <div class="popup-message">${message}</div>
                </div>
                <div class="popup-footer">
                    <!-- 无按钮，不可关闭 -->
                </div>
            </div>
        `;
        
        // 添加到容器
        container.appendChild(popup);
        
        // 显示弹窗
        setTimeout(() => {
            popup.classList.add('show');
        }, 10);
        
        // 禁用点击外部关闭
        popup.addEventListener('click', (e) => {
            // 不做任何操作，阻止事件冒泡
            e.stopPropagation();
        });
        
        // 禁用按Esc键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
            }
        };
        document.addEventListener('keydown', handleEsc);
        
        // 保存Esc键监听器，以便后续移除
        popup._escListener = handleEsc;
        
        return popup;
    },
    
    // 更新进度弹窗
    updateProgressPopup(popup, progress, downloaded, total) {
        if (!popup) return;
        
        // 更新进度条
        const progressBar = popup.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        // 格式化字节数为MB
        const downloadedMB = (downloaded / (1024 * 1024)).toFixed(2);
        const totalMB = (total / (1024 * 1024)).toFixed(2);
        
        // 更新进度文本
        const progressText = popup.querySelector('.progress-text');
        if (progressText) {
            progressText.textContent = `${progress.toFixed(1)}% (${downloadedMB} MB / ${totalMB} MB)`;
        }
    },
    
    // 关闭进度弹窗
    closeProgressPopup(popup) {
        if (!popup) return;
        
        // 移除Esc键监听器
        if (popup._escListener) {
            document.removeEventListener('keydown', popup._escListener);
        }
        
        // 关闭弹窗
        this.close(popup);
    },
    
    // 基础弹窗
    alert(message, options = {}) {
        return new Promise((resolve) => {
            const mergedOptions = { ...this.config, ...options };
            
            // 创建弹窗
            const popup = this.createElement(mergedOptions.type || this.Type.INFO, message, {
                ...mergedOptions,
                footerContent: `
                    <button class="btn btn-primary popup-btn-ok">确定</button>
                `
            });
            
            // 显示弹窗
            setTimeout(() => {
                popup.classList.add('show');
            }, 10);
            
            // 绑定确定按钮事件
            const okBtn = popup.querySelector('.popup-btn-ok');
            okBtn.addEventListener('click', () => {
                this.close(popup);
                resolve();
            });
            
            // 点击弹窗外部关闭
            popup.addEventListener('click', (e) => {
                if (e.target === popup) {
                    this.close(popup);
                    resolve();
                }
            });
            
            // 按Esc键关闭
            function handleEsc(e) {
                if (e.key === 'Escape') {
                    this.close(popup);
                    resolve();
                    document.removeEventListener('keydown', handleEsc);
                }
            }
            document.addEventListener('keydown', handleEsc.bind(this));
        });
    },
    
    // 确认弹窗
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const mergedOptions = { ...this.config, ...options };
            
            // 创建弹窗
            const popup = this.createElement(this.Type.WARNING, message, {
                ...mergedOptions,
                title: mergedOptions.title || '确认操作',
                footerContent: `
                    <button class="btn btn-secondary popup-btn-cancel">取消</button>
                    <button class="btn btn-primary popup-btn-confirm">确定</button>
                `
            });
            
            // 显示弹窗
            setTimeout(() => {
                popup.classList.add('show');
            }, 10);
            
            // 绑定取消按钮事件
            const cancelBtn = popup.querySelector('.popup-btn-cancel');
            cancelBtn.addEventListener('click', () => {
                this.close(popup);
                resolve(false);
            });
            
            // 绑定确定按钮事件
            const confirmBtn = popup.querySelector('.popup-btn-confirm');
            confirmBtn.addEventListener('click', () => {
                this.close(popup);
                resolve(true);
            });
            
            // 点击弹窗外部关闭
            popup.addEventListener('click', (e) => {
                if (e.target === popup) {
                    this.close(popup);
                    resolve(false);
                }
            });
            
            // 按Esc键关闭
            function handleEsc(e) {
                if (e.key === 'Escape') {
                    this.close(popup);
                    resolve(false);
                    document.removeEventListener('keydown', handleEsc);
                }
            }
            document.addEventListener('keydown', handleEsc.bind(this));
        });
    },
    
    // 自动消失提示（替换showSuccess和showError）
    toast(message, type = this.Type.INFO, options = {}) {
        const mergedOptions = { 
            ...this.config, 
            autoClose: true, 
            duration: 3000,
            ...options 
        };
        
        // 使用原有alert样式
        const alert = document.createElement('div');
        
        // 根据类型设置对应样式
        let alertClass = 'alert';
        switch (type) {
            case this.Type.SUCCESS:
                alertClass += ' alert-success';
                break;
            case this.Type.ERROR:
                alertClass += ' alert-danger';
                break;
            case this.Type.WARNING:
                alertClass += ' alert-warning';
                break;
            default: // info
                alertClass += ' alert-info';
        }
        
        alert.className = alertClass;
        alert.innerHTML = `
            <div class="alert-content">
                <span class="alert-icon">${type === this.Type.SUCCESS ? '✓' : type === this.Type.ERROR ? '✗' : type === this.Type.WARNING ? '!' : 'i'}</span>
                <span class="alert-message">${message}</span>
            </div>
            <button class="alert-close">×</button>
        `;
        
        // 添加到页面
        const alertsContainer = document.querySelector('.alerts-container') || document.body;
        if (alertsContainer.classList.contains('alerts-container')) {
            alertsContainer.appendChild(alert);
        } else {
            const container = document.createElement('div');
            container.className = 'alerts-container';
            container.appendChild(alert);
            document.body.insertBefore(container, document.body.firstChild);
        }
        
        // 添加关闭事件
        alert.querySelector('.alert-close').addEventListener('click', function() {
            alert.remove();
        });
        
        // 自动消失
        if (mergedOptions.autoClose) {
            setTimeout(() => {
                alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }, mergedOptions.duration);
        }
        
        return alert;
    },
    
    // 快捷方法
    success(message, options = {}) {
        return this.toast(message, this.Type.SUCCESS, options);
    },
    
    error(message, options = {}) {
        return this.toast(message, this.Type.ERROR, options);
    },
    
    warning(message, options = {}) {
        return this.toast(message, this.Type.WARNING, options);
    },
    
    info(message, options = {}) {
        return this.toast(message, this.Type.INFO, options);
    }
};

// 导出全局变量
window.Popup = Popup;
