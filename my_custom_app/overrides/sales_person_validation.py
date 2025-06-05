# In my_custom_app/my_custom_app/overrides/sales_person_validation.py
import frappe
from frappe import _

def check_visit_target_details(doc, method):
    # This function will be called by the before_save hook on Sales Person
    # Fieldname of the child table in Sales Person DocType (e.g., "visit_target_details")
    child_table_fieldname = "custom_number_visit_target" # <<< CHANGE THIS if your fieldname is different

    if not doc.get(child_table_fieldname):
        return # No rows to validate

    for row_index, row in enumerate(doc.get(child_table_fieldname)):
        customer = row.get("customer")
        territory = row.get("territory")

        if not customer and not territory:
            # Use enumerate index + 1 for user-friendly row number
            frappe.throw(
                _("Row #{}: Please specify either a Customer or a Territory in Visit Target Details. One of them is required.").format(row_index + 1),
                title=_("Missing Information in Visit Target Details")
            )
