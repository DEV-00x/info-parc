from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
import pandas as pd
from io import BytesIO
import pdfkit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///device_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Add this context processor to make 'now' available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# تعريف النماذج
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='فعال')
    location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    # الحقول الجديدة
    owner = db.Column(db.String(100))
    department = db.Column(db.String(100))
    warranty_period = db.Column(db.Integer)
    supplier = db.Column(db.String(100))
    maintenance_records = db.relationship('MaintenanceRecord', backref='device', lazy=True, cascade="all, delete-orphan")
    history_records = db.relationship('DeviceHistory', backref='device', lazy=True, cascade="all, delete-orphan")

class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    maintenance_date = db.Column(db.Date, nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='قيد الانتظار')
    technician = db.Column(db.String(100), nullable=False)
    solution = db.Column(db.Text)
    completion_date = db.Column(db.Date)
    cost = db.Column(db.Float)

# إضافة نموذج جديد لسجل تاريخ الجهاز
class DeviceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    change_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    change_type = db.Column(db.String(50), nullable=False)  # نوع التغيير: تغيير المالك، تغيير الموقع، إلخ
    previous_value = db.Column(db.String(200))  # القيمة السابقة
    new_value = db.Column(db.String(200))  # القيمة الجديدة
    changed_by = db.Column(db.String(100))  # الشخص الذي قام بالتغيير
    notes = db.Column(db.Text)  # ملاحظات إضافية

# إنشاء قاعدة البيانات
with app.app_context():
    db.create_all()

# الصفحة الرئيسية
@app.route('/')
def index():
    # Get latest devices and maintenance records
    latest_devices = Device.query.order_by(Device.id.desc()).limit(5).all()
    latest_maintenance = MaintenanceRecord.query.order_by(MaintenanceRecord.id.desc()).limit(5).all()
    
    # Calculate statistics for devices
    total_devices = Device.query.count()
    active_devices = Device.query.filter_by(status='فعال').count()
    maintenance_devices = Device.query.filter_by(status='قيد الصيانة').count()
    
    # Calculate statistics for maintenance
    total_maintenance = MaintenanceRecord.query.count()
    pending_maintenance = MaintenanceRecord.query.filter_by(status='قيد الانتظار').count()
    completed_maintenance = MaintenanceRecord.query.filter_by(status='مكتمل').count()
    
    return render_template('index.html', 
                          latest_devices=latest_devices, 
                          latest_maintenance=latest_maintenance,
                          total_devices=total_devices,
                          active_devices=active_devices,
                          maintenance_devices=maintenance_devices,
                          total_maintenance=total_maintenance,
                          pending_maintenance=pending_maintenance,
                          completed_maintenance=completed_maintenance,
                          now=datetime.now())  # Add this line

# صفحة الأجهزة
@app.route('/devices')
def devices():
    all_devices = Device.query.all()
    return render_template('devices.html', devices=all_devices)

# إضافة جهاز جديد
@app.route('/devices/add', methods=['GET', 'POST'])
def add_device():
    if request.method == 'POST':
        name = request.form['name']
        device_type = request.form['type']
        serial_number = request.form['serial_number']
        # Remove the line that gets purchase_date from the form
        status = request.form['status']
        location = request.form['location']
        notes = request.form['notes']
        
        # الحقول الجديدة
        owner = request.form.get('owner', '')
        department = request.form.get('department', '')
        # Remove warranty_period and supplier since they're no longer in the form
        
        # التحقق من عدم وجود جهاز بنفس الرقم التسلسلي
        existing_device = Device.query.filter_by(serial_number=serial_number).first()
        if existing_device:
            flash('الرقم التسلسلي موجود بالفعل!', 'danger')
            return redirect(url_for('add_device'))
        
        # Set a default purchase_date since it's required by the database model
        new_device = Device(
            name=name,
            type=device_type,
            serial_number=serial_number,
            purchase_date=date.today(),  # Use today's date as default
            status=status,
            location=location,
            notes=notes,
            owner=owner,
            department=department,
            warranty_period=None,
            supplier=''
        )
        
        db.session.add(new_device)
        db.session.commit()
        
        flash('تمت إضافة الجهاز بنجاح!', 'success')
        return redirect(url_for('devices'))
    
    return render_template('add_device.html', today=date.today().strftime('%Y-%m-%d'))

