/* BiliMate 通用JavaScript文件 */

// 应用主题
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
}

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 应用当前主题
    const currentTheme = document.body.getAttribute('data-theme') || 'light';
    applyTheme(currentTheme);
    
    // 弹窗自动消失功能
    function initAutoDismissAlerts() {
        // 只对alerts-container内的弹窗添加自动消失效果，排除登录状态提示等固定提示
        const alerts = document.querySelectorAll('.alerts-container .alert');
        
        // 为每个弹窗设置5秒后自动消失
        alerts.forEach(alert => {
            setTimeout(() => {
                // 添加淡出动画
                alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                
                // 动画结束后移除元素
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }, 5000);
        });
    }

    // 初始化弹窗关闭按钮
    function initAlertCloseButtons() {
        // 获取所有关闭按钮
        const closeButtons = document.querySelectorAll('.alert-close');
        
        // 为每个关闭按钮添加点击事件监听器
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                const alert = this.parentElement;
                // 添加淡出动画
                alert.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                
                // 动画结束后移除元素
                setTimeout(() => {
                    alert.remove();
                }, 300);
            });
        });
    }
    
    // 初始化设置页面功能
    function initSettingsPage() {
        // 主题切换功能
        const themeRadios = document.querySelectorAll('input[name="theme"]');
        if (themeRadios.length > 0) {
            themeRadios.forEach(radio => {
                radio.addEventListener('change', function() {
                    updateTheme(this.value);
                });
            });
        }
        
        // 内网免密登录开关功能
        const trustLoginCheckbox = document.getElementById('enable_trust_login');
        if (trustLoginCheckbox) {
            trustLoginCheckbox.addEventListener('change', function() {
                updateTrustLogin(this.checked);
            });
        }
        
        // 检查激活状态函数
        function checkActivationStatus() {
            // 发送查询激活状态请求
            return fetch('/api/check_activation_status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(result => {
                // 更新激活状态显示
                const statusText = document.getElementById('activation-status-text');
                const activationCard = statusText ? statusText.closest('.activation-card') : null;
                const activationType = document.getElementById('activation-type');
                const expiryDate = document.getElementById('expiry-date');
                const activationDate = document.getElementById('activation-date');
                
                // 获取数据，确保有默认值
                const data = result.data || {};
                
                // 更新激活状态
                if (statusText) {
                    statusText.textContent = data.activation_status || '未激活';
                }
                if (activationCard) {
                    // 移除所有状态类，避免样式冲突
                    activationCard.classList.remove('active', 'inactive', 'expired');
                    
                    if (data.activation_status === '已激活') {
                        // 激活状态：使用绿色主题
                        activationCard.classList.add('active');
                    } else if (data.activation_status === '已到期') {
                        // 到期状态：使用黄色主题
                        activationCard.classList.add('expired');
                    } else {
                        // 未激活状态：使用红色主题
                        activationCard.classList.add('inactive');
                    }
                }
                
                // 更新激活类型
                if (activationType) {
                    activationType.textContent = data.activation_type || 'NULL';
                }
                
                // 更新到期日期
                if (expiryDate) {
                    expiryDate.textContent = data.expiry_date || 'NULL';
                }
                
                // 更新激活日期
                if (activationDate) {
                    activationDate.textContent = data.activation_date || 'NULL';
                }
            })
            .catch(error => {
                console.error('查询激活状态失败:', error);
                // 不显示弹窗，只在控制台记录错误
            });
        }
        
        // 激活码表单提交功能
        const activationForm = document.getElementById('activation-form');
        if (activationForm) {
            activationForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // 获取激活码
                const activationCodeInput = document.getElementById('activation_code');
                const activationCode = activationCodeInput.value.trim();
                
                if (!activationCode) {
                    Popup.alert('请输入激活码', { type: Popup.Type.INFO });
                    return;
                }
                
                // 获取激活按钮
                const submitBtn = activationForm.querySelector('button[type="submit"]');
                
                // 获取激活状态文本元素
                const statusText = document.getElementById('activation-status-text');
                
                try {
                    // 禁用激活码输入框
                    activationCodeInput.disabled = true;
                    
                    // 禁用激活按钮，保持文字不变
                    submitBtn.disabled = true;
                    
                    // 修改激活状态小卡片显示为"激活中..."，保持颜色不变
                    if (statusText) {
                        statusText.textContent = '激活中...';
                    }
                    
                    // 发送激活请求
                    fetch('/api/activate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            activation_code: activationCode
                        })
                    })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            Popup.alert(result.message || '激活成功', { type: Popup.Type.SUCCESS });
                            // 清空输入框
                            activationCodeInput.value = '';
                            // 激活成功后自动更新激活状态
                            checkActivationStatus();
                        } else {
                            Popup.alert(result.message || '激活失败', { type: Popup.Type.ERROR });
                            // 更新激活状态
                            checkActivationStatus();
                        }
                    })
                    .catch(error => {
                        console.error('激活请求失败:', error);
                        Popup.alert('激活请求失败，请稍后重试', { type: Popup.Type.ERROR });
                        // 更新激活状态
                        checkActivationStatus();
                    })
                    .finally(() => {
                        // 恢复激活码输入框状态
                        activationCodeInput.disabled = false;
                        
                        // 恢复激活按钮状态
                        submitBtn.disabled = false;
                    });
                } catch (error) {
                    console.error('激活处理异常:', error);
                    Popup.alert('激活处理异常，请稍后重试', { type: Popup.Type.ERROR });
                    
                    // 恢复状态
                    activationCodeInput.disabled = false;
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;
                }
            });
        }
        
        // 获取粉丝码按钮点击事件
        const getFanCodeBtn = document.getElementById('get-fan-code-btn');
        if (getFanCodeBtn) {
            getFanCodeBtn.addEventListener('click', async function() {
                // 弹窗提示，使用await等待弹窗关闭
                await Popup.alert('🎉 关注UP主【是萌包子吖】私信获取粉丝码~', { type: Popup.Type.INFO });
                // 弹窗关闭后打开B站链接
                window.open('https://space.bilibili.com/3546855325567315', '_blank');
            });
        }
        
        // 刷新激活状态按钮功能
        const refreshStatusBtn = document.getElementById('refresh-activation-status');
        if (refreshStatusBtn) {
            refreshStatusBtn.addEventListener('click', function() {
                // 禁用按钮，保持文字不变
                refreshStatusBtn.disabled = true;
                
                // 发送手动刷新激活状态请求
                fetch('/api/refresh_activation_status', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(result => {                    
                    // 更新激活状态显示
                    const statusText = document.getElementById('activation-status-text');
                    const activationCard = statusText ? statusText.closest('.activation-card') : null;
                    const activationType = document.getElementById('activation-type');
                    const expiryDate = document.getElementById('expiry-date');
                    const activationDate = document.getElementById('activation-date');
                    
                    // 获取数据，确保有默认值
                    const data = result.data || {};
                    
                    // 更新激活状态
                    statusText.textContent = data.activation_status || '未激活';
                    if (activationCard) {
                        // 移除所有状态类，避免样式冲突
                        activationCard.classList.remove('active', 'inactive', 'expired');
                        
                        if (data.activation_status === '已激活') {
                            // 激活状态：使用绿色主题
                            activationCard.classList.add('active');
                        } else if (data.activation_status === '已到期') {
                            // 到期状态：使用黄色主题
                            activationCard.classList.add('expired');
                        } else {
                            // 未激活状态：使用红色主题
                            activationCard.classList.add('inactive');
                        }
                    }
                    
                    // 更新激活类型
                    activationType.textContent = data.activation_type || 'NULL';
                    
                    // 更新到期日期
                    expiryDate.textContent = data.expiry_date || 'NULL';
                    
                    // 更新激活日期
                    activationDate.textContent = data.activation_date || 'NULL';
                })
                .catch(error => {
                    console.error('刷新激活状态失败:', error);
                    // 不显示弹窗，只在控制台记录错误
                })
                .finally(() => {
                    // 恢复按钮状态
                    refreshStatusBtn.disabled = false;
                });
            });
        }
        
        // 页面加载时自动查询激活状态
        checkActivationStatus();
    }

    // 初始化所有功能
    initAutoDismissAlerts();
    initAlertCloseButtons();
    initSettingsPage();
    
    // 初始化系统资源监控
    initBroadcastChannel();
});

