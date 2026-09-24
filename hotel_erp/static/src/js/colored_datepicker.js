/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { onMounted, onPatched } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// Odoo 18-ის რეესტრიდან DateField-ის კომპონენტის უსაფრთხოდ წამოღება
const dateField = registry.category("fields").get("date");

if (dateField && dateField.component) {
    patch(dateField.component.prototype, {
        setup() {
            super.setup();
            this.orm = useService("orm");

            onMounted(() => this.highlightBookedDates());
            onPatched(() => this.highlightBookedDates());
        },

        async highlightBookedDates() {
            // მხოლოდ check_in და check_out ველებზე ამუშავება
            if (this.props.name !== 'check_in' && this.props.name !== 'check_out') {
                return;
            }

            const record = this.props.record;
            const roomId = record.data.room_id ? record.data.room_id[0] : null;

            if (!roomId) return;

            try {
                // ბაზიდან ამ ოთახის აქტიური ჯავშნების წამოღება
                const reservations = await this.orm.searchRead(
                    "hotel.reservation",
                    [["room_id", "=", roomId], ["state", "!=", "cancelled"]],
                    ["check_in", "check_out"]
                );

                const bookedDates = new Set();
                reservations.forEach(res => {
                    let current = new Date(res.check_in);
                    const stop = new Date(res.check_out);
                    while (current < stop) {
                        bookedDates.add(current.toISOString().split('T')[0]);
                        current.setDate(current.getDate() + 1);
                    }
                });

                // კალენდარში დაკავებული დღეების გაწითლება და დაბლოკვა
                setTimeout(() => {
                    const dayCells = document.querySelectorAll(".o_date_picker .o_day, .o_datetime_picker .o_day, .o_cell");
                    dayCells.forEach(cell => {
                        const cellDate = cell.dataset.date;
                        if (cellDate && bookedDates.has(cellDate)) {
                            cell.style.backgroundColor = "#ff4d4d";
                            cell.style.color = "#ffffff";
                            cell.style.fontWeight = "bold";
                            cell.style.textDecoration = "line-through";
                            cell.style.pointerEvents = "none"; // დაკლიკების დაბლოკვა
                            cell.title = "ეს თარიღი დაკავებულია";
                        }
                    });
                }, 150);

            } catch (error) {
                console.error("Error highlighting dates:", error);
            }
        }
    });
}