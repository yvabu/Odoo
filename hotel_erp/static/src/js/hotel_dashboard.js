import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from '@web/core/utils/hooks';
import { loadJS } from "@web/core/assets";

export class HotelDashboard extends Component {
    static template = "hotel_erp.HotelDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ dateFrom: "", dateTo: "", data: {} });

        this.pieChartRef = useRef("chartCanvas");
        this.barChartRef = useRef("barChartCanvas");

        this.pieChart = null;
        this.barChart = null;

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadDashboardData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    async loadDashboardData() {
        const result = await this.orm.call("hotel.dashboard", "get_dashboard_data", [], {
            date_from: this.state.dateFrom || false,
            date_to: this.state.dateTo || false
        });
        this.state.data = result;
        if (!this.state.dateFrom) this.state.dateFrom = result.date_from;
        if (!this.state.dateTo) this.state.dateTo = result.date_to;

        if (this.pieChartRef.el) {
            this.renderCharts();
        }
    }

    async onDateChange() {
        await this.loadDashboardData();
    }

    // ---------- ლისტის გახსნა ----------
    openList(name, resModel, domain) {
        if (!domain){
            console.warn("Domain is missing for:", name);
            return;
        };
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: resModel,
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    onOccupiedClick() {
        this.openList("Occupied Rooms", "hotel.room", this.state.data.occupied_rooms_domain);
    }
    onAvailableClick() {
        this.openList("Available Rooms", "hotel.room", this.state.data.available_rooms_domain);
    }
    onRevenueClick() {
        this.openList("Revenues", "account.move", this.state.data.revenue_domain);
    }
    onExpensesClick() {
        this.openList("Expenses", "account.move", this.state.data.expenses_domain);
    }
    onProfitClick() {
        this.openList("Profit", "account.move", this.state.data.net_profit_domain);
    }
    onPaidClick() {
        this.openList("Payments", "account.payment", this.state.data.paid_amount_domain);
    }
    onTodayCheckinsClick(){
        this.openList("Today's Check-ins","hotel.reservation",this.state.data.checkins_today_domain)

    }
    onTodayCheckOutClick(){
        this.openList("Today's Check-outs","hotel.reservation",this.state.data.checkouts_today_domain)
    }

    // ---------- დიაგრამები ----------
    renderCharts() {
        this.renderPieChart();
        this.renderBarChart();
    }

    renderPieChart() {
        if (!this.pieChartRef.el || typeof Chart === "undefined") return;
        if (this.pieChart) this.pieChart.destroy();

        const ctx = this.pieChartRef.el.getContext("2d");
        const occupied = this.state.data.occupied_rooms || 0;
        const available = this.state.data.available_rooms || 0;
        const checkins=this.state.data.checkins_today || 0;
        const checkouts = this.state.data.checkouts_today || 0;

        this.pieChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Occupied Rooms", "Available Rooms","Today's Check-Ins","Today's Check-Outs"],
                datasets: [{
                    data: [occupied, available,checkins,checkouts],
                    backgroundColor: ["#818CF8", "#5ED4A5", "#8CBFF5", "#F8C96A"],
                    hoverBackgroundColor: ["#6366F1", "#34B58A", "#5AA2F0", "#F0AD2E"],
                    borderWidth: 4,
                    borderColor: "#FFFFFF",
                    hoverOffset: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "72%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            usePointStyle: true,
                            pointStyle: "circle",
                            padding: 16,
                            color: "#7C8AA0",
                            font: { size: 12 },
                        },
                    },
                },
                onHover: (evt, elements) => {
                    evt.native.target.style.cursor = elements.length ? "pointer" : "default";
                },
                onClick: (evt, elements) => {
                    if (!elements.length) return;

                    const index=elements[0].index

                    if (index === 0) this.onOccupiedClick();
                    else if(index===1) this.onAvailableClick();
                    else if(index===2) this.onTodayCheckinsClick();
                    else if(index===3) this.onTodayCheckOutClick();
                },
            }
        });
    }

    renderBarChart() {
        if (!this.barChartRef.el || typeof Chart === "undefined") return;
        if (this.barChart) this.barChart.destroy();

        const ctx = this.barChartRef.el.getContext("2d");
        const revenue = this.state.data.revenue || 0;
        const expenses = this.state.data.expenses || 0;
        const netProfit = this.state.data.net_profit || 0;

        this.barChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["Revenues", "Expenses", "Profit"],
                datasets: [{
                    label: "Financial Overview (₾)",
                    data: [revenue, expenses, netProfit],
                    backgroundColor: ["#5ED4A5", "#F59A9A", "#818CF8"],
                    hoverBackgroundColor: ["#34B58A", "#EF6B6B", "#6366F1"],
                    borderRadius: 8,
                    borderSkipped: false,
                    maxBarThickness: 56,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { color: "#7C8AA0", font: { size: 12 } },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "#F1F4F9" },
                        border: { display: false },
                        ticks: { color: "#A3AEC0" },
                    },
                },
                onHover: (evt, elements) => {
                    evt.native.target.style.cursor = elements.length ? "pointer" : "default";
                },
                onClick: (evt, elements) => {
                    if (!elements.length) return;
                    const i = elements[0].index;
                    if (i === 0) this.onRevenueClick();
                    else if (i === 1) this.onExpensesClick();
                    else this.onProfitClick();
                },
            }
        });
    }
}

registry.category("actions").add("hotel_erp.dashboard", HotelDashboard);