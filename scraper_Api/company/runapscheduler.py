import logging
import atexit
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django_apscheduler.models import DjangoJob

from .models import Company, DataSet
from jobs.models import Job

# Configurare logging
logging.basicConfig(level=logging.INFO)

# Global: scheduler-ul
scheduler = BackgroundScheduler(timezone="Europe/Bucharest")
scheduler.add_jobstore(DjangoJobStore(), "default")
PUBLISH_JOB_ID = "publish_pending_jobs"
CLEAN_JOB_ID = "clean_job"
MONTHLY_DELETE_JOB_ID = "delete_monthly_stale_companies"
MAX_PUBLISH_WORKERS = 5
INACTIVE_COMPANY_DAYS = 2
MONTHLY_DELETE_COMPANY_DAYS = 30


def unpublish_jobs(company):
    """Dezpublică toate joburile pentru o companie."""
    jobs = Job.objects.filter(company=company)
    for job in jobs:
        if job.published:
            job.unpublish()  # Presupunem că metoda salvează obiectul


def has_valid_location(job):
    remote_value = (job.remote or "").lower()
    has_remote = "remote" in remote_value
    has_locality = bool(job.city and job.county)
    return has_remote or has_locality


def get_last_company_dataset(company):
    return DataSet.objects.filter(company=company).order_by("-date").first()


def is_company_stale(company, inactive_days, today=None):
    if today is None:
        today = datetime.now().date()

    last_data = get_last_company_dataset(company)
    if not last_data:
        return True, None

    return (today - last_data.date).days >= inactive_days, last_data.date


def is_company_inactive(company, today=None):
    return is_company_stale(company, INACTIVE_COMPANY_DAYS, today=today)


def publish_company_jobs(company):
    logging.info("Verific joburile pentru compania %s", company.company)
    jobs = Job.objects.filter(company=company, published=False)
    published_count = 0

    for job in jobs.iterator():
        if not has_valid_location(job):
            logging.info(
                "Jobul %s de la %s nu are locatie valida",
                job.job_title,
                company.company,
            )
            continue

        job.publish()
        published_count += 1

    logging.info(
        "%s joburi au fost publicate pentru compania %s",
        published_count,
        company.company,
    )
    return published_count


def publish_pending_jobs():
    logging.info("Jobul publish_pending_jobs() a inceput!")
    today = datetime.now().date()
    companies = Company.objects.filter(jobs__published=False).distinct()

    if not companies.exists():
        logging.info("Nu exista companii cu joburi nepublicate.")
        return

    active_companies = []
    for company in companies:
        is_inactive, last_dataset_date = is_company_inactive(company, today=today)
        if is_inactive:
            logging.info(
                "Compania %s este inactiva (ultimul dataset: %s), joburile nu vor fi publicate",
                company.company,
                last_dataset_date,
            )
            continue
        active_companies.append(company)

    if not active_companies:
        logging.info("Nu exista companii active cu joburi nepublicate.")
        return

    total_published = 0
    with ThreadPoolExecutor(max_workers=MAX_PUBLISH_WORKERS) as executor:
        futures = {
            executor.submit(publish_company_jobs, company): company.company
            for company in active_companies
        }

        for future in as_completed(futures):
            company_name = futures[future]
            try:
                total_published += future.result()
            except Exception as exc:
                logging.exception(
                    "Eroare la publicarea joburilor pentru %s: %s",
                    company_name,
                    exc,
                )


def clean():
    """Șterge companiile inactive sau dezpublică joburile vechi."""
    logging.info("Jobul clean() a început!")
    today = datetime.now().date()

    companies = Company.objects.values('company', 'source').distinct()

    for company_data in companies:
        company = Company.objects.filter(
            company=company_data['company']).first()
        if not company:
            continue

        is_inactive, _ = is_company_inactive(company, today=today)
        if is_inactive:
            if company.source:
                company.delete()
                logging.info(f"Compania {company.company} a fost ștearsă.")
            else:
                unpublish_jobs(company)
                logging.info(
                    f"Joburile pentru compania {company.company} au fost dezpublicate.")

    logging.info("Jobul clean() s-a încheiat cu succes!")


def delete_monthly_stale_companies():
    """Șterge companiile care nu au mai adus joburi de 30 de zile."""
    logging.info("Jobul delete_monthly_stale_companies() a început!")
    today = datetime.now().date()
    deleted_companies = 0

    for company in Company.objects.all().iterator():
        is_stale, last_dataset_date = is_company_stale(
            company,
            MONTHLY_DELETE_COMPANY_DAYS,
            today=today,
        )
        if not is_stale:
            continue

        company_name = company.company
        company.delete()
        deleted_companies += 1
        logging.info(
            "Compania %s a fost ștearsă de jobul lunar (ultimul dataset: %s)",
            company_name,
            last_dataset_date,
        )

    logging.info(
        "Jobul delete_monthly_stale_companies() s-a încheiat. Companii șterse: %s",
        deleted_companies,
    )


def start():
    """Pornește APScheduler și adaugă joburile dacă nu există."""
    global scheduler

    logging.info("Programăm jobul 'clean_job' la 01:00 zilnic.")
    scheduler.add_job(
        clean,
        trigger="cron",
        hour=1,
        minute=0,
        id=CLEAN_JOB_ID,
        jobstore="default",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    logging.info("Programăm jobul 'publish_pending_jobs' la 03:00 zilnic.")
    scheduler.add_job(
        publish_pending_jobs,
        trigger="cron",
        hour=3,
        minute=0,
        id=PUBLISH_JOB_ID,
        jobstore="default",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    logging.info("Programăm jobul 'delete_monthly_stale_companies' la 05:00 în prima zi a lunii.")
    scheduler.add_job(
        delete_monthly_stale_companies,
        trigger="cron",
        day=1,
        hour=5,
        minute=0,
        id=MONTHLY_DELETE_JOB_ID,
        jobstore="default",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    # Pornește schedulerul dacă nu e deja activ
    if not scheduler.running:
        try:
            register_events(scheduler)
            scheduler.start()
            logging.info("Schedulerul a fost pornit cu succes!")
        except Exception as e:
            logging.error(f"Eroare la pornirea schedulerului: {e}")
    else:
        logging.info("Schedulerul era deja pornit.")


def stop_scheduler():
    """Oprește în siguranță schedulerul la ieșirea din aplicație."""
    if scheduler.running:
        try:
            scheduler.shutdown()
            logging.info("Scheduler oprit cu succes.")
        except Exception as e:
            logging.error(f"Eroare la oprirea schedulerului: {e}")


# Înregistrăm funcția pentru oprire la shutdown
atexit.register(stop_scheduler)


# Dacă rulezi direct fișierul pentru test:
if __name__ == "__main__":
    logging.info("Pornim schedulerul...")
    start()
    try:
        while True:
            time.sleep(1)  # Menține scriptul activ
    except (KeyboardInterrupt, SystemExit):
        logging.info("Oprire manuală detectată, închidem schedulerul...")
        stop_scheduler()
