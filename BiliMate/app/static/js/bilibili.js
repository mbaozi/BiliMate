/* BiliMate B站相关功能整合JavaScript */

// --------------
// 登录页面相关功能
// --------------

// 登录状态轮询间隔（毫秒）
const POLL_INTERVAL = 2000;

// 登录状态轮询定时器
let pollTimer = null;

// 登录二维码Key
let qrcodeKey = null;

// --------------
// 账号管理相关功能
// --------------

// DOM加载完成后执行
(document.addEventListener('DOMContentLoaded', function() {
    // 初始化登录页面功能（如果在登录页面）
    if (window.location.pathname === '/bilibili/login') {
        initLoginPage();
        generateLoginQRCode();
    }
    
    // 初始化账号管理功能（如果在包含账号管理的页面）
    if (document.querySelector('.toggle-autoreply') || document.querySelector('.remove-account')) {
        initAccountManagement();
    }
    
    // 初始化仪表盘功能（如果在仪表盘页面）
    if (window.location.pathname === '/bilibili/dashboard') {
        // 从页面中获取mid，检查多个可能的位置
        let mid = null;
        
        // 从toggle-autoreply按钮中获取mid
        const statusBtn = document.querySelector('.toggle-autoreply');
        if (statusBtn) {
            mid = statusBtn.dataset.mid;
        }
        
        // 如果找到了mid，调用初始化函数
        if (mid) {
            initializeBilibiliDashboard(mid);
        }
    }
}));

/**
 * 初始化登录页面
 */
function initLoginPage() {
    // 绑定刷新按钮事件
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            generateLoginQRCode();
        });
    }
}

/**
 * 初始化账号管理功能
 */
function initAccountManagement() {
    // 为所有切换状态按钮添加点击事件
    document.querySelectorAll('.toggle-autoreply').forEach(button => {
        button.addEventListener('click', handleToggleAutoreply);
    });
    
    // 为所有设置按钮添加点击事件
    document.querySelectorAll('.settings-btn').forEach(button => {
        button.addEventListener('click', handleConfigClick);
    });
    
    // 为所有移除按钮添加点击事件
    document.querySelectorAll('.remove-account').forEach(button => {
        button.addEventListener('click', handleRemoveAccount);
    });
}

/**
 * 处理设置按钮点击事件
 */
function handleConfigClick(e) {
    e.preventDefault();
    e.stopPropagation(); // 阻止事件冒泡，避免触发卡片点击事件
    
    const mid = this.dataset.mid;
    
    // 跳转到通用的自动回复配置页面
    window.location.href = `/replyconfig?platform=bilibili&mid=${mid}`;
}

// ------------------------
// 匹配字典表格相关功能
// ------------------------

/**
 * 初始化匹配字典表格功能
 */
function initMatchTables() {
    // 为所有添加新项按钮添加点击事件
    document.querySelectorAll('.btn[data-table]').forEach(button => {
        button.addEventListener('click', handleAddRow);
    });
    
    // 为所有删除按钮添加点击事件
    document.querySelectorAll('.remove-row').forEach(button => {
        button.addEventListener('click', handleRemoveRow);
    });
    
    // 为所有表单添加提交事件，将表格数据转换为JSON
    const settingForms = document.querySelectorAll('.setting-form');
    settingForms.forEach(form => {
        form.addEventListener('submit', handleSettingFormSubmit);
    });
}

/**
 * 处理添加新行按钮点击事件
 */
function handleAddRow(e) {
    e.preventDefault();
    
    // 获取表格ID
    const tableId = this.dataset.table;
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    // 创建新行
    const newRow = document.createElement('tr');
    
    // 根据表格ID确定输入框的name属性前缀
    const namePrefix = tableId.replace('_table', '');
    
    // 设置行内容
    newRow.innerHTML = `
        <td><input type="text" name="${namePrefix}_key[]" class="form-control table-input" placeholder="关键词"></td>
        <td><input type="text" name="${namePrefix}_value[]" class="form-control table-input" placeholder="回复内容"></td>
        <td>
            <button type="button" class="btn btn-sm btn-danger remove-row">
                删除
            </button>
        </td>
    `;
    
    // 添加到表格
    tbody.appendChild(newRow);
    
    // 为新添加的删除按钮添加事件监听器
    newRow.querySelector('.remove-row').addEventListener('click', handleRemoveRow);
}

