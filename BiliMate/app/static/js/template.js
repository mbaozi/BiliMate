/* 模板管理相关JavaScript功能 */

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 监听创建方式变化
    const createMethodRadio = document.querySelectorAll('input[name="createMethod"]');
    const existingTemplateGroup = document.getElementById('existingTemplateGroup');
    
    if (createMethodRadio && existingTemplateGroup) {
        createMethodRadio.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'existing') {
                    existingTemplateGroup.style.display = 'block';
                } else {
                    existingTemplateGroup.style.display = 'none';
                }
            });
        });
    }
    
    // 为创建模板按钮添加事件监听器
    const createTemplateBtn = document.getElementById('createTemplateBtn');
    if (createTemplateBtn) {
        createTemplateBtn.addEventListener('click', submitCreateTemplate);
    }
    
    // 为所有删除按钮添加事件监听器
    const deleteButtons = document.querySelectorAll('.btn-danger[data-template-id]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const templateId = this.dataset.templateId;
            const templateName = this.dataset.templateName;
            deleteTemplate(templateId, templateName);
        });
    });
});

// 提交创建模板
function submitCreateTemplate() {
    const templateName = document.getElementById('templateName').value.trim();
    const existingTemplateId = document.getElementById('existingTemplate').value;
    
    if (!templateName) {
        Popup.error('请输入模板名称');
        return;
    }
    
    // 验证模板名称不能为"默认模板"
    if (templateName === '默认模板') {
        Popup.error('模板名称不能为"默认模板"');
        return;
    }
    
    // 发送创建模板请求
    let data = {
        template_name: templateName
    };
    
    // 如果不是选择默认模板，则添加模板ID
    if (existingTemplateId !== 'default') {
        data.template_id = existingTemplateId;
    }
    
    fetch('/api/create_template', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 成功后直接刷新页面，通过flash消息显示成功提示
            window.location.reload();
        } else {
            Popup.error('模板创建失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('创建模板失败:', error);
        Popup.error('创建模板失败，请重试');
    });
}

// 删除模板
async function deleteTemplate(templateId, templateName) {
    if (await Popup.confirm(`确定要删除模板 "${templateName}" 吗？`)) {
        fetch('/api/delete_template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                template_id: templateId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 成功后直接刷新页面，通过flash消息显示成功提示
                window.location.reload();
            } else {
                Popup.error('模板删除失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('删除模板失败:', error);
            Popup.error('删除模板失败，请重试');
        });
    }
}