// 引入弹窗组件
// API管理功能 - 合并API测试和API封装管理
document.addEventListener('DOMContentLoaded', function() {
    // 初始化API管理功能
    initApiManagement();
});

// 初始化API管理功能（仅保留API封装管理）
function initApiManagement() {
    // 初始化API封装管理功能
    initApiWrapperManagement();
}



// 初始化JSON编辑器
function initKeyValueEditor(type) {
    // 获取DOM元素
    let formatBtn;
    let jsonTextarea;
    
    // 根据type类型获取不同的元素ID
    if (type === 'header') {
        formatBtn = document.getElementById('format-header');
        jsonTextarea = document.getElementById('api-headers');
    } else if (type === 'body') {
        formatBtn = document.getElementById('format-body');
        jsonTextarea = document.getElementById('api-body');
    } else if (type === 'modal-header') {
        formatBtn = document.getElementById('modal-format-header');
        jsonTextarea = document.getElementById('modal-api-headers');
    } else if (type === 'modal-body') {
        formatBtn = document.getElementById('modal-format-body');
        jsonTextarea = document.getElementById('modal-api-body');
    } else if (type.startsWith('wrapper-')) {
        formatBtn = document.getElementById(`format-${type}`);
        jsonTextarea = document.getElementById(`api-${type.replace('wrapper-', '')}s`);
    }
    
    if (!jsonTextarea) {
        console.warn(`API测试编辑器初始化失败: 缺少JSON文本框 (${type})`);
        return;
    }
    
    // 格式化JSON
    function formatJson(textarea) {
        try {
            const jsonObj = JSON.parse(textarea.value);
            textarea.value = JSON.stringify(jsonObj, null, 2);
            validateJson(textarea);
            Popup.success(`${type.includes('header') ? '请求头' : '请求体'}JSON格式化成功`);
        } catch (e) {
            Popup.error(`JSON格式错误: ${e.message}`);
        }
    }
    
    // 验证JSON
    function validateJson(textarea) {
        const validation = textarea.nextElementSibling;
        if (!validation) return false;
        
        try {
            JSON.parse(textarea.value);
            textarea.classList.remove('is-invalid');
            textarea.classList.add('is-valid');
            validation.textContent = '';
            return true;
        } catch (e) {
            textarea.classList.remove('is-valid');
            textarea.classList.add('is-invalid');
            validation.textContent = `JSON格式错误: ${e.message}`;
            return false;
        }
    }
    
    // 格式化按钮事件
    if (formatBtn) {
        formatBtn.addEventListener('click', function() {
            formatJson(jsonTextarea);
        });
    }
    
    // JSON文本框输入事件，实时验证
    jsonTextarea.addEventListener('input', function() {
        validateJson(this);
    });
    
    // 初始化验证
    validateJson(jsonTextarea);
}



// 初始化模态框中的API测试按钮功能
function initModalTestApiBtn() {
    // 获取DOM元素 - 使用模态框中的元素
    const apiTestBtn = document.getElementById('modal-test-api-btn');
    const apiMethod = document.getElementById('modal-api-wrapper-method');
    const apiUrl = document.getElementById('modal-api-wrapper-url');
    const apiHeaders = document.getElementById('modal-api-headers');
    const apiBody = document.getElementById('modal-api-body');
    const apiResponse = document.getElementById('modal-api-response');
    const systemPromptInput = document.getElementById('modal-api-wrapper-system-prompt');
    
    // 检查关键元素是否存在
    if (!apiTestBtn || !apiMethod || !apiUrl || !apiHeaders || !apiBody || !apiResponse) {
        console.warn('模态框API测试按钮初始化失败: 缺少关键DOM元素');
        return;
    }
    
    // API测试按钮点击事件
    apiTestBtn.addEventListener('click', function() {
        const method = apiMethod.value;
        const url = apiUrl.value;
        const headersStr = apiHeaders.value;
        const bodyStr = apiBody.value;
        const systemPrompt = systemPromptInput ? systemPromptInput.value : '';
        
        // 验证URL
        if (!url) {
            Popup.error('请输入API URL');
            return;
        }
        
        // 解析请求头
        let headersObj = {};
        if (headersStr) {
            try {
                headersObj = JSON.parse(headersStr);
            } catch (e) {
                Popup.error(`请求头格式错误: ${e.message}`);
                return;
            }
        }
        
        // 解析请求体
        let bodyObj = null;
        if (bodyStr && bodyStr.trim() !== '{}') {
            try {
                bodyObj = JSON.parse(bodyStr);
            } catch (e) {
                Popup.error(`请求体格式错误: ${e.message}`);
                return;
            }
        }
        
        // 显示加载状态
        apiResponse.textContent = '正在发送请求...';
        
        // 发送请求
        fetch('/api_wrapper/api_test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                method: method,
                url: url,
                headers: headersObj,
                body: bodyObj,
                system_prompt: systemPrompt,
                context: {
                    prompt: [{"role": "user", "content": "你是谁"}]
                }
            })
        })
        .then(response => {
            // 直接处理所有响应，不区分状态码
            return response.text().then(text => {
                try {
                    return JSON.parse(text);
                } catch {
                    return { success: false, message: text };
                }
            });
        })
        .then(result => {
            // 根据success字段决定显示内容
            if (result.success) {
                // 请求成功，只显示原始数据
                apiResponse.textContent = JSON.stringify(result.data, null, 2);
            } else {
                // 请求失败，只显示失败原因
                apiResponse.textContent = result.message;
            }
        })
        .catch(error => {
            // 网络或其他错误处理
            apiResponse.textContent = error.message;
        });
    });
}



