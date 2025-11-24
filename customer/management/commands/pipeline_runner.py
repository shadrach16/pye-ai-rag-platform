from django.core.management.base import BaseCommand, CommandError
import re
from django.utils import timezone
import datetime as dt
from datetime import datetime,timedelta
from django.core.exceptions import ObjectDoesNotExist
import logging 
import time
import os
from customer.models import Running_Jobs
from customer.utils import transformer_function





class Running_Jobs(models.Model):
    job = models.TextField(null=False,default='') 
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    last_run_date = models.DateField(default=timezone.now)
    last_run_time = models.TimeField(default=timezone.now)
    next_run_date = models.DateField(default=timezone.now)
    next_run_time = models.TimeField(default=timezone.now )


class Command(BaseCommand):
    help = 'Running Pipeline Services' 

    def get_open_jobs(self):
        return Running_Jobs.objects.filter(task__status='running')

    def calculate_run_dates(job):
        now = dt.datetime.now()
        lastrundatetime = dt.datetime.combine(job.last_run_date, job.last_run_time) 
        schedule_time = job.schedule_time
        minute_time= job.minute_time or 0
        daily_time=job.daily_time 
        weekly_time=job.weekly_time 
        weekly_day = job.weekly_day or 0
        weeks = {'mon':0, 'tue':1, 'wed':2, 'thu':3, 'fri':4, 'sat':5, 'sun':6}

        if schedule_time == 'hourly': # in minutes
            nextrundate = lastrundatetime + dt.timedelta(minutes=minute_time) 
        elif schedule_time == 'daily':
            daily_time = daily_time or lastrundatetime.time() 
            nextrundate = dt.datetime.combine(lastrundatetime.date(), daily_time)
            # if nextrundate <= lastrundatetime:
            #     nextrundate += dt.timedelta(days=1)
        elif schedule_time == 'weekly':
            weekly_time = weekly_time or lastrundatetime.time()
            today = lastrundatetime.weekday()  # 0 for Monday, 6 for Sunday
            days_until_next_run = (weeks[weekly_day] - today) % 7
            nextrundate = lastrundatetime + dt.timedelta(days=days_until_next_run)
            nextrundate = dt.datetime.combine(nextrundate.date(), weekly_time)
            # if nextrundate <= lastrundatetime:
            #     nextrundate += dt.timedelta(weeks=1) 
        else:
            pass

        return now, nextrundate



    def handle(self, *args, **options):
        while
        open_jobs = self.get_open_jobs()
        for job in open_jobs:
            transformer_function(task)


    
    def process_alerts(self):
        alerts_generator = self.alerts_generator(self.rule)
        for exception in alerts_generator:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(asyncio.create_task(self.process_exception(exception)))
                loop.close()
            except Exception as e:
                print("Alert Process Event Loop Err: ",e)



    def test_process_alerts(self):
        open_alerts = rica_alerts.objects.get(ricaAlertId='TEST1-000-20230507-16055029')
        self.process_exception(open_alerts) 


    def process_exception(self,exception):
        print("ricaAlertId: ",exception.ricaAlertId)
        try:
            if self.check_overdue(exception):
                overdues = self.get_overdues(exception)
                if int(exception.ricaOverdueCounter) < int(overdues.get('overdue_repeat')):
                    # Send Email
                    rule = self.get_rule(exception.ricaScenarioId)
                    msg_id = str(overdues['overdue_note']).split("-")[-1]
                    risk = self.get_risk(rule.ricaOverdueRiskMatrix or 11)
                    exception.ricaOverdueCounter = int(exception.ricaOverdueCounter) + 1 
                    risk['times'] = int(exception.ricaOverdueCounter)
                    risk['total'] = int(overdues.get('overdue_repeat'))
                    generate_alert_mail(exception,"Overdue - Immediate Attention Required","",exception.ricaLastActivist,msg_id,template='escalate.html',
                        ex_options=risk)
                else:
                    escalation_process =  get_status(overdues['escalation_process'] ,flag=True)
                    if str(escalation_process)=='1':
                        escalated = self.escalate_to_superior(exception)
                    else:
                        escalated = self.escalate_to_assignor(exception)
                    if escalated:
                        exception.ricaOverdueCounter = 0
                        self.update_reminder(exception)
                        print("escalated: ",escalated)

                exception.save()
        except Exception as e:
            print(f"Alert {exception.ricaAlertId} Process Failed: ",e)

 

    def update_reminder(self,exception):
        remind_date = datetime.now().strftime('yyyy-mm-dd')
        remind_time = datetime.now().strftime('%H:%M:%S')

        exception.ricaRemindNextDate = remind_date
        exception.ricaRemindNextTime = remind_time

    def escalate_to_assignor(self,exception):
        print("Escalating to Assignor")
        if exception.ricaAssignor:
            try:
                v_assignor = exception.ricaAssignor
                exception.ricaAssignor = exception.ricaAssignee
                exception.ricaAssignee = v_assignor
                # Send Assign Email to group
                generate_alert_mail(exception,"Assign",v_assignor,exception.ricaLastActivist,"1059") 
                return v_assignor
            except Exception as e:
                print("Escalation Error", e)
                return

    def escalate_to_superior(self,exception):
        print("Escalating to Superior")
        try:
            ex_options = {}
            spf = get_spf(self.language or 'en')
            results = self.get_alert_transactions(exception)
            users =  user_alert_involve(exception,False,spf,entryRecordList=results,field="ricaUserId",response=["ricaAssignee"])
            
            users= list(set(users.get('to',users)))
            all_superiors = []
            for user in users:
                if user:
                    superiors = self.get_user_superiors(exception,user) 
                    if superiors:
                        all_superiors = list(set(all_superiors + superiors)) 

            if len(all_superiors):
                group_id =    self.create_superior_group(exception,all_superiors)
                if group_id:
                    exception.ricaAssignor = exception.ricaAssignee
                    exception.ricaAssignee = group_id
                    # Send Assigne Email to group
                    print('group_id',group_id)
                    generate_alert_mail(exception,"Assign",group_id,exception.ricaLastActivist,"1059") 
                    print("alert has been escalated")
                    return group_id
        except Exception as e:
            print("Escalation Error", e)
            return



    def get_user_superiors(self,exception,user):

        try:
            user_designate = ricauser.objects.get(ricaUserId=user) 
            superior = ricadesignates.objects.get(ricaDesignateId=user_designate.ricaUserRole)
            superior_designate = superior.ricaSuperior
            users = get_user_via_designate(superior.ricaSuperior,exception.ricaBranchId,many=True) 
            return [x.get('ricaUserId') for x in users]

        except Exception as e:
            print('get_user_superiors Err:',e)
            return None

    def get_risk(self,risk_val=11):
        options = {}
        try:
            ricaSuggestedRisk = ricarisk_matrix.objects.get(ricaMatrixId__iexact=risk_val)
            options['risk'] = ricaSuggestedRisk.ricaRisk
            options['bg'] = ricaSuggestedRisk.ricaRiskColour
            options['color'] = 'white'
        except:
            options['risk'] = "Low"
            options['bg'] = 'yellow'
            options['color'] = 'white'

        print(options,risk_val)

        return options



    
    def create_superior_group(self,exception,superiors):
        audit = {

            'ricaLanguage':self.language or 'en',
            'ricaUserLocation':'9.0800128-7.4481664',
            'ricaOperator':'superuser',
            'ricaOperation':f'{self.language}-201',
            'ricaWorkstation':'192.168.0.163',
            'ricaRecordCounter':1,
        }

        _id = exception.ricaAlertId

        try:
            data = ricagroup_designates.objects.get(ricaGroupDesignateId=_id)
            user_group = ricaUserGroups.objects.filter(ricaGroup=_id).delete()

            for x in superiors:
                data = {}
                try:
                    data['ricaUserId'] = x
                    data['ricaUserGroupId'] =  f"{_id}-{createId(data.get('ricaUserId'))}"
                    data['ricaGroup'] = _id
                    data = {**data,**get_audit(audit)}
                    print('sdds======>',data)
                    UserGroups = ricaUserGroups.objects.create(**data)

                except Exception as e:
                    print('edit UserGroups=', e)
            return _id
                        
        except ObjectDoesNotExist: 
            req_data = {
            'ricaGroupDesignateId':_id,**get_audit(audit)
            }
            data = ricagroup_designates.objects.create(**req_data)

            for x in superiors:
                obj = {}
                obj['ricaUserId'] = x
                obj['ricaUserGroupId'] = f"{_id}-{createId(obj['ricaUserId'])}" 
                obj['ricaGroup'] = _id
                obj = {**obj,**get_audit(audit)}
                
                try:
                    UserGroups = ricaUserGroups.objects.get(ricaUserGroupId=obj['ricaUserGroupId'] ) 
                except ObjectDoesNotExist:
                    UserGroups = ricaUserGroups.objects.create(**obj) 
            return _id


    def get_alert_transactions(self,exception):
        results = []

        try:
            MAP = {'RICAEXCEPTIONID': 'ricaExceptionId', 'RICASCENARIOID': 'ricaScenarioId', 
            'RICAEXCEPTIONDESCRIPTION': 'ricaExceptionDescription', 'RICABRANCHID': 'ricaBranchId', 
            'RICAEXCEPTIONINDICATOR': 'ricaExceptionIndicator', 'RICARESPONDENT': 'ricaRespondent', 
            'RICARESPONDENTDESIGNATE': 'ricaRespondentDesignate', 'RICAINVESTIGATOR': 'ricaInvestigator', 
            'RICAINVESTIGATORDESIGNATE': 'ricaInvestigatorDesignate', 'RICAOWNER': 'ricaOwner', 
            'RICAOWNERDESIGNATE': 'ricaOwnerDesignate', 'RICANEXTOWNER': 'ricaNextOwner', 
            'RICANEXTOWNERDESIGNATE': 'ricaNextOwnerDesignate', 'RICAENFORCER': 'ricaEnforcer', 
            'RICAOTHERRECEIVERS': 'ricaOtherReceivers', 
            'RICAEXCEPTIONRESULT': 'ricaExceptionResult',
            'RICAEXCEPTIONRUNDATE': 'ricaExceptionRunDate',
            'RICAEXCEPTIONRUNTIME': 'ricaExceptionRunTime',
            }
            cursor =  create_connection(MAP)
            query = load_queries.get('GET_EXCEPTION_OUTPUT').format(alert_id=exception.ricaAlertId) 
            result = cursor.execute(query)

            for res in result:
                fields,alert_result = html_extract(res.get("ricaExceptionResult"))
                results = results + alert_result

        except Exception as e:
            print('exception output',e)

        return results


    

    def check_overdue(self,exception):
        current_datetime = datetime.now()
        overdues = self.get_overdues(exception)
        if int(overdues.get("overdue_time")) > 0:
            overdue_minutes = int(overdues.get("overdue_time")) * (int(exception.ricaOverdueCounter)+1)     
            print('overdue_minutes: ',overdue_minutes)
            combined_dt = datetime.combine(exception.ricaRemindNextDate , exception.ricaRemindNextTime )
            print('remind_date: ',combined_dt)
            mins_combined_dt  = combined_dt + timedelta(minutes=overdue_minutes)
            print('time to run: ',mins_combined_dt)
            return current_datetime > mins_combined_dt


    def alerts_generator(self,rule):
        print('RULE: ',rule)
        open_alerts = rica_alerts.objects.exclude(ricaScenarioId=rule, ricaAlertStatus=self.close_status)
        for alert in open_alerts:
            yield alert

    def get_overdues(self,exception):
        # check if assignee is respondent or inves,owner,next_owner

        rule = self.get_rule(exception.ricaScenarioId)
        if exception.ricaAssignee == exception.ricaRespondent:
            return {"overdue_time":rule.ricaRespondentOverdueTime,"overdue_repeat":rule.ricaRespondentOverdueRepeat,'overdue_note':rule.ricaRespondentOverdueNote,"escalation_process":rule.ricaRespondentEscalationProcess}
        elif exception.ricaAssignee == exception.ricaOwner:
            return {"overdue_time":rule.ricaOwnerOverdueTime,"overdue_repeat":rule.ricaOwnerOverdueRepeat,'overdue_note':rule.ricaOwnerOverdueNote,"escalation_process":rule.ricaOwnerEscalationProcess}
        elif exception.ricaAssignee == exception.ricaInvestigator:
            return {"overdue_time":rule.ricaInvestigatorOverdueTime,"overdue_repeat":rule.ricaInvestigatorOverdueRepeat,'overdue_note':rule.ricaInvestigatorOverdueNote,"escalation_process":rule.ricaInvestigatorEscalationProcess}
        else:
            return {"overdue_time":rule.ricaRespondentOverdueTime,"overdue_repeat":rule.ricaRespondentOverdueRepeat,'overdue_note':rule.ricaRespondentOverdueNote,"escalation_process":rule.ricaRespondentEscalationProcess}


    def get_rule(self,rule):
        try:
            rule = ricarule_builder.objects.get(ricaRuleId=rule)
            return rule
        except ObjectDoesNotExist:
            return None 




        

def BotScheduler(interval=30,task=None):
    if task:
        scheduler = BackgroundScheduler()
        scheduler.add_job(task, 'interval', seconds= int(interval))
        scheduler.start()
        print('Bot Running: Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

        try:
            # This is here to simulate application activity (which keeps the main thread alive).
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            scheduler.shutdown()