/**
 * 处理删除行按钮点击事件
 */
function handleRemoveRow(e) {
    e.preventDefault();
    
    // 获取当前行
    const row = this.closest('tr');
    if (row) {
        row.remove();
    }
}

/**
 * 处理设置表单提交事件，简化版，只负责提交表单
 */
function handleSettingFormSubmit(e) {
    // 获取当前提交的表单
    const form = e.target;
    
    // 验证表单数据
    if (!validateForm(form)) {
        e.preventDefault();
        return;
    }
    
    // 检查表单中是否包含对应的表格和隐藏字段
    // 处理粉丝相关表格
    if (form.querySelector('#fans_complete_table') && form.querySelector('#fans_complete_dict')) {
        updateTableToJson('fans_complete_table', 'fans_complete_dict');
    }
    
    if (form.querySelector('#fans_keyword_table') && form.querySelector('#fans_keyword_dict')) {
        updateTableToJson('fans_keyword_table', 'fans_keyword_dict');
    }
    
    // 处理非粉丝相关表格
    if (form.querySelector('#non_fans_complete_table') && form.querySelector('#non_fans_complete_dict')) {
        updateTableToJson('non_fans_complete_table', 'non_fans_complete_dict');
    }
    
    if (form.querySelector('#non_fans_keyword_table') && form.querySelector('#non_fans_keyword_dict')) {
        updateTableToJson('non_fans_keyword_table', 'non_fans_keyword_dict');
    }
    
    // 简化版：移除所有不必要的字段检查和处理，只保留基本的表单提交功能
    // 直接提交表单，不做其他处理
}

/**
 * 验证表单数据
 * @param {HTMLFormElement} form - 表单元素
 * @returns {boolean} - 是否验证通过
 */
function validateForm(form) {
    // 检查是否为通用设置表单
    if (form.id === 'general-form') {
        return validateGeneralForm(form);
    }
    
    // 其他表单暂时不需要验证
    return true;
}

/**
 * 验证通用设置表单
 * @param {HTMLFormElement} form - 通用设置表单元素
 * @returns {boolean} - 是否验证通过
 */
function validateGeneralForm(form) {
    // 获取表单字段
    const repetProtectTimes = form.querySelector('#repet_protect_times');
    const replyIntervalSeconds = form.querySelector('#reply_interval_seconds');
    
    // 验证重复回复保护次数
    if (!repetProtectTimes.value || isNaN(repetProtectTimes.value) || parseInt(repetProtectTimes.value) < 3 || parseInt(repetProtectTimes.value) > 100) {
        Popup.error('请输入3-100之间的重复回复保护次数！');
        repetProtectTimes.focus();
        return false;
    }
    
    // 验证回复间隔秒数
    if (!replyIntervalSeconds.value || isNaN(replyIntervalSeconds.value) || parseInt(replyIntervalSeconds.value) < 1 || parseInt(replyIntervalSeconds.value) > 60) {
        Popup.error('请输入1-60之间的回复间隔秒数！');
        replyIntervalSeconds.focus();
        return false;
    }
    
    return true;
}

/**
 * 将表格数据转换为JSON格式，并更新到隐藏字段
 * @param {string} tableId - 表格ID
 * @param {string} hiddenFieldId - 隐藏字段ID
 */
function updateTableToJson(tableId, hiddenFieldId) {
    const table = document.getElementById(tableId);
    const hiddenField = document.getElementById(hiddenFieldId);
    
    if (!table || !hiddenField) return;
    
    const rows = table.querySelectorAll('tbody tr');
    const result = {};
    
    // 根据表格ID确定输入框的name属性前缀
    const namePrefix = tableId.replace('_table', '');
    
    // 遍历所有行，构建JSON对象
    rows.forEach(row => {
        const keyInput = row.querySelector(`input[name^="${namePrefix}_key"]`);
        const valueInput = row.querySelector(`input[name^="${namePrefix}_value"]`);
        
        if (keyInput && valueInput && keyInput.value.trim()) {
            const key = keyInput.value.trim();
            const value = valueInput.value.trim();
            result[key] = value;
        }
    });
    
    // 将JSON对象转换为字符串，并更新到隐藏字段
    hiddenField.value = JSON.stringify(result);
}