// 初始化API封装管理功能
function initApiWrapperManagement() {
    // 检查页面是否包含API封装管理相关元素
    if (!document.getElementById('api-wrapper-container')) {
        // 不是高级功能页面，不初始化API封装管理
        return;
    }
    
    // 加载API封装列表
    loadApiWrappers();
    
    // 初始化添加API按钮
    initAddApiBtn();
    
    // 初始化模态框中的API功能
    initModalApiFeatures();
    
    // 绑定模态框关闭事件
    bindModalCloseEvents();
    
    // 全局处理激活错误的函数
    window.handleActivationError = function(message) {
        Popup.alert(message, { type: Popup.Type.WARNING });
    };
}

// 加载API封装列表
function loadApiWrappers() {
    fetch('/api_wrapper/api_wrappers')
        .then(response => {
            // 无论状态码如何，都尝试解析响应体
            return response.text().then(text => {
                try {
                    return JSON.parse(text);
                } catch {
                    return { success: false, message: text };
                }
            });
        })
        .then(data => {
            if (data.success) {
                renderApiWrappers(data.data);
            } else {
                // 检查是否是激活错误
                if (data.message && (data.message.includes('应用未激活') || data.message.includes('普通注册用户'))) {
                    window.handleActivationError(data.message);
                } else {
                    Popup.error(data.message || '加载API封装列表失败');
                }
            }
        })
        .catch(error => {
            console.error('加载API封装列表错误:', error);
            Popup.error('加载API封装列表失败');
        });
}

// 渲染API封装列表
function renderApiWrappers(apiWrappers) {
    const container = document.getElementById('api-wrapper-container');
    const emptyState = document.getElementById('api-wrapper-empty');
    
    if (!container || !emptyState) {
        console.warn('渲染API封装列表失败: 缺少关键DOM元素');
        return;
    }
    
    // 清空容器
    container.innerHTML = '';
    
    if (apiWrappers && apiWrappers.length > 0) {
        // 显示列表，隐藏空状态
        container.style.display = '';
        emptyState.style.display = 'none';
        
        // 渲染每个API封装条目
        apiWrappers.forEach(apiWrapper => {
            const wrapperItem = document.createElement('div');
            wrapperItem.className = 'form-row template-item';
            
            // API名称
            const nameDiv = document.createElement('div');
            nameDiv.className = 'template-name';
            nameDiv.textContent = apiWrapper.name;
            wrapperItem.appendChild(nameDiv);
            
            // API信息
            const infoDiv = document.createElement('div');
            infoDiv.className = 'template-info';
            
            // 模板类型
            const apiTypeDiv = document.createElement('div');
            apiTypeDiv.className = 'bili-account-stat template-type-stat';
            // 将英文模板类型转换为中文显示
            const apiTypeMap = {
                'custom': '自定义API',
                'openai': 'OpenAI',
                'kimi': 'Kimi',
                'anthropic': 'Anthropic',
                'silicon_flow': '硅基流动'
            };
            const displayApiType = apiTypeMap[apiWrapper.api_type] || apiWrapper.api_type;
            apiTypeDiv.innerHTML = `<span class="stat-label">模板类型:</span> <span class="stat-value">${displayApiType}</span>`;
            infoDiv.appendChild(apiTypeDiv);
            
            // 创建时间（只显示年月日）
            const createdAt = new Date(apiWrapper.created_at).toLocaleDateString('zh-CN');
            const createTimeDiv = document.createElement('div');
            createTimeDiv.className = 'bili-account-stat';
            createTimeDiv.innerHTML = `<span class="stat-label">创建时间:</span> <span class="stat-value">${createdAt}</span>`;
            infoDiv.appendChild(createTimeDiv);
            
            wrapperItem.appendChild(infoDiv);
            
            // 操作按钮
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'bili-account-actions';
            
            // 修改按钮
            const editBtn = document.createElement('button');
            editBtn.className = 'btn btn-sm btn-primary';
            editBtn.textContent = '修改';
            editBtn.addEventListener('click', () => editApiWrapper(apiWrapper.id));
            actionsDiv.appendChild(editBtn);
            
            // 删除按钮
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-sm btn-danger';
            deleteBtn.textContent = '删除';
            deleteBtn.addEventListener('click', () => deleteApiWrapper(apiWrapper.id));
            actionsDiv.appendChild(deleteBtn);
            
            wrapperItem.appendChild(actionsDiv);
            
            container.appendChild(wrapperItem);
        });
    } else {
        // 隐藏列表，显示空状态
        container.style.display = 'none';
        emptyState.style.display = '';
    }
}



