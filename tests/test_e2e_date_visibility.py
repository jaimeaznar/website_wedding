"""End-to-end tests for date-based visibility using Playwright."""
import pytest
import re
from playwright.sync_api import sync_playwright, expect


class TestCardVisibilityE2E:
    """Test actual card visibility in the browser."""
    
    BASE_URL = "http://localhost:5001"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Start browser for each test."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        yield
        self.browser.close()
        self.playwright.stop()
    
    def inject_test_date(self, test_date):
        """Inject a fake date into the page's JavaScript before it loads."""
        self.page.add_init_script(f"""
            // Override Date constructor BEFORE any scripts run
            const FAKE_NOW = new Date('{test_date}').getTime();
            const RealDate = window.Date;
            
            window.Date = class extends RealDate {{
                constructor(...args) {{
                    if (args.length === 0) {{
                        super(FAKE_NOW);
                    }} else {{
                        super(...args);
                    }}
                }}
                
                static now() {{
                    return FAKE_NOW;
                }}
                
                getTime() {{
                    if (this.constructor === window.Date && arguments.length === 0) {{
                        return FAKE_NOW;
                    }}
                    return super.getTime();
                }}
            }};
        """)
    
    def test_all_cards_visible_before_deadline(self):
        """All cards visible before RSVP deadline."""
        self.inject_test_date('2026-05-05T12:00:00')
        self.page.goto(self.BASE_URL)
        self.page.wait_for_load_state('networkidle')
        
        # Check RSVP card is visible (has both data-target and data-href)
        rsvp_card = self.page.locator('.clickable-card[data-href*="rsvp"]')
        expect(rsvp_card).to_be_visible()
        
        # Check Accommodation card is visible
        accommodation_card = self.page.locator('[data-target="accommodation"]')
        expect(accommodation_card).to_be_visible()
        
        # Check countdown shows numbers (not celebration)
        days = self.page.locator('#days')
        expect(days).to_be_visible()
    
    def test_rsvp_hidden_on_deadline(self):
        """RSVP card hidden on deadline day."""
        self.inject_test_date('2026-05-06T12:00:00')
        self.page.goto(self.BASE_URL)
        self.page.wait_for_load_state('networkidle')
        
        # RSVP should be hidden
        rsvp_card = self.page.locator('.clickable-card[data-href*="rsvp"]')
        expect(rsvp_card).to_be_hidden()
        
        # Accommodation should still be visible
        accommodation_card = self.page.locator('[data-target="accommodation"]')
        expect(accommodation_card).to_be_visible()
    
    def test_cards_hidden_on_wedding_day(self):
        """RSVP and Accommodation hidden on wedding day."""
        self.inject_test_date('2026-06-06T12:00:00')
        self.page.goto(self.BASE_URL)
        self.page.wait_for_load_state('networkidle')
        
        # Both should be hidden
        rsvp_card = self.page.locator('.clickable-card[data-href*="rsvp"]')
        expect(rsvp_card).to_be_hidden()
        
        accommodation_card = self.page.locator('[data-target="accommodation"]')
        expect(accommodation_card).to_be_hidden()
    
    def test_celebration_message_on_wedding_day(self):
        """Shows celebration message instead of countdown on wedding day."""
        self.inject_test_date('2026-06-06T14:00:00')
        self.page.goto(self.BASE_URL)
        self.page.wait_for_load_state('networkidle')
        
        # Give time for countdown script to run
        self.page.wait_for_timeout(1000)
        
        # Should show celebration message
        celebration = self.page.locator('.celebration-message')
        expect(celebration).to_be_visible()
        
        # Should contain the celebration text
        celebration_text = self.page.locator('.celebration-text')
        expect(celebration_text).to_be_visible()
    
    def test_modal_not_accessible_when_card_hidden(self):
        """Accommodation modal cannot be opened when card is hidden."""
        self.inject_test_date('2026-06-06T12:00:00')
        self.page.goto(self.BASE_URL)
        self.page.wait_for_load_state('networkidle')
        
        # Modal should not be in DOM (removed) or hidden
        accommodation_modal = self.page.locator('#accommodation-modal')
        expect(accommodation_modal).to_have_count(0)