// 立即应用主题，无需等待DOM加载完成
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        const currentTheme = document.body.getAttribute('data-theme') || 'light';
        applyTheme(currentTheme);
    });
} else {
    const currentTheme = document.body.getAttribute('data-theme') || 'light';
    applyTheme(currentTheme);
}

// 更新内网免密登录设置
function updateTrustLogin(enabled) {
    // 使用AJAX更新设置
    fetch('/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
            'setting_type': 'security',
            'enable_trust_login': enabled ? 'on' : ''
        })
    })
    .then(response => {
        // 处理非JSON响应
        if (response.redirected) {
            // 如果是重定向，刷新页面
            window.location.reload();
        }
        return response.json().catch(() => ({}));
    })
    .then(data => {
        // 可以添加成功提示
    })
    .catch(error => {
        console.error('更新设置失败:', error);
    });
}

// 更新主题设置
function updateTheme(theme) {
    // 创建隐藏表单，使用传统提交方式确保页面刷新
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/settings';
    
    // 添加隐藏字段
    const settingTypeInput = document.createElement('input');
    settingTypeInput.type = 'hidden';
    settingTypeInput.name = 'setting_type';
    settingTypeInput.value = 'appearance';
    form.appendChild(settingTypeInput);
    
    const themeInput = document.createElement('input');
    themeInput.type = 'hidden';
    themeInput.name = 'theme';
    themeInput.value = theme;
    form.appendChild(themeInput);
    
    // 将表单添加到页面并自动提交
    document.body.appendChild(form);
    form.submit();
}