// 删除API封装
async function deleteApiWrapper(id) {
    if (await Popup.confirm('确定要删除这个API封装吗？')) {
        fetch(`/api_wrapper/api_wrappers/${id}`, {
            method: 'DELETE'
        })
            .then(response => {
                // 无论状态码如何，都尝试解析响应体
                return response.text().then(text => {
                    try {
                        return JSON.parse(text);
                    } catch {
                        return { success: false, message: text };
                    }
                });
            })
            .then(data => {
                if (data.success) {
                    // 重新加载API封装列表
                    loadApiWrappers();
                    // 显示成功消息
                    Popup.success('删除API封装成功');
                } else {
                    // 检查是否是激活错误
                    if (data.message && data.message.includes('应用未激活')) {
                        window.handleActivationError(data.message);
                    } else {
                        Popup.error(data.message || '删除API封装失败');
                    }
                }
            })
            .catch(error => {
                console.error('删除API封装错误:', error);
                Popup.error('删除API封装失败');
            });
    }
}

// 编辑API封装
function editApiWrapper(id) {
    // 先检查激活状态
    fetch('/api/check_activation_status')
        .then(response => response.json())
        .then(data => {
            if (!data.success || !data.data.is_activated) {
                // 未激活，显示提示
                Popup.alert('应用未激活，无法使用API相关功能，请先激活应用', { type: Popup.Type.WARNING });
                return;
            }
            
            // 已激活，继续获取API封装详情
            fetch(`/api_wrapper/api_wrappers/${id}`)
                .then(response => {
                    // 无论状态码如何，都尝试解析响应体
                    return response.text().then(text => {
                        try {
                            return JSON.parse(text);
                        } catch {
                            return { success: false, message: text };
                        }
                    });
                })
                .then(data => {
                    if (data.success) {
                        const apiWrapper = data.data;
                        
                        // 重置测试结果区域
                        const apiResponse = document.getElementById('modal-api-response');
                        if (apiResponse) {
                            apiResponse.textContent = '';
                        }
                        
                        // 填充模态框表单
                        document.getElementById('modal-api-wrapper-id').value = apiWrapper.id;
                        document.getElementById('modal-api-wrapper-name').value = apiWrapper.name;
                        document.getElementById('modal-api-wrapper-method').value = apiWrapper.method;
                        document.getElementById('modal-api-wrapper-url').value = apiWrapper.url;
                        document.getElementById('modal-api-headers').value = JSON.stringify(apiWrapper.headers, null, 2);
                        document.getElementById('modal-api-body').value = JSON.stringify(apiWrapper.body, null, 2);
                        document.getElementById('modal-api-wrapper-api-type').value = apiWrapper.api_type;
                        document.getElementById('modal-api-wrapper-limit-type').value = apiWrapper.limit_type;
                        document.getElementById('modal-api-wrapper-limit-value').value = apiWrapper.limit_value;
                        document.getElementById('modal-api-wrapper-limit-field').value = apiWrapper.limit_field;
                        
                        // 填充系统提示字段
                        const systemPromptInput = document.getElementById('modal-api-wrapper-system-prompt');
                        if (systemPromptInput) {
                            systemPromptInput.value = apiWrapper.system_prompt || '';
                        }
                        
                        // 更新模态框中限制值和限制替代值输入框的状态
                        const limitTypeSelect = document.getElementById('modal-api-wrapper-limit-type');
                        const limitValueInput = document.getElementById('modal-api-wrapper-limit-value');
                        const limitFieldInput = document.getElementById('modal-api-wrapper-limit-field');
                        
                        if (limitTypeSelect.value === 'unlimited') {
                            limitValueInput.disabled = true;
                            limitFieldInput.disabled = true;
                        } else {
                            limitValueInput.disabled = false;
                            limitFieldInput.disabled = false;
                        }
                        
                        // 调用toggleSystemPrompt()，确保相关字段显示/隐藏正确
                        toggleSystemPrompt();
                        
                        // 初始化API Key输入框
                        const apiKeyInput = document.getElementById('modal-api-wrapper-api-key');
                        if (apiKeyInput) {
                            // 从API封装数据中提取当前API Key（仅针对标准API类型）
                            let currentApiKey = '';
                            
                            // 只有标准API类型需要提取API Key
                            if (apiWrapper.api_type !== 'custom') {
                                try {
                                    // 从请求头中提取API Key
                                    for (const [key, value] of Object.entries(apiWrapper.headers)) {
                                        if (typeof value === 'string') {
                                            // 匹配Bearer token格式
                                            const bearerMatch = value.match(/^Bearer\s+(.+)$/);
                                            if (bearerMatch) {
                                                currentApiKey = bearerMatch[1];
                                                break;
                                            }
                                            // 匹配直接API Key格式（如x-api-key）
                                            if (value.length > 10) { // 简单判断，API Key通常较长
                                                currentApiKey = value;
                                                break;
                                            }
                                        }
                                    }
                                } catch (e) {
                                    // 解析失败，忽略
                                }
                            }
                            
                            // 设置API Key输入框的值
                            apiKeyInput.value = currentApiKey;
                        }
                        
                        // 设置最大对话数输入框的值
                        const maxConversationsInput = document.getElementById('modal-api-wrapper-max-conversations');
                        if (maxConversationsInput) {
                            maxConversationsInput.value = apiWrapper.max_conversations || 100;
                        }
                        
                        // 动态修改模态框标题
                        const modalTitle = document.querySelector('.modal-title');
                        if (modalTitle) {
                            modalTitle.textContent = '修改API封装';
                        }
                        
                        // 打开模态框
                        const modal = document.getElementById('add-api-modal');
                        modal.classList.add('show');
                        
                        // 添加背景遮罩
                        const backdrop = document.createElement('div');
                        backdrop.className = 'modal-backdrop fade show';
                        backdrop.id = 'add-api-modal-backdrop';
                        document.body.appendChild(backdrop);
                        
                        // 阻止背景滚动
                        document.body.style.overflow = 'hidden';
                        
                        // 初始化API Key输入监听器，确保使用当前表单模板
                        initApiKeyListener();
                        
                        // 初始化HTTP方法选择联动效果
                        initMethodChangeHandler();
                    } else {
                        // 检查是否是激活错误或普通注册用户错误
                        if (data.message && (data.message.includes('应用未激活') || data.message.includes('普通注册用户'))) {
                            window.handleActivationError(data.message);
                        } else {
                            Popup.error(data.message || '获取API封装详情失败');
                        }
                    }
                })
                .catch(error => {
                    console.error('编辑API封装错误:', error);
                    Popup.error('获取API封装详情失败');
                });
        })
        .catch(error => {
            console.error('检查激活状态失败:', error);
            Popup.error('检查激活状态失败');
        });
}

