from boac import db
from boac.models.base import Base
from boac.models.db_relationships import student_athletes
from boac.models.student import Student
from sqlalchemy import func


class Athletics(Base):
    __tablename__ = 'athletics'

    group_code = db.Column(db.String(80), nullable=False, primary_key=True)
    group_name = db.Column(db.String(255))
    team_code = db.Column(db.String(80))
    team_name = db.Column(db.String(255))
    athletes = db.relationship('Student', secondary=student_athletes, back_populates='athletics')

    def __repr__(self):
        return '<TeamGroup {} ({}), team {} ({}), updated={}, created={}>'.format(
            self.group_name,
            self.group_code,
            self.team_code,
            self.team_name,
            self.updated_at,
            self.created_at,
        )

    @classmethod
    def all_team_groups(cls):
        query = db.session.query(cls.group_code, cls.group_name, cls.team_code, cls.team_name, func.count(Student.sid))
        order_by = [cls.group_name, cls.group_code]
        results = query.join(Athletics.athletes).order_by(*order_by).group_by(*order_by).all()

        def translate_row(row):
            return {
                'groupCode': row[0],
                'groupName': row[1],
                'teamCode': row[2],
                'teamName': row[3],
                'totalMemberCount': row[4],
            }
        return [translate_row(row) for row in results]

    @classmethod
    def get_team_groups(cls, group_codes):
        query_filter = cls.group_code.in_(group_codes)
        athletes = cls.query.order_by(cls.group_name).distinct(cls.group_name).filter(query_filter).all()
        return [athlete.to_api_json() for athlete in athletes]

    @classmethod
    def all_teams(cls):
        query = db.session.query(cls.team_code, cls.team_name, func.count(func.distinct(Student.sid)))
        order_by = [cls.team_name, cls.team_code]
        results = query.distinct(cls.team_name).join(Athletics.athletes).order_by(*order_by).group_by(*order_by).all()

        def translate_row(row):
            return {
                'code': row[0],
                'name': row[1],
                'totalMemberCount': row[2],
            }
        return [translate_row(row) for row in results]

    @classmethod
    def get_team(cls, team_code, order_by):
        results = db.session.query(
            cls.team_code,
            cls.team_name,
            cls.group_code,
            cls.group_name,
        ).filter(cls.team_code == team_code).all()
        team = None
        if len(results):
            team = {
                'teamGroups': [],
            }
            for row in results:
                team['code'] = row[0]
                team['name'] = row[1]
                team['teamGroups'].append({
                    'groupCode': row[2],
                    'groupName': row[3],
                })
            group_codes = [group['groupCode'] for group in team['teamGroups']]
            students = Student.get_students(group_codes=group_codes, order_by=order_by, offset=0, limit=None)
            team['members'] = students['students']
            team['totalMemberCount'] = students['totalStudentCount']
        return team

    def to_api_json(self):
        return {
            'groupCode': self.group_code,
            'groupName': self.group_name,
            'teamCode': self.team_code,
            'teamName': self.team_name,
        }
