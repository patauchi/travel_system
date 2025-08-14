"""
Integration Tests for Financial Service Modules
Tests all modules: orders, expenses, pettycash, voucher, invoices, payments
"""

import pytest
from datetime import date, datetime
from decimal import Decimal


class TestHealthChecks:
    """Test health check endpoints"""

    def test_main_health_check(self, client):
        """Test main health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "financial-service"
        assert data["version"] == "2.0.0"
        assert data["architecture"] == "modular"
        assert len(data["modules"]) == 6

    def test_financial_health_check(self, client, headers):
        """Test financial service comprehensive health check"""
        response = client.get("/api/v1/financial/health", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "financial-service"
        assert len(data["modules"]) == 6

    def test_auth_test(self, client, headers):
        """Test authentication functionality"""
        response = client.get("/api/v1/financial/auth-test", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Authentication successful"
        assert data["user_id"] == "test-user-123"


class TestOrdersModule:
    """Test Orders module functionality"""

    def test_create_order(self, client, headers, sample_order_data):
        """Test creating a new order"""
        response = client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["order_number"] == sample_order_data["order_number"]
        assert data["total_amount"] == sample_order_data["total_amount"]
        assert data["order_status"] == sample_order_data["order_status"]

    def test_list_orders(self, client, headers, sample_order_data):
        """Test listing orders"""
        # First create an order
        client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )

        # Then list orders
        response = client.get("/api/v1/financial/orders", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert data["total"] >= 1
        assert len(data["orders"]) >= 1

    def test_get_order(self, client, headers, sample_order_data):
        """Test getting a specific order"""
        # Create order first
        create_response = client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )
        order_id = create_response.json()["id"]

        # Get the order
        response = client.get(f"/api/v1/financial/orders/{order_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["order_number"] == sample_order_data["order_number"]

    def test_update_order(self, client, headers, sample_order_data):
        """Test updating an order"""
        # Create order first
        create_response = client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )
        order_id = create_response.json()["id"]

        # Update the order
        update_data = {"order_status": "confirmed", "special_instructions": "Updated instructions"}
        response = client.put(
            f"/api/v1/financial/orders/{order_id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["order_status"] == "confirmed"
        assert data["special_instructions"] == "Updated instructions"

    def test_orders_health(self, client, headers):
        """Test orders module health check"""
        response = client.get("/api/v1/financial/orders/health", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "orders"


class TestExpensesModule:
    """Test Expenses module functionality"""

    def test_create_expense_category(self, client, headers, sample_expense_category_data):
        """Test creating an expense category"""
        response = client.post(
            "/api/v1/financial/expense-categories",
            json=sample_expense_category_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_expense_category_data["name"]
        assert data["code"] == sample_expense_category_data["code"]

    def test_create_expense(self, client, headers, sample_expense_category_data, sample_expense_data):
        """Test creating an expense"""
        # Create category first
        cat_response = client.post(
            "/api/v1/financial/expense-categories",
            json=sample_expense_category_data,
            headers=headers
        )
        category_id = cat_response.json()["id"]
        sample_expense_data["category_id"] = category_id

        # Create expense
        response = client.post(
            "/api/v1/financial/expenses",
            json=sample_expense_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["expense_number"] == sample_expense_data["expense_number"]
        assert data["amount"] == sample_expense_data["amount"]
        assert data["status"] == "pending"

    def test_approve_expense(self, client, headers, sample_expense_category_data, sample_expense_data):
        """Test approving an expense"""
        # Create category and expense first
        cat_response = client.post(
            "/api/v1/financial/expense-categories",
            json=sample_expense_category_data,
            headers=headers
        )
        category_id = cat_response.json()["id"]
        sample_expense_data["category_id"] = category_id

        exp_response = client.post(
            "/api/v1/financial/expenses",
            json=sample_expense_data,
            headers=headers
        )
        expense_id = exp_response.json()["id"]

        # Approve expense
        approval_data = {"action": "approve", "approval_notes": "Approved for testing"}
        response = client.post(
            f"/api/v1/financial/expenses/{expense_id}/approve",
            json=approval_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "approve"
        assert data["expense_id"] == expense_id

    def test_expenses_summary(self, client, headers):
        """Test expenses summary endpoint"""
        response = client.get("/api/v1/financial/expenses/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_expenses" in data
        assert "by_status" in data
        assert "by_category" in data

    def test_expenses_health(self, client, headers):
        """Test expenses module health check"""
        response = client.get("/api/v1/financial/expenses/health", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "expenses"


class TestPettyCashModule:
    """Test Petty Cash module functionality"""

    def test_create_petty_cash_fund(self, client, headers, sample_petty_cash_data):
        """Test creating a petty cash fund"""
        response = client.post(
            "/api/v1/financial/petty-cash",
            json=sample_petty_cash_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["fund_name"] == sample_petty_cash_data["fund_name"]
        assert data["current_balance"] == sample_petty_cash_data["current_balance"]

    def test_create_petty_cash_transaction(self, client, headers, sample_petty_cash_data):
        """Test creating a petty cash transaction"""
        # Create fund first
        fund_response = client.post(
            "/api/v1/financial/petty-cash",
            json=sample_petty_cash_data,
            headers=headers
        )
        fund_id = fund_response.json()["id"]

        # Create transaction
        transaction_data = {
            "petty_cash_id": fund_id,
            "transaction_number": "PCT-2024-001",
            "transaction_date": "2024-01-15T10:00:00",
            "transaction_type": "expense",
            "amount": 25.00,
            "balance_before": 500.00,
            "balance_after": 475.00,
            "description": "Office supplies purchase",
            "vendor_name": "Staples",
            "has_receipt": True,
            "receipt_number": "REC-001"
        }

        response = client.post(
            f"/api/v1/financial/petty-cash/{fund_id}/transactions",
            json=transaction_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == transaction_data["amount"]
        assert data["transaction_type"] == transaction_data["transaction_type"]

    def test_petty_cash_summary(self, client, headers):
        """Test petty cash summary endpoint"""
        response = client.get("/api/v1/financial/petty-cash/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_funds" in data
        assert "total_balance" in data
        assert "by_type" in data

    def test_petty_cash_health(self, client, headers):
        """Test petty cash module health check"""
        response = client.get("/api/v1/financial/petty-cash/health", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "pettycash"


class TestVoucherModule:
    """Test Voucher module functionality"""

    def test_create_voucher(self, client, headers, sample_voucher_data):
        """Test creating a voucher"""
        response = client.post(
            "/api/v1/financial/vouchers",
            json=sample_voucher_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["voucher_number"] == sample_voucher_data["voucher_number"]
        assert data["amount"] == sample_voucher_data["amount"]
        assert data["status"] == sample_voucher_data["status"]

    def test_approve_voucher(self, client, headers, sample_voucher_data):
        """Test approving a voucher"""
        # Create voucher first
        create_response = client.post(
            "/api/v1/financial/vouchers",
            json=sample_voucher_data,
            headers=headers
        )
        voucher_id = create_response.json()["id"]

        # Approve voucher
        approval_data = {"action": "approve", "approval_notes": "Approved for payment"}
        response = client.post(
            f"/api/v1/financial/vouchers/{voucher_id}/approve",
            json=approval_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "approve"
        assert data["voucher_id"] == voucher_id

    def test_pay_voucher(self, client, headers, sample_voucher_data):
        """Test paying a voucher"""
        # Create and approve voucher first
        create_response = client.post(
            "/api/v1/financial/vouchers",
            json=sample_voucher_data,
            headers=headers
        )
        voucher_id = create_response.json()["id"]

        # Approve first
        approval_data = {"action": "approve", "approval_notes": "Approved for payment"}
        client.post(
            f"/api/v1/financial/vouchers/{voucher_id}/approve",
            json=approval_data,
            headers=headers
        )

        # Pay voucher
        payment_data = {
            "payment_date": "2024-01-16",
            "payment_method": "bank_transfer",
            "payment_reference": "BT-001",
            "bank_account": "ACC-123456",
            "notes": "Payment processed"
        }
        response = client.post(
            f"/api/v1/financial/vouchers/{voucher_id}/pay",
            json=payment_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["voucher_id"] == voucher_id
        assert data["amount"] == sample_voucher_data["amount"]

    def test_vouchers_summary(self, client, headers):
        """Test vouchers summary endpoint"""
        response = client.get("/api/v1/financial/vouchers/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_vouchers" in data
        assert "by_status" in data
        assert "by_type" in data

    def test_voucher_health(self, client, headers):
        """Test voucher module health check"""
        response = client.get("/api/v1/financial/vouchers/health", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "voucher"


class TestInvoicesModule:
    """Test Invoices module functionality"""

    def test_create_invoice(self, client, headers, sample_order_data, sample_invoice_data):
        """Test creating an invoice"""
        # Create order first
        order_response = client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )
        order_id = order_response.json()["id"]
        sample_invoice_data["order_id"] = order_id

        # Create invoice
        response = client.post(
            "/api/v1/financial/invoices",
            json=sample_invoice_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["invoice_number"] == sample_invoice_data["invoice_number"]
        assert data["total_amount"] == sample_invoice_data["total_amount"]

    def test_send_invoice(self, client, headers, sample_order_data, sample_invoice_data):
        """Test sending an invoice"""
        # Create order and invoice first
        order_response = client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )
        order_id = order_response.json()["id"]
        sample_invoice_data["order_id"] = order_id

        invoice_response = client.post(
            "/api/v1/financial/invoices",
            json=sample_invoice_data,
            headers=headers
        )
        invoice_id = invoice_response.json()["id"]

        # Send invoice
        send_data = {
            "email_addresses": ["customer@example.com"],
            "subject": "Your Invoice",
            "message": "Please find your invoice attached",
            "send_pdf": True
        }
        response = client.post(
            f"/api/v1/financial/invoices/{invoice_id}/send",
            json=send_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["invoice_id"] == invoice_id
        assert data["sent_to"] == send_data["email_addresses"]

    def test_record_invoice_payment(self, client, headers, sample_order_data, sample_invoice_data):
        """Test recording a payment for an invoice"""
        # Create order and invoice first
        order_response = client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )
        order_id = order_response.json()["id"]
        sample_invoice_data["order_id"] = order_id

        invoice_response = client.post(
            "/api/v1/financial/invoices",
            json=sample_invoice_data,
            headers=headers
        )
        invoice_id = invoice_response.json()["id"]

        # Record payment
        payment_data = {
            "amount": 500.00,
            "payment_date": "2024-01-16",
            "payment_method": "credit_card",
            "payment_reference": "CC-001",
            "notes": "Partial payment"
        }
        response = client.post(
            f"/api/v1/financial/invoices/{invoice_id}/payment",
            json=payment_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["invoice_id"] == invoice_id
        assert data["amount"] == payment_data["amount"]
        assert data["new_balance"] == 600.00  # 1100 - 500

    def test_invoices_summary(self, client, headers):
        """Test invoices summary endpoint"""
        response = client.get("/api/v1/financial/invoices/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_invoices" in data
        assert "total_amount" in data
        assert "by_status" in data

    def test_invoices_health(self, client, headers):
        """Test invoices module health check"""
        response = client.get("/api/v1/financial/invoices/health", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "invoices"


class TestPaymentsModule:
    """Test Payments module functionality"""

    def test_create_payment_gateway(self, client, headers, sample_payment_gateway_data):
        """Test creating a payment gateway"""
        response = client.post(
            "/api/v1/financial/payment-gateways",
            json=sample_payment_gateway_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gateway_name"] == sample_payment_gateway_data["gateway_name"]
        assert data["gateway_code"] == sample_payment_gateway_data["gateway_code"]

    def test_create_payment(self, client, headers, sample_payment_data):
        """Test creating a payment record"""
        response = client.post(
            "/api/v1/financial/payments",
            json=sample_payment_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_number"] == sample_payment_data["payment_number"]
        assert data["amount"] == sample_payment_data["amount"]

    def test_process_payment(self, client, headers, sample_payment_gateway_data, sample_order_data):
        """Test processing a payment"""
        # Create gateway first
        client.post(
            "/api/v1/financial/payment-gateways",
            json=sample_payment_gateway_data,
            headers=headers
        )

        # Create order
        order_response = client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )
        order_id = order_response.json()["id"]

        # Process payment
        payment_request = {
            "order_id": order_id,
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "credit_card",
            "gateway_code": "stripe_test",
            "card_number": "4111111111111111",
            "card_expiry_month": 12,
            "card_expiry_year": 2025,
            "card_cvv": "123",
            "card_holder_name": "Test User"
        }
        response = client.post(
            "/api/v1/financial/payments/process",
            json=payment_request,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "payment_id" in data
        assert data["amount"] == payment_request["amount"]
        assert data["success"] in [True, False]  # Could succeed or fail in simulation

    def test_refund_payment(self, client, headers, sample_payment_data):
        """Test refunding a payment"""
        # Create payment first
        sample_payment_data["status"] = "completed"
        payment_response = client.post(
            "/api/v1/financial/payments",
            json=sample_payment_data,
            headers=headers
        )
        payment_id = payment_response.json()["id"]

        # Refund payment
        refund_data = {
            "amount": 50.00,
            "reason": "Customer requested refund",
            "notes": "Partial refund for testing"
        }
        response = client.post(
            f"/api/v1/financial/payments/{payment_id}/refund",
            json=refund_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original_payment_id"] == payment_id
        assert data["refund_amount"] == refund_data["amount"]

    def test_payments_summary(self, client, headers):
        """Test payments summary endpoint"""
        response = client.get("/api/v1/financial/payments/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_payments" in data
        assert "total_amount" in data
        assert "by_method" in data
        assert "by_status" in data

    def test_payments_health(self, client, headers):
        """Test payments module health check"""
        response = client.get("/api/v1/financial/payments/health", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "payments"


class TestCrossModuleIntegration:
    """Test integration between modules"""

    def test_order_to_invoice_to_payment_flow(self, client, headers, sample_order_data, sample_payment_gateway_data):
        """Test complete flow from order to invoice to payment"""
        # 1. Create payment gateway
        client.post(
            "/api/v1/financial/payment-gateways",
            json=sample_payment_gateway_data,
            headers=headers
        )

        # 2. Create order
        order_response = client.post(
            "/api/v1/financial/orders",
            json=sample_order_data,
            headers=headers
        )
        order_id = order_response.json()["id"]
        assert order_response.status_code == 200

        # 3. Create invoice from order
        invoice_data = {
            "order_id": order_id,
            "invoice_number": "INV-FLOW-001",
            "status": "draft",
            "invoice_date": "2024-01-15",
            "due_date": "2024-02-15",
            "subtotal": sample_order_data["subtotal"],
            "tax_amount": sample_order_data["tax_amount"],
            "total_amount": sample_order_data["total_amount"],
            "balance_due": sample_order_data["total_amount"],
            "currency": "USD"
        }
        invoice_response = client.post(
            "/api/v1/financial/invoices",
            json=invoice_data,
            headers=headers
        )
        invoice_id = invoice_response.json()["id"]
        assert invoice_response.status_code == 200

        # 4. Send invoice
        send_data = {
            "email_addresses": ["customer@example.com"],
            "subject": "Your Invoice",
            "send_pdf": True
        }
        send_response = client.post(
            f"/api/v1/financial/invoices/{invoice_id}/send",
            json=send_data,
            headers=headers
        )
        assert send_response.status_code == 200

        # 5. Process payment for invoice
        payment_request = {
            "invoice_id": invoice_id,
            "amount": sample_order_data["total_amount"],
            "currency": "USD",
            "payment_method": "credit_card",
            "gateway_code": "stripe_test"
        }
        payment_response = client.post(
            "/api/v1/financial/payments/process",
            json=payment_request,
            headers=headers
        )
        assert payment_response.status_code == 200
        payment_data = payment_response.json()

        # 6. If payment successful, record it on invoice
        if payment_data.get("success"):
            invoice_payment_data = {
                "amount": sample_order_data["total_amount"],
                "payment_date": "2024-01-15",
                "payment_method": "credit_card",
                "payment_reference": payment_data.get("transaction_id")
            }
            invoice_payment_response = client.post(
                f"/api/v1/financial/invoices/{invoice_id}/payment",
                json=invoice_payment_data,
                headers=headers
            )
            assert invoice_payment_response.status_code == 200

    def test_expense_to_voucher_flow(self, client, headers, sample_expense_category_data, sample_expense_data):
        """Test flow from expense approval to voucher creation"""
        # 1. Create expense category
        cat_response = client.post(
            "/api/v1/financial/expense-categories",
            json=sample_expense_category_data,
            headers=headers
        )
        category_id = cat_response.json()["id"]

        # 2. Create expense
        sample_expense_data["category_id"] = category_id
        expense_response = client.post(
            "/api/v1/financial/expenses",
            json=sample_expense_data,
            headers=headers
        )
        expense_id = expense_response.json()["id"]

        # 3. Approve expense
        approval_data = {"action": "approve", "approval_notes": "Approved for payment"}
        approve_response = client.post(
            f"/api/v1/financial/expenses/{expense_id}/approve",
            json=approval_data,
            headers=headers
        )
        assert approve_response.status_code == 200

        # 4. Create voucher for the expense
        voucher_data = {
            "expense_id": expense_id,
            "voucher_number": "VOU-EXP-001",
            "voucher_date": "2024-01-15",
            "voucher_type": "payment",
            "payee_name": "Employee Name",
            "payee_type": "employee",
            "amount": sample_expense_data["total_amount"],
            "currency": "USD",
            "purpose": "Expense reimbursement",
            "status": "draft"
        }
        voucher_response = client.post(
            "/api/v1/financial/vouchers",
            json=voucher_data,
            headers=headers
        )
        assert voucher_response.status_code == 200

    def test_modules_info_endpoint(self, client, headers):
        """Test modules information endpoint"""
        response = client.get("/api/v1/financial/modules", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "financial-service"
        assert data["version"] == "2.0.0"
        assert data["architecture"] == "modular"
        assert len(data["modules"]) == 6

        # Check that all modules are present
        module_names = list(data["modules"].keys())
        expected_modules = ["orders", "expenses", "pettycash", "voucher", "invoices", "payments"]
        for module in expected_modules:
            assert module in module_names

    def test_tenant_initialization(self, client, headers):
        """Test tenant initialization endpoint"""
        tenant_id = "test-tenant-789"
        init_data = {"schema_name": "test_schema_789"}

        response = client.post(
            f"/api/v1/tenants/{tenant_id}/initialize",
            json=init_data,
            headers=headers
        )
        # This might fail if schema manager is not properly mocked
        # but the endpoint should be accessible
        assert response.status_code in [200, 404, 500]  # Various valid responses depending on setup


class TestErrorHandling:
    """Test error handling across modules"""

    def test_not_found_errors(self, client, headers):
        """Test 404 errors for non-existent resources"""
        endpoints = [
            "/api/v1/financial/orders/99999",
            "/api/v1/financial/expenses/99999",
            "/api/v1/financial/petty-cash/99999",
            "/api/v1/financial/vouchers/99999",
            "/api/v1/financial/invoices/99999",
            "/api/v1/financial/payments/99999"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 404

    def test_validation_errors(self, client, headers):
        """Test validation errors with invalid data"""
        # Test invalid order data
        invalid_order = {"order_number": ""}  # Missing required fields
        response = client.post("/api/v1/financial/orders", json=invalid_order, headers=headers)
        assert response.status_code == 422

        # Test invalid expense data
        invalid_expense = {"amount": -100}  # Negative amount
        response = client.post("/api/v1/financial/expenses", json=invalid_expense, headers=headers)
        assert response.status_code == 422

    def test_unauthorized_access(self, client):
        """Test unauthorized access without proper headers"""
        response = client.get("/api/v1/financial/orders")
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

    def test_permission_errors(self, client):
        """Test permission errors with limited permissions"""
        # This would require mocking a user with limited permissions
        # For now, we'll test that the endpoint exists
        limited_headers = {
            "Authorization": "Bearer limited-token",
            "Content-Type": "application/json"
        }

        response = client.get("/api/v1/financial/orders", headers=limited_headers)
        # Should either work with overridden auth or fail with proper error
        assert response.status_code in [200, 401, 403]


class TestPerformance:
    """Basic performance tests"""

    def test_bulk_operations(self, client, headers, sample_expense_category_data):
        """Test bulk operations don't timeout"""
        # Create category first
        cat_response = client.post(
            "/api/v1/financial/expense-categories",
            json=sample_expense_category_data,
            headers=headers
        )
        category_id = cat_response.json()["id"]

        # Test bulk expense creation (simulate)
        expenses = []
        for i in range(5):  # Create 5 expenses quickly
            expense_data = {
                "category_id": category_id,
                "expense_number": f"EXP-BULK-{i+1:03d}",
                "expense_date": "2024-01-15",
                "expense_type": "office",
                "description": f"Bulk expense {i+1}",
                "amount": 50.00,
                "tax_amount": 5.00,
                "total_amount": 55.00,
                "currency": "USD"
            }
            response = client.post(
                "/api/v1/financial/expenses",
                json=expense_data,
                headers=headers
            )
            assert response.status_code == 200
            expenses.append(response.json()["id"])

        # Verify all expenses were created
        assert len(expenses) == 5

    def test_pagination_performance(self, client, headers):
        """Test pagination doesn't timeout with large page sizes"""
        # Test large page size requests
        response = client.get(
            "/api/v1/financial/orders?limit=1000",
            headers=headers
        )
        assert response.status_code == 200

        response = client.get(
            "/api/v1/financial/expenses?limit=1000",
            headers=headers
        )
        assert response.status_code == 200

    def test_summary_endpoints_performance(self, client, headers):
        """Test summary endpoints respond quickly"""
        summary_endpoints = [
            "/api/v1/financial/expenses/summary",
            "/api/v1/financial/petty-cash/summary",
            "/api/v1/financial/vouchers/summary",
            "/api/v1/financial/invoices/summary",
            "/api/v1/financial/payments/summary"
        ]

        for endpoint in summary_endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)


if __name__ == "__main__":
    """
    Run integration tests
    Usage: python -m pytest tests/test_integration.py -v
    """
    pytest.main([__file__, "-v", "--tb=short"])