// 激活码功能提示
function showActivationMessage() {
    // 显示激活码暂不支持的提示
    Popup.alert('激活码功能暂未开放，敬请期待！', { type: Popup.Type.INFO });
}

// 系统资源占用监控
let systemUsageInterval = null;
let isMaster = false;
let broadcastChannel = null;

// 初始化BroadcastChannel
function initBroadcastChannel() {
    broadcastChannel = new BroadcastChannel('systemUsageMonitor');
    
    // 监听其他标签页的消息
    broadcastChannel.addEventListener('message', (event) => {
        if (event.data.type === 'CLAIM_MASTER') {
            // 如果已经有主标签页，放弃竞争
            if (!isMaster) {
                console.log('检测到其他主标签页，当前标签页进入待机状态');
            }
        } else if (event.data.type === 'MASTER_OFFLINE') {
            // 主标签页离线，重新竞争
            console.log('主标签页离线，当前标签页开始竞争主标签页');
            claimMaster();
        }
    });
    
    // 页面加载时竞争主标签页
    claimMaster();
    
    // 页面卸载时通知其他标签页
    window.addEventListener('beforeunload', () => {
        if (isMaster) {
            broadcastChannel.postMessage({ type: 'MASTER_OFFLINE' });
        }
        broadcastChannel.close();
        if (systemUsageInterval) {
            clearInterval(systemUsageInterval);
            systemUsageInterval = null;
        }
    });
}

// 竞争主标签页
function claimMaster() {
    // 检查系统资源监控元素是否存在
    if (!document.getElementById('system-usage')) {
        return;
    }
    
    // 发送竞争消息
    broadcastChannel.postMessage({ type: 'CLAIM_MASTER' });
    
    // 设置一个短延迟，确保其他标签页有时间响应
    setTimeout(() => {
        if (!isMaster) {
            // 成为主标签页
            isMaster = true;
            console.log('当前标签页成为主标签页，开始监控系统资源');
            // 初始调用一次
            updateSystemUsage();
            // 每5秒更新一次
            systemUsageInterval = setInterval(updateSystemUsage, 5000);
        }
    }, 100);
}

