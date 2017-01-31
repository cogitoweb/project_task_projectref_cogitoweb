
drop trigger if exists trig_before_insupd_project_task on project_task;

drop function if exists before_insupd_project_task();

create or replace function before_insupd_project_task()
    returns trigger as
$BODY$
    
begin

    if new.date_deadline is not null and new.date_end is null then

        new.date_end := GREATEST(new.date_deadline + time '19:00', new.date_start + interval '1 hour');
        
    end if;

    if new.date_deadline is not null and new.date_end is not null and new.date_deadline < new.date_end::date then
    
        new.date_deadline = new.date_end::date;
        
    end if;
    
return new;

end;

$BODY$

language plpgsql volatile cost 100;

CREATE TRIGGER trig_before_insupd_project_task BEFORE INSERT OR UPDATE
   ON project_task FOR EACH ROW
   EXECUTE PROCEDURE before_insupd_project_task();

        
update project_task set date_deadline = date_end::date where date_end is not null and date_deadline is null;
update project_task set date_end = GREATEST(date_deadline + time '19:00', date_start + interval '1 hour') where date_deadline is not null and date_end is null;
update project_task set date_deadline = date_end::date where date_deadline < date_end::date;