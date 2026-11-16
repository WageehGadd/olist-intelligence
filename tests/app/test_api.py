"""V3-12 tests use clearly synthetic CSV rows, never the Olist dataset."""
import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app.main import create_app


SYNTHETIC = "SYNTHETIC TEST FIXTURE — not verified Olist data"


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "FIXTURE_NOTICE.txt").write_text(SYNTHETIC, encoding="utf-8")
    write_csv(tmp_path / "sql_kpis.csv",
        ["kpi_name", "period", "value", "unit", "population", "numerator_count", "denominator_count", "definition_version"],
        [["orders_total", "all", "120", "orders", "all source orders", "", "", "v1"],
         ["delay_rate_calendar", "all", "0.1", "fraction", "eligible delivered orders", "2", "20", "v1"],
         ["delay_rate_calendar", "2024-01", "0.25", "fraction", "eligible delivered orders", "1", "4", "v1"],
         ["delay_rate_calendar", "2024-02", "", "fraction", "eligible delivered orders", "0", "0", "v1"]])
    write_csv(tmp_path / "sql_category_item_value.csv",
        ["period", "category_name", "item_value_brl", "definition_version"],
        [["all", "synthetic-category", "125.50", "v1"], ["2024-01", "synthetic-category", "25", "v1"]])
    write_csv(tmp_path / "eda_category_item_counts.csv",
        ["category_name", "item_count", "population", "definition_version"],
        [["synthetic-a", 3, "delivered_order_items", "v1"], ["synthetic-b", 1, "delivered_order_items", "v1"]])
    write_csv(tmp_path / "eda_item_price_distribution.csv",
        ["bin_label", "bin_lower_brl", "bin_upper_brl", "item_count", "population", "definition_version"],
        [["0-25", 0, 25, 3, "all_items_finite_nonnegative_price", "v1"],
         ["25-50", 25, 50, 2, "all_items_finite_nonnegative_price", "v1"],
         ["50-100", 50, 100, 0, "all_items_finite_nonnegative_price", "v1"],
         ["100-250", 100, 250, 0, "all_items_finite_nonnegative_price", "v1"],
         ["250-500", 250, 500, 0, "all_items_finite_nonnegative_price", "v1"],
         ["500+", 500, "", 0, "all_items_finite_nonnegative_price", "v1"]])
    return tmp_path


@pytest.fixture
def client(data_dir):
    return TestClient(create_app(data_directory=data_dir, template_directory=data_dir / "no-rana-templates", static_directory=data_dir / "no-static"))


def test_health_openapi_and_exact_route_set(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/health", "/", "/sales", "/delivery", "/predict",
        "/api/v1/analytics/summary", "/api/v1/analytics/delivery-monthly",
        "/api/v1/analytics/category-item-value", "/api/v1/charts/category-item-counts",
        "/api/v1/charts/item-price-distribution"}
    assert "post" not in paths
    assert client.post("/api/v1/predict").status_code == 404


def test_summary_preserves_authoritative_fixture_fields_and_null_rate(client):
    response = client.get("/api/v1/analytics/summary?period=all")
    assert response.status_code == 200
    data = response.json()
    assert data == {"period": "all", "definition_version": "v1", "kpis": {
        "orders_total": {"value": 120, "unit": "orders", "population": "all source orders", "numerator_count": None, "denominator_count": None, "definition_version": "v1"},
        "delay_rate_calendar": {"value": 0.1, "unit": "fraction", "population": "eligible delivered orders", "numerator_count": 2, "denominator_count": 20, "definition_version": "v1"}}}
    assert SYNTHETIC not in str(data)


def test_delivery_month_filter_and_undefined_month(client):
    all_rows = client.get("/api/v1/analytics/delivery-monthly").json()["series"]
    assert [row["period"] for row in all_rows] == ["2024-01", "2024-02"]
    assert all_rows[1]["value"] is None
    assert client.get("/api/v1/analytics/delivery-monthly?period=2024-01").json()["series"] == [all_rows[0]]


def test_category_period_and_eda_chart_contracts(client):
    all_values = client.get("/api/v1/analytics/category-item-value").json()
    assert len(all_values["series"]) == 2
    assert client.get("/api/v1/analytics/category-item-value?period=2024-01").json()["series"][0]["period"] == "2024-01"
    counts = client.get("/api/v1/charts/category-item-counts").json()
    assert counts["series"][0]["item_count"] == 3
    prices = client.get("/api/v1/charts/item-price-distribution").json()
    assert len(prices["series"]) == 6
    assert prices["series"][-1]["bin_upper_brl"] is None


@pytest.mark.parametrize("period", ["2024-1", "2024-13", "2023-02-29", "yesterday", "", "2024-01-01"])
def test_invalid_period_is_422(client, period):
    response = client.get("/api/v1/analytics/summary", params={"period": period})
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_PERIOD"


