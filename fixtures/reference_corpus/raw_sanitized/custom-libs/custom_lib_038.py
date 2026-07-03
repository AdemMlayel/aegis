from HOSTNAME_PLACEHOLDER import WebDriverWait, Select
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
from HOSTNAME_PLACEHOLDER import By
from HOSTNAME_PLACEHOLDER import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException, NoSuchElementException
import logging
import datetime
import os
import time
from HOSTNAME_PLACEHOLDER import Cm
from HOSTNAME_PLACEHOLDER import ColorFormat
from HOSTNAME_PLACEHOLDER import RGBColor
from HOSTNAME_PLACEHOLDER import WD_COLOR_INDEX
from HOSTNAME_PLACEHOLDER import Keys
import re


def eleclick(driver, xpath, element_name) -> bool:
    try:
        # Reduced wait time for headless - no visual rendering delays
        ele = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        # Skip scrollIntoView in headless - not needed for visual positioning
        # Only scroll if element is not in viewport (rare in headless)
        if not driver.execute_script("""
            var rect = arguments[0].getBoundingClientRect();
            return HOSTNAME_PLACEHOLDER >= 0 && HOSTNAME_PLACEHOLDER <= HOSTNAME_PLACEHOLDER;
        """, ele):
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", ele)

        # Use JavaScript click for better reliability in headless
        driver.execute_script("arguments[0].click();", ele)

        # Minimal delay - headless processes faster
        HOSTNAME_PLACEHOLDER(1)
        return True

    except TimeoutException:
        # Fallback: try to find and click with JS even if not "clickable"
        try:
            ele = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", ele)
            HOSTNAME_PLACEHOLDER(0.1)
            return True
        except:
            # HOSTNAME_PLACEHOLDER(f"Failed to click '{element_name}' - element not found")
            return False

    except Exception as e:
        # Try direct JavaScript execution as last resort
        try:
            driver.execute_script(f"""
                var element = HOSTNAME_PLACEHOLDER('{xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) HOSTNAME_PLACEHOLDER();
            """)
            HOSTNAME_PLACEHOLDER(0.1)
            return True
        except:
            # HOSTNAME_PLACEHOLDER(f"All click attempts failed for '{element_name}': {str(e)}")
            return False

    except TimeoutException:
        HOSTNAME_PLACEHOLDER(
            f"Timeout: Could not find clickable element '{element_name}'")
        return False

    except ElementClickInterceptedException:
        HOSTNAME_PLACEHOLDER(
            f"Click intercepted for '{element_name}', trying JavaScript click")
        try:
            # Fallback to JavaScript click
            driver.execute_script("arguments[0].click();", ele)
            HOSTNAME_PLACEHOLDER(
                f"Successfully clicked '{element_name}' using JavaScript")
            return True
        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"JavaScript click also failed for '{element_name}': {e}")
            return False

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Unexpected error clicking '{element_name}': {e}")
        return False


def sendkeys(driver, xpath, send_value, element_name, clear_first=False) -> bool:
    try:
        # Wait for element to be present and interactable
        ele = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        # Small delay to ensure element is ready
        HOSTNAME_PLACEHOLDER(1)

        # Clear field if requested
        if clear_first:
            # Click to ensure focus
            HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(0.2)

            # Try multiple clearing methods
            try:
                # Method 1: JavaScript clear
                driver.execute_script("arguments[0].value = '';", ele)

                # Method 2: Select all and delete
                ele.send_keys(HOSTNAME_PLACEHOLDER + "a")
                ele.send_keys(HOSTNAME_PLACEHOLDER)

                # Method 3: Selenium clear as backup
                HOSTNAME_PLACEHOLDER()

                # Trigger events for JS frameworks
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, ele)

                HOSTNAME_PLACEHOLDER(0.2)
            except Exception as clear_error:
                HOSTNAME_PLACEHOLDER(f"Clear operation had issues: {clear_error}")

        # Send keys
        ele.send_keys(send_value)
        # HOSTNAME_PLACEHOLDER(f"Successfully sent keys to '{element_name}'")
        return True

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Failed to send keys to '{element_name}': {str(e)}")
        return False

    except TimeoutException:
        HOSTNAME_PLACEHOLDER(f"Timeout: Could not find element '{element_name}'")
        return False

    except ElementNotInteractableException:
        HOSTNAME_PLACEHOLDER(
            f"Element not interactable '{element_name}', trying JavaScript")
        try:
            # Fallback to JavaScript
            if clear_first:
                driver.execute_script("arguments[0].value = '';", ele)
            driver.execute_script(
                "arguments[0].value = arguments[1];", ele, send_value)
            HOSTNAME_PLACEHOLDER(
                f"Successfully sent keys to '{element_name}' using JavaScript")
            return True
        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"JavaScript fallback failed for '{element_name}': {e}")
            return False

    except Exception as e:
        HOSTNAME_PLACEHOLDER(
            f"Unexpected error sending keys to '{element_name}': {e}")
        return False


