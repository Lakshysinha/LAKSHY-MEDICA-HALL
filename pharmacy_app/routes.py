import sqlite3

from flask import flash, redirect, render_template, request, session, url_for

from .auth import authenticate, login_required, role_required
from .service import ValidationError, add_medicine, create_sale, daily_summary, get_short_list, search_medicines


def register_routes(app):
    @app.route("/")
    @login_required
    def dashboard():
        totals, sales = daily_summary(request.args.get("day"), tenant_id=session.get("tenant_id", 1))
        totals, sales = daily_summary(request.args.get("day"))
        return render_template("dashboard.html", totals=totals, sales=sales)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            tenant_slug = request.form.get("tenant_slug") or app.config["DEFAULT_TENANT_SLUG"]
            user = authenticate(request.form["username"], request.form["password"], tenant_slug=tenant_slug)
            user = authenticate(request.form["username"], request.form["password"])
            if user:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                session["tenant_id"] = user["tenant_id"]
                session["tenant_slug"] = user["tenant_slug"]
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/medicines", methods=["GET", "POST"])
    @login_required
    @role_required({"owner", "pharmacist"})
    def medicines():
        tenant_id = session.get("tenant_id", 1)
        if request.method == "POST":
            try:
                add_medicine(request.form.to_dict(), tenant_id=tenant_id)
        if request.method == "POST":
            try:
                add_medicine(request.form.to_dict())
                flash("Medicine added.", "success")
            except (ValidationError, ValueError) as exc:
                flash(str(exc), "danger")
            except sqlite3.IntegrityError as exc:
                flash(f"Unable to save medicine: {exc}", "danger")
        query = request.args.get("q", "")
        rows = search_medicines(query, tenant_id=tenant_id) if query else []
        rows = search_medicines(query) if query else []
        return render_template("medicines.html", rows=rows, query=query)

    @app.route("/short-list")
    @login_required
    def short_list():
        rows = get_short_list(tenant_id=session.get("tenant_id", 1))
        rows = get_short_list()
        return render_template("short_list.html", rows=rows)

    @app.route("/sales", methods=["GET", "POST"])
    @login_required
    def sales():
        tenant_id = session.get("tenant_id", 1)
        if request.method == "POST":
            try:
                create_sale(
                    medicine_id=int(request.form["medicine_id"]),
                    strips_sold=int(request.form.get("strips_sold", 0)),
                    tablets_sold=int(request.form.get("tablets_sold", 0)),
                    payment_mode=request.form["payment_mode"],
                    customer_name=request.form.get("customer_name", ""),
                    user_id=session.get("user_id"),
                    tenant_id=tenant_id,
                )
                flash("Sale saved.", "success")
            except (ValidationError, ValueError) as exc:
                flash(str(exc), "danger")
        query = request.args.get("q", "")
        rows = search_medicines(query, tenant_id=tenant_id) if query else []
        rows = search_medicines(query) if query else []
        return render_template("sales.html", rows=rows, query=query)
