select v.VendName                   as Name,
       v.VendID                     as ID,
       vl.ItemID                    as Item,
       isnull(vl.Description, '')   as Description,
       cast(vl.Quantity as int)		as Qty,
	   cast(vl.UnitCost as money)	as Cost,
	   cast(vl.ExtAmt as money)     as Amount,
       isnull(vl.ExtCmnt, '')       as Comment,
       isnull(vl.PurchaseOrder, '') as PO,
	   cast(v.STaxAmt as money)     as Tax,
	   cast(v.FreightAmt as money)	as Freight
from vdvVoucher v
         left join vdvVoucherLine vl on v.VoucherKey = vl.VoucherKey
where v.CompanyID = 'WWD'
  and v.VouchNo = {vouchno};
