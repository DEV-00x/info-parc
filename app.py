from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import pandas as pd
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_clé_secrète_ici'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modèles de données
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(100), nullable=False, unique=True)
    status = db.Column(db.String(20), default='actif')
    # Renamed owner to assigned_to
    assigned_to = db.Column(db.String(100))
    service = db.Column(db.String(100))
    department = db.Column(db.String(100))
    mac_address = db.Column(db.String(17))
    notes = db.Column(db.Text)
    maintenance_records = db.relationship('MaintenanceRecord', backref='device', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Device {self.name}>'

class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    reference = db.Column(db.String(20))  # Add this line for the reference field
    maintenance_date = db.Column(db.Date, nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    actions_taken = db.Column(db.Text)
    status = db.Column(db.String(20), default='en attente')
    technician = db.Column(db.String(100), nullable=False)
    completion_date = db.Column(db.Date)
    # Removed cost field
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<MaintenanceRecord {self.id}>'

# Add OwnershipChange model here
class OwnershipChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    previous_owner = db.Column(db.String(100))
    new_owner = db.Column(db.String(100))
    change_date = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<OwnershipChange {self.id}>'

# Update Device model to include the relationship
Device.ownership_changes = db.relationship('OwnershipChange', backref='device', lazy=True, cascade="all, delete-orphan")

# Création des tables dans la base de données
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    # Add the current datetime to the template context
    now = datetime.now()
    
    # Statistiques pour le tableau de bord
    total_devices = Device.query.count()
    active_devices = Device.query.filter_by(status='actif').count()
    maintenance_devices = Device.query.filter_by(status='en maintenance').count()
    inactive_devices = Device.query.filter_by(status='inactif').count()
    
    # Appareils récents
    recent_devices = Device.query.order_by(Device.id.desc()).limit(5).all()
    
    # Maintenance récente
    recent_maintenance = MaintenanceRecord.query.order_by(MaintenanceRecord.maintenance_date.desc()).limit(5).all()
    
    # Get list of assigned users with device counts
    assigned_data = db.session.query(
        Device.assigned_to, 
        db.func.count(Device.id).label('device_count')
    ).filter(
        Device.assigned_to != '', 
        Device.assigned_to != None
    ).group_by(
        Device.assigned_to
    ).order_by(
        db.func.count(Device.id).desc()
    ).all()
    
    return render_template('index.html', 
                          now=now,
                          total_devices=total_devices,
                          active_devices=active_devices,
                          maintenance_devices=maintenance_devices,
                          inactive_devices=inactive_devices,
                          recent_devices=recent_devices,
                          recent_maintenance=recent_maintenance,
                          assigned_data=assigned_data)

@app.route('/devices')
def devices():
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)

@app.route('/device/<int:device_id>')
def device_details(device_id):
    device = Device.query.get_or_404(device_id)
    maintenance_records = MaintenanceRecord.query.filter_by(device_id=device_id).order_by(MaintenanceRecord.maintenance_date.desc()).all()
    current_date = datetime.now().date()
    return render_template('device_details.html', device=device, maintenance_records=maintenance_records, current_date=current_date)

@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    if request.method == 'POST':
        # Récupération des données du formulaire
        name = request.form['name']
        type = request.form['type']
        serial_number = request.form['serial_number']
        status = request.form['status']
        # Renamed owner to assigned_to
        assigned_to = request.form.get('assigned_to', '')
        service = request.form.get('service', '')
        department = request.form.get('department', '')
        mac_address = request.form.get('mac_address', '')
        notes = request.form.get('notes', '')
        
        # Vérification si le numéro de série existe déjà
        existing_device = Device.query.filter_by(serial_number=serial_number).first()
        if existing_device:
            flash('Un appareil avec ce numéro de série existe déjà.', 'danger')
            return redirect(url_for('add_device'))
        
        # Création d'un nouvel appareil
        new_device = Device(
            name=name,
            type=type,
            serial_number=serial_number,
            status=status,
            # Renamed owner to assigned_to
            assigned_to=assigned_to,
            service=service,
            department=department,
            mac_address=mac_address,
            notes=notes
        )
        
        # Ajout à la base de données
        db.session.add(new_device)
        db.session.commit()
        
        flash('Appareil ajouté avec succès!', 'success')
        return redirect(url_for('devices'))
    
    # Removed locations query for autocomplete
    
    # Affichage du formulaire
    return render_template('device_form.html', device=Device())

@app.route('/edit_device/<int:device_id>', methods=['GET', 'POST'])
def edit_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        device.name = request.form['name']
        device.type = request.form['type']
        
        # Vérification si le numéro de série a changé et s'il existe déjà
        new_serial = request.form['serial_number']
        if new_serial != device.serial_number:
            existing_device = Device.query.filter_by(serial_number=new_serial).first()
            if existing_device:
                flash('Un appareil avec ce numéro de série existe déjà.', 'danger')
                return redirect(url_for('edit_device', device_id=device_id))
        
        device.serial_number = new_serial
        device.status = request.form['status']
        
        # Check if owner has changed and track the change
        new_owner = request.form.get('assigned_to', '')
        if new_owner != device.assigned_to and (new_owner or device.assigned_to):
            # Create ownership change record
            ownership_change = OwnershipChange(
                device_id=device.id,
                previous_owner=device.assigned_to or 'Non assigné',
                new_owner=new_owner or 'Non assigné',
                change_date=datetime.now(),
                notes=request.form.get('notes', '')
            )
            db.session.add(ownership_change)
        
        # Update device information
        device.assigned_to = new_owner
        device.service = request.form.get('service', '')
        device.department = request.form.get('department', '')
        device.mac_address = request.form.get('mac_address', '')
        device.notes = request.form.get('notes', '')
        
        # Mise à jour dans la base de données
        db.session.commit()
        
        flash('Appareil mis à jour avec succès!', 'success')
        return redirect(url_for('device_details', device_id=device_id))
    
    # Affichage du formulaire
    return render_template('device_form.html', device=device)

@app.route('/delete_device/<int:device_id>')
def delete_device(device_id):
    device = Device.query.get_or_404(device_id)
    
    # Suppression de l'appareil
    db.session.delete(device)
    db.session.commit()
    
    flash('Appareil supprimé avec succès!', 'success')
    return redirect(url_for('devices'))

@app.route('/maintenance')
def maintenance():
    maintenance_records = MaintenanceRecord.query.order_by(MaintenanceRecord.maintenance_date.desc()).all()
    return render_template('maintenance.html', maintenance_records=maintenance_records)

# Move this function outside of the route definition
def generate_maintenance_reference(maintenance_date):
    """Generate a reference number in the format REF:NumberInMonth/INF/Year"""
    year = maintenance_date.year
    month = maintenance_date.month
    
    # Count how many maintenance records exist for this month and year
    count = MaintenanceRecord.query.filter(
        db.extract('year', MaintenanceRecord.maintenance_date) == year,
        db.extract('month', MaintenanceRecord.maintenance_date) == month
    ).count()
    
    # The new record will be count + 1
    number_in_month = count + 1
    
    # Format the reference
    reference = f"REF:{number_in_month:02d}/INF/{year}"
    return reference

@app.route('/add_maintenance', methods=['GET', 'POST'])
@app.route('/add_maintenance/<int:device_id>', methods=['GET', 'POST'])
def add_maintenance(device_id=None):
    if request.method == 'POST':
        # Récupération des données du formulaire
        device_id = request.form['device_id']
        maintenance_date_str = request.form['maintenance_date']
        issue_description = request.form['issue_description']
        actions_taken = request.form.get('actions_taken', '')
        status = request.form['status']
        technician = request.form['technician']
        completion_date_str = request.form.get('completion_date', '')
        # Removed cost_str processing
        notes = request.form.get('notes', '')
        
        # Conversion des dates et du coût
        maintenance_date = datetime.strptime(maintenance_date_str, '%Y-%m-%d').date()
        completion_date = datetime.strptime(completion_date_str, '%Y-%m-%d').date() if completion_date_str else None
        
        # Generate reference number
        reference = generate_maintenance_reference(maintenance_date)
        
        # Création d'un nouveau registre de maintenance
        new_record = MaintenanceRecord(
            device_id=device_id,
            reference=reference,  # Add the reference
            maintenance_date=maintenance_date,
            issue_description=issue_description,
            actions_taken=actions_taken,
            status=status,
            technician=technician,
            completion_date=completion_date,
            notes=notes
        )
        
        # Ajout à la base de données
        db.session.add(new_record)
        
        # Mise à jour du statut de l'appareil si nécessaire
        device = Device.query.get(device_id)
        if status == 'en cours' and device.status != 'en maintenance':
            device.status = 'en maintenance'
        elif status == 'terminé' and device.status == 'en maintenance':
            device.status = 'actif'
        
        db.session.commit()
        
        flash('Registre de maintenance ajouté avec succès!', 'success')
        return redirect(url_for('device_details', device_id=device_id))
    
    # Liste des appareils pour le formulaire
    devices = Device.query.all()
    
    # Liste des techniciens existants pour l'autocomplétion
    technicians = db.session.query(MaintenanceRecord.technician).distinct().filter(MaintenanceRecord.technician != None, MaintenanceRecord.technician != '').all()
    technicians = [technician[0] for technician in technicians]
    
    # Date du jour
    today = datetime.now().date().strftime('%Y-%m-%d')
    
    # Affichage du formulaire
    return render_template('maintenance_form.html', record=MaintenanceRecord(), devices=devices, technicians=technicians, today=today, device_id=device_id)

@app.route('/edit_maintenance/<int:record_id>', methods=['GET', 'POST'])
def edit_maintenance(record_id):
    record = MaintenanceRecord.query.get_or_404(record_id)
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        old_status = record.status
        
        record.maintenance_date = datetime.strptime(request.form['maintenance_date'], '%Y-%m-%d').date()
        
        # If the maintenance date changed, update the reference
        if record.maintenance_date != datetime.strptime(request.form['maintenance_date'], '%Y-%m-%d').date():
            record.reference = generate_maintenance_reference(record.maintenance_date)
            
        record.issue_description = request.form['issue_description']
        record.actions_taken = request.form.get('actions_taken', '')
        record.status = request.form['status']
        record.technician = request.form['technician']
        
        completion_date_str = request.form.get('completion_date', '')
        record.completion_date = datetime.strptime(completion_date_str, '%Y-%m-%d').date() if completion_date_str else None
        
        # Remove this cost-related code since cost field was removed
        # cost_str = request.form.get('cost', '')
        # record.cost = float(cost_str) if cost_str else None
        
        record.notes = request.form.get('notes', '')
        
        # Mise à jour du statut de l'appareil si nécessaire
        device = Device.query.get(record.device_id)
        if record.status == 'en cours' and device.status != 'en maintenance' and old_status != 'en cours':
            device.status = 'en maintenance'
        elif record.status == 'terminé' and device.status == 'en maintenance' and old_status != 'terminé':
            device.status = 'actif'
        
        # Mise à jour dans la base de données
        db.session.commit()
        
        flash('Registre de maintenance mis à jour avec succès!', 'success')
        return redirect(url_for('device_details', device_id=record.device_id))
    
    # Liste des appareils pour le formulaire
    devices = Device.query.all()
    
    # Liste des techniciens existants pour l'autocomplétion
    technicians = db.session.query(MaintenanceRecord.technician).distinct().filter(MaintenanceRecord.technician != None, MaintenanceRecord.technician != '').all()
    technicians = [technician[0] for technician in technicians]
    
    # Affichage du formulaire
    return render_template('maintenance_form.html', record=record, devices=devices, technicians=technicians, today=datetime.now().date().strftime('%Y-%m-%d'))

@app.route('/delete_maintenance/<int:record_id>')
def delete_maintenance(record_id):
    record = MaintenanceRecord.query.get_or_404(record_id)
    device_id = record.device_id
    
    # Suppression du registre
    db.session.delete(record)
    db.session.commit()
    
    flash('Registre de maintenance supprimé avec succès!', 'success')
    return redirect(url_for('device_details', device_id=device_id))

@app.route('/export_devices_excel')
def export_devices_excel():
    devices = Device.query.all()
    
    # Création d'un DataFrame pandas
    data = []
    for device in devices:
        data.append({
            'ID': device.id,
            'Nom': device.name,
            'Type': device.type,
            'Numéro de Série': device.serial_number,
            'Statut': device.status,
            'Assigné à': device.assigned_to,
            'Service': device.service,
            'Département': device.department,
            'Adresse MAC': device.mac_address,
            'Notes': device.notes
        })
    
    df = pd.DataFrame(data)
    
    # Création du fichier Excel en mémoire
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Appareils', index=False)
        
        # Ajustement automatique de la largeur des colonnes
        worksheet = writer.sheets['Appareils']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # Envoi du fichier
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'appareils_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/export_maintenance_excel')
def export_maintenance_excel():
    records = MaintenanceRecord.query.all()
    
    # Création d'un DataFrame pandas
    data = []
    for record in records:
        data.append({
            'ID': record.id,
            'Référence': record.reference or '',
            'Appareil': record.device.name,
            'Type d\'Appareil': record.device.type,
            'Numéro de Série': record.device.serial_number,
            'Date de Maintenance': record.maintenance_date.strftime('%d/%m/%Y'),
            'Description du Problème': record.issue_description,
            'Actions Effectuées': record.actions_taken,
            'Statut': record.status,
            'Technicien': record.technician,
            'Date d\'Achèvement': record.completion_date.strftime('%d/%m/%Y') if record.completion_date else '',
            # Removed Coût (€)
            'Notes': record.notes
        })
    
    df = pd.DataFrame(data)
    
    # Création du fichier Excel en mémoire
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Maintenance', index=False)
        
        # Ajustement automatique de la largeur des colonnes
        worksheet = writer.sheets['Maintenance']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # Envoi du fichier
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'maintenance_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

