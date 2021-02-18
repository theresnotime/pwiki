from datetime import datetime

from pwiki.ns import NS

from .base import QueryTestCase


class TestWikiQuery(QueryTestCase):
    """Tests wiki's query methods.  These are basically smoke tests because the backing modules are more thoroughly tested."""

    def test_categories_on_page(self):
        self.assertListEqual(["Category:Fastily Test"], self.wiki.categories_on_page("User:Fastily/Sandbox/Page/3"))

    def test_category_members(self):
        self.assertCountEqual(["File:FastilyTest.png"], self.wiki.category_members("Category:Fastily Test2", [NS.FILE]))

    def test_category_size(self):
        self.assertEqual(2, self.wiki.category_size("Category:Fastily Test2"))

    def test_contribs(self):
        result = self.wiki.contribs("FastilyClone", True, [NS.FILE])

        self.assertEqual(2, len(result))
        self.assertEqual("File:FCTest1.png", result[0].title)
        self.assertEqual("unit test for Fastily's jwiki", result[1].summary)
        self.assertTrue(result[1].is_page_create)

    def test_duplicate_files(self):
        self.assertListEqual(["File:FastilyTest.svg"], self.wiki.duplicate_files("File:FastilyTestCopy.svg"))

    def test_exists(self):
        self.assertTrue(self.wiki.exists("Main Page"))

    def test_external_links(self):
        self.assertCountEqual(["https://www.google.com", "https://www.facebook.com", "https://github.com"], self.wiki.external_links("User:Fastily/Sandbox/ExternalLink"))

    def test_file_usage(self):
        self.assertCountEqual(["User:Fastily/Sandbox/ImageLinks", "User:Fastily/Sandbox/Page"], self.wiki.file_usage("File:FastilyTest.svg"))

    def test_first_editor_of(self):
        self.assertEqual("Fastily", self.wiki.first_editor_of("User:Fastily/Sandbox/RevisionTest"))

    def test_global_usage(self):
        self.assertTrue(self.wiki.global_usage("File:4thInstarLarvae3500px.jpg"))

    def test_image_info(self):
        self.assertEqual(1, len(result := self.wiki.image_info("File:FastilyTestCircle1.svg")))
        self.assertEqual(512, result[0].width)
        self.assertEqual(502, result[0].height)
        self.assertEqual("0bfe3100d0277c0d42553b9d16db71a89cc67ef7", result[0].sha1)

    def test_images_on_page(self):
        self.assertCountEqual(["File:FastilyTest.svg", "File:FastilyTest.png"], self.wiki.images_on_page("User:Fastily/Sandbox/Page"))

    def test_last_editor_of(self):
        self.assertEqual("FSock", self.wiki.last_editor_of("User:Fastily/Sandbox/RevisionTest"))

    def test_links_on_page(self):
        self.assertListEqual(["User:Fastily/Sandbox/Link/1"], self.wiki.links_on_page("User:Fastily/Sandbox/Link/2"))
        self.assertFalse(self.wiki.links_on_page("User:Fastily/Sandbox/Link/3", NS.MAIN))

    def test_list_duplicate_files(self):
        pass  # not a sane test, already tested in gquery tests.

    def test_list_user_rights(self):
        self.assertFalse(self.wiki.list_user_rights())
        self.assertIn("user", self.wiki.list_user_rights("FastilyClone"))

    def test_logs(self):
        result = self.wiki.logs("File:FastilyTestCircle2.svg", older_first=True)

        self.assertEqual(1, len(result))
        self.assertEqual("upload", result[0].type)
        self.assertEqual("upload", result[0].action)
        self.assertEqual("unit test for wiki\n\n[[Category:Fastily Test3]]", result[0].summary)
        self.assertEqual(datetime.fromisoformat("2016-03-21T02:13:15+00:00"), result[0].timestamp)

    def test_normalize_title(self):
        self.assertEqual("Wikipedia:An", self.wiki.normalize_title("wp:an"))

    def test_page_text(self):
        self.assertEqual("[[Category:Fastily Test]]", self.wiki.page_text("User:Fastily/Sandbox/Page/3"))

    def test_prefix_index(self):
        self.assertListEqual(["User:FastilyClone/Page/1"], self.wiki.prefix_index(NS.USER, "FastilyClone/"))

    def test_random(self):
        self.assertTrue(self.wiki.random())
        self.assertTrue(self.wiki.random([NS.USER]).startswith("User:"))

    def test_resolve_redirect(self):
        self.assertEqual("User:Fastily/Sandbox/RedirectTarget", self.wiki.resolve_redirect("User:Fastily/Sandbox/Redirect2"))

    def test_revisions(self):
        # newer first
        result = self.wiki.revisions("User:Fastily/Sandbox/RevisionTest", include_text=True)
        self.assertEqual(3, len(result))
        self.assertEqual("foo", result[1].text)
        self.assertEqual("a", result[2].summary)
        self.assertEqual(datetime.fromisoformat("2021-02-09T04:33:26+00:00"), result[0].timestamp)

        # older first
        result = self.wiki.revisions("User:Fastily/Sandbox/RevisionTest", True, include_text=False)
        self.assertEqual("c", result[2].summary)
        self.assertIsNone(result[0].text)

    def test_search(self):
        self.assertTrue(result := self.wiki.search("Fastily", [NS.USER_TALK]))
        self.assertTrue(result[0].startswith("User talk:"))

    def test_templates_on_page(self):
        self.assertCountEqual(["User:Fastily/Sandbox/T/1", "Template:FastilyTest"], self.wiki.templates_on_page("User:Fastily/Sandbox/T"))

    def test_uploadable_filetypes(self):
        self.assertTrue(self.wiki.uploadable_filetypes())

    def test_user_uploads(self):
        self.assertCountEqual(["File:FCTest2.svg", "File:FCTest1.png"], self.wiki.user_uploads("FastilyClone"))

    def test_whoami(self):
        self.assertTrue(self.wiki.whoami())
