select a.FormattedGLAcctNo,a.Description ,sum(b.BudgetAmt) as BudgetAmt
from tglBudget b
left join vdvglAccount a on b.GLAcctKey = a.GLAcctKey
where b.FiscYear = ( select top 1 d.FiscYear from tglFiscalPeriod d
					 where getdate() between d.StartDate and d.EndDate)
group by a.FormattedGLAcctNo, a.Description
order by a.FormattedGLAcctNo

-- grant select on tglBudget to public;
-- grant select on tglFiscalPeriod to public;
-- grant select on vdvglAccount to public;