def test_all_pages_render_context_and_missing_source_state(tmp_path):
    client = TestClient(create_app(data_directory=tmp_path, template_directory=tmp_path / "none", static_directory=tmp_path / "none-static"))
    for path in ("/", "/sales", "/delivery"):
        response = client.get(path)
        assert response.status_code == 200
        assert "Backend fallback template" in response.text
        assert "unavailable" in response.text
        assert "Authoritative analytics data is not available yet." in response.text
    prediction = client.get("/predict")
    assert prediction.status_code == 200
    assert "Academic demonstration only" in prediction.text
    assert client.get("/api/v1/analytics/summary").json() == {"detail": "Authoritative analytics source is unavailable", "code": "DATA_UNAVAILABLE"}


def test_malformed_existing_file_fails_safely(data_dir):
    (data_dir / "sql_kpis.csv").write_text("wrong,header\n", encoding="utf-8")
    response = TestClient(create_app(data_directory=data_dir)).get("/api/v1/analytics/summary")
    assert response.status_code == 500
    assert response.json() == {"detail": "Authoritative analytics source is invalid", "code": "DATA_INVALID"}
    assert str(data_dir) not in response.text


def test_duplicate_kpi_key_is_rejected(data_dir):
    with (data_dir / "sql_kpis.csv").open("a", encoding="utf-8") as stream:
        stream.write("orders_total,all,120,orders,all source orders,,,v1\n")
    assert TestClient(create_app(data_directory=data_dir)).get("/api/v1/analytics/summary").json()["code"] == "DATA_INVALID"


def test_injected_rana_template_is_used(tmp_path):
    templates = tmp_path / "templates"
    (templates / "pages").mkdir(parents=True)
    (templates / "pages" / "overview.html").write_text("{{ page_urls.sales }}|{{ asset_prefix }}|{{ data_state }}", encoding="utf-8")
    response = TestClient(create_app(data_directory=tmp_path / "data", template_directory=templates)).get("/")
    assert response.status_code == 200
    assert response.text == "/sales|/static|unavailable"


def test_static_mount_is_omitted_when_directory_missing_or_symlink(tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(external, target_is_directory=True)
    app = create_app(data_directory=tmp_path / "data", template_directory=tmp_path / "templates", static_directory=linked)
    assert "/static" not in app.openapi()["paths"]

@pytest.mark.parametrize("replacement", [
    "delay_rate_calendar,2024-01,0.25,fraction,eligible delivered orders,1,4,v9",
    "delay_rate_calendar,2024-01,0.25,percent,eligible delivered orders,1,4,v1",
    "delay_rate_calendar,2024-01,2.0,fraction,eligible delivered orders,1,4,v1",
    "delay_rate_calendar,2024-01,0.25,fraction,eligible delivered orders,5,4,v1",
])
def test_invalid_kpi_contract_values_are_rejected(data_dir, replacement):
    path = data_dir / "sql_kpis.csv"
    rows = path.read_text(encoding="utf-8").splitlines()
    rows[3] = replacement
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    response = TestClient(create_app(data_directory=data_dir)).get("/api/v1/analytics/summary")
    assert response.status_code == 500
    assert response.json()["code"] == "DATA_INVALID"


def test_invalid_nonselected_kpi_row_still_fails_monthly_endpoint(data_dir):
    path = data_dir / "sql_kpis.csv"
    rows = path.read_text(encoding="utf-8").splitlines()
    rows[2] = rows[2].replace(",v1", ",v2")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    response = TestClient(create_app(data_directory=data_dir)).get("/api/v1/analytics/delivery-monthly?period=2024-01")
    assert response.status_code == 500
    assert response.json()["code"] == "DATA_INVALID"


def test_html_template_symlink_cannot_escape_configured_root(tmp_path):
    outside = tmp_path / "outside.html"
    outside.write_text("outside-root", encoding="utf-8")
    templates = tmp_path / "templates"
    (templates / "pages").mkdir(parents=True)
    (templates / "pages" / "overview.html").symlink_to(outside)
    response = TestClient(create_app(data_directory=tmp_path / "data", template_directory=templates)).get("/")
    assert response.status_code == 200
    assert "Backend fallback template" in response.text
    assert "outside-root" not in response.text


def test_static_assets_mount_only_inside_configured_root(tmp_path):
    static_root = tmp_path / "static"
    static_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside-only", encoding="utf-8")
    (static_root / "site.css").write_text("body{}", encoding="utf-8")
    (static_root / "escape.txt").symlink_to(outside)
    client = TestClient(create_app(data_directory=tmp_path / "data", template_directory=tmp_path / "templates", static_directory=static_root))
    assert client.get("/static/site.css").status_code == 200
    escaped = client.get("/static/escape.txt")
    assert escaped.status_code == 404
    assert "outside-only" not in escaped.text


def test_sales_page_keeps_available_charts_when_one_source_is_missing(data_dir):
    (data_dir / "sql_category_item_value.csv").unlink()
    response = TestClient(create_app(data_directory=data_dir)).get("/sales")
    assert response.status_code == 200
    assert "Data state: unavailable" in response.text
    assert '"category_name": "synthetic-a"' in response.text
    assert "Authoritative analytics data is not available yet." in response.text