# After the existing routes, add this new route
@app.route('/devices_by_assigned/<assigned_to>')
def devices_by_assigned(assigned_to):
    devices = Device.query.filter_by(assigned_to=assigned_to).all()
    return render_template('devices.html', 
                          devices=devices, 
                          title=f'Appareils assignés à {assigned_to}',
                          filtered_by_assigned=True,
                          current_assigned=assigned_to)

# Remove this route completely
# @app.route('/devices_by_owner/<owner>')
# def devices_by_owner(owner):
#     devices = Device.query.filter_by(owner=owner).all()
#     return render_template('devices.html', 
#                           devices=devices, 
#                           title=f'Appareils gérés par {owner}',
#                           filtered_by_owner=True,
#                           current_owner=owner)

@app.route('/maintenance/<int:record_id>/print')
def print_maintenance(record_id):
    # Get the maintenance record
    maintenance_record = MaintenanceRecord.query.get_or_404(record_id)
    
    # Render a simplified template for printing
    return render_template('print_maintenance.html', record=maintenance_record)

# Add this context processor to make now() available in templates
@app.context_processor
def utility_processor():
    return dict(now=datetime.now)

@app.route('/device/<int:device_id>/ownership_history')
def ownership_history(device_id):
    device = Device.query.get_or_404(device_id)
    ownership_changes = OwnershipChange.query.filter_by(device_id=device_id).order_by(OwnershipChange.change_date.desc()).all()
    return render_template('ownership_history.html', device=device, ownership_changes=ownership_changes)

@app.route('/device/<int:device_id>/export_ownership_history')
def export_ownership_history(device_id):
    device = Device.query.get_or_404(device_id)
    ownership_changes = OwnershipChange.query.filter_by(device_id=device_id).order_by(OwnershipChange.change_date.desc()).all()
    
    # Création d'un DataFrame pandas
    data = []
    for change in ownership_changes:
        data.append({
            'ID': change.id,
            'Date': change.change_date.strftime('%d/%m/%Y %H:%M'),
            'Ancien Propriétaire': change.previous_owner,
            'Nouveau Propriétaire': change.new_owner,
            'Notes': change.notes
        })
    
    df = pd.DataFrame(data)
    
    # Création du fichier Excel en mémoire
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Historique Propriétaires', index=False)
        
        # Ajustement automatique de la largeur des colonnes
        worksheet = writer.sheets['Historique Propriétaires']
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_width)
    
    output.seek(0)
    
    # Envoi du fichier
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'historique_proprietaires_{device.name}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True)