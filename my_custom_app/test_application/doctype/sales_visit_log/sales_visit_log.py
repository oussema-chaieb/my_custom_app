# In my_custom_app/my_custom_app/doctype/sales_visit_log/sales_visit_log.py
import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class SalesVisitLog(Document):
    # This method will be called by the on_submit hook
    def on_submit(self):
        self.update_visit_target_count()

    def update_visit_target_count(self):
        # Get necessary data from the submitted visit log
        sales_person_name = self.get("sales_person")
        visit_date_str = self.get("visit_date")
        customer_name = self.get("customer")

        if not sales_person_name or not visit_date_str or not customer_name:
            frappe.log_error(
                f"Sales Visit Log {self.name} missing Sales Person, Visit Date, or Customer.", 
                "Visit Target Update Failed"
            )
            return

        visit_date = getdate(visit_date_str)

        try:
            # Load the parent Sales Person document
            sales_person_doc = frappe.get_doc("Sales Person", sales_person_name)
            child_table_fieldname = "custom_number_visit_target" # Your child table fieldname
            visit_targets = sales_person_doc.get(child_table_fieldname)
            target_row_found = False

            if not visit_targets:
                return # No targets to update

            # Iterate through the visit target rows
            for target_row in visit_targets:
                target_customer = target_row.get("customer")
                start_date_str = target_row.get("start_date")
                end_date_str = target_row.get("end_date")

                # Check if this row matches the customer and date range
                if (target_customer == customer_name and 
                    start_date_str and end_date_str):
                    
                    start_date = getdate(start_date_str)
                    end_date = getdate(end_date_str)

                    if start_date <= visit_date <= end_date:
                        # Found the matching target row, increment the count
                        current_count = target_row.get("completed_visits") or 0
                        target_row.completed_visits = current_count + 1
                        target_row_found = True
                        # Optional: Add a log message
                        frappe.log_info(
                            f"Incremented completed_visits for SP {sales_person_name}, Customer {customer_name}, Row {target_row.idx}",
                            "Visit Target Update"
                        )
                        break # Stop checking rows once a match is found and updated
            
            if target_row_found:
                # Save the parent Sales Person document to persist changes in the child table
                # Use flags to avoid triggering recursive saves if there are other hooks
                sales_person_doc.flags.ignore_validate = True # Skip our overlap validation on this save
                sales_person_doc.save(ignore_permissions=True) # Use ignore_permissions if needed
                frappe.db.commit() # Ensure change is committed
            else:
                 frappe.log_error(
                    f"No matching Visit Target found for Sales Visit Log {self.name} (SP: {sales_person_name}, Customer: {customer_name}, Date: {visit_date_str})",
                    "Visit Target Update Failed"
                 )

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Error updating visit target for {self.name}")