// 测试API封装
function testApiWrapper(id) {
    // 获取API封装详情
    fetch(`/api_wrapper/api_wrappers/${id}`)
        .then(response => {
            return response.text().then(text => {
                try {
                    return JSON.parse(text);
                } catch {
                    return { success: false, message: text };
                }
            });
        })
        .then(data => {
            if (data.success) {
                const apiWrapper = data.data;
                
                // 显示加载状态
                const apiResponse = document.getElementById('api-response');
                if (apiResponse) {
                    apiResponse.textContent = '正在发送请求...';
                }
                
                // 发送请求
                fetch('/api_wrapper/test', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        method: apiWrapper.method,
                        url: apiWrapper.url,
                        headers: apiWrapper.headers,
                        body: apiWrapper.body
                    })
                })
                .then(response => {
                    return response.text().then(text => {
                        try {
                            return JSON.parse(text);
                        } catch {
                            return { success: false, message: text };
                        }
                    });
                })
                .then(result => {
                    // 成功处理
                    if (apiResponse) {
                        if (result.success) {
                            // 请求成功，只显示原始数据
                            apiResponse.textContent = JSON.stringify(result.data, null, 2);
                            Popup.success('API测试成功');
                        } else {
                            // 请求失败，显示失败原因
                            apiResponse.textContent = result.message;
                            Popup.error('API测试失败');
                        }
                    }
                })
                .catch(error => {
                    // 网络或其他错误处理
                    if (apiResponse) {
                        apiResponse.textContent = error.message;
                    }
                    Popup.error('API测试失败');
                });
            } else {
                const apiResponse = document.getElementById('api-response');
                if (apiResponse) {
                    apiResponse.textContent = data.message;
                }
                Popup.error('获取API封装详情失败');
            }
        })
        .catch(error => {
            console.error('测试API封装错误:', error);
            const apiResponse = document.getElementById('api-response');
            if (apiResponse) {
                apiResponse.textContent = error.message;
            }
            Popup.error('获取API封装详情失败');
        });
}

// 复制API封装调用语法
function copyApiWrapperSyntax(name) {
    const syntax = `{{api:${name}:字段路径}}`;
    
    // 复制到剪贴板
    navigator.clipboard.writeText(syntax)
        .then(() => {
            Popup.success('调用语法已复制到剪贴板');
        })
        .catch(error => {
            console.error('复制调用语法错误:', error);
            Popup.error('复制调用语法失败');
        });
}