// 在DOM加载完成后初始化匹配字典表格功能
(document.addEventListener('DOMContentLoaded', function() {
    // 检查是否在自动回复配置页面
    if (window.location.pathname === '/replyconfig') {
        initMatchTables();
        initSettingToggles();
        initResetDefaultButtons();
        initTemplateSwitch();
    }
}));



/**
 * 初始化恢复默认按钮功能
 */
function initResetDefaultButtons() {
    // 为所有恢复默认按钮添加点击事件监听器
    const resetButtons = document.querySelectorAll('.btn-reset-default');
    resetButtons.forEach(button => {
        button.addEventListener('click', handleResetDefaultClick);
    });
}

/**
 * 初始化模板切换功能
 */
function initTemplateSwitch() {
    // 获取模板切换相关元素
    const templateSwitchSelect = document.getElementById('template-switch-select');
    const templateId = new URLSearchParams(window.location.search).get('template_id');
    const mid = new URLSearchParams(window.location.search).get('mid');
    
    if (templateSwitchSelect) {
        // 监听下拉框变化事件
        templateSwitchSelect.addEventListener('change', async function() {
            const selectedValue = this.value;
            
            // 检查是否在模板编辑页面
            if (templateId) {
                // 模板编辑页面：直接跳转到所选模板的编辑页面
                if (await Popup.confirm('确定要切换到所选模板吗？当前编辑内容将丢失。')) {
                    window.location.href = `/replyconfig?template_id=${selectedValue}`;
                } else {
                    // 如果取消，恢复原来的选中项
                    // 这里需要获取原来的模板ID，暂时无法实现，所以不恢复
                }
            } else if (mid) {
                // 账号设置页面：执行模板切换操作
                if (selectedValue === 'custom') {
                    // 切换为自定义设置
                    if (await Popup.confirm('确定要切换为自定义设置吗？当前设置将与模板脱离关联。')) {
                        switchToCustomSetting(mid);
                    } else {
                        // 如果取消，恢复原来的选中项
                        // 这里需要获取原来的模板ID，暂时无法实现，所以不恢复
                    }
                } else {
                    // 应用模板
                    if (await Popup.confirm('确定要应用所选模板吗？当前设置将被模板覆盖。')) {
                        applyTemplateToAccount(mid, selectedValue);
                    } else {
                        // 如果取消，恢复原来的选中项
                        // 这里需要获取原来的模板ID，暂时无法实现，所以不恢复
                    }
                }
            }
        });
    }
}

/**
 * 处理模板切换
 */
function handleTemplateSwitch() {
    // 这个函数已经不再使用，因为现在直接通过下拉框变化事件处理
}

/**
 * 切换到自定义设置
 */
function switchToCustomSetting(mid) {
    fetch('/bilibili/switch_to_custom', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            mid: mid
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Popup.success('已切换为自定义设置！');
            window.location.reload();
        } else {
            Popup.error('切换失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('切换到自定义设置失败:', error);
        Popup.error('切换失败，请重试');
    });
}

/**
 * 应用模板到账号
 */
function applyTemplateToAccount(mid, templateId) {
    fetch('/bilibili/apply_template', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            mid: mid,
            template_id: templateId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Popup.success('模板应用成功！');
            window.location.reload();
        } else {
            Popup.error('模板应用失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('应用模板失败:', error);
        Popup.error('应用模板失败，请重试');
    });
}

/**
 * 处理恢复默认按钮点击事件
 * @param {Event} e - 点击事件对象
 */
async function handleResetDefaultClick(e) {
    e.preventDefault();
    
    // 获取表单ID
    const formId = this.dataset.form;
    const form = document.getElementById(formId);
    if (!form) return;
    
    // 显示确认弹窗
    if (await Popup.confirm('确定要恢复默认设置吗？此操作不可撤销！')) {
        // 创建恢复默认请求
        const formData = new FormData(form);
        formData.append('reset_default', 'true');
        
        // 发送请求到后端
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                // 重新加载页面以显示更新后的设置
                window.location.reload();
            } else {
                Popup.error('恢复默认设置失败');
            }
        } catch (error) {
            console.error('恢复默认设置错误:', error);
            Popup.error('恢复默认设置失败');
        }
    }
}

