import React, { useEffect } from 'react';
import { Container, Row, Col, Table, Alert } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { Service } from '../interfaces/Service';
import { getServicios } from '../api';
import { useApi } from '../hooks/useApi';
import ServiceTableSkeleton from './ServiceTableSkeleton';
import 'react-loading-skeleton/dist/skeleton.css';

const Services: React.FC = () => {
  const { t } = useTranslation();
  const { data: services, loading, error, request: fetchServices } = useApi<Service[], []>(getServicios);

  useEffect(() => {
    fetchServices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Container className="mt-5">
      <div className="bg-white p-4 rounded shadow-sm"> {/* Added div with background */}
        <Row>
          <Col>
            <h2>{t('our_services')}</h2>
          </Col>
        </Row>

        <Row className="mt-4">
          <Col>
            <div className="table-responsive">
              {error && !loading && <Alert variant="danger">{t(error) || error}</Alert>}

              {loading && <ServiceTableSkeleton />}

              {!loading && !error && services && (
                  <Table striped bordered hover>
                    <thead>
                      <tr>
                        <th>{t('name')}</th>
                        <th>{t('description')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {services.map((service: Service) => (
                        <tr key={service.id}>
                          <td>{service.nombre}</td>
                          <td>{service.descripcion}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
              )}
            </div>
          </Col>
        </Row>
      </div> {/* Closing div */}
    </Container>
  );
};

export default Services;