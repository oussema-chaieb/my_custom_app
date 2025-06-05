# In my_custom_app/my_custom_app/overrides/sales_person_validation.py
import frappe
from frappe import _
from frappe.utils import getdate # Import getdate for comparison

def check_visit_target_details(doc, method):
    # This function will be called by the before_save hook on Sales Person
    child_table_fieldname = "custom_number_visit_target" # Confirmed fieldname

    if not doc.get(child_table_fieldname):
        return # No rows to validate

    for row_index, row in enumerate(doc.get(child_table_fieldname)):
        # --- Existing Validation --- 
        customer = row.get("customer")
        territory = row.get("territory")

        if not customer and not territory:
            frappe.throw(
                _("Row #{}: Please specify either a Customer or a Territory in Visit Target Details. One of them is required.").format(row_index + 1),
                title=_("Missing Information in Visit Target Details")
            )

        # --- New Validation for Period --- 
        period_type = row.get("period_type")
        start_date = row.get("start_date")
        end_date = row.get("end_date")

        if period_type == "Custom Range":
            # Check if dates are missing
            if not start_date or not end_date:
                frappe.throw(
                    _("Row #{}: Start Date and End Date are required when Period Type is 'Custom Range'.").format(row_index + 1),
                    title=_("Missing Date Information")
                )
            # Optional but recommended: Check if end_date is before start_date
            elif getdate(end_date) < getdate(start_date):
                 frappe.throw(
                    _("Row #{}: End Date cannot be before Start Date.").format(row_index + 1),
                    title=_("Invalid Date Range")
                )

