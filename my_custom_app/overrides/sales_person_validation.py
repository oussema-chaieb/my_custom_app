# In my_custom_app/my_custom_app/overrides/sales_person_validation.py
import frappe
from frappe import _
from frappe.utils import getdate

def check_visit_target_details(doc, method):
    # This function will be called by the before_save hook on Sales Person
    child_table_fieldname = "custom_number_visit_target" # Confirmed fieldname
    visit_targets = doc.get(child_table_fieldname)

    if not visit_targets:
        return # No rows to validate

    # --- Validation Loop --- 
    for i, row1 in enumerate(visit_targets):
        # --- Existing Validation: Customer/Territory --- 
        customer1 = row1.get("customer")
        territory1 = row1.get("territory")

        if not customer1 and not territory1:
            frappe.throw(
                _("Row #{}: Please specify either a Customer or a Territory in Visit Target Details. One of them is required.").format(i + 1),
                title=_("Missing Information in Visit Target Details")
            )

        # --- Existing Validation: Period Dates --- 
        period_type1 = row1.get("period_type")
        start_date1_str = row1.get("start_date")
        end_date1_str = row1.get("end_date")

        if period_type1 == "Custom Range":
            if not start_date1_str or not end_date1_str:
                frappe.throw(
                    _("Row #{}: Start Date and End Date are required when Period Type is 'Custom Range'.").format(i + 1),
                    title=_("Missing Date Information")
                )
            else:
                start_date1 = getdate(start_date1_str)
                end_date1 = getdate(end_date1_str)
                if end_date1 < start_date1:
                    frappe.throw(
                        _("Row #{}: End Date cannot be before Start Date.").format(i + 1),
                        title=_("Invalid Date Range")
                    )
        elif start_date1_str and end_date1_str: # Ensure dates exist for comparison even if not Custom
             start_date1 = getdate(start_date1_str)
             end_date1 = getdate(end_date1_str)
        else:
             # If dates are missing for non-custom types, skip overlap check for this row
             continue 

        # --- New Validation: Check for Overlaps with Other Rows --- 
        for j, row2 in enumerate(visit_targets):
            if i == j: # Don't compare a row with itself
                continue

            customer2 = row2.get("customer")
            start_date2_str = row2.get("start_date")
            end_date2_str = row2.get("end_date")

            # Only compare if customers match and are not empty, and both rows have valid dates
            if customer1 and customer1 == customer2 and start_date2_str and end_date2_str:
                start_date2 = getdate(start_date2_str)
                end_date2 = getdate(end_date2_str)

                # Check for overlap: (StartA <= EndB) and (EndA >= StartB)
                if (start_date1 <= end_date2) and (end_date1 >= start_date2):
                    frappe.throw(
                        _("Overlap detected between Row #{row1} and Row #{row2} for Customer {customer}. Please ensure date ranges do not overlap for the same customer.").format(
                            row1=i + 1,
                            row2=j + 1,
                            customer=customer1
                        ),
                        title=_("Overlapping Visit Target Dates")
                    )