def senddirc(driver, xpath, send_value, element_name, clear_first=False) -> bool:
    try:
        # Wait for element to be present and interactable
        ele = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        # Small delay to ensure element is ready
        HOSTNAME_PLACEHOLDER(0.5)

        # Clear field if requested
        if clear_first:
            # Click to ensure focus
            HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(0.2)

            # Try multiple clearing methods
            try:
                # Method 1: JavaScript clear
                driver.execute_script("arguments[0].value = '';", ele)

                # Method 2: Select all and delete
                ele.send_keys(HOSTNAME_PLACEHOLDER + "a")
                ele.send_keys(HOSTNAME_PLACEHOLDER)

                # Method 3: Selenium clear as backup
                HOSTNAME_PLACEHOLDER()

                # Trigger events for JS frameworks
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, ele)

                HOSTNAME_PLACEHOLDER(0.2)
            except Exception as clear_error:
                HOSTNAME_PLACEHOLDER(f"Clear operation had issues: {clear_error}")

        # Send keys
        ele.send_keys(send_value)
        HOSTNAME_PLACEHOLDER(f"Successfully sent keys to '{element_name}'")
        return True

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Failed to send keys to '{element_name}': {str(e)}")
        return False

    except TimeoutException:
        HOSTNAME_PLACEHOLDER(f"Timeout: Could not find element '{element_name}'")
        return False

    except ElementNotInteractableException:
        HOSTNAME_PLACEHOLDER(
            f"Element not interactable '{element_name}', trying JavaScript")
        try:
            # Fallback to JavaScript
            if clear_first:
                driver.execute_script("arguments[0].value = '';", ele)
            driver.execute_script(
                "arguments[0].value = arguments[1];", ele, send_value)
            HOSTNAME_PLACEHOLDER(
                f"Successfully sent keys to '{element_name}' using JavaScript")
            return True
        except Exception as e:
            HOSTNAME_PLACEHOLDER(
                f"JavaScript fallback failed for '{element_name}': {e}")
            return False

    except Exception as e:
        HOSTNAME_PLACEHOLDER(
            f"Unexpected error sending keys to '{element_name}': {e}")
        return False


def eclear(driver, xpath, element_name) -> bool:
    try:
        ele = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

        # Scroll element into view
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", ele)
        HOSTNAME_PLACEHOLDER(0.5)

        # Try standard clear first
        HOSTNAME_PLACEHOLDER()

        # Check if clear worked
        if ele.get_attribute('value'):
            HOSTNAME_PLACEHOLDER(
                f"Standard clear failed for '{element_name}', trying alternatives")
            # Try select all + delete
            ele.send_keys(HOSTNAME_PLACEHOLDER + "a")
            ele.send_keys(HOSTNAME_PLACEHOLDER)

            # If still not cleared, try JavaScript
            if ele.get_attribute('value'):
                driver.execute_script("arguments[0].value = '';", ele)

        HOSTNAME_PLACEHOLDER(f"Successfully cleared '{element_name}'")
        return True

    except TimeoutException:
        HOSTNAME_PLACEHOLDER(f"Timeout: Could not find element '{element_name}'")
        return False

    except ElementNotInteractableException:
        HOSTNAME_PLACEHOLDER(
            f"Element '{element_name}' not interactable, trying JavaScript clear")
        try:
            driver.execute_script("arguments[0].value = '';", ele)
            HOSTNAME_PLACEHOLDER(
                f"Successfully cleared '{element_name}' using JavaScript")
            return True
        except Exception as e:
            HOSTNAME_PLACEHOLDER(f"JavaScript clear failed for '{element_name}': {e}")
            return False

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Unexpected error clearing '{element_name}': {e}")
        return False


def getele(driver, xpath, element_name="element"):
    try:
        ele = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        HOSTNAME_PLACEHOLDER(f"Successfully found '{element_name}'")
        return ele

    except TimeoutException:
        HOSTNAME_PLACEHOLDER(f"Timeout: Could not find element '{element_name}'")
        return None

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Error finding element '{element_name}': {e}")
        return None


