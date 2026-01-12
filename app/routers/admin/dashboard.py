"""
School Admin Dashboard API endpoints.
All endpoints are filtered by school_id to ensure data isolation.
"""

from typing import List, Optional
from datetime import datetime, date, time, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.database import get_db
from app.dependencies import get_current_admin
from app.models import (
    User, UserRole, School, Subject, Class, ClassStudent,
    StudentParent, Lesson, Lecture, TimetableSlot,
    Holiday, Event, Announcement
)
from app.schemas import (
    TeacherCreate, TeacherResponse, TeacherUpdate,
    StudentCreate, StudentResponse, StudentUpdate,
    ParentCreate, ParentResponse, ParentUpdate, ExcelUploadResponse,
    SubjectCreate, SubjectResponse, ClassCreate, ClassResponse,
    TimetableSlotCreate, TimetableSlotResponse,
    HolidayCreate, HolidayResponse, EventCreate, EventResponse,
    AnnouncementCreate, AnnouncementResponse, DashboardStatsResponse,
    StudentParentLinkCreate, StudentParentLinkResponse,
    StudentWithParentsResponse, ParentWithStudentsResponse,
    ParentStudentStatsResponse
)
from app.utils.password_generator import generate_unique_password
from app.utils.excel_upload import upload_teachers_excel, upload_students_excel, upload_parents_excel
from app.utils.excel_upload_combined import upload_students_parents_combined_excel
from app.auth import get_password_hash
from app.email_service import send_login_credentials_email

router = APIRouter(prefix="/admin", tags=["school-admin"])


# ==================== DASHBOARD STATS ====================

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get dashboard statistics for School Admin."""
    try:
        school_id = current_user.school_id
        
        # Count teachers
        total_teachers = db.query(User).filter(
            User.school_id == school_id,
            User.role == UserRole.TEACHER,
            User.is_active == True
        ).count()
        
        # Count students
        total_students = db.query(User).filter(
            User.school_id == school_id,
            User.role == UserRole.STUDENT,
            User.is_active == True
        ).count()
        
        # Count parents
        total_parents = db.query(User).filter(
            User.school_id == school_id,
            User.role == UserRole.PARENT,
            User.is_active == True
        ).count()
        
        # Count classes (handle case where table might not exist)
        try:
            total_classes = db.query(Class).filter(Class.school_id == school_id).count()
        except Exception:
            total_classes = 0
        
        # Count lessons (handle case where table might not exist)
        try:
            total_lessons = db.query(Lesson).filter(Lesson.school_id == school_id).count()
        except Exception:
            total_lessons = 0
        
        # Today's classes (classes with lessons today)
        today = date.today()
        try:
            todays_classes = db.query(Lesson).filter(
                Lesson.school_id == school_id,
                Lesson.lesson_date == today
            ).count()
        except Exception:
            todays_classes = 0
        
        # Upcoming holidays (next 30 days)
        try:
            upcoming_holidays = db.query(Holiday).filter(
                Holiday.school_id == school_id,
                Holiday.start_date >= today,
                Holiday.start_date <= date.today().replace(day=1) if date.today().month < 12 else date.today().replace(year=date.today().year + 1, month=1, day=1)
            ).count()
        except Exception:
            upcoming_holidays = 0
        
        # Upcoming events (next 30 days)
        try:
            upcoming_events = db.query(Event).filter(
                Event.school_id == school_id,
                Event.event_date >= today,
                Event.event_date <= date.today().replace(day=1) if date.today().month < 12 else date.today().replace(year=date.today().year + 1, month=1, day=1)
            ).count()
        except Exception:
            upcoming_events = 0
        
        return DashboardStatsResponse(
            total_teachers=total_teachers,
            total_students=total_students,
            total_parents=total_parents,
            total_classes=total_classes,
            total_lessons=total_lessons,
            todays_classes=todays_classes,
            upcoming_holidays=upcoming_holidays,
            upcoming_events=upcoming_events
        )
    except Exception as e:
        print(f"Error in get_dashboard_stats: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard statistics: {str(e)}"
        )


# ==================== TEACHERS MANAGEMENT ====================

@router.get("/teachers", response_model=List[TeacherResponse])
def get_teachers(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all teachers in the school."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.TEACHER,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    teachers = query.all()
    return [TeacherResponse(id=t.id, name=t.name, email=t.email, subject=t.subject, school_id=t.school_id) for t in teachers]


@router.post("/teachers", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new teacher."""
    school_id = current_user.school_id
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == teacher_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Generate unique password
    password = generate_unique_password(db, teacher_data.email, teacher_data.name, UserRole.TEACHER.value, school_id)
    hashed_password = get_password_hash(password)
    
    # Create teacher
    teacher = User(
        name=teacher_data.name,
        email=teacher_data.email,
        password=hashed_password,
        role=UserRole.TEACHER,
        school_id=school_id,
        is_active=True,
        subject=teacher_data.subject
    )
    
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    
    # Send login credentials email
    try:
        await send_login_credentials_email(db, teacher, password, UserRole.TEACHER.value)
    except Exception as e:
        print(f"Warning: Failed to send email to {teacher.email}: {str(e)}")
    
    return TeacherResponse(id=teacher.id, name=teacher.name, email=teacher.email, subject=teacher_data.subject, school_id=teacher.school_id)


