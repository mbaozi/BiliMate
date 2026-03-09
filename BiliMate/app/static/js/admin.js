// 管理员页面通用功能

// 复制链接功能
function initCopyButtons() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const link = this.getAttribute('data-link');
            
            // 使用Clipboard API复制文本
            navigator.clipboard.writeText(link)
                .then(() => {
                    // 显示复制成功提示
                    const originalText = this.textContent;
                    this.textContent = '已复制';
                    this.classList.add('btn-success');
                    
                    setTimeout(() => {
                        this.textContent = originalText;
                        this.classList.remove('btn-success');
                    }, 2000);
                })
                .catch(err => {
                    console.error('复制失败:', err);
                });
        });
    });
}

// 注册设置功能
function initRegistrationSettings() {
    // 从DOM获取设置URL
    const settingsUrls = document.getElementById('settings-urls');
    const registrationSettingsUrl = settingsUrls ? settingsUrls.getAttribute('data-registration-url') : '';
    
    function toggleInvitationOption() {
        const allowRegistrationCheckbox = document.getElementById('allow_registration');
        const invitationGroup = document.getElementById('invitation-group');
        if (allowRegistrationCheckbox && invitationGroup) {
            const allowRegistration = allowRegistrationCheckbox.checked;
            invitationGroup.style.display = allowRegistration ? 'block' : 'none';
        }
    }
    
    function saveSetting(key, value) {
        if (!registrationSettingsUrl) {
            console.error('Registration settings URL not found');
            return;
        }
        
        fetch(registrationSettingsUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ [key]: value })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 可以添加成功提示
            }
        })
        .catch(error => {
            console.error('保存设置失败:', error);
        });
    }
    
    // 初始化
    toggleInvitationOption();
    
    // 监听允许注册选项变化
    const allowRegistrationCheckbox = document.getElementById('allow_registration');
    if (allowRegistrationCheckbox) {
        allowRegistrationCheckbox.addEventListener('change', function() {
            const value = this.checked;
            toggleInvitationOption();
            saveSetting('allow_registration', value);
        });
    }
    
    // 监听需要邀请码选项变化
    const requireInvitationCheckbox = document.getElementById('require_invitation');
    if (requireInvitationCheckbox) {
        requireInvitationCheckbox.addEventListener('change', function() {
            const value = this.checked;
            saveSetting('require_invitation', value);
        });
    }
}

// 初始化用户等级相关功能
function initUserLevelFeatures() {
    // 监听用户等级变化，显示/隐藏VIP有效期
    const userLevelSelect = document.getElementById('user_level');
    if (userLevelSelect) {
        userLevelSelect.addEventListener('change', function() {
            const userLevel = this.value;
            const vipExpiryContainer = document.getElementById('vip-expiry-container');
            if (vipExpiryContainer) {
                vipExpiryContainer.style.display = userLevel === 'vip' ? 'flex' : 'none';
            }
        });
        
        // 初始化VIP有效期显示状态
        userLevelSelect.dispatchEvent(new Event('change'));
    }
    
    // 监听创建用户表单的用户等级变化
    const createUserLevelSelect = document.getElementById('user_level');
    if (createUserLevelSelect) {
        function toggleExpiryDateField() {
            const userLevel = createUserLevelSelect.value;
            const expiryDateGroup = document.getElementById('expiry-date-group');
            if (expiryDateGroup) {
                if (userLevel === 'vip') {
                    expiryDateGroup.style.display = 'block';
                } else {
                    expiryDateGroup.style.display = 'none';
                    // 清除到期时间值
                    const expiryDateInput = document.getElementById('expiry_date');
                    if (expiryDateInput) {
                        expiryDateInput.value = '';
                    }
                }
            }
        }
        
        // 初始化到期时间显示状态
        toggleExpiryDateField();
        
        // 监听用户等级变化
        createUserLevelSelect.addEventListener('change', toggleExpiryDateField);
    }
    
    // 监听修改用户表单的用户等级变化
    const editUserLevelSelect = document.getElementById('edit-user-level');
    if (editUserLevelSelect) {
        function toggleEditExpiryDateField() {
            const userLevel = editUserLevelSelect.value;
            const expiryDateGroup = document.getElementById('edit-expiry-date-group');
            if (expiryDateGroup) {
                if (userLevel === 'vip') {
                    expiryDateGroup.style.display = 'block';
                } else {
                    expiryDateGroup.style.display = 'none';
                    // 清除到期时间值
                    const editExpiryDateInput = document.getElementById('edit-expiry-date');
                    if (editExpiryDateInput) {
                        editExpiryDateInput.value = '';
                    }
                }
            }
        }
        
        // 监听用户等级变化
        editUserLevelSelect.addEventListener('change', toggleEditExpiryDateField);
    }
}