# تفاصيل الجهاز
@app.route('/devices/<int:device_id>')
def device_details(device_id):
    device = Device.query.get_or_404(device_id)
    maintenance_records = MaintenanceRecord.query.filter_by(device_id=device_id).order_by(MaintenanceRecord.maintenance_date.desc()).all()
    return render_template('device_details.html', device=device, maintenance_records=maintenance_records)

# تعديل الجهاز
@app.route('/devices/edit/<int:device_id>', methods=['GET', 'POST'])
def edit_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    if request.method == 'POST':
        # تسجيل التغييرات في المالك
        if hasattr(device, 'owner') and device.owner != request.form.get('owner', ''):
            history_record = DeviceHistory(
                device_id=device.id,
                change_type='تغيير المالك',
                previous_value=device.owner or 'غير محدد',
                new_value=request.form.get('owner', '') or 'غير محدد',
                changed_by='مدير النظام',
                notes=f'تم تغيير المالك من {device.owner or "غير محدد"} إلى {request.form.get("owner", "") or "غير محدد"}'
            )
            db.session.add(history_record)
        
        # تسجيل التغييرات في الموقع
        if device.location != request.form.get('location', ''):
            history_record = DeviceHistory(
                device_id=device.id,
                change_type='تغيير الموقع',
                previous_value=device.location or 'غير محدد',
                new_value=request.form.get('location', '') or 'غير محدد',
                changed_by='مدير النظام',
                notes=f'تم نقل الجهاز من {device.location or "غير محدد"} إلى {request.form.get("location", "") or "غير محدد"}'
            )
            db.session.add(history_record)
        
        # تسجيل التغييرات في القسم
        if hasattr(device, 'department') and device.department != request.form.get('department', ''):
            history_record = DeviceHistory(
                device_id=device.id,
                change_type='تغيير القسم',
                previous_value=device.department or 'غير محدد',
                new_value=request.form.get('department', '') or 'غير محدد',
                changed_by='مدير النظام',
                notes=f'تم تغيير القسم من {device.department or "غير محدد"} إلى {request.form.get("department", "") or "غير محدد"}'
            )
            db.session.add(history_record)
        
        # تسجيل التغييرات في الحالة
        if device.status != request.form['status']:
            history_record = DeviceHistory(
                device_id=device.id,
                change_type='تغيير الحالة',
                previous_value=device.status,
                new_value=request.form['status'],
                changed_by='مدير النظام',
                notes=f'تم تغيير حالة الجهاز من {device.status} إلى {request.form["status"]}'
            )
            db.session.add(history_record)
        
        device.name = request.form['name']
        device.type = request.form['type']
        
        # التحقق من الرقم التسلسلي إذا تم تغييره
        if device.serial_number != request.form['serial_number']:
            existing_device = Device.query.filter_by(serial_number=request.form['serial_number']).first()
            if existing_device:
                flash('الرقم التسلسلي موجود بالفعل!', 'danger')
                return redirect(url_for('edit_device', device_id=device_id))
            device.serial_number = request.form['serial_number']
        
        # Remove the line that updates purchase_date
        # device.purchase_date = datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date()
        
        device.status = request.form['status']
        device.location = request.form['location']
        device.notes = request.form['notes']
        
        # تحديث الحقول الجديدة
        if hasattr(device, 'owner'):
            device.owner = request.form.get('owner', '')
        if hasattr(device, 'department'):
            device.department = request.form.get('department', '')
        
        db.session.commit()
        flash('تم تحديث الجهاز بنجاح!', 'success')
        return redirect(url_for('device_details', device_id=device_id))
    
    return render_template('edit_device.html', device=device)