// 初始化添加API按钮
function initAddApiBtn() {
    const addApiBtn = document.getElementById('add-api-btn');
    if (!addApiBtn) {
        console.warn('初始化添加API按钮失败: 缺少DOM元素');
        return;
    }
    
    // 点击添加API按钮，显示模态框
    addApiBtn.addEventListener('click', function() {
        // 先检查激活状态
        fetch('/api/check_activation_status')
            .then(response => response.json())
            .then(data => {
                if (!data.success || !data.data.is_activated) {
                    // 未激活，显示提示
                    Popup.alert('应用未激活，无法使用API相关功能，请先激活应用', { type: Popup.Type.WARNING });
                    return;
                }
                
                // 已激活，继续显示模态框
                // 重置模态框表单
                resetModalForm();
                
                // 设置模态框标题为添加API封装
                const modalTitle = document.querySelector('.modal-title');
                if (modalTitle) {
                    modalTitle.textContent = '添加API封装';
                }
                
                // 显示模态框
                const modal = document.getElementById('add-api-modal');
                modal.classList.add('show');
                
                // 添加背景遮罩
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                backdrop.id = 'add-api-modal-backdrop';
                document.body.appendChild(backdrop);
                
                // 阻止背景滚动
                document.body.style.overflow = 'hidden';
                
                // 初始化API Key输入监听器，确保使用当前表单模板
                initApiKeyListener();
            })
            .catch(error => {
                console.error('检查激活状态失败:', error);
                Popup.error('检查激活状态失败');
            });
    });
}

// 绑定模态框关闭事件
function bindModalCloseEvents() {
    const modal = document.getElementById('add-api-modal');
    const closeBtn = modal.querySelector('.close');
    const cancelBtn = document.getElementById('modal-cancel-btn');
    
    // 点击关闭按钮
    closeBtn.addEventListener('click', closeModal);
    
    // 点击取消按钮
    cancelBtn.addEventListener('click', closeModal);
    
    // 点击模态框外部
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });
}

// 关闭模态框
function closeModal() {
    const modal = document.getElementById('add-api-modal');
    const backdrop = document.getElementById('add-api-modal-backdrop');
    
    // 隐藏模态框
    modal.classList.remove('show');
    
    // 移除背景遮罩
    if (backdrop) {
        backdrop.remove();
    }
    
    // 恢复背景滚动
    document.body.style.overflow = '';
}

// 重置模态框表单
function resetModalForm() {
    const form = document.getElementById('modal-api-wrapper-form');
    if (form) {
        form.reset();
        
        // 重置隐藏字段
        document.getElementById('modal-api-wrapper-id').value = '';
        
        // 重置API类型和相关字段
        const apiTypeSelect = document.getElementById('modal-api-wrapper-api-type');
        if (apiTypeSelect) {
            apiTypeSelect.value = 'custom';
            resetToCustomApi();
            // 切换预制角色和API Key输入框的显示/隐藏
            toggleSystemPrompt();
        }
        
        // 重置JSON编辑器
        document.getElementById('modal-api-headers').value = JSON.stringify({"Content-Type": "application/json"}, null, 2);
        document.getElementById('modal-api-body').value = JSON.stringify({"key": "value"}, null, 2);
        
        // 重置API Key输入框
        const apiKeyInput = document.getElementById('modal-api-wrapper-api-key');
        if (apiKeyInput) {
            apiKeyInput.value = '';
        }
        
        // 重置最大对话数输入框
        const maxConversationsInput = document.getElementById('modal-api-wrapper-max-conversations');
        if (maxConversationsInput) {
            maxConversationsInput.value = 100;
        }
        
        // 重置限制类型选择联动效果
        const limitTypeSelect = document.getElementById('modal-api-wrapper-limit-type');
        const limitValueInput = document.getElementById('modal-api-wrapper-limit-value');
        const limitFieldInput = document.getElementById('modal-api-wrapper-limit-field');
        
        if (limitTypeSelect) {
            limitTypeSelect.value = 'unlimited';
            limitValueInput.disabled = true;
            limitFieldInput.disabled = true;
            limitValueInput.value = '';
            limitFieldInput.value = '';
        }
        
        // 重置测试结果区域
        const apiResponse = document.getElementById('modal-api-response');
        if (apiResponse) {
            apiResponse.textContent = '';
        }
        
        // 初始化HTTP方法选择联动效果
        initMethodChangeHandler();
    }
}

