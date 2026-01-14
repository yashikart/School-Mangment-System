from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.dependencies import get_current_teacher
from app.models import (
    User, UserRole, Class, ClassStudent, Lesson, Lecture, 
    TimetableSlot, Subject, Announcement, Attendance
)
from app.schemas import (
    ClassResponse, StudentResponse, 
    TimetableSlotResponse, AnnouncementResponse,
    AttendanceResponse, AttendanceBulkCreate
)
from pydantic import BaseModel
from datetime import date, datetime

router = APIRouter(prefix="/teacher", tags=["teacher"])


# ==================== TEACHER DASHBOARD STATS ====================

class TeacherDashboardStats(BaseModel):
    total_classes: int
    total_students: int
    total_lessons: int
    upcoming_lessons: int


@router.get("/dashboard/stats", response_model=TeacherDashboardStats)
def get_teacher_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get teacher dashboard statistics."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Count classes assigned to this teacher
    total_classes = db.query(Class).filter(
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).count()
    
    # Count students in teacher's classes
    classes = db.query(Class).filter(
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).all()
    class_ids = [cls.id for cls in classes]
    total_students = db.query(ClassStudent).filter(
        ClassStudent.class_id.in_(class_ids)
    ).count() if class_ids else 0
    
    # Count total lessons
    total_lessons = db.query(Lesson).filter(
        Lesson.teacher_id == teacher_id,
        Lesson.school_id == school_id
    ).count()
    
    # Count upcoming lessons (today and future)
    today = date.today()
    upcoming_lessons = db.query(Lesson).filter(
        Lesson.teacher_id == teacher_id,
        Lesson.school_id == school_id,
        Lesson.lesson_date >= today
    ).count()
    
    return TeacherDashboardStats(
        total_classes=total_classes,
        total_students=total_students,
        total_lessons=total_lessons,
        upcoming_lessons=upcoming_lessons
    )


# ==================== TEACHER'S CLASSES ====================

@router.get("/classes", response_model=List[ClassResponse])
def get_my_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all classes assigned to the current teacher."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    classes = db.query(Class).filter(
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).all()
    
    # Get subject and teacher names for each class
    result = []
    for cls in classes:
        subject = db.query(Subject).filter(Subject.id == cls.subject_id).first()
        teacher = db.query(User).filter(User.id == cls.teacher_id).first()
        
        result.append(ClassResponse(
            id=cls.id,
            name=cls.name,
            grade=cls.grade,
            subject_id=cls.subject_id,
            teacher_id=cls.teacher_id,
            school_id=cls.school_id,
            academic_year=cls.academic_year,
            subject_name=subject.name if subject else None,
            teacher_name=teacher.name if teacher else None
        ))
    
    return result


@router.get("/classes/{class_id}/students", response_model=List[StudentResponse])
def get_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all students in a specific class (only if teacher is assigned to that class)."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Verify teacher is assigned to this class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you are not assigned to this class"
        )
    
    # Get all students enrolled in this class
    class_students = db.query(ClassStudent).filter(
        ClassStudent.class_id == class_id
    ).all()
    
    result = []
    for cs in class_students:
        student = db.query(User).filter(
            User.id == cs.student_id,
            User.role == UserRole.STUDENT,
            User.is_active == True
        ).first()
        
        if student:
            result.append(StudentResponse(
                id=student.id,
                name=student.name,
                email=student.email,
                grade=student.grade,
                school_id=student.school_id
            ))
    
    return result


# ==================== TEACHER'S LESSONS ====================

@router.get("/lessons")
def get_my_lessons(
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all lessons created by the current teacher."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    query = db.query(Lesson).filter(
        Lesson.teacher_id == teacher_id,
        Lesson.school_id == school_id
    )
    
    if class_id:
        query = query.filter(Lesson.class_id == class_id)
    
    lessons = query.order_by(Lesson.lesson_date.desc()).all()
    
    result = []
    for lesson in lessons:
        class_obj = db.query(Class).filter(Class.id == lesson.class_id).first()
        subject = db.query(Subject).filter(Subject.id == class_obj.subject_id).first() if class_obj else None
        lectures = db.query(Lecture).filter(Lecture.lesson_id == lesson.id).all()
        
        result.append({
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "class_id": lesson.class_id,
            "teacher_id": lesson.teacher_id,
            "lesson_date": lesson.lesson_date.isoformat(),
            "class_name": class_obj.name if class_obj else None,
            "subject_name": subject.name if subject else None,
            "lectures": [
                {
                    "id": l.id,
                    "title": l.title,
                    "content": l.content,
                    "lecture_date": l.lecture_date.isoformat(),
                    "start_time": l.start_time.strftime("%H:%M") if l.start_time else None,
                    "end_time": l.end_time.strftime("%H:%M") if l.end_time else None
                }
                for l in lectures
            ]
        })
    
    return result


# ==================== TEACHER'S TIMETABLE ====================

