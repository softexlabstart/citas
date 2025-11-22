import React from 'react';
import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

interface GenericSkeletonProps {
    count?: number;
    type?: 'line' | 'circle' | 'card' | 'list';
    height?: number;
}

const GenericSkeleton: React.FC<GenericSkeletonProps> = ({
    count = 3,
    type = 'line',
    height = 20
}) => {
    const renderSkeleton = () => {
        switch (type) {
            case 'circle':
                return <Skeleton circle width={height} height={height} />;

            case 'card':
                return (
                    <div className="card mb-3">
                        <div className="card-body">
                            <Skeleton height={25} width="60%" className="mb-2" />
                            <Skeleton count={3} height={15} />
                        </div>
                    </div>
                );

            case 'list':
                return (
                    <div className="list-group-item mb-2">
                        <div className="d-flex align-items-center">
                            <Skeleton circle width={40} height={40} className="me-3" />
                            <div className="flex-grow-1">
                                <Skeleton width="60%" height={18} className="mb-1" />
                                <Skeleton width="40%" height={14} />
                            </div>
                        </div>
                    </div>
                );

            case 'line':
            default:
                return <Skeleton height={height} />;
        }
    };

    return (
        <SkeletonTheme baseColor="#e9ecef" highlightColor="#f8f9fa">
            <div>
                {Array(count).fill(0).map((_, index) => (
                    <div key={index} className="mb-2">
                        {renderSkeleton()}
                    </div>
                ))}
            </div>
        </SkeletonTheme>
    );
};

export default GenericSkeleton;