/**
 * 初始化设置页面的开关功能
 */
function initSettingToggles() {
    // 为所有切换开关添加事件监听器
    const toggleSwitches = document.querySelectorAll('.toggle-switch input[type="checkbox"]');
    toggleSwitches.forEach(switchInput => {
        // 初始化状态
        updateToggleSectionStatus(switchInput);
        
        // 添加change事件监听器
        switchInput.addEventListener('change', function() {
            updateToggleSectionStatus(this);
        });
    });
}

/**
 * 更新切换开关对应的内容区域状态
 * @param {HTMLElement} switchInput - 切换开关元素
 */
function updateToggleSectionStatus(switchInput) {
    // 获取开关状态
    const isEnabled = switchInput.checked;
    
    // 找到包含开关的form元素
    const formElement = switchInput.closest('form');
    if (!formElement) return;
    
    // 找到该form中的所有setting-row元素
    const settingRows = formElement.querySelectorAll('.setting-row');
    
    // 更新所有setting-row的状态
    settingRows.forEach(settingRow => {
        if (isEnabled) {
            // 启用状态
            settingRow.style.opacity = '1';
            settingRow.style.pointerEvents = 'auto';
            
            // 启用所有输入元素
            const inputs = settingRow.querySelectorAll('input, textarea, button');
            inputs.forEach(input => {
                input.disabled = false;
            });
        } else {
            // 禁用状态
            settingRow.style.opacity = '0.6';
            settingRow.style.pointerEvents = 'none';
            
            // 禁用所有输入元素
            const inputs = settingRow.querySelectorAll('input, textarea, button');
            inputs.forEach(input => {
                input.disabled = true;
            });
        }
    });
}

/**
 * 生成登录二维码
 */
function generateLoginQRCode() {    
    // 清除之前的定时器
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
    
    // 显示加载状态
    showLoading(true);
    updateStatus('正在生成登录二维码...', 'waiting');
    
    // 发送请求生成二维码
    fetch('/bilibili/login/generate_qrcode', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        return response.json();
    })
    .then(data => {        
        if (data.success && data.data) {
            // 获取二维码URL和Key
            const loginUrl = data.data.url;
            qrcodeKey = data.data.qrcode_key;
            
            if (loginUrl) {
                // 使用QRCode.js生成二维码
                generateQRCodeImage(loginUrl);
                updateStatus('未扫码，请及时扫码', 'waiting');
            } else {
                updateStatus('生成失败，请重新生成', 'error');
            }
            
            // 开始轮询登录状态
            startPollingLoginStatus();
        } else {
            // 生成失败
            updateStatus('生成失败，请重新生成', 'error');
        }
    })
    .catch(error => {
        console.error('生成二维码失败:', error);
        updateStatus('生成失败，请重新生成', 'error');
    })
    .finally(() => {
        // 隐藏加载状态
        showLoading(false);
    });
}

/**
 * 使用QRCode.js生成二维码图片
 * @param {string} url - 登录URL
 */
function generateQRCodeImage(url) {    
    // 获取二维码容器
    const qrcodeContainer = document.getElementById('qrcode-container');
    if (!qrcodeContainer) {
        console.error('未找到二维码容器');
        return;
    }
    
    // 清除容器内之前的内容（除了加载动画）
    const loadingSpinner = qrcodeContainer.querySelector('.loading-spinner');
    qrcodeContainer.innerHTML = '';
    if (loadingSpinner) {
        qrcodeContainer.appendChild(loadingSpinner);
    }
    
    try {
        // 生成二维码
        const qr = qrcode(0, 'L');
        qr.addData(url);
        qr.make();
        
        // 创建二维码图片元素
        qrcodeContainer.innerHTML += qr.createImgTag(4, 0);
    } catch (error) {
        console.error('使用QRCode.js生成二维码失败:', error);
        updateStatus('已失效，请重新生成', 'error');
    }
}

