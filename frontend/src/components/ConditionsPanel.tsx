import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react';

interface RiskAssessmentProps {
  riskAssessment?: any;
  conditions?: any[];
}

const ConditionsPanel: React.FC<RiskAssessmentProps> = ({ riskAssessment, conditions }) => {
  const getRiskColor = (level: string) => {
    switch(level) {
      case 'SAFE': return 'bg-green-50 border-green-200';
      case 'MODERATE': return 'bg-yellow-50 border-yellow-200';
      case 'HIGH': return 'bg-orange-50 border-orange-200';
      case 'CRITICAL': return 'bg-red-50 border-red-200';
      default: return 'bg-gray-50';
    }
  };

  const getRiskIcon = (level: string) => {
    switch(level) {
      case 'SAFE': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'MODERATE': return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'HIGH':
      case 'CRITICAL': return <AlertTriangle className="w-5 h-5 text-red-600" />;
      default: return null;
    }
  };

  return (
    <div className="conditions-panel">
      <h2 className="text-lg font-bold mb-4">Marine Intelligence</h2>
      
      {riskAssessment && (
        <div className={`risk-card p-4 rounded-lg border-2 mb-4 ${getRiskColor(riskAssessment.risk_level)}`}>
          <div className="flex items-center gap-2 mb-2">
            {getRiskIcon(riskAssessment.risk_level)}
            <h3 className="font-bold text-lg">{riskAssessment.risk_level}</h3>
          </div>
          <p className="text-sm mb-2">Risk Score: <span className="font-bold">{riskAssessment.risk_score}/100</span></p>
          
          <div className="mb-3">
            <h4 className="font-semibold text-sm mb-1">Factors:</h4>
            <ul className="text-sm space-y-1">
              {riskAssessment.factors.map((factor: string, idx: number) => (
                <li key={idx} className="text-xs">• {factor}</li>
              ))}
            </ul>
          </div>
          
          <div className="bg-white bg-opacity-60 p-2 rounded text-sm">
            <p className="font-semibold mb-1">Recommendation:</p>
            <p>{riskAssessment.recommendation}</p>
          </div>
        </div>
      )}
      
      {conditions && conditions.length > 0 && (
        <div className="space-y-2">
          {conditions.map((cond: any, idx: number) => (
            <div key={idx} className="bg-gray-50 p-3 rounded border border-gray-200">
              <h4 className="font-bold text-sm capitalize mb-1">{cond.type}</h4>
              <div className="text-xs space-y-1">
                {cond.data.hourly && (
                  <p>Latest Data: {cond.data.hourly.time?.[0]}</p>
                )}
                {cond.data.latitude && (
                  <p>Location: {cond.data.latitude}, {cond.data.longitude}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {!riskAssessment && !conditions && (
        <div className="text-center text-gray-500 py-8">
          <p className="text-sm">Send a message to get marine intelligence</p>
        </div>
      )}
    </div>
  );
};

export default ConditionsPanel;