// QMS 通用交互逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 删除确认
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm || '确认执行此操作？')) {
                e.preventDefault();
            }
        });
    });
});