@router.post("/teachers/upload-excel", response_model=ExcelUploadResponse)
async def upload_teachers_excel_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Upload teachers from Excel file."""
    school_id = current_user.school_id
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    result = await upload_teachers_excel(file, school_id, db)
    
    return ExcelUploadResponse(
        success=True,
        message=f"Upload completed. {result.success_count} teachers created, {len(result.failed_rows)} failed.",
        success_count=result.success_count,
        failed_count=len(result.failed_rows),
        failed_rows=result.failed_rows
    )


@router.put("/teachers/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a teacher's information."""
    school_id = current_user.school_id
    
    # Get teacher
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.school_id == school_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found or does not belong to this school"
        )
    
    # Update fields if provided
    if teacher_data.name is not None:
        teacher.name = teacher_data.name
    
    if teacher_data.email is not None and teacher_data.email != teacher.email:
        # Check if new email already exists
        existing_user = db.query(User).filter(
            User.email == teacher_data.email,
            User.id != teacher_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        teacher.email = teacher_data.email
    
    if teacher_data.subject is not None:
        teacher.subject = teacher_data.subject
    
    db.commit()
    db.refresh(teacher)
    
    return TeacherResponse(
        id=teacher.id,
        name=teacher.name,
        email=teacher.email,
        subject=teacher.subject,
        school_id=teacher.school_id
    )


@router.delete("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete (deactivate) a teacher."""
    school_id = current_user.school_id
    
    # Get teacher
    teacher = db.query(User).filter(
        User.id == teacher_id,
        User.school_id == school_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found or does not belong to this school"
        )
    
    # Soft delete: set is_active to False
    teacher.is_active = False
    db.commit()
    
    return None


# ==================== STUDENTS MANAGEMENT ====================

@router.get("/students", response_model=List[StudentResponse])
def get_students(
    search: Optional[str] = Query(None),
    grade: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all students in the school."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    students = query.all()
    return [StudentResponse(id=s.id, name=s.name, email=s.email, grade=grade, school_id=s.school_id) for s in students]


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new student."""
    school_id = current_user.school_id
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == student_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Generate unique password
    password = generate_unique_password(db, student_data.email, student_data.name, UserRole.STUDENT.value, school_id)
    hashed_password = get_password_hash(password)
    
    # Create student
    student = User(
        name=student_data.name,
        email=student_data.email,
        password=hashed_password,
        role=UserRole.STUDENT,
        school_id=school_id,
        is_active=True
    )
    
    db.add(student)
    db.flush()
    
    # Link to parent if provided
    if student_data.parent_email:
        parent = db.query(User).filter(
            User.email == student_data.parent_email,
            User.role == UserRole.PARENT,
            User.school_id == school_id
        ).first()
        
        if parent:
            student_parent = StudentParent(
                student_id=student.id,
                parent_id=parent.id,
                relationship_type="Parent"
            )
            db.add(student_parent)
    
    db.commit()
    db.refresh(student)
    
    # Send login credentials email
    try:
        await send_login_credentials_email(db, student, password, UserRole.STUDENT.value)
    except Exception as e:
        print(f"Warning: Failed to send email to {student.email}: {str(e)}")
    
    return StudentResponse(id=student.id, name=student.name, email=student.email, grade=student_data.grade, school_id=student.school_id)


@router.post("/students/upload-excel", response_model=ExcelUploadResponse)
async def upload_students_excel_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Upload students from Excel file."""
    school_id = current_user.school_id
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    result = await upload_students_excel(file, school_id, db)
    
    return ExcelUploadResponse(
        success=True,
        message=f"Upload completed. {result.success_count} students created, {len(result.failed_rows)} failed.",
        success_count=result.success_count,
        failed_count=len(result.failed_rows),
        failed_rows=result.failed_rows
    )


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a student's information."""
    school_id = current_user.school_id
    
    # Get student
    student = db.query(User).filter(
        User.id == student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to this school"
        )
    
    # Update fields if provided
    if student_data.name is not None:
        student.name = student_data.name
    
    if student_data.email is not None and student_data.email != student.email:
        # Check if new email already exists
        existing_user = db.query(User).filter(
            User.email == student_data.email,
            User.id != student_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        student.email = student_data.email
    
    db.commit()
    db.refresh(student)
    
    return StudentResponse(
        id=student.id,
        name=student.name,
        email=student.email,
        grade=student_data.grade,
        school_id=student.school_id
    )


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete (deactivate) a student."""
    school_id = current_user.school_id
    
    # Get student
    student = db.query(User).filter(
        User.id == student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to this school"
        )
    
    # Soft delete: set is_active to False
    student.is_active = False
    db.commit()
    
    return None


# ==================== PARENTS MANAGEMENT ====================

@router.get("/parents", response_model=List[ParentResponse])
def get_parents(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all parents in the school."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    parents = query.all()
    return [ParentResponse(id=p.id, name=p.name, email=p.email, school_id=p.school_id) for p in parents]


@router.post("/parents", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
async def create_parent(
    parent_data: ParentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new parent."""
    school_id = current_user.school_id
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == parent_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Generate unique password
    password = generate_unique_password(db, parent_data.email, parent_data.name, UserRole.PARENT.value, school_id)
    hashed_password = get_password_hash(password)
    
    # Create parent
    parent = User(
        name=parent_data.name,
        email=parent_data.email,
        password=hashed_password,
        role=UserRole.PARENT,
        school_id=school_id,
        is_active=True
    )
    
    db.add(parent)
    db.flush()
    
    # Link to student if provided
    if parent_data.student_email:
        student = db.query(User).filter(
            User.email == parent_data.student_email,
            User.role == UserRole.STUDENT,
            User.school_id == school_id
        ).first()
        
        if student:
            student_parent = StudentParent(
                student_id=student.id,
                parent_id=parent.id,
                relationship_type="Parent"
            )
            db.add(student_parent)
    
    db.commit()
    db.refresh(parent)
    
    # Send login credentials email
    try:
        await send_login_credentials_email(db, parent, password, UserRole.PARENT.value)
    except Exception as e:
        print(f"Warning: Failed to send email to {parent.email}: {str(e)}")
    
    return ParentResponse(id=parent.id, name=parent.name, email=parent.email, school_id=parent.school_id)


@router.post("/parents/upload-excel", response_model=ExcelUploadResponse)
async def upload_parents_excel_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Upload parents from Excel file."""
    school_id = current_user.school_id
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    result = await upload_parents_excel(file, school_id, db)
    
    return ExcelUploadResponse(
        success=True,
        message=f"Upload completed. {result.success_count} parents created, {len(result.failed_rows)} failed.",
        success_count=result.success_count,
        failed_count=len(result.failed_rows),
        failed_rows=result.failed_rows
    )


@router.put("/parents/{parent_id}", response_model=ParentResponse)
def update_parent(
    parent_id: int,
    parent_data: ParentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a parent's information."""
    school_id = current_user.school_id
    
    # Get parent
    parent = db.query(User).filter(
        User.id == parent_id,
        User.school_id == school_id,
        User.role == UserRole.PARENT
    ).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found or does not belong to this school"
        )
    
    # Update fields if provided
    if parent_data.name is not None:
        parent.name = parent_data.name
    
    if parent_data.email is not None and parent_data.email != parent.email:
        # Check if new email already exists
        existing_user = db.query(User).filter(
            User.email == parent_data.email,
            User.id != parent_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        parent.email = parent_data.email
    
    db.commit()
    db.refresh(parent)
    
    return ParentResponse(
        id=parent.id,
        name=parent.name,
        email=parent.email,
        school_id=parent.school_id
    )


@router.delete("/parents/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete (deactivate) a parent."""
    school_id = current_user.school_id
    
    # Get parent
    parent = db.query(User).filter(
        User.id == parent_id,
        User.school_id == school_id,
        User.role == UserRole.PARENT
    ).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found or does not belong to this school"
        )
    
    # Soft delete: set is_active to False
    parent.is_active = False
    db.commit()
    
    return None


# ==================== SUBJECTS MANAGEMENT ====================

@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all subjects in the school."""
    school_id = current_user.school_id
    
    subjects = db.query(Subject).filter(Subject.school_id == school_id).all()
    return subjects


@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject_data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new subject."""
    school_id = current_user.school_id
    
    subject = Subject(
        name=subject_data.name,
        code=subject_data.code,
        school_id=school_id
    )
    
    db.add(subject)
    db.commit()
    db.refresh(subject)
    
    return subject


# ==================== CLASSES MANAGEMENT ====================

@router.get("/classes", response_model=List[ClassResponse])
def get_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all classes in the school."""
    school_id = current_user.school_id
    
    classes = db.query(Class).filter(Class.school_id == school_id).all()
    return classes


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a new class."""
    school_id = current_user.school_id
    
    # Verify teacher belongs to this school
    teacher = db.query(User).filter(
        User.id == class_data.teacher_id,
        User.school_id == school_id,
        User.role == UserRole.TEACHER
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher not found or does not belong to this school"
        )
    
    # Verify subject belongs to this school
    subject = db.query(Subject).filter(
        Subject.id == class_data.subject_id,
        Subject.school_id == school_id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject not found or does not belong to this school"
        )
    
    class_obj = Class(
        name=class_data.name,
        grade=class_data.grade,
        subject_id=class_data.subject_id,
        teacher_id=class_data.teacher_id,
        school_id=school_id,
        academic_year=class_data.academic_year
    )
    
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)
    
    return class_obj


@router.post("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_201_CREATED)
def assign_student_to_class(
    class_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Assign a student to a class."""
    school_id = current_user.school_id
    
    # Verify class belongs to school
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.school_id == school_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify student belongs to school
    student = db.query(User).filter(
        User.id == student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if already assigned
    existing = db.query(ClassStudent).filter(
        ClassStudent.class_id == class_id,
        ClassStudent.student_id == student_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already assigned to this class"
        )
    
    class_student = ClassStudent(
        class_id=class_id,
        student_id=student_id
    )
    
    db.add(class_student)
    db.commit()
    
    return {"success": True, "message": "Student assigned to class"}


# ==================== TIMETABLE MANAGEMENT ====================

@router.get("/timetable", response_model=List[TimetableSlotResponse])
def get_timetable(
    class_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get timetable slots."""
    school_id = current_user.school_id
    
    query = db.query(TimetableSlot).filter(TimetableSlot.school_id == school_id)
    
    if class_id:
        query = query.filter(TimetableSlot.class_id == class_id)
    
    slots = query.all()
    return slots


@router.post("/timetable", response_model=TimetableSlotResponse, status_code=status.HTTP_201_CREATED)
def create_timetable_slot(
    slot_data: TimetableSlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a timetable slot."""
    school_id = current_user.school_id
    
    # Parse time strings
    start_time_obj = datetime.strptime(slot_data.start_time, "%H:%M").time()
    end_time_obj = datetime.strptime(slot_data.end_time, "%H:%M").time()
    
    # Check for conflicts (same teacher, same day, overlapping time)
    conflicting = db.query(TimetableSlot).filter(
        TimetableSlot.school_id == school_id,
        TimetableSlot.teacher_id == slot_data.teacher_id,
        TimetableSlot.day_of_week == slot_data.day_of_week,
        or_(
            and_(TimetableSlot.start_time <= start_time_obj, TimetableSlot.end_time > start_time_obj),
            and_(TimetableSlot.start_time < end_time_obj, TimetableSlot.end_time >= end_time_obj),
            and_(TimetableSlot.start_time >= start_time_obj, TimetableSlot.end_time <= end_time_obj)
        )
    ).first()
    
    if conflicting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher has a conflicting schedule at this time"
        )
    
    slot = TimetableSlot(
        class_id=slot_data.class_id,
        subject_id=slot_data.subject_id,
        teacher_id=slot_data.teacher_id,
        school_id=school_id,
        day_of_week=slot_data.day_of_week,
        start_time=start_time_obj,
        end_time=end_time_obj,
        room=slot_data.room
    )
    
    db.add(slot)
    db.commit()
    db.refresh(slot)
    
    return TimetableSlotResponse(
        id=slot.id,
        class_id=slot.class_id,
        subject_id=slot.subject_id,
        teacher_id=slot.teacher_id,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time.strftime("%H:%M"),
        end_time=slot.end_time.strftime("%H:%M"),
        room=slot.room
    )


# ==================== HOLIDAYS & EVENTS ====================

@router.get("/holidays", response_model=List[HolidayResponse])
def get_holidays(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all holidays."""
    school_id = current_user.school_id
    
    holidays = db.query(Holiday).filter(Holiday.school_id == school_id).order_by(Holiday.start_date).all()
    return holidays


@router.post("/holidays", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
def create_holiday(
    holiday_data: HolidayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a holiday."""
    school_id = current_user.school_id
    
    holiday = Holiday(
        name=holiday_data.name,
        start_date=holiday_data.start_date,
        end_date=holiday_data.end_date,
        description=holiday_data.description,
        school_id=school_id
    )
    
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    
    return holiday


@router.get("/events", response_model=List[EventResponse])
def get_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all events."""
    school_id = current_user.school_id
    
    events = db.query(Event).filter(Event.school_id == school_id).order_by(Event.event_date).all()
    return events


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create an event."""
    school_id = current_user.school_id
    
    event_time_obj = None
    if event_data.event_time:
        event_time_obj = datetime.strptime(event_data.event_time, "%H:%M").time()
    
    event = Event(
        title=event_data.title,
        description=event_data.description,
        event_date=event_data.event_date,
        event_time=event_time_obj,
        event_type=event_data.event_type,
        school_id=school_id
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        event_time=event.event_time.strftime("%H:%M") if event.event_time else None,
        event_type=event.event_type,
        school_id=event.school_id
    )


# ==================== ANNOUNCEMENTS ====================

@router.get("/announcements", response_model=List[AnnouncementResponse])
def get_announcements(
    target_audience: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all announcements."""
    school_id = current_user.school_id
    
    query = db.query(Announcement).filter(Announcement.school_id == school_id)
    
    if target_audience:
        query = query.filter(Announcement.target_audience == target_audience)
    
    announcements = query.order_by(Announcement.published_at.desc()).all()
    return announcements


@router.post("/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement_data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create an announcement."""
    school_id = current_user.school_id
    
    valid_audiences = ["TEACHERS", "STUDENTS", "PARENTS", "EVERYONE"]
    if announcement_data.target_audience not in valid_audiences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"target_audience must be one of: {', '.join(valid_audiences)}"
        )
    
    announcement = Announcement(
        title=announcement_data.title,
        content=announcement_data.content,
        target_audience=announcement_data.target_audience,
        school_id=school_id,
        created_by=current_user.id
    )
    
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    
    return announcement


# ==================== LESSONS & LECTURES (VIEW MODE) ====================

@router.get("/lessons", response_model=List[dict])
def get_lessons(
    class_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all lessons (view mode for admin)."""
    school_id = current_user.school_id
    
    query = db.query(Lesson).filter(Lesson.school_id == school_id)
    
    if class_id:
        query = query.filter(Lesson.class_id == class_id)
    
    lessons = query.order_by(Lesson.lesson_date.desc()).all()
    
    result = []
    for lesson in lessons:
        lectures = db.query(Lecture).filter(Lecture.lesson_id == lesson.id).all()
        result.append({
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "class_id": lesson.class_id,
            "teacher_id": lesson.teacher_id,
            "lesson_date": lesson.lesson_date.isoformat(),
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


# ==================== PARENT-STUDENT MAPPING MANAGEMENT ====================

@router.get("/students/{student_id}/parents", response_model=List[StudentParentLinkResponse])
def get_student_parents(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all parents linked to a specific student."""
    school_id = current_user.school_id
    
    # Verify student belongs to this school
    student = db.query(User).filter(
        User.id == student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to this school"
        )
    
    # Get all parent-student links for this student
    links = db.query(StudentParent).filter(
        StudentParent.student_id == student_id
    ).all()
    
    result = []
    for link in links:
        parent = db.query(User).filter(User.id == link.parent_id).first()
        if parent and parent.school_id == school_id:
            result.append(StudentParentLinkResponse(
                id=link.id,
                student_id=link.student_id,
                parent_id=link.parent_id,
                relationship_type=link.relationship_type,
                student_name=student.name,
                student_email=student.email,
                parent_name=parent.name,
                parent_email=parent.email
            ))
    
    return result


@router.get("/parents/{parent_id}/students", response_model=List[StudentParentLinkResponse])
def get_parent_students(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all students linked to a specific parent."""
    school_id = current_user.school_id
    
    # Verify parent belongs to this school
    parent = db.query(User).filter(
        User.id == parent_id,
        User.school_id == school_id,
        User.role == UserRole.PARENT
    ).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found or does not belong to this school"
        )
    
    # Get all parent-student links for this parent
    links = db.query(StudentParent).filter(
        StudentParent.parent_id == parent_id
    ).all()
    
    result = []
    for link in links:
        student = db.query(User).filter(User.id == link.student_id).first()
        if student and student.school_id == school_id:
            result.append(StudentParentLinkResponse(
                id=link.id,
                student_id=link.student_id,
                parent_id=link.parent_id,
                relationship_type=link.relationship_type,
                student_name=student.name,
                student_email=student.email,
                parent_name=parent.name,
                parent_email=parent.email
            ))
    
    return result


@router.post("/parent-student/link", response_model=StudentParentLinkResponse, status_code=status.HTTP_201_CREATED)
def create_parent_student_link(
    link_data: StudentParentLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a link between a parent and a student."""
    school_id = current_user.school_id
    
    # Verify student belongs to this school
    student = db.query(User).filter(
        User.id == link_data.student_id,
        User.school_id == school_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student not found or does not belong to this school"
        )
    
    # Verify parent belongs to this school
    parent = db.query(User).filter(
        User.id == link_data.parent_id,
        User.school_id == school_id,
        User.role == UserRole.PARENT
    ).first()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent not found or does not belong to this school"
        )
    
    # Check if link already exists
    existing_link = db.query(StudentParent).filter(
        StudentParent.student_id == link_data.student_id,
        StudentParent.parent_id == link_data.parent_id
    ).first()
    
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link between this parent and student already exists"
        )
    
    # Create the link
    link = StudentParent(
        student_id=link_data.student_id,
        parent_id=link_data.parent_id,
        relationship_type=link_data.relationship_type
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    
    return StudentParentLinkResponse(
        id=link.id,
        student_id=link.student_id,
        parent_id=link.parent_id,
        relationship_type=link.relationship_type,
        student_name=student.name,
        student_email=student.email,
        parent_name=parent.name,
        parent_email=parent.email
    )


@router.delete("/parent-student/link/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parent_student_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a parent-student link."""
    school_id = current_user.school_id
    
    # Get the link
    link = db.query(StudentParent).filter(StudentParent.id == link_id).first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Verify both student and parent belong to this school
    student = db.query(User).filter(User.id == link.student_id).first()
    parent = db.query(User).filter(User.id == link.parent_id).first()
    
    if not student or not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student or parent not found"
        )
    
    if student.school_id != school_id or parent.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete link: student or parent does not belong to this school"
        )
    
    db.delete(link)
    db.commit()
    
    return None


@router.get("/students-with-parents", response_model=List[StudentWithParentsResponse])
def get_students_with_parents(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all students with their linked parents."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    students = query.all()
    result = []
    
    for student in students:
        # Get linked parents
        links = db.query(StudentParent).filter(
            StudentParent.student_id == student.id
        ).all()
        
        linked_parents = []
        for link in links:
            parent = db.query(User).filter(User.id == link.parent_id).first()
            if parent and parent.school_id == school_id:
                linked_parents.append({
                    "id": parent.id,
                    "name": parent.name,
                    "email": parent.email,
                    "relationship_type": link.relationship_type
                })
        
        result.append(StudentWithParentsResponse(
            id=student.id,
            name=student.name,
            email=student.email,
            grade=None,  # Grade would need to be stored separately or fetched from classes
            school_id=student.school_id,
            linked_parents=linked_parents
        ))
    
    return result


@router.get("/parents-with-students", response_model=List[ParentWithStudentsResponse])
def get_parents_with_students(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all parents with their linked students."""
    school_id = current_user.school_id
    
    query = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    )
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
    
    parents = query.all()
    result = []
    
    for parent in parents:
        # Get linked students
        links = db.query(StudentParent).filter(
            StudentParent.parent_id == parent.id
        ).all()
        
        linked_students = []
        for link in links:
            student = db.query(User).filter(User.id == link.student_id).first()
            if student and student.school_id == school_id:
                linked_students.append({
                    "id": student.id,
                    "name": student.name,
                    "email": student.email,
                    "relationship_type": link.relationship_type
                })
        
        result.append(ParentWithStudentsResponse(
            id=parent.id,
            name=parent.name,
            email=parent.email,
            school_id=parent.school_id,
            linked_students=linked_students
        ))
    
    return result


@router.get("/parent-student/stats", response_model=ParentStudentStatsResponse)
def get_parent_student_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get statistics about parent-student relationships."""
    school_id = current_user.school_id
    
    # Count total parents and students
    total_parents = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    ).count()
    
    total_students = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).count()
    
    # Get all links for this school
    all_students = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.STUDENT,
        User.is_active == True
    ).all()
    
    all_parents = db.query(User).filter(
        User.school_id == school_id,
        User.role == UserRole.PARENT,
        User.is_active == True
    ).all()
    
    # Count linked and unlinked
    linked_student_ids = set()
    linked_parent_ids = set()
    
    for student in all_students:
        links = db.query(StudentParent).filter(
            StudentParent.student_id == student.id
        ).all()
        if links:
            linked_student_ids.add(student.id)
            for link in links:
                parent = db.query(User).filter(User.id == link.parent_id).first()
                if parent and parent.school_id == school_id:
                    linked_parent_ids.add(parent.id)
    
    unlinked_students = total_students - len(linked_student_ids)
    unlinked_parents = total_parents - len(linked_parent_ids)
    
    # Count total links
    total_links = db.query(StudentParent).join(User, StudentParent.student_id == User.id).filter(
        User.school_id == school_id
    ).count()
    
    # Students per parent (for chart)
    students_per_parent = []
    for parent in all_parents:
        links = db.query(StudentParent).filter(
            StudentParent.parent_id == parent.id
        ).count()
        if links > 0:
            students_per_parent.append({
                "parent_name": parent.name,
                "student_count": links
            })
    
    # Parents per student (for chart)
    parents_per_student = []
    for student in all_students:
        links = db.query(StudentParent).filter(
            StudentParent.student_id == student.id
        ).count()
        if links > 0:
            parents_per_student.append({
                "student_name": student.name,
                "parent_count": links
            })
    
    return ParentStudentStatsResponse(
        total_parents=total_parents,
        total_students=total_students,
        unlinked_students=unlinked_students,
        unlinked_parents=unlinked_parents,
        total_links=total_links,
        students_per_parent=students_per_parent,
        parents_per_student=parents_per_student
    )


@router.post("/parent-student/upload-combined-excel", response_model=ExcelUploadResponse)
async def upload_students_parents_combined_excel_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Upload students and parents from a combined Excel file.
    Expected columns: Student Name, Student Email, Grade/Class, Parent Name, Parent Email
    """
    school_id = current_user.school_id
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    result = await upload_students_parents_combined_excel(file, school_id, db)
    
    return ExcelUploadResponse(
        success=True,
        message=f"Upload completed. {result.success_count} records processed, {len(result.failed_rows)} failed.",
        success_count=result.success_count,
        failed_count=len(result.failed_rows),
        failed_rows=result.failed_rows
    )