// 初始化模态框功能
function initModals() {
    // 创建邀请码模态框
    const invitationModal = document.getElementById('create-invitation-modal');
    const createInvitationBtn = document.getElementById('create-invitation-btn');
    if (invitationModal && createInvitationBtn) {
        const invitationCloseBtn = invitationModal.querySelector('.close');
        const invitationCancelBtn = invitationModal.querySelector('.modal-footer [data-dismiss="modal"]');
        const invitationForm = document.getElementById('create-invitation-form');
        
        // 打开邀请码模态框
        createInvitationBtn.addEventListener('click', function() {
            invitationModal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // 添加背景遮罩
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = 'create-invitation-modal-backdrop';
            document.body.appendChild(backdrop);
        });
        
        // 关闭邀请码模态框
        function closeInvitationModal() {
            invitationModal.classList.remove('show');
            document.body.style.overflow = '';
            
            // 移除背景遮罩
            const backdrop = document.getElementById('create-invitation-modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }
        
        // 点击关闭按钮
        if (invitationCloseBtn) {
            invitationCloseBtn.addEventListener('click', closeInvitationModal);
        }
        
        // 点击取消按钮
        if (invitationCancelBtn) {
            invitationCancelBtn.addEventListener('click', closeInvitationModal);
        }
        
        // 点击模态框外部
        window.addEventListener('click', function(event) {
            if (event.target === invitationModal) {
                closeInvitationModal();
            }
        });
        
        // 处理邀请码表单提交
        if (invitationForm) {
            invitationForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const formDataObj = {};
                formData.forEach((value, key) => {
                    formDataObj[key] = value;
                });
                
                fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formDataObj)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 显示成功消息
                        Popup.success(data.message);
                        // 关闭模态框
                        closeInvitationModal();
                        // 刷新页面以显示新生成的邀请码
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        // 显示错误消息
                        Popup.error(data.message || '生成邀请码失败');
                    }
                })
                .catch(error => {
                    console.error('生成邀请码错误:', error);
                    Popup.error('生成邀请码失败');
                });
            });
        }
    }
    
    // 创建用户模态框
    const createUserModal = document.getElementById('create-user-modal');
    const createUserBtn = document.getElementById('create-user-btn');
    if (createUserModal && createUserBtn) {
        const closeBtn = createUserModal.querySelector('.close');
        const cancelBtn = createUserModal.querySelector('.modal-footer [data-dismiss="modal"]');
        const createUserForm = document.getElementById('create-user-form');
        
        // 打开模态框
        createUserBtn.addEventListener('click', function() {
            createUserModal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // 添加背景遮罩
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = 'create-user-modal-backdrop';
            document.body.appendChild(backdrop);
        });
        
        // 关闭模态框
        function closeModal() {
            createUserModal.classList.remove('show');
            document.body.style.overflow = '';
            
            // 移除背景遮罩
            const backdrop = document.getElementById('create-user-modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }
        
        // 点击关闭按钮
        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }
        
        // 点击取消按钮
        if (cancelBtn) {
            cancelBtn.addEventListener('click', closeModal);
        }
        
        // 点击模态框外部
        window.addEventListener('click', function(event) {
            if (event.target === createUserModal) {
                closeModal();
            }
        });
        
        // 处理创建用户表单提交
        if (createUserForm) {
            createUserForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const formDataObj = {};
                formData.forEach((value, key) => {
                    formDataObj[key] = value;
                });
                
                fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formDataObj)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 显示成功消息
                        Popup.success(data.message);
                        // 关闭模态框
                        closeModal();
                        // 刷新页面以显示新创建的用户
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        // 显示错误消息
                        Popup.error(data.message || '创建用户失败');
                    }
                })
                .catch(error => {
                    console.error('创建用户错误:', error);
                    Popup.error('创建用户失败');
                });
            });
        }
    }
    
    // 修改用户模态框
    const editModal = document.getElementById('edit-user-modal');
    const editUserBtns = document.querySelectorAll('.edit-user-btn');
    if (editModal && editUserBtns.length > 0) {
        const editCloseBtn = editModal.querySelector('.close');
        const editCancelBtn = editModal.querySelector('.modal-footer [data-dismiss="modal"]');
        const editUserIdInput = document.getElementById('edit-user-id');
        const editUsernameInput = document.getElementById('edit-username');
        const editUserForm = document.getElementById('edit-user-form');
        
        // 打开修改模态框
        editUserBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const userId = this.getAttribute('data-user-id');
                const username = this.getAttribute('data-username');
                const userLevel = this.getAttribute('data-user-level');
                const expiryDate = this.getAttribute('data-expiry-date');
                const userRole = this.getAttribute('data-user-role');
                
                if (editUserIdInput) editUserIdInput.value = userId;
                if (editUsernameInput) editUsernameInput.value = username;
                
                // 显示或隐藏用户等级和到期时间设置
                const userLevelGroup = document.querySelector('#edit-user-form .form-group:nth-of-type(4)');
                const expiryDateGroup = document.getElementById('edit-expiry-date-group');
                
                if (userRole === 'registered') {
                    if (userLevelGroup) userLevelGroup.style.display = 'block';
                    // 初始显示或隐藏到期时间设置
                    if (userLevel === 'vip') {
                        if (expiryDateGroup) expiryDateGroup.style.display = 'block';
                    } else {
                        if (expiryDateGroup) expiryDateGroup.style.display = 'none';
                        // 清除到期时间值
                        const editExpiryDateInput = document.getElementById('edit-expiry-date');
                        if (editExpiryDateInput) {
                            editExpiryDateInput.value = '';
                        }
                    }
                    // 设置用户等级和到期时间
                    const editUserLevelSelect = document.getElementById('edit-user-level');
                    if (editUserLevelSelect && userLevel) {
                        editUserLevelSelect.value = userLevel;
                    }
                    const editExpiryDateInput = document.getElementById('edit-expiry-date');
                    if (editExpiryDateInput && expiryDate && userLevel === 'vip') {
                        editExpiryDateInput.value = expiryDate;
                    }
                } else {
                    if (userLevelGroup) userLevelGroup.style.display = 'none';
                    if (expiryDateGroup) expiryDateGroup.style.display = 'none';
                }
                
                editModal.classList.add('show');
                document.body.style.overflow = 'hidden';
                
                // 添加背景遮罩
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                backdrop.id = 'edit-user-modal-backdrop';
                document.body.appendChild(backdrop);
            });
        });
        
        // 关闭修改模态框
        function closeEditModal() {
            editModal.classList.remove('show');
            document.body.style.overflow = '';
            
            // 移除背景遮罩
            const backdrop = document.getElementById('edit-user-modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }
        
        // 点击关闭按钮
        if (editCloseBtn) {
            editCloseBtn.addEventListener('click', closeEditModal);
        }
        
        // 点击取消按钮
        if (editCancelBtn) {
            editCancelBtn.addEventListener('click', closeEditModal);
        }
        
        // 点击模态框外部
        window.addEventListener('click', function(event) {
            if (event.target === editModal) {
                closeEditModal();
            }
        });
        
        // 处理用户编辑表单提交
        if (editUserForm) {
            editUserForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const formDataObj = {};
                formData.forEach((value, key) => {
                    formDataObj[key] = value;
                });
                
                fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formDataObj)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 显示成功消息
                        Popup.success(data.message);
                        // 关闭模态框
                        closeEditModal();
                        // 刷新页面以显示更新后的用户信息
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        // 显示错误消息
                        Popup.error(data.message || '更新用户失败');
                    }
                })
                .catch(error => {
                    console.error('更新用户错误:', error);
                    Popup.error('更新用户失败');
                });
            });
        }
    }
}