/**
 * 开始轮询登录状态
 */
function startPollingLoginStatus() {
    // 清除之前的定时器
    if (pollTimer) {
        clearInterval(pollTimer);
    }
    
    // 设置轮询定时器
    pollTimer = setInterval(function() {
        checkLoginStatus();
    }, POLL_INTERVAL);
}

/**
 * 检查登录状态
 */
function checkLoginStatus() {
    if (!qrcodeKey) {
        return;
    }
    
    // 发送请求检查登录状态
    fetch('/bilibili/login/check_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            qrcode_key: qrcodeKey
        })
    })
    .then(response => response.json())
    .then(result => {
        // 直接从返回结果获取状态和消息
        const status = result.data?.status || 'waiting';
        const message = result.message || '未知状态';
        
        // 更新状态显示
        updateStatus(message, status);
        
        // 根据状态处理
        if (status === 'success') {
            // 登录成功
            // 清除轮询定时器
            if (pollTimer) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
            
            // 登录成功，跳转到首页
            setTimeout(function() {
                window.location.href = '/';
            }, 1500);
        } else if (status === 'error' || status === 'expired') {
            // 错误或二维码已失效，停止轮询
            if (pollTimer) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
            
            // 添加激活错误弹窗处理
            if (message && message.includes('应用未激活')) {
                // 使用全局激活错误处理函数
                if (window.handleActivationError) {
                    window.handleActivationError(message);
                } else {
                    Popup.alert(message, { type: Popup.Type.WARNING });
                }
            } else if (status === 'error') {
                // 显示普通错误弹窗
                Popup.error(message);
            }
        }
        // 其他状态（scanned, waiting）继续轮询
    })
    .catch(error => {
        console.error('检查登录状态失败:', error);
    });
}

/**
 * 更新登录状态
 * @param {string} message - 状态消息
 * @param {string} status - 状态类型：waiting, scanned, success, error
 */
function updateStatus(message, status) {
    const statusElement = document.getElementById('login-status');
    if (statusElement) {
        // 更新消息内容
        statusElement.textContent = message;
        
        // 移除之前的状态类
        statusElement.className = 'status-indicator';
        
        // 添加新的状态类
        statusElement.classList.add(status);
    }
}

/**
 * 显示/隐藏加载状态
 * @param {boolean} show - 是否显示加载状态
 */
function showLoading(show) {
    let loadingSpinner = document.getElementById('loading-spinner');
    
    // 如果loading-spinner不存在，创建它
    if (!loadingSpinner) {
        const qrcodeContainer = document.getElementById('qrcode-container');
        if (qrcodeContainer) {
            loadingSpinner = document.createElement('div');
            loadingSpinner.id = 'loading-spinner';
            loadingSpinner.className = 'loading-spinner';
            qrcodeContainer.appendChild(loadingSpinner);
        }
    }
    
    if (loadingSpinner) {
        if (show) {
            loadingSpinner.classList.add('loading');
            // 隐藏二维码图片（如果存在）
            const qrcodeImages = document.querySelectorAll('#qrcode-container img');
            qrcodeImages.forEach(img => {
                img.style.display = 'none';
            });
        } else {
            loadingSpinner.classList.remove('loading');
        }
    }
}

/**
 * 处理账号自动回复状态切换
 */
async function handleToggleAutoreply(e) {
    e.preventDefault();
    e.stopPropagation(); // 阻止事件冒泡，避免触发卡片点击事件
    
    const mid = this.dataset.mid;
    const action = this.dataset.action;
    const isActivating = action === 'activate';
    
    // 显示确认弹窗
    if (await Popup.confirm(`确定要${isActivating ? '启用' : '停用'}该账号的自动回复功能吗？`)) {
        // 发送请求切换账号状态
        fetch('/bilibili/toggle_autoreply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mid: mid
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 显示成功提示
                Popup.success(data.message);
                
                // 刷新页面，让模板引擎自动更新按钮样式和文本
                window.location.reload();
            } else {
                // 显示错误提示
                Popup.error(data.message || '操作失败');
            }
        })
        .catch(error => {
            console.error('切换账号自动回复状态失败:', error);
            Popup.error('操作失败，请重试');
        });
    }
}

