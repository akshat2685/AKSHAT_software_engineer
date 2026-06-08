import React from 'react';
import { AvatarViewer } from './AvatarViewer';

export const AvatarPanel: React.FC = () => {
  return (
    <div className="glass-panel p-4">
      <AvatarViewer />
    </div>
  );
};
