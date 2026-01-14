alert('s');

odoo.define('sale_test.hide_create_button', function (require) {
    const ListController = require('web.ListController');

    ListController.include({
        renderButtons() {
            this._super.apply(this, arguments);
            if (this.modelName === 'product.template') {
                const $create = this.$buttons.find('.o_list_button_add');
                if ($create.length) {
                    $create.hide();
                }
            }
        }
    });
});
✅ Test Summary:
Keep create in access rights ✅

Set create="false" in both tree and form XML ✅

Duplicate will still work ✅

"Create" button will disappear ❌

Let me know if you'd like me to check your XML or views directly.