# حذف الجهاز
@app.route('/devices/delete/<int:device_id>')
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    db.session.delete(device)
    db.session.commit()
    flash('تم حذف الجهاز بنجاح!', 'success')
    return redirect(url_for('devices'))

# صفحة الصيانة
@app.route('/maintenance')
def maintenance():
    maintenance_records = MaintenanceRecord.query.order_by(MaintenanceRecord.maintenance_date.desc()).all()
    return render_template('maintenance.html', maintenance_records=maintenance_records)

# إضافة سجل صيانة
@app.route('/maintenance/add/<int:device_id>', methods=['GET', 'POST'])
def add_maintenance(device_id):
    device = Device.query.get_or_404(device_id)
    
    if request.method == 'POST':
        maintenance_date = datetime.strptime(request.form['maintenance_date'], '%Y-%m-%d').date()
        issue_description = request.form['issue_description']
        status = request.form['status']
        technician = request.form['technician']
        
        new_record = MaintenanceRecord(
            device_id=device_id,
            maintenance_date=maintenance_date,
            issue_description=issue_description,
            status=status,
            technician=technician
        )
        
        # إذا كانت الحالة مكتملة، أضف تاريخ الإكمال
        if status == 'مكتمل':
            new_record.completion_date = date.today()
        
        # تحديث حالة الجهاز إذا كان قيد الصيانة
        if status != 'مكتمل' and device.status != 'قيد الصيانة':
            device.status = 'قيد الصيانة'
        
        db.session.add(new_record)
        db.session.commit()
        
        flash('تمت إضافة سجل الصيانة بنجاح!', 'success')
        return redirect(url_for('device_details', device_id=device_id))
    
    return render_template('add_maintenance.html', device=device, today=date.today().strftime('%Y-%m-%d'))

# تعديل سجل صيانة
@app.route('/maintenance/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_maintenance(record_id):
    maintenance_record = MaintenanceRecord.query.get_or_404(record_id)
    
    if request.method == 'POST':
        maintenance_record.maintenance_date = datetime.strptime(request.form['maintenance_date'], '%Y-%m-%d').date()
        maintenance_record.issue_description = request.form['issue_description']
        maintenance_record.status = request.form['status']
        maintenance_record.technician = request.form['technician']
        maintenance_record.solution = request.form.get('solution', '')
        
        # تحويل التكلفة إلى رقم إذا تم إدخالها
        cost = request.form.get('cost', '')
        maintenance_record.cost = float(cost) if cost else None
        
        # إذا كانت الحالة مكتملة، أضف تاريخ الإكمال
        if maintenance_record.status == 'مكتمل' and not maintenance_record.completion_date:
            maintenance_record.completion_date = date.today()
        elif maintenance_record.status != 'مكتمل':
            maintenance_record.completion_date = None
        
        # تحديث حالة الجهاز بناءً على حالة الصيانة
        device = Device.query.get(maintenance_record.device_id)
        if maintenance_record.status == 'مكتمل':
            # التحقق مما إذا كانت هناك سجلات صيانة أخرى غير مكتملة
            other_records = MaintenanceRecord.query.filter(
                MaintenanceRecord.device_id == device.id,
                MaintenanceRecord.id != record_id,
                MaintenanceRecord.status != 'مكتمل'
            ).count()
            
            if other_records == 0:
                device.status = 'فعال'
        else:
            device.status = 'قيد الصيانة'
        
        db.session.commit()
        flash('تم تحديث سجل الصيانة بنجاح!', 'success')
        return redirect(url_for('device_details', device_id=maintenance_record.device_id))
    
    return render_template('edit_maintenance.html', maintenance_record=maintenance_record)

# طباعة سجل صيانة
@app.route('/maintenance/print/<int:record_id>')
def print_maintenance(record_id):
    maintenance_record = MaintenanceRecord.query.get_or_404(record_id)
    device = Device.query.get(maintenance_record.device_id)
    return render_template('print_maintenance.html', maintenance_record=maintenance_record, device=device, now=datetime.now())

# تصدير سجل صيانة بصيغة PDF
@app.route('/maintenance/export-pdf/<int:record_id>')
def export_maintenance_pdf(record_id):
    maintenance_record = MaintenanceRecord.query.get_or_404(record_id)
    device = Device.query.get(maintenance_record.device_id)
    
    # إنشاء HTML
    html = render_template('maintenance_pdf.html', maintenance_record=maintenance_record, device=device, now=datetime.now())
    
    # تحويل HTML إلى PDF
    pdf = pdfkit.from_string(html, False)
    
    # إنشاء استجابة لتنزيل الملف
    buffer = BytesIO(pdf)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'maintenance_report_{record_id}.pdf',
        mimetype='application/pdf'
    )

