import frappe

def execute():
    if frappe.db.exists("Workspace", "ERPNext Integrations"):
        frappe.delete_doc("Workspace", "ERPNext Integrations", ignore_permissions=True, force=True)
        frappe.db.commit() # Ensure the change is saved
        print("Deleted standard Workspace: ERPNext Integrations")