// 初始化模态框中的API功能
function initModalApiFeatures() {
    // 初始化模态框中的JSON编辑器
    initKeyValueEditor('modal-header');
    initKeyValueEditor('modal-body');
    
    // 初始化模态框中的保存API封装按钮
    initModalSaveApiWrapper();
    
    // 初始化模态框中的API限制类型选择联动效果
    initModalApiLimitType();
    
    // 初始化模态框中的API类型切换功能
    initApiTypeSwitch();
    
    // 初始化模态框中的测试API按钮
    initModalTestApiBtn();
    
    // 初始化预制角色显示/隐藏
    toggleSystemPrompt();
    
    // 初始化HTTP方法选择联动效果
    initMethodChangeHandler();
}

// 初始化HTTP方法选择联动效果
function initMethodChangeHandler() {
    const methodSelect = document.getElementById('modal-api-wrapper-method');
    if (!methodSelect) {
        console.warn('初始化HTTP方法选择联动效果失败: 缺少DOM元素');
        return;
    }
    
    // 初始状态处理
    updateRequestBodySection(methodSelect.value);
    
    // 方法选择变化时的处理
    methodSelect.addEventListener('change', function() {
        updateRequestBodySection(this.value);
    });
}

// 根据HTTP方法更新请求体部分
function updateRequestBodySection(method) {    
    // 获取请求体部分 - 使用更精确的选择器
    const bodySection = document.querySelector('.api-test-section');
    if (!bodySection) {
        console.error('未找到请求体部分');
        return;
    }
    
    // 找到第二个api-test-section，即请求体部分
    const sections = document.querySelectorAll('.api-test-section');
    if (sections.length < 2) {
        console.error('请求体部分数量不足');
        return;
    }
    
    const requestBodySection = sections[1];
    const bodyTitle = requestBodySection.querySelector('.setting-label');
    
    if (method === 'GET') {
        // GET请求：修改标题为"参数"
        if (bodyTitle) {
            bodyTitle.textContent = '参数';        }
        // 显示请求体部分
        requestBodySection.style.display = 'block';
    } else if (method === 'DELETE') {
        // DELETE请求：隐藏整个请求体部分
        requestBodySection.style.display = 'none';
    } else {
        // 其他请求：恢复标题为"请求体"
        if (bodyTitle) {
            bodyTitle.textContent = '请求体';
        }
        // 显示请求体部分
        requestBodySection.style.display = 'block';
    }
}

// 初始化模态框中的保存API封装按钮
function initModalSaveApiWrapper() {
    const saveBtn = document.getElementById('modal-save-api-wrapper');
    if (!saveBtn) {
        console.warn('初始化模态框保存API封装按钮失败: 缺少DOM元素');
        return;
    }
    
    saveBtn.addEventListener('click', function() {
        saveModalApiWrapper();
    });
}

// 保存模态框中的API封装
function saveModalApiWrapper() {
    // 获取表单数据
    const id = document.getElementById('modal-api-wrapper-id').value;
    const name = document.getElementById('modal-api-wrapper-name').value;
    const method = document.getElementById('modal-api-wrapper-method').value;
    const url = document.getElementById('modal-api-wrapper-url').value;
    const apiType = document.getElementById('modal-api-wrapper-api-type').value;
    const headersStr = document.getElementById('modal-api-headers').value;
    const bodyStr = document.getElementById('modal-api-body').value;
    const systemPrompt = document.getElementById('modal-api-wrapper-system-prompt')?.value || '';
    const limitType = document.getElementById('modal-api-wrapper-limit-type').value;
    const limitValue = document.getElementById('modal-api-wrapper-limit-value').value;
    const limitField = document.getElementById('modal-api-wrapper-limit-field').value;
    const maxConversations = document.getElementById('modal-api-wrapper-max-conversations')?.value || 100;
    
    // 验证必填字段
    if (!name || !url) {
        Popup.error('名称和URL不能为空');
        return;
    }
    
    // 验证限制值
    if (limitType !== 'unlimited' && (!limitValue || isNaN(limitValue) || parseInt(limitValue) <= 0)) {
        Popup.error('限制值必须是大于0的整数');
        return;
    }
    
    // 解析请求头和请求体
    let headersObj = {};
    let bodyObj = {};
    
    try {
        headersObj = JSON.parse(headersStr);
    } catch (e) {
        Popup.error(`请求头格式错误: ${e.message}`);
        return;
    }
    
    try {
        bodyObj = JSON.parse(bodyStr);
    } catch (e) {
        Popup.error(`请求体格式错误: ${e.message}`);
        return;
    }
    
    // 构建请求数据
    const apiWrapperData = {
        name,
        method,
        url,
        api_type: apiType,
        headers: headersObj,
        body: bodyObj,
        system_prompt: systemPrompt,
        limit_type: limitType,
        limit_value: limitType === 'unlimited' ? 0 : parseInt(limitValue),
        limit_field: limitField,
        max_conversations: parseInt(maxConversations) || 100
    };
    
    // 构建请求配置
    const fetchConfig = {
        method: id ? 'PUT' : 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(apiWrapperData)
    };
    
    // 发送请求
    fetch(id ? `/api_wrapper/api_wrappers/${id}` : '/api_wrapper/api_wrappers', fetchConfig)
        .then(response => {
            // 无论状态码如何，都尝试解析响应体
            return response.text().then(text => {
                try {
                    return JSON.parse(text);
                } catch {
                    return { success: false, message: text };
                }
            });
        })
        .then(data => {
            if (data.success) {
                // 重新加载API封装列表
                loadApiWrappers();
                // 显示成功消息
                Popup.success(id ? '更新API封装成功' : '创建API封装成功');
                // 关闭模态框
                closeModal();
            } else {
                // 检查是否是激活错误或普通注册用户错误
                if (data.message && (data.message.includes('应用未激活') || data.message.includes('普通注册用户'))) {
                    window.handleActivationError(data.message);
                    // 关闭模态框
                    closeModal();
                } else {
                    Popup.error(data.message || (id ? '更新API封装失败' : '创建API封装失败'));
                }
            }
        })
        .catch(error => {
            console.error('保存API封装错误:', error);
            Popup.error(id ? '更新API封装失败' : '创建API封装失败');
        });
}

