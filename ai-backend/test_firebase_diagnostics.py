import unittest
from unittest.mock import Mock
from firebase_diagnostics import check_storage_permissions, describe_error, FirebaseOperationError, REQUIRED_STORAGE_PERMISSIONS

class DiagnosticTests(unittest.TestCase):
    def test_storage_requires_create_read_and_metadata_update(self):
        bucket=Mock();bucket.test_iam_permissions.return_value=["storage.objects.get"]
        with self.assertRaisesRegex(PermissionError,"storage.objects.create"):
            check_storage_permissions(bucket)
        bucket.test_iam_permissions.return_value=list(REQUIRED_STORAGE_PERMISSIONS)
        check_storage_permissions(bucket)
        bucket.test_iam_permissions.assert_called_with(list(REQUIRED_STORAGE_PERMISSIONS),timeout=8,retry=None)
    def test_billing_error_has_specific_guidance(self):
        error=RuntimeError("403 UserProjectAccountProblem: billing account is absent")
        self.assertIn("Blaze",describe_error(error))
    def test_sensitive_query_and_bearer_are_redacted(self):
        text=describe_error(RuntimeError("POST https://example.invalid/o?token=secret123 Authorization: Bearer secret456"))
        self.assertNotIn("secret123",text);self.assertNotIn("secret456",text)
    def test_service_account_errors_do_not_suggest_public_rules(self):
        text=describe_error(PermissionError("storage.objects.create denied"))
        self.assertIn("IAM",text);self.assertIn("do not open public rules",text)
    def test_operation_remains_visible(self):
        text=str(FirebaseOperationError("Storage evidence upload",PermissionError("403 denied")))
        self.assertIn("Storage evidence upload",text)

if __name__=="__main__":unittest.main()
