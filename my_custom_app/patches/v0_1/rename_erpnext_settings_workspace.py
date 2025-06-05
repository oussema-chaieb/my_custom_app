# In my_custom_app/patches/v0_1/rename_erpnext_settings_workspace.py
import frappe

def execute():
    old_name = "ERPNext Settings"
    new_name = "Settings"

    # Check if the old workspace exists and the new one doesn't already exist
    if frappe.db.exists("Workspace", old_name) and not frappe.db.exists("Workspace", new_name):
        try:
            # Rename the document
            frappe.rename_doc("Workspace", old_name, new_name, ignore_permissions=True)
            frappe.db.commit() # Ensure the change is saved
            print(f"Renamed standard Workspace: '{old_name}' to '{new_name}'")
        except Exception as e:
            print(f"Error renaming workspace '{old_name}' to '{new_name}': {e}")
            # Optional: add more robust error handling if needed
    elif frappe.db.exists("Workspace", new_name):
        print(f"Workspace '{new_name}' already exists or was already renamed. Skipping rename.")
    else:
        print(f"Workspace '{old_name}' not found. Skipping rename.")