"""
Page Object Model (POM) for Enterprise and Swag Labs Login Pages.
Encapsulates selectors and page properties to maintain clean test specifications dynamically.
"""
from core.config import Config


class LoginPage:
    """
    Selectors and endpoints for the Net Banking and Swag Labs login portals.
    """

    # Target login endpoint loaded from centralized Config!
    URL = Config.UI_BASE_URL

    @classmethod
    def get_locator(cls, page, element_name: str):
        """
        Returns the exact, precise native Playwright Locator for the element.
        Dynamically detects if we are automating Swag Labs or Enterprise Portals!
        """
        norm_name = str(element_name).lower().strip().replace(" ", "_").replace("-", "_")
        
        # Detect active browser URL
        current_url = page.url if page else ""
        is_swag_labs = "saucedemo" in current_url
        
        if is_swag_labs:
            # Swag Labs (saucedemo.com) Specific Locators
            if norm_name in ["username", "user_name"]:
                return page.locator("input#user-name, [data-test='username']")
            if norm_name == "password":
                return page.locator("input#password, [data-test='password']")
            if norm_name in ["login_button", "loginbutton"]:
                return page.locator("input#login-button, [data-test='login-button']")
            if norm_name in ["cart_badge", "cartbadge", "cart_item_count"]:
                return page.locator(".shopping_cart_badge, span.shopping_cart_badge")
            
            try:
                from .swag_labs_inventory_page import SwagLabsInventoryPage
                if norm_name in SwagLabsInventoryPage.SELECTORS:
                    return page.locator(SwagLabsInventoryPage.SELECTORS[norm_name])
            except ImportError:
                pass
                
        # Default fallback: Enterprise Portal Locators
        if norm_name == "username":
            # page.getByRole('textbox', { name: 'User ID' })
            return page.get_by_role("textbox", name="User ID")
            
        if norm_name == "password":
            # page.getByLabel('Password')
            return page.get_by_label("Password")
            
        if norm_name in ["login_button", "loginbutton"]:
            # page.locator('button.login-btn')
            return page.locator("button.login-btn")
            
        # Fallback to standard selector if not predefined
        return page.locator(element_name)
