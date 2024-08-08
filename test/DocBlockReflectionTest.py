import unittest

from pystratum_common.DocBlockReflection import DocBlockReflection


class DocBlockReflectionTest(unittest.TestCase):
    """
    Unit test for class DocBlockReflection.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def test01(self):
        """
        Test empty DocBlock.
        """
        doc_block = []
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('', description)

        params = reflection.get_tags('param')
        self.assertEqual([], params)

    # ------------------------------------------------------------------------------------------------------------------
    def test02(self):
        """
        Test DocBlock with description only and minimal whitespace.
        """
        doc_block = ['/** Hello World */']
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('Hello World', description)

        params = reflection.get_tags('param')
        self.assertEqual([], params)

    # ------------------------------------------------------------------------------------------------------------------
    def test03(self):
        """
        Test DocBlock with description only and proper whitespace.
        """
        doc_block = ['/**',
                     '  * Hello World',
                     '  */']
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('Hello World', description)

        params = reflection.get_tags('param')
        self.assertEqual([], params)

    # ------------------------------------------------------------------------------------------------------------------
    def test04(self):
        """
        Test DocBlock with description only and not proper whitespace.
        """
        doc_block = ['  /**',
                     ' * Hello World',
                     '  */  ']
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('Hello World', description)

        params = reflection.get_tags('param')
        self.assertEqual([], params)

    # ------------------------------------------------------------------------------------------------------------------
    def test10(self):
        """
        Test DocBlock with description and parameters and proper whitespace.
        """
        doc_block = ['/**',
                     ' * Hello World',
                     ' *',
                     ' * @param p1 This is param1.',
                     ' * @param p2 This is param2.',
                     ' */']
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('Hello World', description)

        params = reflection.get_tags('param')
        self.assertEqual(['@param p1 This is param1.', '@param p2 This is param2.'], params)

    # ------------------------------------------------------------------------------------------------------------------
    def test11(self):
        """
        Test DocBlock with description and parameters and not proper whitespace.
        """
        doc_block = [' /**',
                     ' * Hello World',
                     '',
                     ' ',
                     '   * @param p1  ',
                     '* @param p2 This is param2. ',
                     ' */ ']
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('Hello World', description)

        params = reflection.get_tags('param')
        self.assertEqual(['@param p1', '@param p2 This is param2.'], params)

    # ------------------------------------------------------------------------------------------------------------------
    def test12(self):
        """
        Test DocBlock with description and parameters and not proper whitespace.
        """
        doc_block = [' /**',
                     ' * Hello World',
                     '   * @param p1  ',
                     '* @param p2 This is param2. ',
                     ' */ ']
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('Hello World', description)

        params = reflection.get_tags('param')
        self.assertEqual(['@param p1', '@param p2 This is param2.'], params)

    # ------------------------------------------------------------------------------------------------------------------
    def test20(self):
        """
        Test DocBlock without description and parameters with proper whitespace.
        """
        doc_block = ['/**',
                     ' * @param p1 This is param1.',
                     ' * @param p2 This is param2.',
                     ' */']
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('', description)

        params = reflection.get_tags('param')
        self.assertEqual(['@param p1 This is param1.', '@param p2 This is param2.'], params)

    # ------------------------------------------------------------------------------------------------------------------
    def test30(self):
        """
        Test DocBlock without description and parameters with proper whitespace.
        """
        doc_block = ['/**',
                     ' * Hello World.',
                     ' * ',
                     ' * @param p1 This is param1.',
                     ' * @param p2 This is param2.',
                     ' *           This is more about param2',
                     ' */']
        reflection = DocBlockReflection(doc_block)

        description = reflection.get_description()
        self.assertEqual('Hello World.', description)

        params = reflection.get_tags('param')
        self.assertEqual(['@param p1 This is param1.', '@param p2 This is param2.\nThis is more about param2'], params)

    # ------------------------------------------------------------------------------------------------------------------
    def testParameterWithDoubleColon(self):
        """
        Test parameters with leading double colon.
        """
        doc_block = """
/**
 * Test for designation type singleton0.
 *
 * @param int :p_count The number of rows selected.
 *
 * @type   singleton0
 * @return int|null
 */
 """
        reflection = DocBlockReflection(doc_block.strip().split("\n"))

        description = reflection.get_description()
        self.assertEqual('Test for designation type singleton0.', description)

        params = reflection.get_tags('param')
        self.assertEqual(['@param int :p_count The number of rows selected.'], params)

        types = reflection.get_tags('type')
        self.assertEqual(['@type   singleton0'], types)

        returns = reflection.get_tags('return')
        self.assertEqual(['@return int|null'], returns)

# ----------------------------------------------------------------------------------------------------------------------
