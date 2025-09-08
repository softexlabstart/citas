import React from 'react';
import { Table } from 'react-bootstrap';
import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import { useTranslation } from 'react-i18next';

const AppointmentTableSkeleton: React.FC = () => {
  const { t } = useTranslation();
  const skeletonRows = Array(8).fill(0); // Show 8 skeleton rows

  return (
    <SkeletonTheme baseColor="#e9ecef" highlightColor="#f8f9fa">
      <div className="table-responsive">
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>{t('id')}</th>
              <th>{t('client_name')}</th>
              <th>{t('date')}</th>
              <th>{t('service')}</th>
              <th>{t('sede_label')}</th>
              <th>{t('status')}</th>
              <th>{t('actions')}</th>
            </tr>
          </thead>
          <tbody>
            {skeletonRows.map((_, index) => (
              <tr key={index}>
                <td><Skeleton width={30} /></td>
                <td><Skeleton /></td>
                <td><Skeleton /></td>
                <td><Skeleton /></td>
                <td><Skeleton /></td>
                <td><Skeleton width={100} /></td>
                <td><Skeleton width={80} /></td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </SkeletonTheme>
  );
};

export default AppointmentTableSkeleton;