@router.get("/timetable", response_model=List[TimetableSlotResponse])
def get_my_timetable(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get the current teacher's timetable/schedule."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    timetable_slots = db.query(TimetableSlot).filter(
        TimetableSlot.teacher_id == teacher_id,
        TimetableSlot.school_id == school_id
    ).order_by(TimetableSlot.day_of_week, TimetableSlot.start_time).all()
    
    result = []
    for slot in timetable_slots:
        class_obj = db.query(Class).filter(Class.id == slot.class_id).first()
        subject = db.query(Subject).filter(Subject.id == slot.subject_id).first()
        
        result.append(TimetableSlotResponse(
            id=slot.id,
            class_id=slot.class_id,
            subject_id=slot.subject_id,
            teacher_id=slot.teacher_id,
            school_id=slot.school_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            room=slot.room,
            class_name=class_obj.name if class_obj else None,
            subject_name=subject.name if subject else None,
            teacher_name=current_user.name
        ))
    
    return result


# ==================== TEACHER'S ANNOUNCEMENTS ====================

@router.get("/announcements", response_model=List[AnnouncementResponse])
def get_my_announcements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get announcements targeted to teachers."""
    school_id = current_user.school_id
    
    announcements = db.query(Announcement).filter(
        Announcement.school_id == school_id,
        or_(
            Announcement.target_audience == "TEACHERS",
            Announcement.target_audience == "EVERYONE"
        )
    ).order_by(Announcement.published_at.desc()).all()
    
    result = []
    for ann in announcements:
        creator = db.query(User).filter(User.id == ann.created_by).first()
        
        result.append(AnnouncementResponse(
            id=ann.id,
            title=ann.title,
            content=ann.content,
            target_audience=ann.target_audience,
            school_id=ann.school_id,
            published_at=ann.published_at,
            created_by=ann.created_by,
            created_by_name=creator.name if creator else None
        ))
    
    return result


# ==================== ATTENDANCE MANAGEMENT ====================

@router.get("/attendance", response_model=List[AttendanceResponse])
def get_attendance(
    class_id: int = Query(..., description="Class ID"),
    attendance_date: Optional[date] = Query(None, description="Attendance date (defaults to today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get attendance records for a class on a specific date (defaults to today)."""
    teacher_id = current_user.id
    school_id = current_user.school_id
    
    # Verify teacher is assigned to this class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == teacher_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you are not assigned to this class"
        )
    
    # Default to today if no date provided
    if not attendance_date:
        attendance_date = date.today()
    
    # Get attendance records
    attendance_records = db.query(Attendance).filter(
        Attendance.class_id == class_id,
        Attendance.attendance_date == attendance_date,
        Attendance.school_id == school_id
    ).all()
    
    result = []
    for att in attendance_records:
        student = db.query(User).filter(User.id == att.student_id).first()
        result.append(AttendanceResponse(
            id=att.id,
            student_id=att.student_id,
            class_id=att.class_id,
            teacher_id=att.teacher_id,
            school_id=att.school_id,
            attendance_date=att.attendance_date,
            status=att.status,
            remarks=att.remarks,
            created_at=att.created_at,
            student_name=student.name if student else None,
            class_name=class_obj.name
        ))
    
    return result


@router.post("/attendance/mark", response_model=List[AttendanceResponse])
def mark_attendance(
    attendance_data: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Mark attendance for multiple students in a class."""
    try:
        teacher_id = current_user.id
        school_id = current_user.school_id
        
        # Verify teacher is assigned to this class
        class_obj = db.query(Class).filter(
            Class.id == attendance_data.class_id,
            Class.teacher_id == teacher_id,
            Class.school_id == school_id
        ).first()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found or you are not assigned to this class"
            )
        
        # Validate status values
        valid_statuses = ["PRESENT", "ABSENT", "LATE", "EXCUSED"]
        
        # Check if attendance already exists for this date
        existing_attendance = db.query(Attendance).filter(
            Attendance.class_id == attendance_data.class_id,
            Attendance.attendance_date == attendance_data.attendance_date,
            Attendance.school_id == school_id
        ).all()
        
        # Delete existing attendance for this date/class
        for existing in existing_attendance:
            db.delete(existing)
        
        # Create new attendance records
        created_records = []
        for record in attendance_data.attendance_records:
            if record.status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {record.status}. Must be one of: {', '.join(valid_statuses)}"
                )
            
            # Verify student is enrolled in this class
            enrollment = db.query(ClassStudent).filter(
                ClassStudent.class_id == attendance_data.class_id,
                ClassStudent.student_id == record.student_id
            ).first()
            
            if not enrollment:
                continue  # Skip students not enrolled in this class
            
            attendance = Attendance(
                student_id=record.student_id,
                class_id=attendance_data.class_id,
                teacher_id=teacher_id,
                school_id=school_id,
                attendance_date=attendance_data.attendance_date,
                status=record.status,
                remarks=record.remarks
            )
            
            db.add(attendance)
            created_records.append(attendance)
        
        db.commit()
        
        # Refresh and return created records
        result = []
        for att in created_records:
            db.refresh(att)
            student = db.query(User).filter(User.id == att.student_id).first()
            result.append(AttendanceResponse(
                id=att.id,
                student_id=att.student_id,
                class_id=att.class_id,
                teacher_id=att.teacher_id,
                school_id=att.school_id,
                attendance_date=att.attendance_date,
                status=att.status,
                remarks=att.remarks,
                created_at=att.created_at,
                student_name=student.name if student else None,
                class_name=class_obj.name
            ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error marking attendance: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking attendance: {str(e)}"
        )

