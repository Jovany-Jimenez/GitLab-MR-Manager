// Handle checkbox selection and select-all functionality
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.project-checkbox').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const projectId = parseInt(this.getAttribute('data-id'));
            const selected = this.checked;
            const projectItem = this.closest('.project-item');
            if (selected) {
                projectItem.classList.add('selected');
            } else {
                projectItem.classList.remove('selected');
            }
            fetch('/update_selection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: projectId, selected: selected })
            });
        });
    });
    
    const selectAll = document.getElementById('select-all');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            const checked = this.checked;
            document.querySelectorAll('.project-checkbox').forEach(function(checkbox) {
                checkbox.checked = checked;
                checkbox.dispatchEvent(new Event('change'));
            });
        });
    }
    
    // Handle View Changes button clicks - Fix navigation to project details
    document.querySelectorAll('.view-changes-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent any default behavior
            const projectId = this.getAttribute('data-id');
            console.log('View Changes clicked for project ID:', projectId);
            // Force a hard navigation to the project detail page
            window.location.href = `/project/${projectId}`;
        });
    });
    
    // Expand/collapse diff functionality
    document.querySelectorAll('.expand-diff-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const projectId = this.getAttribute('data-id');
            const diffContainer = document.getElementById(`diff-container-${projectId}`);
            
            if (diffContainer) {
                // Toggle the expanded class to control the height
                diffContainer.classList.toggle('expanded');
                // Update button text
                this.textContent = diffContainer.classList.contains('expanded') ? 'Collapse Diff' : 'Expand Diff';
            }
        });
    });
    
    // Handle "Expand All" button
    const expandAllBtn = document.getElementById('expand-all-btn');
    if (expandAllBtn) {
        expandAllBtn.addEventListener('click', function() {
            const diffContainers = document.querySelectorAll('.diff-container');
            const isExpanding = !diffContainers[0]?.classList.contains('expanded');
            
            diffContainers.forEach(container => {
                container.classList.toggle('expanded', isExpanding);
            });
            
            // Update all expand buttons text
            document.querySelectorAll('.expand-diff-btn').forEach(function(btn) {
                btn.textContent = isExpanding ? 'Collapse Diff' : 'Expand Diff';
            });
            
            // Update the expand all button text
            this.textContent = isExpanding ? 'Collapse All' : 'Expand All';
        });
    }
});

