import unittest
from pathlib import Path

from pharmacy_app import create_app
from pharmacy_app.db import get_connection
from pharmacy_app.service import ValidationError, add_medicine, create_sale, daily_summary, get_short_list


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.db_path = Path("/tmp/lakshy_medical_test.db")
        if self.db_path.exists():
            self.db_path.unlink()
        self.app = create_app({"TESTING": True, "DB_PATH": self.db_path})

    def test_low_stock_short_list(self):
        with self.app.app_context():
            add_medicine(
                {
                    "name": "Paracetamol",
                    "batch_no": "B1",
                    "mfg_date": "2026-01-01",
                    "exp_date": "2027-01-01",
                    "quantity": 3,
                    "rate": 2,
                }
            )
            short = get_short_list()
            self.assertEqual(len(short), 1)

    def test_sale_updates_stock_and_summary(self):
        with self.app.app_context():
            med_id = add_medicine(
                {
                    "name": "Aspirin",
                    "batch_no": "B2",
                    "mfg_date": "2026-01-01",
                    "exp_date": "2027-01-01",
                    "quantity": 20,
                    "rate": 5,
                }
            )
            create_sale(medicine_id=med_id, strips_sold=2, tablets_sold=1, payment_mode="cash")
            conn = get_connection()
            qty = conn.execute("SELECT quantity FROM medicines WHERE id=?", (med_id,)).fetchone()["quantity"]
            self.assertEqual(qty, 17)
            totals, _ = daily_summary()
            self.assertEqual(totals["medicines_sold"], 3)
            self.assertEqual(totals["cash_total"], 15)

    def test_invalid_sale_quantity_raises(self):
        with self.app.app_context():
            med_id = add_medicine(
                {
                    "name": "Ibuprofen",
                    "batch_no": "B3",
                    "mfg_date": "2026-01-01",
                    "exp_date": "2027-01-01",
                    "quantity": 1,
                    "rate": 10,
                }
            )
            with self.assertRaises(ValidationError):
                create_sale(medicine_id=med_id, strips_sold=2, tablets_sold=0, payment_mode="cash")

    def test_tenant_summary_isolation(self):
        with self.app.app_context():
            conn = get_connection()
            second_tenant_id = conn.execute(
                "INSERT INTO tenants (slug, name) VALUES (?, ?)", ("b2", "Branch 2")
            ).lastrowid
            conn.commit()

            med_1 = add_medicine(
                {
                    "name": "Tenant1Med",
                    "batch_no": "T1",
                    "mfg_date": "2026-01-01",
                    "exp_date": "2027-01-01",
                    "quantity": 10,
                    "rate": 10,
                },
                tenant_id=1,
            )
            med_2 = add_medicine(
                {
                    "name": "Tenant2Med",
                    "batch_no": "T2",
                    "mfg_date": "2026-01-01",
                    "exp_date": "2027-01-01",
                    "quantity": 10,
                    "rate": 10,
                },
                tenant_id=second_tenant_id,
            )
            create_sale(medicine_id=med_1, strips_sold=1, tablets_sold=0, payment_mode="cash", tenant_id=1)
            create_sale(
                medicine_id=med_2,
                strips_sold=2,
                tablets_sold=0,
                payment_mode="online",
                tenant_id=second_tenant_id,
            )

            totals_1, _ = daily_summary(tenant_id=1)
            totals_2, _ = daily_summary(tenant_id=second_tenant_id)
            self.assertEqual(totals_1["medicines_sold"], 1)
            self.assertEqual(totals_2["medicines_sold"], 2)


if __name__ == "__main__":
    unittest.main()
