#!/usr/bin/env python
"""
Author: Ron Lockwood-Childs

Licensed under LGPL v2.1 (see file COPYING for details)

Unit test the pygame_maker.support.css_to_style module.
"""

import unittest
import logging
from pyparsing import ParseException
from pygame_maker.support.css_to_style import CSSStyleGenerator, CSSStyleEntry

CSSLOGGER = logging.getLogger("CSSStyleParser")
CSSHANDLER = logging.StreamHandler()
CSSFORMATTER = logging.Formatter("%(levelname)s: %(message)s")
CSSHANDLER.setFormatter(CSSFORMATTER)
CSSLOGGER.addHandler(CSSHANDLER)
CSSLOGGER.setLevel(logging.INFO)

def get_test_style():
    """Produce a CSSStyle for unit tests."""
    style_test = CSSStyleGenerator.get_css_style("""/* one identifier from each precedence entry */
a {
    color: blue;
    border: gray;
}
a.foo {
    text-align: center;
    border: blue;
}
a.foo:hover {
    border: green;
}
a:hover {
    border: brown;
}
a#bar {
    vertical-align: middle;
    border: red;
}
a#bar:hover {
    border: orange;
}
a[target] {
    border: black;
}
a[target="_blank"] {
    border: pink;
}
[target] {
    padding: 10%;
    border: peach;
}
.foo {
    width: 50%;
    border: turquoise;
}
.foo:hover {
    border: teal;
}
#bar {
    height: 100;
    border: puce;
}
#bar:hover {
    border: white;
}
""")
    return style_test