# صفحة التقارير
@app.route('/reports')
def reports():
    # إحصائيات الأجهزة
    total_devices = Device.query.count()
    active_devices = Device.query.filter_by(status='فعال').count()
    inactive_devices = total_devices - active_devices
    
    # إحصائيات الصيانة
    total_maintenance = MaintenanceRecord.query.count()
    pending_maintenance = MaintenanceRecord.query.filter_by(status='قيد الانتظار').count()
    in_progress_maintenance = MaintenanceRecord.query.filter_by(status='قيد التنفيذ').count()
    completed_maintenance = MaintenanceRecord.query.filter_by(status='مكتمل').count()
    
    # متوسط وقت الصيانة
    completed_records = MaintenanceRecord.query.filter(
        MaintenanceRecord.status == 'مكتمل',
        MaintenanceRecord.completion_date.isnot(None)
    ).all()
    
    avg_maintenance_time = 0
    if completed_records:
        total_days = 0
        for record in completed_records:
            delta = record.completion_date - record.maintenance_date
            total_days += delta.days
        avg_maintenance_time = total_days / len(completed_records)
    
    # توزيع أنواع الأجهزة
    device_types = {}
    for device in Device.query.all():
        if device.type in device_types:
            device_types[device.type] += 1
        else:
            device_types[device.type] = 1
    
    return render_template(
        'reports.html',
        total_devices=total_devices,
        active_devices=active_devices,
        inactive_devices=inactive_devices,
        total_maintenance=total_maintenance,
        pending_maintenance=pending_maintenance,
        in_progress_maintenance=in_progress_maintenance,
        completed_maintenance=completed_maintenance,
        avg_maintenance_time=avg_maintenance_time,
        device_types=device_types
    )

# تصدير الأجهزة بصيغة Excel
@app.route('/export/devices-excel')
def export_devices_excel():
    devices = Device.query.all()
    
    # إنشاء DataFrame
    data = []
    for device in devices:
        data.append({
            'الرقم': device.id,
            'الاسم': device.name,
            'النوع': device.type,
            'الرقم التسلسلي': device.serial_number,
            'تاريخ الشراء': device.purchase_date.strftime('%Y-%m-%d'),
            'الحالة': device.status,
            'الموقع': device.location,
            'ملاحظات': device.notes
        })
    
    df = pd.DataFrame(data)
    
    # إنشاء ملف Excel في الذاكرة
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='الأجهزة')
        worksheet = writer.sheets['الأجهزة']
        for idx, col in enumerate(df.columns):
            worksheet.set_column(idx, idx, 20)
    
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='devices_report.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# تصدير سجلات الصيانة بصيغة Excel
@app.route('/export/maintenance-excel')
def export_maintenance_excel():
    records = MaintenanceRecord.query.all()
    
    # إنشاء DataFrame
    data = []
    for record in records:
        device = Device.query.get(record.device_id)
        data.append({
            'الرقم': record.id,
            'الجهاز': device.name,
            'الرقم التسلسلي': device.serial_number,
            'تاريخ الصيانة': record.maintenance_date.strftime('%Y-%m-%d'),
            'وصف المشكلة': record.issue_description,
            'الحالة': record.status,
            'الفني': record.technician,
            'الحل': record.solution,
            'تاريخ الإكمال': record.completion_date.strftime('%Y-%m-%d') if record.completion_date else '',
            'التكلفة': record.cost if record.cost else 0
        })
    
    df = pd.DataFrame(data)
    
    # إنشاء ملف Excel في الذاكرة
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='سجلات الصيانة')
        worksheet = writer.sheets['سجلات الصيانة']
        for idx, col in enumerate(df.columns):
            worksheet.set_column(idx, idx, 20)
    
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='maintenance_report.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# تسجيل الخروج
@app.route('/logout')
def logout():
    # Add a proper implementation since you can't have an empty function
    flash('تم تسجيل الخروج بنجاح!', 'success')
    return redirect(url_for('index'))

