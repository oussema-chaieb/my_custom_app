frappe.ui.form.on('Visit Target Detail', {
    // Trigger when the period_type field changes
    period_type: function(frm, cdt, cdn) {
        console.log("Period Type Changed for row:", cdn); // Log entry point

        let row = locals[cdt][cdn];
        let period_type = row.period_type;
        let start_date = null;
        let end_date = null;
        let today = frappe.datetime.now_date();
        let read_only = 0;
        let child_table_fieldname = "custom_number_visit_target"; // Confirm this is correct

        console.log("Selected Period Type:", period_type); // Log selected type

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
        } else {
            start_date = null;
            end_date = null;
            read_only = 0;
        }

        console.log("Calculated Start Date:", start_date); // Log calculated dates
        console.log("Calculated End Date:", end_date);

        // Set the values in the child table row
        frappe.model.set_value(cdt, cdn, 'start_date', start_date);
        frappe.model.set_value(cdt, cdn, 'end_date', end_date);

        console.log("Values set for row:", cdn);

        // Refresh the row/table to show changes immediately
        console.log("Refreshing table field:", child_table_fieldname);
        frm.refresh_field(child_table_fieldname);

        // Set read-only status
        console.log("Attempting to set read-only status...");
        try {
            if (frm.fields_dict[child_table_fieldname] && frm.fields_dict[child_table_fieldname].grid.grid_rows_by_docname[cdn]) {
                 frm.fields_dict[child_table_fieldname].grid.grid_rows_by_docname[cdn].toggle_editable('start_date', !read_only);
                 frm.fields_dict[child_table_fieldname].grid.grid_rows_by_docname[cdn].toggle_editable('end_date', !read_only);
                 console.log("Read-only status set for row:", cdn);
            } else {
                 console.log("Could not find grid row to set read-only status for row:", cdn);
            }
        } catch (e) {
            console.error("Error setting read-only status:", e); // Log errors
        }
    },

    // Apply read-only on refresh for existing rows
    refresh: function(frm) {
        console.log("Refresh trigger called for Sales Person form"); // Log refresh
        let child_table_fieldname = "custom_number_visit_target"; // Confirm this is correct
        let grid = frm.fields_dict[child_table_fieldname] ? frm.fields_dict[child_table_fieldname].grid : null;
        if (grid && frm.doc[child_table_fieldname]) {
            console.log("Processing existing rows on refresh...");
            frm.doc[child_table_fieldname].forEach(function(row) {
                let grid_row = grid.grid_rows_by_docname[row.name];
                if (grid_row) {
                    let read_only = (['Current Month', 'Current Quarter', 'Next 30 Days'].includes(row.period_type));
                    console.log("Setting read-only for existing row:", row.name, "Read Only:", read_only);
                    try {
                        grid_row.toggle_editable('start_date', !read_only);
                        grid_row.toggle_editable('end_date', !read_only);
                    } catch (e) {
                         console.error("Error setting read-only status on refresh for row:", row.name, e);
                    }
                } else {
                    console.log("Could not find grid row on refresh for row:", row.name);
                }
            });
        } else {
             console.log("No grid or no child table data found on refresh.");
        }
    }
});
