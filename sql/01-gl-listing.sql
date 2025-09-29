select v.FormattedGLAcctNo as gl,
       v.Description       as descrip,
       v.Segment1Desc      as seg01,
       case
           when v.Segment2Desc = 'Default Description' then '-'
           else v.Segment2Desc
           end             as seg02,
       case
           when v.Segment3Desc = 'Default Description' then '-'
           else v.Segment3Desc
           end             as seg03,
       case
           when v.Segment4Desc = 'Default Description' then '-'
           else v.Segment4Desc
           end             as seg04,
       case
           when v.Segment5Desc = 'Default Description' then '-'
           else v.Segment5Desc
           end             as seg05,
       v.accttypeid,
       v.accttypedesc
from vdvglaccount v
where CompanyID = 'WWD'
  and v.Status = 1
  and isnull(right(v.FormattedGLAcctNo, 14), '00-00-00-00-00') <> '00-00-00-00-00'
order by v.FormattedGLAcctNo;

-- grant select on vdvglaccount to public;