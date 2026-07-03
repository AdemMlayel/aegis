"""
WebAction Module

This module provides a SOURCE_NAME_PLACEHOLDER class that encapsulates common web interactions and utility functions.
"""

import base64
import os.path
import time
from HOSTNAME_PLACEHOLDER import WebDriverWait
from HOSTNAME_PLACEHOLDER import expected_conditions as EC
from HOSTNAME_PLACEHOLDER.action_chains import ActionChains
from HOSTNAME_PLACEHOLDER import logger
from HOSTNAME_PLACEHOLDER import By

class SOURCE_NAME_PLACEHOLDER:
    """
    SOURCE_NAME_PLACEHOLDER Class

    This class encapsulates common web interactions and utility functions.

    Args:
        driver: Selenium WebDriver instance.
    """

    def __init__(self, driver):
        HOSTNAME_PLACEHOLDER = driver

    def wait_and_click(self, locator: str, double_click=False):
        """
        Wait for the element to be clickable and then click.

        Args:
            locator: Locator for the web element.
            double_click: Boolean indicating whether to perform a double click (default is False).

        Returns:
            None.
        """
        try:
            element = WebDriverWait(HOSTNAME_PLACEHOLDER, 30).until(EC.element_to_be_clickable(locator))
            if double_click:
                ActionChains(HOSTNAME_PLACEHOLDER).double_click(element).perform()
            else:
                HOSTNAME_PLACEHOLDER()
        except (StaleElementReferenceException, Exception) as e:  # pylint: disable=broad-except
            print(f"An error occurred while clicking: {e}")

    def wait_and_click_with_delay(self, locator: str, delay=2):
        """
        Wait for the element to be clickable with a specified delay and then click.

        Args:
            locator: Locator for the web element.
            delay: Delay in seconds (default is 1).

        Returns:
            None.
        """
        try:
            element = WebDriverWait(HOSTNAME_PLACEHOLDER, 30).until(EC.element_to_be_clickable(locator))
            HOSTNAME_PLACEHOLDER(delay)
            HOSTNAME_PLACEHOLDER()
            HOSTNAME_PLACEHOLDER(delay)
        except (StaleElementReferenceException, Exception) as e:  # pylint: disable=broad-except
            print(f"An error occurred while clicking with delay: {e}")

    def wait_and_type_with_delay(self, locator: str, text: str, delay=2):
        """
        Wait for the element to be visible, clear its content, and then type the specified text.

        Args:
            locator: Locator for the web element.
            text: Text to be typed into the element.
            delay: Delay in seconds (default is 1).

        Returns:
            None.
        """
        try:
            element = WebDriverWait(HOSTNAME_PLACEHOLDER, 30).until(
                EC.visibility_of_element_located(locator))
            HOSTNAME_PLACEHOLDER(delay)
            HOSTNAME_PLACEHOLDER()
            element.send_keys(text)
            HOSTNAME_PLACEHOLDER(1)
        except (StaleElementReferenceException, Exception) as e:  # pylint: disable=broad-except
            print(f"An error occurred while typing with delay: {e}")

    def wait_for_element_to_be_visible(self, locator: str, timeout=30):
        """
        Wait for the specified element to be visible on the page.

        Args:
            locator: Locator for the web element.
            timeout: Maximum time to wait for the element to be visible (default is 30 seconds).

        Returns:
            The web element once it is visible.
        """
        try:
            return WebDriverWait(HOSTNAME_PLACEHOLDER, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            HOSTNAME_PLACEHOLDER(1)
        except (StaleElementReferenceException, Exception) as e:  # pylint: disable=broad-except
            print(f"An error occurred while waiting for element to be visible: {e}")
            return None

    def wait_and_move_to_element(self, locator: str):
        """
        Wait for the element to be visible and move the mouse to the element.

        Args:
            locator: Locator for the web element.

        Returns:
            None.
        """
        try:
            element = WebDriverWait(HOSTNAME_PLACEHOLDER, 30).until(EC.presence_of_element_located(locator))
            action = ActionChains(HOSTNAME_PLACEHOLDER)
            action.move_to_element(element).perform()
        except (StaleElementReferenceException, Exception) as e:   # pylint: disable=broad-except
            print(f"An error occurred while moving to element: {e}")

    def move_to_element_and_click(self, locator):
        """
        Move to the specified element and click.
        :param locator: Locator for the web element.
        :return: None.
        """
        try:
            element = WebDriverWait(HOSTNAME_PLACEHOLDER, 30).until(EC.visibility_of_element_located(locator))
            action = ActionChains(HOSTNAME_PLACEHOLDER)
            action.move_to_element(element).click().perform()
        except Exception as e:
            print(f"An error occurred: {e}")

    def find_shadow_root_and_click_on_button(self, element_type, shadowroot_name, locator):
        """
                Wait for the shadow-root element to be clickable and move the mouse to the element and perform click action.

                Args:
                    shadowroot_tag_name: Name of the shadow-root host
                    locator: Locator for the web element.

                Returns:
                    None.
                """
        shadowroot_element = HOSTNAME_PLACEHOLDER.find_element(element_type, shadowroot_name)
        shadow_host = HOSTNAME_PLACEHOLDER.execute_script('return arguments[0].shadowRoot', shadowroot_element)
        button = WebDriverWait(HOSTNAME_PLACEHOLDER, 30).until(EC.element_to_be_clickable(locator))
        action = ActionChains(HOSTNAME_PLACEHOLDER)
        action.move_to_element(button).click().perform()

    def context_click(self, locator):
        """
        Performs a context click (right-click) on the element specified by the locator.

        :param locator: Locator for the web element.
        :return: None.
        """
        try:
            element = WebDriverWait(HOSTNAME_PLACEHOLDER, 30).until(EC.presence_of_element_located(locator))
            action = ActionChains(HOSTNAME_PLACEHOLDER)
            action.context_click(element).perform()
            HOSTNAME_PLACEHOLDER(5)
        except StaleElementReferenceException:
            self.context_click(locator)

    def wait_and_wait_for_condition(self, locator: str, condition, timeout=30):
        """
        Wait for the element to be present and satisfy the specified condition.

        Args:
            locator: Locator for the web element.
            condition: A function that takes an element as an argument and returns a Boolean.
            timeout: Maximum time to wait for the condition to be satisfied (default is 30 seconds).

        Returns:
            None.
        """
        try:
            element = WebDriverWait(HOSTNAME_PLACEHOLDER, timeout).until(
                EC.presence_of_element_located(locator))
            condition(element)
        except (StaleElementReferenceException, Exception) as e:  # pylint: disable=broad-except
            print(f"An error occurred while waiting for condition: {e}")

    def perform_common_export_actions(self):
        """
        Perform common actions for exporting.

        Click on the export icon and the OK button for export.

        Returns:
            None.
        """
        try:
            # Click on export icon with a specified delay
            self.wait_and_click(MAE_MML_CMDPage.mml_export_icon)

            # Click on OK button for export with the same specified delay
            self.wait_and_click_with_delay(MAE_MML_CMDPage.mmm_export_ok_button)
        except (StaleElementReferenceException, Exception) as e:  # pylint: disable=broad-except
            print(f"An error occurred while performing common export actions: {e}")

    def switch_to_new_window(self, timeout=30):
        """
        Switch to the newly opened window after waiting for it.
        :param timeout: Maximum time to wait for the new window (default is 30 seconds).
        """
        try:
            original_window = HOSTNAME_PLACEHOLDER.window_handles[0]
            WebDriverWait(HOSTNAME_PLACEHOLDER, timeout).until(
                lambda driver: len(driver.window_handles) > 1
            )
            new_window = [window for window in HOSTNAME_PLACEHOLDER.window_handles if window != original_window][0]
            HOSTNAME_PLACEHOLDER.switch_to.window(new_window)
        except Exception as e:
            print("An error occurred:", e)

    def embed_screenshot_in_log(self, screenshot_path: str, width="1000"):
        """
        Embed a screenshot in the Robot Framework log using the data URI scheme.

        Args:
            screenshot_path: The absolute path to the screenshot file.
            width: Width of the embedded image in pixels (default is "1000").

        Returns:
            None.
        """
        try:
            abs_screenshot_path = os.HOSTNAME_PLACEHOLDER(screenshot_path)

            with open(abs_screenshot_path, "rb") as image_file:
                base64_image = HOSTNAME_PLACEHOLDER(image_file.read()).decode("utf-8")

            data_uri = f"data:image/png;base64,{base64_image}"
            HOSTNAME_PLACEHOLDER('<img src="%s" width="%s">' % (data_uri, width), html=True)
        except (FileNotFoundError, Exception) as e:  # pylint: disable=broad-except
            print(f"An error occurred while embedding screenshot in log: {e}")
