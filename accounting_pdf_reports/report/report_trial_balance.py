import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportTrialBalance(models.AbstractModel):
    _name = 'report.accounting_pdf_reports.report_trialbalance'
    _description = 'Trial Balance Report'

    def _get_accounts(self, accounts, display_account, date_from=None):
        """
        Compute the balance, debit, and credit for the provided accounts,
        and include the initial balance if `date_from` is provided.

        :param accounts: list of accounts record
        :param display_account: filter type for displaying accounts
        :param date_from: starting date to calculate initial balance
        :return: list of dictionaries of accounts with initial balance, debit, credit, and balance
        """
        account_result = {}
        initial_balance_result = {}

        # Prepare SQL query based on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)

        # Compute the balance, debit, and credit for the provided accounts
        request = """
            SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit,
            (SUM(debit) - SUM(credit)) AS balance
            FROM {tables} 
            WHERE account_id IN %s {filters}
            GROUP BY account_id
        """.format(tables=tables, filters=filters)
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)

        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        # Compute initial balance up to `date_from` if provided
        if date_from:
            initial_balance_query = """
                SELECT account_id AS id, SUM(debit) - SUM(credit) AS initial_balance
                FROM account_move_line
                WHERE account_id IN %s AND date < %s AND parent_state = 'posted'
                GROUP BY account_id
            """
            self.env.cr.execute(initial_balance_query, (tuple(accounts.ids), date_from))
            for row in self.env.cr.dictfetchall():
                initial_balance_result[row['id']] = row['initial_balance']

        # Prepare account results with initial balance
        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance', 'initial_balance'])
            currency = account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            res['initial_balance'] = initial_balance_result.get(account.id, 0.0)

            if account.id in account_result:
                res['debit'] = account_result[account.id].get('debit', 0.0)
                res['credit'] = account_result[account.id].get('credit', 0.0)
                res['balance'] = account_result[account.id].get('balance', 0.0)

            res['balance']=res['initial_balance'] + res['balance'] if res['balance'] else res['initial_balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (
                    not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        domain = []
        if data['form'].get('account_ids', False):
            domain.append(('id', 'in', data['form']['account_ids']))
        accounts = docs if model == 'account.account' else self.env['account.account'].search(domain)
        context = data['form'].get('used_context')
        analytic_accounts = []
        if data['form'].get('analytic_account_ids'):
            analytic_account_ids = self.env['account.analytic.account'].browse(data['form'].get('analytic_account_ids'))
            context['analytic_account_ids'] = analytic_account_ids
            analytic_accounts = [account.name for account in analytic_account_ids]
        account_res = self.with_context(context)._get_accounts(accounts, display_account,
                                                               date_from=data['form'].get('date_from'))
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'print_journal': codes,
            'analytic_accounts': analytic_accounts,
            'time': time,
            'Accounts': account_res,
        }
