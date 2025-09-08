import React from 'react';
import { Table } from 'react-bootstrap';
import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import { useTranslation } from 'react-i18next';

const ServiceTableSkeleton: React.FC = () => {
  const { t } = useTranslation();
  // Creamos un array para renderizar varias filas de esqueleto
  const skeletonRows = Array(5).fill(0);

  return (
    <SkeletonTheme baseColor="#e0e0e0" highlightColor="#f5f5f5">
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>{t('name')}</th>
            <th>{t('description')}</th>
          </tr>
        </thead>
        <tbody>
          {skeletonRows.map((_, index) => (
            <tr key={index}>
              <td><Skeleton /></td>
              <td><Skeleton /></td>
            </tr>
          ))}
        </tbody>
      </Table>
    </SkeletonTheme>
  );
};

export default ServiceTableSkeleton;