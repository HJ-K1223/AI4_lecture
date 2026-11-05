from io import StringIO
from pathlib import Path
import json
import tempfile
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.exceptions import ValidationError
from django.db import connection, IntegrityError, transaction
from django.utils import timezone
from accounts.models import Member
from board.models import Post, Comment
from moderation.models import BannedTerm
from moderation.services import Masker, add_terms

PASSWORD = "Woodland!73Breeze"


@override_settings(APP_URL_PREFIX="/note-demo", FORCE_SCRIPT_NAME="/note-demo",
                   LOGIN_URL="/note-demo/accounts/login/", STATIC_URL="/note-demo/static/",
                   SESSION_COOKIE_NAME="note_demo_sessionid", CSRF_COOKIE_NAME="note_demo_csrftoken",
                   SESSION_COOKIE_PATH="/note-demo/", CSRF_COOKIE_PATH="/note-demo/")
class MountedSiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.create_user("mount@example.com", PASSWORD, nickname="회원")
        cls.post = Post.objects.create(author=cls.member, title="분리된 게시글", content="본문")

    def tearDown(self):
        from django.urls import set_script_prefix
        set_script_prefix("/")

    def test_login_links_and_anonymous_redirect_stay_in_mount(self):
        response = self.client.get("/accounts/login/", SCRIPT_NAME="/note-demo")
        self.assertContains(response, 'href="/note-demo/accounts/signup/"')
        self.assertNotContains(response, 'href="/accounts/')
        self.assertContains(response, '/note-demo/static/css/site.')
        response = self.client.get("/posts/", SCRIPT_NAME="/note-demo")
        self.assertTrue(response["Location"].startswith("/note-demo/accounts/login/?next="))

    def test_login_cookie_and_logout_are_isolated(self):
        response = self.client.post("/accounts/login/", {"email":"mount@example.com", "password":PASSWORD}, SCRIPT_NAME="/note-demo")
        self.assertEqual(response["Location"], "/note-demo/posts/")
        self.assertEqual(response.cookies["note_demo_sessionid"]["path"], "/note-demo/")
        self.assertNotIn("sessionid", response.cookies)
        response = self.client.post("/accounts/logout/", SCRIPT_NAME="/note-demo")
        self.assertEqual(response["Location"], "/note-demo/accounts/login/")

    def test_login_next_cannot_escape_to_existing_site(self):
        response = self.client.post("/accounts/login/", {"email":"mount@example.com", "password":PASSWORD, "next":"/guestbook/"}, SCRIPT_NAME="/note-demo")
        self.assertEqual(response["Location"], "/note-demo/posts/")

    def test_board_links_and_save_redirect_have_prefix(self):
        self.client.force_login(self.member)
        response = self.client.get(f"/posts/{self.post.pk}/", SCRIPT_NAME="/note-demo")
        self.assertContains(response, f'action="/note-demo/posts/{self.post.pk}/comments/"')
        response = self.client.post("/posts/new/", {"title":"새글", "content":"내용"}, SCRIPT_NAME="/note-demo")
        self.assertTrue(response["Location"].startswith("/note-demo/posts/"))

    def test_wsgi_adapter_handles_both_upstream_path_formats(self):
        from config.mount import MountedApplication
        seen = []
        def downstream(environ, start_response):
            seen.append((environ["SCRIPT_NAME"], environ["PATH_INFO"]))
            return [b"ok"]
        app = MountedApplication(downstream, "/note-demo")
        for path in ["/note-demo/accounts/login/", "/accounts/login/"]:
            self.assertEqual(app({"PATH_INFO":path}, lambda *args: None), [b"ok"])
            self.assertEqual(seen[-1], ("/note-demo", "/accounts/login/"))
        status = []
        app({"PATH_INFO":"/note-demo", "QUERY_STRING":"a=1"}, lambda code, headers: status.append((code,dict(headers))))
        self.assertEqual(status[0][1]["Location"], "/note-demo/?a=1")

class AppTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = Member.objects.create_user("owner@example.com", PASSWORD, nickname="작성자")
        cls.other = Member.objects.create_user("other@example.com", PASSWORD, nickname="다른회원")
        cls.admin = Member.objects.create_user("admin@example.com", PASSWORD, nickname="관리자", role="ADMIN")
        cls.post = Post.objects.create(author=cls.owner, title="원래 제목", content="원래 내용")
    def login_owner(self):
        self.client.force_login(self.owner)
    def test_home_opens_login_for_anonymous(self):
        response = self.client.get("/", follow=True)
        self.assertEqual(response.redirect_chain, [("/accounts/login/", 302)])
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertContains(response, '<button type="submit">로그인</button>', html=True)
        self.assertIn("no-store", response["Cache-Control"])
    def test_login_signup_link_is_below_form(self):
        response = self.client.get("/accounts/login/")
        html = response.content.decode()
        self.assertLess(html.index("</form>"), html.index('href="/accounts/signup/"'))
        self.assertContains(response, "아직 회원이 아니신가요?")
        self.assertEqual(self.client.get("/accounts/signup/").status_code, 200)
    def test_anonymous_board_reads_require_login(self):
        for path in ["/posts/", f"/posts/{self.post.pk}/", "/posts/?page=2"]:
            response = self.client.get(path, follow=True)
            self.assertTemplateUsed(response, "accounts/login.html")
            self.assertEqual(response.redirect_chain[0][1], 302)
            self.assertNotContains(response, self.post.content)
    def test_authenticated_entry_skips_login(self):
        self.login_owner()
        self.assertRedirects(self.client.get("/"), "/posts/")
        for path in ["/accounts/login/", "/accounts/signup/"]:
            self.assertRedirects(self.client.get(path), "/posts/", status_code=303)
    def test_login_returns_to_requested_post_after_failure(self):
        target = f"/posts/{self.post.pk}/"
        response = self.client.post("/accounts/login/", {"email":"owner@example.com", "password":"wrong", "next":target})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, f'name="next" value="{target}"', status_code=400)
        response = self.client.post("/accounts/login/", {"email":"owner@example.com", "password":PASSWORD, "next":target})
        self.assertRedirects(response, target, status_code=303)
    def test_logout_returns_to_login_and_blocks_board(self):
        self.login_owner()
        response = self.client.post("/accounts/logout/")
        self.assertRedirects(response, "/accounts/login/", status_code=303)
        self.assertEqual(self.client.get("/posts/").status_code, 302)
    def test_signup_normalizes_hashes_and_ignores_role(self):
        response = self.client.post("/accounts/signup/", {"email": "New@Example.com ", "nickname": "새회원", "password": PASSWORD, "password_confirm": PASSWORD, "role": "ADMIN"})
        self.assertEqual(response.status_code, 303)
        member = Member.objects.get(email="new@example.com")
        self.assertTrue(member.check_password(PASSWORD))
        self.assertNotEqual(member.password, PASSWORD)
        self.assertEqual(member.role, "USER")
        self.assertNotIn(PASSWORD.encode(), response.content)
    def test_signup_duplicate_case(self):
        response = self.client.post("/accounts/signup/", {"email": "OWNER@example.com", "nickname": "중복", "password": PASSWORD, "password_confirm": PASSWORD})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Member.objects.count(), 3)
    def test_signup_invalid_values(self):
        for data in [{"email":"bad", "nickname":" ", "password":"123", "password_confirm":"456"}, {}]:
            self.assertEqual(self.client.post("/accounts/signup/", data).status_code, 400)
    def test_login_logout_invalidates_session(self):
        response = self.client.post("/accounts/login/", {"email":"OWNER@example.com", "password":PASSWORD})
        self.assertEqual(response.status_code, 303)
        old_key = self.client.cookies["sessionid"].value
        self.assertEqual(self.client.post("/accounts/logout/").status_code, 303)
        self.client.cookies["sessionid"] = old_key
        self.assertEqual(self.client.get("/posts/new/").status_code, 302)
    def test_login_failure_and_external_redirect(self):
        self.assertEqual(self.client.post("/accounts/login/", {"email":"owner@example.com", "password":"bad"}).status_code, 400)
        response = self.client.post("/accounts/login/", {"email":"owner@example.com", "password":PASSWORD, "next":"https://evil.example/"})
        self.assertEqual(response["Location"], "/posts/")
    def test_logout_get_rejected(self):
        self.login_owner()
        self.assertEqual(self.client.get("/accounts/logout/").status_code, 405)
    def test_mock_no_change_or_email(self):
        password = self.owner.password
        with patch("django.core.mail.send_mail") as mail:
            a = self.client.post("/accounts/password-help/", {"email":"owner@example.com"})
            b = self.client.post("/accounts/password-help/", {"email":"absent@example.com"})
            mail.assert_not_called()
        self.assertContains(a, "Mock")
        self.assertContains(b, "Mock")
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.password, password)
    def test_pagination_0_10_11(self):
        self.client.force_login(self.other)
        Post.objects.all().delete()
        self.assertContains(self.client.get("/posts/"), "아직 작성된 글이 없습니다.")
        for i in range(11):
            Post.objects.create(author=self.owner, title=f"제목{i}", content="보이면안되는본문")
            if i == 9:
                self.assertEqual(len(self.client.get("/posts/").context["page"]), 10)
        response = self.client.get("/posts/")
        self.assertEqual(len(response.context["page"]), 10)
        self.assertNotContains(response, "보이면안되는본문")
        self.assertNotContains(response, "작성자")
        self.assertEqual(len(self.client.get("/posts/?page=2").context["page"]), 1)
    def test_invalid_pages(self):
        self.client.force_login(self.other)
        for value in ["0", "-1", "abc", "1.0", "９", "", "9" * 5000]:
            self.assertEqual(self.client.get("/posts/", {"page":value}).status_code, 400)
        self.assertEqual(self.client.get("/posts/?page=99").status_code, 404)
    def test_equal_timestamp_order(self):
        self.client.force_login(self.other)
        other = Post.objects.create(author=self.owner, title="두번째", content="내용")
        Post.objects.all().update(created_at=timezone.now())
        page = self.client.get("/posts/").context["page"]
        self.assertEqual([p.pk for p in page], [other.pk, self.post.pk])
    def test_create_and_edit_uses_authenticated_author(self):
        self.login_owner()
        response = self.client.post("/posts/new/", {"title":"새제목", "content":"새내용", "author_id":self.other.pk})
        self.assertEqual(response.status_code, 303)
        post = Post.objects.get(title="새제목")
        self.assertEqual(post.author_id, self.owner.pk)
        self.assertEqual(self.client.post(f"/posts/{post.pk}/edit/", {"title":"수정", "content":"수정내용"}).status_code, 303)
        post.refresh_from_db()
        self.assertEqual(post.title, "수정")
    def test_other_and_admin_cannot_mutate_post_or_read_original(self):
        for member in [self.other, self.admin]:
            self.client.force_login(member)
            for method, path in [("get",f"/posts/{self.post.pk}/edit/"),("post",f"/posts/{self.post.pk}/edit/"),("post",f"/posts/{self.post.pk}/delete/")]:
                self.assertEqual(getattr(self.client, method)(path).status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
    def test_owner_edit_private_no_store(self):
        self.login_owner()
        response = self.client.get(f"/posts/{self.post.pk}/edit/")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertContains(response, self.post.content)
    def test_post_validation_and_missing_resource(self):
        self.login_owner()
        for data in [{"title":" ", "content":"x"}, {"title":"x", "content":"x"*20001}, {"title":"x"*201,"content":"x"}]:
            self.assertEqual(self.client.post("/posts/new/", data).status_code, 400)
        self.assertEqual(self.client.get("/posts/99999/").status_code, 404)
    def test_comment_create_delete_and_wrong_owner(self):
        self.login_owner()
        self.assertEqual(self.client.post(f"/posts/{self.post.pk}/comments/", {"content":"댓글", "author_id":self.other.pk}).status_code, 303)
        comment = Comment.objects.get()
        self.assertEqual(comment.author_id, self.owner.pk)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f"/comments/{comment.pk}/delete/").status_code, 403)
        self.login_owner()
        self.assertEqual(self.client.post(f"/comments/{comment.pk}/delete/").status_code, 303)
        self.assertFalse(Comment.objects.exists())
    def test_comment_validation_and_missing_post(self):
        self.login_owner()
        for value in [" ", "x"*1001]:
            self.assertEqual(self.client.post(f"/posts/{self.post.pk}/comments/", {"content":value}).status_code, 400)
        self.assertEqual(self.client.post("/posts/99999/comments/", {"content":"댓글"}).status_code, 404)
    def test_comment_pagination(self):
        self.client.force_login(self.other)
        url = f"/posts/{self.post.pk}/"
        self.assertEqual(len(self.client.get(url).context["comments"]), 0)
        for i in range(21):
            Comment.objects.create(post=self.post, author=self.owner, content=f"댓글{i}")
            if i == 19:
                self.assertEqual(len(self.client.get(url).context["comments"]), 20)
        self.assertEqual(len(self.client.get(url).context["comments"]), 20)
        self.assertEqual(len(self.client.get(url+"?comment_page=2").context["comments"]), 1)
        self.assertEqual(self.client.get(url+"?comment_page=-1").status_code, 400)
        self.assertEqual(self.client.get(url+"?comment_page=3").status_code, 404)
    def test_delete_post_cascades(self):
        Comment.objects.create(post=self.post, author=self.other, content="댓글")
        self.login_owner()
        self.assertEqual(self.client.post(f"/posts/{self.post.pk}/delete/").status_code, 303)
        self.assertFalse(Comment.objects.exists())
    def test_mask_all_fields_and_change_rules(self):
        self.client.force_login(self.other)
        self.post.title, self.post.content = "bad 제목", "본문 BAD"
        self.post.save()
        Comment.objects.create(post=self.post, author=self.owner, content="bad 댓글")
        add_terms([{"pattern":"bad"}])
        self.assertContains(self.client.get("/posts/"), "*** 제목")
        response = self.client.get(f"/posts/{self.post.pk}/")
        self.assertContains(response, "본문 ***")
        self.assertContains(response, "*** 댓글")
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "bad 제목")
        BannedTerm.objects.all().delete()
        self.assertContains(self.client.get(f"/posts/{self.post.pk}/"), "본문 BAD")
    def test_admin_guard_and_normalized_duplicate(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/moderation/terms/").status_code, 403)
        self.assertEqual(self.client.post("/moderation/terms/", {"pattern":"bad"}).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post("/moderation/terms/", {"pattern":"ＢＡＤ", "created_by":self.owner.pk}).status_code, 303)
        term = BannedTerm.objects.get()
        self.assertEqual(term.created_by_id, self.admin.pk)
        self.assertEqual(term.pattern, "bad")
        self.assertEqual(self.client.post("/moderation/terms/", {"pattern":"BAD"}).status_code, 400)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(f"/moderation/terms/{term.pk}/delete/").status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(f"/moderation/terms/{term.pk}/delete/").status_code, 303)
    def test_admin_regex_rejected(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post("/moderation/terms/", {"pattern":".*", "match_type":"REGEX"}).status_code, 400)
        self.assertFalse(BannedTerm.objects.exists())
    def test_rule_cap_all_paths(self):
        BannedTerm.objects.bulk_create([BannedTerm(pattern=f"term{i}") for i in range(500)])
        with self.assertRaises(ValidationError):
            add_terms([{"pattern":"overflow"}])
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post("/moderation/terms/", {"pattern":"overflow"}).status_code, 400)
        self.assertEqual(BannedTerm.objects.count(), 500)
    def test_seed_idempotence_and_explicit_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"seed.json"
            path.write_text(json.dumps([{"pattern":"ＢＡＤ","source_note":"test only"}]), encoding="utf-8")
            for _ in range(2):
                call_command("load_banned_terms", str(path), stdout=StringIO())
            self.assertEqual(BannedTerm.objects.count(), 1)
            self.assertIsNone(BannedTerm.objects.get().created_by_id)
            BannedTerm.objects.all().delete()
            self.client.get("/posts/")
            self.assertFalse(BannedTerm.objects.exists())
            path.write_text(json.dumps([{"pattern":"ok"},{"pattern":".*","match_type":"REGEX"}]), encoding="utf-8")
            with self.assertRaises(CommandError):
                call_command("load_banned_terms", str(path), stdout=StringIO())
            self.assertFalse(BannedTerm.objects.exists())
    def test_html_escaped(self):
        self.client.force_login(self.other)
        self.post.title = "<script>alert(1)</script>"
        self.post.content = "<img src=x onerror=alert(1)>"
        self.post.save()
        response = self.client.get(f"/posts/{self.post.pk}/")
        self.assertNotContains(response, "<script>")
        self.assertNotContains(response, "<img")
        self.assertContains(response, "&lt;script&gt;")
    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/accounts/login/", {"email":"owner@example.com","password":PASSWORD}).status_code, 403)
        client.force_login(self.owner)
        self.assertEqual(client.post("/posts/new/", {"title":"x","content":"y"}).status_code, 403)
    def test_anonymous_mutation_redirects(self):
        for path in ["/posts/new/",f"/posts/{self.post.pk}/edit/",f"/posts/{self.post.pk}/delete/", f"/posts/{self.post.pk}/comments/"]:
            self.assertEqual(self.client.post(path, {}).status_code, 302)
    def test_direct_database_cascade(self):
        Comment.objects.create(post=self.post, author=self.other, content="댓글")
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM posts WHERE id=%s", [self.post.pk])
        self.assertFalse(Comment.objects.exists())
    def test_direct_database_set_null(self):
        term = BannedTerm.objects.create(pattern="bad", created_by=self.admin)
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM members WHERE id=%s", [self.admin.pk])
        term.refresh_from_db()
        self.assertIsNone(term.created_by_id)
    def test_direct_member_restrict_and_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM members WHERE id=%s", [self.owner.pk])
        for action in [lambda: Post.objects.create(author=self.owner, title=" ", content="x"),
                       lambda: Post.objects.create(author=self.owner, title="x", content="x"*20001),
                       lambda: BannedTerm.objects.create(pattern=".*", match_type="REGEX"),
                       lambda: Member.objects.create(email="UPPER@EXAMPLE.COM", nickname="x", password="hash"),
                       lambda: Member.objects.filter(pk=self.other.pk).update(role="ROOT")]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                action()
    def test_create_admin_command(self):
        with patch("getpass.getpass", return_value=PASSWORD):
            call_command("create_admin", email="newadmin@example.com", nickname="운영자", stdout=StringIO())
        member = Member.objects.get(email="newadmin@example.com")
        self.assertEqual(member.role, "ADMIN")
        self.assertTrue(member.check_password(PASSWORD))
    def test_production_static_and_https(self):
        self.client.force_login(self.other)
        from django.test import override_settings
        with override_settings(DEBUG=False, SECURE_SSL_REDIRECT=True, SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")):
            self.assertEqual(self.client.get("/posts/").status_code, 301)
            self.assertEqual(self.client.get("/posts/", HTTP_X_FORWARDED_PROTO="https").status_code, 200)
    def test_masking_unicode_overlap_and_false_positives(self):
        self.assertEqual(Masker(["bad","ad","badword"]).mask("BADword!"), "***!")
        self.assertEqual(Masker(["ff"]).mask("aﬀb"), "a***b")
        self.assertEqual(Masker(["가"]).mask("가나다"), "***나다")
        self.assertEqual(Masker(["é"]).mask("e\u0301!"), "***!")
        self.assertEqual(Masker(["ss"]).mask("Straße"), "Stra***e")
        self.assertEqual(Masker(["bad"]).mask("b a d"), "b a d")
        self.assertEqual(Masker(["ass"]).mask("class"), "cl***")
        self.assertEqual(Masker(["bad"]).mask("fine"), "fine")
        self.assertEqual(Masker(["bad"]).mask("badbad"), "******")

