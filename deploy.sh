#!/bin/bash
cd /var/www/agendaweb
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
sudo systemctl restart agendaweb
echo "Deploy completed at $(date)" >> /var/log/deploy.log