class TestCSSStyles(unittest.TestCase):
    """Unit tests for the css_to_style module."""

    def test_005valid_types(self):
        """Test valid CSS style type selectors."""
        test_data_t1 = CSSStyleEntry("p")
        test_data_t1.parameters.update({"text-color": ["blue"]})
        valid_type1 = CSSStyleGenerator.get_css_style("p { text-color: blue; }")
        self.assertTrue(test_data_t1.is_equal(valid_type1.styles["p"]))
        test_data_t2 = CSSStyleEntry("_type_with_underscores")
        test_data_t2.parameters.update({"background-color": ["green"]})
        valid_type2 = CSSStyleGenerator.get_css_style(
            "_type_with_underscores { background-color: green; }")
        self.assertTrue(test_data_t2.is_equal(valid_type2.styles["_type_with_underscores"]))
        test_data_t3 = CSSStyleEntry("n4096")
        test_data_t3.parameters.update({"border-color": ["cyan"]})
        valid_type3 = CSSStyleGenerator.get_css_style("n4096 { border-color: cyan; }")
        self.assertTrue(test_data_t3.is_equal(valid_type3.styles["n4096"]))
        # verify that previous get_css_style() data didn't get copied in
        self.assertEqual(len(list(valid_type3.styles.keys())), 1)
        valid_type3.pretty_print()

    def test_010valid_classes(self):
        """Test valid CSS style class selectors."""
        test_data_c1 = CSSStyleEntry("._baz1")
        test_data_c1.parameters.update({"background-color": ["blue"]})
        valid_class1 = CSSStyleGenerator.get_css_style("._baz1 { background-color: blue; }")
        self.assertTrue(test_data_c1.is_equal(valid_class1.styles["._baz1"]))
        test_data_c2 = CSSStyleEntry("td.foo")
        test_data_c2.parameters.update({"text-align": ["center"]})
        valid_class2 = CSSStyleGenerator.get_css_style("td.foo { text-align: center; }")
        self.assertTrue(test_data_c2.is_equal(valid_class2.styles["td.foo"]))

    def test_015valid_ids(self):
        """Test valid CSS style id selectors."""
        test_data_i1 = CSSStyleEntry("#_obj_test1")
        test_data_i1.parameters.update({"background-color": ["black"]})
        valid_id1 = CSSStyleGenerator.get_css_style("#_obj_test1 { background-color: black; }")
        self.assertTrue(test_data_i1.is_equal(valid_id1.styles["#_obj_test1"]))
        test_data_i2 = CSSStyleEntry("CollideableObjectType#obj_solid1")
        test_data_i2.parameters.update({"background-color": ["white"]})
        valid_id2 = CSSStyleGenerator.get_css_style(
            "CollideableObjectType#obj_solid1 { background-color: white; }")
        self.assertTrue(test_data_i2.is_equal(valid_id2.styles["CollideableObjectType#obj_solid1"]))

    def test_020valid_attr_selectors(self):
        """Test valid CSS style attribute selectors."""
        test_data_a1 = CSSStyleEntry("a[target]")
        test_data_a1.parameters.update({"background-color": ["orange"]})
        valid_attr1 = CSSStyleGenerator.get_css_style("a[target] { background-color: orange; }")
        self.assertTrue(test_data_a1.is_equal(valid_attr1.styles["a[target]"]))
        test_data_a2 = CSSStyleEntry("a[target=\"_blank\"]")
        test_data_a2.parameters.update({"background-color": ["peach"]})
        valid_attr2 = CSSStyleGenerator.get_css_style(
            "a[target=\"_blank\"] { background-color: peach; }")
        self.assertTrue(test_data_a2.is_equal(valid_attr2.styles["a[target=\"_blank\"]"]))
        test_data_a3 = CSSStyleEntry("input[value~=\"your\"]")
        test_data_a3.parameters.update({"border-color": ["red"]})
        valid_attr3 = CSSStyleGenerator.get_css_style(
            "input[value~=\"your\"] { border-color: red; }")
        self.assertTrue(test_data_a3.is_equal(valid_attr3.styles["input[value~=\"your\"]"]))
        test_data_a4 = CSSStyleEntry("input[value|=\"test\"]")
        test_data_a4.parameters.update({"border-color": ["black"]})
        valid_attr4 = CSSStyleGenerator.get_css_style(
            "input[value|=\"test\"] { border-color: black; }")
        self.assertTrue(test_data_a4.is_equal(valid_attr4.styles["input[value|=\"test\"]"]))
        test_data_a5 = CSSStyleEntry("input[value^=\"pas\"]")
        test_data_a5.parameters.update({"border-color": ["green"]})
        valid_attr5 = CSSStyleGenerator.get_css_style(
            "input[value^=\"pas\"] { border-color: green; }")
        self.assertTrue(test_data_a5.is_equal(valid_attr5.styles["input[value^=\"pas\"]"]))
        test_data_a6 = CSSStyleEntry("input[value$=\"day\"]")
        test_data_a6.parameters.update({"border-color": ["blue"]})
        valid_attr6 = CSSStyleGenerator.get_css_style(
            "input[value$=\"day\"] { border-color: blue; }")
        self.assertTrue(test_data_a6.is_equal(valid_attr6.styles["input[value$=\"day\"]"]))
        test_data_a7 = CSSStyleEntry("input[value*=\"pub\"]")
        test_data_a7.parameters.update({"border-color": ["teal"]})
        valid_attr7 = CSSStyleGenerator.get_css_style(
            "input[value*=\"pub\"] { border-color: teal; }")
        self.assertTrue(test_data_a7.is_equal(valid_attr7.styles["input[value*=\"pub\"]"]))
        valid_attr7.pretty_print()

    def test_025invalid_selectors(self):
        """
        Test that invalid CSS style selector strings result in the expected
        parse exceptions.
        """
        with self.assertRaises(ParseException):
            CSSStyleGenerator.get_css_style("foo!bar { border: none; }")
        with self.assertRaises(ParseException):
            CSSStyleGenerator.get_css_style("foo.bar.baz { border: none; }")
        with self.assertRaises(ParseException):
            CSSStyleGenerator.get_css_style("foo#bar#baz { border: none; }")
        with self.assertRaises(ParseException):
            CSSStyleGenerator.get_css_style("foo[bar=baz] { border: none; }")
        with self.assertRaises(ParseException):
            CSSStyleGenerator.get_css_style("foo[bar!=\"baz\"] { border: none; }")
        with self.assertRaises(ParseException):
            CSSStyleGenerator.get_css_style("foo:bar(\"nope\") { border: none; }")

    def test_030valid_data_types(self):
        """Test that valid parameter values get parsed correctly."""
        test_data = CSSStyleEntry("ImageButton")
        test_params = {
            "background-color": ["#FF00FF"],
            "tooltip-delay": ["1.0"],
            "border-width": ["1px"],
            "width": ["40%"],
            "background-image": ["url(\"button.png\")"],
            "background-repeat": ["no-repeat"]
        }
        test_data.parameters.update(test_params)
        valid_data = CSSStyleGenerator.get_css_style("""ImageButton {
    background-color: #FF00FF;
    tooltip-delay: 1.0;
    border-width: 1px;
    width: 40%;
    background-image: url("button.png");
    background-repeat: no-repeat;
}
""")
        self.assertTrue(test_data.is_equal(valid_data.styles["ImageButton"]))
        valid_data.pretty_print()

    def test_035multiple_data_entries(self):
        """
        Test that parameters that can receive multiple values receive them
        correctly.
        """
        test_data = CSSStyleEntry("Table")
        test_data.parameters.update({"border": ["1px", "solid", "black"]})
        valid_data_entries = CSSStyleGenerator.get_css_style("Table { border: 1px solid black; }")
        self.assertTrue(test_data.is_equal(valid_data_entries.styles["Table"]))
        valid_data_entries.pretty_print()

    def test_040valid_pseudo_classes(self):
        """Test that valid pseudo-class selectors are parsed correctly."""
        test_data_p1 = CSSStyleEntry("td:hover")
        test_data_p1.parameters.update({"background-color": ["blue"]})
        valid_pseudo_class1 = CSSStyleGenerator.get_css_style(
            "td:hover { background-color: blue; }")
        self.assertTrue(test_data_p1.is_equal(valid_pseudo_class1.styles["td:hover"]))
        test_data_p2 = CSSStyleEntry("p:lang(it)")
        test_data_p2.parameters.update({"width": ["100%"]})
        valid_pseudo_class2 = CSSStyleGenerator.get_css_style("p:lang(it) { width: 100%; }")
        self.assertTrue(test_data_p2.is_equal(valid_pseudo_class2.styles["p:lang(it)"]))
        test_data_p3 = CSSStyleEntry("p:nth-child(1)")
        test_data_p3.parameters.update({"width": ["50%"]})
        valid_pseudo_class3 = CSSStyleGenerator.get_css_style("p:nth-child(1) { width: 50%; }")
        self.assertTrue(test_data_p3.is_equal(valid_pseudo_class3.styles["p:nth-child(1)"]))
        test_data_p4 = CSSStyleEntry(".data_cell:hover")
        test_data_p4.parameters.update({"background-color": ["gray"]})
        valid_pseudo_class4 = CSSStyleGenerator.get_css_style(
            ".data_cell:hover { background-color: gray; }")
        valid_pseudo_class4.pretty_print()
        self.assertTrue(test_data_p4.is_equal(valid_pseudo_class4.styles[".data_cell:hover"]))

    def test_045comments(self):
        """Test that comments are ignored at any location."""
        test_data = CSSStyleEntry("ImageButton")
        test_params = {
            "background-color": ["#FF00FF"],
            "tooltip-delay": ["1.0"],
            "border-width": ["1px"],
            "width": ["40%"],
            "background-image": ["url(\"button.png\")"],
            "background-repeat": ["no-repeat"]
        }
        test_data.parameters.update(test_params)
        valid_data = CSSStyleGenerator.get_css_style("""/* First line comment */
ImageButton { /* comment before any attributes */
    background-color: #FF00FF /* comment after a value */;
    tooltip-delay: /* comment before a value */ 1.0;
    border-width: 1px; /* comment between attributes */
    width: 40%;
/* comment with * / that aren't adjacent */
    background-image: url("button.png");
    background-repeat: no-repeat;
    /* comment after all attributes */
}
/* This is a
 * multi-line
 * comment
 */
/* last line comment */
""")
        self.assertTrue(test_data.is_equal(valid_data.styles["ImageButton"]))

    def test_050get_style(self):
        """
        Test that get_style() finds the most specific matching CSS style entry.
        """
        style_test = CSSStyleGenerator.get_css_style(
            """/* one identifier from each precedence entry */
a { border: gray; }
a.foo { border: blue; }
a.foo:hover { border: green; }
a:hover { border: brown; }
a#bar { border: red; }
a#bar:hover { border: orange; }
a[target] { border: black; }
a[target="_blank"] { border: pink; }
[target] { border: peach; }
.foo { border: turquoise; }
.foo:hover { border: teal; }
#bar { border: puce; }
#bar:hover { border: white; }
""")
        style_test.element_table.pretty_print()
        match_entry = {
            "element_type": "a",
            "element_class": "foo",
            "element_id": "bar",
            "attribute_dict": {"target": "_blank"},
            "pseudo_class": "hover"
        }
        expected_style = {"border": ["orange"]}
        returned_style = style_test.get_style(**match_entry)
        self.assertEqual(expected_style, returned_style)

    def test_055priority_test(self):
        """
        Test that get_style() returns parameters from all matching CSS style
        entries, with more-specific match parameters overriding less-specific
        matches.
        """
        style_test = get_test_style()
        check_style = style_test.get_style(element_type="a")
        self.assertEqual({"border": ["gray"], "color": ["blue"]}, check_style)
        check_style = style_test.get_style(element_class="foo")
        self.assertEqual({"border": ["turquoise"], "width": ["50%"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_class="foo")
        self.assertEqual({"border": ["blue"], "color": ["blue"],
                          "width": ["50%"], "text-align":["center"]}, check_style)
        check_style = style_test.get_style(element_class="foo", pseudo_class="hover")
        self.assertEqual({"border": ["teal"], "width": ["50%"]}, check_style)
        check_style = style_test.get_style(element_type="a", pseudo_class="hover")
        self.assertEqual({"border": ["brown"], "color": ["blue"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_class="foo",
                                           pseudo_class="hover")
        self.assertEqual({"border": ["green"], "color": ["blue"],
                          "width": ["50%"], "text-align":["center"]}, check_style)
        check_style = style_test.get_style(element_id="bar")
        self.assertEqual({"border": ["puce"], "height": ["100"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_id="bar")
        self.assertEqual({"border": ["red"], "color": ["blue"], "height": ["100"],
                          "vertical-align": ["middle"]}, check_style)
        check_style = style_test.get_style(element_id="bar", pseudo_class="hover")
        self.assertEqual({"border": ["white"], "height": ["100"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_id="bar", pseudo_class="hover")
        self.assertEqual({"border": ["orange"], "color": ["blue"], "height": ["100"],
                          "vertical-align": ["middle"]}, check_style)
        check_style = style_test.get_style(attribute_dict={"target": ""})
        self.assertEqual({"border": ["peach"], "padding": ["10%"]}, check_style)
        check_style = style_test.get_style(element_type="a", attribute_dict={"target": ""})
        self.assertEqual({"border": ["black"], "color": ["blue"], "padding": ["10%"]}, check_style)
        check_style = style_test.get_style(element_type="a", attribute_dict={"target": "_blank"})
        self.assertEqual({"border": ["pink"], "color": ["blue"], "padding": ["10%"]}, check_style)

    def test_056mismatched_styles(self):
        """Test that CSS style matching doesn't get false positives."""
        style_test = get_test_style()
        check_style = style_test.get_style(element_type="b")
        self.assertEqual(len(check_style), 0)
        check_style = style_test.get_style(element_class="bar")
        self.assertEqual(len(check_style), 0)
        check_style = style_test.get_style(element_type="b", element_class="foo")
        self.assertEqual({"border": ["turquoise"], "width": ["50%"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_class="bar")
        self.assertEqual({"border": ["gray"], "color": ["blue"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_class="bar",
                                           pseudo_class="link")
        self.assertEqual({"border": ["gray"], "color": ["blue"]}, check_style)
        check_style = style_test.get_style(element_class="foo", element_id="baz")
        self.assertEqual({"border": ["turquoise"], "width": ["50%"]}, check_style)
        check_style = style_test.get_style(element_class="foo", pseudo_class="link")
        self.assertEqual({"border": ["turquoise"], "width": ["50%"]}, check_style)
        check_style = style_test.get_style(element_type="b", element_class="foo",
                                           pseudo_class="hover")
        self.assertEqual({"border": ["teal"], "width": ["50%"]}, check_style)
        check_style = style_test.get_style(element_type="b", element_class="foo",
                                           pseudo_class="link")
        self.assertEqual({"border": ["turquoise"], "width": ["50%"]}, check_style)
        check_style = style_test.get_style(element_type="a", pseudo_class="link")
        self.assertEqual({"border": ["gray"], "color": ["blue"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_class="foo",
                                           pseudo_class="link")
        self.assertEqual({"border": ["blue"], "color": ["blue"], "width": ["50%"],
                          "text-align":["center"]}, check_style)
        check_style = style_test.get_style(element_id="baz")
        self.assertEqual(len(check_style), 0)
        check_style = style_test.get_style(element_type="a", element_id="baz")
        self.assertEqual({"border": ["gray"], "color": ["blue"]}, check_style)
        check_style = style_test.get_style(element_type="b", element_id="bar")
        self.assertEqual({"border": ["puce"], "height": ["100"]}, check_style)
        check_style = style_test.get_style(element_id="bar", pseudo_class="link")
        self.assertEqual({"border": ["puce"], "height": ["100"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_id="bar", pseudo_class="link")
        self.assertEqual({"border": ["red"], "color": ["blue"], "height": ["100"],
                          "vertical-align": ["middle"]}, check_style)
        check_style = style_test.get_style(element_type="b", element_id="bar", pseudo_class="link")
        self.assertEqual({"border": ["puce"], "height": ["100"]}, check_style)
        check_style = style_test.get_style(element_type="a", element_id="baz", pseudo_class="hover")
        self.assertEqual({"border": ["brown"], "color": ["blue"]}, check_style)
        check_style = style_test.get_style(element_type="b", element_id="bar", pseudo_class="hover")
        self.assertEqual({"border": ["white"], "height": ["100"]}, check_style)
        check_style = style_test.get_style(attribute_dict={"href": ""})
        self.assertEqual(len(check_style), 0)
        check_style = style_test.get_style(attribute_dict={"target": "foo"})
        self.assertEqual({"border": ["peach"], "padding": ["10%"]}, check_style)
        check_style = style_test.get_style(element_type="b", attribute_dict={"target": ""})
        self.assertEqual({"border": ["peach"], "padding": ["10%"]}, check_style)
        check_style = style_test.get_style(element_type="a", attribute_dict={"href": ""})
        self.assertEqual({"border": ["gray"], "color": ["blue"]}, check_style)
        check_style = style_test.get_style(element_type="a", attribute_dict={"target": "foo"})
        self.assertEqual({"border": ["black"], "color": ["blue"], "padding": ["10%"]}, check_style)


unittest.main()
