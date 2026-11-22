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

    def test_malformed_matching_personal_identifiers_are_denied(self):
        for bad_id in (None, 0, 123, True, " ", "\t\n"):
            with self.subTest(bad_id=bad_id):
                result = authorize(
                    Principal(bad_id),
                    Resource(ResourceKind.PERSONAL, bad_id),
                    Action.READ,
                )
                self.assertFalse(result.allowed)
                self.assertEqual(result.reason, "invalid_identity")

    def test_malformed_organization_identifiers_are_denied(self):
        cases = (
            (Principal(123, {"org-a": frozenset({"admin"})}), "org-a"),
            (Principal("alice", {123: frozenset({"admin"})}), 123),
            (Principal("alice", {"   ": frozenset({"admin"})}), "   "),
        )
        for principal, tenant_id in cases:
            with self.subTest(tenant_id=tenant_id):
                result = authorize(
                    principal,
                    Resource(ResourceKind.ORGANIZATION, tenant_id),
                    Action.MANAGE,
                )
                self.assertFalse(result.allowed)
                self.assertEqual(result.reason, "invalid_identity")

    def test_non_contract_inputs_are_denied_without_exception(self):
        valid_principal = Principal("alice")
        valid_resource = Resource(ResourceKind.PERSONAL, "alice")
        self.assertEqual(
            authorize(None, valid_resource, Action.READ).reason, "invalid_request"
        )
        self.assertEqual(
            authorize(valid_principal, None, Action.READ).reason, "invalid_request"
        )
        self.assertFalse(
            authorize(valid_principal, valid_resource, object()).allowed
        )

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

    def test_roles_are_immutable_snapshot(self):
        roles = {"org-a": {"viewer"}}
        principal = Principal("alice", roles)
        roles["org-a"].add("admin")
        roles["org-b"] = {"admin"}
        self.assertFalse(authorize(principal, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.MANAGE).allowed)
        self.assertFalse(authorize(principal, Resource(ResourceKind.ORGANIZATION, "org-b"), Action.MANAGE).allowed)
        with self.assertRaises(TypeError):
            principal.organization_roles["org-a"] = frozenset({"admin"})

    def test_unknown_role_denied(self):
        p = Principal("alice", {"org-a": frozenset({"superuser"})})
        self.assertFalse(authorize(p, Resource(ResourceKind.ORGANIZATION, "org-a"), Action.READ).allowed)


if __name__ == "__main__":
    unittest.main()