@app.route('/users')
def users():
    # ... users management code ...
    return render_template('users.html')  # Add a proper return statement

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    # Not implemented yet
    pass
    if request.method == 'POST':
        # Process form data here
        flash('تمت إضافة المستخدم بنجاح!', 'success')
        return redirect(url_for('users'))
    return render_template('add_user.html')

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    # Temporary implementation
    if request.method == 'POST':
        # Process form data here
        flash('تم تحديث المستخدم بنجاح!', 'success')
        return redirect(url_for('users'))
    return render_template('edit_user.html')

@app.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    # Temporary implementation
    flash('تم حذف المستخدم بنجاح!', 'success')
    return redirect(url_for('users'))

@app.route('/reports/export-pdf')
def export_reports_pdf():
    # Specify the path to wkhtmltopdf executable
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    
    # Get the same data that's used for the reports page
    # This should match what you're using in your reports route
    total_devices = Device.query.count()
    active_devices = Device.query.filter_by(status='فعال').count()
    inactive_devices = Device.query.filter(Device.status != 'فعال').count()
    
    # Get maintenance statistics
    total_maintenance = MaintenanceRecord.query.count()
    pending_maintenance = MaintenanceRecord.query.filter_by(status='قيد الانتظار').count()
    in_progress_maintenance = MaintenanceRecord.query.filter_by(status='قيد التنفيذ').count()
    completed_maintenance = MaintenanceRecord.query.filter_by(status='مكتمل').count()
    
    # Calculate average maintenance time
    completed_records = MaintenanceRecord.query.filter_by(status='مكتمل').all()
    total_days = 0
    count = 0
    for record in completed_records:
        if record.completion_date and record.maintenance_date:
            days = (record.completion_date - record.maintenance_date).days
            total_days += days
            count += 1
    
    avg_maintenance_time = total_days / count if count > 0 else 0
    
    # Get device types distribution
    device_types = {}
    for device in Device.query.all():
        if device.type in device_types:
            device_types[device.type] += 1
        else:
            device_types[device.type] = 1
    
    # Render the template for PDF
    html = render_template('reports_pdf.html',
                          total_devices=total_devices,
                          active_devices=active_devices,
                          inactive_devices=inactive_devices,
                          total_maintenance=total_maintenance,
                          pending_maintenance=pending_maintenance,
                          in_progress_maintenance=in_progress_maintenance,
                          completed_maintenance=completed_maintenance,
                          avg_maintenance_time=avg_maintenance_time,
                          device_types=device_types)
    
    # Generate PDF with the specified configuration
    pdf = pdfkit.from_string(html, False, configuration=config)
    
    # Create a BytesIO object
    buffer = BytesIO(pdf)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name='device_management_report.pdf',
        mimetype='application/pdf'
    )

# Add the device history route here, before the if __name__ == '__main__': line
@app.route('/devices/<int:device_id>/history')
def device_history(device_id):
    device = Device.query.get_or_404(device_id)
    history_records = DeviceHistory.query.filter_by(device_id=device_id).order_by(DeviceHistory.change_date.desc()).all()
    return render_template('device_history.html', device=device, history_records=history_records)

# في نهاية الملف، قم بتعديل طريقة تشغيل التطبيق
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)