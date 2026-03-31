import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash

from pharmacy_app import create_app
from pharmacy_app.db import get_connection


class ApiTests(unittest.TestCase):
    def setUp(self):
        db_path = Path("/tmp/lakshy_medical_api_test.db")
        if db_path.exists():
            db_path.unlink()
        self.app = create_app({"TESTING": True, "DB_PATH": db_path, "DEFAULT_OWNER_PASSWORD": "owner123"})
        self.client = self.app.test_client()

    def _login_token(self, username="owner", password="owner123", tenant_slug="default"):
        response = self.client.post(
            "/api/login", json={"username": username, "password": password, "tenant_slug": tenant_slug}
        )
        self.assertEqual(response.status_code, 200)
        return response.get_json()["access_token"]

    def test_api_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

    def test_add_medicine_and_summary(self):
        token = self._login_token()
        headers = {"Authorization": f"Bearer {token}"}

        add = self.client.post(
            "/api/medicines",
            headers=headers,
            json={
                "name": "Cetirizine",
                "batch_no": "C1",
                "mfg_date": "2026-01-01",
                "exp_date": "2027-01-01",
                "quantity": 10,
                "rate": 7,
            },
        )
        self.assertEqual(add.status_code, 201)
        med_id = add.get_json()["id"]

        sale = self.client.post(
            "/api/sales",
            headers=headers,
            json={"medicine_id": med_id, "strips_sold": 1, "tablets_sold": 0, "payment_mode": "online"},
        )
        self.assertEqual(sale.status_code, 201)

        summary = self.client.get("/api/summary/daily", headers=headers)
        body = summary.get_json()
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(body["totals"]["online_total"], 7.0)

    def test_tenant_isolation(self):
        with self.app.app_context():
            conn = get_connection()
            tenant_id = conn.execute("INSERT INTO tenants (slug, name) VALUES (?, ?)", ("branch-2", "Branch 2")).lastrowid
            conn.execute(
                "INSERT INTO users (tenant_id, username, password_hash, role) VALUES (?, ?, ?, ?)",
                (tenant_id, "branch_owner", generate_password_hash("branch123"), "owner"),
            )
            conn.commit()

        owner_token = self._login_token()
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        self.client.post(
            "/api/medicines",
            headers=owner_headers,
            json={
                "name": "TenantOneMed",
                "batch_no": "T1",
                "mfg_date": "2026-01-01",
                "exp_date": "2027-01-01",
                "quantity": 5,
                "rate": 2,
            },
        )

        branch_token = self._login_token(username="branch_owner", password="branch123", tenant_slug="branch-2")
        branch_headers = {"Authorization": f"Bearer {branch_token}"}
        result = self.client.get("/api/medicines?q=TenantOneMed", headers=branch_headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()["count"], 0)


if __name__ == "__main__":
    unittest.main()