// 初始化模态框中的API限制类型选择联动效果
function initModalApiLimitType() {
    const limitTypeSelect = document.getElementById('modal-api-wrapper-limit-type');
    const limitValueInput = document.getElementById('modal-api-wrapper-limit-value');
    const limitFieldInput = document.getElementById('modal-api-wrapper-limit-field');
    
    if (!limitTypeSelect || !limitValueInput || !limitFieldInput) {
        console.warn('初始化模态框API限制类型选择联动效果失败: 缺少DOM元素');
        return;
    }
    
    // 初始状态设置
    if (limitTypeSelect.value === 'unlimited') {
        limitValueInput.disabled = true;
        limitFieldInput.disabled = true;
        limitValueInput.value = '';
        limitFieldInput.value = '';
    }
    
    // 限制类型选择变化时，控制限制值和限制替代值输入框的显示
    limitTypeSelect.addEventListener('change', function() {
        if (this.value === 'unlimited') {
            limitValueInput.disabled = true;
            limitFieldInput.disabled = true;
            limitValueInput.value = '';
            limitFieldInput.value = '';
        } else {
            limitValueInput.disabled = false;
            limitFieldInput.disabled = false;
        }
    });
}

// 标准API配置模板
const STANDARD_API_TEMPLATES = {
    openai: {
        method: 'POST',
        url: 'https://api.openai.com/v1/chat/completions',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {{api_key}}'
        },
        body: {
            model: 'gpt-3.5-turbo',
            messages: [{"role": "user", "content": "{{prompt}}"}],
            temperature: 0.7,
            max_tokens: 1000
        }
    },
    kimi: {
        method: 'POST',
        url: 'https://api.moonshot.cn/v1/chat/completions',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {{api_key}}'
        },
        body: {
            model: 'moonshot-v1-8k',
            messages: [{"role": "user", "content": "{{prompt}}"}],
            temperature: 0.7,
            max_tokens: 1000
        }
    },
    anthropic: {
        method: 'POST',
        url: 'https://api.anthropic.com/v1/messages',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': '{{api_key}}',
            'anthropic-version': '2023-06-01'
        },
        body: {
            model: 'claude-3-sonnet-20240229',
            messages: [{"role": "user", "content": "{{prompt}}"}],
            max_tokens: 1000
        }
    },
    silicon_flow: {
        method: 'POST',
        url: 'https://api.siliconflow.cn/v1/chat/completions',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {{api_key}}'
        },
        body: {
            model: 'deepseek-ai/DeepSeek-V3.2',
            messages: [{"role": "user", "content": "{{prompt}}"}],
            temperature: 0.7,
            max_tokens: 1000
        }
    }
};

// 应用标准API模板到表单
function applyStandardApiTemplate(apiName) {
    const template = STANDARD_API_TEMPLATES[apiName];
    if (!template) return;
    
    // 填充表单字段
    document.getElementById('modal-api-wrapper-method').value = template.method;
    // 更新请求体部分的标题
    updateRequestBodySection(template.method);
    document.getElementById('modal-api-wrapper-url').value = template.url;
    document.getElementById('modal-api-headers').value = JSON.stringify(template.headers, null, 2);
    document.getElementById('modal-api-body').value = JSON.stringify(template.body, null, 2);
    
    // 重置API Key输入框
    const apiKeyInput = document.getElementById('modal-api-wrapper-api-key');
    if (apiKeyInput) {
        apiKeyInput.value = '';
    }
    
    // 重新初始化API Key输入监听器，确保使用最新模板
    initApiKeyListener();
}