// 更新系统资源占用显示（CPU和内存）
function updateSystemUsage() {
    // 只有主标签页才执行更新
    if (!isMaster) {
        return;
    }
    
    fetch('/api/system_usage')
        .then(response => {
            // 检查是否重定向到登录页面
            if (response.redirected) {
                console.warn('未登录或会话过期，停止系统资源监控');
                // 清除定时器
                if (systemUsageInterval) {
                    clearInterval(systemUsageInterval);
                    systemUsageInterval = null;
                }
                isMaster = false;
                return Promise.reject('redirected');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 处理CPU占用率
                const physicalCores = data.data.physical_cores;
                // 使用进程CPU使用率（单个核心），与任务管理器显示一致
                const cpuPercentage = data.data.process_cpu_percentage / physicalCores;
                const cpuValueElement = document.getElementById('cpu-value');
                
                if (cpuValueElement) {
                    // 更新CPU显示值
                    cpuValueElement.textContent = `${cpuPercentage.toFixed(1)}%`;
                    
                    // 根据CPU占用率更新样式类
                    if (cpuPercentage < 30) {
                        cpuValueElement.className = 'task-usage-value low';
                    } else if (cpuPercentage < 70) {
                        cpuValueElement.className = 'task-usage-value medium';
                    } else {
                        cpuValueElement.className = 'task-usage-value high';
                    }
                }
                
                // 处理内存使用量（转换为MB）
                const memoryBytes = data.data.process_memory_bytes;
                const memoryMB = (memoryBytes / (1024 * 1024)).toFixed(0);
                const ramValueElement = document.getElementById('ram-value');
                
                if (ramValueElement) {
                    // 更新内存显示值
                    ramValueElement.textContent = `${memoryMB}M`;
                    
                    // 根据内存占用率更新样式类
                    const memoryPercentage = data.data.process_memory_percentage;
                    if (memoryPercentage < 30) {
                        ramValueElement.className = 'task-usage-value low';
                    } else if (memoryPercentage < 70) {
                        ramValueElement.className = 'task-usage-value medium';
                    } else {
                        ramValueElement.className = 'task-usage-value high';
                    }
                }
            }
        })
        .catch(error => {
            if (error !== 'redirected') {
                console.error('获取系统资源占用失败:', error);
            }
        });
}

// 缓存管理函数

// 获取更新状态缓存
function getUpdateStatusCache() {
    try {
        const cachedData = sessionStorage.getItem('bilimate_update_status');
        if (cachedData) {
            return JSON.parse(cachedData);
        }
    } catch (error) {
        console.error('获取更新状态缓存失败:', error);
    }
    return null;
}

// 设置更新状态缓存
function setUpdateStatusCache(data) {
    try {
        // 不缓存forceUpdate字段，避免一直弹窗提醒
        const cacheData = {
            is_available: data.is_available,
            latest_version: data.latest_version,
            release_notes: data.release_notes,
            timestamp: Date.now()
        };
        sessionStorage.setItem('bilimate_update_status', JSON.stringify(cacheData));
    } catch (error) {
        console.error('设置更新状态缓存失败:', error);
    }
}

// 清除更新状态缓存
function clearUpdateStatusCache() {
    try {
        sessionStorage.removeItem('bilimate_update_status');
    } catch (error) {
        console.error('清除更新状态缓存失败:', error);
    }
}

// 初始化升级功能
function initUpgradeFeature() {
    // 版本号元素
    const versionElement = document.getElementById('current-version');
    if (versionElement) {
        versionElement.addEventListener('click', function() {
            checkForUpdates();
        });
    }
    
    // 页面加载时自动检查升级
    checkForUpdatesOnLoad();
}

// 页面加载时检查升级
function checkForUpdatesOnLoad() {
    // 检查是否有缓存的升级状态
    const cachedStatus = getUpdateStatusCache();
    if (cachedStatus) {
        console.log('使用缓存的升级状态:', cachedStatus);
        
        // 有新版本可用
        if (cachedStatus.is_available) {
            const versionElement = document.getElementById('current-version');
            if (versionElement) {
                // 添加新版本提示样式类
                versionElement.classList.add('update-available');
                
                // 更新title属性
                versionElement.title = `发现新版本 v${cachedStatus.latest_version}，点击检查升级`;
            }
        }
        return;
    }
    
    // 没有缓存，发送检查升级请求
    fetch('/api/check_update', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        console.log('页面加载时检查升级结果:', result);

        if (result.success) {
            const data = result.data || {};
            // 存储升级状态到缓存（不包含forceUpdate）
            setUpdateStatusCache(data);
            
            if (data.is_available) {
                // 有新版本可用
                const versionElement = document.getElementById('current-version');
                if (versionElement) {
                    // 添加新版本提示样式类
                    versionElement.classList.add('update-available');
                    
                    // 更新title属性
                    versionElement.title = `发现新版本 v${data.latest_version}，点击检查升级`;
                }
                
                // 只有当forceUpdate为true时才主动弹窗
                if (data.forceUpdate) {
                    // 显示升级提示（和手动检测一样）
                    Popup.confirm(
                        `发现新版本 v${data.latest_version}，是否升级？`,
                        {
                            title: '升级提示',
                            message: data.release_notes || ''
                        }
                    ).then(function(confirmed) {
                        if (confirmed) {
                            downloadAndUpgrade(data.download_url);
                        }
                    });
                }
            }
        }
    })
    .catch(error => {
        console.error('页面加载时检查升级失败:', error);
        // 页面加载时检查升级失败，不显示错误提示，避免打扰用户
    });
}

