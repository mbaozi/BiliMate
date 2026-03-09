/* BiliMate 自动回复配置JavaScript文件 */

// API相关功能
let apiWrappers = [];

/**
 * 检查激活状态并禁用/启用高级功能
 */
async function checkActivationStatusForAdvancedFeatures() {
    try {
        const response = await fetch('/api/check_activation_status');
        const data = await response.json();
        const isActivated = data.success && data.data.is_activated;
        
        // 获取用户信息
        const userResponse = await fetch('/api/user_info');
        const userData = await userResponse.json();
        const isVip = userData.success && userData.data.user_level === 'vip';
        
        // 获取所有API选择下拉框
        const apiSelects = document.querySelectorAll('.api-select');
        apiSelects.forEach(select => {
            select.disabled = !isActivated || !isVip;
            
            // 添加提示信息
            if (!isActivated || !isVip) {
                select.title = '应用未激活或非VIP用户，无法使用API功能';
            } else {
                select.title = '';
            }
        });
        
        // 处理个性标识输入框
        const personalityInput = document.getElementById('personality_identifier');
        if (personalityInput) {
            personalityInput.disabled = !isActivated || !isVip;
            
            // 添加提示信息
            if (!isActivated || !isVip) {
                personalityInput.title = '应用未激活或非VIP用户，无法使用个性标识功能';
            } else {
                personalityInput.title = '';
            }
        }
    } catch (error) {
        console.error('检查激活状态失败:', error);
        // 出错时默认禁用API选择下拉框和个性标识输入框
        const apiSelects = document.querySelectorAll('.api-select');
        apiSelects.forEach(select => {
            select.disabled = true;
            select.title = '应用未激活或非VIP用户，无法使用API功能';
        });
        
        // 出错时默认禁用个性标识输入框
        const personalityInput = document.getElementById('personality_identifier');
        if (personalityInput) {
            personalityInput.disabled = true;
            personalityInput.title = '应用未激活或非VIP用户，无法使用个性标识功能';
        }
    }
}

/**
 * 加载API封装列表
 */
async function loadApiWrappers() {
    try {
        const response = await fetch('/api_wrapper/api_wrappers');
        const data = await response.json();
        if (data.success) {
            apiWrappers = data.data;
            populateApiSelects();
        }
    } catch (error) {
        console.error('加载API封装列表失败:', error);
    }
}

/**
 * 填充所有API选择下拉框
 */
function populateApiSelects() {
    const apiSelects = document.querySelectorAll('.api-select');
    apiSelects.forEach(select => {
        // 清空现有选项（保留第一个默认选项）
        select.innerHTML = '<option value="">选择API</option>';
        
        // 添加API选项
        apiWrappers.forEach(api => {
            const option = document.createElement('option');
            option.value = api.name;
            option.textContent = api.name;
            select.appendChild(option);
        });
        
        // 重新应用禁用状态
        checkActivationStatusForAdvancedFeatures();
    });
}

/**
 * 初始化API选择下拉框事件监听
 */
function initApiSelectListeners() {
    const apiSelects = document.querySelectorAll('.api-select');
    apiSelects.forEach(select => {
        select.addEventListener('change', handleApiSelectChange);
    });
}

/**
 * 处理API选择下拉框变化事件
 */
function handleApiSelectChange() {
    const apiName = this.value;
    if (!apiName) return;
    
    // 获取对应的textarea元素ID
    const selectId = this.id;
    let textareaId = '';
    
    if (selectId === 'fans_api_select') {
        textareaId = 'fans_other_reply';
    } else if (selectId === 'non_fans_api_select') {
        textareaId = 'non_fans_other_reply';
    } else if (selectId === 'new_fans_api_select') {
        textareaId = 'new_fans_reply';
    }
    
    const textarea = document.getElementById(textareaId);
    if (!textarea) return;
    
    // 生成API调用代码
    const apiCall = `{{api:${apiName}}}{{field:${apiName}:choices[0].message.content:API异常}}`;
    
    // 覆盖整个输入框内容
    textarea.value = apiCall;
    
    // 聚焦到textarea
    textarea.focus();
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
        <td><textarea name="${namePrefix}_value[]" class="form-control table-input" rows="1" style="resize: vertical;" placeholder="回复内容"></textarea></td>
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
 * 处理设置表单提交事件，使用AJAX请求
 */
function handleSettingFormSubmit(e) {
    e.preventDefault(); // 阻止默认表单提交
    
    // 获取当前提交的表单
    const form = e.target;
    
    // 验证表单数据
    if (!validateForm(form)) {
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
    
    // 收集表单数据
    const formData = new FormData(form);
    
    // 发送AJAX请求到新的API路由
    fetch('/api/save_settings', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Popup.success(data.message || '保存成功！');
        } else {
            Popup.error(data.message || '保存失败！');
        }
    })
    .catch(error => {
        console.error('保存设置错误:', error);
        Popup.error('保存失败，请重试');
    });
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
        const valueInput = row.querySelector(`textarea[name^="${namePrefix}_value"]`);
        
        if (keyInput && valueInput && keyInput.value.trim()) {
            const key = keyInput.value.trim();
            const value = valueInput.value.trim();
            result[key] = value;
        }
    });
    
    // 将JSON对象转换为字符串，并更新到隐藏字段
    hiddenField.value = JSON.stringify(result);
}

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
        
        // 发送请求到新的API路由
        try {
            const response = await fetch('/api/save_settings', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                Popup.success('恢复默认设置成功！');
                // 重新加载页面以显示更新后的设置
                window.location.reload();
            } else {
                Popup.error(data.message || '恢复默认设置失败');
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

// 在DOM加载完成后初始化所有功能
document.addEventListener('DOMContentLoaded', function() {
    initMatchTables();
    initSettingToggles();
    initResetDefaultButtons();
    initTemplateSwitch();
    
    // 初始化API相关功能
    loadApiWrappers();
    initApiSelectListeners();
    
    // 检查激活状态并禁用/启用高级功能
    checkActivationStatusForAdvancedFeatures();
});
