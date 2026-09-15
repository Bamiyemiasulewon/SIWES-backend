from app import create_app
from app.extensions import db
from app.models import Department, User, Asset, Ticket


app = create_app()


def seed_data():
    with app.app_context():
        db.drop_all()
        db.create_all()

        it = Department(name="IT", description="Technology support and infrastructure")
        hr = Department(name="Human Resources", description="Employee support and onboarding")
        finance = Department(name="Finance", description="Finance operations and support")
        db.session.add_all([it, hr, finance])
        db.session.commit()

        admin = User(name="Admin User", email="admin@example.com", role="admin", department_id=it.id)
        admin.password = "admin123"
        tech = User(name="Tech User", email="tech@example.com", role="technician", department_id=it.id)
        tech.password = "tech123"
        employee = User(name="Employee User", email="employee@example.com", role="employee", department_id=hr.id)
        employee.password = "emp123"
        db.session.add_all([admin, tech, employee])
        db.session.commit()

        laptop = Asset(name="Dell Latitude 5440", type="laptop", serial_number="DL-1001", status="active", assigned_to=employee.id, department_id=it.id)
        monitor = Asset(name="Dell Monitor 27", type="monitor", serial_number="DM-2001", status="in_repair", assigned_to=tech.id, department_id=it.id)
        printer = Asset(name="HP LaserJet", type="printer", serial_number="HP-3001", status="active", department_id=finance.id)
        db.session.add_all([laptop, monitor, printer])
        db.session.commit()

        ticket1 = Ticket(
            title="Laptop not turning on",
            description="Employee laptop will not boot after update.",
            status="open",
            priority="high",
            created_by=employee.id,
            assigned_to=tech.id,
            asset_id=laptop.id,
            department_id=it.id,
        )
        ticket2 = Ticket(
            title="Monitor flickering",
            description="Monitor flickers intermittently during use.",
            status="in_progress",
            priority="medium",
            created_by=employee.id,
            assigned_to=tech.id,
            asset_id=monitor.id,
            department_id=it.id,
        )
        db.session.add_all([ticket1, ticket2])
        db.session.commit()

        print("Sample data seeded successfully.")


if __name__ == "__main__":
    seed_data()