// 检查升级
function checkForUpdates() {
    const versionElement = document.getElementById('current-version');
    if (versionElement) {
        // 保存原始版本号文本
        versionElement.setAttribute('data-original-text', versionElement.textContent);
        versionElement.style.pointerEvents = 'none';
        versionElement.textContent = '检查中...';
    }

    // 发送检查升级请求
    fetch('/api/check_update', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        console.log('检查升级结果:', result);

        if (result.success) {
            const data = result.data || {};
            // 手动检查升级后更新缓存
            setUpdateStatusCache(data);
            
            if (data.is_available) {
                // 有新版本可用，显示升级提示
                Popup.confirm(
                    `发现新版本 v${data.latest_version}，是否升级？`,
                    {
                        title: '升级提示',
                        message: data.release_notes || ''
                    }
                ).then(function(confirmed) {
                    if (confirmed) {
                        downloadAndUpgrade(data.download_url);
                    }
                });
            } else {
                // 已经是最新版本
                Popup.alert('当前已是最新版本', { type: Popup.Type.INFO });
            }
        } else {
            Popup.alert(result.message || '检查升级失败', { type: Popup.Type.ERROR });
        }
    })
    .catch(error => {
        console.error('检查升级失败:', error);
        Popup.alert('检查升级失败，请稍后重试', { type: Popup.Type.ERROR });
    })
    .finally(() => {
        if (versionElement) {
            versionElement.style.pointerEvents = 'auto';
            // 恢复原始版本号，保留 'v' 前缀
            const originalText = versionElement.getAttribute('data-original-text') || 'v1.0.0';
            versionElement.textContent = originalText;
        }
    });
}

