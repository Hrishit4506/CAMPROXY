#!/usr/bin/env python3
"""
Setup script to create initial admin user for UniSync
"""
import os
from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an initial admin user"""
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User()
        admin.username = 'admin'
        admin.email = 'admin@unisync.local'
        admin.password_hash = generate_password_hash('admin123')
        admin.role = 'admin'
        
        db.session.add(admin)
        db.session.commit()
        
        print("✓ Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("\nPlease change the password after first login.")

if __name__ == '__main__':
    create_admin_user()