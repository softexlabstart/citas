import React from 'react';
import { Card, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';

interface DashboardCardProps {
  title: string;
  text: string;
  linkTo: string;
  icon: React.ReactNode;
  variant: string;
}

const DashboardCard: React.FC<DashboardCardProps> = ({ title, text, linkTo, icon, variant }) => {
  return (
    <Card className="h-100 text-center shadow-sm card-hover">
      <Card.Body>
        <div className={`text-${variant} mb-3`}>{icon}</div>
        <Card.Title className="h4">{title}</Card.Title>
        <Card.Text>{text}</Card.Text>
        <Link to={linkTo}>
          <Button variant={`outline-${variant}`} className="mt-auto">
            Ir a {title.split(' ')[1]}
          </Button>
        </Link>
      </Card.Body>
    </Card>
  );
};

export default DashboardCard;
