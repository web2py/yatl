from yatl.helpers import TAG, XML
import unittest


class TestHelpers(unittest.TestCase):
    def test_all_tags(self):
        for x in TAG.__all_tags__:
            self.assertEqual(TAG[x]().xml(), "<%s></%s>" %
                (x, x) if not x[-1] == "/" else "<%s>" % x)

    def test_tags(self):
        DIV = TAG.div
        IMG = TAG['img/']
        self.assertEqual(DIV().xml(), "<div></div>")
        self.assertEqual(IMG().xml(), "<img/>")
        self.assertEqual(DIV(_id="my_id").xml(), "<div id=\"my_id\"></div>")
        self.assertEqual(IMG(_src="crazy").xml(), "<img src=\"crazy\"/>")
        self.assertEqual(
            DIV(_class="my_class", _mytrueattr=True).xml(),
            "<div class=\"my_class\" mytrueattr=\"mytrueattr\"></div>")
        self.assertEqual(
            DIV(_id="my_id", _none=None, _false=False, whitout_underline="serius?").xml(),
            "<div id=\"my_id\"></div>")
        self.assertEqual(
            DIV("<b>xmlscapedthis</b>").xml(), "<div>&lt;b&gt;xmlscapedthis&lt;/b&gt;</div>")
        self.assertEqual(
            DIV(XML("<b>don'txmlscapedthis</b>")).xml(), "<div><b>don'txmlscapedthis</b></div>")

    def test_invalid_atribute_name(self):
        i = [" ", "=", "'", '"', ">", "<", "/"]
        for x in i:
            DIV = TAG.div
            b = "_any%sthings" % x
            attr = {b: "invalid_atribute_name"}
            self.assertRaises(ValueError, DIV("any content", **attr).xml)


if __name__ == '__main__':
    unittest.main()
