-- List all transactions for the current fiscal year, based on today's date.
-- Fiscal year starts on 3/1 and ends just before the next year's 3/1
-- This version avoids DECLARE/SET by inlining the window via a CTE.

;WITH fisc AS (
    SELECT
        CASE WHEN MONTH(GETDATE()) < 3
             THEN DATEFROMPARTS(YEAR(GETDATE()) - 1, 3, 1)
             ELSE DATEFROMPARTS(YEAR(GETDATE())    , 3, 1)
        END AS fiscFrom,
        DATEADD(YEAR, 1,
            CASE WHEN MONTH(GETDATE()) < 3
                 THEN DATEFROMPARTS(YEAR(GETDATE()) - 1, 3, 1)
                 ELSE DATEFROMPARTS(YEAR(GETDATE())    , 3, 1)
            END
        ) AS fiscToExclusive
), t AS (
    SELECT
        v.FormattedGLAcctNo AS gl,
        v.PostCmnt          AS description,
        CAST(v.CreateDate AS date) AS tr_date,
        vo.TranAmt			AS amount,
        v.VouchNo,
        vo.PurchAddrName    AS vendor_name
    FROM vdvglAccountTran v
    LEFT JOIN vdvVoucher vo ON v.VouchNo = vo.VouchNo
    CROSS JOIN fisc
    WHERE v.CompanyID = 'WWD'
      AND v.CreateDate >= fisc.fiscFrom
      AND v.CreateDate <  fisc.fiscToExclusive
      AND v.JrnlID IN ('AP')
      AND ISNULL(v.VouchNo,'') > ''
      AND RIGHT(v.FormattedGLAcctNo,14) > '00-00-00-00-00'
)
SELECT
    distinct
    t.gl,
    t.description,
    t.tr_date,
    t.VouchNo,
    t.vendor_name,
    t.amount
FROM t
ORDER BY t.gl, t.tr_date, t.VouchNo;

-- grant select on vdvglAccountTran to public;
-- grant select on vdvVoucher to public;
