/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ListController } from "@web/views/list/list_controller";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

console.log("🚀 MODULE LOADED!");

// =============================================================================
// LIST CONTROLLER PATCH
// =============================================================================
patch(ListController.prototype, {
    setup() {
        super.setup();
        console.log("🎯 LIST CONTROLLER SETUP CALLED!");
    },

    /**
     * @override
     * Intercept duplicate action in list view
     */
    async duplicateRecords() {
        console.log("🔍 DUPLICATE RECORDS CALLED FROM LIST VIEW!");

        const selection = this.model.root.selection;
        const recordCount = selection.length;
        const message = recordCount === 1
            ? _t("Are you sure you want to duplicate this record?")
            : _t("Are you sure you want to duplicate these %s records?", recordCount);

        return new Promise((resolve) => {
            this.dialogService.add(ConfirmationDialog, {
                title: _t("Duplicate Confirmation"),
                body: message,
                confirm: async () => {
                    console.log("✅ User confirmed duplication from list view");
                    const result = await super.duplicateRecords(...arguments);
                    resolve(result);
                },
                confirmLabel: _t("Duplicate"),
                cancel: () => {
                    console.log("❌ User cancelled duplication from list view");
                    resolve();
                },
                cancelLabel: _t("Cancel"),
            });
        });
    },

    /**
     * @override
     * Intercept create button in list view
     */
    async onClickCreate() {
        console.log("🔍 CREATE CLICKED IN LIST VIEW!");

        return new Promise((resolve) => {
            this.dialogService.add(ConfirmationDialog, {
                title: _t("Create Confirmation"),
                body: _t("Are you sure you want to create a new record?"),
                confirm: async () => {
                    console.log("✅ User confirmed creation from list view");
                    const result = await super.onClickCreate(...arguments);
                    resolve(result);
                },
                confirmLabel: _t("Create"),
                cancel: () => {
                    console.log("❌ User cancelled creation from list view");
                    resolve();
                },
                cancelLabel: _t("Cancel"),
            });
        });
    }
});

// =============================================================================
// FORM CONTROLLER PATCH
// =============================================================================
patch(FormController.prototype, {
    setup() {
        super.setup();
        console.log("🎯 FORM CONTROLLER SETUP CALLED!");
    },

    /**
     * @override
     * Intercept duplicate button in form view
     */
    async duplicateRecord() {
        console.log("🔍 DUPLICATE RECORD CALLED FROM FORM VIEW!");

        return new Promise((resolve) => {
            this.dialogService.add(ConfirmationDialog, {
                title: _t("Duplicate Confirmation"),
                body: _t("Are you sure you want to duplicate this record?"),
                confirm: async () => {
                    console.log("✅ User confirmed duplication from form view");
                    const result = await super.duplicateRecord(...arguments);
                    resolve(result);
                },
                confirmLabel: _t("Duplicate"),
                cancel: () => {
                    console.log("❌ User cancelled duplication from form view");
                    resolve();
                },
                cancelLabel: _t("Cancel"),
            });
        });
    }
});