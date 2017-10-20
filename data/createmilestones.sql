
insert into project_task(create_date,
  date_end,
  write_uid,
  planned_hours,
  partner_id,
  create_uid,
  user_id,
  date_start,
  company_id,
  project_id,
  project_ref_id,
  date_last_stage_update,
  write_date,
  active,
  stage_id,
  name,
  date_deadline,
  reviewer_id,
  total_hours,
  remaining_hours,
  sale_order_id,
  milestone,
  invoiced,
  invoice_amount,
  invoice_date,cost,effective_cost,price) 
  select b.create_date, b.invoice_date, b.write_uid, 0, a.partner_id, b.create_uid, 7,
  b.invoice_date, 1, 290, a.project_id, b.invoice_date, b.write_date, true, 
  case when b.invoiced = true then 7 else 5002 end, 'Fatturazione del ' || to_char(b.invoice_date::timestamp,'DD/MM/YYYY'), b.invoice_date, 1,
  0,0, b.sale_order_id, false, b.invoiced, b.planned_amount, b.invoice_date,0,0,0
  from crossovered_budget_lines b
  inner join account_analytic_account a on b.analytic_account_id = a.id
  inner join sale_order s on b.sale_order_id = s.id
  where s.state = 'manual';


---- todo: riportare lo stato dell'ordine sul task

  