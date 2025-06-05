frappe.ui.form.on('Visit Target Detail', {
    // Trigger when the period_type field changes
    period_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let period_type = row.period_type;
        let start_date = null;
        let end_date = null;
        let today = frappe.datetime.now_date();
        let read_only = 0; // 0 = false, 1 = true
        // let mandatory = 0; // Client-side mandatory on child tables is less reliable

        if (period_type === 'Current Month') {
            start_date = frappe.datetime.start_of(today, "month");
            end_date = frappe.datetime.end_of(today, "month");
            read_only = 1;
        } else if (period_type === 'Current Quarter') {
            start_date = frappe.datetime.start_of(today, "quarter");
            end_date = frappe.datetime.end_of(today, "quarter");
            read_only = 1;
        } else if (period_type === 'Next 30 Days') {
            start_date = today;
            end_date = frappe.datetime.add_days(today, 30);
            read_only = 1;
        } else if (period_type === 'Custom Range') {
            start_date = row.start_date || null;
            end_date = row.end_date || null;
            read_only = 0;
            // mandatory = 1; // Rely on server-side validation if needed
        } else {
            start_date = null;
            end_date = null;
            read_only = 0;
        }

        // Set the values in the child table row
        frappe.model.set_value(cdt, cdn, 'start_date', start_date);
        frappe.model.set_value(cdt, cdn, 'end_date', end_date);

        // Refresh the row/table to show changes immediately
        // Use the CORRECT fieldname of the table in the PARENT doctype
        frm.refresh_field('custom_number_visit_target'); 

        // Set read-only status
        // Use the CORRECT fieldname of the table in the PARENT doctype
        if (frm.fields_dict['custom_number_visit_target'] && frm.fields_dict['custom_number_visit_target'].grid.grid_rows_by_docname[cdn]) {
             frm.fields_dict['custom_number_visit_target'].grid.grid_rows_by_docname[cdn].toggle_editable('start_date', !read_only);
             frm.fields_dict['custom_number_visit_target'].grid.grid_rows_by_docname[cdn].toggle_editable('end_date', !read_only);
        }
    },

    // Apply read-only on refresh for existing rows
    refresh: function(frm) {
        // Use the CORRECT fieldname of the table in the PARENT doctype
        let grid = frm.fields_dict['custom_number_visit_target'] ? frm.fields_dict['custom_number_visit_target'].grid : null;
        if (grid && frm.doc.custom_number_visit_target) {
            frm.doc.custom_number_visit_target.forEach(function(row) {
                let grid_row = grid.grid_rows_by_docname[row.name];
                if (grid_row) {
                    let read_only = (['Current Month', 'Current Quarter', 'Next 30 Days'].includes(row.period_type));
                    grid_row.toggle_editable('start_date', !read_only);
                    grid_row.toggle_editable('end_date', !read_only);
                }
            });
        }
    }
});
