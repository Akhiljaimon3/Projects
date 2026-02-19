$(document).ready(function () {
    const notyf = new Notyf({
        duration: 2000,
        position: { x: 'right', y: 'bottom' },
        ripple: true
    });

    const messages = window.djangoMessages || [];
    messages.forEach(msg => {
        if (msg.tags === 'error') {
            notyf.error(msg.text);
        } else {
            notyf.success(msg.text);
        }
    });

    const heading = $('.form-heading'); // select the heading
    const topActions = $('#top-actions'); // select the top "All Volunteers" button container

    $('input[name="role"]').on('change', function () {
        const selectedRole = $(this).val();
        const container = $('#extra-dropdown-container');
        container.empty();

        // Show top button only for Registration Desk
        // if (selectedRole === 'registration') {
        //     topActions.show();
        // } else {
        //     topActions.hide();
        // }

        // Update heading based on selected role
        if (selectedRole === 'registration') {
            heading.text('Registration Desk Volunteers');
        } else if (selectedRole === 'ashaworker') {
            heading.text('ASHA Workers');
        } else if (selectedRole === 'followup') {
            heading.text('Follow Up Volunteers');
        } else {
            heading.text('Users');
        }

        // Generate conditional dropdowns
        if (selectedRole === 'ashaworker') {
            let wardOptions = '<option value="">-- Select Ward --</option>';
            for (let i = 1; i <= 44; i++) {
                wardOptions += `<option value="${i}">Ward ${i}</option>`;
            }

            container.html(`
                <div class="form-group">
                    <label for="ward">Ward</label>
                    <select id="ward" name="ward" required>
                        ${wardOptions}
                    </select>
                </div>
            `);

        } else if (selectedRole === 'registration') {
            const deptOptions = window.departmentOptions || [];
            let deptHtml = '<option value="" selected disabled>-- Select Department --</option>';
            deptOptions.forEach(d => {
                deptHtml += `<option value="${d.id}">${d.name}</option>`;
            });

            const deskHtml = `
                <option value="" selected disabled>-- Select Desk --</option>
                <option value="Registration">Registration</option>
                <option value="Consultation Confirmation">Consultation Confirmation</option>
                <option value="Medicine Confirmation">Medicine Confirmation</option>
            `;

            container.html(`
                <div class="form-group">
                    <label for="department">Department</label>
                    <select id="department" name="department" required>
                        ${deptHtml}
                    </select>
                </div>
                <div class="form-group mt-2">
                    <label for="desk">Desk</label>
                    <select id="desk" name="desk" required>
                        ${deskHtml}
                    </select>
                </div>
            `);

        } else if (selectedRole === 'followup') {
            const deptOptions = window.departmentOptions || [];
            let deptHtml = '<option value="">-- Select Department --</option>';
            deptOptions.forEach(d => {
                deptHtml += `<option value="${d.id}">${d.name}</option>`;
            });

            container.html(`
                <div class="form-group">
                    <label for="department">Department</label>
                    <select id="department" name="department" required>
                        ${deptHtml}
                    </select>
                </div>
            `);
        }
    });

    $('#toggle-upload').on('click', function (e) {
        e.preventDefault();
        $('#upload-box').slideToggle(200);
    });
});
