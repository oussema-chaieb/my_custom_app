"""Installation helpers for my_custom_app.

This module currently contains only a stub implementation of `after_install` so
that older hook references remain valid. Real post-install logic should be
added here if required.
"""
import frappe

def after_install():
    """Run once after the app is installed on a new site.

    Currently this is a no-op placeholder to maintain backward compatibility.
    """
    frappe.logger().info("my_custom_app.install.after_install – no-op") 