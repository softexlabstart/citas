import React from 'react';
import { Badge } from 'react-bootstrap';
import { RoleType, ROLE_CHOICES } from '../interfaces/Role';

interface RoleBadgeProps {
    role: RoleType;
    additionalRoles?: RoleType[];
    showAdditionalCount?: boolean;
    size?: 'sm' | 'md' | 'lg';
}

const RoleBadge: React.FC<RoleBadgeProps> = ({
    role,
    additionalRoles = [],
    showAdditionalCount = true,
    size = 'md'
}) => {
    const roleInfo = ROLE_CHOICES.find(r => r.value === role);

    if (!roleInfo) {
        return null;
    }

    const getBadgeVariant = (roleValue: RoleType): string => {
        const variants: Record<RoleType, string> = {
            owner: 'warning',
            admin: 'danger',
            sede_admin: 'primary',
            colaborador: 'success',
            cliente: 'info'
        };
        return variants[roleValue];
    };

    const getSizeClass = (sizeValue: string): string => {
        const sizeMap: Record<string, string> = {
            sm: 'fs-7',
            md: 'fs-6',
            lg: 'fs-5'
        };
        return sizeMap[sizeValue] || sizeMap.md;
    };

    const additionalCount = additionalRoles.length;

    return (
        <div className="d-inline-flex align-items-center gap-1">
            <Badge
                bg={getBadgeVariant(role)}
                className={`${getSizeClass(size)} px-2 py-1`}
            >
                {roleInfo.emoji} {roleInfo.label}
            </Badge>
            {showAdditionalCount && additionalCount > 0 && (
                <Badge
                    bg="secondary"
                    className={`${getSizeClass(size)} px-2 py-1`}
                    title={`Roles adicionales: ${additionalRoles.map(r => ROLE_CHOICES.find(rc => rc.value === r)?.label).join(', ')}`}
                >
                    +{additionalCount}
                </Badge>
            )}
        </div>
    );
};

export default RoleBadge;