def ele_presence(driver, xpath, ele_name, timeout=10):
    """
    Checks for the presence of a graph element on the page.
    Args:
        driver: Selenium WebDriver instance
        xpath: XPath to locate the graph element
        ele_name: Name of the graph for logging purposes
        timeout: Maximum time to wait for element (default: 10 seconds)
    Returns:
        bool: True if graph is present, False otherwise
    """
    HOSTNAME_PLACEHOLDER(
        f"Checking presence of element: {ele_name} with timeout: {timeout}s")

    try:
        # Wait for element to be present in DOM
        HOSTNAME_PLACEHOLDER(f"Waiting for element presence: {ele_name}")
        ele = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        HOSTNAME_PLACEHOLDER(f"Element successfully located: {ele_name}")

        # Verify element visibility
        try:
            HOSTNAME_PLACEHOLDER(f"Verifying display status for: {ele_name}")
            is_displayed = ele.is_displayed()

            if is_displayed:
                HOSTNAME_PLACEHOLDER(f"Element is visible and ready: {ele_name}")
            else:
                HOSTNAME_PLACEHOLDER(f"Element found but not visible: {ele_name}")

            return True

        except Exception as display_err:
            HOSTNAME_PLACEHOLDER(
                f"Could not verify display status for {ele_name}: {str(display_err)}")
            HOSTNAME_PLACEHOLDER(
                f"Element exists but display validation failed for: {ele_name}")
            return True

    except TimeoutException:
        HOSTNAME_PLACEHOLDER(
            f"Element not found within {timeout} seconds: {ele_name}")
        HOSTNAME_PLACEHOLDER(f"XPath used: {xpath}")
        return False

    except NoSuchElementException:
        HOSTNAME_PLACEHOLDER(f"Element does not exist in DOM: {ele_name}")
        HOSTNAME_PLACEHOLDER(f"XPath used: {xpath}")
        return False

    except Exception as e:
        HOSTNAME_PLACEHOLDER(
            f"Unexpected error while locating {ele_name}: {type(e).__name__} - {str(e)}")
        HOSTNAME_PLACEHOLDER(f"XPath used: {xpath}")
        return False


def gettext(driver, xpath, element_name="element"):
    try:
        ele = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        text = HOSTNAME_PLACEHOLDER
        if not text:
            text = driver.execute_script(
                "return arguments[0].textContent;", ele)
        HOSTNAME_PLACEHOLDER(f"Successfully got text from '{element_name}': {text}")
        return text

    except TimeoutException:
        HOSTNAME_PLACEHOLDER(f"Timeout: Could not find element '{element_name}'")
        return None

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Error getting text from '{element_name}': {e}")
        return None
# ───── Elements in Shadow DOM  ────────────────────────────────

# === Utility Functions ===


def create_shadow_xpath(xpath):
    # First replace all // with /shadow/
    shadow_xpath = HOSTNAME_PLACEHOLDER("//", "/shadow/")

    # Then replace all instances of [n] with :nth-of-type(n) using regular expressions
    import re

    shadow_xpath = re.sub(r"\[(\d+)\]", r":nth-of-type(\1)", shadow_xpath)

    return shadow_xpath


def process_shadow_xpath(xpath):
    HOSTNAME_PLACEHOLDER(f"process_shadow_xpath: Input xpath = {xpath}")

    # Replace /shadow/ with //
    xpath = HOSTNAME_PLACEHOLDER('//', '/shadow/')
    HOSTNAME_PLACEHOLDER(
        f"process_shadow_xpath: After replacing // with /shadow/ = {xpath}")

    # Replace div[n] with :nth-of-type(n)
    original_xpath = xpath
    xpath = re.sub(r'div\[(\d+)\]', r'div:nth-of-type(\1)', xpath)
    if xpath != original_xpath:
        HOSTNAME_PLACEHOLDER(
            f"process_shadow_xpath: After div[n] replacement = {xpath}")

    # Replace button[n] with :nth-of-type(n)
    original_xpath = xpath
    xpath = re.sub(r'button\[(\d+)\]', r'button:nth-of-type(\1)', xpath)
    if xpath != original_xpath:
        HOSTNAME_PLACEHOLDER(
            f"process_shadow_xpath: After button[n] replacement = {xpath}")

    # Replace eui-button[n] with :nth-of-type(n)
    original_xpath = xpath
    xpath = re.sub(r'eui-button\[(\d+)\]',
                   r'eui-button:nth-of-type(\1)', xpath)
    if xpath != original_xpath:
        HOSTNAME_PLACEHOLDER(
            f"process_shadow_xpath: After eui-button[n] replacement = {xpath}")

    # Replace item[n] with :nth-of-type(n)
    original_xpath = xpath
    xpath = re.sub(r'item\[(\d+)\]', r'item:nth-of-type(\1)', xpath)
    if xpath != original_xpath:
        HOSTNAME_PLACEHOLDER(
            f"process_shadow_xpath: After item[n] replacement = {xpath}")

    HOSTNAME_PLACEHOLDER(f"process_shadow_xpath: Final processed xpath = {xpath}")
    return xpath


