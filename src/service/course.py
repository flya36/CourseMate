from src.schema.course import CourseCreate
FAKE_COURSES = []

# 创建新课程
def create_course(course_create:CourseCreate):
    new_course = course_create.model_dump()
    new_course['course_id'] = len(FAKE_COURSES) + 1
    FAKE_COURSES.append(new_course)
    return new_course

# 查询现有课程
def list_courses():
    return FAKE_COURSES