// 下载并升级
function downloadAndUpgrade(downloadUrl) {
    let progressPopup = null;
    
    // 检查升级前条件
    fetch('/api/check_upgrade_preconditions', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(result => {
        if (!result.success) {
            throw new Error(result.message || '检查升级前条件失败');
        }
        
        const preconditionResult = result.data;
        
        // 根据提示类型显示不同的弹窗
        if (preconditionResult.type === 'error') {
            // 错误提示，只有确认按钮
            Popup.alert(preconditionResult.message, { type: Popup.Type.ERROR });
            return Promise.reject(new Error(preconditionResult.message));
        } else if (preconditionResult.type === 'warning') {
            // 警告提示，有取消和确认按钮
            return Popup.confirm(preconditionResult.message, {
                title: '警告',
                type: Popup.Type.WARNING
            });
        } else if (preconditionResult.type === 'info') {
            // 信息提示，只有确认按钮
            return Popup.alert(preconditionResult.message, {
                type: Popup.Type.INFO
            }).then(() => true);
        }
    })
    .then(confirmed => {
        if (!confirmed) {
            return Promise.reject(new Error('用户取消升级'));
        }
        
        // 创建不可关闭的进度弹窗
        progressPopup = Popup.createProgressPopup('升级中', '开始下载升级包...');

        // 发送下载升级包请求（使用SSE流式传输）
        return fetch('/api/download_update_stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ download_url: downloadUrl })
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 获取响应流
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let downloadResult = null;
        let downloadError = null;
        
        // 处理流数据
        function processStream() {
            return reader.read().then(({ done, value }) => {
                if (done) {
                    // 流结束
                    if (downloadError) {
                        throw new Error(downloadError);
                    } else if (downloadResult) {
                        return downloadResult;
                    } else {
                        throw new Error('下载失败：未知错误');
                    }
                }
                
                // 解码数据
                buffer += decoder.decode(value, { stream: true });
                
                // 处理SSE事件
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // 保留不完整的最后一行
                
                lines.forEach(line => {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.substring(6);
                        try {
                            const data = JSON.parse(dataStr);
                            
                            // 处理不同类型的事件
                            switch (data.type) {
                                case 'progress':
                                    // 更新进度条
                                    Popup.updateProgressPopup(progressPopup, data.progress, data.downloaded, data.total);
                                    break;
                                case 'complete':
                                    // 下载完成
                                    downloadResult = data.result;
                                    break;
                                case 'error':
                                    // 下载错误
                                    downloadError = data.message;
                                    break;
                            }
                        } catch (e) {
                            console.error('解析SSE数据失败:', e);
                        }
                    }
                });
                
                // 继续处理流
                return processStream();
            });
        }
        
        return processStream();
    })
    .then(result => {
        console.log('下载升级包结果:', result);

        if (result.success) {
            // 下载成功，确保进度条显示100%
            Popup.updateProgressPopup(progressPopup, 100, result.data.file_size, result.data.file_size);
            
            // 短暂延迟，让用户看到100%的进度
            return new Promise(resolve => {
                setTimeout(() => {
                    // 开始升级
                    fetch('/api/update_application', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ upgrade_package_path: result.data.download_path })
                    })
                    .then(response => response.json())
                    .then(upgradeResult => {
                        resolve(upgradeResult);
                    });
                }, 500);
            });
        } else {
            throw new Error(result.message || '下载升级包失败');
        }
    })
    .then(upgradeResult => {
        if (upgradeResult.success) {
            // 关闭进度弹窗
            Popup.closeProgressPopup(progressPopup);
            
            // 升级成功，提示用户重启应用
            Popup.confirm(
                '升级成功，请重启应用以应用更改',
                {
                    title: '升级成功'
                }
            ).then(function(confirmed) {
                if (confirmed) {
                    // 调用重启应用API
                    fetch('/api/restart_application', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(result => {
                        if (!result.success) {
                            console.error('重启失败:', result.message);
                            Popup.alert(`重启失败: ${result.message}`, { type: Popup.Type.ERROR });
                        } else {
                            showRestartCountdown();
                        }
                    })
                    .catch(error => {
                        console.error('重启请求失败:', error);
                        // 重启请求可能会因为连接中断而失败，这是正常的
                        showRestartCountdown();
                    });
                }
            });
        } else {
            throw new Error(upgradeResult.message || '升级应用失败');
        }
    })
    .catch(error => {
        console.error('升级失败:', error);
        // 关闭进度弹窗
        Popup.closeProgressPopup(progressPopup);
        // 显示错误信息
        Popup.alert(`升级失败: ${error.message}`, { type: Popup.Type.ERROR });
    });
}

// 显示重启倒计时弹窗
function showRestartCountdown() {
    // 创建倒计时弹窗（无进度条）
    const countdownPopup = Popup.createCountdownPopup('应用重启中', '应用重启中，5秒后自动刷新...');
    
    let countdown = 5;
    
    // 更新倒计时
    const countdownInterval = setInterval(() => {
        countdown--;
        if (countdown > 0) {
            // 更新弹窗消息
            const messageElement = countdownPopup.querySelector('.popup-message');
            if (messageElement) {
                messageElement.textContent = `应用重启中，${countdown}秒后自动刷新...`;
            }
        } else {
            clearInterval(countdownInterval);
            // 尝试刷新页面
            try {
                window.location.reload();
                // 如果刷新成功，这行代码之后的内容不会执行
                // 关闭弹窗
                Popup.closeProgressPopup(countdownPopup);
            } catch (refreshError) {
                // 刷新失败，提示用户手动刷新
                Popup.closeProgressPopup(countdownPopup);
                Popup.alert('自动刷新失败，请手动刷新页面', { type: Popup.Type.WARNING });
            }
        }
    }, 1000);
}

// 在DOM加载完成后初始化升级功能
document.addEventListener('DOMContentLoaded', function() {
    initUpgradeFeature();
});