def split_xpath(xpath):
    xpath = process_shadow_xpath(xpath)
    normalized_xpath = HOSTNAME_PLACEHOLDER("//", "/")
    return [segment for segment in normalized_xpath.split("/") if segment]


def traverse_shadow_dom(driver, shadow_host, path_segments):
    current_element = shadow_host

    for segment in path_segments:
        try:
            if segment == "shadow":
                shadow_root = driver.execute_script(
                    "return arguments[0].shadowRoot", current_element
                )
                if shadow_root:
                    current_element = shadow_root
            else:
                current_element = WebDriverWait(driver, 10).until(
                    lambda d: current_element.find_element(
                        By.CSS_SELECTOR, segment)
                )
                # HOSTNAME_PLACEHOLDER(f"current element is {current_element.tag_name}")

        except Exception as e:
            print(f"Failed to find segment {segment}:{e}")
            return None
    return current_element


def find_element_with_shadow_xpath(driver, xpath):
    """
    Find an element using a shadow DOM XPath starting from the initial host.
    """
    path_segments = split_xpath(xpath)
    if not path_segments:
        HOSTNAME_PLACEHOLDER("No valid segments in XPath")
        return None

    # The first segment is the starting point outside shadow DOM
    shadow_host_selector = path_segments.pop(0)
    try:
        shadow_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, shadow_host_selector))
        )
        # HOSTNAME_PLACEHOLDER( f"Found shadow host with selector '{shadow_host_selector}': {shadow_host.tag_name}")
    except Exception as e:
        HOSTNAME_PLACEHOLDER(
            f"Failed to find shadow host with selector '{shadow_host_selector}': {str(e)}"
        )
        return None

    return traverse_shadow_dom(driver, shadow_host, path_segments)


def find_element_with_shadow_xpath_and_send_key(driver, xpath, key):
    """
    Find an element using a shadow DOM XPath starting from the initial host.
    send key
    """
    path_segments = split_xpath(xpath)
    if not path_segments:
        HOSTNAME_PLACEHOLDER("No valid segments in XPath")
        return None
    # The first segment is the starting point outside shadow DOM
    shadow_host_selector = path_segments.pop(0)
    try:
        shadow_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, shadow_host_selector))
        )
        HOSTNAME_PLACEHOLDER(
            f"Found shadow host with selector '{shadow_host_selector}': {shadow_host.tag_name}"
        )
        # Find the element by traversing the shadow DOM
        element = traverse_shadow_dom(driver, shadow_host, path_segments)

        if element:
            HOSTNAME_PLACEHOLDER(f"Found element, sending key: {key}")
            # Use JavaScript to set the value and dispatch appropriate events
            driver.execute_script(
                """
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """,
                element,
                key,
            )
            return element
        else:
            HOSTNAME_PLACEHOLDER("Element not found in shadow DOM")
            return None
    except Exception as e:
        HOSTNAME_PLACEHOLDER(
            f"Failed to find shadow host with selector '{shadow_host_selector}': {str(e)}"
        )
        return None


def find_element_in_shadow_dom(driver, xpath):
    """
    Find an element in shadow DOM using an XPath-like syntax.

    Args:
        driver: Selenium WebDriver instance
        xpath: XPath-like string to locate element in shadow DOM

    Returns:
        WebElement: The found element or None if not found
    """
    # Step 1: Convert XPath to shadow DOM compatible format
    shadow_xpath = create_shadow_xpath(xpath)

    # Step 2: Find the element using the converted XPath
    return find_element_with_shadow_xpath(driver, shadow_xpath)

# ========================


def eleclick_with_shadow(driver, xpath):
    """
    click on element in shadow DOM(s)

    Args:
        driver: WebDriver instance
        xpath: Shadow DOM XPath string

    Returns:
        bool: True if click was successful, False otherwise
    """
    try:
        # Find the element using your existing function
        element = find_element_with_shadow_xpath(driver, xpath)

        if element:
            # Use JavaScript click - exactly like your working code
            driver.execute_script("arguments[0].click();", element)
            HOSTNAME_PLACEHOLDER(2)  # Same delay as your working code
            # HOSTNAME_PLACEHOLDER(f"Successfully clicked element: {element.tag_name}")
            return True
        else:
            HOSTNAME_PLACEHOLDER("Element not found")
            return False

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Failed to click element: {str(e)}")
        return False