// 重置为自定义API默认配置
function resetToCustomApi() {
    document.getElementById('modal-api-wrapper-method').value = 'GET';
    // 更新请求体部分的标题
    updateRequestBodySection('GET');
    document.getElementById('modal-api-wrapper-url').value = '';
    // 使用JSON.stringify生成格式化的JSON字符串
    document.getElementById('modal-api-headers').value = JSON.stringify({"Content-Type": "application/json"}, null, 2);
    document.getElementById('modal-api-body').value = JSON.stringify({"key": "value"}, null, 2);
}

// 初始化API类型切换功能
function initApiTypeSwitch() {
    const apiTypeSelect = document.getElementById('modal-api-wrapper-api-type');
    
    if (!apiTypeSelect) {
        console.warn('初始化API类型切换功能失败: 缺少DOM元素');
        return;
    }
    
    // API类型切换事件
    apiTypeSelect.addEventListener('change', function() {
        // 清空API Key输入框
        const apiKeyInput = document.getElementById('modal-api-wrapper-api-key');
        if (apiKeyInput) {
            apiKeyInput.value = '';
        }
        
        if (this.value === 'custom') {
            // 重置为自定义API默认配置
            resetToCustomApi();
        } else {
            // 应用对应标准API模板
            applyStandardApiTemplate(this.value);
        }
        
        // 切换预制角色显示/隐藏
        toggleSystemPrompt();
    });
}

// 初始化API Key输入监听，动态更新请求头和URL
function initApiKeyListener() {
    const apiKeyInput = document.getElementById('modal-api-wrapper-api-key');
    const apiHeadersTextarea = document.getElementById('modal-api-headers');
    const apiUrlInput = document.getElementById('modal-api-wrapper-url');
    
    if (!apiKeyInput || !apiHeadersTextarea || !apiUrlInput) {
        return;
    }
    
    // 获取当前API类型
    const apiTypeSelect = document.getElementById('modal-api-wrapper-api-type');
    const apiType = apiTypeSelect ? apiTypeSelect.value : 'custom';
    
    // 关键：从STANDARD_API_TEMPLATES获取包含{{api_key}}占位符的原始模板
    let originalHeadersTemplate = apiHeadersTextarea.value;
    let originalUrlTemplate = apiUrlInput.value;
    
    // 只有标准API类型才有{{api_key}}占位符，自定义API没有占位符，不需要特殊处理
    if (apiType !== 'custom' && STANDARD_API_TEMPLATES[apiType]) {
        const template = STANDARD_API_TEMPLATES[apiType];
        originalHeadersTemplate = JSON.stringify(template.headers, null, 2);
        originalUrlTemplate = template.url;
    }
    
    // 移除之前的监听器
    apiKeyInput.oninput = null;
    
    // 添加新的输入事件监听器
    apiKeyInput.oninput = function() {
        // 获取当前API Key值
        const apiKey = this.value;
        
        // 关键：每次都基于原始模板替换，不是当前内容
        if (originalHeadersTemplate.includes('{{api_key}}')) {
            const updatedHeaders = originalHeadersTemplate.replace(/\{\{api_key\}\}/g, apiKey);
            apiHeadersTextarea.value = updatedHeaders;
        }
        
        if (originalUrlTemplate.includes('{{api_key}}')) {
            const updatedUrl = originalUrlTemplate.replace(/\{\{api_key\}\}/g, apiKey);
            apiUrlInput.value = updatedUrl;
        }
    };
    
    // 监听API类型切换事件
    if (apiTypeSelect) {
        // 移除旧的事件监听器
        apiTypeSelect.onchange = null;
        
        // 添加新的事件监听器
        apiTypeSelect.onchange = function() {
            // 清空API Key输入框
            apiKeyInput.value = '';
            
            // 延迟执行，确保模板已经应用
            setTimeout(() => {
                // 重新初始化监听器，使用新模板
                initApiKeyListener();
            }, 200); // 增加延迟时间，确保模板已经完全应用
        };
    }
}

// 切换预制角色和API Key输入框的显示/隐藏
function toggleSystemPrompt() {
    // 大模型类型列表
    const llmTypes = ['openai', 'kimi', 'anthropic', 'silicon_flow'];
    
    // 获取元素
    const apiTypeSelect = document.getElementById('modal-api-wrapper-api-type');
    const apiKeyContainer = document.getElementById('api-key-container');
    const systemPromptContainer = document.getElementById('system-prompt-container');
    
    // 确保元素存在
    if (!apiTypeSelect) {
        return;
    }
    
    // 根据API类型显示/隐藏相关输入框
    const selectedType = apiTypeSelect.value;
    const isLlmType = llmTypes.includes(selectedType);
    
    // 控制API Key输入框
    if (apiKeyContainer) {
        apiKeyContainer.style.display = isLlmType ? 'flex' : 'none';
    }
    
    // 控制预制角色输入框
    if (systemPromptContainer) {
        systemPromptContainer.style.display = isLlmType ? 'flex' : 'none';
    }
}

