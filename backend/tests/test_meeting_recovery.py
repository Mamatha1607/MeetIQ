from datetime import datetime, timedelta, timezone

from app.models.meeting import Meeting, MeetingStatus
from app.services.meeting_recovery import find_stale_meetings

from app.services.meeting_recovery import update_meeting_heartbeat
import threading
import time
import uuid


from app.services.meeting_recovery import run_heartbeat

def test_find_stale_processing_meetings(client, db_session):
    now = datetime.now(timezone.utc)

    # Worker stopped sending heartbeats 90 minutes ago.
    stale_meeting = Meeting(
        title="Stuck Meeting",
        status=MeetingStatus.PROCESSING,
        processing_started_at=now - timedelta(minutes=90),
        last_heartbeat_at=now - timedelta(minutes=90),
    )

    # Worker started 90 minutes ago but is still sending heartbeats.
    active_meeting = Meeting(
        title="Active Meeting",
        status=MeetingStatus.PROCESSING,
        processing_started_at=now - timedelta(minutes=90),
        last_heartbeat_at=now - timedelta(minutes=5),
    )

    # Completed meetings must never be considered stale.
    completed_meeting = Meeting(
        title="Completed Meeting",
        status=MeetingStatus.COMPLETED,
        processing_started_at=now - timedelta(minutes=120),
        last_heartbeat_at=now - timedelta(minutes=90),
    )

    db_session.add_all([
        stale_meeting,
        active_meeting,
        completed_meeting,
    ])
    db_session.commit()

    results = find_stale_meetings(
        db=db_session,
        timeout_minutes=60,
    )

    result_ids = {meeting.id for meeting in results}

    assert stale_meeting.id in result_ids
    assert active_meeting.id not in result_ids
    assert completed_meeting.id not in result_ids
    assert len(results) == 1
def test_update_meeting_heartbeat(client, db_session):
    old_heartbeat = datetime.now(timezone.utc) - timedelta(minutes=10)
    attempt_id = uuid.uuid4()

    meeting = Meeting(
        title="Heartbeat Test",
        status=MeetingStatus.PROCESSING,
        processing_started_at=old_heartbeat,
        last_heartbeat_at=old_heartbeat,
        processing_attempt_id=attempt_id,
    )

    db_session.add(meeting)
    db_session.commit()

    updated = update_meeting_heartbeat(
        db=db_session,
        meeting_id=meeting.id,
        attempt_id=attempt_id,
    )

    assert updated is True

    db_session.refresh(meeting)

    assert meeting.last_heartbeat_at > old_heartbeat
    assert meeting.status == MeetingStatus.PROCESSING
def test_heartbeat_thread_stops():
    """
    Verify that the heartbeat thread stops when signaled.
    """

    stop_event = threading.Event()
    attempt_id = uuid.uuid4()

    thread = threading.Thread(
        target=run_heartbeat,
        kwargs={
            "meeting_id": uuid.uuid4(),
            "attempt_id": attempt_id,
            "session_factory": lambda: None,
            "stop_event": stop_event,
            "interval_seconds": 30,
        },
        daemon=True,
    )

    thread.start()

    # Stop before the first heartbeat is due.
    stop_event.set()
    thread.join(timeout=2)

    assert not thread.is_alive()
def test_heartbeat_updates_database(
    client,
    db_session,
    test_session_factory,
):
    now = datetime.now(timezone.utc)
    attempt_id = uuid.uuid4()

    meeting = Meeting(
        title="Background Heartbeat Test",
        status=MeetingStatus.PROCESSING,
        processing_started_at=now,
        last_heartbeat_at=now,
        processing_attempt_id=attempt_id,
    )

    db_session.add(meeting)
    db_session.commit()

    meeting_id = meeting.id

    stop_event = threading.Event()

    thread = threading.Thread(
        target=run_heartbeat,
        kwargs={
            "meeting_id": meeting_id,
            "attempt_id": attempt_id,
            "session_factory": test_session_factory,
            "stop_event": stop_event,
            "interval_seconds": 1,
        },
        daemon=True,
    )

    thread.start()

    try:
        time.sleep(2.5)
    finally:
        stop_event.set()
        thread.join(timeout=5)

    assert not thread.is_alive()

    db_session.expire_all()
    updated_meeting = db_session.get(Meeting, meeting_id)

    assert updated_meeting.last_heartbeat_at > now
def test_outdated_worker_cannot_update_heartbeat(client, db_session):
    now = datetime.now(timezone.utc)

    current_attempt_id = uuid.uuid4()
    outdated_attempt_id = uuid.uuid4()

    meeting = Meeting(
        title="Ownership Protection Test",
        status=MeetingStatus.PROCESSING,
        processing_started_at=now,
        last_heartbeat_at=now,
        processing_attempt_id=current_attempt_id,
    )

    db_session.add(meeting)
    db_session.commit()

    meeting_id = meeting.id

    # Simulate an outdated worker attempting a heartbeat.
    updated = update_meeting_heartbeat(
        db=db_session,
        meeting_id=meeting_id,
        attempt_id=outdated_attempt_id,
    )

    assert updated is False

    db_session.refresh(meeting)

    # The rejected heartbeat must not change the timestamp.
    assert meeting.last_heartbeat_at == now
    assert meeting.processing_attempt_id == current_attempt_id