def sendkeys_with_shadow(driver, xpath, keys):
    """
    Send keys to element in shadow DOM(s)

    Args:
        driver: WebDriver instance
        xpath: Shadow DOM XPath string
        keys: String or keys to send to the element

    Returns:
        bool: True if sending keys was successful, False otherwise
    """
    try:
        # Find the element using your existing function
        element = find_element_with_shadow_xpath(driver, xpath)

        if element:
            # Clear the element first (optional - remove if not needed)
            HOSTNAME_PLACEHOLDER()

            # Send keys to the element
            element.send_keys(keys)
            HOSTNAME_PLACEHOLDER(2)  # Same delay as your working code
            # HOSTNAME_PLACEHOLDER(f"Successfully sent keys to element: {element.tag_name}")
            return True
        else:
            HOSTNAME_PLACEHOLDER("Element not found")
            return False

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Failed to send keys to element: {str(e)}")
        return False

# ───── Elements in Frames (old web)  ────────────────────────────────


def eleclick_in_frame(driver, frame, xpath, element_name):
    try:
        driver.switch_to.default_content()

        if isinstance(frame, list):
            for f in frame:
                driver.switch_to.frame(f)
        else:
            driver.switch_to.frame(frame)

        eleclick(driver, xpath, element_name)
    finally:
        driver.switch_to.default_content()