/**
 * 处理账号移除
 */
async function handleRemoveAccount(e) {
    e.preventDefault();
    e.stopPropagation(); // 阻止事件冒泡，避免触发卡片点击事件
    
    const mid = this.dataset.mid;
    const card = this.closest('.page-card-link');
    
    // 显示确认弹窗
    if (await Popup.confirm('确定要移除该账号吗？此操作不可恢复！')) {
        // 发送请求移除账号
        fetch('/bilibili/remove_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mid: mid
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 移除卡片
                if (card) {
                    card.remove();
                }
                
                // 显示成功提示
                Popup.success(data.message);
            } else {
                // 显示错误提示
                Popup.error(data.message || '移除失败');
            }
        })
        .catch(error => {
            console.error('移除账号失败:', error);
            Popup.error('移除失败，请重试');
        });
    }
}

/**
 * 页面卸载时清理资源
 */
window.addEventListener('beforeunload', function() {
    // 清除轮询定时器
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
});

// --------------
// 仪表盘页面相关功能
// --------------

/**
 * 定期更新视频数据
 */
function initializeBilibiliDashboard(mid) {
    // 更新间隔时间（毫秒），默认1小时，后续可通过参数配置
    const UPDATE_INTERVAL = 3600000;
    
    // 更新视频数据的函数
    function updateVideoData() {
        fetch(`/bilibili/update_video_data?mid=${mid}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新页面上的统计数据
                    const stats = data.data.stat;
                    
                    // 更新总粉丝数
                    const fansElement = document.querySelector('.stats-card-primary .stats-card-value');
                    if (fansElement) {
                        fansElement.textContent = stats.total_fans || 0;
                    }
                    const fansIncElement = document.querySelector('.stats-card-primary .stats-card-increase');
                    if (fansIncElement) {
                        const fansInc = stats.incr_fans || 0;
                        fansIncElement.textContent = `${fansInc > 0 ? '↗' : fansInc < 0 ? '↘' : '−'} ${fansInc}`;
                        fansIncElement.className = `stats-card-increase ${fansInc > 0 ? 'positive' : fansInc < 0 ? 'negative' : 'neutral'}`;
                    }
                    
                    // 更新总播放量
                    const viewElement = document.querySelector('.stats-card-success .stats-card-value');
                    if (viewElement) {
                        viewElement.textContent = stats.total_click || 0;
                    }
                    const viewIncElement = document.querySelector('.stats-card-success .stats-card-increase');
                    if (viewIncElement) {
                        const viewInc = stats.incr_click || 0;
                        viewIncElement.textContent = `${viewInc > 0 ? '↗' : viewInc < 0 ? '↘' : '−'} ${viewInc}`;
                        viewIncElement.className = `stats-card-increase ${viewInc > 0 ? 'positive' : viewInc < 0 ? 'negative' : 'neutral'}`;
                    }
                    
                    // 更新总点赞数
                    const likesElement = document.querySelector('.stats-card-accent .stats-card-value');
                    if (likesElement) {
                        likesElement.textContent = stats.total_like || 0;
                    }
                    const likesIncElement = document.querySelector('.stats-card-accent .stats-card-increase');
                    if (likesIncElement) {
                        const likesInc = stats.inc_like || 0;
                        likesIncElement.textContent = `${likesInc > 0 ? '↗' : likesInc < 0 ? '↘' : '−'} ${likesInc}`;
                        likesIncElement.className = `stats-card-increase ${likesInc > 0 ? 'positive' : likesInc < 0 ? 'negative' : 'neutral'}`;
                    }
                    
                    // 更新总收藏数
                    const favElement = document.querySelector('.stats-card-secondary .stats-card-value');
                    if (favElement) {
                        favElement.textContent = stats.total_fav || 0;
                    }
                    const favIncElement = document.querySelector('.stats-card-secondary .stats-card-increase');
                    if (favIncElement) {
                        const favInc = stats.inc_fav || 0;
                        favIncElement.textContent = `${favInc > 0 ? '↗' : favInc < 0 ? '↘' : '−'} ${favInc}`;
                        favIncElement.className = `stats-card-increase ${favInc > 0 ? 'positive' : favInc < 0 ? 'negative' : 'neutral'}`;
                    }
                }
            })
            .catch(error => {
                console.error('更新视频数据失败:', error);
            });
    }
    
    // 页面加载时立即更新一次
    updateVideoData();
    
    // 定时更新
    setInterval(updateVideoData, UPDATE_INTERVAL);
    
    // 初始化对话列表
    initializeConversationList(mid);
    
    // 初始化对话详情模态框
    initConversationModal();
}

/**
 * 初始化对话列表更新
 */
function initializeConversationList(mid) {
    // 更新间隔时间（毫秒），默认5秒
    const UPDATE_INTERVAL = 5000;
    
    // 加载对话列表的函数
    function loadConversations() {
        fetch(`/bilibili/conversations?mid=${mid}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const conversations = data.data;
                    renderConversations(conversations);
                } else {
                    console.error('加载对话列表失败:', data.message);
                    renderNoConversations();
                }
            })
            .catch(error => {
                console.error('加载对话列表失败:', error);
                renderNoConversations();
            });
    }
    
    // 渲染对话列表
    function renderConversations(conversations) {
        const container = document.getElementById('conversations-container');
        if (!container) return;
        
        if (conversations && conversations.length > 0) {
            let html = '';
            conversations.forEach(conversation => {
                html += `
                    <div class="conversation-card">
                        <!-- 左侧头像 -->
                        <div class="conversation-avatar">
                            <img src="${conversation.talker_avatar || 'https://i0.hdslb.com/bfs/face/member/noface.jpg'}" alt="${conversation.talker_name}">
                        </div>
                        
                        <!-- 中间信息区域 -->
                        <div class="conversation-info">
                            <!-- 对话者信息 -->
                            <div class="talker-info">
                                <h4 class="talker-name">${conversation.talker_name}</h4>
                                <p class="talker-uid">UID: ${conversation.talker_id}</p>
                            </div>
                            
                            <!-- 对话统计 -->
                            <div class="conversation-stats">
                                <div class="conversation-stat">
                                    <span class="stat-label">最后对话：</span>
                                    <span class="stat-value">${conversation.last_msg_time || '无'}</span>
                                </div>
                                <div class="conversation-stat">
                                    <span class="stat-label">对话次数：</span>
                                    <span class="stat-value">${conversation.msg_count}次</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 右侧操作按钮 -->
                        <div class="conversation-actions">
                            <button class="btn btn-primary view-detail" data-talker-id="${conversation.talker_id}" data-mid="${mid}">
                                查看详情
                            </button>
                            <button class="btn btn-danger delete-conversation" data-talker-id="${conversation.talker_id}" data-mid="${mid}">
                                删除记录
                            </button>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
            
            // 绑定查看详情按钮事件
            bindViewDetailEvents();
            // 绑定删除对话按钮事件
            bindDeleteConversationEvents();
        } else {
            renderNoConversations();
        }
    }
    
    // 渲染无对话状态
    function renderNoConversations() {
        const container = document.getElementById('conversations-container');
        if (!container) return;
        
        container.innerHTML = `
            <div class="no-conversations">
                <i class="fa fa-envelope-open-o"></i> 暂无对话记录
            </div>
        `;
    }
    
    // 绑定查看详情按钮事件
    function bindViewDetailEvents() {
        const viewDetailButtons = document.querySelectorAll('.view-detail');
        viewDetailButtons.forEach(button => {
            button.addEventListener('click', function() {
                const talkerId = this.dataset.talkerId;
                const mid = this.dataset.mid;
                showConversationDetail(mid, talkerId);
            });
        });
    }
    
    // 绑定删除对话按钮事件
    function bindDeleteConversationEvents() {
        const deleteButtons = document.querySelectorAll('.delete-conversation');
        deleteButtons.forEach(button => {
            button.addEventListener('click', function() {
                const talkerId = this.dataset.talkerId;
                const mid = this.dataset.mid;
                clearConversation(mid, talkerId);
            });
        });
    }
    
    // 页面加载时立即加载一次
    loadConversations();
    
    // 定时更新
    setInterval(loadConversations, UPDATE_INTERVAL);
}

/**
 * 显示对话详情
 */
function showConversationDetail(mid, talkerId) {
    // 显示模态框
    const modal = document.getElementById('conversation-modal');
    // 设置当前对话的mid和talkerId
    modal.setAttribute('data-mid', mid);
    modal.setAttribute('data-talker-id', talkerId);
    modal.classList.add('show');
    
    // 清空容器内容
    const container = document.getElementById('conversation-messages');
    container.innerHTML = '<div class="loading-message">加载中...</div>';
    
    // 直接获取所有消息，然后按正确顺序显示
    fetch(`/bilibili/conversations/${talkerId}?mid=${mid}&limit=1000`)  // 一次获取所有消息
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 直接渲染所有消息，按正确顺序显示
                renderConversationDetail(data.data);
            } else {
                console.error('加载对话详情失败:', data.message);
                Popup.error('加载对话详情失败');
            }
        })
        .catch(error => {
            console.error('加载对话详情失败:', error);
            Popup.error('加载对话详情失败');
        });
}

/**
 * 渲染对话详情
 */
function renderConversationDetail(conversationData) {
    const container = document.getElementById('conversation-messages');
    if (!container) return;
    
    const messagePairs = conversationData.message_pairs;
    
    if (messagePairs && messagePairs.length > 0) {
        let html = '';
        messagePairs.forEach(pair => {
            // 渲染用户消息
            html += `
                <div class="message-item user-message">
                    <div class="message-content">${escapeHtml(pair.receive_msg)}</div>
                    <div class="message-time">${pair.created_at}</div>
                </div>
            `;
            
            // 渲染系统回复
            html += `
                <div class="message-item bot-message">
                    <div class="message-content">${escapeHtml(pair.reply_msg)}</div>
                    <div class="message-time">${pair.created_at}</div>
                    <div class="message-status">
                        回复状态：<span class="${pair.reply_status ? 'status-success' : 'status-danger'}">${pair.reply_status ? '成功' : '失败'}</span>
                    </div>
                </div>
            `;
        });
        
        // 直接替换内容
        container.innerHTML = html;
        
        // 滚动到底部，显示最新消息
        container.scrollTop = container.scrollHeight;
    } else {
        container.innerHTML = `
            <div class="no-conversations">
                <i class="fa fa-comments-o"></i> 暂无对话内容
            </div>
        `;
    }
}



/**
 * HTML转义函数
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 初始化对话详情模态框
 */
function initConversationModal() {
    // 关闭按钮事件
    const closeBtn = document.querySelector('.modal .close');
    const modal = document.getElementById('conversation-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const clearConversationBtn = document.getElementById('clear-conversation');
    
    // 点击关闭按钮
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.classList.remove('show');
        });
    }
    
    // 点击关闭按钮
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            modal.classList.remove('show');
        });
    }
    
    // 点击清空对话按钮
    if (clearConversationBtn) {
        clearConversationBtn.addEventListener('click', function() {
            // 获取当前对话的mid和talkerId
            const mid = modal.getAttribute('data-mid');
            const talkerId = modal.getAttribute('data-talker-id');
            
            if (mid && talkerId) {
                clearConversation(mid, talkerId);
            }
        });
    }
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.classList.remove('show');
        }
    });
}

/**
 * 清空对话
 */
async function clearConversation(mid, talkerId) {
    // 显示确认弹窗
    if (await Popup.confirm('确定要清空该对话的所有记录吗？此操作不可恢复！')) {
        // 发送请求清空对话
        fetch(`/bilibili/conversations/${talkerId}/clear?mid=${mid}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 清空成功，关闭模态框并刷新对话列表
                const modal = document.getElementById('conversation-modal');
                modal.classList.remove('show');
                
                // 刷新对话列表
                initializeConversationList(mid);
                
                Popup.alert('对话已清空', { type: Popup.Type.SUCCESS });
            } else {
                console.error('清空对话失败:', data.message);
                Popup.alert('清空对话失败: ' + data.message, { type: Popup.Type.ERROR });
            }
        })
        .catch(error => {
            console.error('清空对话失败:', error);
            Popup.alert('清空对话失败，请重试', { type: Popup.Type.ERROR });
        });
    }
}
