# Copyright (c) 2025, DON and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class VisitTargetDetail(Document):
    def before_save(self):
        # Check if both customer and territory fields are empty or None
        customer = self.customer
        territory = self.territory

        if not customer and not territory:
            # If both are empty, raise a validation error
            frappe.throw(_("Please specify either a Customer or a Territory. One of them is required."))
