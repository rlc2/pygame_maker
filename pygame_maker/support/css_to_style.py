"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Game engine CSS styling module.
"""

import re
import logging
from pyparsing import Literal, Word, Optional, ZeroOrMore, OneOrMore, nums, hexnums, alphas, \
    Regex, Keyword, Combine, delimitedList

def collect_hash_from_props(props, all_kwargs):
    """
    Produce a sub-set of a keyword argument mapping containing only the listed
    keys.

    :param props: The list of property name keys
    :type props: list
    :param all_kwargs: A keyword args dict
    :type all_kwargs: dict
    :returns: A subset of all_kwargs
    :rtype: dict
    """
    new_kwargs = {}
    if "id" in props:
        new_kwargs["element_id"] = all_kwargs["element_id"]
    if "type" in props:
        new_kwargs["element_type"] = all_kwargs["element_type"]
    if "class" in props:
        new_kwargs["element_class"] = all_kwargs["element_class"]
    if "pclass" in props:
        new_kwargs["pseudo_class"] = all_kwargs["pseudo_class"]
    if "attribute" in props:
        new_kwargs["attribute_dict"] = all_kwargs["attribute_dict"]
    return new_kwargs

def attribute_match(element, attribute_dict):
    """
    Compare a CSS style entry with an attribute mapping, and determine
    whether the attribute comparison matches.

    :param element: A CSS style entry
    :type element: CSSStyleEntry
    :param attribute_dict: The attribute mapping
    :type attribute_dict: dict
    :returns: True if the attribute mapping is matched by the CSS entry,
        False otherwise.
    :rtype: bool
    """
    matched = False
    if element.attr_str in list(attribute_dict.keys()):
        attr_val = attribute_dict[element.attr_str]
        if element.attr_type == "matches":
            matched = (element.attr_val == attr_val)
        elif element.attr_type == "starts_with_word":
            minfo = re.search(r"^{}\W".format(element.attr_val), attr_val)
            if minfo is not None:
                matched = True
            minfo = re.search("^{}$".format(element.attr_val), attr_val)
            if minfo is not None:
                matched = True
        elif element.attr_type == "contains_word":
            minfo = re.search(r"\W{}\W".format(element.attr_val), attr_val)
            if minfo is not None:
                matched = True
            minfo = re.search(r"^{}\W".format(element.attr_val), attr_val)
            if minfo is not None:
                matched = True
            minfo = re.search(r"\W{}$".format(element.attr_val), attr_val)
            if minfo is not None:
                matched = True
            minfo = re.search("^{}$".format(element.attr_val), attr_val)
            if minfo is not None:
                matched = True
        elif element.attr_type == "starts_with":
            matched = element.attr_val.startswith(attr_val)
        elif element.attr_type == "ends_with":
            matched = element.attr_val.endswith(attr_val)
        elif element.attr_type == "contains":
            matched = (element.attr_val in attr_val)
        elif element.attr_type == "any":
            matched = True
    return matched


class CSSStyleEntry(object):
    """Represent a single CSS style block."""
    SELECTOR_TYPES = ["type", "id", "class", "pclass", "attribute"]
    ID_SELECTOR_RE = re.compile("([0-9a-zA-Z_]*)#([0-9a-zA-Z_]+)")
    CLASS_SELECTOR_RE = re.compile(r"([0-9a-zA-Z_]*)\.([0-9a-zA-Z_]+)")
    PCLASS_SELECTOR_RE = re.compile(":([0-9a-zA-Z-]+)([(]([^)]+)[)])?$")
    ATTR_SELECTOR_RE = re.compile(
        r"([0-9a-zA-Z_]*)[[]([0-9a-zA-Z_]+)(([~*^$|]?[=])\"([0-9a-zA-Z_]+)\")?[\]]")
    ATTR_SELECTOR_TABLE = {
        "=": "matches",
        "~=": "contains_word",
        "|=": "starts_with_word",
        "^=": "starts_with",
        "$=": "ends_with",
        "*=": "contains"
    }

    def __init__(self, entry_string):
        self.name = entry_string
        self.parameters = {}
        self.selector_types = set()
        self.id_str = ""
        self.class_str = ""
        self.pclass_str = ""
        self.pclass_arg = ""
        self.type_str = ""
        self.attr_str = ""
        self.attr_val = ""
        self.attr_type = "any"
        self._parse_entry_string(entry_string)

    def _collect_id(self, id_match_info, pcls_match_info):
        if len(id_match_info.group(1)) > 0:
            self.type_str = id_match_info.group(1)
            if "type" not in self.selector_types:
                self.selector_types.add("type")
        self.id_str = id_match_info.group(2)
        if "id" not in self.selector_types:
            self.selector_types.add("id")
        if pcls_match_info is not None:
            self._collect_pclass(pcls_match_info)

    def _collect_class(self, cls_match_info, pcls_match_info):
        if len(cls_match_info.group(1)) > 0:
            self.type_str = cls_match_info.group(1)
            if "type" not in self.selector_types:
                self.selector_types.add("type")
        self.class_str = cls_match_info.group(2)
        if "class" not in self.selector_types:
            self.selector_types.add("class")
        if pcls_match_info is not None:
            self._collect_pclass(pcls_match_info)

    def _collect_pclass(self, pcls_match_info):
        self.pclass_str = pcls_match_info.group(1)
        if pcls_match_info.group(2) is not None:
            self.pclass_arg = pcls_match_info.group(3)
        if "pclass" not in self.selector_types:
            self.selector_types.add("pclass")

    def _collect_attr(self, attr_match_info, pcls_match_info):
        if len(attr_match_info.group(1)) > 0:
            self.type_str = attr_match_info.group(1)
            if "type" not in self.selector_types:
                self.selector_types.add("type")
        self.attr_str = attr_match_info.group(2)
        if attr_match_info.group(3) is not None:
            # comparison with an attribute value
            self.attr_type = self.ATTR_SELECTOR_TABLE[attr_match_info.group(4)]
            self.attr_val = attr_match_info.group(5)
        else:
            self.attr_type = "any"
        if "attribute" not in self.selector_types:
            self.selector_types.add("attribute")
        if pcls_match_info is not None:
            self.selector_types.add("pclass")

    def _parse_entry_string(self, entry_string):
        if len(entry_string) == 0:
            return
        id_minfo = self.ID_SELECTOR_RE.search(entry_string)
        cls_minfo = self.CLASS_SELECTOR_RE.search(entry_string)
        attr_minfo = self.ATTR_SELECTOR_RE.search(entry_string)
        pcls_minfo = self.PCLASS_SELECTOR_RE.search(entry_string)
        if id_minfo:
            self._collect_id(id_minfo, pcls_minfo)
        elif cls_minfo:
            self._collect_class(cls_minfo, pcls_minfo)
        elif attr_minfo:
            self._collect_attr(attr_minfo, pcls_minfo)
        else:
            if pcls_minfo:
                self._collect_pclass(pcls_minfo)
            self.selector_types.add("type")
            self.type_str = re.sub(self.PCLASS_SELECTOR_RE, "", entry_string)

    def pretty_print(self, indent=0):
        """Print a nicely-formatted summary of the CSS entry."""
        indent_str = " " * indent
        print("{}CSS Style Element {}:".format(indent_str, self.name))
        if "type" in self.selector_types:
            print("{}type name: {}".format(indent_str, self.type_str))
        if "id" in self.selector_types:
            print("{}element ID: {}".format(indent_str, self.id_str))
        if "class" in self.selector_types:
            print("{}class name: {}".format(indent_str, self.class_str))
        if "pclass" in self.selector_types:
            pcls_arg = ""
            if len(self.pclass_arg) > 0:
                pcls_arg = "({})".format(self.pclass_arg)
            print("{}pclass name: {}{}".format(indent_str, self.pclass_str, pcls_arg))
        if "attribute" in self.selector_types:
            attr_name = "any"
            if self.attr_type != "any":
                attr_name = "{} {}".format(self.attr_type, self.attr_val)
            print("{}attribute {} {}".format(indent_str, self.attr_str, attr_name))
        print("{}parameters:".format(indent_str))
        for param in list(self.parameters.keys()):
            print("{}  {}: {}".format(indent_str, param, self.parameters[param]))

    def __getitem__(self, itemname):
        return self.parameters[itemname]

    def __setitem__(self, itemname, value):
        self.parameters[itemname] = value

    def __repr__(self):
        val_list = []
        if "type" in self.selector_types:
            val_list.append("T={}".format(self.type_str))
        if "id" in self.selector_types:
            val_list.append("I={}".format(self.id_str))
        if "class" in self.selector_types:
            val_list.append("C={}".format(self.class_str))
        if "pclass" in self.selector_types:
            pcls_arg = ""
            if len(self.pclass_arg) > 0:
                pcls_arg = "({})".format(self.pclass_arg)
            val_list.append("P={}{}".format(self.pclass_str, pcls_arg))
        if "attribute" in self.selector_types:
            attr_name = "any"
            if self.attr_type != "any":
                attr_name = "{} {}".format(self.attr_type, self.attr_val)
            val_list.append("A:{}".format(attr_name))
        return "<CSSStyleEntry {}>".format(" ".join(val_list))

    def is_equal(self, other):
        """Return true if this style setting matches another."""
        return ((self.type_str == other.type_str) and
                (self.id_str == other.id_str) and
                (self.class_str == other.class_str) and
                (self.attr_str == other.attr_str) and
                (self.attr_type == other.attr_type) and
                (self.attr_val == other.attr_val) and
                (self.pclass_str == other.pclass_str) and
                (self.pclass_arg == other.pclass_arg) and
                (self.parameters == other.parameters))


class ElementPrioritizerTable(object):
    """
    Store CSS style entries in order of precedence, for quickly matching an
    item with the most specific style entry.
    """
    PROPERTY_PRECEDENCE = [
        frozenset(("type", "id", "pclass")),
        frozenset(("type", "class", "pclass")),
        frozenset(("id", "pclass")),
        frozenset(("type", "id")),
        frozenset(("id",)),
        frozenset(("class", "pclass")),
        frozenset(("type", "pclass")),
        frozenset(("type", "class")),
        frozenset(("class",)),
        frozenset(("type", "attribute")),
        frozenset(("type",)),
        frozenset(("attribute",)),
    ]
    ATTR_SELECTOR_PRECEDENCE = [
        "matches", "starts_with_word", "contains_word", "starts_with", "ends_with", "contains",
        "any"
    ]

    def __init__(self):
        #: The table of all known CSS style entries
        self.element_table = {}
        for prop in self.PROPERTY_PRECEDENCE:
            if "attribute" in prop:
                attribute_table = {}
                for attr_sel in self.ATTR_SELECTOR_PRECEDENCE:
                    attribute_table[attr_sel] = []
                self.element_table[prop] = attribute_table
            else:
                self.element_table[prop] = []
        self.reverse_precedence = list(self.PROPERTY_PRECEDENCE)
        self.reverse_precedence.reverse()

    def add_element(self, element):
        """
        Add a new CSS style entry to the table, ordered by priority.

        :param element: A CSS style entry
        :type element: CSSStyleEntry
        """
        # print("Add {} to element table..".format(element))
        for fset in self.PROPERTY_PRECEDENCE:
            # print("Test element {} against {}".format(element, fset))
            if element.selector_types == fset:
                if "attribute" in fset:
                    # attribute comparisons are prioritized separately
                    self.element_table[fset][element.attr_type].append(element)
                else:
                    self.element_table[fset].append(element)
                break

    def _element_matched(self, element, match_props, **kwargs):
        # Compare an item's properties against a CSS style entry, and determine
        #  whether the style applies or not.
        matched = False
        pseudo_class = None
        element_type = None
        element_class = None
        element_id = None
        attribute_dict = None
        if "pseudo_class" in kwargs:
            pseudo_class = kwargs["pseudo_class"]
        if "element_type" in kwargs:
            element_type = kwargs["element_type"]
        if "element_class" in kwargs:
            element_class = kwargs["element_class"]
        if "element_id" in kwargs:
            element_id = kwargs["element_id"]
        if "attribute_dict" in kwargs:
            attribute_dict = kwargs["attribute_dict"]
        for idx, prop_type in enumerate(match_props):
            if prop_type in element.selector_types:
                if idx > 0:
                    # reset matched if 2 or more properties must match
                    if not matched:
                        break
                    else:
                        matched = False
                if ((prop_type == "type") and (element_type is not None) and
                        (element.type_str == element_type)):
                    # print("matched type {}".format(element_type))
                    matched = True
                elif ((prop_type == "class") and (element_class is not None) and
                      (element.class_str == element_class)):
                    # print("matched class {}".format(element_class))
                    matched = True
                elif ((prop_type == "pclass") and (pseudo_class is not None) and
                      (element.pclass_str == pseudo_class)):
                    # print("matched pclass {}".format(pseudo_class))
                    matched = True
                elif ((prop_type == "id") and (element_id is not None) and
                      (element.id_str == element_id)):
                    # print("matched id {}".format(element_id))
                    matched = True
                elif (prop_type == "attribute") and (attribute_dict is not None):
                    # print("matched attribute {}".format(attribute_dict))
                    matched = attribute_match(element, attribute_dict)
        return matched

    def priority_match(self, **kwargs):
        """
        Match the element properties supplied in kwargs, starting from
        highest-precedence to lowest of the elements stored in the element
        table.

        :param kwargs: Supply one or more of the following::

            * pseudo_class: The name of a pseudo class to match
            * element_type: An element type
            * element_class: An element class
            * element_id: An element id
            * attribute_dict: A dict mapping an element's attribute values

        """
        matched_element = None
        matched_props = None
        for prop in self.PROPERTY_PRECEDENCE:
            if "attribute" in prop:
                for attr_type_name in self.ATTR_SELECTOR_PRECEDENCE:
                    for element in self.element_table[prop][attr_type_name]:
                        if self._element_matched(element, list(prop), **kwargs):
                            # print("Matched {} (attr); using parameters {}".format(
                            #       prop, element.parameters))
                            matched_element = element
                            matched_props = prop
                            break
                    if matched_element is not None:
                        break
            else:
                for element in self.element_table[prop]:
                    # print("Test element {} against {}".format(element, prop))
                    if self._element_matched(element, list(prop), **kwargs):
                        # print("Matched {}; using parameters {}".format(prop, element.parameters))
                        matched_element = element
                        matched_props = prop
                        break
            if matched_element is not None:
                break
        return (matched_element, matched_props)

    def compose_style(self, **kwargs):
        """
        Given an item's relevant properties, return the style parameters from
        all CSS style entries that match the properties, with more specific
        style match parameters overriding those in less specific matches.
        """
        specific_match, all_props = self.priority_match(**kwargs)
        style = {}
        if specific_match is None:
            return style
        specific_params = specific_match.parameters
        # print("kwargs {}: specific style: {}".format(kwargs, specific_params))
        if all_props is not None and (len(all_props) > 1):
            for rvs_props in self.reverse_precedence:
                # collect from least to most specific parameters
                if rvs_props < all_props:
                    kwarg_hash = collect_hash_from_props(rvs_props, kwargs)
                    general_match, unused = self.priority_match(**kwarg_hash)
                    if general_match is not None:
                        style.update(general_match.parameters)
                        # print("  kwargs {}: current style: {}".format(kwarg_hash, style))
        style.update(specific_params)
        return style

    def pretty_print(self):
        """Print a nicely-formatted representation of the element table."""
        for prop_set in self.PROPERTY_PRECEDENCE:
            if "attribute" in prop_set:
                for attr_type_name in self.ATTR_SELECTOR_PRECEDENCE:
                    for tel in self.element_table[prop_set][attr_type_name]:
                        print("{}:".format(tel.name))
                        tel.pretty_print(2)
            else:
                for tel in self.element_table[prop_set]:
                    print("{}:".format(tel.name))
                    tel.pretty_print(2)


class CSSStyle(object):
    """Capture and operate on a set of CSS style entries."""
    # order least to most specific for determining which css property or
    # properties override others
    def __init__(self):
        self.element_table = ElementPrioritizerTable()
        self.styles = {}

    def add_element(self, element):
        """
        Add a new CSS style entry.

        :param element: A CSS style entry.
        :type element: CSSStyleEntry
        """
        self.element_table.add_element(element)
        self.styles[element.name] = element

    def get_style(self, **kwargs):
        """
        Collect the style parameters according to specified selector
        information.

        :param kwargs: Supply one or more of the following::

            * pseudo_class: The name of a pseudo class to match
            * element_type: An element type
            * element_class: An element class
            * element_id: An element id
            * attribute_dict: A dict mapping an element's attribute values

        """
        return self.element_table.compose_style(**kwargs)

    def copy(self, other):
        """
        Copy the CSS properties to another instance.

        :param other: Another CSSStyle instance.
        :type other: CSSStyle
        """
        self.element_table = other.element_table
        self.styles.update(other.styles)

    def pretty_print(self):
        """Print a nicely-formatted representation of all CSS style entries."""
        self.element_table.pretty_print()


class CSSStyleParser(CSSStyle):
    """Collect CSS styles from string data."""
    def __init__(self):
        super(CSSStyleParser, self).__init__()
        self.__value_list = []
        self.__param_name = ""
        self.__ident_list = []
        self.__style_block = {}
        self.logger = logging.getLogger("CSSStyleParser")

    def push_value(self, parsestr, loc, toks):
        """
        Append this value to the current value list.

        :param parsestr: The string parsed by PyParsing
        :param loc: The location within the string
        :param toks: The tokens supplied by PyParsing
        """
        self.logger.debug("push_value(<css str>, parsestr={}, loc={}, toks={}):".format(
            parsestr, loc, toks))
        new_value = "".join(toks.asList())
        self.logger.debug("add {} to value list".format(new_value))
        self.__value_list.append(new_value)
        self.logger.debug("self.__value_list is now: {}".format(self.__value_list))

    def push_ident_list(self, parsestr, loc, toks):
        """
        Store the list of identifiers found in front of a CSS block.

        :param parsestr: The string parsed by PyParsing
        :param loc: The location within the string
        :param toks: The tokens supplied by PyParsing
        """
        self.logger.debug("push_ident_list(<css str>, parsestr={}, loc={}, toks={}):".format(
            parsestr, loc, toks))
        self.__ident_list = list(toks.asList())
        self.logger.debug("self.__ident_list is now: {}".format(self.__ident_list))

    def push_param_name(self, parsestr, loc, toks):
        """
        Set the current parameter name.

        :param parsestr: The string parsed by PyParsing
        :param loc: The location within the string
        :param toks: The tokens supplied by PyParsing
        """
        self.logger.debug("push_param_name(<css str>, parsestr={}, loc={}, toks={}):".format(
            parsestr, loc, toks))
        self.__param_name = "".join(toks.asList())
        self.logger.debug("Param name is now: {}".format(self.__param_name))

    def push_parameter(self, parsestr, loc, toks):
        """
        After a parameter has been completely parsed, add it to the style
        block.

        :param parsestr: The string parsed by PyParsing
        :param loc: The location within the string
        :param toks: The tokens supplied by PyParsing
        """
        self.logger.debug("push_parameter(<css str>, parsestr={}, loc={}, toks={}):".format(
            parsestr, loc, toks))
        self.__style_block[self.__param_name] = list(self.__value_list)
        self.logger.debug("__style_block is now {}".format(self.__style_block))
        # clear the name for the next parameter
        self.__param_name = ""
        # clear the value list for the next parameter
        self.__value_list = []

    def push_param_block(self, parsestr, loc, toks):
        """
        After an entire block has been parsed, add its entries to the table.

        :param parsestr: The string parsed by PyParsing
        :param loc: The location within the string
        :param toks: The tokens supplied by PyParsing
        """
        self.logger.debug("push_param_block(<css str>, parsestr={}, loc={}, toks={}):".format(
            parsestr, loc, toks))
        for an_ident in self.__ident_list:
            self.logger.debug("Create new style entry named '{}'".format(an_ident))
            new_style_entry = CSSStyleEntry(an_ident)
            new_style_entry.parameters.update(self.__style_block)
            self.add_element(new_style_entry)
        # clear the identifier list for the next block
        self.__ident_list = []
        # clear the style block for the next block
        self.__style_block = {}

    def missing_or_bad_value(self, substr, loc, expr, err):
        """Log missing or bad values reported by pyparsing."""
        substr_len = min(len(substr) - loc, 10)
        self.logger.debug("missing_or_bad_value(<css str>, " + \
            "loc={}, substr='{}', expr={}, err='{}'):".format(
                loc, substr[loc:loc+substr_len], expr, err))

    def clear(self):
        """Clear the parsed data to prepare to parse another CSS string."""
        self.element_table = ElementPrioritizerTable()
        self.styles = {}
        self.__value_list = []
        self.__param_name = ""
        self.__ident_list = []
        self.__style_block = {}


class CSSStyleGenerator(object):
    """
    Generate a CSSStyle using the get_css() class method on a CSS
    input string.
    """
    css_bnf = None
    css_style_obj = CSSStyleParser()

    @classmethod
    def get_css_style(cls, css_string_data):
        """Generate a new CSSStyle instance that represents CSS string data."""
        cls.css_bnf = bnf(cls.css_style_obj)
        new_css_obj = CSSStyle()
        try:
            cls.css_bnf.parseString(css_string_data)
            # print("CSS parse tree:\n{}".format(astree))
            new_css_obj.copy(cls.css_style_obj)
        finally:
            cls.css_style_obj.clear()
        return new_css_obj


BNF = None


def bnf(css_style_obj):
    """
    * decimal_digit   :: '0' .. '9'
    * sign            :: '-' | '+'
    * integer         :: decimal_digit+
    * float           :: [ sign ] integer '.' [ integer ] [ 'e' | 'E' [ sign ] integer ]
    * lower_case      :: 'a' .. 'z'
    * upper_case      :: 'A' .. 'Z'
    * alpha           :: lower_case | upper_case
    * punctuation     :: '`' | '~' | '!' | '@' | '#' | '$' | '%' | '^' | '&' | '*' | '(' | ')' |
                         '_' | '=' | '+' | ';' | ':' | '\'' | ',' | '<' | '.' | '>' | '/' | '?' |
                         ' ' | '-'
    * string_delim    :: '"' | '\''
    * string          :: string_delim [ alpha | decimal_digit | punctuation ]* string_delim
    * identifier      :: '_' | alpha [ alpha | decimal_digit | '_' ]*
    * attr_selector   :: '[' + identifier [ [ '~' | '*' | '^' | '$' | '|' ] '=' string ] ']'
    * class_or_id     :: ( '#' | '.' ) identifier
    * pseudo_class    :: ':' alpha [ alpha | '-' ]* [ '(' integer | identifier ')' ]
    * selector        :: identifier [ class_or_id | attr_selector ] [ pseudo_class ]
                         [ identifier [ pseudo_class ] ]
    * parameter_name  :: alpha [ alpha | decimal_digit | '_' | '-' ]*
    * lower_hex       :: 'a' .. 'f'
    * upper_hex       :: 'A' .. 'F'
    * hex_digit       :: decimal_digit | lower_hex | upper_hex
    * color           :: '#' hex_digit * 6
    * comment         :: '/' '*' .*? '*' '/'
    * url             :: 'url' '(' string ')'
    * pixel_count     :: integer 'px'
    * percentage      :: integer '%'
    * parameter_val   :: url | color | pixel_count | percentage | parameter_name | float | integer
    * parameter       :: parameter_name ':' [ comment* ]* parameter_val
                         [ parameter_val | comment* ]+ ';'
    * parameter_block :: selector [ ',' selector ]* '{' ( parameter | comment* )+ '}'
    """
    global BNF
    if BNF is None:
        fnumber = Regex(r"[+-]?\d+(:?\.\d*)?(:?[eE][+-]?\d+)?")
        identifier = Word("_"+alphas+nums)
        tilde = Literal("~")
        asterisk = Literal("*")
        caret = Literal("^")
        dsign = Literal("$")
        pipe = Literal("|")
        equal = Literal("=")
        squote = Literal("'")
        sqstring = squote + Regex(r"[^']+") + squote
        dquote = Literal('"')
        dqstring = dquote + Regex(r"[^\"]+") + dquote
        string = sqstring | dqstring
        class_or_id = Word("#"+".", "_"+alphas+nums)
        pclass = Combine(Word(":", "-"+alphas) + Optional(
            '(' + (Word(nums) | identifier) + ')'))
        attr_selector = Combine("[" + identifier + Optional(Optional(
            tilde | asterisk | caret | dsign | pipe) + equal + string) + "]")
        selector = Combine(Word("_"+alphas, "_"+alphas+nums) + Optional(
            attr_selector | class_or_id) + Optional(pclass)) | Combine(
                class_or_id + Optional(pclass)) | attr_selector
        integer = Word(nums)
        parameter_name = Word(alphas, alphas + nums + "_-")
        param_str = Word(alphas, alphas + nums + "_-")
        comment = Regex(r"[/][*].*?[*][/]", flags=re.S)
        lbrack = Literal("{")
        rbrack = Literal("}")
        px_suffix = Literal("px")
        pix_count = Combine(Word(nums) + px_suffix)
        percent = Literal("%")
        percentage = Combine(Word(nums) + percent)
        color = Word("#", hexnums, exact=7)
        urlstr = Keyword("url")
        url = urlstr + '(' + string + ')'
        parameter_val = url | color | pix_count | percentage | param_str | fnumber | integer
        parameter = (parameter_name.setParseAction(
            css_style_obj.push_param_name) + ':' + ZeroOrMore(comment.suppress()) + OneOrMore(
                parameter_val.setParseAction(css_style_obj.push_value) + ZeroOrMore(
                    comment.suppress())) + ';').setParseAction(css_style_obj.push_parameter)
        parameter_block = (delimitedList(selector).setParseAction(
            css_style_obj.push_ident_list) + lbrack + OneOrMore(
                comment.suppress() | parameter) + rbrack).setParseAction(
                    css_style_obj.push_param_block)
        BNF = OneOrMore(comment.suppress() | parameter_block)
    return BNF

