frappe.ui.form.on("Visit Target Detail", {
    // Event triggered when "period_type" changes IN THIS ROW
    period_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let period_type = row.period_type;
        let start_date = null;
        let end_date = null;
        let today_moment = moment(); // Use moment.js
        let read_only = 0;
        // We need the parent's fieldname for the table to refresh it
        // Get it from the grid object if possible, otherwise hardcode (less ideal)
        let grid = frm.fields_dict[row.parentfield]?.grid; // Get grid object via parentfield
        let child_table_fieldname = row.parentfield || "custom_number_visit_target"; // Default if needed

        if (period_type === "Current Month") {
            start_date = today_moment.startOf("month").format("YYYY-MM-DD");
            end_date = today_moment.endOf("month").format("YYYY-MM-DD");
            read_only = 1;
        } else if (period_type === "Current Quarter") {
            start_date = today_moment.startOf("quarter").format("YYYY-MM-DD");
            end_date = today_moment.endOf("quarter").format("YYYY-MM-DD");
            read_only = 1;
        } else if (period_type === "Next 30 Days") {
            start_date = today_moment.format("YYYY-MM-DD"); // Today
            end_date = today_moment.add(30, "days").format("YYYY-MM-DD");
            read_only = 1;
        } else if (period_type === "Custom Range") {
            start_date = row.start_date || null;
            end_date = row.end_date || null;
            read_only = 0;
        } else {
            start_date = null;
            end_date = null;
            read_only = 0;
        }

        // Set the values in the child table row
        // Use flags to prevent immediate refresh triggering infinite loops
        frm.setting_child_value = true;
        frappe.model.set_value(cdt, cdn, "start_date", start_date);
        frappe.model.set_value(cdt, cdn, "end_date", end_date);
        frm.setting_child_value = false;

        // Refresh the specific row fields
        let grid_row = grid?.grid_rows_by_docname[cdn];
        if (grid_row) {
             grid_row.refresh_field("start_date");
             grid_row.refresh_field("end_date");
        } else {
            // Fallback: Refresh the whole table on the parent form
            frm.refresh_field(child_table_fieldname);
        }

        // Set read-only status
        if (grid_row) {
            try {
                 grid_row.toggle_editable("start_date", !read_only);
                 grid_row.toggle_editable("end_date", !read_only);
            } catch (e) {
                console.error("Error setting read-only status:", e);
            }
        } else {
             console.log("Could not find grid row to set read-only status for row:", cdn);
        }
    },
});