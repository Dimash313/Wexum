import unittest

from wexum_core.authorization import (
    Action,
    Principal,
    Resource,
    ResourceKind,
    authorize,
)


class AuthorizationTests(unittest.TestCase):
    def test_owner_can_manage_personal_resource(self):
        self.assertTrue(authorize(Principal("alice"), Resource(ResourceKind.PERSONAL, "alice"), Action.MANAGE).allowed)

    def test_cross_user_personal_resource_denied(self):
        self.assertFalse(authorize(Principal("alice"), Resource(ResourceKind.PERSONAL, "bob"), Action.READ).allowed)

    def test_untrusted_or_missing_identity_denied(self):
        self.assertFalse(authorize(Principal(""), Resource(ResourceKind.PERSONAL, ""), Action.READ).allowed)
        self.assertFalse(authorize(Principal("alice"), Resource(ResourceKind.PERSONAL, "alice"), "read").allowed)

    def test_unknown_resource_kind_denied(self):
        self.assertFalse(authorize(Principal("alice"), Resource("unknown", "alice"), Action.READ).allowed)

    def test_org_viewer_is_read_only(self):
        p = Principal("alice", {"org-a": frozenset({"viewer"})})
        self.assertTrue(authorize(p, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.READ).allowed)
        self.assertFalse(authorize(p, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.WRITE).allowed)
        self.assertFalse(authorize(p, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.MANAGE).allowed)

    def test_org_editor_and_admin(self):
        editor = Principal("alice", {"org-a": frozenset({"editor"})})
        admin = Principal("bob", {"org-a": frozenset({"admin"})})
        self.assertTrue(authorize(editor, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.WRITE).allowed)
        self.assertFalse(authorize(editor, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.MANAGE).allowed)
        self.assertTrue(authorize(admin, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.MANAGE).allowed)

    def test_org_cross_tenant_denied(self):
        p = Principal("alice", {"org-a": frozenset({"admin"})})
        self.assertFalse(authorize(p, Resource(ResourceKind.ORGANIZATION, "org-b"), Action.READ).allowed)

    def test_unknown_role_denied(self):
        p = Principal("alice", {"org-a": frozenset({"superuser"})})
        self.assertFalse(authorize(p, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.READ).allowed)


if __name__ == "__main__":
    unittest.main()

