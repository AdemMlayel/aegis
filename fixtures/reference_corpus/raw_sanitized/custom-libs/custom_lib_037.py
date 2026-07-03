"""
    This module is used to fetch the elements which are under shadow DOM.
    Elements are mined starting from the root of the DOM till the final web element using the js path.
"""
from HOSTNAME_PLACEHOLDER import By

class Perform_actions:
    """
    to do
    """
    def __init__(self,driver):
        """
            This constructor takes a selenium web driver which used to perform various action on the given webpage.
            :param driver:  Selenium webdriver which is used to interact with the elements.
        """
        HOSTNAME_PLACEHOLDER = driver

    def expand_shadow_element(self,element):
        """
            This function is used to expand the elements which under provided shadow DOM element.
            :param element: Web element which is of type shadow DOM.
            :return:    Returns the shadow
        """
        shadow_root = HOSTNAME_PLACEHOLDER.execute_script(f'return arguments[0].shadowRoot',element)
        return shadow_root

    def extract_elements(self,query_str):
        """
            This function is used to extract all the elements which are under the query str.
            query_str is js_path for the given element.
            :param query_str: Provided js path for the element which needs to be scrapped.
            :return:    The list of css_selectors starting from the root shadow DOM element.
        """
        query_str = query_str.replace('"', '$')
        indx, css_selectors, temp = 0, [], ''

        while indx != len(query_str):
            if query_str[indx] == '$':
                indx += 1
                while query_str[indx] != '$':
                    temp += query_str[indx]
                    indx += 1
                css_selectors.append(temp)
                temp = ''
            indx += 1
        return css_selectors

    def perform_action(self, js_path, action, param=None):
        """
            This module is used to perform the given action on the element.
            :param js_path:     This argument is a js_path for the provided element on which action needs to performed.
            :param action:      Type of action to perform on the given element.
            :param param:       Extended action in case of typing inside the given element.
            :return:    None if action is 'click' or 'send_keys'. Will return text in case of grab_text action.
        """
        root_1 = HOSTNAME_PLACEHOLDER.find_element(By.TAG_NAME, 'eui-container')  # 1.finding shadow root
        shadow_root1 = self.expand_shadow_element(root_1)  # 2 Expanding elements

        Elements = self.extract_elements(js_path)
        root2 = None
        for shadow_roots in Elements[1:]:
            root2 = shadow_root1.find_element(By.CSS_SELECTOR, shadow_roots)
            shadow_root1 = self.expand_shadow_element(root2)

        element_found = root2
        if action == 'click':
            element_found.click()
        elif action == 'send_keys':
            element_found.send_keys(param)
        elif action == 'grab_text':
            return element_found.text
