document.addEventListener('DOMContentLoaded', function() {
    // 步骤切换逻辑
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    
    const step1NextBtn = document.getElementById('step1-next');
    const step2BackBtn = document.getElementById('step2-back');
    const step3BackBtn = document.getElementById('step3-back');
    
    // 隐藏所有步骤，只显示当前步骤
    function showStep(stepElement) {
        [step1, step2, step3].forEach(step => {
            step.classList.remove('active');
            step.style.display = 'none';
        });
        stepElement.classList.add('active');
        stepElement.style.display = 'block';
    }
    
    // 检查URL参数，判断是否需要直接显示步骤3
    function checkUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('step') && urlParams.get('step') === '3') {
            showStep(step3);
            return true;
        }
        return false;
    }
    
    // 初始显示步骤1，除非URL参数指定显示步骤3
    if (!checkUrlParams()) {
        showStep(step1);
    }
    
    // 步骤1：下一步按钮点击事件
    step1NextBtn.addEventListener('click', function() {
        const selectedMode = document.querySelector('input[name="app_mode"]:checked').value;
        if (selectedMode === 'personal') {
            // 个人版本：显示步骤2
            showStep(step2);
        } else {
            // 团队版本：显示步骤3
            showStep(step3);
        }
    });
    
    // 步骤2：返回按钮点击事件
    step2BackBtn.addEventListener('click', function() {
        showStep(step1);
    });
    
    // 步骤3：返回按钮点击事件
    step3BackBtn.addEventListener('click', function() {
        showStep(step1);
    });
});