def get_text_in_frame(driver, frame, xpath):
    try:
        driver.switch_to.default_content()

        if isinstance(frame, list):
            for f in frame:
                driver.switch_to.frame(f)
        else:
            driver.switch_to.frame(frame)

        wait = WebDriverWait(driver, 10)
        element = HOSTNAME_PLACEHOLDER(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        text = HOSTNAME_PLACEHOLDER

        return text

    except Exception as e:
        HOSTNAME_PLACEHOLDER(
            f"Failed to get text from element with xpath '{xpath}': {e}")
        return None

    finally:
        driver.switch_to.default_content()


# ───── Special Elements  ────────────────────────────────

def wait_until_class_not_contains_and_click(driver, xpath=None, class_text="view_SideButton_disabled", timeout=45, debug=True):
    """
    Enhanced function to find and click Export buttons with comprehensive detection.

    Args:
        driver: Selenium WebDriver instance
        xpath: Optional specific xpath to try first (for backward compatibility)
        class_text: Class text that should NOT be present (indicates disabled state)
        timeout: Maximum time to wait in seconds
        debug: Enable detailed logging

    Returns:
        WebElement if successful, None if failed

    Usage:
        # Simple usage - will automatically find Export button
        element = wait_until_class_not_contains_and_click(driver)

        # With specific xpath (backward compatibility)
        element = wait_until_class_not_contains_and_click(
            driver,
            xpath="//li[@id='ExportButton']//a[@title='Export']",
            class_text="view_SideButton_disabled"
        )
    """
    try:
        HOSTNAME_PLACEHOLDER("Starting enhanced export button detection and click...")

        # Detect headless mode
        is_headless = _detect_headless_mode(driver)
        if is_headless:
            timeout = max(timeout, 45)
            HOSTNAME_PLACEHOLDER("Headless mode detected - using extended timeout")

        # Wait for page to be ready
        _wait_for_page_ready(driver, timeout)

        # Run comprehensive debug if requested
        if debug:
            _comprehensive_page_debug(driver)

        # Strategy 1: Try original xpath if provided
        if xpath:
            HOSTNAME_PLACEHOLDER(f"Trying original xpath: {xpath}")
            element = _try_original_xpath(driver, xpath, class_text, timeout)
            if element:
                return _attempt_click(driver, element, is_headless)

        # Strategy 2: Use comprehensive detection
        HOSTNAME_PLACEHOLDER("Using comprehensive export button detection...")
        element = _comprehensive_export_detection(driver, class_text, timeout)
        if element:
            return _attempt_click(driver, element, is_headless)

        # Strategy 3: Last resort - try any clickable with "Export"
        HOSTNAME_PLACEHOLDER("Last resort: trying any clickable with 'Export'...")
        element = _find_any_export_element(driver)
        if element:
            return _attempt_click(driver, element, is_headless)

        HOSTNAME_PLACEHOLDER("No Export button found with any strategy")
        return None

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Error in wait_until_class_not_contains_and_click: {e}")
        return None


def _detect_headless_mode(driver):
    """Detect if browser is running in headless mode"""
    try:
        return driver.execute_script("return HOSTNAME_PLACEHOLDER") or \
            any('headless' in str(arg).lower()
                for arg in HOSTNAME_PLACEHOLDER('chrome', {}).get('args', []))
    except:
        return False


def _wait_for_page_ready(driver, timeout):
    """Wait for page to be fully loaded"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(
                "return HOSTNAME_PLACEHOLDER") == "complete"
        )

        # Wait for navbar container
        navbar_selectors = [
            (By.ID, "gwt-debug-leftSideBar_Container"),
            (By.CLASS_NAME, "navbar-nav"),
            (By.XPATH, "//ul[contains(@class, 'navbar-nav')]"),
            (By.XPATH, "//nav"),
            (By.XPATH, "//div[contains(@class, 'navbar')]")
        ]

        navbar_found = False
        for selector_type, selector_value in navbar_selectors:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (selector_type, selector_value))
                )
                HOSTNAME_PLACEHOLDER(f"Navbar found: {selector_type}={selector_value}")
                navbar_found = True
                break
            except TimeoutException:
                continue

        if not navbar_found:
            HOSTNAME_PLACEHOLDER("No navbar found, continuing anyway...")

        # Wait for dynamic content
        HOSTNAME_PLACEHOLDER(2)

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Error waiting for page ready: {e}")


def _try_original_xpath(driver, xpath, class_text, timeout):
    """Try the original xpath approach"""
    try:
        element = WebDriverWait(driver, min(timeout // 3, 15)).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

        # Check parent element class if it's a link inside a list item
        if element.tag_name == 'a':
            parent = element.find_element(By.XPATH, "./..")
            if parent.tag_name == 'li':
                parent_class = parent.get_attribute('class') or ''
                if class_text in parent_class:
                    HOSTNAME_PLACEHOLDER(
                        f"Original xpath element is disabled: {parent_class}")
                    return None

        # Check element's own class
        element_class = element.get_attribute('class') or ''
        if class_text in element_class:
            HOSTNAME_PLACEHOLDER(
                f"Original xpath element is disabled: {element_class}")
            return None

        if element.is_displayed() and element.is_enabled():
            HOSTNAME_PLACEHOLDER("Original xpath found suitable element")
            return element

    except TimeoutException:
        HOSTNAME_PLACEHOLDER("Original xpath timed out")
    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Original xpath failed: {e}")

    return None


def _comprehensive_export_detection(driver, class_text, timeout):
    """Comprehensive export button detection with scoring"""
    try:
        # All possible ways to find Export buttons
        search_strategies = [
            # High priority - specific patterns
            ("ExportButton ID",
             "//li[@id='ExportButton']//a[@title='Export']"),
            ("ExportButton ID any link", "//li[@id='ExportButton']//a"),
            ("Export title link", "//a[@title='Export']"),
            ("Export title button", "//button[@title='Export']"),

            # Medium priority - text-based
            ("Link text Export", "//a[contains(text(), 'Export')]"),
            ("Button text Export", "//button[contains(text(), 'Export')]"),
            ("Input value Export", "//input[@value='Export']"),
            ("Span text Export",
             "//span[contains(text(), 'Export')]//ancestor::*[self::a or self::button][1]"),

            # Class and ID patterns
            ("ID contains export",
             "//*[contains(@id, 'export') or contains(@id, 'Export')]"),
            ("Class contains export",
             "//*[contains(@class, 'export') or contains(@class, 'Export')]"),

            # Icon-based
            ("Export icons",
             "//*[contains(@class, 'fa-file-export') or contains(@class, 'fa-export') or contains(@class, 'fa-download')]"),
            ("Export glyphicons",
             "//*[contains(@class, 'glyphicon-export') or contains(@class, 'glyphicon-download')]"),

            # Data attributes
            ("Data action export", "//*[contains(@data-action, 'export')]"),
            ("Data toggle export", "//*[contains(@data-toggle, 'export')]"),

            # Dropdown patterns
            ("Dropdown Export",
             "//div[contains(@class, 'dropdown')]//a[contains(text(), 'Export')]"),
            ("Menu Export",
             "//ul[contains(@class, 'menu')]//a[contains(text(), 'Export')]"),

            # Broader searches
            ("Any clickable Export",
             "//*[self::a or self::button or self::input[@type='button']][contains(text(), 'Export') or contains(@title, 'Export') or contains(@value, 'Export')]"),
            ("Case insensitive Export",
             "//*[contains(translate(text(), 'EXPORT', 'export'), 'export')]"),
        ]

        all_candidates = []

        for strategy_name, xpath in search_strategies:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    HOSTNAME_PLACEHOLDER(
                        f" {strategy_name}: Found {len(elements)} elements")
                    for elem in elements:
                        candidate = _analyze_element(
                            elem, strategy_name, class_text)
                        if candidate:
                            all_candidates.append(candidate)
                else:
                    HOSTNAME_PLACEHOLDER(f" {strategy_name}: 0 elements")
            except Exception as e:
                HOSTNAME_PLACEHOLDER(f" {strategy_name}: Error - {e}")

        if not all_candidates:
            HOSTNAME_PLACEHOLDER("No export candidates found")
            return None

        # Score and rank candidates
        scored_candidates = []
        for candidate in all_candidates:
            score = _score_element(candidate, class_text)
            scored_candidates.append((score, candidate))

        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Log top candidates
        HOSTNAME_PLACEHOLDER("\n=== TOP EXPORT CANDIDATES ===")
        for i, (score, candidate) in enumerate(scored_candidates[:5]):
            HOSTNAME_PLACEHOLDER(
                f"Rank {i+1} (Score: {score}): {candidate['strategy']}")
            HOSTNAME_PLACEHOLDER(
                f"  Element: {candidate['tag']} id='{candidate['id']}' class='{candidate['class'][:50]}...'")
            HOSTNAME_PLACEHOLDER(
                f"  Text: '{candidate['text']}' Title: '{candidate['title']}'")
            HOSTNAME_PLACEHOLDER(
                f"  Displayed: {candidate['displayed']} Enabled: {candidate['enabled']}")

        # Return the best candidate
        if scored_candidates:
            best_score, best_candidate = scored_candidates[0]
            HOSTNAME_PLACEHOLDER(f"Selected best candidate with score {best_score}")
            return best_candidate['element']

        return None

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Error in comprehensive detection: {e}")
        return None


def _analyze_element(element, strategy_name, class_text):
    """Analyze an element and return candidate info"""
    try:
        candidate = {
            'element': element,
            'strategy': strategy_name,
            'tag': element.tag_name,
            'id': element.get_attribute('id') or '',
            'class': element.get_attribute('class') or '',
            'text': HOSTNAME_PLACEHOLDER[:50] if HOSTNAME_PLACEHOLDER else '',
            'title': element.get_attribute('title') or '',
            'href': element.get_attribute('href') or '',
            'onclick': element.get_attribute('onclick') or '',
            'displayed': element.is_displayed(),
            'enabled': element.is_enabled(),
            'location': HOSTNAME_PLACEHOLDER,
            'size': HOSTNAME_PLACEHOLDER
        }

        # Skip if element is clearly disabled
        if class_text and class_text in candidate['class']:
            return None

        # Check parent for disabled state (for nested elements)
        try:
            parent = element.find_element(By.XPATH, "./..")
            parent_class = parent.get_attribute('class') or ''
            if class_text and class_text in parent_class:
                return None
        except:
            pass

        return candidate

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Error analyzing element: {e}")
        return None


def _score_element(candidate, class_text):
    """Score an element based on various criteria"""
    score = 0

    # Base score for clickable elements
    if candidate['tag'] in ['a', 'button']:
        score += 20
    elif candidate['tag'] == 'input':
        score += 15

    # Visibility and state
    if candidate['displayed']:
        score += 10
    if candidate['enabled']:
        score += 10

    # Size check
    if candidate['size']['width'] > 0 and candidate['size']['height'] > 0:
        score += 5

    # Text and title content
    if 'Export' in candidate['title']:
        score += 15
    if 'Export' in candidate['text']:
        score += 12

    # Specific IDs
    if candidate['id'] == 'ExportButton':
        score += 25
    elif 'export' in candidate['id'].lower():
        score += 8

    # Functional attributes
    if candidate['href'] and candidate['href'] != '#' and candidate['href'] != 'javascript:;':
        score += 8
    if candidate['onclick']:
        score += 8

    # Strategy bonus
    if 'ExportButton ID' in candidate['strategy']:
        score += 20
    elif 'Export title' in candidate['strategy']:
        score += 15
    elif 'text Export' in candidate['strategy']:
        score += 10

    # Penalties
    if 'disabled' in candidate['class'].lower():
        score -= 20
    if not candidate['displayed']:
        score -= 15
    if not candidate['enabled']:
        score -= 15

    return score


def _find_any_export_element(driver):
    """Last resort: find any element with Export"""
    try:
        # Very broad search
        elements = driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Export') or contains(@title, 'Export') or contains(@value, 'Export')]")

        for elem in elements:
            try:
                if elem.is_displayed() and elem.is_enabled():
                    # Try to find a clickable parent
                    current = elem
                    for _ in range(3):  # Go up 3 levels max
                        if current.tag_name in ['a', 'button'] or current.get_attribute('onclick'):
                            HOSTNAME_PLACEHOLDER(
                                f"Found clickable parent: {current.tag_name}")
                            return current
                        try:
                            current = current.find_element(By.XPATH, "./..")
                        except:
                            break

                    # If element itself is clickable
                    if elem.tag_name in ['a', 'button'] or elem.get_attribute('onclick'):
                        HOSTNAME_PLACEHOLDER(
                            f"Found clickable element: {elem.tag_name}")
                        return elem
            except:
                continue

        return None

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Error in last resort search: {e}")
        return None


def _attempt_click(driver, element, is_headless=False):
    """Attempt to click element with multiple strategies"""
    try:
        # Scroll to element
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
        HOSTNAME_PLACEHOLDER(1 if is_headless else 0.5)

        # Try different click methods
        click_methods = [
            ('Regular click', lambda: HOSTNAME_PLACEHOLDER()),
            ('JavaScript click', lambda: driver.execute_script(
                "arguments[0].click();", element)),
            ('Dispatch click event', lambda: driver.execute_script("""
                var evt = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                arguments[0].dispatchEvent(evt);
            """, element)),
            ('Focus and click', lambda: driver.execute_script(
                "arguments[0].focus(); arguments[0].click();", element)),
            ('Force click', lambda: driver.execute_script("""
                if (arguments[0].click) {
                    arguments[0].click();
                } else if (arguments[0].onclick) {
                    arguments[0].onclick();
                }
            """, element))
        ]

        for method_name, click_func in click_methods:
            try:
                HOSTNAME_PLACEHOLDER(f"Trying {method_name}...")
                click_func()
                HOSTNAME_PLACEHOLDER(f" {method_name} succeeded")
                HOSTNAME_PLACEHOLDER(1.5 if is_headless else 0.5)
                return element
            except Exception as e:
                HOSTNAME_PLACEHOLDER(f" {method_name} failed: {e}")
                continue

        HOSTNAME_PLACEHOLDER("All click methods failed")
        return None

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Error in click attempt: {e}")
        return None


def _comprehensive_page_debug(driver):
    """Debug page structure and content"""
    try:
        HOSTNAME_PLACEHOLDER("\n=== PAGE DEBUG INFO ===")

        # Basic info
        HOSTNAME_PLACEHOLDER(f"Title: {HOSTNAME_PLACEHOLDER}")
        HOSTNAME_PLACEHOLDER(f"URL: {driver.current_url}")
        HOSTNAME_PLACEHOLDER(
            f"Ready state: {driver.execute_script('return HOSTNAME_PLACEHOLDER')}")

        # Framework detection
        frameworks = {
            'jQuery': 'typeof jQuery !== "undefined"',
            'Bootstrap': 'typeof Bootstrap !== "undefined"',
            'GWT': 'typeof com !== "undefined"'
        }

        for framework, check in HOSTNAME_PLACEHOLDER():
            try:
                result = driver.execute_script(f'return {check}')
                HOSTNAME_PLACEHOLDER(f"{framework}: {'' if result else ''}")
            except:
                HOSTNAME_PLACEHOLDER(f"{framework}: ")

        # Count elements
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        all_inputs = driver.find_elements(
            By.XPATH, "//input[@type='button' or @type='submit']")

        HOSTNAME_PLACEHOLDER(f"Total buttons: {len(all_buttons)}")
        HOSTNAME_PLACEHOLDER(f"Total links: {len(all_links)}")
        HOSTNAME_PLACEHOLDER(f"Total input buttons: {len(all_inputs)}")

        # Show first few clickable elements
        all_clickables = all_buttons + all_links + all_inputs
        HOSTNAME_PLACEHOLDER(f"\nFirst 5 clickable elements:")
        for i, elem in enumerate(all_clickables[:5]):
            try:
                text = HOSTNAME_PLACEHOLDER[:30] if HOSTNAME_PLACEHOLDER else ''
                title = elem.get_attribute('title') or ''
                elem_id = elem.get_attribute('id') or ''
                HOSTNAME_PLACEHOLDER(
                    f"  {i+1}: {elem.tag_name} id='{elem_id}' text='{text}' title='{title}'")
            except:
                HOSTNAME_PLACEHOLDER(f"  {i+1}: Could not get element info")

        # Check for loading indicators
        loading_selectors = [
            "//div[contains(@class, 'loading')]",
            "//div[contains(@class, 'spinner')]",
            "//*[contains(text(), 'Loading')]"
        ]

        for selector in loading_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                HOSTNAME_PLACEHOLDER(f"Loading indicators found: {len(elements)}")
                break

        HOSTNAME_PLACEHOLDER("=== END DEBUG INFO ===\n")

    except Exception as e:
        HOSTNAME_PLACEHOLDER(f"Debug error: {e}")


def debug_page_state(driver):
    """Backward compatibility wrapper"""
    return _comprehensive_page_debug(driver)