// 初始化删除按钮功能
function initDeleteButtons() {
    // 处理删除邀请码按钮
    document.querySelectorAll('.delete-code-btn').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const codeId = this.getAttribute('data-code-id');
            if (await Popup.confirm('确定要删除此邀请码吗？')) {
                fetch('/api/delete_invitation_code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ code_id: codeId })
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
                        // 从DOM中移除对应的行
                        this.closest('tr').remove();
                        // 显示成功消息
                        Popup.success('邀请码删除成功');
                    } else {
                        // 显示错误消息
                        Popup.error(data.message || '删除邀请码失败');
                    }
                })
                .catch(error => {
                    console.error('删除邀请码错误:', error);
                    Popup.error('删除邀请码失败');
                });
            }
        });
    });
    
    // 处理删除用户按钮
    document.querySelectorAll('.delete-user-btn').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const userId = this.getAttribute('data-user-id');
            if (await Popup.confirm('确定要删除此用户吗？')) {
                fetch('/api/delete_user', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_id: userId })
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
                        // 从DOM中移除对应的行
                        this.closest('tr').remove();
                        // 显示成功消息
                        Popup.success('用户删除成功');
                    } else {
                        // 显示错误消息
                        Popup.error(data.message || '删除用户失败');
                    }
                })
                .catch(error => {
                    console.error('删除用户错误:', error);
                    Popup.error('删除用户失败');
                });
            }
        });
    });
}

// 初始化所有功能
document.addEventListener('DOMContentLoaded', function() {
    initCopyButtons();
    initRegistrationSettings();
    initUserLevelFeatures();
    initModals();
    initDeleteButtons();
});