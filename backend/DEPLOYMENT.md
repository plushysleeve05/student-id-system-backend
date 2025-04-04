# Student ID System - Production Deployment Guide

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Nginx (for reverse proxy)
- SSL certificate (for HTTPS)
- Linux server (recommended Ubuntu 20.04 LTS or higher)

## Security Checklist

1. **Environment Variables**
   - Never commit `.env` file to version control
   - Use strong, randomly generated SECRET_KEY
   - Store sensitive credentials in environment variables
   - Rotate secrets periodically

2. **Database Security**
   - Use strong passwords
   - Limit database access to specific IP addresses
   - Regular backups
   - Keep PostgreSQL updated

3. **API Security**
   - Enable CORS only for trusted domains
   - Use HTTPS only
   - Implement rate limiting
   - Regular security audits

## Installation Steps

1. **System Updates**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. **Install Dependencies**
   ```bash
   sudo apt install python3-pip python3-venv postgresql nginx
   ```

3. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements_final.txt
   ```

4. **PostgreSQL Setup**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE student_id_system;
   CREATE USER myuser WITH PASSWORD 'strong_password';
   GRANT ALL PRIVILEGES ON DATABASE student_id_system TO myuser;
   ```

5. **Environment Configuration**
   ```bash
   # Create and edit .env file
   cp .env.example .env
   nano .env

   # Generate a secure secret key
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

6. **Nginx Configuration**
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

7. **SSL Configuration (using Certbot)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your_domain.com
   ```

8. **Create Systemd Service**
   ```bash
   sudo nano /etc/systemd/system/student-id-api.service
   ```
   ```ini
   [Unit]
   Description=Student ID System API
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/your/app
   Environment="PATH=/path/to/your/venv/bin"
   EnvironmentFile=/path/to/your/.env
   ExecStart=/path/to/your/venv/bin/python run.py

   [Install]
   WantedBy=multi-user.target
   ```

9. **Start the Service**
   ```bash
   sudo systemctl start student-id-api
   sudo systemctl enable student-id-api
   ```

## Monitoring and Maintenance

1. **Log Monitoring**
   - Check application logs: `sudo journalctl -u student-id-api`
   - Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`

2. **Database Backups**
   ```bash
   # Create backup script
   pg_dump -U myuser student_id_system > backup_$(date +%Y%m%d).sql
   ```

3. **Regular Updates**
   - Keep system packages updated
   - Update Python dependencies regularly
   - Monitor security advisories

## Security Best Practices

1. **Firewall Configuration**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 'Nginx Full'
   sudo ufw enable
   ```

2. **Regular Security Updates**
   ```bash
   sudo apt update
   sudo apt upgrade
   ```

3. **SSL/TLS Configuration**
   - Use strong SSL configuration
   - Regular certificate renewal
   - Enable HTTP/2

4. **Database Security**
   - Regular password rotation
   - Connection pooling
   - Regular security patches

## Backup Strategy

1. **Database Backups**
   - Daily automated backups
   - Backup verification
   - Off-site backup storage

2. **Application Backups**
   - Configuration files
   - Environment variables
   - Static files

## Scaling Considerations

1. **Horizontal Scaling**
   - Load balancer configuration
   - Multiple application instances
   - Database replication

2. **Vertical Scaling**
   - CPU and memory monitoring
   - Database optimization
   - Cache implementation

## Troubleshooting

1. **Common Issues**
   - Check application logs
   - Verify database connectivity
   - Monitor system resources

2. **Performance Issues**
   - Database query optimization
   - Application profiling
   - Resource monitoring

## Contact and Support

For production support and security issues, contact:
- Email: your-email@domain.com
- Emergency Contact: your-phone-number

Remember to replace placeholder values with your actual production values and keep this document updated with any changes to the deployment process.
